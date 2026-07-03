from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_recovered_decision_visual_triage_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_recovered_decision_visual_triage_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_formal_intake(path: Path, *, download_approved: str = "no") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_queue_id",
        "candidate_photo_url",
        "evidence_url",
        "evidence_summary",
        "identity_anchor_url",
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
        "notes",
        "operator_verify_required",
        "manual_reviewer",
        "manual_review_status",
        "manual_next_action",
        "download_approved",
        "quarantine_target_hint",
        "review_only",
        "publish_ready",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "candidate_queue_id": "APCS023",
                "candidate_photo_url": "https://cdn.wnba.com/sites/1611661330/2026/06/Rhyne-Howard.png",
                "evidence_url": "https://dream.wnba.com/news/dream-makes-a-statement-with-win-against-indiana",
                "evidence_summary": "Review deck carry-forward only.",
                "identity_anchor_url": "",
                "source_url": "https://dream.wnba.com/news/dream-makes-a-statement-with-win-against-indiana",
                "entity_id": "wnba_atlanta_dream_rhyne_howard",
                "rights_class": "official_team_site",
                "identity_confidence": "medium",
                "intended_review_only_use": "review_only_renderer_social_visual_testing",
                "notes": "Carry-forward from review deck.",
                "operator_verify_required": "yes",
                "manual_reviewer": "",
                "manual_review_status": "carried_forward_pending_formal_download_approval",
                "manual_next_action": "Human must separately approve download.",
                "download_approved": download_approved,
                "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/review_deck/apcs023_operator_review.jpg",
                "review_only": "true",
                "publish_ready": "false",
            }
        )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_recovered_decision_visual_triage_builds_remote_review_board(tmp_path: Path) -> None:
    module = load_module()
    formal = tmp_path / "formal.csv"
    output = tmp_path / "out"
    write_formal_intake(formal)

    manifest = module.build_packet(formal_intake_csv=formal, output_dir=output, limit=10)

    converted = read_csv(output / "recovered_carry_forward_remote_visual_triage_input.csv")
    triage_rows = read_csv(output / "action_photo_remote_visual_triage.csv")
    html = (output / "action_photo_remote_visual_triage.html").read_text(encoding="utf-8")
    manifest_json = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "remote_visual_triage_ready"
    assert manifest_json["version_wrapper"] == "hsd-action-photo-recovered-decision-visual-triage-v1-review-only"
    assert manifest_json["carry_forward_rows"] == 1
    assert manifest_json["triage_rows"] == 1
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["source_fetching"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["download_approved_default"] == "no"
    assert converted[0]["download_approved"] == "no"
    assert converted[0]["fetch_status"] == "candidate_metadata_extracted"
    assert triage_rows[0]["scout_candidate_id"] == "APCS023"
    assert triage_rows[0]["download_approved"] == "no"
    assert triage_rows[0]["review_only"] == "true"
    assert triage_rows[0]["publish_ready"] == "false"
    assert "Rhyne-Howard.png" in html
    assert not list(output.glob("*.jpg"))
    assert not list(output.glob("*.png"))


def test_recovered_decision_visual_triage_blocks_download_approved_rows(tmp_path: Path) -> None:
    module = load_module()
    formal = tmp_path / "formal.csv"
    output = tmp_path / "out"
    write_formal_intake(formal, download_approved="yes")

    try:
        module.build_packet(formal_intake_csv=formal, output_dir=output, limit=10)
    except ValueError as exc:
        assert "download_approved=yes" in str(exc)
    else:
        raise AssertionError("Expected download_approved=yes to be blocked")
