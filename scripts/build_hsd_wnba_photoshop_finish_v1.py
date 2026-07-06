from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts import build_hsd_wnba_editorial_rescue_v1 as rescue

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


VERSION = "hsd-wnba-photoshop-finish-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_photoshop_finish_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_photoshop_finish_v1")
CANVAS = {"width": 1080, "height": 1350}
TARGET_VARIANTS = {"jackie_final_cover", "aja_control_line"}
CONTACT_SHEET_NAME = "photoshop_finish_contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "photoshop_finish_review_intake.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def js_string(value: str | Path) -> str:
    return str(value).replace("\\", "/").replace('"', r"\"")


def build_photoshop_jsx(rows: list[dict[str, Any]], result_path: Path) -> str:
    jobs = []
    for row in rows:
        jobs.append(
            "{"
            f'id:"{js_string(row["variant_id"])}",'
            f'inPath:"{js_string(row["base_render_path"])}",'
            f'outPath:"{js_string(row["photoshop_render_path"])}"'
            "}"
        )
    jobs_js = ",\n  ".join(jobs)
    return f"""#target photoshop
app.displayDialogs = DialogModes.NO;

var jobs = [
  {jobs_js}
];
var resultFile = new File("{js_string(result_path)}");
var results = [];

function finishOne(job) {{
  var inputFile = new File(job.inPath);
  var outputFile = new File(job.outPath);
  outputFile.parent.create();

  var doc = app.open(inputFile);
  doc.flatten();
  doc.bitsPerChannel = BitsPerChannelType.EIGHT;

  try {{
    doc.activeLayer.applyUnSharpMask(92, 1.15, 3);
  }} catch (sharpError) {{}}

  try {{
    doc.activeLayer.adjustBrightnessContrast(3, 9);
  }} catch (contrastError) {{}}

  var pngOptions = new PNGSaveOptions();
  doc.saveAs(outputFile, pngOptions, true, Extension.LOWERCASE);
  doc.close(SaveOptions.DONOTSAVECHANGES);
  results.push('{{"variant_id":"' + job.id + '","status":"exported","path":"' + job.outPath + '"}}');
}}

for (var i = 0; i < jobs.length; i++) {{
  finishOne(jobs[i]);
}}

resultFile.parent.create();
resultFile.open("w");
resultFile.write('{{"ok":true,"photoshop_version":"' + app.version + '","results":[' + results.join(",") + ']}}');
resultFile.close();
"""


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


def build_contact_sheet(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for contact sheet generation")
    sheet = Image.new("RGB", (CANVAS["width"], CANVAS["height"]), (12, 14, 18))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(36, bold=True)
    label_font = load_font(20, bold=True)
    small_font = load_font(17, bold=False)
    draw.text((34, 26), "WNBA PHOTOSHOP FINISH V1", fill=(245, 246, 248), font=title_font)
    draw.text((34, 68), "Review-only Photoshop pass. Jackie lead, A'ja backup. No downloads, approvals, or publishing.", fill=(184, 192, 205), font=small_font)
    tile_w = 486
    tile_h = 608
    for index, row in enumerate(rows):
        x = 34 + index * (tile_w + 36)
        y = 116
        with Image.open(row["photoshop_render_path"]) as image:
            thumb = image.convert("RGB").resize((tile_w, tile_h))
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + tile_w, y + tile_h), outline=(235, 238, 244), width=2)
        draw.text((x, y + tile_h + 18), row["variant_id"], fill=(246, 247, 250), font=label_font)
        draw.text((x, y + tile_h + 48), row["decision"].upper(), fill=(202, 212, 226), font=small_font)
        draw.text((x, y + tile_h + 76), "Photoshop finish: unsharp mask + contrast pass", fill=(164, 174, 188), font=small_font)
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path)
    return path


def build_report(manifest: dict[str, Any]) -> str:
    rows = manifest["variant_rows"]
    table = "\n".join(
        f"| `{row['variant_id']}` | {row['decision'].upper()} | `{row['photoshop_render_path']}` | {row['known_limit']} |"
        for row in rows
    )
    return f"""# WNBA Photoshop Finish V1

Status: `{manifest['status']}`
Version: `{manifest['version']}`

This is a review-only Photoshop-first finishing pass for the two carry-forward routes only: `jackie_final_cover` and `aja_control_line`.

## Blunt Read

- Keep: `jackie_final_cover`
- Backup: `aja_control_line`
- Kill: any APCS039/HUD/bracket/rail/lower-gradient language
- Ceiling: this improves finish discipline and sharpness, but it does not turn local player images into real action photography.

## Photoshop Tool Rationale

- Photoshop used: `{str(manifest['photoshop_used']).lower()}`
- Photoshop version: `{manifest['photoshop_version']}`
- Wrapper command: `{manifest['photoshop_command']}`
- Cleanup verification: `{manifest['photoshop_cleanup_status']}`

## Variant Table

| Variant | Decision | Export | Known Limit |
| --- | --- | --- | --- |
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


def build_packet(*, output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    base_dir = output_dir / "base_rescue"
    photoshop_dir = output_dir / "photoshop_exports"
    working_dir = output_dir / "working"
    for path in [output_dir, base_dir, photoshop_dir, working_dir]:
        path.mkdir(parents=True, exist_ok=True)

    base_manifest = rescue.build_packet(output_dir=base_dir, head_commit=head_commit)
    target_rows: list[dict[str, Any]] = []
    for row in base_manifest["variant_rows"]:
        if row["variant_id"] not in TARGET_VARIANTS:
            continue
        output_name = Path(row["render_path"]).name.replace(".png", "_photoshop_finish.png")
        target_rows.append(
            {
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "decision": row["decision"],
                "known_limit": row["known_limit"],
                "base_render_path": row["render_path"],
                "photoshop_render_path": (photoshop_dir / output_name).as_posix(),
            }
        )

    result_path = working_dir / "photoshop_finish_result.json"
    jsx_path = working_dir / "photoshop_finish.jsx"
    write_text(jsx_path, build_photoshop_jsx(target_rows, result_path))

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
        "120",
    ]
    completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True, timeout=150)
    wrapper_payload = json.loads(completed.stdout.strip()) if completed.stdout.strip() else {}
    if completed.returncode != 0 or not result_path.exists():
        raise RuntimeError(f"Photoshop finish failed: stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}")

    photoshop_result = json.loads(result_path.read_text(encoding="utf-8"))
    if not photoshop_result.get("ok"):
        raise RuntimeError(f"Photoshop JSX result was not ok: {photoshop_result}")

    contact_sheet_path = build_contact_sheet(output_dir, target_rows)
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
        "status": "wnba_photoshop_finish_ready",
        "repo_head": head_commit,
        "output_dir": output_dir.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "manifest_path": (output_dir / MANIFEST_NAME).as_posix(),
        "report_path": (output_dir / REPORT_NAME).as_posix(),
        "base_manifest_path": base_manifest["manifest_path"],
        "variant_count": len(target_rows),
        "best_variant_id": "jackie_final_cover",
        "variant_rows": target_rows,
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
                "base_render_path": row["base_render_path"],
                "photoshop_render_path": row["photoshop_render_path"],
                "review_only": "true",
                "photoshop_used": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
            for row in target_rows
        ],
        [
            "variant_id",
            "decision",
            "base_render_path",
            "photoshop_render_path",
            "review_only",
            "photoshop_used",
            "asset_downloads",
            "approval_state_change",
            "publish_ready",
            "publishing",
        ],
    )
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only Photoshop finish for WNBA Jackie/A'ja routes.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(output_dir=resolve_output_dir(args.output_dir or None), head_commit=args.head_commit.strip())
    print(json.dumps({"status": manifest["status"], "output_dir": manifest["output_dir"], "variant_count": manifest["variant_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
