from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import read_csv, write_csv, write_json, write_text


VERSION = "hsd-wnba-source-quality-next-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_action_photo_source_quality_board_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_source_quality_next_v1"

TARGET_ROWS_CSV = REPO_ROOT / "data" / "asset_registry" / "action_photo_candidates" / "review_only_wnba_final_score_hero_action_photo_targets_v1.csv"
WNBA_TEAMS_CSV = REPO_ROOT / "data" / "asset_registry" / "wnba" / "teams.csv"
WNBA_ATHLETE_SOURCES_CSV = REPO_ROOT / "data" / "asset_registry" / "wnba" / "athlete_sources.csv"

SEED_CSV_NAME = "wnba_source_quality_next_seed.csv"
BOARD_CSV_NAME = "wnba_source_quality_next_board.csv"
REPORT_MD_NAME = "wnba_source_quality_next_report.md"
MANIFEST_JSON_NAME = "manifest.json"

CSV_FIELDS = [
    "source_family_id",
    "example_target_id",
    "source_family_label",
    "source_category",
    "source_quality_score",
    "source_quality_tier",
    "target_row_count",
    "focus_team_id",
    "focus_team_name",
    "focus_player_name",
    "focus_team_home_url",
    "focus_roster_url",
    "source_url_or_search_macro",
    "target_moment_type",
    "blocked_low_value_cues",
    "positive_signals",
    "risk_flags",
    "why_this_source_family_matters",
    "manual_next_action",
    "download_approved",
    "review_only",
    "publish_ready",
    "asset_downloads",
    "approval_state_change",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def slug(value: str) -> str:
    return clean(value).lower().replace("/", " ").replace("&", " and ")


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def output_root() -> Path:
    raw = clean(os.environ.get("HSD_RUN_OUTPUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_OUTPUT_DIR


def output_path(*parts: str) -> Path:
    return output_root().joinpath(*parts)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def one_by(rows: Iterable[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        value = clean(row.get(key))
        if value and value not in mapping:
            mapping[value] = row
    return mapping


def source_category_rank(source_category: str) -> tuple[int, str, list[str], list[str], str]:
    category = clean(source_category)
    if category == "official_league_gallery":
        return (
            95,
            "A_primary_source_lead",
            ["official-domain", "high-trust-team-context", "best-odds-for-clean-action-crop"],
            ["gallery-coverage-varies-by-game", "still-review-only"],
            "Check the official WNBA/team gallery and recap pages first; they are the strongest free public lead for clean game-action frames.",
        )
    if category == "editorial_wire":
        return (
            90,
            "A_primary_source_lead",
            ["wire-coverage-depth", "action-first-captures", "broad-game-coverage"],
            ["licensing-sensitive", "manual-verification-needed"],
            "Use wire coverage when the official pages are thin or the game needs sharper action specificity than a recap gallery provides.",
        )
    if category == "official_social":
        return (
            83,
            "B_strong_source_lead",
            ["team-controlled-posting", "celebration-heavy", "timely-publish-path"],
            ["caption-quality-varies", "crop-framing-can-be-tight"],
            "Check official team or league social posts when you want celebration, bench, or quick-turn action leads without leaving official channels.",
        )
    if category == "reputable_newsroom_gallery":
        return (
            77,
            "B_strong_source_lead",
            ["local-beat-gallery", "game-context", "often-action-first"],
            ["paywall-or-gallery-churn", "manual-review-needed"],
            "Local or reputable newsroom galleries can surface cleaner action frames than static roster pages when official galleries stall.",
        )
    return (
        68,
        "C_secondary_source_lead",
        ["public-portfolio", "often-action-heavy", "manual-source-quality-review"],
        ["rights-unclear-until-confirmed", "review-only-scouting-only"],
        "Public creator portfolios stay useful as a backup lead, but they need the most careful manual source-quality review before they ever inform any later decision.",
    )


def build_rows() -> list[dict[str, str]]:
    target_rows = read_csv_rows(TARGET_ROWS_CSV)
    teams_by_name = one_by(read_csv_rows(WNBA_TEAMS_CSV), "team_name")
    athlete_sources = one_by(read_csv_rows(WNBA_ATHLETE_SOURCES_CSV), "team_id")

    focus_team_name = clean(target_rows[0].get("team")) if target_rows else ""
    focus_player_name = clean(target_rows[0].get("player")) if target_rows else ""
    focus_team_row = teams_by_name.get(focus_team_name, {})
    focus_team_id = clean(focus_team_row.get("team_id"))
    focus_team_slug = clean(focus_team_row.get("slug")) or focus_team_id
    focus_team_home_url = f"https://www.wnba.com/team/{focus_team_slug.replace('_', '-')}" if focus_team_slug else ""
    focus_roster_url = clean(athlete_sources.get(focus_team_id, {}).get("roster_url"))

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in target_rows:
        grouped.setdefault(clean(row.get("source_family")), []).append(row)

    rows: list[dict[str, str]] = []
    for source_family, items in grouped.items():
        source_category = clean(items[0].get("source_category"))
        score, tier, positive_signals, risk_flags, rationale = source_category_rank(source_category)
        first = items[0]
        family_label = clean(source_family) or source_category
        search_macro = clean(first.get("source_url_or_search_macro"))
        blocked_cues = clean(first.get("low_value_cues"))
        rows.append(
            {
                "source_family_id": slug(family_label).replace(" ", "_"),
                "example_target_id": clean(first.get("target_id")),
                "source_family_label": family_label,
                "source_category": source_category,
                "source_quality_score": str(score),
                "source_quality_tier": tier,
                "target_row_count": str(len(items)),
                "focus_team_id": focus_team_id,
                "focus_team_name": focus_team_name,
                "focus_player_name": focus_player_name,
                "focus_team_home_url": focus_team_home_url,
                "focus_roster_url": focus_roster_url,
                "source_url_or_search_macro": search_macro,
                "target_moment_type": clean(first.get("target_moment_type")),
                "blocked_low_value_cues": blocked_cues,
                "positive_signals": "|".join(positive_signals),
                "risk_flags": "|".join(risk_flags),
                "why_this_source_family_matters": rationale,
                "manual_next_action": clean(first.get("next_action")) or "Open the family lead manually and verify source quality before any later review-only use.",
                "download_approved": "no",
                "review_only": "true",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "none",
            }
        )

    return sorted(rows, key=lambda row: (-int(row["source_quality_score"]), row["source_family_label"]))


def render_markdown(rows: list[dict[str, str]], generated_at: str) -> str:
    focus_team = clean(rows[0].get("focus_team_name")) if rows else ""
    focus_player = clean(rows[0].get("focus_player_name")) if rows else ""
    seed_target = clean(rows[0].get("example_target_id")) if rows else ""
    focus_home = clean(rows[0].get("focus_team_home_url")) if rows else ""
    focus_roster = clean(rows[0].get("focus_roster_url")) if rows else ""
    lines = [
        "# WNBA Source Quality Next Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only source-quality board for WNBA action-photo discovery. It ranks public, manual-safe source families that can surface better game-action leads without downloading, approving, or publishing anything.",
        "",
        "## Current Gap Context",
        "",
        f"- Seed target: `{seed_target}`",
        f"- Focus team: `{focus_team}`",
        f"- Focus player: `{focus_player}`",
        f"- Team home anchor: `{focus_home}`",
        f"- Roster anchor: `{focus_roster}`",
        "",
        "## Ranking",
        "",
        "| Rank | Source family | Category | Score | Tier | Search / anchor | Next action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows, start=1):
        search = row["source_url_or_search_macro"]
        anchor = row["focus_team_home_url"] or row["focus_roster_url"]
        lines.append(
            f"| {idx} | {row['source_family_label']} | {row['source_category']} | {row['source_quality_score']} | {row['source_quality_tier']} | {search or anchor} | {row['manual_next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- publish_ready=false",
            "- asset_downloads=false",
            "- approval_state_change=none",
            "- paid_apis=false",
            "- no_source_auto_enablement=true",
            "- no_publish_ready_lane=true",
        ]
    )
    return "\n".join(lines) + "\n"


def write_board_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    write_csv(path, rows, CSV_FIELDS)


def main() -> int:
    generated_at = now_iso()
    out_root = output_root()
    out_root.mkdir(parents=True, exist_ok=True)
    board_rows = build_rows()

    seed_csv = output_path(SEED_CSV_NAME)
    board_csv = output_path(BOARD_CSV_NAME)
    report_md = output_path(REPORT_MD_NAME)
    manifest_json = output_path(MANIFEST_JSON_NAME)

    write_board_csv(seed_csv, board_rows)
    write_board_csv(board_csv, board_rows)
    write_text(report_md, render_markdown(board_rows, generated_at), if_changed=False)

    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "status": "wnba_source_quality_next_board_ready" if board_rows else "wnba_source_quality_next_board_empty",
        "review_only": True,
        "seed_target_id": clean(board_rows[0].get("example_target_id")) if board_rows else "",
        "focus_team_name": clean(board_rows[0].get("focus_team_name")) if board_rows else "",
        "focus_player_name": clean(board_rows[0].get("focus_player_name")) if board_rows else "",
        "target_row_count": len(read_csv_rows(TARGET_ROWS_CSV)),
        "source_family_count": len(board_rows),
        "seed_csv_path": repo_rel(seed_csv),
        "board_csv_path": repo_rel(board_csv),
        "report_path": repo_rel(report_md),
        "guardrails": {
            "review_only": True,
            "download_approved": False,
            "publish_ready": False,
            "asset_downloads": False,
            "approval_state_change": False,
            "no_paid_apis": True,
            "no_source_auto_enablement": True,
            "no_publish_ready_lane": True,
        },
        "rows": board_rows,
    }
    write_json(manifest_json, manifest)

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "source_family_count": manifest["source_family_count"],
                "focus_team": manifest["focus_team_name"],
                "focus_player": manifest["focus_player_name"],
                "board_csv": board_csv.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
