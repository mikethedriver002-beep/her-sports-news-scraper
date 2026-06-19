from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

VERSION = "v4.0-wnba-canonical-template-contract"
ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "config/graphics/v4/approved"
REGISTRY = APPROVED / "template_registry_v4.json"
SOURCE = APPROVED / "source_manifest_v4.json"
FONT = APPROVED / "font_contract_v4.json"
ROUTING = APPROVED / "variant_matrix_v4.json"
SCHEMA = APPROVED / "template_spec_schema_v4.json"
REPORT_DIR = ROOT / "outputs/latest/HSD_TEMPLATE_CONTRACT"
DEFAULT_JSON = REPORT_DIR / "template_contract_v4_report.json"
DEFAULT_MD = REPORT_DIR / "template_contract_v4_report.md"
FORMAT_CANVASES = {
    "ig_feed_threads": (1080, 1350),
    "ig_story_reels": (1080, 1920),
    "ig_carousel": (1080, 1350),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def iter_boxes(value: Any, prefix: str = "root") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if "x" in value and "y" in value and any(key in value for key in ("w", "w_max", "width")):
            yield prefix, value
        for key, child in value.items():
            yield from iter_boxes(child, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_boxes(child, f"{prefix}[{index}]")


def validate_spec(spec: dict[str, Any], template_id: str) -> list[str]:
    errors: list[str] = []
    for key in ["template_id", "family", "variant", "format", "canvas", "safe_zones", "badge"]:
        if key not in spec:
            errors.append(f"{template_id}:missing_required_field:{key}")
    if not ("zones" in spec or ("cover_slide" in spec and "package_slides" in spec)):
        errors.append(f"{template_id}:missing_layout_definition")
    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    try:
        width = int(canvas.get("width"))
        height = int(canvas.get("height"))
    except Exception:
        return errors + [f"{template_id}:invalid_canvas"]
    expected = FORMAT_CANVASES.get(str(spec.get("format")))
    if expected and (width, height) != expected:
        errors.append(f"{template_id}:format_canvas_mismatch:{width}x{height}:expected_{expected[0]}x{expected[1]}")
    safe = spec.get("safe_zones") if isinstance(spec.get("safe_zones"), dict) else {}
    try:
        top, right, bottom, left = (int(safe.get(k)) for k in ["top", "right", "bottom", "left"])
        if min(top, right, bottom, left) < 0 or left + right >= width or top + bottom >= height:
            errors.append(f"{template_id}:invalid_safe_zone")
    except Exception:
        errors.append(f"{template_id}:invalid_safe_zone")
    badge = spec.get("badge") if isinstance(spec.get("badge"), dict) else {}
    if badge.get("asset") != "official_hsd_badge_reference.png":
        errors.append(f"{template_id}:invalid_badge_asset")
    if not badge.get("rules"):
        errors.append(f"{template_id}:badge_rules_missing")
    for path, box in iter_boxes(spec):
        try:
            x = int(box.get("x")); y = int(box.get("y"))
            box_w = int(box.get("w", box.get("w_max", box.get("width", 0))))
            box_h_raw = box.get("h", box.get("h_max", box.get("height")))
            box_h = int(box_h_raw) if box_h_raw is not None else 0
        except Exception:
            errors.append(f"{template_id}:invalid_box:{path}")
            continue
        if x < 0 or y < 0 or box_w <= 0:
            errors.append(f"{template_id}:invalid_box:{path}")
            continue
        if x + box_w > width or y > height or (box_h and (box_h <= 0 or y + box_h > height)):
            errors.append(f"{template_id}:box_outside_canvas:{path}")
    return errors


def build_report() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    source = load_json(SOURCE)
    font = load_json(FONT)
    routing = load_json(ROUTING)
    schema = load_json(SCHEMA)
    blockers: list[str] = []
    warnings: list[str] = []
    missing_assets: list[str] = []
    hash_mismatches: list[str] = []
    dimension_mismatches: list[str] = []
    invalid_zones: list[str] = []
    duplicate_ids: list[str] = []
    spec_ids: list[str] = []
    entries = registry.get("templates") if isinstance(registry.get("templates"), list) else []
    if not registry:
        blockers.append("template_registry_missing_or_invalid")
    if not source:
        blockers.append("source_manifest_missing_or_invalid")
    if not font:
        blockers.append("font_contract_missing_or_invalid")
    if not routing:
        blockers.append("variant_matrix_missing_or_invalid")
    if not schema:
        blockers.append("template_schema_missing_or_invalid")

    badge_info = source.get("badge") if isinstance(source.get("badge"), dict) else {}
    badge_path = ROOT / str(badge_info.get("path", ""))
    badge_hash_valid = False
    if not badge_path.exists():
        missing_assets.append(badge_path.as_posix())
    else:
        badge_hash_valid = sha256(badge_path) == str(badge_info.get("sha256", ""))
        if not badge_hash_valid:
            hash_mismatches.append(badge_path.as_posix())
        try:
            expected_badge_dims = tuple(badge_info.get("dimensions") or [])
            if expected_badge_dims and image_dimensions(badge_path) != expected_badge_dims:
                dimension_mismatches.append(badge_path.as_posix())
        except Exception:
            dimension_mismatches.append(badge_path.as_posix())

    for entry in entries:
        if not isinstance(entry, dict):
            blockers.append("invalid_registry_entry")
            continue
        template_id = str(entry.get("template_id", ""))
        if template_id in spec_ids:
            duplicate_ids.append(template_id)
        spec_ids.append(template_id)
        spec_path = ROOT / str(entry.get("spec_path", ""))
        if not spec_path.exists():
            missing_assets.append(spec_path.as_posix())
            continue
        if sha256(spec_path) != str(entry.get("spec_sha256", "")):
            hash_mismatches.append(spec_path.as_posix())
        spec = load_json(spec_path)
        if spec.get("template_id") != template_id:
            blockers.append(f"registry_spec_id_mismatch:{template_id}")
        invalid_zones.extend(validate_spec(spec, template_id))
        for role in ["public_mockup", "layout_reference"]:
            asset_path = ROOT / str(entry.get(f"{role}_path", ""))
            if not asset_path.exists():
                missing_assets.append(asset_path.as_posix())
                continue
            if sha256(asset_path) != str(entry.get(f"{role}_sha256", "")):
                hash_mismatches.append(asset_path.as_posix())
            try:
                expected_dims = tuple(entry.get(f"{role}_dimensions") or [])
                if expected_dims and image_dimensions(asset_path) != expected_dims:
                    dimension_mismatches.append(asset_path.as_posix())
            except Exception:
                dimension_mismatches.append(asset_path.as_posix())

    expected_count = int(registry.get("template_count") or 0)
    if len(entries) != expected_count or expected_count != 7:
        blockers.append(f"template_count_mismatch:{len(entries)}:{expected_count}")
    route_rows = routing.get("routes") if isinstance(routing.get("routes"), list) else []
    routed_ids = {str(row.get("template_id")) for row in route_rows if isinstance(row, dict) and row.get("template_id")}
    missing_routes = sorted(set(spec_ids) - routed_ids)
    unknown_routes = sorted(routed_ids - set(spec_ids))
    if missing_routes:
        blockers.append("templates_missing_routes:" + ",".join(missing_routes))
    if unknown_routes:
        blockers.append("unknown_routed_templates:" + ",".join(unknown_routes))
    if duplicate_ids:
        blockers.append("duplicate_template_ids")
    if missing_assets:
        blockers.append("missing_canonical_assets")
    if hash_mismatches:
        blockers.append("canonical_asset_hash_mismatch")
    if dimension_mismatches:
        blockers.append("canonical_asset_dimension_mismatch")
    if invalid_zones:
        blockers.append("invalid_template_geometry")
    font_status = "missing"
    if font:
        font_status = "selected" if font.get("selected_fonts") else "declared"
        if font.get("silent_fallback_allowed") is not False:
            blockers.append("silent_font_fallback_not_disabled")
        if not font.get("selected_fonts"):
            warnings.append("font_candidates_declared_but_not_selected_phase6b_required")
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "passed_template_contract" if not blockers else "blocked_template_contract",
        "strict_exit_code": 0 if not blockers else 2,
        "template_count": len(entries),
        "template_ids": sorted(spec_ids),
        "badge_hash_valid": badge_hash_valid,
        "font_contract_status": font_status,
        "renderer_cutover_allowed": False,
        "missing_assets": sorted(set(missing_assets)),
        "hash_mismatches": sorted(set(hash_mismatches)),
        "dimension_mismatches": sorted(set(dimension_mismatches)),
        "invalid_zones": sorted(set(invalid_zones)),
        "duplicate_template_ids": sorted(set(duplicate_ids)),
        "missing_routes": missing_routes,
        "unknown_routes": unknown_routes,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "policy": {
            "canonical_specs_are_immutable_inputs": True,
            "public_mockups_are_visual_source_of_truth": True,
            "layout_references_are_geometry_source_of_truth": True,
            "renderer_v3_remains_fallback_only": True,
            "phase6b_visual_baselines_required_before_cutover": True,
            "free_only": True,
        },
    }
    return report


def write_reports(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# HSD Template Contract v4",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Status: `{report['status']}`",
        f"Templates: `{report['template_count']}`",
        f"Badge hash valid: `{report['badge_hash_valid']}`",
        f"Font contract: `{report['font_contract_status']}`",
        f"Renderer cutover allowed: `{report['renderer_cutover_allowed']}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    lines += ["", "## Templates", ""]
    lines += [f"- `{value}`" for value in report["template_ids"]]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the HSD WNBA canonical template contract.")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", default=DEFAULT_JSON.as_posix())
    parser.add_argument("--md", default=DEFAULT_MD.as_posix())
    args = parser.parse_args(argv)
    report = build_report()
    write_reports(report, Path(args.json), Path(args.md))
    print(json.dumps({
        "status": report["status"],
        "template_count": report["template_count"],
        "badge_hash_valid": report["badge_hash_valid"],
        "font_contract_status": report["font_contract_status"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
    }, indent=2))
    return 2 if args.strict and report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
