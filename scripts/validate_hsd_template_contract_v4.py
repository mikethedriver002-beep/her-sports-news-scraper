from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from PIL import Image

VERSION = "v4.0-canonical-template-contract-validator"
REGISTRY = Path("config/graphics/v4/approved/template_registry_v4.json")
ROUTING_CONTRACT = Path("config/graphics/v4/approved/routing_v4.json")
FONT_CONTRACT = Path("config/graphics/v4/approved/font_contract_v4.json")
SPEC_SCHEMA = Path("config/graphics/v4/approved/template_spec_schema_v4.json")
OUT_JSON = Path("template_contract_v4_report.json")
OUT_MD = Path("template_contract_v4_report.md")
EXPECTED_TEMPLATE_COUNT = 7


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def semantic_json_sha256(value: Dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def geometry_nodes(value: Any, prefix: str = "") -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(value, dict):
        if all(key in value for key in ("x", "y", "w", "h")):
            yield prefix, value
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            yield from geometry_nodes(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from geometry_nodes(child, f"{prefix}[{index}]")


def build_report(repo_root: Path) -> Dict[str, Any]:
    root = repo_root.resolve()
    registry = load_json(root / REGISTRY)
    matrix = load_json(root / ROUTING_CONTRACT)
    fonts = load_json(root / FONT_CONTRACT)
    schema = load_json(root / SPEC_SCHEMA)
    blockers: List[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        blockers.append("template_spec_schema_missing_or_invalid")
    warnings: List[str] = []
    invalid_zones: List[str] = []
    missing_assets: List[str] = []
    hash_mismatches: List[str] = []
    duplicate_template_ids: List[str] = []
    template_results: List[Dict[str, Any]] = []

    templates = registry.get("templates") if isinstance(registry.get("templates"), list) else []
    ids = [str(item.get("template_id") or "") for item in templates]
    duplicate_template_ids = sorted({item for item in ids if item and ids.count(item) > 1})
    if duplicate_template_ids:
        blockers.append("duplicate_template_ids")
    if len(templates) != EXPECTED_TEMPLATE_COUNT:
        blockers.append("unexpected_template_count")

    pack_info = registry.get("canonical_source_pack") if isinstance(registry.get("canonical_source_pack"), dict) else {}
    pack_path = root / str(pack_info.get("path") or "")
    if not pack_path.exists():
        missing_assets.append(pack_path.as_posix())
        blockers.append("canonical_source_pack_missing")
        pack = None
    else:
        if sha256_file(pack_path) != str(pack_info.get("sha256") or ""):
            hash_mismatches.append(pack_path.as_posix())
            blockers.append("canonical_source_pack_hash_mismatch")
        pack = zipfile.ZipFile(pack_path)

    for item in templates:
        tid = str(item.get("template_id") or "")
        spec_path = root / str(item.get("spec_path") or "")
        row: Dict[str, Any] = {"template_id": tid, "status": "passed"}
        if not spec_path.exists():
            missing_assets.append(spec_path.as_posix())
            row["status"] = "blocked"
            blockers.append(f"missing_spec:{tid}")
            template_results.append(row)
            continue
        spec = load_json(spec_path)
        if semantic_json_sha256(spec) != str(item.get("spec_semantic_sha256") or ""):
            hash_mismatches.append(spec_path.as_posix())
            row["status"] = "blocked"
            blockers.append(f"spec_semantic_hash_mismatch:{tid}")
        for field in ("template_id", "family", "variant", "format"):
            if str(spec.get(field)) != str(item.get(field)):
                blockers.append(f"registry_spec_mismatch:{tid}:{field}")
                row["status"] = "blocked"
        canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
        width = int(canvas.get("width") or 0)
        height = int(canvas.get("height") or 0)
        if width <= 0 or height <= 0:
            blockers.append(f"invalid_canvas:{tid}")
            row["status"] = "blocked"
        for path, zone in geometry_nodes(spec):
            x, y, w, h = (int(zone.get(key) or 0) for key in ("x", "y", "w", "h"))
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                invalid_zones.append(f"{tid}:{path}:{x},{y},{w},{h}")
                row["status"] = "blocked"
        if pack is not None:
            checks = [
                ("source_pack_spec_path", "source_spec_byte_sha256", None),
                ("public_mockup_pack_path", "public_mockup_sha256", item.get("public_mockup_dimensions")),
                ("layout_reference_pack_path", "layout_reference_sha256", item.get("layout_reference_dimensions")),
            ]
            for path_key, hash_key, dimensions in checks:
                member = str(item.get(path_key) or "")
                try:
                    data = pack.read(member)
                except KeyError:
                    missing_assets.append(f"{pack_path.as_posix()}::{member}")
                    row["status"] = "blocked"
                    continue
                if sha256_bytes(data) != str(item.get(hash_key) or ""):
                    hash_mismatches.append(f"{pack_path.as_posix()}::{member}")
                    row["status"] = "blocked"
                if path_key == "source_pack_spec_path":
                    try:
                        source_spec = json.loads(data.decode("utf-8"))
                    except Exception:
                        source_spec = {}
                    if semantic_json_sha256(source_spec) != str(item.get("spec_semantic_sha256") or ""):
                        hash_mismatches.append(f"semantic::{pack_path.as_posix()}::{member}")
                        row["status"] = "blocked"
                if dimensions:
                    with pack.open(member) as handle:
                        with Image.open(handle) as image:
                            if list(image.size) != list(dimensions) or list(image.size) != [width, height]:
                                blockers.append(f"reference_dimensions_mismatch:{tid}:{member}")
                                row["status"] = "blocked"
        template_results.append(row)

    badge_hash_valid = False
    if pack is not None:
        brand = registry.get("brand_contract") if isinstance(registry.get("brand_contract"), dict) else {}
        member = str(brand.get("badge_pack_path") or "")
        try:
            badge_hash_valid = sha256_bytes(pack.read(member)) == str(brand.get("badge_sha256") or "")
        except KeyError:
            missing_assets.append(f"{pack_path.as_posix()}::{member}")
        if not badge_hash_valid:
            blockers.append("badge_hash_invalid")
        pack.close()

    template_ids = set(ids)
    routes = matrix.get("routes") if isinstance(matrix.get("routes"), list) else []
    for route in routes:
        target = str(route.get("template_id") or "")
        if target not in template_ids:
            blockers.append(f"routing_unknown_template:{target}")
    if not routes:
        blockers.append("routing_contract_empty")

    roles = fonts.get("roles") if isinstance(fonts.get("roles"), dict) else {}
    font_contract_status = "declared" if roles and fonts.get("silent_fallback_allowed") is False else "invalid"
    if font_contract_status != "declared":
        blockers.append("font_contract_invalid")
    if fonts.get("selected_fonts") == {}:
        warnings.append("font_reference_matching_pending_phase6b")

    blockers.extend(f"invalid_zone:{item}" for item in invalid_zones)
    blockers.extend(f"missing_asset:{item}" for item in missing_assets)
    blockers.extend(f"hash_mismatch:{item}" for item in hash_mismatches)
    blockers = sorted(set(blockers))
    return {
        "version": VERSION,
        "status": "passed_template_contract" if not blockers else "blocked_template_contract",
        "strict_exit_code": 0 if not blockers else 2,
        "template_count": len(templates),
        "duplicate_template_ids": duplicate_template_ids,
        "invalid_zones": invalid_zones,
        "missing_assets": missing_assets,
        "hash_mismatches": hash_mismatches,
        "badge_hash_valid": badge_hash_valid,
        "font_contract_status": font_contract_status,
        "renderer_cutover_allowed": bool(registry.get("renderer_cutover_allowed")),
        "warnings": sorted(set(warnings)),
        "blockers": blockers,
        "templates": template_results,
    }


def write_report(report: Dict[str, Any], root: Path) -> None:
    (root / OUT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Template Contract v4", "", f"Status: `{report['status']}`",
        f"Template count: `{report['template_count']}`", f"Badge hash valid: `{report['badge_hash_valid']}`",
        f"Font contract: `{report['font_contract_status']}`", f"Renderer cutover allowed: `{report['renderer_cutover_allowed']}`",
        "", "## Blockers", "",
    ]
    lines += [f"- `{item}`" for item in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{item}`" for item in report["warnings"]] or ["- None"]
    (root / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    report = build_report(root)
    write_report(report, root)
    print(json.dumps({key: report[key] for key in ("status", "template_count", "badge_hash_valid", "font_contract_status", "blockers")}, indent=2))
    return 2 if args.strict and report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
