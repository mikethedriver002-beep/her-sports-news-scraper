from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_csv, write_json, write_text


VERSION = "hsd-wnba-storm-visual-rank-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_storm_visual_rank_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_next_v1"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_storm_visual_rank_v1"
BOARD_INPUT_NAME = "wnba_storm_source_scout_board.csv"
INTAKE_INPUT_NAME = "wnba_storm_source_scout_intake.csv"
BOARD_CSV_NAME = "wnba_storm_visual_rank_board.csv"
INTAKE_CSV_NAME = "wnba_storm_visual_rank_intake.csv"
REPORT_MD_NAME = "wnba_storm_visual_rank_report.md"
HTML_NAME = "wnba_storm_visual_rank_board.html"
MANIFEST_JSON_NAME = "manifest.json"
REQUIRED_QUEUE_IDS = [f"WSFS{i:03d}" for i in range(1, 6)]

CSV_FIELDS = [
    "board_rank",
    "candidate_queue_id",
    "seed_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "identity_honesty",
    "visual_rank_score",
    "visual_review_priority",
    "crop_notes",
    "negative_space_notes",
    "carry_forward_prompt",
    "reject_prompt",
    "source_scout_rank",
    "source_scout_score",
    "source_scout_tier",
    "source_provenance_clarity",
    "identity_confidence",
    "manual_next_action",
    "review_only",
    "download_approved",
    "publish_ready",
    "asset_downloads",
    "approval_state_change",
    "publishing",
    "notes",
]

INTAKE_FIELDS = [
    "deck_item_id",
    "candidate_queue_id",
    "entity_id",
    "source_url",
    "candidate_image_url",
    "operator_decision",
    "operator_notes",
    "manual_reviewer",
    "reviewed_at_utc",
    "formal_intake_next_action",
    "review_only",
    "download_approved",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def repo_rel(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def output_root() -> Path:
    raw = clean(os.environ.get("HSD_RUN_OUTPUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_OUTPUT_DIR


def input_dir() -> Path:
    raw = clean(os.environ.get("HSD_WNBA_STORM_SOURCE_SCOUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_INPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def row_lookup(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        value = clean(row.get(key))
        if value and value not in out:
            out[value] = row
    return out


def truncate(text: str, max_len: int) -> str:
    value = clean(text)
    if len(value) <= max_len:
        return value
    return value[: max(0, max_len - 1)].rstrip() + "..."


def subject_name(entity_id: str) -> str:
    suffix = entity_id.rsplit("_", 1)[-1]
    if entity_id.endswith("skylar_diggins"):
        return "Skylar Diggins"
    if entity_id.endswith("dominique_malonga"):
        return "Dominique Malonga"
    if entity_id.endswith("erica_wheeler"):
        return "Erica Wheeler"
    if entity_id.endswith("nneka_ogwumike"):
        return "Nneka Ogwumike"
    if entity_id.endswith("gabby_williams"):
        return "Gabby Williams"
    return suffix.replace("_", " ").title()


def identity_honesty(board: dict[str, str], intake: dict[str, str]) -> tuple[str, str]:
    entity = clean(board.get("entity_id"))
    subject = subject_name(entity)
    haystack = f"{clean(board.get('image_alt'))} {clean(intake.get('evidence_summary'))}".lower()
    alt = clean(board.get("image_alt")).lower()
    subject_lower = subject.lower()
    if subject_lower in alt:
        return "subject_explicit_in_alt_text", f"Alt text names {subject}; inspect crop and image quality first."
    if subject_lower in haystack:
        return "subject_in_body_copy_only", f"Body copy names {subject}, but the image metadata is not direct enough to trust."
    return "team_context_only", f"Metadata does not clearly name {subject}; treat as wrong-person risk until manually confirmed."


def score_row(board: dict[str, str], intake: dict[str, str]) -> tuple[int, str, str]:
    score = 65
    alt = clean(board.get("image_alt")).lower()
    entity = clean(board.get("entity_id"))
    subject = subject_name(entity).lower()
    source_score = int(clean(board.get("score")) or "0")
    source_type = clean(board.get("source_type"))
    identity = clean(board.get("identity_confidence"))
    image_url = clean(board.get("candidate_image_url"))

    if source_type == "official_team_recap":
        score += 8
    if image_url:
        score += 8
    if source_score >= 90:
        score += 8
    elif source_score >= 80:
        score += 4
    if identity == "strong_context":
        score += 6
    elif identity == "medium":
        score += 2
    if subject in alt:
        score += 12
    if "skylar diggins" in alt and subject != "skylar diggins":
        score -= 4
    if "nneka ogwumike" in alt and subject != "nneka ogwumike":
        score -= 4
    if "gabby williams" in alt and subject != "gabby williams":
        score -= 4
    if "erica wheeler" in alt and subject != "erica wheeler":
        score -= 3
    if len(alt) > 180:
        score -= 4
    if len(alt) > 260:
        score -= 3

    honesty, _ = identity_honesty(board, intake)
    if honesty == "subject_in_body_copy_only":
        score -= 3
    elif honesty == "team_context_only":
        score -= 12

    score = max(0, min(100, score))
    if score >= 94:
        priority = "P1_visual_review_now"
    elif score >= 84:
        priority = "P2_manual_confirm"
    else:
        priority = "P3_hold_or_fast_reject"
    return score, priority, honesty


def crop_note(row: dict[str, str], honesty: str) -> str:
    if honesty == "subject_explicit_in_alt_text":
        return "Best metadata fit; still verify the remote image is a real action frame with the subject dominant."
    if honesty == "subject_in_body_copy_only":
        return "Open carefully: the subject may be in the story, not necessarily the image."
    return "High wrong-person risk; carry forward only if visual identity is obvious."


def negative_space_note(row: dict[str, str], score: int) -> str:
    if score >= 94:
        return "Likely worth 4:5 inspection, but metadata cannot prove clean side/top space."
    if score >= 84:
        return "Check for crowding and multi-player overlap before any formal intake."
    return "Do not spend time unless the image is unexpectedly clean and solo."


def carry_forward_prompt(row: dict[str, str], honesty: str) -> str:
    subject = subject_name(clean(row.get("entity_id")))
    if honesty == "subject_explicit_in_alt_text":
        return f"Carry forward if {subject} is visually dominant and the crop has premium 4:5 space."
    if honesty == "subject_in_body_copy_only":
        return f"Carry forward only if the remote image clearly shows {subject}, not just a Storm team scene."
    return f"Carry forward only with unmistakable visual identity for {subject}."


def reject_prompt(row: dict[str, str], honesty: str) -> str:
    if honesty == "team_context_only":
        return "Reject if the subject is not obvious immediately; avoid creating wrong-person review debt."
    return "Reject if wrong-player, group-heavy, too tight, or visually weak for WNBA graphics."


def build_rows(board_rows: list[dict[str, str]], intake_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    board_by_id = row_lookup(board_rows, "candidate_queue_id")
    intake_by_id = row_lookup(intake_rows, "candidate_queue_id")
    missing = [candidate_id for candidate_id in REQUIRED_QUEUE_IDS if candidate_id not in board_by_id or candidate_id not in intake_by_id]
    if missing:
        raise ValueError(f"Missing required Storm rows: {', '.join(missing)}")

    rows: list[dict[str, str]] = []
    for source_rank, candidate_id in enumerate(REQUIRED_QUEUE_IDS, start=1):
        board = board_by_id[candidate_id]
        intake = intake_by_id[candidate_id]
        score, priority, honesty = score_row(board, intake)
        honesty_value, honesty_note = identity_honesty(board, intake)
        rows.append(
            {
                "board_rank": str(source_rank),
                "candidate_queue_id": candidate_id,
                "seed_id": clean(board.get("seed_id")),
                "entity_id": clean(board.get("entity_id")),
                "source_type": clean(board.get("source_type")),
                "source_url": clean(board.get("source_url")),
                "candidate_image_url": clean(board.get("candidate_image_url")),
                "image_alt": clean(board.get("image_alt")),
                "identity_honesty": honesty_value,
                "visual_rank_score": str(score),
                "visual_review_priority": priority,
                "crop_notes": crop_note(board, honesty),
                "negative_space_notes": negative_space_note(board, score),
                "carry_forward_prompt": carry_forward_prompt(board, honesty),
                "reject_prompt": reject_prompt(board, honesty),
                "source_scout_rank": clean(board.get("board_rank")),
                "source_scout_score": clean(board.get("score")),
                "source_scout_tier": clean(board.get("candidate_quality_tier")),
                "source_provenance_clarity": clean(board.get("source_provenance_clarity")),
                "identity_confidence": clean(board.get("identity_confidence")),
                "manual_next_action": clean(intake.get("manual_next_action")),
                "review_only": "true",
                "download_approved": "no",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publishing": "false",
                "notes": f"{clean(board.get('notes'))} | visual_rank={score}; identity_honesty={honesty_value}; {honesty_note}",
            }
        )
    rows.sort(key=lambda row: (-int(row["visual_rank_score"]), int(row["source_scout_rank"])))
    for rank, row in enumerate(rows, start=1):
        row["board_rank"] = str(rank)
    return rows


def build_intake_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "deck_item_id": f"storm_visual_rank_{row['candidate_queue_id'].lower()}",
            "candidate_queue_id": row["candidate_queue_id"],
            "entity_id": row["entity_id"],
            "source_url": row["source_url"],
            "candidate_image_url": row["candidate_image_url"],
            "operator_decision": "",
            "operator_notes": "",
            "manual_reviewer": "",
            "reviewed_at_utc": "",
            "formal_intake_next_action": row["manual_next_action"],
            "review_only": "true",
            "download_approved": "no",
            "asset_downloads": "false",
            "approval_state_change": "false",
            "publish_ready": "false",
            "publishing": "false",
        }
        for row in rows
    ]


def render_report(rows: list[dict[str, str]], generated_at: str, board_csv: Path, intake_csv: Path, html_path: Path) -> str:
    lines = [
        "# WNBA Storm Visual Rank Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only visual-rank board for WSFS001-WSFS005. It references remote candidate image URLs for manual review and does not download, approve, move, or publish anything.",
        "",
        "## Outputs",
        "",
        f"- Board CSV: `{repo_rel(board_csv)}`",
        f"- Intake CSV: `{repo_rel(intake_csv)}`",
        f"- HTML board: `{repo_rel(html_path)}`",
        "",
        "## Strongest Manual Review Rows",
        "",
        "| Rank | Candidate | Score | Identity honesty | Carry-forward cue | Reject cue |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:3]:
        lines.append(
            f"| {row['board_rank']} | {row['candidate_queue_id']} | {row['visual_rank_score']} | {row['identity_honesty']} | {truncate(row['carry_forward_prompt'], 90)} | {truncate(row['reject_prompt'], 90)} |"
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
            "- approval_state_change=false",
            "- publishing=false",
            "- no paid APIs",
            "- no source auto-enablement",
            "- no downloads",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(rows: list[dict[str, str]], generated_at: str, board_csv: Path, intake_csv: Path) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
      <article class="card">
        <div class="card-head">
          <div>
            <div class="badge">Rank {html.escape(row['board_rank'])}</div>
            <h2>{html.escape(row['candidate_queue_id'])}</h2>
            <p>{html.escape(row['entity_id'])} · score {html.escape(row['visual_rank_score'])}</p>
          </div>
          <div class="score">{html.escape(row['identity_honesty'])}</div>
        </div>
        <div class="image-wrap">
          <img src="{html.escape(row['candidate_image_url'])}" alt="{html.escape(row['image_alt'])}" loading="lazy">
        </div>
        <dl class="details">
          <div><dt>Source</dt><dd><a href="{html.escape(row['source_url'])}" target="_blank" rel="noreferrer">{html.escape(row['source_url'])}</a></dd></div>
          <div><dt>Image URL</dt><dd><a href="{html.escape(row['candidate_image_url'])}" target="_blank" rel="noreferrer">{html.escape(row['candidate_image_url'])}</a></dd></div>
          <div><dt>Alt evidence</dt><dd>{html.escape(row['image_alt'])}</dd></div>
          <div><dt>Identity</dt><dd>{html.escape(row['identity_honesty'])}</dd></div>
          <div><dt>Crop note</dt><dd>{html.escape(row['crop_notes'])}</dd></div>
          <div><dt>Negative space</dt><dd>{html.escape(row['negative_space_notes'])}</dd></div>
          <div><dt>Carry forward</dt><dd>{html.escape(row['carry_forward_prompt'])}</dd></div>
          <div><dt>Reject</dt><dd>{html.escape(row['reject_prompt'])}</dd></div>
        </dl>
      </article>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WNBA Storm Visual Rank Board</title>
  <style>
    :root {{ color-scheme: dark; --bg: #0d1117; --panel: #141b24; --line: #2b3442; --ink: #eff4fb; --muted: #aeb8c6; --accent: #6bd6ff; --good: #64d19d; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: linear-gradient(180deg, #0f1b25 0, #0d1117 28rem); color: var(--ink); font: 15px/1.5 Arial, Helvetica, sans-serif; }}
    header {{ padding: 24px clamp(18px, 4vw, 40px) 16px; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 40px); letter-spacing: 0; }}
    header p {{ margin: 0; max-width: 1100px; color: var(--muted); }}
    .meta-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }}
    .pill {{ border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px; color: var(--muted); }}
    main {{ padding: 20px clamp(18px, 4vw, 40px) 40px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
    .card {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(20, 27, 36, .92); overflow: hidden; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 12px; padding: 14px; border-bottom: 1px solid var(--line); }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: rgba(107, 214, 255, .12); color: var(--accent); border: 1px solid rgba(107, 214, 255, .32); font-size: 12px; font-weight: 700; }}
    h2 {{ margin: 8px 0 2px; font-size: 18px; letter-spacing: 0; }}
    .card-head p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .score {{ min-width: 120px; text-align: right; color: var(--good); font-weight: 800; font-size: 13px; overflow-wrap: anywhere; }}
    .image-wrap {{ background: #0a0f15; border-bottom: 1px solid var(--line); }}
    .image-wrap img {{ display: block; width: 100%; max-height: 320px; object-fit: cover; background: #0a0f15; }}
    .details {{ display: grid; gap: 0; margin: 0; padding: 10px 14px 14px; }}
    .details > div {{ display: grid; grid-template-columns: 132px minmax(0, 1fr); gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,.06); }}
    .details > div:last-child {{ border-bottom: 0; }}
    dt {{ color: #d8e0eb; font-weight: 700; }}
    dd {{ margin: 0; color: var(--muted); overflow-wrap: anywhere; }}
    a {{ color: #9cc6ff; }}
  </style>
</head>
<body>
  <header>
    <h1>WNBA Storm Visual Rank Board</h1>
    <p>Review-only enrichment board for WSFS001-WSFS005. It separates direct subject metadata from body-copy or team-context rows without downloading assets.</p>
    <div class="meta-row">
      <div class="pill">Board CSV: {html.escape(repo_rel(board_csv))}</div>
      <div class="pill">Intake CSV: {html.escape(repo_rel(intake_csv))}</div>
      <div class="pill">Generated: {html.escape(generated_at)}</div>
      <div class="pill">review_only=true</div>
      <div class="pill">download_approved=no</div>
      <div class="pill">no downloads</div>
    </div>
  </header>
  <main><section class="grid">{''.join(cards)}</section></main>
</body>
</html>
"""


def build_packet(*, board_csv: Path, intake_csv: Path, output_dir: Path) -> dict[str, Any]:
    board_rows = read_csv_rows(board_csv)
    intake_rows = read_csv_rows(intake_csv)
    rows = build_rows(board_rows, intake_rows)
    generated_at = now_iso()
    output_dir.mkdir(parents=True, exist_ok=True)
    board_out = output_dir / BOARD_CSV_NAME
    intake_out = output_dir / INTAKE_CSV_NAME
    report_out = output_dir / REPORT_MD_NAME
    html_out = output_dir / HTML_NAME
    manifest_out = output_dir / MANIFEST_JSON_NAME

    write_csv(board_out, rows, CSV_FIELDS)
    write_csv(intake_out, build_intake_rows(rows), INTAKE_FIELDS)
    write_text(report_out, render_report(rows, generated_at, board_out, intake_out, html_out))
    write_text(html_out, render_html(rows, generated_at, board_out, intake_out), if_changed=False)
    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "status": "wnba_storm_visual_rank_ready" if rows else "wnba_storm_visual_rank_empty",
        "review_only": True,
        "board_csv_path": repo_rel(board_out),
        "intake_csv_path": repo_rel(intake_out),
        "report_path": repo_rel(report_out),
        "html_path": repo_rel(html_out),
        "row_count": len(rows),
        "candidate_queue_ids": [row["candidate_queue_id"] for row in rows],
        "guardrails": {
            "review_only": True,
            "download_approved": False,
            "publish_ready": False,
            "asset_downloads": False,
            "approval_state_change": False,
            "publishing": False,
            "no_paid_apis": True,
            "no_source_auto_enablement": True,
            "no_downloads": True,
        },
        "rows": rows,
    }
    write_json(manifest_out, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the WNBA Storm visual-rank review board.")
    parser.add_argument("--board-csv", default=(input_dir() / BOARD_INPUT_NAME).as_posix())
    parser.add_argument("--intake-csv", default=(input_dir() / INTAKE_INPUT_NAME).as_posix())
    parser.add_argument("--output-dir", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else output_root()
    manifest = build_packet(board_csv=Path(args.board_csv), intake_csv=Path(args.intake_csv), output_dir=output_dir)
    print(json.dumps({"status": manifest["status"], "row_count": manifest["row_count"], "output_dir": output_dir.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
