from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_creative_tools import build_photoshop_cli_command, resolve_photoshop_execution


VERSION = "hsd-photoshop-integration-smoke-v1"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/photoshop_integration_smoke_v1")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_smoke_jsx(png_path: Path, proof_path: Path) -> str:
    png_text = png_path.as_posix()
    proof_text = proof_path.as_posix()
    return f"""#target photoshop
app.displayDialogs = DialogModes.NO;

function esc(text) {{
  return String(text)
    .replace(/\\\\/g, "\\\\\\\\")
    .replace(/"/g, '\\\\"')
    .replace(/\\r/g, "\\\\r")
    .replace(/\\n/g, "\\\\n");
}}

function writeText(path, content) {{
  var file = new File(path);
  file.encoding = "UTF8";
  if (!file.open("w")) {{
    throw new Error("Unable to open proof file: " + path);
  }}
  file.write(content);
  file.close();
}}

var pngPath = "{png_text}";
var proofPath = "{proof_text}";
var doc = app.documents.add(320, 200, 72, "HSD Photoshop Smoke");
doc.activeLayer.name = "smoke_bg";
var black = new SolidColor();
black.rgb.red = 0;
black.rgb.green = 0;
black.rgb.blue = 0;
doc.selection.selectAll();
doc.selection.fill(black);
doc.selection.deselect();
var layer = doc.artLayers.add();
layer.kind = LayerKind.TEXT;
layer.name = "smoke_text";
layer.textItem.contents = "HSD";
layer.textItem.font = "Arial-BoldMT";
layer.textItem.size = 48;
layer.textItem.position = [34, 110];
var white = new SolidColor();
white.rgb.red = 255;
white.rgb.green = 255;
white.rgb.blue = 255;
layer.textItem.color = white;
doc.flatten();
var saveOptions = new PNGSaveOptions();
saveOptions.interlaced = false;
doc.saveAs(new File(pngPath), saveOptions, true, Extension.LOWERCASE);
doc.close(SaveOptions.DONOTSAVECHANGES);
writeText(
  proofPath,
  '{{"ok":true,"version":"{VERSION}","photoshop_version":"' + esc(app.version) + '","png_path":"' + esc(pngPath) + '"}}'
);
"""


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real Photoshop JSX smoke test and capture proof.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--visible", default="false")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    working_dir = output_dir / "working"
    proof_dir = output_dir / "proof"
    working_dir.mkdir(parents=True, exist_ok=True)
    proof_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "photoshop_smoke.png"
    jsx_path = working_dir / "photoshop_smoke.jsx"
    proof_path = proof_dir / "photoshop_smoke_result.json"
    report_path = output_dir / "manifest.json"

    jsx_path.write_text(build_smoke_jsx(png_path, proof_path), encoding="utf-8")

    photoshop = resolve_photoshop_execution(probe_com=True)
    command = build_photoshop_cli_command(
        mode="jsx",
        jsx_path=jsx_path.as_posix(),
        visible=parse_bool(args.visible),
        quit_after=True,
        launch_if_needed=True,
        timeout_sec=args.timeout_sec,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=args.timeout_sec + 15,
    )

    wrapper_payload: dict[str, object] = {}
    if completed.stdout.strip():
        try:
            wrapper_payload = json.loads(completed.stdout.strip())
        except json.JSONDecodeError:
            wrapper_payload = {"raw_stdout": completed.stdout.strip()}

    proof_payload: dict[str, object] = {}
    if proof_path.exists():
        try:
            proof_payload = json.loads(proof_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            proof_payload = {"raw_proof": proof_path.read_text(encoding="utf-8")}

    manifest = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "status": "ok"
        if completed.returncode == 0 and png_path.exists() and proof_payload.get("ok") is True
        else "failed",
        "photoshop_available": bool(photoshop.get("available")),
        "photoshop_executable_path": photoshop.get("executable_path", ""),
        "photoshop_preferred_execution_mode": photoshop.get("preferred_execution_mode", ""),
        "photoshop_com_available": bool(photoshop.get("com_available")),
        "wrapper_command": command,
        "wrapper_returncode": completed.returncode,
        "wrapper_payload": wrapper_payload,
        "stderr": completed.stderr.strip(),
        "png_path": png_path.as_posix(),
        "jsx_path": jsx_path.as_posix(),
        "proof_path": proof_path.as_posix(),
        "png_exists": png_path.exists(),
        "proof_payload": proof_payload,
    }
    report_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest))
    return 0 if manifest["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
