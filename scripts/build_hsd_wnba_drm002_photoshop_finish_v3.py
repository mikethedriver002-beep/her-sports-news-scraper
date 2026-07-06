from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]


VERSION = "hsd-wnba-drm002-photoshop-finish-v3-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_drm002_photoshop_finish_v3.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_drm002_photoshop_finish_v3")
DEFAULT_LATEST_OUTPUT_DIR = Path("outputs/local/latest/files/wnba_drm002_photoshop_finish_v3")
DEFAULT_INTAKE_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
)
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "photoshop_finish_review_intake.csv"
LAYER_MAP_NAME = "layer_map.md"
BUNDLE_NAME = "wnba_drm002_photoshop_finish_v3_bundle.zip"


VARIANT_SPECS: list[dict[str, Any]] = [
    {
        "variant_id": "drm002_raw_friction_lux",
        "variant_name": "DRM002 Raw Friction Lux",
        "output_base": "variant_01_drm002_raw_friction_lux",
        "scale_height": 1600,
        "crop_center": 0.735,
        "crop_top": 118,
        "kicker": "WNBA CASE STUDY",
        "kicker_top": 108,
        "kicker_size": 12,
        "kicker_tracking": 210,
        "headline": "RAW|FRICTION",
        "headline_top": 1012,
        "headline_left": 72,
        "headline_size": 32,
        "headline_leading": 31,
        "headline_tracking": 6,
        "scrim_opacity": 23,
        "footer": "DRM002 // REVIEW ONLY",
        "footer_size": 10,
        "footer_tracking": 210,
        "decision": "keep",
        "note": "lead route; best balance of aggression and polish, with the type finally feeling designed instead of pasted on",
    },
    {
        "variant_id": "drm002_luxury_pressure",
        "variant_name": "DRM002 Luxury Pressure",
        "output_base": "variant_02_drm002_luxury_pressure",
        "scale_height": 1600,
        "crop_center": 0.75,
        "crop_top": 118,
        "kicker": "EDITORIAL NOTE",
        "kicker_top": 108,
        "kicker_size": 12,
        "kicker_tracking": 220,
        "headline": "UNYIELDING|PRESSURE",
        "headline_top": 968,
        "headline_left": 72,
        "headline_size": 28,
        "headline_leading": 28,
        "headline_tracking": 8,
        "scrim_opacity": 23,
        "footer": "REVIEW ONLY",
        "footer_size": 10,
        "footer_tracking": 210,
        "decision": "keep",
        "note": "most refined backup; quieter and more expensive, but it gives up some of the lead comp's bite",
    },
    {
        "variant_id": "drm002_quiet_casefile",
        "variant_name": "DRM002 Quiet Casefile",
        "output_base": "variant_03_drm002_quiet_casefile",
        "scale_height": 1600,
        "crop_center": 0.73,
        "crop_top": 118,
        "kicker": "REVIEW FILE",
        "kicker_top": 108,
        "kicker_size": 12,
        "kicker_tracking": 225,
        "headline": "MOTION|STUDY",
        "headline_top": 1038,
        "headline_left": 72,
        "headline_size": 26,
        "headline_leading": 26,
        "headline_tracking": 10,
        "scrim_opacity": 21,
        "footer": "LOCAL QUARANTINE",
        "footer_size": 10,
        "footer_tracking": 210,
        "decision": "kill",
        "note": "too restrained; tasteful, but it sands off the image tension and stops feeling like a cover",
    },
]


def load_module(filename: str, name: str):
    script_path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V1 = load_module("build_hsd_wnba_drm002_photoshop_finish_v1.py", "build_hsd_wnba_drm002_photoshop_finish_v1")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


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
            f'id:"{V1.js_string(spec["variant_id"])}",'
            f'name:"{V1.js_string(spec["variant_name"])}",'
            f'scaleHeight:{spec["scale_height"]},'
            f'cropCenter:{spec["crop_center"]},'
            f'cropTop:{spec["crop_top"]},'
            f'kicker:"{V1.js_string(spec["kicker"])}",'
            f'kickerTop:{spec["kicker_top"]},'
            f'kickerSize:{spec["kicker_size"]},'
            f'kickerTracking:{spec["kicker_tracking"]},'
            f'headline:"{V1.js_string(spec["headline"])}",'
            f'headlineTop:{spec["headline_top"]},'
            f'headlineLeft:{spec["headline_left"]},'
            f'headlineSize:{spec["headline_size"]},'
            f'headlineLeading:{spec["headline_leading"]},'
            f'headlineTracking:{spec["headline_tracking"]},'
            f'scrimOpacity:{spec["scrim_opacity"]},'
            f'footer:"{V1.js_string(spec["footer"])}",'
            f'footerSize:{spec["footer_size"]},'
            f'footerTracking:{spec["footer_tracking"]},'
            f'outBase:"{V1.js_string(spec["output_base"])}",'
            f'outPng:"{V1.js_string(export_dir / (spec["output_base"] + ".png"))}",'
            f'outPsd:"{V1.js_string(working_dir / (spec["output_base"] + ".psd"))}"'
            "}"
        )
    jobs_js = ",\n  ".join(jobs)
    return f"""#target photoshop
app.displayDialogs = DialogModes.NO;

var SOURCE_PATH = "{V1.js_string(source_path)}";
var RESULT_PATH = "{V1.js_string(result_path)}";
var PROOF_PATH = "{V1.js_string(proof_dir / 'photoshop_finish_result.json')}";
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

function addScrim(doc, opacityPercent) {{
  var layer = doc.artLayers.add();
  layer.name = "global_scrim";
  doc.activeLayer = layer;
  doc.selection.selectAll();
  doc.selection.fill(blackColor());
  doc.selection.deselect();
  layer.opacity = opacityPercent;
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

function addSoftShadow(doc, opacityPercent) {{
  var layer = doc.artLayers.add();
  layer.name = "bottom_shadow";
  doc.activeLayer = layer;
  doc.selection.select([
      [new UnitValue(0, "px"), new UnitValue(860, "px")],
      [new UnitValue(1080, "px"), new UnitValue(860, "px")],
      [new UnitValue(1080, "px"), new UnitValue(1350, "px")],
      [new UnitValue(0, "px"), new UnitValue(1350, "px")]
  ]);
  doc.selection.fill(blackColor());
  doc.selection.deselect();
  layer.opacity = opacityPercent;
}}

function finishOne(job) {{
  var src = app.open(new File(SOURCE_PATH));
  src.resizeImage(null, new UnitValue(job.scaleHeight, "px"), null, ResampleMethod.BICUBICSHARPER);
  var fullWidth = src.width.as("px");
  var fullHeight = src.height.as("px");
  var cropWidth = 1080;
  var cropHeight = 1350;
  var cropLeft = Math.round((fullWidth - cropWidth) * job.cropCenter);
  if (cropLeft < 0) cropLeft = 0;
  if (cropLeft > fullWidth - cropWidth) cropLeft = Math.round(fullWidth - cropWidth);
  var cropTop = job.cropTop;
  if (cropTop < 0) cropTop = 0;
  if (cropTop > fullHeight - cropHeight) cropTop = Math.round(fullHeight - cropHeight);
  src.crop([
    new UnitValue(cropLeft, "px"),
    new UnitValue(cropTop, "px"),
    new UnitValue(cropLeft + cropWidth, "px"),
    new UnitValue(cropTop + cropHeight, "px")
  ]);

  addScrim(src, job.scrimOpacity);
  addSoftShadow(src, 18);
  addTextLayer(src, "kicker", job.kicker, 74, job.kickerTop, job.kickerSize, job.kickerTracking, job.kickerSize + 2, false);
  addTextLayer(
    src,
    "headline",
    job.headline.replace(/\\|/g, "\\r"),
    job.headlineLeft,
    job.headlineTop,
    job.headlineSize,
    job.headlineTracking,
    job.headlineLeading,
    true
  );
  addTextLayer(src, "footer", job.footer, 76, 1288, job.footerSize, job.footerTracking, job.footerSize + 2, false);

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
                "crop_top": spec["crop_top"],
                "scale_height": spec["scale_height"],
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


def build_contact_sheet(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for contact sheet generation")
    sheet = Image.new("RGB", (1080, 1350), (10, 12, 16))
    draw = ImageDraw.Draw(sheet)
    title_font = V1.load_font(36, bold=True)
    label_font = V1.load_font(20, bold=True)
    small_font = V1.load_font(17, bold=False)
    draw.text((34, 26), "WNBA DRM002 PHOTOSHOP FINISH V3", fill=(245, 246, 248), font=title_font)
    draw.text((34, 68), "Luxury editorial refinement from the local DRM002 quarantine asset. Review-only. No downloads, approvals, or publishing.", fill=(184, 192, 205), font=small_font)
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
        wrapped = V1.wrap_text(draw, f"{row['decision'].upper()} // {row['note']}", small_font, tile_w - 8)
        for line_index, line in enumerate(wrapped[:3]):
            draw.text((x, y + tile_h + 44 + (line_index * 22)), line, fill=(202, 212, 226), font=small_font)
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path)
    return path


def build_layer_map(output_dir: Path, rows: list[dict[str, Any]], source_path: Path) -> Path:
    lines = [
        "# DRM002 Photoshop layer map v3",
        "",
        f"- source: {source_path.as_posix()}",
        f"- layered working reference: {(output_dir / 'working' / 'drm002_photoshop_finish_v3_master.psd').as_posix()}",
        "",
        "## Variants",
    ]
    for row in rows:
        lines.append(f"- {row['variant_id']}: {row['working_psd_path']}")
    return write_text(output_dir / LAYER_MAP_NAME, "\n".join(lines) + "\n")


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


def build_report(manifest: dict[str, Any]) -> str:
    rows = manifest["variant_rows"]
    table = "\n".join(
        f"| `{row['variant_id']}` | {row['variant_name']} | {row['decision'].upper()} | `{row['render_path']}` | {row['note']} |"
        for row in rows
    )
    return f"""# WNBA DRM002 Photoshop Finish Pass V3

Status: `{manifest['status']}`
Version: `{manifest['version']}`

This is a review-only Photoshop-first editorial v3 pass from the local DRM002 quarantine asset.

## Blunt Read

- Best premium route: `{manifest['best_variant_id']}`
- Keep: `drm002_raw_friction_lux`, `drm002_luxury_pressure`
- Kill: `drm002_quiet_casefile`
- Verdict: ALMOST MERGE-WORTHY
- Why: the lead finally feels luxurious enough to defend, but the backup still proves we are one polish pass away from something truly finished.
- Hard boundary: no downloads, no approvals, no `.approved`, no protected movement, no publish-ready lane, no publishing.

## Photoshop Proof

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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only Photoshop finish v3 for DRM002.")
    parser.add_argument("--intake-csv", default=DEFAULT_INTAKE_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--no-latest", action="store_true")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--timeout-sec", type=int, default=150)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None).resolve(strict=False)
    export_dir = output_dir / "photoshop_exports"
    working_dir = output_dir / "working"
    proof_dir = output_dir / "proof"
    for path in [output_dir, export_dir, working_dir, proof_dir]:
        path.mkdir(parents=True, exist_ok=True)

    runner_manifest = V1.verify_runner(timeout_sec=min(args.timeout_sec, 90))
    result_path = working_dir / "photoshop_finish_result.json"
    jsx_path = working_dir / "photoshop_finish_v3.jsx"
    source_path = V1.resolve_drm002_source_asset(resolve_path(args.intake_csv))
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
        str(args.timeout_sec),
    ]
    completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True, timeout=args.timeout_sec + 30)
    wrapper_payload = json.loads(completed.stdout.strip()) if completed.stdout.strip() else {}
    if completed.returncode != 0 or not result_path.exists():
        raise RuntimeError(f"Photoshop finish v3 failed: stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}")

    photoshop_result = json.loads(result_path.read_text(encoding="utf-8"))
    if not photoshop_result.get("ok"):
        raise RuntimeError(f"Photoshop JSX result was not ok: {photoshop_result}")

    rows = load_rows_for_manifest(output_dir)
    contact_sheet_path = build_contact_sheet(output_dir, rows)
    layer_map_path = build_layer_map(output_dir, rows, source_path)
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
        "generated_at_utc": V1.now_iso(),
        "status": "wnba_drm002_photoshop_finish_v3_ready",
        "repo_head": args.head_commit.strip(),
        "source_image_path": source_path.as_posix(),
        "source_url": "https://dream.wnba.com/news/dream-scores-a-win-in-reeses-return-to-chicago-howard-makes-history",
        "resolved_image_url": "https://cdn.wnba.com/sites/1611661330/2026/06/6.9-story.png",
        "output_dir": output_dir.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "bundle_zip_path": bundle_zip_path.as_posix(),
        "manifest_path": (output_dir / MANIFEST_NAME).as_posix(),
        "report_path": (output_dir / REPORT_NAME).as_posix(),
        "layer_map_path": layer_map_path.as_posix(),
        "variant_count": len(rows),
        "best_variant_id": "drm002_raw_friction_lux",
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

    latest = None if args.no_latest else resolve_path(args.latest_output_dir)
    if latest:
        V1.mirror_latest(output_dir, latest.resolve(strict=False))

    print(
        json.dumps(
            {
                "output_dir": output_dir.as_posix(),
                "status": manifest["status"],
                "variant_count": manifest["variant_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
