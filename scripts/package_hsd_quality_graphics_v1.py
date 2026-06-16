from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v1.0-package-hsd-quality-graphics"
SRC = Path("outputs/latest/HSD_QUALITY_GRAPHICS")
OUT_ZIP = Path("hsd_quality_graphics.zip")
OUT_JSON = Path("hsd_quality_graphics_zip_manifest.json")


def main() -> None:
    files = sorted([p for p in SRC.rglob("*.png") if p.is_file()]) if SRC.exists() else []
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(SRC.parent).as_posix())
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": SRC.as_posix(),
        "zip_path": OUT_ZIP.as_posix(),
        "png_count": len(files),
        "files": [p.as_posix() for p in files],
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"hsd_quality_graphics_zip": OUT_ZIP.as_posix(), "png_count": len(files)}, indent=2))


if __name__ == "__main__":
    main()
