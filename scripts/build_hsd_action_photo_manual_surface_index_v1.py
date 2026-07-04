from __future__ import annotations

import argparse
import csv
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


VERSION = "hsd-action-photo-manual-surface-index-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_manual_surface_index_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_manual_surface_index_v1")
DEFAULT_LATEST_FILES_ROOT = Path("outputs/local/latest/files")

HTML_NAME = "action_photo_manual_surface_index.html"
CSV_NAME = "action_photo_manual_surface_index.csv"
REPORT_NAME = "action_photo_manual_surface_index.md"
MANIFEST_NAME = "manifest.json"


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


def read_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def clean(value: Any) -> str:
    return str(value or "").strip()


def file_uri(path: Path) -> str:
    return path.resolve(strict=False).as_uri()


@dataclass(frozen=True)
class SurfaceSpec:
    surface_id: str
    surface_name: str
    packet_root_name: str
    primary_artifact_name: str
    report_name: str
    csv_name: str
    attachment_mode: str
    manual_action: str
    attachment_guidance: str
    summary_note: str


def discover_surface_root(latest_files_root: Path, packet_root_name: str) -> Path | None:
    candidate = latest_files_root / packet_root_name
    return candidate if candidate.exists() else None


def discover_latest_ranker_root(latest_files_root: Path) -> Path | None:
    roots: list[tuple[int, Path]] = []
    for path in latest_files_root.glob("action_photo_ranker_review_deck_v*"):
        if not path.is_dir():
            continue
        suffix = path.name.rsplit("_v", 1)[-1]
        if not suffix.isdigit():
            continue
        roots.append((int(suffix), path))
    if not roots:
        return None
    roots.sort(key=lambda item: item[0])
    return roots[-1][1]


def surface_rows(latest_files_root: Path) -> list[dict[str, Any]]:
    surface_specs = [
        SurfaceSpec(
            surface_id="apcs048_visual_rescue",
            surface_name="APCS048 visual rescue contact sheet",
            packet_root_name="apcs048_visual_rescue_v1",
            primary_artifact_name="contact_sheet.png",
            report_name="visual_report.md",
            csv_name="manual_visual_review_intake.csv",
            attachment_mode="literal_contact_sheet",
            manual_action="Open the contact sheet first, compare the carry-forward candidate by eye, and keep the rescue lane review-only.",
            attachment_guidance="Attach the literal contact_sheet.png first when emailing. Add visual_report.md only as supporting context.",
            summary_note="This is the only surface in the packet with a literal local contact sheet image ready to attach.",
        ),
        SurfaceSpec(
            surface_id="purdue_v7_focus_deck",
            surface_name="Purdue women's soccer v7 focused deck",
            packet_root_name="action_photo_review_deck_official_source_expansion_v7",
            primary_artifact_name="action_photo_review_deck.html",
            report_name="action_photo_review_deck_report.md",
            csv_name="manual_decision_export_template.csv",
            attachment_mode="deck_html",
            manual_action="Open the focused deck, review the Purdue women’s soccer rows, and keep the lane review-only.",
            attachment_guidance="Attach the deck HTML or a screenshot/export of the deck. Prefer the literal deck if it is present locally.",
            summary_note="This focused deck is the new Purdue women’s soccer review surface and stays review-only.",
        ),
        SurfaceSpec(
            surface_id="uconn_v6_focus_deck",
            surface_name="UConn v6 focused deck",
            packet_root_name="action_photo_review_deck_official_source_expansion_v6",
            primary_artifact_name="action_photo_review_deck.html",
            report_name="action_photo_review_deck_report.md",
            csv_name="manual_decision_export_template.csv",
            attachment_mode="deck_html",
            manual_action="Open the focused deck, review the candidate rows, and use the deck as the visual decision surface.",
            attachment_guidance="Attach the deck HTML or a screenshot/export of the deck. If a literal render appears later, prefer that over prose.",
            summary_note="This focused deck is the current UConn review surface and stays review-only.",
        ),
        SurfaceSpec(
            surface_id="world_rugby_v5_focus_deck",
            surface_name="World Rugby v5 focused deck",
            packet_root_name="action_photo_review_deck_official_source_expansion_v5",
            primary_artifact_name="action_photo_review_deck.html",
            report_name="action_photo_review_deck_report.md",
            csv_name="manual_decision_export_template.csv",
            attachment_mode="deck_html",
            manual_action="Open the focused deck, confirm the strongest rugby rows, and keep the lane review-only.",
            attachment_guidance="Attach the deck HTML or a screenshot/export of the deck. Prefer a literal render if a later packet generates one.",
            summary_note="This is the current World Rugby review surface and does not change approval state.",
        ),
        SurfaceSpec(
            surface_id="latest_broad_deck",
            surface_name="Latest broad deck",
            packet_root_name="__discover_latest_ranker__",
            primary_artifact_name="action_photo_review_deck.html",
            report_name="action_photo_review_deck_report.md",
            csv_name="manual_decision_export_template.csv",
            attachment_mode="deck_html",
            manual_action="Open the latest broad ranker deck for the widest current pass, then hand off only review notes.",
            attachment_guidance="Attach the deck HTML or a screenshot/export of the deck. If the deck later gains a literal render, attach that instead.",
            summary_note="This row resolves to the highest-numbered action-photo ranker deck currently present in latest/files.",
        ),
    ]

    rows: list[dict[str, Any]] = []
    for spec in surface_specs:
        if spec.packet_root_name == "__discover_latest_ranker__":
            packet_root = discover_latest_ranker_root(latest_files_root)
        else:
            packet_root = discover_surface_root(latest_files_root, spec.packet_root_name)

        available = packet_root is not None
        manifest_path = packet_root / MANIFEST_NAME if packet_root else latest_files_root / spec.packet_root_name / MANIFEST_NAME
        manifest = read_json_payload(manifest_path)
        report_path = packet_root / spec.report_name if packet_root else latest_files_root / spec.packet_root_name / spec.report_name
        csv_path = packet_root / spec.csv_name if packet_root else latest_files_root / spec.packet_root_name / spec.csv_name
        primary_artifact_path = packet_root / spec.primary_artifact_name if packet_root else latest_files_root / spec.packet_root_name / spec.primary_artifact_name

        generated_at = clean(manifest.get("generated_at_utc") or manifest.get("generated_at") or "")
        status = clean(manifest.get("status") or ("available" if available else "missing"))
        candidate_count = clean(
            manifest.get("candidate_item_count")
            or manifest.get("deck_item_count")
            or manifest.get("renderer_proof_item_count")
            or ""
        )
        row = {
            "surface_id": spec.surface_id,
            "surface_name": spec.surface_name,
            "available": "true" if available else "false",
            "status": status,
            "generated_at_utc": generated_at,
            "candidate_or_deck_count": candidate_count,
            "manual_action": spec.manual_action if available else f"Missing local surface packet: {spec.surface_name}",
            "attachment_mode": spec.attachment_mode,
            "attachment_guidance": spec.attachment_guidance,
            "summary_note": spec.summary_note,
            "packet_root": packet_root.as_posix() if packet_root else "",
            "primary_artifact_path": primary_artifact_path.as_posix(),
            "primary_artifact_uri": file_uri(primary_artifact_path) if available else "",
            "report_path": report_path.as_posix(),
            "csv_path": csv_path.as_posix(),
            "manifest_path": manifest_path.as_posix(),
        }
        rows.append(row)
    return rows


def build_report(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    available_rows = [row for row in rows if row["available"] == "true"]
    attachment_ready_rows = [row for row in rows if row["attachment_mode"] == "literal_contact_sheet"]
    lines = [
        "# Action Photo Manual Surface Index V1",
        "",
        f"Status: `{manifest['status']}`",
        f"Version: `{VERSION}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "This packet is a review-only operator index. It does not approve downloads, download assets, move protected files, change approval state, create publish-ready files, or publish anything.",
        "",
        "## Current Surfaces",
        "",
        f"- Surfaces indexed: `{manifest['surface_count']}`",
        f"- Available surfaces: `{len(available_rows)}`",
        f"- Literal contact-sheet surfaces: `{len(attachment_ready_rows)}`",
        f"- Latest broad deck resolved: `{manifest['latest_broad_deck_resolved']}`",
        "",
        "| Surface | Status | Manual action | Primary artifact | Attachment guidance |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        artifact = row["primary_artifact_path"]
        guidance = row["attachment_guidance"]
        lines.append(
            f"| {row['surface_name']} | {row['status']} | {row['manual_action']} | `{artifact}` | {guidance} |"
        )

    lines.extend(
        [
            "",
            "## Packet Paths",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"### {row['surface_name']}",
                f"- Local packet root: `{row['packet_root'] or 'missing'}`",
                f"- Manifest: `{row['manifest_path']}`",
                f"- Report: `{row['report_path']}`",
                f"- CSV: `{row['csv_path']}`",
                f"- Primary artifact: `{row['primary_artifact_path']}`",
                f"- Attachment guidance: {row['attachment_guidance']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Guardrails",
            "",
            "- review_only=true",
            "- asset_downloads=false",
            "- approval_state_change=false",
            "- headshot_writes=false",
            "- protected_asset_moves=false",
            "- publish_ready=false",
            "- publishing=false",
            "- paid_apis=false",
            "- source_auto_enabled=false",
            "",
            "## Manual Action",
            "",
            "Mike has a manual action on every available row in this packet: open the listed surface, inspect the referenced file, and attach the literal contact sheet or render when one exists locally.",
            "",
        ]
    )
    return "\n".join(lines)


def build_html(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    def row_html(row: dict[str, Any]) -> str:
        status_class = "ok" if row["available"] == "true" else "missing"
        return f"""
        <tr class="{status_class}">
          <td>
            <strong>{html.escape(row["surface_name"])}</strong>
            <div class="muted">{html.escape(row["surface_id"])}</div>
          </td>
          <td>{html.escape(row["status"])}</td>
          <td>{html.escape(row["manual_action"])}</td>
          <td><code>{html.escape(row["primary_artifact_path"])}</code></td>
          <td>{html.escape(row["attachment_guidance"])}</td>
          <td>{html.escape(row["generated_at_utc"] or "n/a")}</td>
        </tr>"""

    body_rows = "\n".join(row_html(row) for row in rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Action Photo Manual Surface Index V1</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1018;
      --panel: #121926;
      --panel-2: #171f2d;
      --text: #f2f5fa;
      --muted: #a7b2c3;
      --line: #2a3444;
      --accent: #f0be61;
      --good: #2f7d57;
      --missing: #6e3740;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #0b1018, #090d14 36rem);
      color: var(--text);
      font: 14px/1.45 Arial, Helvetica, sans-serif;
    }}
    header, main {{
      width: min(1440px, calc(100vw - 32px));
      margin: 0 auto;
    }}
    header {{
      padding: 24px 0 10px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0;
      font-size: 28px;
      letter-spacing: 0;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px 20px;
      margin-top: 8px;
      color: var(--muted);
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      padding: 16px 0 18px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    .metric .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0; }}
    .metric .value {{ margin-top: 6px; font-size: 20px; font-weight: 700; }}
    .metric .sub {{ margin-top: 4px; color: var(--muted); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 12px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      background: var(--panel-2);
    }}
    tr.ok td:first-child {{ border-left: 4px solid var(--good); }}
    tr.missing td:first-child {{ border-left: 4px solid var(--missing); }}
    code {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      word-break: break-all;
    }}
    .section {{
      margin-top: 22px;
      padding: 16px 0 0;
    }}
    .section h2 {{
      margin: 0 0 10px;
      font-size: 18px;
    }}
    .section p, .section li {{ color: var(--text); }}
    .muted {{ color: var(--muted); }}
    .paths {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }}
    .path-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .path-card h3 {{
      margin: 0 0 8px;
      font-size: 15px;
    }}
    .path-card p {{
      margin: 0 0 8px;
      color: var(--muted);
    }}
    .path-card ul {{
      margin: 0;
      padding-left: 18px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Action Photo Manual Surface Index V1</h1>
    <div class="meta">
      <span>Status: <strong>{html.escape(manifest["status"])}</strong></span>
      <span>Generated: <strong>{html.escape(manifest["generated_at_utc"])}</strong></span>
      <span>Latest broad deck: <strong>{html.escape(manifest["latest_broad_deck_resolved"])}</strong></span>
    </div>
  </header>
  <main>
    <section class="summary">
      <div class="metric"><div class="label">Surfaces indexed</div><div class="value">{manifest["surface_count"]}</div><div class="sub">review-only operator lanes</div></div>
      <div class="metric"><div class="label">Available</div><div class="value">{manifest["available_surface_count"]}</div><div class="sub">current local packets found</div></div>
      <div class="metric"><div class="label">Literal contact sheets</div><div class="value">{manifest["literal_contact_sheet_count"]}</div><div class="sub">best email attachment candidates</div></div>
    </section>

    <section class="section">
      <h2>Current Surfaces</h2>
      <table>
        <thead>
          <tr>
            <th>Surface</th>
            <th>Status</th>
            <th>Manual action</th>
            <th>Primary artifact</th>
            <th>Attachment guidance</th>
            <th>Generated</th>
          </tr>
        </thead>
        <tbody>
          {body_rows}
        </tbody>
      </table>
    </section>

    <section class="section">
      <h2>Packet Paths</h2>
      <div class="paths">
        {''.join(_path_card_html(row) for row in rows)}
      </div>
    </section>

    <section class="section">
      <h2>Manual Action</h2>
      <p>Mike has a manual action on every available row in this packet. Open the surface, inspect the referenced file, and attach the literal contact sheet or render when one exists locally.</p>
    </section>
  </main>
</body>
</html>
"""


def _path_card_html(row: dict[str, Any]) -> str:
    return f"""
      <div class="path-card">
        <h3>{html.escape(row['surface_name'])}</h3>
        <p>{html.escape(row['summary_note'])}</p>
        <ul>
          <li><code>{html.escape(row['packet_root'] or 'missing')}</code></li>
          <li><code>{html.escape(row['manifest_path'])}</code></li>
          <li><code>{html.escape(row['report_path'])}</code></li>
          <li><code>{html.escape(row['csv_path'])}</code></li>
        </ul>
      </div>
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

    rows = surface_rows(latest_files_root)
    available_rows = [row for row in rows if row["available"] == "true"]
    literal_contact_sheet_count = sum(1 for row in rows if row["attachment_mode"] == "literal_contact_sheet")
    latest_broad_deck_row = next((row for row in rows if row["surface_id"] == "latest_broad_deck"), {})

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_manual_surface_index_ready",
        "output_dir": output_dir.as_posix(),
        "latest_files_root": latest_files_root.as_posix(),
        "latest_broad_deck_resolved": latest_broad_deck_row.get("packet_root", ""),
        "surface_count": len(rows),
        "available_surface_count": len(available_rows),
        "literal_contact_sheet_count": literal_contact_sheet_count,
        "review_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "protected_asset_moves": False,
        "publish_ready": False,
        "publishing": False,
        "paid_apis": False,
        "source_auto_enabled": False,
    }

    csv_path = write_csv(output_dir / CSV_NAME, rows, [
        "surface_id",
        "surface_name",
        "available",
        "status",
        "generated_at_utc",
        "candidate_or_deck_count",
        "manual_action",
        "attachment_mode",
        "attachment_guidance",
        "summary_note",
        "packet_root",
        "primary_artifact_path",
        "primary_artifact_uri",
        "report_path",
        "csv_path",
        "manifest_path",
    ])
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
    parser = argparse.ArgumentParser(description="Build a review-only index of current manual action-photo surfaces.")
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
