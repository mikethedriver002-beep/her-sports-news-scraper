from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_remote_visual_triage_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_remote_visual_triage_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_candidate_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "scout_candidate_id",
        "entity_id",
        "source_type",
        "source_url",
        "candidate_image_url",
        "image_alt",
        "credit_byline",
        "fetch_status",
        "manual_review_status",
        "face_likely_visible",
        "body_margin_likely",
        "four_by_five_crop_potential",
        "text_safe_negative_space",
        "source_provenance_clarity",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def candidate_row(
    candidate_id: str,
    *,
    entity_id: str = "nwsl_test_player",
    image_url: str = "https://images.test/action.jpg",
    manual_status: str = "",
    face: str = "likely",
    crop: str = "possible",
    space: str = "possible",
    body: str = "likely",
) -> dict[str, str]:
    return {
        "scout_candidate_id": candidate_id,
        "entity_id": entity_id,
        "source_type": "official_team_gallery",
        "source_url": f"https://fixtures.test/{candidate_id.lower()}",
        "candidate_image_url": image_url,
        "image_alt": "Forward celebrates after scoring with room around the subject",
        "credit_byline": "Fixture Photographer",
        "fetch_status": "candidate_metadata_extracted",
        "manual_review_status": manual_status,
        "face_likely_visible": face,
        "body_margin_likely": body,
        "four_by_five_crop_potential": crop,
        "text_safe_negative_space": space,
        "source_provenance_clarity": "clear",
    }


def test_remote_visual_triage_builds_review_only_board_without_downloads(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "candidate_intake.csv"
    output_dir = tmp_path / "triage"
    write_candidate_csv(
        input_csv,
        [
            candidate_row("APCS114", entity_id="nwsl_portland_thorns_sophia_wilson", image_url="https://images.test/sophia.jpg"),
            candidate_row("APCS026", entity_id="wnba_las_vegas_aces_jackie_young", image_url="https://images.test/jackie.jpg"),
            candidate_row("APCS108", entity_id="wnba_golden_state_valkyries_gabby_williams", image_url="https://images.test/burton.jpg", manual_status="rejected_wrong_person"),
        ],
    )

    manifest = module.build_packet(input_csv=input_csv, output_dir=output_dir, limit=2)

    rows = read_csv(output_dir / "action_photo_remote_visual_triage.csv")
    html = (output_dir / "action_photo_remote_visual_triage.html").read_text(encoding="utf-8")
    report = (output_dir / "action_photo_remote_visual_triage_report.md").read_text(encoding="utf-8")
    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "remote_visual_triage_ready"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["source_fetching"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["approved_marker_writes"] is False
    assert manifest_json["publish_ready"] is False
    assert len(rows) == 2
    assert {row["scout_candidate_id"] for row in rows} == {"APCS114", "APCS026"}
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert "https://images.test/sophia.jpg" in html
    assert "https://images.test/jackie.jpg" in html
    assert "https://images.test/burton.jpg" not in html
    assert "writes no image bytes" in html
    assert "does not save source images" in report
    assert not list(output_dir.glob("*.jpg"))
    assert not list(output_dir.glob("*.png"))


def test_remote_visual_triage_handles_missing_image_candidates(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "candidate_intake.csv"
    output_dir = tmp_path / "triage"
    row = candidate_row("APCS200", image_url="")
    write_candidate_csv(input_csv, [row])

    manifest = module.build_packet(input_csv=input_csv, output_dir=output_dir, limit=10)

    rows = read_csv(output_dir / "action_photo_remote_visual_triage.csv")
    report = (output_dir / "action_photo_remote_visual_triage_report.md").read_text(encoding="utf-8")

    assert manifest["triage_rows"] == 0
    assert rows == []
    assert "Triage rows: `0`" in report
