from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "v1.0-phase8b-daily-multisport-packet-ingestion"
SUPPORTED = {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"}
OUT_DIR = Path("outputs/latest/HSD_PHASE8B")
OUT_JSON = OUT_DIR / "daily_multisport_events.json"
OUT_CSV = OUT_DIR / "daily_multisport_events.csv"
REPORT_JSON = Path("phase8b_daily_multisport_packets_report.json")
REPORT_MD = Path("phase8b_daily_multisport_packets_report.md")
POLICY = Path("config/graphics/v5/phase8b/daily_packet_policy_v1.json")
FIXTURE = Path("data/phase8b/manual_packets/phase8b_fixture_events.json")

FIELDS = ["event_id", "sport_id", "kind", "primary_name", "secondary_name", "winner_name", "loser_name", "scoreline", "event_title", "verified_angle", "source_name", "source_url", "packet_path"]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "event"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_policy() -> Dict[str, Any]:
    try:
        value = read_json(POLICY)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def normalize_sport(value: Any) -> str:
    text = clean(value).lower().replace(" ", "_").replace("'", "")
    mapping = {"wta": "tennis", "womens_tennis": "tennis", "women_tennis": "tennis", "softball": "ncaa_softball", "college_softball": "ncaa_softball", "ncaasb": "ncaa_softball", "ncaavb": "volleyball", "women_volleyball": "volleyball"}
    return mapping.get(text, text)


def normalize_kind(value: Any) -> str:
    text = clean(value).lower()
    if text in {"final", "recap", "result"}:
        return "result"
    if text in {"preview", "watch", "tonight"}:
        return "preview"
    return text or "story"


def load_json_events(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = data.get("events") or data.get("items") or []
    else:
        events = []
    return [dict(e, packet_path=path.as_posix()) for e in events if isinstance(e, dict)]


def load_csv_events(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row, packet_path=path.as_posix()) for row in reader]


def discover_paths(mode: str) -> List[Path]:
    paths: List[Path] = []
    env_path = clean(os.environ.get("HSD_PHASE8B_DAILY_PACKET_PATH"))
    if env_path:
        for part in env_path.split(os.pathsep):
            p = Path(part)
            if p.exists():
                paths.append(p)
    policy = read_policy()
    for pattern in policy.get("manual_packet_globs") or []:
        paths.extend(Path(p) for p in glob.glob(pattern))
    if mode == "fixture_audit" and FIXTURE.exists():
        paths.append(FIXTURE)
    seen = set()
    unique = []
    for path in paths:
        key = path.resolve().as_posix()
        if key not in seen and path.exists() and path.is_file():
            seen.add(key)
            unique.append(path)
    return unique


def normalize_event(raw: Mapping[str, Any], idx: int) -> Dict[str, Any]:
    sport_id = normalize_sport(raw.get("sport_id") or raw.get("sport") or raw.get("league"))
    kind = normalize_kind(raw.get("kind") or raw.get("event_kind"))
    primary = clean(raw.get("primary_name") or raw.get("team_name") or raw.get("player_name") or raw.get("away_name") or raw.get("winner_name"))
    secondary = clean(raw.get("secondary_name") or raw.get("opponent_name") or raw.get("home_name") or raw.get("loser_name"))
    winner = clean(raw.get("winner_name") or raw.get("winner"))
    loser = clean(raw.get("loser_name") or raw.get("loser"))
    scoreline = clean(raw.get("scoreline") or raw.get("score_display"))
    event_title = clean(raw.get("event_title") or raw.get("title") or raw.get("headline"))
    event_id = clean(raw.get("event_id")) or slug("-".join([sport_id, kind, primary, secondary, winner, loser, scoreline, str(idx)]))
    return {
        **dict(raw),
        "event_id": event_id,
        "sport_id": sport_id,
        "kind": kind,
        "primary_name": primary,
        "secondary_name": secondary,
        "primary_short": clean(raw.get("primary_short")) or primary,
        "secondary_short": clean(raw.get("secondary_short")) or secondary,
        "winner_name": winner,
        "loser_name": loser,
        "winner_short": clean(raw.get("winner_short")) or winner,
        "loser_short": clean(raw.get("loser_short")) or loser,
        "scoreline": scoreline,
        "event_title": event_title,
        "verified_angle": clean(raw.get("verified_angle") or raw.get("angle")),
        "source_name": clean(raw.get("source_name")),
        "source_url": clean(raw.get("source_url")),
        "packet_path": clean(raw.get("packet_path")),
    }


def validate_event(event: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    if clean(event.get("sport_id")) not in SUPPORTED:
        reasons.append("unsupported_sport")
    if clean(event.get("sport_id")) == "wnba":
        reasons.append("wnba_packet_not_needed_in_phase8b_manual_inbox")
    if clean(event.get("kind")) not in {"preview", "result", "story"}:
        reasons.append("unsupported_kind")
    if not clean(event.get("primary_name")) and not clean(event.get("winner_name")):
        reasons.append("missing_primary_or_winner")
    if clean(event.get("kind")) == "result" and not (clean(event.get("scoreline")) or clean(event.get("winner_name"))):
        reasons.append("result_missing_score_or_winner")
    if clean(event.get("kind")) == "preview" and not (clean(event.get("secondary_name")) or clean(event.get("event_title"))):
        reasons.append("preview_missing_secondary_or_title")
    return reasons


def load_events(mode: str) -> List[Dict[str, Any]]:
    raw_events: List[Dict[str, Any]] = []
    for path in discover_paths(mode):
        try:
            if path.suffix.lower() == ".json":
                raw_events.extend(load_json_events(path))
            elif path.suffix.lower() == ".csv":
                raw_events.extend(load_csv_events(path))
        except Exception as exc:
            raw_events.append({"sport_id": "", "kind": "", "primary_name": "", "packet_path": path.as_posix(), "load_error": str(exc)})
    return [normalize_event(raw, i) for i, raw in enumerate(raw_events)]


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def build_report(mode: str) -> Dict[str, Any]:
    events = load_events(mode)
    rows = []
    blockers: List[str] = []
    warnings: List[str] = []
    for event in events:
        reasons = validate_event(event)
        event["phase8b_packet_status"] = "passed_phase8b_packet_validation" if not reasons else "blocked_phase8b_packet_validation"
        event["phase8b_packet_reasons"] = ";".join(reasons)
        rows.append(event)
        blockers.extend(f"{event.get('event_id')}:{reason}" for reason in reasons)
    non_wnba = [event for event in rows if clean(event.get("sport_id")) in SUPPORTED and clean(event.get("sport_id")) != "wnba" and event.get("phase8b_packet_status") == "passed_phase8b_packet_validation"]
    if mode == "live_data" and not non_wnba:
        warnings.append("no_non_wnba_daily_packets_found")
    status = "passed_phase8b_daily_multisport_packets" if not blockers else "blocked_phase8b_daily_multisport_packets"
    return {
        "version": VERSION,
        "mode": mode,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "discovered_events": len(rows),
        "passed_events": sum(r.get("phase8b_packet_status") == "passed_phase8b_packet_validation" for r in rows),
        "non_wnba_passed_events": len(non_wnba),
        "sports_present": sorted({clean(r.get("sport_id")) for r in non_wnba if clean(r.get("sport_id"))}),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "items": rows,
    }


def write_report(report: Mapping[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"version": report.get("version"), "items": report.get("items") or []}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, report.get("items") or [])
    REPORT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 8B Daily Multi-Sport Packets",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Discovered events: `{report.get('discovered_events')}`",
        f"Passed events: `{report.get('passed_events')}`",
        f"Non-WNBA passed events: `{report.get('non_wnba_passed_events')}`",
        f"Sports present: `{', '.join(report.get('sports_present') or []) or 'none'}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{b}`" for b in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{w}`" for w in report.get("warnings") or []] or ["- None"]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.mode)
    write_report(report)
    print(json.dumps({k: report[k] for k in ["version", "mode", "status", "discovered_events", "non_wnba_passed_events", "sports_present", "blockers", "warnings"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
