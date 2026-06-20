from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

VERSION = "v1.0-phase6f-visual-approval-packet"
OUT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4")
APPROVAL_DIR = OUT / "approval"
NEAR_POST_PATHS = [
    Path("near_post_ready_v4_report.json"),
    OUT / "near_post_ready" / "near_post_ready_v4_report.json",
]
MANIFEST_PATH = OUT / "hsd_template_renderer_v4_manifest.csv"
POLICY_PATH = Path("config/graphics/v4/approval/visual_approval_policy_v4.json")

CANDIDATES_CSV = APPROVAL_DIR / "visual_approval_candidates_v4.csv"
DECISIONS_TEMPLATE_CSV = APPROVAL_DIR / "visual_approval_decisions_template_v4.csv"
PACKET_MD = APPROVAL_DIR / "visual_approval_packet_v4.md"
REPORT_JSON = APPROVAL_DIR / "visual_approval_packet_v4_report.json"
REPORT_MD = APPROVAL_DIR / "visual_approval_packet_v4_report.md"
CONTACT_SHEET = APPROVAL_DIR / "visual_approval_contact_sheet_v4.jpg"

CANDIDATE_FIELDS = [
    "approval_id", "approval_status", "decision", "reviewer", "reviewed_at", "reason",
    "render_sha256", "item_id", "template_id", "platform", "variant", "module_mode", "headline",
    "output_path", "width", "height", "near_post_ready_candidate", "fixture_only_player_asset",
    "placeholder_layer_count", "zone_overflow_count", "team_logo_count", "team_logo_modes", "player_assets_used",
    "player_names", "player_asset_kind", "mask_compliance_status", "outside_changed_ratio", "inside_changed_ratio",
    "fidelity_score", "notes", "reasons",
]
DECISION_FIELDS = ["approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"]


def clean(value: Any) -> str:
    return str(value or "").strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def locate_near_post_report(root: Path) -> Path:
    for rel in NEAR_POST_PATHS:
        candidate = root / rel
        if candidate.exists():
            return candidate
    raise FileNotFoundError("near_post_ready_v4_report.json not found")


def row_to_bool(value: Any) -> bool:
    return clean(value).lower() in {"true", "1", "yes", "y"}


def row_int(value: Any) -> int:
    try:
        return int(float(clean(value)))
    except Exception:
        return 0


def candidate_status(row: Dict[str, Any]) -> str:
    if not row_to_bool(row.get("near_post_ready_candidate")):
        return "review_only_not_candidate"
    if row_to_bool(row.get("fixture_only_player_asset")):
        return "review_only_fixture_player"
    if row_int(row.get("placeholder_layer_count")) > 0:
        return "blocked_placeholder_layer"
    if row_int(row.get("zone_overflow_count")) > 0:
        return "blocked_zone_overflow"
    if clean(row.get("mask_compliance_status")) and clean(row.get("mask_compliance_status")) != "passed_mask_compliance":
        return "blocked_mask_compliance"
    return "approval_candidate"


def make_approval_id(row: Dict[str, Any], render_sha: str) -> str:
    seed = "|".join([
        clean(row.get("item_id")), clean(row.get("template_id")), clean(row.get("platform")),
        clean(row.get("module_mode")), render_sha[:16]
    ])
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def read_fidelity_scores(root: Path) -> Dict[str, str]:
    path = root / "template_fidelity_v4_report.json"
    if not path.exists():
        path = root / OUT / "fidelity" / "template_fidelity_v4_report.json"
    data = read_json(path)
    scores = {}
    for row in data.get("rows") or []:
        scores[clean(row.get("item_id"))] = clean(row.get("overall_score"))
    return scores


def build_candidates(root: Path) -> List[Dict[str, Any]]:
    near_path = locate_near_post_report(root)
    data = read_json(near_path)
    scores = read_fidelity_scores(root)
    rows: List[Dict[str, Any]] = []
    for raw in data.get("rows") or []:
        row = dict(raw)
        output_path = root / clean(row.get("output_path"))
        render_sha = sha256(output_path) if output_path.exists() else ""
        status = candidate_status(row)
        candidate = {
            "approval_id": make_approval_id(row, render_sha),
            "approval_status": status,
            "decision": "",
            "reviewer": "",
            "reviewed_at": "",
            "reason": "",
            "render_sha256": render_sha,
            "item_id": clean(row.get("item_id")),
            "template_id": clean(row.get("template_id")),
            "platform": clean(row.get("platform")),
            "variant": clean(row.get("variant")),
            "module_mode": clean(row.get("module_mode")),
            "headline": clean(row.get("headline")),
            "output_path": clean(row.get("output_path")),
            "width": clean(row.get("width")),
            "height": clean(row.get("height")),
            "near_post_ready_candidate": clean(row.get("near_post_ready_candidate")),
            "fixture_only_player_asset": clean(row.get("fixture_only_player_asset")),
            "placeholder_layer_count": clean(row.get("placeholder_layer_count")),
            "zone_overflow_count": clean(row.get("zone_overflow_count")),
            "team_logo_count": clean(row.get("team_logo_count")),
            "team_logo_modes": clean(row.get("team_logo_modes")),
            "player_assets_used": clean(row.get("player_assets_used")),
            "player_names": clean(row.get("player_names")),
            "player_asset_kind": clean(row.get("player_asset_kind")),
            "mask_compliance_status": clean(row.get("mask_compliance_status")),
            "outside_changed_ratio": clean(row.get("outside_changed_ratio")),
            "inside_changed_ratio": clean(row.get("inside_changed_ratio")),
            "fidelity_score": scores.get(clean(row.get("item_id")), ""),
            "notes": clean(row.get("notes")),
            "reasons": clean(row.get("reasons")),
        }
        rows.append(candidate)
    return rows


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for raw in candidates:
        path = Path(raw)
        if path.exists():
            return ImageFont.truetype(path.as_posix(), size=size)
    return ImageFont.load_default()


def build_contact_sheet(root: Path, rows: List[Dict[str, Any]]) -> None:
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        return
    columns = 2
    cell_w, cell_h = 540, 560
    header_h = 92
    sheet = Image.new("RGB", (columns * cell_w + 40, math.ceil(len(rows) / columns) * cell_h + header_h + 30), (238, 238, 238))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(24)
    label_font = load_font(15)
    small_font = load_font(13)
    draw.text((24, 22), "HSD Phase 6F Visual Approval Packet", fill=(15, 15, 15), font=title_font)
    draw.text((24, 56), "Approve by approval_id + render_sha256. Fixture-only player proofs cannot be approved.", fill=(70, 70, 70), font=small_font)
    for idx, row in enumerate(rows):
        col = idx % columns
        row_i = idx // columns
        x0 = 20 + col * cell_w
        y0 = header_h + row_i * cell_h
        render_path = root / row["output_path"]
        if render_path.exists():
            img = Image.open(render_path).convert("RGB")
            img.thumbnail((500, 410), Image.Resampling.LANCZOS)
            sheet.paste(img, (x0 + (500 - img.width)//2 + 10, y0 + 10))
        status = row["approval_status"]
        color = (10, 105, 45) if status == "approval_candidate" else (150, 70, 0)
        draw.text((x0 + 10, y0 + 425), f"{idx+1}. {status}", fill=color, font=label_font)
        draw.text((x0 + 10, y0 + 450), f"ID: {row['approval_id']}", fill=(20,20,20), font=small_font)
        draw.text((x0 + 10, y0 + 472), f"{row['template_id']} • {row['platform']} • {row['module_mode']}", fill=(50,50,50), font=small_font)
        draw.text((x0 + 10, y0 + 494), row["headline"][:64], fill=(50,50,50), font=small_font)
        draw.text((x0 + 10, y0 + 516), f"score={row.get('fidelity_score','')} fixture={row['fixture_only_player_asset']} hash={row['render_sha256'][:12]}", fill=(80,80,80), font=small_font)
    sheet.save(CONTACT_SHEET, quality=92)


def build_packet_md(rows: List[Dict[str, Any]], report: Dict[str, Any]) -> str:
    approval_candidates = [r for r in rows if r["approval_status"] == "approval_candidate"]
    review_rows = [r for r in rows if r["approval_status"] != "approval_candidate"]
    lines = [
        "# HSD Phase 6F Visual Approval Packet",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Total rows: `{len(rows)}`",
        f"Approval candidates: `{len(approval_candidates)}`",
        f"Review-only / blocked rows: `{len(review_rows)}`",
        "",
        "## How to approve",
        "",
        "Copy `visual_approval_decisions_template_v4.csv` to `config/graphics/v4/approval/visual_approval_decisions_v4.csv`.",
        "For each row you approve, set `decision` to `approved`, add a reviewer name, review timestamp, reason, and keep the exact `render_sha256`.",
        "Use `rejected`, `needs_fix`, or `hold` for anything that should not move forward.",
        "",
        "Do not approve fixture-only player reference rows. They are proof-only until replaced by a real approved player asset.",
        "",
        "## Approval candidates",
        "",
    ]
    for r in approval_candidates:
        lines += [
            f"### {r['approval_id']} — {r['template_id']} / {r['platform']}",
            f"- Headline: {r['headline']}",
            f"- Module: {r['module_mode']}",
            f"- Fidelity score: {r['fidelity_score']}",
            f"- Render hash: `{r['render_sha256']}`",
            f"- Output: `{r['output_path']}`",
            "",
        ]
    lines += ["## Review-only / cannot approve yet", ""]
    for r in review_rows:
        lines += [
            f"- `{r['approval_id']}` — {r['approval_status']} — {r['template_id']} / {r['platform']} / {r['module_mode']} — {r['reasons'] or 'see candidate CSV'}",
        ]
    lines += [
        "",
        "## Cutover policy",
        "",
        "Phase 6F can create an approved operator handoff manifest, but production cutover remains blocked until a separate cutover PR explicitly changes promotion routing.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    global APPROVAL_DIR, CANDIDATES_CSV, DECISIONS_TEMPLATE_CSV, PACKET_MD, REPORT_JSON, REPORT_MD, CONTACT_SHEET
    APPROVAL_DIR = root / APPROVAL_DIR
    CANDIDATES_CSV = root / CANDIDATES_CSV
    DECISIONS_TEMPLATE_CSV = root / DECISIONS_TEMPLATE_CSV
    PACKET_MD = root / PACKET_MD
    REPORT_JSON = root / REPORT_JSON
    REPORT_MD = root / REPORT_MD
    CONTACT_SHEET = root / CONTACT_SHEET
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

    rows = build_candidates(root)
    approval_candidates = [r for r in rows if r["approval_status"] == "approval_candidate"]
    review_rows = [r for r in rows if r["approval_status"] != "approval_candidate"]
    blockers: List[str] = []
    if not rows:
        blockers.append("no_visual_approval_rows")
    if not approval_candidates:
        blockers.append("no_approval_candidates")
    write_csv(CANDIDATES_CSV, rows, CANDIDATE_FIELDS)
    decision_rows = [{field: "" for field in DECISION_FIELDS} | {"approval_id": r["approval_id"], "render_sha256": r["render_sha256"]} for r in approval_candidates]
    write_csv(DECISIONS_TEMPLATE_CSV, decision_rows, DECISION_FIELDS)
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "visual_approval_packet_ready" if not blockers else "blocked_visual_approval_packet",
        "strict_exit_code": 0 if not blockers else 2,
        "total_rows": len(rows),
        "approval_candidates": len(approval_candidates),
        "review_only_rows": len(review_rows),
        "blockers": blockers,
        "human_visual_approval_required": True,
        "production_cutover_allowed": False,
        "limited_operator_handoff_allowed_after_approval": True,
        "outputs": {
            "candidates_csv": CANDIDATES_CSV.as_posix(),
            "decisions_template_csv": DECISIONS_TEMPLATE_CSV.as_posix(),
            "packet_md": PACKET_MD.as_posix(),
            "contact_sheet": CONTACT_SHEET.as_posix(),
        },
    }
    build_contact_sheet(root, rows)
    PACKET_MD.write_text(build_packet_md(rows, report), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_MD.write_text("\n".join([
        "# HSD Phase 6F Visual Approval Packet Report",
        "",
        f"Status: `{report['status']}`",
        f"Total rows: `{len(rows)}`",
        f"Approval candidates: `{len(approval_candidates)}`",
        f"Review-only rows: `{len(review_rows)}`",
        f"Blockers: `{blockers}`",
        "",
        "Production cutover remains blocked. Human approval by render hash is required.",
        "",
    ]), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
