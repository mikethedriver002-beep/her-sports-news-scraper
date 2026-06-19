from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

VERSION = "v1.0-phase6b-renderer-v4-validator"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("template_renderer_v4_validation_report.json")
OUT_MD = Path("template_renderer_v4_validation_report.md")
EXPECTED = {
    "hsd_tonight_in_the_w_a": (1080, 1350),
    "hsd_game_recap_final_score_a": (1080, 1350),
    "hsd_game_recap_final_score_b": (1080, 1350),
    "hsd_game_recap_final_score_c_story": (1080, 1920),
}

def read_json(path: Path) -> dict[str, Any]:
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    manifest = read_json(MANIFEST)
    blockers: list[str] = []
    warnings: list[str] = []
    items = manifest.get("items") if isinstance(manifest.get("items"), list) else []
    if not manifest: blockers.append("renderer_v4_manifest_missing")
    if manifest.get("renderer_cutover_allowed") is not False: blockers.append("renderer_cutover_must_remain_blocked")
    if not items: blockers.append("no_renderer_v4_items")
    templates = {item.get("template_id") for item in items}
    for tid in EXPECTED:
        if tid not in templates: blockers.append(f"missing_template:{tid}")
    for item in items:
        tid = str(item.get("template_id"))
        expected = EXPECTED.get(tid)
        path = Path(str(item.get("output_path") or ""))
        if not expected:
            blockers.append(f"unknown_template:{tid}")
            continue
        if (int(item.get("width") or 0), int(item.get("height") or 0)) != expected:
            blockers.append(f"bad_dimensions:{tid}:{item.get('width')}x{item.get('height')}")
        if not path.exists(): blockers.append(f"missing_output:{path}")
        if item.get("review_only") != "true": blockers.append(f"not_review_only:{tid}")
        if int(item.get("team_logo_count") or 0) < 0: blockers.append(f"bad_logo_count:{tid}")
    if any(str(item.get("template_id")) == "hsd_game_recap_final_score_b" and int(item.get("player_assets_used") or 0) == 0 for item in items):
        warnings.append("final_score_b_rendered_without_real_player_asset_placeholder_only")
    report = {"version":VERSION, "status":"passed_renderer_v4_validation" if not blockers else "blocked_renderer_v4_validation", "strict_exit_code": 2 if blockers else 0, "rendered_count":len(items), "templates":sorted(t for t in templates if t), "blockers":blockers, "warnings":warnings, "renderer_version":manifest.get("version")}
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# HSD Renderer v4 Phase 6B Validation", "", f"Status: `{report['status']}`", f"Rendered: `{len(items)}`", "", "## Blockers", ""]
    lines += [f"- `{b}`" for b in blockers] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{w}`" for w in warnings] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 2 if args.strict and blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
