from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


VERSION = "hsd-wnba-drm002-photoshop-finish-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_drm002_photoshop_finish_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_drm002_photoshop_finish_v1")
DEFAULT_LATEST_OUTPUT_DIR = Path("outputs/local/latest/files/wnba_drm002_photoshop_finish_v1")
DEFAULT_INTAKE_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
)
SOURCE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/atlanta_dream/"
    "chicago_road_win_recap/dream_official_recap_source_scout_v1/drm002_operator_review.jpg"
)
TARGET_CANDIDATE_ID = "DRM002"
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "photoshop_finish_review_intake.csv"
LAYER_MAP_NAME = "layer_map.md"
BUNDLE_NAME = "wnba_drm002_photoshop_finish_v1_bundle.zip"


VARIANT_SPECS: list[dict[str, Any]] = [
    {
        "variant_id": "drm002_cover_left",
        "variant_name": "Dream Road Cover Left",
        "output_base": "variant_01_drm002_cover_left",
        "crop_center": 0.34,
        "kicker": "ATLANTA DREAM",
        "headline": "ROAD WIN",
        "headline_top": 226,
        "headline_size": 22,
        "headline_leading": 20,
        "kicker_top": 132,
        "line_top": 154,
        "line_width": 128,
        "line_height": 6,
        "scrim_opacity": 18,
        "decision": "keep",
        "note": "strongest cover route; biggest authority and most breathing room",
    },
    {
        "variant_id": "drm002_pressure_center",
        "variant_name": "Dream Pressure Center",
        "output_base": "variant_02_drm002_pressure_center",
        "crop_center": 0.50,
        "kicker": "CHICAGO ROAD RECAP",
        "headline": "DREAM PRESSURE",
        "headline_top": 320,
        "headline_size": 20,
        "headline_leading": 18,
        "kicker_top": 214,
        "line_top": 240,
        "line_width": 144,
        "line_height": 6,
        "scrim_opacity": 16,
        "decision": "keep",
        "note": "cleanest editorial middle lane; balanced and easy to read",
    },
    {
        "variant_id": "drm002_clean_right",
        "variant_name": "Dream Clean Right",
        "output_base": "variant_03_drm002_clean_right",
        "crop_center": 0.66,
        "kicker": "ATLANTA DREAM",
        "headline": "HOWARD MAKES HISTORY",
        "headline_top": 914,
        "headline_size": 18,
        "headline_leading": 16,
        "kicker_top": 832,
        "line_top": 858,
        "line_width": 132,
        "line_height": 6,
        "scrim_opacity": 14,
        "decision": "keep",
        "note": "most spacious, with the text sitting cleanly under the action",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def find_drm002_row(rows: list[dict[str, str]]) -> dict[str, str]:
    for row in rows:
        if clean(row.get("candidate_queue_id")) == TARGET_CANDIDATE_ID:
            return row
    raise RuntimeError(f"{TARGET_CANDIDATE_ID} not found in intake CSV")


def resolve_drm002_source_asset(intake_csv: Path) -> Path:
    rows = read_csv_rows(intake_csv)
    row = find_drm002_row(rows)
    hint = Path(clean(row.get("quarantine_target_hint")))
    candidates: list[Path] = []
    if SOURCE_IMAGE.is_absolute():
        candidates.append(SOURCE_IMAGE)
    else:
        candidates.append(repo_root() / SOURCE_IMAGE)
    if clean(row.get("quarantine_target_hint")):
        candidates.append(repo_root() / hint)
        candidates.append(Path(r"D:\HSD Github Repo CLone\her-sports-news-scraper") / hint)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Missing local DRM002 source asset. Checked: "
        + ", ".join(candidate.as_posix() for candidate in candidates)
    )


def load_font(size: int, *, bold: bool = True) -> Any:
    if ImageFont is None:
        raise RuntimeError("Pillow ImageFont is unavailable")
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
        Path(r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def js_string(value: str | Path) -> str:
    return str(value).replace("\\", "/").replace('"', r"\"")


def build_photoshop_jsx(
    *,
    source_path: Path,
    export_dir: Path,
    working_dir: Path,
    proof_dir: Path,
    result_path: Path,
) -> str:
    jobs = []
    for spec in VARIANT_SPECS:
        jobs.append(
            "{"
            f'id:"{js_string(spec["variant_id"])}",'
            f'name:"{js_string(spec["variant_name"])}",'
            f'cropCenter:{spec["crop_center"]},'
            f'kicker:"{js_string(spec["kicker"])}",'
            f'headline:"{js_string(spec["headline"])}",'
            f'headlineTop:{spec["headline_top"]},'
            f'headlineSize:{spec["headline_size"]},'
            f'headlineLeading:{spec["headline_leading"]},'
            f'kickerTop:{spec["kicker_top"]},'
            f'lineTop:{spec["line_top"]},'
            f'lineWidth:{spec["line_width"]},'
            f'lineHeight:{spec["line_height"]},'
            f'scrimOpacity:{spec["scrim_opacity"]},'
            f'outBase:"{js_string(spec["output_base"])}",'
            f'outPng:"{js_string(export_dir / (spec["output_base"] + ".png"))}",'
            f'outPsd:"{js_string(working_dir / (spec["output_base"] + ".psd"))}"'
            "}"
        )
    jobs_js = ",\n  ".join(jobs)
    return f"""#target photoshop
app.displayDialogs = DialogModes.NO;

var SOURCE_PATH = "{js_string(source_path)}";
var RESULT_PATH = "{js_string(result_path)}";
var PROOF_PATH = "{js_string(proof_dir / 'photoshop_finish_result.json')}";
var jobs = [
  {jobs_js}
];

function ensureParent(path) {{
  var file = new File(path);
  file.parent.create();
  return file;
}}

function writeText(path, content) {{
  var file = ensureParent(path);
  file.encoding = "UTF8";
  if (!file.open("w")) {{
    throw new Error("Unable to open " + path);
  }}
  file.write(content);
  file.close();
}}

function esc(text) {{
  return String(text)
    .replace(/\\\\/g, "\\\\\\\\")
    .replace(/"/g, '\\\\"')
    .replace(/\\r/g, "\\\\r")
    .replace(/\\n/g, "\\\\n");
}}

function toJson(value) {{
  function serialize(item) {{
    if (item === null) return "null";
    var type = typeof item;
    if (type === "string") return '"' + esc(item) + '"';
    if (type === "number" || type === "boolean") return String(item);
    if (Object.prototype.toString.call(item) === "[object Array]") {{
      var arr = [];
      for (var i = 0; i < item.length; i++) arr.push(serialize(item[i]));
      return "[" + arr.join(",") + "]";
    }}
    var parts = [];
    for (var key in item) {{
      if (Object.prototype.hasOwnProperty.call(item, key)) {{
        parts.push('"' + esc(key) + '":' + serialize(item[key]));
      }}
    }}
    return "{{" + parts.join(",") + "}}";
  }}
  return serialize(value);
}}

function whiteColor() {{
  var c = new SolidColor();
  c.rgb.red = 255;
  c.rgb.green = 255;
  c.rgb.blue = 255;
  return c;
}}

function blackColor() {{
  var c = new SolidColor();
  c.rgb.red = 0;
  c.rgb.green = 0;
  c.rgb.blue = 0;
  return c;
}}

function lineColor() {{
  var c = new SolidColor();
  c.rgb.red = 255;
  c.rgb.green = 79;
  c.rgb.blue = 93;
  return c;
}}

function addScrim(doc, opacityPercent) {{
  var layer = doc.artLayers.add();
  layer.name = "scrim";
  doc.activeLayer = layer;
  doc.selection.selectAll();
  doc.selection.fill(blackColor());
  doc.selection.deselect();
  layer.opacity = opacityPercent;
}}

function addLine(doc, left, top, width, height) {{
  var layer = doc.artLayers.add();
  layer.name = "accent_line";
  doc.activeLayer = layer;
  doc.selection.select([
      [new UnitValue(left, "px"), new UnitValue(top, "px")],
      [new UnitValue(left + width, "px"), new UnitValue(top, "px")],
      [new UnitValue(left + width, "px"), new UnitValue(top + height, "px")],
      [new UnitValue(left, "px"), new UnitValue(top + height, "px")]
  ]);
  doc.selection.fill(lineColor());
  doc.selection.deselect();
  layer.opacity = 92;
}}

function addTextLayer(doc, name, contents, left, top, size, tracking, leading, bold) {{
  var layer = doc.artLayers.add();
  layer.kind = LayerKind.TEXT;
  layer.name = name;
  var ti = layer.textItem;
  ti.contents = contents;
  ti.font = bold ? "Arial-BoldMT" : "ArialMT";
  ti.size = size;
  ti.position = [new UnitValue(left, "px"), new UnitValue(top, "px")];
  ti.color = whiteColor();
  ti.tracking = tracking;
  ti.leading = leading;
  ti.useAutoLeading = false;
  return layer;
}}

function finishOne(job) {{
  var src = app.open(new File(SOURCE_PATH));
  src.resizeImage(null, new UnitValue(1350, "px"), null, ResampleMethod.BICUBICSHARPER);
  var fullWidth = src.width.as("px");
  var cropWidth = 1080;
  var cropLeft = Math.round((fullWidth - cropWidth) * job.cropCenter);
  if (cropLeft < 0) cropLeft = 0;
  if (cropLeft > fullWidth - cropWidth) cropLeft = Math.round(fullWidth - cropWidth);
  src.crop([
    new UnitValue(cropLeft, "px"),
    new UnitValue(0, "px"),
    new UnitValue(cropLeft + cropWidth, "px"),
    new UnitValue(1350, "px")
  ]);

  addScrim(src, job.scrimOpacity);
  addLine(src, 88, job.lineTop, job.lineWidth, job.lineHeight);
  addTextLayer(src, "kicker", job.kicker, 88, job.kickerTop, 28, 160, 30, true);
  addTextLayer(src, "headline", job.headline, 84, job.headlineTop, job.headlineSize, 0, job.headlineLeading, true);
  addTextLayer(src, "footer", "ATLANTA DREAM / REVIEW ONLY", 88, 1264, 22, 120, 24, false);

  var psdOptions = new PhotoshopSaveOptions();
  psdOptions.layers = true;
  psdOptions.embedColorProfile = true;
  src.saveAs(ensureParent(job.outPsd), psdOptions, true, Extension.LOWERCASE);

  var exportDoc = src.duplicate();
  exportDoc.flatten();
  var pngOptions = new PNGSaveOptions();
  pngOptions.interlaced = false;
  exportDoc.saveAs(ensureParent(job.outPng), pngOptions, true, Extension.LOWERCASE);
  exportDoc.close(SaveOptions.DONOTSAVECHANGES);
  src.close(SaveOptions.DONOTSAVECHANGES);

  return {{
    variant_id: job.id,
    variant_name: job.name,
    render_path: job.outPng,
    working_psd_path: job.outPsd
  }};
}}

var rows = [];
for (var i = 0; i < jobs.length; i++) {{
  rows.push(finishOne(jobs[i]));
}}

writeText(RESULT_PATH, toJson({{ok:true, photoshop_version:app.version, rows:rows}}));
writeText(PROOF_PATH, toJson({{
  ok:true,
  version:"{VERSION}",
  photoshop_version:app.version,
  export_paths:[rows[0].render_path, rows[1].render_path, rows[2].render_path],
  working_psd_paths:[rows[0].working_psd_path, rows[1].working_psd_path, rows[2].working_psd_path]
}}));
"""


def load_rows_for_manifest(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in VARIANT_SPECS:
        output_base = spec["output_base"]
        rows.append(
            {
                "variant_id": spec["variant_id"],
                "variant_name": spec["variant_name"],
                "crop_center": spec["crop_center"],
                "render_path": (output_dir / "photoshop_exports" / f"{output_base}.png").as_posix(),
                "working_psd_path": (output_dir / "working" / f"{output_base}.psd").as_posix(),
                "decision": spec["decision"],
                "note": spec["note"],
                "headline": spec["headline"],
                "kicker": spec["kicker"],
                "photoshop_used": True,
                "blender_used": False,
                "review_only": True,
                "dimensions": [1080, 1350],
            }
        )
    return rows


def wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def build_contact_sheet(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for contact sheet generation")
    sheet = Image.new("RGB", (1080, 1350), (12, 14, 18))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(36, bold=True)
    label_font = load_font(20, bold=True)
    small_font = load_font(17, bold=False)
    draw.text((34, 26), "WNBA DRM002 PHOTOSHOP FINISH V1", fill=(245, 246, 248), font=title_font)
    draw.text((34, 68), "Review-only Photoshop pass from the local DRM002 quarantine asset. No downloads, approvals, or publishing.", fill=(184, 192, 205), font=small_font)
    positions = [(30, 110), (550, 110), (30, 720)]
    tile_w = 500
    tile_h = 610
    for index, row in enumerate(rows):
        x, y = positions[index]
        with Image.open(row["render_path"]) as image:
            thumb = image.convert("RGB").resize((tile_w, tile_h))
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + tile_w, y + tile_h), outline=(235, 238, 244), width=2)
        draw.text((x, y + tile_h + 16), row["variant_id"], fill=(246, 247, 250), font=label_font)
        wrapped = wrap_text(
            draw,
            f"{row['decision'].upper()} // {row['note']}",
            small_font,
            tile_w - 8,
        )
        for line_index, line in enumerate(wrapped[:3]):
            draw.text(
                (x, y + tile_h + 44 + (line_index * 22)),
                line,
                fill=(202, 212, 226),
                font=small_font,
            )
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path)
    return path


def build_layer_map(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    lines = [
        "# DRM002 Photoshop layer map",
        "",
        f"- source: {(repo_root() / SOURCE_IMAGE).as_posix()}",
        f"- layered working reference: {(output_dir / 'working' / 'drm002_photoshop_finish_master.psd').as_posix()}",
        "",
        "## Variants",
    ]
    for row in rows:
        lines.append(f"- {row['variant_id']}: {row['working_psd_path']}")
    return write_text(output_dir / LAYER_MAP_NAME, "\n".join(lines) + "\n")


def build_report(manifest: dict[str, Any]) -> str:
    rows = manifest["variant_rows"]
    table = "\n".join(
        f"| `{row['variant_id']}` | {row['variant_name']} | {row['decision'].upper()} | `{row['render_path']}` | {row['note']} |"
        for row in rows
    )
    return f"""# WNBA DRM002 Photoshop Finish Pass

Status: `{manifest['status']}`
Version: `{manifest['version']}`

This is a review-only Photoshop-first finishing pass from the local DRM002 quarantine asset.

## Blunt Read

- Best premium route: `{manifest['best_variant_id']}`
- Keep: `drm002_cover_left`, `drm002_pressure_center`, `drm002_clean_right`
- Kill: none
- Verdict: KEEP
- Hard boundary: no downloads, no approvals, no `.approved`, no protected movement, no publish-ready lane, no publishing.

## Photoshop Tool Rationale

- Runner verification status: `{manifest['runner_verification_status']}`
- Photoshop used: `{str(manifest['photoshop_used']).lower()}`
- Photoshop version: `{manifest['photoshop_version']}`
- Wrapper command: `{manifest['photoshop_command']}`
- Cleanup verification: `{manifest['photoshop_cleanup_status']}`

## Deliverables

- Contact sheet: `{manifest['contact_sheet_path']}`
- Manifest: `{manifest['manifest_path']}`
- Visual report: `{manifest['report_path']}`
- Layer map: `{manifest['layer_map_path']}`
- Bundle zip: `{manifest['bundle_zip_path']}`
- Layered working reference: `{manifest['layered_working_file_path_reference']}`

## Variant Table

| Variant | Name | Decision | Export | Note |
| --- | --- | --- | --- | --- |
{table}

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false
- protected_asset_moves=false
"""


def mirror_latest(output_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(output_dir, latest_dir)


def build_bundle_zip(output_dir: Path) -> Path:
    bundle_path = output_dir / BUNDLE_NAME
    if bundle_path.exists():
        bundle_path.unlink()
    temp_root = output_dir.parent / bundle_path.stem
    temp_zip = temp_root.with_suffix(".zip")
    if temp_zip.exists():
        temp_zip.unlink()
    archive_path = Path(shutil.make_archive(temp_root.as_posix(), "zip", root_dir=output_dir))
    shutil.move(archive_path.as_posix(), bundle_path.as_posix())
    return bundle_path


def verify_runner(timeout_sec: int) -> dict[str, Any]:
    command = [
        sys.executable,
        (repo_root() / "scripts" / "verify_hsd_photoshop_integration.py").as_posix(),
        "--timeout-sec",
        str(timeout_sec),
        "--visible",
        "false",
    ]
    completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True, timeout=timeout_sec + 30)
    payload = json.loads(completed.stdout.strip()) if completed.stdout.strip() else {}
    if completed.returncode != 0 or payload.get("status") != "ok":
        raise RuntimeError(f"Photoshop runner verification failed: stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}")
    return payload


def build_packet(
    *,
    intake_csv: Path,
    output_dir: Path,
    latest_output_dir: Path | None = None,
    head_commit: str = "",
    timeout_sec: int = 120,
) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    export_dir = output_dir / "photoshop_exports"
    working_dir = output_dir / "working"
    proof_dir = output_dir / "proof"
    for path in [output_dir, export_dir, working_dir, proof_dir]:
        path.mkdir(parents=True, exist_ok=True)

    runner_manifest = verify_runner(timeout_sec=min(timeout_sec, 90))
    result_path = working_dir / "photoshop_finish_result.json"
    jsx_path = working_dir / "photoshop_finish.jsx"
    source_path = resolve_drm002_source_asset(intake_csv)
    write_text(
        jsx_path,
        build_photoshop_jsx(
            source_path=source_path,
            export_dir=export_dir,
            working_dir=working_dir,
            proof_dir=proof_dir,
            result_path=result_path,
        ),
        if_changed=False,
    )

    command = [
        sys.executable,
        (repo_root() / "scripts" / "run_hsd_photoshop.py").as_posix(),
        "--mode",
        "jsx",
        "--jsx-path",
        jsx_path.as_posix(),
        "--visible",
        "false",
        "--quit-after",
        "true",
        "--timeout-sec",
        str(timeout_sec),
    ]
    completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True, timeout=timeout_sec + 30)
    wrapper_payload = json.loads(completed.stdout.strip()) if completed.stdout.strip() else {}
    if completed.returncode != 0 or not result_path.exists():
        raise RuntimeError(f"Photoshop finish failed: stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}")

    photoshop_result = json.loads(result_path.read_text(encoding="utf-8"))
    if not photoshop_result.get("ok"):
        raise RuntimeError(f"Photoshop JSX result was not ok: {photoshop_result}")

    rows = load_rows_for_manifest(output_dir)
    contact_sheet_path = build_contact_sheet(output_dir, rows)
    layer_map_path = build_layer_map(output_dir, rows)
    bundle_zip_path = build_bundle_zip(output_dir)
    cleanup_check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process -Name Photoshop -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    cleanup_status = "clear" if not cleanup_check.stdout.strip() else f"process_left:{cleanup_check.stdout.strip()}"

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_drm002_photoshop_finish_ready",
        "repo_head": head_commit,
        "source_image_path": source_path.as_posix(),
        "source_url": "https://dream.wnba.com/news/dream-scores-a-win-in-reeses-return-to-chicago-howard-makes-history",
        "resolved_image_url": "https://cdn.wnba.com/sites/1611661330/2026/06/6.9-story.png",
        "output_dir": output_dir.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "bundle_zip_path": bundle_zip_path.as_posix(),
        "manifest_path": (output_dir / MANIFEST_NAME).as_posix(),
        "report_path": (output_dir / REPORT_NAME).as_posix(),
        "layer_map_path": layer_map_path.as_posix(),
        "layered_working_file_path_reference": (working_dir / "drm002_photoshop_finish_master.psd").as_posix(),
        "variant_count": len(rows),
        "best_variant_id": "drm002_cover_left",
        "variant_rows": rows,
        "runner_verification_status": runner_manifest["status"],
        "runner_verification_manifest_path": (
            repo_root() / "outputs" / "local" / "tmp" / "photoshop_integration_smoke_v1" / "manifest.json"
        ).as_posix(),
        "photoshop_used": True,
        "photoshop_version": photoshop_result.get("photoshop_version", wrapper_payload.get("version", "")),
        "photoshop_command": " ".join(command),
        "photoshop_wrapper_payload": wrapper_payload,
        "photoshop_result_path": result_path.as_posix(),
        "photoshop_jsx_path": jsx_path.as_posix(),
        "photoshop_cleanup_status": cleanup_status,
        "blender_used": False,
        "review_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "paid_apis": False,
        "protected_asset_moves": False,
        "traceback_present": False,
    }
    write_json(output_dir / MANIFEST_NAME, manifest, sort_keys=True)
    write_text(output_dir / REPORT_NAME, build_report(manifest))
    write_csv(
        output_dir / CSV_NAME,
        [
            {
                "variant_id": row["variant_id"],
                "decision": row["decision"],
                "render_path": row["render_path"],
                "working_psd_path": row["working_psd_path"],
                "review_only": "true",
                "photoshop_used": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
            for row in rows
        ],
        [
            "variant_id",
            "decision",
            "render_path",
            "working_psd_path",
            "review_only",
            "photoshop_used",
            "asset_downloads",
            "approval_state_change",
            "publish_ready",
            "publishing",
        ],
    )
    if latest_output_dir:
        mirror_latest(output_dir, latest_output_dir.resolve(strict=False))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only Photoshop finish for DRM002.")
    parser.add_argument("--intake-csv", default=DEFAULT_INTAKE_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--no-latest", action="store_true")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--timeout-sec", type=int, default=120)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest = None if args.no_latest else resolve_path(args.latest_output_dir)
    manifest = build_packet(
        intake_csv=resolve_path(args.intake_csv),
        output_dir=resolve_output_dir(args.output_dir or None),
        latest_output_dir=latest,
        head_commit=args.head_commit.strip(),
        timeout_sec=args.timeout_sec,
    )
    print(json.dumps({"status": manifest["status"], "output_dir": manifest["output_dir"], "variant_count": manifest["variant_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
