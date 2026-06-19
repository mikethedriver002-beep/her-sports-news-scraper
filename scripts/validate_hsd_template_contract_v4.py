from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from PIL import Image

VERSION = "v4.0-wnba-canonical-template-contract"
ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "config" / "graphics" / "v4" / "approved"
SOURCE_PACK_PATH = ROOT / "assets" / "graphics" / "v4" / "approved" / "hsd_wnba_canonical_templates_v4.zip"

EXPECTED_TEMPLATE_IDS = {
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
    "hsd_tonight_in_the_w_a",
    "hsd_last_night_in_the_w_variant_a_multi_game_feed",
    "hsd_last_night_in_the_w_variant_b_story_rolling_recap",
    "hsd_last_night_in_the_w_variant_c_carousel_cover_recap_package",
}
EXPECTED_CANVASES = {
    "ig_feed_threads": (1080, 1350),
    "ig_story_reels": (1080, 1920),
    "ig_carousel": (1080, 1350),
}
REQUIRED_PACK_DOCS = {
    "SOURCE_MANIFEST.json",
    "source_docs/HSD_Last_Night_In_The_W_Final_JSON_Specs.md",
    "source_docs/HSD_Template_Library_Final_JSON_Specs.md",
    "source_docs/WHEN_TO_USE.md",
    "source_docs/WHEN_TO_USE_AND_RELEASE_NOTES.md",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def zip_json(archive: zipfile.ZipFile, name: str) -> Dict[str, Any]:
    try:
        value = json.loads(archive.read(name).decode("utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def image_dimensions(data: bytes) -> Tuple[int, int]:
    with Image.open(io.BytesIO(data)) as image:
        return image.size


def iter_rectangles(value: Any, path: str = "$") -> Iterator[Tuple[str, Dict[str, Any]]]:
    if isinstance(value, dict):
        if all(key in value for key in ("x", "y", "w", "h")):
            yield path, value
        for key, child in value.items():
            yield from iter_rectangles(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_rectangles(child, f"{path}[{index}]")


def add_unique(target: List[str], value: str) -> None:
    if value not in target:
        target.append(value)


def validate_spec_structure(spec: Dict[str, Any], expected_id: str, invalid_zones: List[str], blockers: List[str]) -> None:
    required = ["template_id", "family", "variant", "format", "canvas", "safe_zones", "badge"]
    for key in required:
        if key not in spec:
            add_unique(blockers, f"{expected_id}:missing_required_key:{key}")
    if spec.get("template_id") != expected_id:
        add_unique(blockers, f"{expected_id}:template_id_mismatch")

    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    width = canvas.get("width")
    height = canvas.get("height")
    expected_canvas = EXPECTED_CANVASES.get(str(spec.get("format") or ""))
    if not isinstance(width, int) or not isinstance(height, int):
        add_unique(blockers, f"{expected_id}:invalid_canvas")
        return
    if expected_canvas and (width, height) != expected_canvas:
        add_unique(blockers, f"{expected_id}:unexpected_canvas:{width}x{height}")

    safe = spec.get("safe_zones") if isinstance(spec.get("safe_zones"), dict) else {}
    if any(not isinstance(safe.get(side), int) or safe.get(side, -1) < 0 for side in ("top", "right", "bottom", "left")):
        add_unique(blockers, f"{expected_id}:invalid_safe_zones")
    elif safe["left"] + safe["right"] >= width or safe["top"] + safe["bottom"] >= height:
        add_unique(blockers, f"{expected_id}:safe_zones_consume_canvas")

    badge = spec.get("badge") if isinstance(spec.get("badge"), dict) else {}
    if badge.get("asset") != "official_hsd_badge_reference.png":
        add_unique(blockers, f"{expected_id}:badge_asset_not_canonical")
    if not isinstance(badge.get("rules"), list) or not badge.get("rules"):
        add_unique(blockers, f"{expected_id}:badge_rules_missing")

    for rect_path, rect in iter_rectangles(spec):
        try:
            x, y, rect_width, rect_height = (int(rect[key]) for key in ("x", "y", "w", "h"))
        except Exception:
            add_unique(invalid_zones, f"{expected_id}:{rect_path}:non_integer_rectangle")
            continue
        if x < 0 or y < 0 or rect_width <= 0 or rect_height <= 0 or x + rect_width > width or y + rect_height > height:
            add_unique(invalid_zones, f"{expected_id}:{rect_path}:{x},{y},{rect_width},{rect_height}:canvas={width}x{height}")

    has_zones = isinstance(spec.get("zones"), dict) and bool(spec.get("zones"))
    has_carousel = isinstance(spec.get("cover_slide"), dict) and isinstance(spec.get("package_slides"), dict)
    if not has_zones and not has_carousel:
        add_unique(blockers, f"{expected_id}:no_layout_zones")


def build_report(root: Path = ROOT) -> Dict[str, Any]:
    contract_root = root / "config" / "graphics" / "v4" / "approved"
    registry_path = contract_root / "template_registry_v4.json"
    source_manifest_path = contract_root / "source_manifest_v4.json"
    variant_matrix_path = contract_root / "variant_matrix_v4.json"
    font_contract_path = contract_root / "font_contract_v4.json"
    schema_path = contract_root / "template_spec_schema_v4.json"
    source_pack_path = root / "assets" / "graphics" / "v4" / "approved" / "hsd_wnba_canonical_templates_v4.zip"

    registry = read_json(registry_path)
    source_manifest = read_json(source_manifest_path)
    variant_matrix = read_json(variant_matrix_path)
    font_contract = read_json(font_contract_path)
    schema = read_json(schema_path)

    blockers: List[str] = []
    warnings: List[str] = []
    missing_assets: List[str] = []
    invalid_zones: List[str] = []
    spec_hash_mismatches: List[str] = []
    reference_hash_mismatches: List[str] = []
    reference_dimension_mismatches: List[str] = []
    duplicate_template_ids: List[str] = []
    template_results: List[Dict[str, Any]] = []

    for path, label in [
        (registry_path, "template_registry_v4.json"),
        (source_manifest_path, "source_manifest_v4.json"),
        (variant_matrix_path, "variant_matrix_v4.json"),
        (font_contract_path, "font_contract_v4.json"),
        (schema_path, "template_spec_schema_v4.json"),
    ]:
        if not path.exists():
            add_unique(blockers, f"missing_contract_file:{label}")

    templates = registry.get("templates") if isinstance(registry.get("templates"), list) else []
    template_ids = [str(item.get("template_id") or "") for item in templates if isinstance(item, dict)]
    seen: set[str] = set()
    for template_id in template_ids:
        if template_id in seen:
            add_unique(duplicate_template_ids, template_id)
        seen.add(template_id)
    if set(template_ids) != EXPECTED_TEMPLATE_IDS:
        missing = sorted(EXPECTED_TEMPLATE_IDS - set(template_ids))
        unknown = sorted(set(template_ids) - EXPECTED_TEMPLATE_IDS)
        if missing:
            add_unique(blockers, f"registry_missing_templates:{','.join(missing)}")
        if unknown:
            add_unique(blockers, f"registry_unknown_templates:{','.join(unknown)}")
    if int(registry.get("template_count") or 0) != 7 or len(templates) != 7:
        add_unique(blockers, "registry_template_count_not_7")
    if duplicate_template_ids:
        add_unique(blockers, "duplicate_template_ids")

    route_items = variant_matrix.get("routes") if isinstance(variant_matrix.get("routes"), list) else []
    routed_ids = {str(item.get("template_id") or "") for item in route_items if isinstance(item, dict)}
    if routed_ids != EXPECTED_TEMPLATE_IDS:
        add_unique(blockers, "variant_matrix_does_not_cover_exact_template_set")
    if variant_matrix.get("status") != "canonical_frozen":
        add_unique(blockers, "variant_matrix_not_frozen")
    if not bool((variant_matrix.get("global_rules") or {}).get("registered_templates_only")):
        add_unique(blockers, "variant_matrix_allows_unregistered_templates")
    final_b_routes = [item for item in route_items if isinstance(item, dict) and item.get("template_id") == "hsd_game_recap_final_score_b"]
    if not final_b_routes or final_b_routes[0].get("fallback") != "hsd_game_recap_final_score_a":
        add_unique(blockers, "final_score_b_fallback_not_locked_to_a")
    preview_player_routes = [item for item in route_items if isinstance(item, dict) and item.get("template_id") == "hsd_tonight_in_the_w_a" and item.get("player_asset_state") == "approved"]
    if not preview_player_routes or preview_player_routes[0].get("active_module") != "APPROVED PLAYER PHOTO SLOT":
        add_unique(blockers, "preview_player_route_not_limited_to_approved_module")

    font_status = str(font_contract.get("status") or "missing")
    if font_status != "declared_reference_match_required":
        add_unique(blockers, "font_contract_status_invalid")
    if bool(font_contract.get("silent_fallback_allowed")):
        add_unique(blockers, "silent_font_fallback_allowed")
    if bool(font_contract.get("renderer_cutover_allowed")):
        add_unique(blockers, "renderer_cutover_enabled_before_font_selection")
    if font_contract.get("selected_fonts"):
        add_unique(warnings, "font_selection_present_verify_phase6b_baselines")
    else:
        add_unique(warnings, "font_selection_pending_phase6b_reference_match")

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        add_unique(blockers, "template_schema_not_draft_2020_12")

    expected_pack_hash = str(source_manifest.get("canonical_source_pack_sha256") or registry.get("source_pack", {}).get("sha256") or "")
    source_pack_present = source_pack_path.exists()
    source_pack_sha256 = sha256_path(source_pack_path) if source_pack_present else ""
    source_pack_hash_valid = bool(source_pack_present and expected_pack_hash and source_pack_sha256 == expected_pack_hash)
    if not source_pack_present:
        add_unique(missing_assets, source_pack_path.relative_to(root).as_posix())
        add_unique(blockers, "canonical_source_pack_missing")
    elif not source_pack_hash_valid:
        add_unique(blockers, "canonical_source_pack_hash_mismatch")

    badge_hash_valid = False
    badge_dimensions_valid = False
    pack_manifest: Dict[str, Any] = {}
    pack_names: set[str] = set()
    archive: Optional[zipfile.ZipFile] = None

    if source_pack_hash_valid:
        try:
            archive = zipfile.ZipFile(source_pack_path)
            pack_names = set(archive.namelist())
            unsafe_names = sorted(name for name in pack_names if name.startswith("/") or ".." in Path(name).parts)
            if unsafe_names:
                add_unique(blockers, "canonical_source_pack_has_unsafe_paths")
            for required in REQUIRED_PACK_DOCS:
                if required not in pack_names:
                    add_unique(missing_assets, f"source_pack:{required}")
            pack_manifest = zip_json(archive, "SOURCE_MANIFEST.json")

            badge_info = pack_manifest.get("badge") if isinstance(pack_manifest.get("badge"), dict) else {}
            badge_path = str(badge_info.get("path") or "")
            if badge_path not in pack_names:
                add_unique(missing_assets, f"source_pack:{badge_path or 'badge_path_missing'}")
            else:
                badge_bytes = archive.read(badge_path)
                expected_badge_hash = str(source_manifest.get("badge_sha256") or registry.get("badge", {}).get("sha256") or "")
                expected_badge_dimensions = list(registry.get("badge", {}).get("dimensions") or badge_info.get("dimensions") or [])
                badge_hash_valid = sha256_bytes(badge_bytes) == expected_badge_hash == badge_info.get("sha256")
                badge_dimensions_valid = list(image_dimensions(badge_bytes)) == expected_badge_dimensions == list(badge_info.get("dimensions") or [])
                if not badge_hash_valid:
                    add_unique(blockers, "badge_hash_mismatch")
                if not badge_dimensions_valid:
                    add_unique(blockers, "badge_dimensions_mismatch")
        except Exception as exc:
            add_unique(blockers, f"canonical_source_pack_unreadable:{type(exc).__name__}")
            archive = None

    pack_entries = {
        str(item.get("template_id") or ""): item
        for item in (pack_manifest.get("templates") or [])
        if isinstance(item, dict)
    }

    for entry in templates:
        if not isinstance(entry, dict):
            continue
        template_id = str(entry.get("template_id") or "")
        spec_rel = str(entry.get("spec_path") or "")
        spec_path = root / spec_rel
        result = {
            "template_id": template_id,
            "spec_path": spec_rel,
            "spec_present": spec_path.exists(),
            "spec_semantic_match": False,
            "source_pack_spec_hash_valid": False,
            "public_mockup_hash_valid": False,
            "public_mockup_dimensions_valid": False,
            "layout_reference_hash_valid": False,
            "layout_reference_dimensions_valid": False,
        }
        if not spec_path.exists():
            add_unique(missing_assets, spec_rel)
            add_unique(blockers, f"{template_id}:repo_spec_missing")
            template_results.append(result)
            continue

        spec = read_json(spec_path)
        validate_spec_structure(spec, template_id, invalid_zones, blockers)

        pack_entry = pack_entries.get(template_id, {})
        if not pack_entry:
            add_unique(blockers, f"{template_id}:missing_from_source_pack_manifest")
        elif pack_entry.get("spec_sha256") != entry.get("spec_sha256"):
            add_unique(spec_hash_mismatches, f"{template_id}:registry_vs_pack_manifest")

        if archive is not None:
            spec_pack_path = str(entry.get("source_pack_spec_path") or "")
            if spec_pack_path not in pack_names:
                add_unique(missing_assets, f"source_pack:{spec_pack_path or template_id + ':source_pack_spec_path'}")
            else:
                pack_spec_bytes = archive.read(spec_pack_path)
                pack_spec = json.loads(pack_spec_bytes.decode("utf-8"))
                result["source_pack_spec_hash_valid"] = sha256_bytes(pack_spec_bytes) == entry.get("spec_sha256")
                result["spec_semantic_match"] = canonical_json_bytes(spec) == canonical_json_bytes(pack_spec)
                if not result["source_pack_spec_hash_valid"]:
                    add_unique(spec_hash_mismatches, f"{template_id}:source_pack_spec_hash")
                if not result["spec_semantic_match"]:
                    add_unique(spec_hash_mismatches, f"{template_id}:repo_spec_semantic_mismatch")

            for kind in ("public_mockup", "layout_reference"):
                pack_path = str(entry.get(f"{kind}_pack_path") or "")
                if not pack_path or pack_path not in pack_names:
                    add_unique(missing_assets, f"source_pack:{pack_path or template_id + ':' + kind}")
                    continue
                data = archive.read(pack_path)
                hash_valid = sha256_bytes(data) == entry.get(f"{kind}_sha256")
                dims_valid = list(image_dimensions(data)) == list(entry.get(f"{kind}_dimensions") or []) == [entry["canvas"]["width"], entry["canvas"]["height"]]
                result[f"{kind}_hash_valid"] = hash_valid
                result[f"{kind}_dimensions_valid"] = dims_valid
                if not hash_valid:
                    add_unique(reference_hash_mismatches, f"{template_id}:{kind}")
                if not dims_valid:
                    add_unique(reference_dimension_mismatches, f"{template_id}:{kind}")
        template_results.append(result)

    if archive is not None:
        archive.close()

    if spec_hash_mismatches:
        add_unique(blockers, "spec_hash_mismatches")
    if reference_hash_mismatches:
        add_unique(blockers, "reference_hash_mismatches")
    if reference_dimension_mismatches:
        add_unique(blockers, "reference_dimension_mismatches")
    if invalid_zones:
        add_unique(blockers, "invalid_template_zones")
    if missing_assets:
        add_unique(blockers, "missing_contract_assets")

    add_unique(warnings, "renderer_v4_not_active_by_design")
    status = "passed_template_contract" if not blockers else "blocked_template_contract"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "template_count": len(template_ids),
        "expected_template_count": 7,
        "source_pack_path": source_pack_path.relative_to(root).as_posix(),
        "source_pack_present": source_pack_present,
        "source_pack_sha256": source_pack_sha256,
        "source_pack_hash_valid": source_pack_hash_valid,
        "badge_hash_valid": badge_hash_valid,
        "badge_dimensions_valid": badge_dimensions_valid,
        "font_contract_status": font_status,
        "renderer_cutover_allowed": bool(font_contract.get("renderer_cutover_allowed")),
        "duplicate_template_ids": duplicate_template_ids,
        "missing_assets": sorted(missing_assets),
        "invalid_zones": sorted(invalid_zones),
        "spec_hash_mismatches": sorted(spec_hash_mismatches),
        "reference_hash_mismatches": sorted(reference_hash_mismatches),
        "reference_dimension_mismatches": sorted(reference_dimension_mismatches),
        "blockers": sorted(blockers),
        "warnings": sorted(warnings),
        "templates": template_results,
        "policy": {
            "free_only": True,
            "review_only": True,
            "production_renderer_changed": False,
            "manual_source_pack_upload_required": True,
        },
    }


def write_report(report: Dict[str, Any], root: Path = ROOT) -> None:
    json_path = root / "template_contract_v4_report.json"
    md_path = root / "template_contract_v4_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Template Contract v4",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Version: `{report['version']}`",
        f"Status: `{report['status']}`",
        "",
        "## Core checks",
        "",
        f"- Template count: `{report['template_count']}` / `{report['expected_template_count']}`",
        f"- Source pack present: `{report['source_pack_present']}`",
        f"- Source pack hash valid: `{report['source_pack_hash_valid']}`",
        f"- Badge hash valid: `{report['badge_hash_valid']}`",
        f"- Badge dimensions valid: `{report['badge_dimensions_valid']}`",
        f"- Font contract status: `{report['font_contract_status']}`",
        f"- Renderer cutover allowed: `{report['renderer_cutover_allowed']}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    lines += ["", "## Templates", ""]
    for item in report["templates"]:
        lines.append(
            f"- `{item['template_id']}` | repo/pack semantic match={item['spec_semantic_match']} | "
            f"pack spec hash={item['source_pack_spec_hash_valid']} | "
            f"mockup={item['public_mockup_hash_valid']}/{item['public_mockup_dimensions_valid']} | "
            f"layout={item['layout_reference_hash_valid']}/{item['layout_reference_dimensions_valid']}"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the frozen HSD WNBA template contract v4.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when any contract blocker exists.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root for tests or local validation.")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    report = build_report(root)
    write_report(report, root)
    print(json.dumps({
        "version": report["version"],
        "status": report["status"],
        "template_count": report["template_count"],
        "source_pack_hash_valid": report["source_pack_hash_valid"],
        "badge_hash_valid": report["badge_hash_valid"],
        "font_contract_status": report["font_contract_status"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
    }, indent=2))
    if args.strict and report["blockers"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
