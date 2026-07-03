from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from pathlib import Path
from typing import Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text


VERSION = "hsd-action-photo-remote-visual-triage-v1-review-only"
DEFAULT_INPUT_CSV = Path("outputs/local/latest/files/action_photo_candidate_scout_seed_expansion/action_photo_candidate_intake.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_remote_visual_triage_v1")
TRIAGE_FIELDS = [
    "triage_id",
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "credit_byline",
    "visual_priority",
    "selection_reason",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "manual_visual_decision",
    "manual_visual_notes",
    "download_approved",
    "review_only",
    "publish_ready",
    "asset_downloads",
    "approval_state_change",
    "approved_marker_writes",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def read_rows(path: Path) -> list[dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Missing candidate intake CSV: {resolved}")
    with resolved.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def priority_score(row: Mapping[str, str]) -> int:
    score = 0
    if clean(row.get("fetch_status")) == "candidate_metadata_extracted":
        score += 3
    if clean(row.get("candidate_image_url")):
        score += 3
    if clean(row.get("face_likely_visible")) == "likely":
        score += 3
    elif clean(row.get("face_likely_visible")) == "possible":
        score += 1
    if clean(row.get("four_by_five_crop_potential")) == "likely":
        score += 3
    elif clean(row.get("four_by_five_crop_potential")) == "possible":
        score += 2
    if clean(row.get("text_safe_negative_space")) == "likely":
        score += 2
    elif clean(row.get("text_safe_negative_space")) == "possible":
        score += 1
    if clean(row.get("source_provenance_clarity")) == "clear":
        score += 2
    if clean(row.get("body_margin_likely")) == "likely":
        score += 2
    elif clean(row.get("body_margin_likely")) == "possible":
        score += 1
    source_type = clean(row.get("source_type")).lower()
    if "official" in source_type:
        score += 2
    status = clean(row.get("manual_review_status")).lower()
    if status.startswith("rejected"):
        score -= 20
    if "hold" in status:
        score -= 8
    if "wrong_person" in status:
        score -= 20
    return score


def priority_label(score: int) -> str:
    if score >= 15:
        return "P1_visual_review_now"
    if score >= 11:
        return "P2_visual_review_next"
    return "P3_backup_or_reject_fast"


def selection_reason(row: Mapping[str, str], score: int) -> str:
    reasons: list[str] = []
    for field in [
        "face_likely_visible",
        "four_by_five_crop_potential",
        "text_safe_negative_space",
        "body_margin_likely",
        "source_provenance_clarity",
    ]:
        value = clean(row.get(field))
        if value in {"likely", "possible", "clear"}:
            reasons.append(f"{field}={value}")
    if "official" in clean(row.get("source_type")).lower():
        reasons.append("official_source_surface")
    return "; ".join(reasons) or f"metadata_score={score}"


def triage_rows(rows: Iterable[Mapping[str, str]], limit: int) -> list[dict[str, str]]:
    candidates = [
        (priority_score(row), row)
        for row in rows
        if clean(row.get("fetch_status")) == "candidate_metadata_extracted" and clean(row.get("candidate_image_url"))
    ]
    candidates.sort(
        key=lambda item: (
            item[0],
            clean(item[1].get("source_provenance_clarity")) == "clear",
            clean(item[1].get("face_likely_visible")) == "likely",
            clean(item[1].get("four_by_five_crop_potential")) in {"likely", "possible"},
        ),
        reverse=True,
    )
    output: list[dict[str, str]] = []
    for index, (score, row) in enumerate(candidates[:limit], start=1):
        output.append(
            {
                "triage_id": f"APVT{index:03d}",
                "scout_candidate_id": clean(row.get("scout_candidate_id")),
                "entity_id": clean(row.get("entity_id")),
                "source_type": clean(row.get("source_type")),
                "source_url": clean(row.get("source_url")),
                "candidate_image_url": clean(row.get("candidate_image_url")),
                "image_alt": clean(row.get("image_alt")),
                "credit_byline": clean(row.get("credit_byline")),
                "visual_priority": priority_label(score),
                "selection_reason": selection_reason(row, score),
                "face_likely_visible": clean(row.get("face_likely_visible")),
                "body_margin_likely": clean(row.get("body_margin_likely")),
                "four_by_five_crop_potential": clean(row.get("four_by_five_crop_potential")),
                "text_safe_negative_space": clean(row.get("text_safe_negative_space")),
                "source_provenance_clarity": clean(row.get("source_provenance_clarity")),
                "manual_visual_decision": "",
                "manual_visual_notes": "",
                "download_approved": "no",
                "review_only": "true",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "none",
                "approved_marker_writes": "false",
            }
        )
    return output


def render_html(rows: list[Mapping[str, str]], input_csv: Path) -> str:
    cards: list[str] = []
    for row in rows:
        cards.append(
            f"""
      <article class="card">
        <div class="media">
          <img loading="lazy" referrerpolicy="no-referrer" src="{html.escape(clean(row.get('candidate_image_url')), quote=True)}" alt="{html.escape(clean(row.get('image_alt')), quote=True)}">
        </div>
        <div class="meta">
          <div class="kicker">{html.escape(clean(row.get('visual_priority')))}</div>
          <h2>{html.escape(clean(row.get('scout_candidate_id')))} / {html.escape(clean(row.get('entity_id')))}</h2>
          <p>{html.escape(clean(row.get('selection_reason')))}</p>
          <dl>
            <div><dt>4:5</dt><dd>{html.escape(clean(row.get('four_by_five_crop_potential')))}</dd></div>
            <div><dt>Face</dt><dd>{html.escape(clean(row.get('face_likely_visible')))}</dd></div>
            <div><dt>Space</dt><dd>{html.escape(clean(row.get('text_safe_negative_space')))}</dd></div>
            <div><dt>Source</dt><dd>{html.escape(clean(row.get('source_provenance_clarity')))}</dd></div>
          </dl>
          <a href="{html.escape(clean(row.get('source_url')), quote=True)}">source page</a>
        </div>
      </article>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HSD Action Photo Remote Visual Triage</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: Arial, Helvetica, sans-serif;
      background: #101316;
      color: #f6f1e8;
    }}
    body {{ margin: 0; padding: 28px; }}
    header {{ max-width: 1120px; margin: 0 auto 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    .note {{ color: #c8c0b2; line-height: 1.45; max-width: 960px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; max-width: 1480px; margin: 0 auto; }}
    .card {{ background: #171b20; border: 1px solid #303841; border-radius: 8px; overflow: hidden; }}
    .media {{ aspect-ratio: 4 / 3; background: #0b0d0f; display: grid; place-items: center; }}
    .media img {{ width: 100%; height: 100%; object-fit: cover; }}
    .meta {{ padding: 14px 16px 16px; }}
    .kicker {{ color: #e8d36d; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
    h2 {{ margin: 0 0 8px; font-size: 16px; line-height: 1.25; }}
    p {{ margin: 0 0 12px; color: #d6cec1; font-size: 13px; line-height: 1.4; }}
    dl {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 0 0 12px; }}
    dl div {{ background: #20262d; padding: 8px; border-radius: 6px; }}
    dt {{ color: #9ba7b1; font-size: 11px; text-transform: uppercase; }}
    dd {{ margin: 3px 0 0; font-size: 13px; }}
    a {{ color: #8ec5ff; }}
  </style>
</head>
<body>
  <header>
    <h1>HSD Action Photo Remote Visual Triage</h1>
    <p class="note">Review-only board generated from <code>{html.escape(input_csv.as_posix())}</code>. The script records metadata and writes no image bytes. Opening this HTML in a browser may request remote images from their public source URLs. No asset approval, renderer approval, approved markers, publish-ready state, or publishing is implied.</p>
  </header>
  <main class="grid">
    {''.join(cards)}
  </main>
</body>
</html>
"""


def render_report(rows: list[Mapping[str, str]], input_csv: Path) -> str:
    p1 = sum(1 for row in rows if clean(row.get("visual_priority")) == "P1_visual_review_now")
    lines = [
        "# HSD Action Photo Remote Visual Triage",
        "",
        "This packet is review-only and metadata-first. It does not save source images, approve assets, move files, create approved markers, mark publish-ready, or publish.",
        "",
        f"- Version: `{VERSION}`",
        f"- Input CSV: `{input_csv.as_posix()}`",
        f"- Triage rows: `{len(rows)}`",
        f"- P1 visual-review rows: `{p1}`",
        "- Manual use: open the HTML board, reject weak/group/wrong-person rows quickly, and only move a strong row into the formal human intake path after review.",
        "",
        "## Top Rows",
        "",
        "| Triage | Scout | Entity | Priority | 4:5 | Face | Space | Source |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:20]:
        lines.append(
            "| {triage} | {scout} | {entity} | {priority} | {crop} | {face} | {space} | {source} |".format(
                triage=clean(row.get("triage_id")),
                scout=clean(row.get("scout_candidate_id")),
                entity=clean(row.get("entity_id")),
                priority=clean(row.get("visual_priority")),
                crop=clean(row.get("four_by_five_crop_potential")),
                face=clean(row.get("face_likely_visible")),
                space=clean(row.get("text_safe_negative_space")),
                source=clean(row.get("source_provenance_clarity")),
            )
        )
    return "\n".join(lines) + "\n"


def build_manifest(rows: list[Mapping[str, str]], input_csv: Path, output_dir: Path) -> dict[str, object]:
    return {
        "version": VERSION,
        "status": "remote_visual_triage_ready",
        "input_csv": input_csv.as_posix(),
        "output_dir": output_dir.as_posix(),
        "triage_rows": len(rows),
        "p1_visual_review_rows": sum(1 for row in rows if clean(row.get("visual_priority")) == "P1_visual_review_now"),
        "html_path": (output_dir / "action_photo_remote_visual_triage.html").as_posix(),
        "csv_path": (output_dir / "action_photo_remote_visual_triage.csv").as_posix(),
        "report_path": (output_dir / "action_photo_remote_visual_triage_report.md").as_posix(),
        "csv_fields": TRIAGE_FIELDS,
        "review_only": True,
        "publish_ready": False,
        "asset_downloads": False,
        "source_fetching": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "auto_approval": False,
        "auto_publish": False,
        "paid_apis": False,
        "remote_image_policy": "html_references_remote_urls_only_no_local_image_bytes_written_by_script",
    }


def build_packet(*, input_csv: Path, output_dir: Path, limit: int) -> dict[str, object]:
    resolved_input = input_path(input_csv)
    out_dir = output_path(output_dir)
    rows = triage_rows(read_rows(input_csv), limit)
    write_csv(out_dir / "action_photo_remote_visual_triage.csv", rows, TRIAGE_FIELDS)
    write_text(out_dir / "action_photo_remote_visual_triage.html", render_html(rows, resolved_input))
    write_text(out_dir / "action_photo_remote_visual_triage_report.md", render_report(rows, resolved_input))
    manifest = build_manifest(rows, resolved_input, out_dir)
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only remote visual triage board from scout candidate metadata.")
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=36)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_packet(input_csv=Path(args.input_csv), output_dir=Path(args.output_dir), limit=max(1, args.limit))
    print(json.dumps({"version": VERSION, "status": manifest["status"], "triage_rows": manifest["triage_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
