from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_athlete_photo_onboarding_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_athlete_photo_onboarding_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_headshot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (260, 190), (8, 24, 44, 255))
    for x in range(92, 170):
        for y in range(30, 126):
            image.putpixel((x, y), (214, 154, 121, 255))
    for x in range(75, 188):
        for y in range(118, 184):
            image.putpixel((x, y), (24, 126, 112, 255))
    image.save(path)


def test_athlete_photo_onboarding_builds_review_only_variants_and_contact_sheet(tmp_path: Path) -> None:
    module = load_module()
    module.PROJECT_ROOT = tmp_path
    module.OUT_DIR = tmp_path / "run" / "files" / "athlete_photo_onboarding"
    module.VARIANT_DIR = module.OUT_DIR / "variants"
    module.SHEET_DIR = module.OUT_DIR / "contact_sheets"

    source = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "test_player" / "headshot.png"
    marker = Path(source.as_posix() + ".approved")
    make_headshot(source)
    marker.write_text(json.dumps({"approved_at_utc": "2026-06-25T00:00:00+00:00"}), encoding="utf-8")

    row = {
        "athlete_id": "test_player",
        "athlete_name": "Test Player",
        "team_id": "test_team",
        "local_asset_path": source.as_posix(),
        "approved_marker_path": marker.as_posix(),
        "source_evidence": "approved_assets_registry",
    }

    metadata_rows, sheets = module.build_metadata([row])
    decisions = module.decision_rows(metadata_rows)

    assert len(metadata_rows) == 1
    metadata = metadata_rows[0]
    assert metadata["variant_status"] == "review_variant_ready"
    assert metadata["renderer_review_candidate"] == "true"
    assert metadata["approval_scope"] == "review_only_derivative_from_approved_headshot"
    assert metadata["publish_ready"] == "false"
    assert metadata["auto_approval"] == "false"
    assert metadata["move_files"] == "false"
    assert Path(metadata["feed_variant_path"]).exists()
    assert Path(metadata["story_variant_path"]).exists()
    assert Path(metadata["square_variant_path"]).exists()
    assert sheets["test_team"].endswith("test_team_contact_sheet.jpg")
    assert Path(sheets["test_team"]).exists()
    assert decisions[0]["allowed_decisions"] == "approve_variant_for_review_drafts|hold|revise_crop"
    assert decisions[0]["operator_decision"] == ""
