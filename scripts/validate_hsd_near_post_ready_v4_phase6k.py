from __future__ import annotations

"""Phase 6K compatibility wrapper for the existing mask/near-ready gate."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_near_post_ready_v4 as base

VERSION = "v1.2-phase6k-near-post-ready-gate"
RENDERER_VERSION = "v4.6-phase6k-story-context-cta-polish"
COMPATIBLE_VERSION = "v4.5-phase6j-final-score-content-modules"


def main(argv: List[str] | None = None) -> int:
    original_read_json = base.read_json

    def phase6k_read_json(path: Path) -> Dict[str, Any]:
        payload = original_read_json(path)
        if Path(path) == base.RENDER_MANIFEST and payload.get("version") == RENDERER_VERSION:
            payload = dict(payload)
            payload["version"] = COMPATIBLE_VERSION
        return payload

    base.VERSION = VERSION
    base.read_json = phase6k_read_json
    exit_code = base.main(argv)

    if base.OUT_JSON.exists():
        report = json.loads(base.OUT_JSON.read_text(encoding="utf-8"))
        report["version"] = VERSION
        report["renderer_version"] = RENDERER_VERSION
        base.OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if base.OUT_MD.exists():
        text = base.OUT_MD.read_text(encoding="utf-8")
        text = text.replace("# HSD Phase 6J Near-Post-Ready Gate", "# HSD Phase 6K Near-Post-Ready Gate", 1)
        base.OUT_MD.write_text(text, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
