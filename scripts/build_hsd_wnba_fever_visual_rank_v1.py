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


VERSION = "hsd-wnba-fever-visual-rank-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_fever_visual_rank_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_fever_source_scout_v1"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_fever_visual_rank_v1"
BOARD_INPUT_NAME = "wnba_fever_source_scout_board.csv"
INTAKE_INPUT_NAME = "wnba_fever_source_scout_intake.csv"
BOARD_CSV_NAME = "wnba_fever_visual_rank_board.csv"
INTAKE_CSV_NAME = "wnba_fever_visual_rank_intake.csv"
REPORT_MD_NAME = "wnba_fever_visual_rank_report.md"
HTML_NAME = "wnba_fever_visual_rank_board.html"
MANIFEST_JSON_NAME = "manifest.json"
REQUIRED_QUEUE_IDS = [f"WFFS{i:03d}" for i in range(1, 6)]

CSV_FIELDS = [
    "board_rank",
    "candidate_queue_id",
    "seed_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "evidence_excerpt",
    "identity_honesty",
    "crop_notes",
    "negative_space_notes",
    "carry_forward_prompt",
    "reject_prompt",
    "visual_rank_score",
    "source_domain",
    "source_family_id",
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
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def output_root() -> Path:
    raw = clean(os.environ.get("HSD_RUN_OUTPUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_OUTPUT_DIR


def input_dir() -> Path:
    raw = clean(os.environ.get("HSD_WNBA_FEVER_SOURCE_SCOUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_INPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: Iterable[dict[str, str]], fields: list[str]) -> None:
    write_csv(path, rows, fields)


def truncate(text: str, max_len: int) -> str:
    value = clean(text)
    if len(value) <= max_len:
        return value
    return value[: max(0, max_len - 1)].rstrip() + "..."


def row_lookup(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        value = clean(row.get(key))
        if value and value not in out:
            out[value] = row
    return out


def identity_honesty_note(board: dict[str, str], intake: dict[str, str]) -> tuple[str, str]:
    image_alt = clean(board.get("image_alt"))
    evidence_excerpt = clean(intake.get("evidence_summary"))
    source_type = clean(board.get("source_type"))
    if "kelsey mitchell" in image_alt.lower():
        return "subject_explicit_in_alt_text", "Alt text names the subject directly, so the source is easy to judge without guesswork."
    if "kelsey mitchell" in evidence_excerpt.lower():
        return "subject_in_body_copy_only", "The body copy names the subject, but the visible image metadata is less direct."
    if source_type == "official_team_story":
        return "team_story_context_only", "This reads like a team story first, so the subject needs a stricter visual check."
    return "subject_context_only", "The metadata points at the right lane, but the subject still needs a visual confirm."


def crop_note(board: dict[str, str], intake: dict[str, str], score: int) -> str:
    image_alt = clean(board.get("image_alt"))
    evidence_excerpt = clean(intake.get("evidence_summary"))
    alt_len = len(image_alt)
    if score >= 95:
        return "Likely the easiest 4:5 carry-forward read; still confirm the subject stays dominant and not chopped."
    if "caitlin clark" in evidence_excerpt.lower() and "kelsey mitchell" in evidence_excerpt.lower():
        return "Multi-player recap context may create a busy crop; check whether Kelsey still owns the frame."
    if alt_len > 150:
        return "Long caption proxy suggests a crowded top half; verify headroom, shoulders, and no broadcast clutter."
    if alt_len > 110:
        return "Probably usable, but confirm the crop does not spend too much space on surrounding players or text."
    return "Clean metadata read; verify the subject lands in a comfortable 4:5 crop with room for edits if needed."


def negative_space_note(board: dict[str, str], intake: dict[str, str], score: int) -> str:
    source_type = clean(board.get("source_type"))
    evidence_excerpt = clean(intake.get("evidence_summary"))
    if source_type == "official_team_story":
        return "Story copy may leave less open field around the subject; confirm the frame has enough breathing room for a first-choice crop."
    if "30-point" in evidence_excerpt.lower() or "first victory" in evidence_excerpt.lower():
        return "Game recap energy usually means action is present, but the metadata still cannot prove open negative space."
    if score >= 95:
        return "Most likely the cleanest lane for negative space, though the browser image still needs the final visual check."
    return "Metadata-only proxy: look for open court, jersey space, and a crop that can take text later if needed."


def carry_forward_prompt(row: dict[str, str], honesty: str) -> str:
    subject = "Kelsey Mitchell"
    if honesty == "subject_in_body_copy_only":
        return f"Carry forward only if the remote image shows {subject} as the primary subject and the crop feels clean at 4:5."
    if honesty == "team_story_context_only":
        return f"Carry forward only if the remote image clearly resolves to {subject} instead of a generic team-context frame."
    return f"Carry forward if the remote image is a clean {subject} action lead with enough breathing room for a 4:5 crop."


def reject_prompt(row: dict[str, str], honesty: str) -> str:
    source_type = clean(row.get("source_type"))
    if source_type == "official_team_story":
        return "Reject if it is really a team-story frame, wrong player, or a crowded context shot that buries the subject."
    if honesty == "subject_in_body_copy_only":
        return "Reject if the image turns out to be a caption-heavy team scene, wrong person, or too tight for a lead."
    return "Reject if the image is wrong-player, group-heavy, or lacks enough clean space to function as a lead."


def score_row(board: dict[str, str], intake: dict[str, str]) -> tuple[int, str, str, str]:
    score = 72
    source_type = clean(board.get("source_type"))
    image_alt = clean(board.get("image_alt"))
    evidence_excerpt = clean(intake.get("evidence_summary"))
    source_url = clean(board.get("source_url"))
    candidate_image_url = clean(board.get("candidate_image_url"))
    if source_type == "official_team_recap":
        score += 10
    elif source_type == "official_team_story":
        score += 7
    if candidate_image_url:
        score += 8
    if "kelsey mitchell" in image_alt.lower():
        score += 10
    if "kelsey mitchell" in evidence_excerpt.lower():
        score += 5
    if "aliyah boston" in image_alt.lower() and "kelsey mitchell" not in image_alt.lower():
        score -= 6
    if "caitlin clark" in image_alt.lower() and "kelsey mitchell" not in image_alt.lower():
        score -= 4
    if len(image_alt) > 150:
        score -= 5
    if len(image_alt) > 220:
        score -= 4
    if "fever.wnba.com/news/" in source_url:
        score += 2
    if score >= 95:
        tier = "A_primary_visual_lead"
    elif score >= 88:
        tier = "B_strong_visual_lead"
    else:
        tier = "C_review_only_visual_lead"
    honesty, honesty_note = identity_honesty_note(board, intake)
    return max(0, min(100, score)), tier, honesty, honesty_note


def build_rows(board_rows: list[dict[str, str]], intake_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    board_by_id = row_lookup(board_rows, "candidate_queue_id")
    intake_by_id = row_lookup(intake_rows, "candidate_queue_id")
    missing = [candidate_id for candidate_id in REQUIRED_QUEUE_IDS if candidate_id not in board_by_id or candidate_id not in intake_by_id]
    if missing:
        raise ValueError(f"Missing required Fever rows: {', '.join(missing)}")

    rows: list[dict[str, str]] = []
    for scout_rank, candidate_id in enumerate(REQUIRED_QUEUE_IDS, start=1):
        board = board_by_id[candidate_id]
        intake = intake_by_id[candidate_id]
        score, tier, honesty, honesty_note = score_row(board, intake)
        evidence_excerpt = truncate(intake.get("evidence_summary", ""), 240)
        rows.append(
            {
                "board_rank": str(scout_rank),
                "candidate_queue_id": candidate_id,
                "seed_id": clean(board.get("seed_id")),
                "entity_id": clean(board.get("entity_id")),
                "source_type": clean(board.get("source_type")),
                "source_url": clean(board.get("source_url")),
                "candidate_image_url": clean(board.get("candidate_image_url")),
                "image_alt": clean(board.get("image_alt")),
                "evidence_excerpt": evidence_excerpt,
                "identity_honesty": honesty,
                "crop_notes": crop_note(board, intake, score),
                "negative_space_notes": negative_space_note(board, intake, score),
                "carry_forward_prompt": carry_forward_prompt(board, honesty),
                "reject_prompt": reject_prompt(board, honesty),
                "visual_rank_score": str(score),
                "source_domain": clean(board.get("source_domain")),
                "source_family_id": clean(board.get("source_family_id")),
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
                "notes": f"{clean(board.get('notes'))} | visual_rank={score}; identity_honesty={honesty}; {honesty_note}",
            }
        )
    rows.sort(key=lambda row: (-int(row["visual_rank_score"]), int(row["source_scout_rank"])))
    for rank, row in enumerate(rows, start=1):
        row["board_rank"] = str(rank)
    return rows


def build_intake_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    intake_rows: list[dict[str, str]] = []
    for row in rows:
        intake_rows.append(
            {
                "deck_item_id": f"fever_visual_rank_{row['candidate_queue_id'].lower()}",
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
        )
    return intake_rows


def render_report(rows: list[dict[str, str]], generated_at: str, board_csv: Path, intake_csv: Path, html_path: Path) -> str:
    strongest = rows[:3]
    lines = [
        "# WNBA Fever Visual Rank Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only visual-rank board for WFFS001-WFFS005. It keeps the lane metadata-first, references the remote image URL in HTML for manual review, and does not download, approve, move, or publish anything.",
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
    for row in strongest:
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
                <p>{html.escape(row['source_family_id'])} · {html.escape(row['source_type'])} · score {html.escape(row['visual_rank_score'])}</p>
              </div>
              <div class="score">{html.escape(row['identity_honesty'])}</div>
            </div>
            <div class="image-wrap">
              <img src="{html.escape(row['candidate_image_url'])}" alt="{html.escape(row['image_alt'])}" loading="lazy">
            </div>
            <dl class="details">
              <div><dt>Source</dt><dd><a href="{html.escape(row['source_url'])}" target="_blank" rel="noreferrer">{html.escape(row['source_url'])}</a></dd></div>
              <div><dt>Image URL</dt><dd><a href="{html.escape(row['candidate_image_url'])}" target="_blank" rel="noreferrer">{html.escape(row['candidate_image_url'])}</a></dd></div>
              <div><dt>Alt / caption evidence</dt><dd>{html.escape(row['image_alt'])}</dd></div>
              <div><dt>Evidence excerpt</dt><dd>{html.escape(row['evidence_excerpt'])}</dd></div>
              <div><dt>Identity honesty</dt><dd>{html.escape(row['identity_honesty'])}</dd></div>
              <div><dt>Crop note</dt><dd>{html.escape(row['crop_notes'])}</dd></div>
              <div><dt>Negative-space note</dt><dd>{html.escape(row['negative_space_notes'])}</dd></div>
              <div><dt>Carry forward</dt><dd>{html.escape(row['carry_forward_prompt'])}</dd></div>
              <div><dt>Reject</dt><dd>{html.escape(row['reject_prompt'])}</dd></div>
              <div><dt>Manual next action</dt><dd>{html.escape(row['manual_next_action'])}</dd></div>
            </dl>
          </article>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WNBA Fever Visual Rank Board</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0d1117;
      --panel: #141b24;
      --panel-2: #101720;
      --ink: #eff4fb;
      --muted: #aeb8c6;
      --line: #2b3442;
      --accent: #e6b95b;
      --good: #64d19d;
      --bad: #f16f6f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #111826 0, #0d1117 28rem);
      color: var(--ink);
      font: 15px/1.5 Arial, Helvetica, sans-serif;
    }}
    header {{
      padding: 24px clamp(18px, 4vw, 40px) 16px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 40px);
      letter-spacing: 0;
    }}
    header p {{
      margin: 0;
      max-width: 1100px;
      color: var(--muted);
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(255,255,255,.03);
      color: var(--muted);
      white-space: nowrap;
    }}
    main {{
      display: grid;
      gap: 18px;
      padding: 18px clamp(18px, 4vw, 40px) 30px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      align-items: start;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(20, 27, 36, .96);
      overflow: hidden;
      box-shadow: 0 18px 40px rgba(0,0,0,.22);
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
      padding: 14px 14px 10px;
      border-bottom: 1px solid var(--line);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(230, 185, 91, .14);
      color: var(--accent);
      border: 1px solid rgba(230, 185, 91, .35);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 8px 0 2px;
      font-size: 18px;
    }}
    .card-head p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .score {{
      min-width: 92px;
      text-align: right;
      color: var(--good);
      font-weight: 800;
    }}
    .image-wrap {{
      background: #0a0f15;
      border-bottom: 1px solid var(--line);
    }}
    .image-wrap img {{
      display: block;
      width: 100%;
      max-height: 320px;
      object-fit: cover;
      background: #0a0f15;
    }}
    .details {{
      display: grid;
      gap: 0;
      margin: 0;
      padding: 10px 14px 14px;
    }}
    .details > div {{
      display: grid;
      grid-template-columns: 150px minmax(0, 1fr);
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255,255,255,.06);
    }}
    .details > div:last-child {{
      border-bottom: 0;
    }}
    dt {{
      color: #d8e0eb;
      font-weight: 700;
    }}
    dd {{
      margin: 0;
      color: var(--muted);
      overflow-wrap: anywhere;
    }}
    a {{ color: #9cc6ff; }}
    .summary {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(16, 23, 32, .88);
      padding: 14px 16px;
    }}
    .summary h3 {{
      margin: 0 0 8px;
      font-size: 18px;
    }}
    .summary table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .summary th, .summary td {{
      text-align: left;
      padding: 8px 8px 8px 0;
      vertical-align: top;
      border-bottom: 1px solid rgba(255,255,255,.06);
    }}
    .summary th {{ color: #d8e0eb; }}
    .guardrails {{
      color: var(--muted);
      font-size: 13px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
      display: grid;
      gap: 4px;
    }}
    @media (max-width: 720px) {{
      .details > div {{
        grid-template-columns: 1fr;
      }}
      .score {{
        min-width: 0;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>WNBA Fever Visual Rank Board</h1>
    <p>Review-only enrichment board for WFFS001-WFFS005. It surfaces the source URL, remote candidate image URL, alt/caption evidence, identity honesty, crop and negative-space notes, and fast carry-forward or reject prompts without any downloads.</p>
    <div class="meta-row">
      <div class="pill">Board CSV: {html.escape(repo_rel(board_csv))}</div>
      <div class="pill">Intake CSV: {html.escape(repo_rel(intake_csv))}</div>
      <div class="pill">Generated: {html.escape(generated_at)}</div>
      <div class="pill">review_only=true</div>
      <div class="pill">download_approved=no</div>
      <div class="pill">no source auto-enablement</div>
    </div>
  </header>
  <main>
    <section class="summary">
      <h3>Top carry-forward candidates</h3>
      <table>
        <thead>
          <tr><th>Rank</th><th>Candidate</th><th>Score</th><th>Why it matters</th></tr>
        </thead>
        <tbody>
          {''.join(f"<tr><td>{html.escape(row['board_rank'])}</td><td>{html.escape(row['candidate_queue_id'])}</td><td>{html.escape(row['visual_rank_score'])}</td><td>{html.escape(row['carry_forward_prompt'])}</td></tr>" for row in rows[:3])}
        </tbody>
      </table>
    </section>
    <section class="grid">
      {''.join(cards)}
    </section>
    <section class="guardrails">
      <div>review_only=true</div>
      <div>download_approved=no</div>
      <div>publish_ready=false</div>
      <div>asset_downloads=false</div>
      <div>approval_state_change=false</div>
      <div>publishing=false</div>
      <div>no paid APIs</div>
      <div>no downloads</div>
    </section>
  </main>
</body>
</html>
"""


def build_packet(*, board_csv: Path, intake_csv: Path, output_dir: Path) -> dict[str, Any]:
    board_rows = read_csv_rows(board_csv)
    intake_rows = read_csv_rows(intake_csv)
    rows = build_rows(board_rows, intake_rows)
    intake_template_rows = build_intake_rows(rows)
    generated_at = now_iso()

    output_dir.mkdir(parents=True, exist_ok=True)
    board_out = output_dir / BOARD_CSV_NAME
    intake_out = output_dir / INTAKE_CSV_NAME
    report_out = output_dir / REPORT_MD_NAME
    html_out = output_dir / HTML_NAME
    manifest_out = output_dir / MANIFEST_JSON_NAME

    write_csv_rows(board_out, rows, CSV_FIELDS)
    write_csv_rows(intake_out, intake_template_rows, INTAKE_FIELDS)
    write_text(report_out, render_report(rows, generated_at, board_out, intake_out, html_out))
    write_text(html_out, render_html(rows, generated_at, board_out, intake_out))

    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "status": "wnba_fever_visual_rank_ready" if rows else "wnba_fever_visual_rank_empty",
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
    parser = argparse.ArgumentParser(description="Build the WNBA Fever visual-rank review board.")
    parser.add_argument("--board-csv", default=(input_dir() / BOARD_INPUT_NAME).as_posix())
    parser.add_argument("--intake-csv", default=(input_dir() / INTAKE_INPUT_NAME).as_posix())
    parser.add_argument("--output-dir", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else output_root()
    manifest = build_packet(board_csv=Path(args.board_csv), intake_csv=Path(args.intake_csv), output_dir=output_dir)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "row_count": manifest["row_count"],
                "output_dir": output_dir.as_posix(),
                "html_path": manifest["html_path"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
