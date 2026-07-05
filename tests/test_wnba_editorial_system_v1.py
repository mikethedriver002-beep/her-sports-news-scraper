from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_editorial_system_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_editorial_system_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_variant_specs_define_four_headshot_led_routes_without_dead_ui_language() -> None:
    module = load_module()
    specs = module.SOURCE_SPECS

    assert [spec["route_id"] for spec in specs] == [
        "route_01_jackie_monograph",
        "route_02_kelsey_left_drive",
        "route_03_sabrina_luxury_cover",
        "route_04_rhyne_press_run",
    ]
    assert any(spec["keep_or_kill"] == "keep" for spec in specs)
    assert any("premium" in spec["visual_strength"].lower() for spec in specs)
    assert all(Path(spec["source_path"]).exists() for spec in specs)
    assert all("boxed" not in spec["deck"].lower() for spec in specs)
    assert all("hud" not in spec["deck"].lower() for spec in specs)
    assert all("rail" not in spec["deck"].lower() for spec in specs)


def test_build_packet_writes_review_only_packet_with_correct_dimensions(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_editorial_system_v1"

    manifest = module.build_packet(output_dir=out_dir, head_commit="abc123")
    manifest_json = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "visual_report.md").read_text(encoding="utf-8")
    rows = read_csv(out_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "wnba_editorial_system_ready"
    assert manifest_json["version"] == "hsd-wnba-editorial-system-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["route_count"] == 4
    assert manifest_json["keep_count"] == 2
    assert manifest_json["kill_count"] == 2
    assert manifest_json["best_route_id"] == "route_01_jackie_monograph"
    assert manifest_json["review_only"] is True
    assert manifest_json["artifact_only"] is True
    assert manifest_json["source_mode"] == "local_wnba_headshots_only"
    assert "APCS039 is dead" in report
    assert "route_03_sabrina_luxury_cover" in report
    assert len(rows) == 4
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)

    expected_files = [
        out_dir / "manifest.json",
        out_dir / "visual_report.md",
        out_dir / "manual_visual_review_intake.csv",
        out_dir / "contact_sheet.png",
        out_dir / "route_01_jackie_monograph.png",
        out_dir / "route_02_kelsey_left_drive.png",
        out_dir / "route_03_sabrina_luxury_cover.png",
        out_dir / "route_04_rhyne_press_run.png",
    ]
    for path in expected_files:
        assert path.exists()

    with Image.open(out_dir / "contact_sheet.png") as contact_sheet:
        assert contact_sheet.size == (1080, 1560)

    for row in manifest_json["routes"]:
        with Image.open(Path(row["render_path"])) as image:
            assert image.size == (1080, 1350)

