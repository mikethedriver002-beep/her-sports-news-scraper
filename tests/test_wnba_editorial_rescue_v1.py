from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_editorial_rescue_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_editorial_rescue_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_variant_specs_uses_four_local_wnba_sources() -> None:
    module = load_module()
    specs = module.build_variant_specs()

    assert [spec["variant_id"] for spec in specs] == [
        "jackie_final_cover",
        "aja_control_line",
        "arike_break_shot",
        "nneka_front_page",
    ]
    assert [spec["source_key"] for spec in specs] == [
        "jackie_young",
        "aja_wilson",
        "arike_ogunbowale",
        "nneka_ogwumike",
    ]
    assert all("headline_lines" in spec for spec in specs)
    assert all(spec["decision"] in {"keep", "kill"} for spec in specs)


def test_build_packet_writes_review_only_premium_rescue_packet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_editorial_rescue_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(
        module,
        "discover_local_creative_tools",
        lambda probe_photoshop_com=False: {
            "photoshop": {
                "available": True,
                "executable_path": "E:/Installed Programs/Creative Cloud/Adobe Photoshop 2025/Photoshop.exe",
                "preferred_execution_mode": "exe",
            }
        },
    )

    manifest = module.build_packet(output_dir=run_dir, head_commit="abc123")
    manifest_json = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "visual_report.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "wnba_editorial_rescue_ready"
    assert manifest_json["version"] == "hsd-wnba-editorial-rescue-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["variant_count"] == 4
    assert manifest_json["best_variant_id"] == "jackie_final_cover"
    assert manifest_json["review_only"] is True
    assert manifest_json["photoshop_used"] is False
    assert manifest_json["photoshop_available"] is True
    assert manifest_json["photoshop_executable_path"] == "E:/Installed Programs/Creative Cloud/Adobe Photoshop 2025/Photoshop.exe"
    assert manifest_json["photoshop_execution_mode"] == "exe"
    assert manifest_json["blender_used"] is False
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False
    assert manifest_json["source_auto_enabled"] is False
    assert manifest_json["paid_apis"] is False
    assert manifest_json["traceback_present"] is False
    assert manifest_json["layered_working_file_path_reference"].endswith("working/wnba_editorial_rescue_v1.psd")
    assert manifest_json["layer_map_path"].endswith("layer_map.md")
    assert manifest_json["contact_sheet_path"].endswith("contact_sheet.png")
    assert manifest_json["report_path"].endswith("visual_report.md")

    for item in manifest_json["variant_rows"]:
        assert item["source_image_present"] is True
        assert item["photoshop_used"] is False
        assert item["blender_used"] is False
        assert item["review_only"] is True
        assert item["dimensions"] == [1080, 1350]
        assert Path(item["render_path"]).exists()
        assert Image.open(item["render_path"]).size == (1080, 1350)

    contact_sheet = Image.open(run_dir / "contact_sheet.png")
    assert contact_sheet.size == (1080, 1350)
    assert "Best premium route" in report
    assert "Kill:" in report
    assert "Photoshop is installed at" in report
    assert "used Pillow for reproducible local comping" in report

    assert len(rows) == 4
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["photoshop_used"] == "false" for row in rows)
    assert all(row["blender_used"] == "false" for row in rows)
