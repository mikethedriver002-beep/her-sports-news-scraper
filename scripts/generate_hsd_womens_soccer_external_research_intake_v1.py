from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text


VERSION = "hsd-womens-soccer-external-research-intake-v1-review-only"
ROOT = Path("data/asset_registry/womens_soccer/external_research")
NWSL_INPUT = ROOT / "nwsl_correction_enrichment_report.csv"
EUROPE_INPUT = ROOT / "europe_official_source_map.csv"
OUT_MD = output_path(ROOT / "womens_soccer_external_research_intake_board.md")
OUT_CSV = output_path(ROOT / "womens_soccer_external_research_intake_board.csv")
OUT_JSON = output_path(ROOT / "womens_soccer_external_research_intake_board.json")

BOARD_FIELDS = [
    "research_lane",
    "operator_bucket",
    "source_priority",
    "league_id",
    "league_name",
    "team_name",
    "player_name",
    "issue_type",
    "operator_action",
    "source_url",
    "source_domain",
    "official_status",
    "confidence",
    "operator_verify_required",
    "safe_next_action",
    "notes",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "publishing",
    "paid_apis",
]

NWSL_P0_VERIFY_ISSUES = {
    "expired_replacement_player_candidate",
    "loan_duplicate_needs_status_metadata",
    "loan_status_missing",
    "missing_player_profile_candidate",
    "stale_or_short_term_candidate",
    "stale_player_candidate",
    "stale_team_assignment_duplicate_identity",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def count_by(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, int]:
    return dict(sorted(Counter(clean(row.get(field)) or "blank" for row in rows).items()))


def nwsl_bucket(row: Mapping[str, str]) -> str:
    priority = clean(row.get("source_priority"))
    issue_type = clean(row.get("issue_type"))
    official_status = clean(row.get("official_status"))
    confidence = clean(row.get("confidence")).lower()
    if priority == "P3" or official_status.startswith("non_official") or "gray_area" in issue_type or confidence == "low":
        return "p3_gray_area_manual_verification_only"
    if priority == "P0" and issue_type in NWSL_P0_VERIFY_ISSUES:
        return "p0_nwsl_operator_verify_first"
    return "p1_metadata_candidate_only"


def europe_bucket(row: Mapping[str, str]) -> str:
    official_status = clean(row.get("official_status"))
    verify_required = clean(row.get("operator_verify_required")).lower()
    if not official_status.startswith("official"):
        return "europe_gray_area_manual_verification_only"
    if verify_required == "yes":
        return "europe_operator_verify_required"
    return "europe_official_no_verify_metadata_candidate"


def safe_next_action(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "p0_nwsl_operator_verify_first":
        return "Review official roster/transaction metadata manually before any later human-edited candidate-state change."
    if bucket == "p1_metadata_candidate_only":
        return "Treat as source/profile metadata candidate only; enrich review notes after manual source check."
    if bucket == "p3_gray_area_manual_verification_only":
        return "Park as gray-area lead; do not treat as official roster confirmation without official NWSL/team source."
    if bucket == "europe_official_no_verify_metadata_candidate":
        return "Use as official source-map candidate for future manual player research; no asset action."
    if bucket == "europe_operator_verify_required":
        return "Verify source page manually before using for player-level candidate intake."
    return "Manual research only; no approval, download, or candidate-state writeback."


def guardrail_fields() -> Dict[str, str]:
    return {
        "review_only": "true",
        "approval_state_change": "false",
        "candidate_state_change": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "publish_ready": "false",
        "publishing": "false",
        "paid_apis": "false",
    }


def board_rows(nwsl_rows: Iterable[Mapping[str, str]], europe_rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for row in nwsl_rows:
        bucket = nwsl_bucket(row)
        output.append(
            {
                "research_lane": "nwsl_correction_enrichment",
                "operator_bucket": bucket,
                "source_priority": clean(row.get("source_priority")),
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "team_name": clean(row.get("team_id_or_name")),
                "player_name": clean(row.get("player_name_if_applicable")),
                "issue_type": clean(row.get("issue_type")),
                "operator_action": clean(row.get("operator_action")),
                "source_url": clean(row.get("evidence_url")),
                "source_domain": clean(row.get("source_domain")),
                "official_status": clean(row.get("official_status")),
                "confidence": clean(row.get("confidence")),
                "operator_verify_required": "yes",
                "safe_next_action": safe_next_action(row, bucket),
                "notes": clean(row.get("notes")),
                **guardrail_fields(),
            }
        )
    for row in europe_rows:
        bucket = europe_bucket(row)
        output.append(
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": bucket,
                "source_priority": clean(row.get("source_priority")),
                "league_id": clean(row.get("league_id")),
                "league_name": clean(row.get("league_name")),
                "team_name": clean(row.get("team_name")),
                "player_name": "",
                "issue_type": "official_source_map",
                "operator_action": "source_metadata_review_only",
                "source_url": clean(row.get("roster_url_if_available")) or clean(row.get("source_url")),
                "source_domain": clean(row.get("source_domain")),
                "official_status": clean(row.get("official_status")),
                "confidence": clean(row.get("confidence")),
                "operator_verify_required": clean(row.get("operator_verify_required")) or "yes",
                "safe_next_action": safe_next_action(row, bucket),
                "notes": clean(row.get("freshness_note")) or clean(row.get("rights_or_usage_note")),
                **guardrail_fields(),
            }
        )
    return output


def render_markdown(rows: List[Mapping[str, str]], nwsl_rows: List[Mapping[str, str]], europe_rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "operator_bucket")
    nwsl_issue_counts = count_by(nwsl_rows, "issue_type")
    europe_league_counts = count_by(europe_rows, "league_id")
    europe_verify_counts = count_by(europe_rows, "operator_verify_required")
    lines = [
        "# Women's Soccer External Research Intake Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only intake board for external ChatGPT Pro research. These rows are advisory metadata candidates only. This packet does not download images, approve assets, write `headshot.png`, create `.approved` markers, change current candidate state, move files into publish-ready lanes, publish, or use paid APIs.",
        "",
        "## Summary",
        "",
        f"- NWSL research rows: `{len(nwsl_rows)}`",
        f"- Europe source-map rows: `{len(europe_rows)}`",
        f"- Combined board rows: `{len(rows)}`",
        "- Source CSVs: `nwsl_correction_enrichment_report.csv`, `europe_official_source_map.csv`",
        "- Board CSV: `womens_soccer_external_research_intake_board.csv`",
        "",
        "## Operator Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## NWSL First",
        "",
        "- P0 rows: verify duplicate/stale team assignments, loans, missing official roster candidates, expired/short-term holds, and stale candidates against official NWSL/team sources before any later human-edited intake change.",
        "- P1 rows: source/profile enrichment metadata only.",
        "- P3 rows: park gray-area or non-official leads for manual verification only. The Sam Kerr/Gotham Reuters row is not current official roster confirmation.",
        "",
        "### NWSL Issue Counts",
        "",
    ]
    lines.extend(f"- {issue}: `{count}`" for issue, count in nwsl_issue_counts.items())
    lines += [
        "",
        "## Europe Source Map",
        "",
        "- Official/no-verify rows are source-map candidates for later manual player research only.",
        "- `operator_verify_required=yes` rows must be checked by a human before player-level candidate intake.",
        "- Gray-area/non-official backups are parked and cannot be treated as official roster confirmation.",
        "",
        "### Europe League Counts",
        "",
    ]
    lines.extend(f"- {league}: `{count}`" for league, count in europe_league_counts.items())
    lines += [
        "",
        "### Europe Verify Counts",
        "",
    ]
    lines.extend(f"- {key}: `{count}`" for key, count in europe_verify_counts.items())
    lines += [
        "",
        "## Safe Next Action",
        "",
        "Use this board to decide which source/roster metadata rows need manual verification first. Do not write current roster/candidate state from this artifact. A later human-edited intake must explicitly authorize any registry change.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    nwsl_rows = read_csv(NWSL_INPUT)
    europe_rows = read_csv(EUROPE_INPUT)
    rows = board_rows(nwsl_rows, europe_rows)
    write_csv(OUT_CSV, rows, BOARD_FIELDS)
    write_text(OUT_MD, render_markdown(rows, nwsl_rows, europe_rows, generated_at))
    manifest = {
        "version": VERSION,
        "status": "external_research_intake_ready",
        "generated_at_utc": generated_at,
        "nwsl_rows": len(nwsl_rows),
        "europe_rows": len(europe_rows),
        "board_rows": len(rows),
        "operator_bucket_counts": count_by(rows, "operator_bucket"),
        "nwsl_issue_counts": count_by(nwsl_rows, "issue_type"),
        "nwsl_source_priority_counts": count_by(nwsl_rows, "source_priority"),
        "nwsl_official_status_counts": count_by(nwsl_rows, "official_status"),
        "nwsl_confidence_counts": count_by(nwsl_rows, "confidence"),
        "europe_league_counts": count_by(europe_rows, "league_id"),
        "europe_source_priority_counts": count_by(europe_rows, "source_priority"),
        "europe_official_status_counts": count_by(europe_rows, "official_status"),
        "europe_operator_verify_counts": count_by(europe_rows, "operator_verify_required"),
        "europe_confidence_counts": count_by(europe_rows, "confidence"),
        "gray_area_rows": sum(1 for row in rows if "gray_area" in clean(row.get("operator_bucket"))),
        "sam_kerr_reuters_gray_area_only": any(
            clean(row.get("player_name")) == "Sam Kerr"
            and "reuters" in clean(row.get("source_domain")).lower()
            and clean(row.get("operator_bucket")) == "p3_gray_area_manual_verification_only"
            for row in rows
        ),
        "input_csvs": [NWSL_INPUT.as_posix(), EUROPE_INPUT.as_posix()],
        "board_md": OUT_MD.as_posix(),
        "board_csv": OUT_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "paid_apis": False,
    }
    write_json(OUT_JSON, manifest)
    print(json.dumps({"version": VERSION, "status": manifest["status"], "nwsl_rows": len(nwsl_rows), "europe_rows": len(europe_rows), "board": OUT_MD.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
