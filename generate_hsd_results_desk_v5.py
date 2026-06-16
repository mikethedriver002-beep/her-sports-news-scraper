from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import generate_hsd_results_desk_v4 as v4  # reuse parser/reconciler helpers, not paid sources

VERSION = "v5.0-free-public-source-accuracy"

# v4-compatible output files consumed by existing downstream scripts.
OBSERVATIONS_FILE = "source_observations.csv"
RECONCILED_FILE = "reconciled_events.csv"
RESULTS_BOARD_FILE = "today_results_board.csv"
WOMENS_RESULTS_FILE = "today_womens_results.csv"
FINAL_RESULTS_FILE = "today_final_results.csv"
TOP_RESULTS_FILE = "top_womens_results.csv"
MANUAL_REVIEW_FILE = "manual_review_queue.csv"
SOURCE_HEALTH_FILE = "source_health_report.csv"
BOX_SCORE_AUDIT_FILE = "wnba_box_score_audit.csv"
BOX_SCORE_SUMMARY_FILE = "wnba_box_score_summary.md"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
RECOMMENDATIONS_FILE = "daily_results_recommendations.md"
HUB_FILE = "results_system_hub.md"
MANIFEST_FILE = "run_manifest.json"

# v5 accuracy outputs.
V5_MANIFEST = Path("results_desk_v5_manifest.json")
V5_REPORT = Path("results_desk_v5_report.md")
SOURCE_ACCURACY_JSON = Path("source_accuracy_v5.json")
SOURCE_ACCURACY_MD = Path("source_accuracy_v5.md")
DUPLICATE_AUDIT = Path("duplicate_game_audit_v5.csv")
STALE_AUDIT = Path("stale_source_audit_v5.csv")
MISSING_ALERT_JSON = Path("missing_games_alert_v5.json")
MISSING_ALERT_MD = Path("missing_games_alert_v5.md")
EXPECTED_GAMES = [Path("config/hsd_expected_games_v5.csv"), Path("data/expected_games/wnba_expected_games.csv"), Path("expected_games.csv")]

DUP_FIELDS = ["canonical_key", "source_count", "source_names", "score_variants", "date", "teams", "decision"]
STALE_FIELDS = ["source_name", "source_event_id", "canonical_key", "scheduled_date_local", "status_norm", "source_url", "reason"]
EXPECTED_FIELDS = ["date", "league", "home_team", "away_team", "expected_key", "matched", "matched_event_uid", "reason"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return v4.clean(value)


def write_csv(path: str | Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out: Dict[str, Any] = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(value, float) and field in {"confidence", "editorial_rank"}:
                    value = f"{value:.2f}" if field == "confidence" else f"{value:.1f}"
                out[field] = value
            writer.writerow(out)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def allowed_sources() -> List[str]:
    # V5 hard rule: free/public/manual only. No paid API keys, no RapidAPI, no paid search.
    raw = os.environ.get("HSD_RESULTS_V5_SOURCES", "espn_wnba_public,manual_seed")
    allowed = {"espn_wnba_public", "manual_seed"}
    return [s for s in [x.strip().lower() for x in raw.split(",") if x.strip()] if s in allowed]


def event_score_variant(obs: Dict[str, str]) -> str:
    if not v4.score_present(obs.get("home_score"), obs.get("away_score")):
        return "no_score"
    return "|".join([
        clean(obs.get("home_team_norm")), clean(obs.get("home_score")),
        clean(obs.get("away_team_norm")), clean(obs.get("away_score")),
    ])


def observation_date_status(obs: Dict[str, str], iso_dates: List[str]) -> Tuple[bool, str]:
    date = clean(obs.get("scheduled_date_local"))
    if not date:
        return True, "missing_scheduled_date"
    if date not in set(iso_dates):
        return True, f"outside_window:{date}"
    return False, "in_window"


def free_source_observations(run_id: str, compact_dates: List[str], iso_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    sources = allowed_sources()

    if "espn_wnba_public" in sources:
        obs, h = v4.fetch_espn_wnba(run_id, compact_dates)
        for row in obs:
            row["source_name"] = "espn_wnba_public"
            row["source_priority"] = "95"
            row["notes"] = clean(row.get("notes") + "; v5_free_public_source")
        for row in h:
            row["source_name"] = "espn_wnba_public"
            row["notes"] = clean(row.get("notes") + "; free public ESPN scoreboard endpoint")
        observations.extend(obs)
        health.extend(h)

    manual_rows = load_manual_seed_observations(run_id, iso_dates)
    if manual_rows:
        observations.extend(manual_rows)
        health.append({
            "source_name": "manual_seed",
            "sport_or_league": "all",
            "date": ",".join(iso_dates),
            "http_status": 0,
            "ok": "Yes",
            "events_found": len(manual_rows),
            "observations_emitted": len(manual_rows),
            "stale_rejected": 0,
            "notes": "user/manual seed rows loaded from free local files",
        })
    elif "manual_seed" in sources:
        health.append({
            "source_name": "manual_seed",
            "sport_or_league": "all",
            "date": ",".join(iso_dates),
            "http_status": 0,
            "ok": "Yes",
            "events_found": 0,
            "observations_emitted": 0,
            "stale_rejected": 0,
            "notes": "no manual seed file found; optional fallback only",
        })

    return observations, health


def load_manual_seed_observations(run_id: str, iso_dates: List[str]) -> List[Dict[str, str]]:
    candidates = [Path("manual_results_seed.csv"), Path("data/manual_results_seed.csv"), Path("config/manual_results_seed.csv")]
    rows: List[Dict[str, str]] = []
    for path in candidates:
        for row in read_csv(path):
            obs = normalize_manual_seed_row(run_id, row, path.as_posix())
            if obs:
                rows.append(obs)
    return rows


def normalize_manual_seed_row(run_id: str, row: Dict[str, str], source_file: str) -> Dict[str, str] | None:
    league = clean(row.get("league") or "WNBA")
    sport = clean(row.get("sport") or "basketball")
    date = clean(row.get("scheduled_date_local") or row.get("event_date_local") or row.get("date"))
    home = clean(row.get("home_team") or row.get("home_team_name"))
    away = clean(row.get("away_team") or row.get("away_team_name"))
    if not date or not home or not away:
        return None
    home_score = clean(row.get("home_score") or row.get("score_home"))
    away_score = clean(row.get("away_score") or row.get("score_away"))
    status = v4.normalize_status(row.get("status") or row.get("status_norm") or "scheduled")
    return {
        "run_id": run_id,
        "source_name": "manual_seed",
        "source_priority": "100",
        "source_event_id": clean(row.get("source_event_id") or row.get("event_id")),
        "canonical_key": v4.canonical_key(sport, date, home, away, league),
        "sport_norm": sport,
        "league_norm": league,
        "competition_id": clean(row.get("competition_id") or "manual"),
        "gender_scope": "women" if league.upper() == "WNBA" else clean(row.get("gender_scope") or "women"),
        "scheduled_start_utc": clean(row.get("scheduled_start_utc")),
        "scheduled_date_local": date,
        "home_team_raw": home,
        "away_team_raw": away,
        "home_team_norm": v4.normalize_team_for_context(home, league, sport),
        "away_team_norm": v4.normalize_team_for_context(away, league, sport),
        "status_raw": status,
        "status_norm": status,
        "home_score": home_score,
        "away_score": away_score,
        "score_by_period_json": clean(row.get("score_by_period_json")),
        "team_stats_json": clean(row.get("team_stats_json")),
        "player_stats_json": clean(row.get("player_stats_json")),
        "top_performers_json": clean(row.get("top_performers_json")),
        "source_url": clean(row.get("source_url") or source_file),
        "fetched_at_utc": now_iso(),
        "http_status": "0",
        "parse_ok": "Yes",
        "stale_rejected": "No",
        "women_match_method": "manual_seed",
        "raw_archive_path": source_file,
        "notes": "manual seed fallback; must be user/source reviewed",
    }


def duplicate_audit(observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for obs in observations:
        key = clean(obs.get("canonical_key")) or f"missing|{len(grouped)}"
        grouped[key].append(obs)
    rows: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        scores = sorted(set(event_score_variant(obs) for obs in group))
        sources = sorted(set(clean(obs.get("source_name")) for obs in group if clean(obs.get("source_name"))))
        first = group[0]
        decision = "merge_same_score" if len(scores) == 1 else "manual_review_score_conflict"
        rows.append({
            "canonical_key": key,
            "source_count": len(group),
            "source_names": ";".join(sources),
            "score_variants": " || ".join(scores),
            "date": first.get("scheduled_date_local", ""),
            "teams": f"{first.get('away_team_raw')} at {first.get('home_team_raw')}",
            "decision": decision,
        })
    return rows


def stale_audit(observations: List[Dict[str, str]], iso_dates: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for obs in observations:
        stale, reason = observation_date_status(obs, iso_dates)
        if stale:
            obs["stale_rejected"] = "Yes"
            rows.append({
                "source_name": obs.get("source_name"),
                "source_event_id": obs.get("source_event_id"),
                "canonical_key": obs.get("canonical_key"),
                "scheduled_date_local": obs.get("scheduled_date_local"),
                "status_norm": obs.get("status_norm"),
                "source_url": obs.get("source_url"),
                "reason": reason,
            })
    return rows


def expected_game_rows() -> List[Dict[str, str]]:
    for path in EXPECTED_GAMES:
        rows = read_csv(path)
        if rows:
            return rows
    return []


def expected_key(row: Dict[str, str]) -> str:
    date = clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local"))
    league = clean(row.get("league") or "WNBA")
    sport = clean(row.get("sport") or "basketball")
    home = clean(row.get("home_team") or row.get("home_team_name"))
    away = clean(row.get("away_team") or row.get("away_team_name"))
    if not date or not home or not away:
        return ""
    return v4.canonical_key(sport, date, home, away, league)


def missing_games_alert(expected_rows: List[Dict[str, str]], events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    event_by_key = {clean(e.get("canonical_key")): e for e in events if clean(e.get("canonical_key"))}
    rows: List[Dict[str, str]] = []
    for row in expected_rows:
        key = expected_key(row)
        matched = key in event_by_key
        event = event_by_key.get(key, {})
        rows.append({
            "date": clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local")),
            "league": clean(row.get("league") or "WNBA"),
            "home_team": clean(row.get("home_team") or row.get("home_team_name")),
            "away_team": clean(row.get("away_team") or row.get("away_team_name")),
            "expected_key": key,
            "matched": "Yes" if matched else "No",
            "matched_event_uid": clean(event.get("event_uid")),
            "reason": "matched" if matched else "missing_from_free_sources_or_outside_window",
        })
    summary = {
        "expected_fixture_file_present": bool(expected_rows),
        "expected_games": len(expected_rows),
        "matched": sum(1 for row in rows if row.get("matched") == "Yes"),
        "missing": sum(1 for row in rows if row.get("matched") == "No"),
    }
    return rows, summary


def source_accuracy(events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], duplicates: List[Dict[str, Any]], stale: List[Dict[str, Any]], expected_summary: Dict[str, Any]) -> Dict[str, Any]:
    women = [e for e in events if e.get("gender_scope") == "women"]
    finals = [e for e in women if e.get("status_norm") == "final"]
    score_conflicts = [e for e in events if e.get("score_conflict")]
    manual_review = [e for e in events if e.get("manual_review")]
    health_ok = [h for h in health if clean(h.get("ok")) == "Yes"]
    public_observations = [o for o in observations if o.get("source_name") == "espn_wnba_public"]
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "free_only": True,
        "paid_sources_required": False,
        "source_policy": "free public ESPN WNBA scoreboard plus optional manual seed; no paid APIs required",
        "counts": {
            "observations": len(observations),
            "public_espn_observations": len(public_observations),
            "reconciled_events": len(events),
            "women_events": len(women),
            "women_finals": len(finals),
            "score_conflicts": len(score_conflicts),
            "manual_review": len(manual_review),
            "duplicate_groups": len(duplicates),
            "stale_observations": len(stale),
            "source_health_rows": len(health),
            "source_health_ok_rows": len(health_ok),
            **{f"expected_{k}": v for k, v in expected_summary.items()},
        },
        "health": health,
        "risk_flags": {
            "score_conflicts_present": bool(score_conflicts),
            "stale_observations_present": bool(stale),
            "missing_expected_games_present": expected_summary.get("missing", 0) > 0,
            "expected_games_fixture_missing": not expected_summary.get("expected_fixture_file_present"),
        },
    }


def write_source_accuracy_md(data: Dict[str, Any]) -> str:
    counts = data.get("counts", {})
    risk = data.get("risk_flags", {})
    lines = [
        "# HSD Source Accuracy v5",
        "",
        f"Generated: `{data.get('generated_at_utc')}`",
        f"Version: `{data.get('version')}`",
        "",
        "## Source policy",
        "",
        "- Free/public sources only.",
        "- No API-Sports, RapidAPI, paid sports data, paid search, paid scraping proxy, or LLM dependency is required.",
        "- Current source: public ESPN WNBA scoreboard endpoint plus optional local manual seed fallback.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Risk flags", ""])
    for key, value in risk.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Health rows", ""])
    for item in data.get("health", []):
        lines.append(f"- {item.get('source_name')} | {item.get('date')} | ok={item.get('ok')} | events={item.get('events_found')} | emitted={item.get('observations_emitted')} | {item.get('notes')}")
    return "\n".join(lines) + "\n"


def report_md(run_id: str, manifest: Dict[str, Any], source_data: Dict[str, Any]) -> str:
    counts = manifest.get("counts", {})
    return "\n".join([
        "# Her Sports Daily Results Desk v5",
        "",
        f"Run ID: `{run_id}`",
        f"Generated: `{manifest.get('generated_at_utc')}`",
        f"Version: `{VERSION}`",
        "",
        "## What v5 changes",
        "",
        "- Removes paid API reliance from the active Results Desk path.",
        "- Uses free/public WNBA scoreboard data plus manual seed fallback.",
        "- Keeps v4-compatible output filenames so existing contracts, story results, and graphics packs keep working.",
        "- Adds duplicate, stale-source, expected-game, and source-health audits.",
        "",
        "## Counts",
        "",
        *[f"- {k}: `{v}`" for k, v in counts.items()],
        "",
        "## Next QA files",
        "",
        "- `source_accuracy_v5.md`",
        "- `duplicate_game_audit_v5.csv`",
        "- `stale_source_audit_v5.csv`",
        "- `missing_games_alert_v5.md`",
    ]) + "\n"


def main() -> None:
    iso_dates, compact_dates = v4.date_window()
    run_id = v4.stable_id(v4.iso_now(), VERSION, ",".join(allowed_sources()))

    observations, health = free_source_observations(run_id, compact_dates, iso_dates)
    stale_rows = stale_audit(observations, iso_dates)
    duplicate_rows = duplicate_audit(observations)

    events = v4.reconcile(run_id, observations)
    events = v4.apply_strict_date_window_gate(events, iso_dates)
    events = v4.apply_global_editorial_buckets(events)
    box_audit_rows = v4.audit_wnba_box_scores(events)
    events = v4.apply_global_editorial_buckets(events)

    all_events = events
    womens = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")]
    finals = [e for e in events if e.get("gender_scope") == "women" and e.get("status_norm") == "final" and float(e.get("confidence") or 0) >= 0.70]
    top = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")][:50]
    review = [e for e in events if e.get("gender_scope") == "women" and e.get("manual_review")]

    expected_rows, expected_summary = missing_games_alert(expected_game_rows(), events)
    accuracy = source_accuracy(events, observations, health, duplicate_rows, stale_rows, expected_summary)

    write_csv(OBSERVATIONS_FILE, observations, v4.OBS_FIELDS)
    write_csv(RECONCILED_FILE, events, v4.EVENT_FIELDS)
    write_csv(RESULTS_BOARD_FILE, all_events, v4.EVENT_FIELDS)
    write_csv(WOMENS_RESULTS_FILE, womens, v4.EVENT_FIELDS)
    write_csv(FINAL_RESULTS_FILE, finals, v4.EVENT_FIELDS)
    write_csv(TOP_RESULTS_FILE, top, v4.EVENT_FIELDS)
    write_csv(MANUAL_REVIEW_FILE, review, v4.EVENT_FIELDS)
    write_csv(SOURCE_HEALTH_FILE, health, ["source_name", "sport_or_league", "date", "http_status", "ok", "events_found", "observations_emitted", "stale_rejected", "notes"])
    write_csv(BOX_SCORE_AUDIT_FILE, box_audit_rows, ["event_uid", "espn_event_id", "graphics_headline", "league_norm", "http_status", "audit_status", "top_performers", "source_url", "notes"])
    write_csv(DUPLICATE_AUDIT, duplicate_rows, DUP_FIELDS)
    write_csv(STALE_AUDIT, stale_rows, STALE_FIELDS)
    write_csv("missing_games_alert_v5.csv", expected_rows, EXPECTED_FIELDS)

    Path(BOX_SCORE_SUMMARY_FILE).write_text(v4.box_score_summary_md(box_audit_rows), encoding="utf-8")
    Path(GRAPHICS_QUEUE_FILE).write_text(v4.graphics_queue(events), encoding="utf-8")
    Path(RECOMMENDATIONS_FILE).write_text(v4.recommendations_md(events), encoding="utf-8")
    Path(HUB_FILE).write_text(v5_hub_md(run_id, events, observations, health, iso_dates), encoding="utf-8")

    SOURCE_ACCURACY_JSON.write_text(json.dumps(accuracy, indent=2), encoding="utf-8")
    SOURCE_ACCURACY_MD.write_text(write_source_accuracy_md(accuracy), encoding="utf-8")
    MISSING_ALERT_JSON.write_text(json.dumps({"summary": expected_summary, "rows": expected_rows}, indent=2), encoding="utf-8")
    MISSING_ALERT_MD.write_text(missing_games_md(expected_summary, expected_rows), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "run_id": run_id,
        "generated_at_utc": now_iso(),
        "sources": allowed_sources(),
        "date_window": iso_dates,
        "free_only": True,
        "paid_sources_required": False,
        "counts": {
            "observations": len(observations),
            "reconciled_events": len(events),
            "women_events": len(womens),
            "final_women_events": len(finals),
            "manual_review": len(review),
            "graphics_ready": sum(1 for e in events if e.get("include_in_graphics")),
            "must_post": sum(1 for e in events if e.get("editorial_bucket") == "Must Post"),
            "strong_maybe": sum(1 for e in events if e.get("editorial_bucket") == "Strong Maybe"),
            "watchlist": sum(1 for e in events if e.get("editorial_bucket") == "Watchlist"),
            "carryover_archived": sum(1 for e in events if e.get("is_carryover") == "Yes"),
            "wnba_box_audit_rows": len(box_audit_rows),
            "duplicate_groups": len(duplicate_rows),
            "stale_observations": len(stale_rows),
            "expected_games": expected_summary.get("expected_games", 0),
            "missing_expected_games": expected_summary.get("missing", 0),
        },
        "source_health": health,
        "v5_audit_files": {
            "source_accuracy": SOURCE_ACCURACY_JSON.as_posix(),
            "duplicates": DUPLICATE_AUDIT.as_posix(),
            "stale": STALE_AUDIT.as_posix(),
            "missing_games": MISSING_ALERT_JSON.as_posix(),
        },
    }
    Path(MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    V5_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    V5_REPORT.write_text(report_md(run_id, manifest, accuracy), encoding="utf-8")

    print("Created Results Desk v5 outputs")
    print(json.dumps(manifest["counts"], indent=2))


def v5_hub_md(run_id: str, events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], iso_dates: List[str]) -> str:
    women = [e for e in events if e.get("gender_scope") == "women"]
    finals = [e for e in women if e.get("status_norm") == "final"]
    graphics = [e for e in events if e.get("include_in_graphics")]
    review = [e for e in events if e.get("manual_review") and e.get("gender_scope") == "women"]
    lines = [
        "# Her Sports Daily Results Desk v5 Hub",
        "",
        f"Run ID: `{run_id}`",
        f"Generated: `{now_iso()}`",
        f"Date window: `{', '.join(iso_dates)}`",
        "",
        "## Source strategy",
        "",
        "- Free/public sources only.",
        "- Active source: ESPN public WNBA scoreboard endpoint.",
        "- Optional fallback: local/manual seed CSVs.",
        "- Paid API keys are not required and are not read by v5.",
        "",
        "## Run summary",
        "",
        f"- Raw source observations: {len(observations)}",
        f"- Reconciled events: {len(events)}",
        f"- Women's events surfaced: {len(women)}",
        f"- Women's finals: {len(finals)}",
        f"- Graphics-ready results: {len(graphics)}",
        f"- Manual review items: {len(review)}",
        "",
        "## Accuracy gates",
        "",
        "- Duplicate groups are written to `duplicate_game_audit_v5.csv`.",
        "- Stale/out-of-window observations are written to `stale_source_audit_v5.csv`.",
        "- Expected-game fixtures, when provided, are checked in `missing_games_alert_v5.*`.",
        "- No player stats are invented. ESPN summary enrichment is review-only context.",
    ]
    return "\n".join(lines) + "\n"


def missing_games_md(summary: Dict[str, Any], rows: List[Dict[str, str]]) -> str:
    lines = [
        "# Missing Games Alert v5",
        "",
        f"Generated: `{now_iso()}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    if not summary.get("expected_fixture_file_present"):
        lines.extend([
            "## Status",
            "",
            "No expected-games fixture file was found. V5 can audit source coverage and duplicates, but cannot prove complete slate coverage without an expected-games fixture.",
            "Add `config/hsd_expected_games_v5.csv` with columns `date,league,home_team,away_team` when testing a known slate.",
        ])
    elif summary.get("missing", 0):
        lines.extend(["## Missing", ""])
        for row in rows:
            if row.get("matched") == "No":
                lines.append(f"- {row.get('date')} | {row.get('league')} | {row.get('away_team')} at {row.get('home_team')} | {row.get('reason')}")
    else:
        lines.extend(["## Status", "", "All expected games matched the current free-source observations."])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
