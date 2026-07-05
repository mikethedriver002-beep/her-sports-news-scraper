from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-wnba-manual-surface-index-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_manual_surface_index_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_manual_surface_index_v1")
DEFAULT_LATEST_FILES_ROOT = Path("outputs/local/latest/files")

HTML_NAME = "wnba_manual_surface_index.html"
CSV_NAME = "wnba_manual_surface_index.csv"
REPORT_NAME = "wnba_manual_surface_index.md"
MANIFEST_NAME = "manifest.json"

CSV_FIELDS = [
    "surface_id",
    "surface_name",
    "available",
    "priority",
    "surface_type",
    "manual_action",
    "packet_root",
    "primary_artifact_path",
    "primary_artifact_uri",
    "report_path",
    "csv_path",
    "manifest_path",
    "status",
    "generated_at_utc",
    "candidate_or_variant_count",
    "guardrail_note",
    "attachment_guidance",
    "blunt_read",
]


@dataclass(frozen=True)
class SurfaceSpec:
    surface_id: str
    surface_name: str
    packet_root_name: str
    primary_artifact_name: str
    report_name: str
    csv_name: str
    priority: str
    surface_type: str
    manual_action: str
    attachment_guidance: str
    blunt_read: str


SURFACES = [
    SurfaceSpec(
        surface_id="wnba_fever_visual_rank",
        surface_name="WNBA Fever visual-rank board",
        packet_root_name="wnba_fever_visual_rank_v1",
        primary_artifact_name="wnba_fever_visual_rank_board.html",
        report_name="wnba_fever_visual_rank_report.md",
        csv_name="wnba_fever_visual_rank_board.csv",
        priority="P1_manual_review_now",
        surface_type="source_quality_visual_rank",
        manual_action="Open first. Inspect WFFS001/WFFS002/WFFS005 before lower-confidence Fever rows.",
        attachment_guidance="Attach HTML board plus CSV/report when emailing Mike.",
        blunt_read="Best current WNBA source-quality surface; keeps the Fever candidates honest without downloads.",
    ),
    SurfaceSpec(
        surface_id="wnba_fever_swipe_deck",
        surface_name="WNBA Fever original swipe deck",
        packet_root_name="wnba_fever_source_scout_v1/review_deck",
        primary_artifact_name="action_photo_review_deck.html",
        report_name="action_photo_review_deck_report.md",
        csv_name="manual_decision_export_template.csv",
        priority="P2_swipe_if_visual_rank_passes",
        surface_type="source_quality_swipe_deck",
        manual_action="Use after the visual-rank board if a swipe/export decision surface is needed.",
        attachment_guidance="Attach the deck HTML and decision template when asking for manual exports.",
        blunt_read="Useful for decision export; less compact than the visual-rank board.",
    ),
    SurfaceSpec(
        surface_id="wnba_storm_visual_rank",
        surface_name="WNBA Storm visual-rank board",
        packet_root_name="wnba_storm_visual_rank_v1",
        primary_artifact_name="wnba_storm_visual_rank_board.html",
        report_name="wnba_storm_visual_rank_report.md",
        csv_name="wnba_storm_visual_rank_board.csv",
        priority="P3_storm_manual_review_now",
        surface_type="source_quality_visual_rank",
        manual_action="Open after Fever. Inspect WSFS001/WSFS003/WSFS005 before Storm context rows.",
        attachment_guidance="Attach HTML board plus CSV/report when emailing Mike.",
        blunt_read="Best compact Storm surface; rank board is more useful than raw scout rows for manual review.",
    ),
    SurfaceSpec(
        surface_id="wnba_storm_source_scout",
        surface_name="WNBA Storm scout and deck",
        packet_root_name="wnba_official_source_expansion_next_v1",
        primary_artifact_name="wnba_storm_source_scout_report.md",
        report_name="wnba_storm_source_scout_report.md",
        csv_name="wnba_storm_source_scout_board.csv",
        priority="P4_storm_source_context",
        surface_type="metadata_scout",
        manual_action="Inspect WSFS001 first, then WSFS003/WSFS005 with stricter identity checks.",
        attachment_guidance="Attach report, board CSV, intake CSV, and deck HTML when emailing Mike.",
        blunt_read="Useful second WNBA source family; lower rows need harder visual identity review than Fever.",
    ),
    SurfaceSpec(
        surface_id="wnba_fever_source_scout",
        surface_name="WNBA Fever scout report and intake",
        packet_root_name="wnba_fever_source_scout_v1",
        primary_artifact_name="wnba_fever_source_scout_report.md",
        report_name="wnba_fever_source_scout_report.md",
        csv_name="wnba_fever_source_scout_intake.csv",
        priority="P5_fever_source_context",
        surface_type="metadata_scout",
        manual_action="Use as provenance/context. Do not treat scout rows as download approvals.",
        attachment_guidance="Attach report/intake/board only as supporting context.",
        blunt_read="Strong official Fever metadata scout; visual confirmation still required.",
    ),
    SurfaceSpec(
        surface_id="wnba_apcs039_score_command",
        surface_name="APCS039 WNBA score-command graphics",
        packet_root_name="wnba_apcs039_score_command_refine_v2",
        primary_artifact_name="contact_sheet.png",
        report_name="visual_report.md",
        csv_name="manual_visual_review_intake.csv",
        priority="P6_visual_hold_unless_selected",
        surface_type="graphic_visual_review",
        manual_action="Review only if Mike picks a WNBA graphic direction to carry forward.",
        attachment_guidance="Attach contact_sheet.png first; include visual report as context.",
        blunt_read="Best current local WNBA graphic surface, but do not blind-polish without a selected variant.",
    ),
    SurfaceSpec(
        surface_id="wnba_source_quality_next",
        surface_name="WNBA source-quality next board",
        packet_root_name="wnba_source_quality_next_v1",
        primary_artifact_name="wnba_source_quality_next_report.md",
        report_name="wnba_source_quality_next_report.md",
        csv_name="wnba_source_quality_next_board.csv",
        priority="P7_strategy_context",
        surface_type="source_strategy_board",
        manual_action="Use only as strategic context for the current WNBA-only loop.",
        attachment_guidance="Attach the board/report if explaining why Fever is the current lead source family.",
        blunt_read="Good steering board; superseded operationally by the Fever visual-rank board.",
    ),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_root(raw: str | Path | None, default: Path) -> Path:
    if raw is None or str(raw).strip() == "":
        return default
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def file_uri(path: Path) -> str:
    return path.resolve(strict=False).as_uri()


def candidate_count_from_manifest(manifest: dict[str, Any]) -> str:
    for key in ("row_count", "candidate_item_count", "candidate_row_count", "deck_item_count", "variant_count"):
        if key in manifest:
            return clean(manifest.get(key))
    rows = manifest.get("rows")
    if isinstance(rows, list):
        return str(len(rows))
    return ""


def build_rows(latest_files_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in SURFACES:
        packet_root = latest_files_root / spec.packet_root_name
        manifest_path = packet_root / MANIFEST_NAME
        primary_artifact = packet_root / spec.primary_artifact_name
        report_path = packet_root / spec.report_name
        csv_path = packet_root / spec.csv_name
        manifest = read_json_payload(manifest_path)
        available = packet_root.exists() and primary_artifact.exists()
        rows.append(
            {
                "surface_id": spec.surface_id,
                "surface_name": spec.surface_name,
                "available": "true" if available else "false",
                "priority": spec.priority,
                "surface_type": spec.surface_type,
                "manual_action": spec.manual_action,
                "packet_root": packet_root.as_posix(),
                "primary_artifact_path": primary_artifact.as_posix(),
                "primary_artifact_uri": file_uri(primary_artifact) if available else "",
                "report_path": report_path.as_posix(),
                "csv_path": csv_path.as_posix(),
                "manifest_path": manifest_path.as_posix(),
                "status": clean(manifest.get("status")) or ("available_no_manifest" if available else "missing"),
                "generated_at_utc": clean(manifest.get("generated_at_utc")),
                "candidate_or_variant_count": candidate_count_from_manifest(manifest),
                "guardrail_note": "review_only; download_approved=no; no downloads; no approvals; no publishing",
                "attachment_guidance": spec.attachment_guidance,
                "blunt_read": spec.blunt_read,
            }
        )
    return rows


def build_report(manifest: dict[str, Any], rows: list[dict[str, str]]) -> str:
    lines = [
        "# WNBA Manual Surface Index V1",
        "",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "WNBA-only operator index for the current action-photo/source-quality loop.",
        "",
        "## Priority Order",
        "",
        "| Priority | Surface | Available | Manual action |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['priority']} | {row['surface_name']} | {row['available']} | {row['manual_action']} |")
    lines.extend(
        [
            "",
            "## Blunt Read",
            "",
            "- Use the Fever visual-rank board first, then the Storm visual-rank board.",
            "- Do not polish APCS039 unless Mike selects a specific WNBA graphic direction.",
            "- Do not pivot to non-WNBA source lanes from this packet.",
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- no downloads",
            "- no approvals",
            "- no source auto-enablement",
            "- no `.approved` markers",
            "- no protected asset movement",
            "- no publish-ready state",
            "- no publishing",
        ]
    )
    return "\n".join(lines) + "\n"


def build_html(manifest: dict[str, Any], rows: list[dict[str, str]]) -> str:
    cards = []
    for row in rows:
        artifact_link = (
            f'<a href="{html.escape(row["primary_artifact_uri"])}">Open artifact</a>'
            if row["primary_artifact_uri"]
            else "Missing"
        )
        cards.append(
            f"""
      <article class="card">
        <div class="card-head">
          <span>{html.escape(row['priority'])}</span>
          <strong>{html.escape(row['available'])}</strong>
        </div>
        <h2>{html.escape(row['surface_name'])}</h2>
        <p>{html.escape(row['blunt_read'])}</p>
        <dl>
          <div><dt>Manual action</dt><dd>{html.escape(row['manual_action'])}</dd></div>
          <div><dt>Primary</dt><dd>{artifact_link}</dd></div>
          <div><dt>Report</dt><dd><code>{html.escape(row['report_path'])}</code></dd></div>
          <div><dt>CSV</dt><dd><code>{html.escape(row['csv_path'])}</code></dd></div>
          <div><dt>Attachment</dt><dd>{html.escape(row['attachment_guidance'])}</dd></div>
          <div><dt>Guardrail</dt><dd>{html.escape(row['guardrail_note'])}</dd></div>
        </dl>
      </article>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WNBA Manual Surface Index</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0e1218;
      --panel: #151b24;
      --line: #2d3746;
      --ink: #f4f7fb;
      --muted: #b7c1cf;
      --accent: #f4c04e;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 15px/1.45 Arial, Helvetica, sans-serif; color: var(--ink); background: var(--bg); }}
    header {{ padding: 24px clamp(18px, 4vw, 42px); border-bottom: 1px solid var(--line); background: #101722; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    header p {{ margin: 0; color: var(--muted); max-width: 980px; }}
    .summary {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
    .pill {{ border: 1px solid var(--line); border-radius: 999px; padding: 8px 12px; color: var(--muted); }}
    main {{ padding: 22px clamp(18px, 4vw, 42px); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }}
    .card {{ border: 1px solid var(--line); border-radius: 8px; background: var(--panel); overflow: hidden; }}
    .card-head {{ display: flex; justify-content: space-between; gap: 10px; padding: 12px 14px; border-bottom: 1px solid var(--line); color: var(--accent); font-weight: 700; }}
    h2 {{ margin: 14px 14px 8px; font-size: 20px; letter-spacing: 0; }}
    .card p {{ margin: 0 14px 10px; color: var(--muted); }}
    dl {{ margin: 0; padding: 0 14px 14px; }}
    dl div {{ display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: 10px; padding: 8px 0; border-top: 1px solid rgba(255,255,255,.06); }}
    dt {{ color: var(--ink); font-weight: 700; }}
    dd {{ margin: 0; color: var(--muted); overflow-wrap: anywhere; }}
    a {{ color: #9cc6ff; }}
    code {{ color: #dce5f2; }}
  </style>
</head>
<body>
  <header>
    <h1>WNBA Manual Surface Index</h1>
    <p>One WNBA-only operator surface map for the current source-quality and graphics loop. No downloads, approvals, source enablement, or publishing.</p>
    <div class="summary">
      <div class="pill">Status: {html.escape(manifest['status'])}</div>
      <div class="pill">Surfaces: {manifest['surface_count']}</div>
      <div class="pill">Available: {manifest['available_surface_count']}</div>
      <div class="pill">Generated: {html.escape(manifest['generated_at_utc'])}</div>
    </div>
  </header>
  <main>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def mirror_to_latest(output_dir: Path, latest_files_root: Path) -> Path:
    mirror_dir = latest_files_root / output_dir.name
    mirror_dir.mkdir(parents=True, exist_ok=True)
    for source in output_dir.iterdir():
        if source.is_file():
            shutil.copy2(source, mirror_dir / source.name)
    return mirror_dir


def build_packet(*, output_dir: Path, latest_files_root: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    latest_files_root = latest_files_root.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_files_root.mkdir(parents=True, exist_ok=True)

    generated_at = now_iso()
    rows = build_rows(latest_files_root)
    available_rows = [row for row in rows if row["available"] == "true"]
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "status": "wnba_manual_surface_index_ready",
        "output_dir": output_dir.as_posix(),
        "latest_files_root": latest_files_root.as_posix(),
        "surface_count": len(rows),
        "available_surface_count": len(available_rows),
        "review_only": True,
        "download_approved": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "protected_asset_moves": False,
        "publish_ready": False,
        "publishing": False,
        "paid_apis": False,
        "source_auto_enabled": False,
    }
    csv_path = write_csv(output_dir / CSV_NAME, rows, CSV_FIELDS)
    html_path = write_text(output_dir / HTML_NAME, build_html(manifest, rows), if_changed=False)
    report_path = write_text(output_dir / REPORT_NAME, build_report(manifest, rows))
    manifest["csv_path"] = csv_path.as_posix()
    manifest["html_path"] = html_path.as_posix()
    manifest["report_path"] = report_path.as_posix()
    manifest["manifest_path"] = (output_dir / MANIFEST_NAME).as_posix()
    manifest["rows"] = rows
    manifest_path = write_json(output_dir / MANIFEST_NAME, manifest, sort_keys=True)
    mirror_dir = mirror_to_latest(output_dir, latest_files_root)
    manifest["mirror_dir"] = mirror_dir.as_posix()
    write_json(manifest_path, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the WNBA-only manual surface index.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-files-root", default=DEFAULT_LATEST_FILES_ROOT.as_posix())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        output_dir=resolve_output_dir(args.output_dir or None),
        latest_files_root=resolve_root(args.latest_files_root, DEFAULT_LATEST_FILES_ROOT),
    )
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "surface_count": manifest["surface_count"],
                "available_surface_count": manifest["available_surface_count"],
                "output_dir": manifest["output_dir"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
