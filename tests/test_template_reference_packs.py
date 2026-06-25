from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "config/graphics/v4/template_reference_packs_v1.json"


def count_files(path: Path, suffix: str) -> int:
    return len([item for item in path.glob(f"*{suffix}") if item.is_file()])


def test_templates_hsd_reference_pack_is_discoverable_and_review_only() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pack = next(row for row in manifest["packs"] if row["pack_id"] == "templates_hsd_20260625")

    assert manifest["status"] == "reference_only"
    assert manifest["renderer_cutover_allowed"] is False
    assert manifest["auto_publish_allowed"] is False
    assert pack["guardrails"]["reference_only"] is True
    assert pack["guardrails"]["publish_ready"] is False
    assert pack["guardrails"]["auto_approval"] is False
    assert pack["guardrails"]["auto_render"] is False
    assert pack["guardrails"]["auto_publish"] is False
    assert pack["guardrails"]["paid_apis"] is False
    assert (REPO / pack["brand_reference"]).exists()


def test_templates_hsd_reference_pack_family_assets_exist() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pack = next(row for row in manifest["packs"] if row["pack_id"] == "templates_hsd_20260625")

    public_root = REPO / pack["public_mockup_root"]
    layout_root = REPO / pack["layout_reference_root"]
    spec_root = REPO / pack["reference_spec_root"]
    doc_root = REPO / pack["source_doc_root"]

    for family in pack["families"]:
        key = family["family_key"]
        assert count_files(public_root / key, ".png") == family["public_mockup_count"]
        assert count_files(layout_root / key, ".png") == family["layout_reference_count"]
        assert count_files(spec_root / key, ".json") == family["reference_spec_count"]
        assert count_files(doc_root / key, "") == family["source_doc_count"]
