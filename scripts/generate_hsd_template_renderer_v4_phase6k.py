from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from hsd_phase6k_story_handoff import PATCH_VERSION, install_patch

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "generate_hsd_template_renderer_v4.py"
MANIFEST_JSON = ROOT / "outputs" / "latest" / "HSD_TEMPLATE_FACTORY" / "template_renderer_v4" / "hsd_template_renderer_v4_manifest.json"
REPORT_JSON = ROOT / "outputs" / "latest" / "HSD_TEMPLATE_FACTORY" / "template_renderer_v4" / "hsd_template_renderer_v4_report.json"
REPORT_MD = ROOT / "outputs" / "latest" / "HSD_TEMPLATE_FACTORY" / "template_renderer_v4" / "hsd_template_renderer_v4_report.md"


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("hsd_renderer_v4_phase6k_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load renderer: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def stamp_phase6k(path: Path) -> None:
    payload = read_json(path)
    if not payload:
        return
    payload["effective_renderer_version"] = PATCH_VERSION
    payload["compatibility_renderer_version"] = payload.get("version", "")
    payload["story_handoff_patch_active"] = True
    payload["story_handoff_policy"] = "omit unknown venue/date context; require matchup-specific CTA hierarchy"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def update_markdown() -> None:
    if not REPORT_MD.exists():
        return
    text = REPORT_MD.read_text(encoding="utf-8")
    prefix = "\n".join([
        "# HSD Template Renderer v4.6 Phase 6K",
        "",
        f"Effective renderer: `{PATCH_VERSION}`",
        "Compatibility renderer remains v4.5 so the established clean-plate and fidelity validators continue to run unchanged.",
        "Final Score Story context now omits unknown venue/date placeholders, and the Story CTA is matchup-specific with a stronger YOUR TAKE hierarchy.",
        "",
    ])
    if not text.startswith("# HSD Template Renderer v4.6 Phase 6K"):
        REPORT_MD.write_text(prefix + text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    base = install_patch(load_base())
    result = int(base.main(argv))
    stamp_phase6k(MANIFEST_JSON)
    stamp_phase6k(REPORT_JSON)
    update_markdown()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
