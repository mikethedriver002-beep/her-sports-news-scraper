from __future__ import annotations

"""Build normalized Phase 7 editorial events from fixtures and existing HSD packets."""

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from hsd_phase7_editorial_engine import (
    SUPPORTED_SPORTS,
    clean,
    normalize_event,
    normalize_sport,
    slug,
)

VERSION = "v1.0-phase7-event-packet-builder"
FIXTURES = Path("config/graphics/v5/phase7/fixture_events_v1.json")
OUT_ROOT = Path("outputs/latest/HSD_PHASE7")
OUT_JSON = OUT_ROOT / "phase7_editorial_events.json"
OUT_CSV = OUT_ROOT / "phase7_editorial_events.csv"
REPORT_JSON = Path("phase7_event_packets_report.json")
REPORT_MD = Path("phase7_event_packets_report.md")

FIELDS = [
    "event_id",
    "sport_id",
    "kind",
    "primary_name",
    "secondary_name",
    "primary_short",
    "secondary_short",
    "winner_name",
    "loser_name",
    "scoreline",
    "source_headline",
    "verified_angle",
    "event_date",
    "source_type",
    "source_ref",
    "fixture_only",
]

LIVE_JSON_CANDIDATES = [
    Path("data/phase7/live_events.json"),
    Path("operator/inbox/phase7_live_events.json"),
    Path("outputs/latest/HSD_PHASE7_SOURCE_PACKETS/events.json"),
    Path("phase7_live_events.json"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        try:
            item = json.loads(value)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def split_values(value: Any) -> List[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    text = clean(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [clean(item) for item in parsed if clean(item)]
    except Exception:
        pass
    return [clean(item) for item in re.split(r"\s*(?:;|\||,|\bvs\.?\b|\bat\b)\s*", text, flags=re.I) if clean(item)]


def ready_packet(row: Mapping[str, Any]) -> bool:
    readiness = clean(row.get("content_readiness") or row.get("readiness") or row.get("status")).lower()
    return any(token in readiness for token in ["ready", "approved", "verified"])


def derive_kind(row: Mapping[str, Any]) -> str:
    explicit = clean(row.get("kind") or row.get("event_kind")).lower()
    if explicit in {"preview", "spotlight", "result", "story"}:
        return explicit
    hay = " ".join(
        clean(row.get(key))
        for key in ["story_type", "content_family", "headline", "scores", "scoreline"]
    ).lower()
    if any(token in hay for token in ["final", "result", "recap", "beat", "wins", "won"]):
        return "result"
    if any(token in hay for token in ["preview", "tonight", "upcoming", "watch", "matchup"]):
        return "preview"
    if any(token in hay for token in ["spotlight", "feature"]):
        return "spotlight"
    return "story"


def packet_entities(row: Mapping[str, Any], sport_id: str) -> tuple[str, str]:
    teams = split_values(row.get("teams") or row.get("team_names"))
    players = split_values(row.get("players") or row.get("athletes"))
    if sport_id in {"tennis", "lpga"}:
        values = players or teams
        if values:
            primary = values[0]
            secondary = values[1] if len(values) > 1 else ("The Field" if sport_id == "lpga" else "Opponent")
            return primary, secondary
    values = teams or players
    if len(values) >= 2:
        return values[0], values[1]
    headline = clean(row.get("headline") or row.get("source_headline"))
    for separator in [r"\s+at\s+", r"\s+vs\.?\s+", r"\s+v\.?\s+"]:
        parts = re.split(separator, headline, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            return clean(parts[0]), clean(parts[1])
    return (values[0], "") if values else ("", "")


def manual_packet_event(row: Mapping[str, Any], source_type: str) -> Optional[Dict[str, Any]]:
    if not ready_packet(row):
        return None
    sport_id = normalize_sport(row.get("sport"), row.get("league"))
    if sport_id not in SUPPORTED_SPORTS:
        return None
    primary, secondary = packet_entities(row, sport_id)
    if not primary:
        return None
    kind = derive_kind(row)
    scoreline = clean(row.get("scoreline") or row.get("scores") or row.get("score_display"))
    headline = clean(row.get("headline") or row.get("source_headline"))
    packet_id = clean(row.get("packet_id") or row.get("source_id") or row.get("story_id"))
    event = normalize_event(
        {
            "event_id": packet_id or f"phase7-{slug(sport_id)}-{slug(headline or primary)}",
            "sport_id": sport_id,
            "kind": kind,
            "primary_name": primary,
            "secondary_name": secondary,
            "winner_name": primary if kind == "result" else "",
            "loser_name": secondary if kind == "result" else "",
            "scoreline": scoreline,
            "source_headline": headline or f"{primary} vs {secondary}".strip(),
            "verified_angle": clean(row.get("angle") or row.get("summary") or row.get("threads_angle")),
            "event_date": clean(row.get("event_date") or row.get("event_date_local")),
            "source_type": source_type,
            "source_ref": clean(row.get("source_ref") or row.get("source_urls") or row.get("evidence_urls")),
            "fixture_only": False,
        }
    )
    return event


def events_from_manual_packets() -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    sources = [
        (Path("manual_workflow_content_packets.csv"), "manual_workflow_content_packets_csv"),
        (Path("operator/inbox/manual_workflow_inbox.csv"), "manual_workflow_inbox_csv"),
        (Path("story_candidates_manual.csv"), "manual_story_candidate_csv"),
    ]
    for path, source_type in sources:
        for row in read_csv(path):
            event = manual_packet_event(row, source_type)
            if event:
                output.append(event)
    for row in read_jsonl(Path("manual_workflow_content_packets.jsonl")):
        event = manual_packet_event(row, "manual_workflow_content_packets_jsonl")
        if event:
            output.append(event)
    for row in read_jsonl(Path("operator/inbox/phase7_live_events.jsonl")):
        event = normalize_event({**row, "source_type": clean(row.get("source_type")) or "phase7_live_events_jsonl", "fixture_only": False})
        if event.get("sport_id") in SUPPORTED_SPORTS and event.get("primary_name"):
            output.append(event)
    return output


def events_from_live_json() -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for path in LIVE_JSON_CANDIDATES:
        payload = read_json(path)
        if payload is None:
            continue
        raw_events = payload.get("events") if isinstance(payload, dict) else payload
        if not isinstance(raw_events, list):
            continue
        for raw in raw_events:
            if not isinstance(raw, dict):
                continue
            event = normalize_event({**raw, "source_type": clean(raw.get("source_type")) or path.as_posix(), "fixture_only": False})
            if event.get("sport_id") in SUPPORTED_SPORTS and event.get("primary_name"):
                output.append(event)
    return output


def events_from_wnba_manifest() -> List[Dict[str, Any]]:
    path = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
    payload = read_json(path)
    if not isinstance(payload, dict):
        return []
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        source_id = clean(item.get("source_id") or item.get("item_id"))
        headline = clean(item.get("headline"))
        if not source_id or source_id in grouped:
            continue
        if clean(item.get("template_id")) == "hsd_tonight_in_the_w_a":
            primary, secondary = "", ""
            if " at " in headline:
                primary, secondary = [clean(value) for value in headline.split(" at ", 1)]
            grouped[source_id] = normalize_event(
                {
                    "event_id": source_id,
                    "sport_id": "wnba",
                    "kind": "preview",
                    "primary_name": primary,
                    "secondary_name": secondary,
                    "source_headline": headline,
                    "source_type": "wnba_renderer_manifest",
                    "source_ref": path.as_posix(),
                    "fixture_only": bool(payload.get("fixture_mode")),
                }
            )
        elif clean(item.get("template_id")) == "hsd_game_recap_final_score_a":
            winner, loser = "", ""
            match = re.match(r"(.+?)\s+beat\s+(.+)$", headline, flags=re.I)
            if match:
                winner, loser = clean(match.group(1)), clean(match.group(2))
            grouped[source_id] = normalize_event(
                {
                    "event_id": source_id,
                    "sport_id": "wnba",
                    "kind": "result",
                    "primary_name": winner,
                    "secondary_name": loser,
                    "winner_name": winner,
                    "loser_name": loser,
                    "scoreline": clean(item.get("editorial_scoreline") or item.get("content_module_body")),
                    "source_headline": headline,
                    "source_type": "wnba_renderer_manifest",
                    "source_ref": path.as_posix(),
                    "fixture_only": bool(payload.get("fixture_mode")),
                }
            )
    return [event for event in grouped.values() if event.get("primary_name")]


def fixture_events() -> List[Dict[str, Any]]:
    payload = read_json(FIXTURES)
    raw_events = payload.get("events") if isinstance(payload, dict) else []
    return [normalize_event(raw) for raw in raw_events if isinstance(raw, dict)]


def dedupe(events: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in events:
        event = normalize_event(raw)
        key = (clean(event.get("event_id")), clean(event.get("sport_id")), clean(event.get("kind")))
        if key in seen:
            continue
        seen.add(key)
        output.append(event)
    return output


def build(mode: str) -> Dict[str, Any]:
    if mode == "fixture_audit":
        events = dedupe(fixture_events())
    else:
        events = dedupe([*events_from_live_json(), *events_from_manual_packets(), *events_from_wnba_manifest()])

    blockers: List[str] = []
    warnings: List[str] = []
    invalid: List[str] = []
    for event in events:
        ident = clean(event.get("event_id")) or "missing-id"
        if clean(event.get("sport_id")) not in SUPPORTED_SPORTS:
            invalid.append(f"unsupported_sport:{ident}")
        if clean(event.get("kind")) not in {"preview", "spotlight", "result", "story"}:
            invalid.append(f"unsupported_kind:{ident}")
        if not clean(event.get("primary_name")):
            invalid.append(f"missing_primary_name:{ident}")
        if mode == "live_data" and event.get("fixture_only"):
            invalid.append(f"fixture_event_in_live_data:{ident}")
    blockers.extend(invalid)

    sport_counts = {sport_id: 0 for sport_id in sorted(SUPPORTED_SPORTS)}
    kind_counts: Dict[str, int] = {}
    for event in events:
        sport_id = clean(event.get("sport_id"))
        kind = clean(event.get("kind"))
        if sport_id in sport_counts:
            sport_counts[sport_id] += 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    if mode == "fixture_audit":
        for sport_id, count in sport_counts.items():
            if count < 2:
                blockers.append(f"fixture_sport_not_fully_covered:{sport_id}:{count}")
    else:
        if not events:
            blockers.append("no_phase7_live_events")
        missing_non_wnba = [sport_id for sport_id in sorted(SUPPORTED_SPORTS - {"wnba"}) if sport_counts[sport_id] == 0]
        if missing_non_wnba:
            warnings.append("non_wnba_live_packets_not_present:" + ",".join(missing_non_wnba))

    status = "passed_phase7_event_packets" if not blockers else "blocked_phase7_event_packets"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "mode": mode,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "event_count": len(events),
        "sport_counts": sport_counts,
        "kind_counts": kind_counts,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "human_visual_approval_required": True,
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "events": events,
    }


def write_outputs(report: Mapping[str, Any]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "hsd.phase7.editorial_event.v1",
        "version": VERSION,
        "mode": report.get("mode"),
        "events": report.get("events") or [],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, report.get("events") or [])
    REPORT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 7 Event Packets",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Events: `{report.get('event_count')}`",
        "",
        "## Sports",
        "",
    ]
    for sport_id, count in (report.get("sport_counts") or {}).items():
        lines.append(f"- `{sport_id}`: `{count}`")
    lines += ["", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phase 7 normalized editorial events.")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build(args.mode)
    write_outputs(report)
    print(json.dumps({key: report[key] for key in ["version", "mode", "status", "event_count", "sport_counts", "blockers", "warnings"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
