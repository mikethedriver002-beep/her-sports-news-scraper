from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_next_candidate_board_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_next_candidate_board_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def remote_row(candidate_id: str, *, entity: str, priority: str = "P1_visual_review_now") -> dict[str, str]:
    return {
        "triage_id": f"APVT-{candidate_id}",
        "scout_candidate_id": candidate_id,
        "entity_id": entity,
        "source_type": "official_team_gallery",
        "source_url": "https://example.com/source",
        "candidate_image_url": f"https://example.com/{entity}.jpg",
        "image_alt": "Official action image",
        "credit_byline": "",
        "visual_priority": priority,
        "selection_reason": "fixture",
        "face_likely_visible": "likely",
        "body_margin_likely": "likely",
        "four_by_five_crop_potential": "possible",
        "text_safe_negative_space": "possible",
        "source_provenance_clarity": "clear",
        "manual_visual_decision": "",
        "manual_visual_notes": "",
        "download_approved": "no",
        "review_only": "true",
        "publish_ready": "false",
        "asset_downloads": "false",
        "approval_state_change": "none",
        "approved_marker_writes": "false",
    }


def scout_row(candidate_id: str, *, status: str = "", action: str = "") -> dict[str, str]:
    return {
        "scout_candidate_id": candidate_id,
        "seed_id": "seed",
        "entity_id": "entity",
        "source_type": "official_team_gallery",
        "source_page_url": "https://example.com/source",
        "source_url": "https://example.com/source",
        "candidate_photo_url": "https://example.com/source",
        "candidate_image_url": f"https://example.com/{candidate_id}.jpg",
        "image_alt": "Official action image",
        "image_caption": "",
        "image_title": "",
        "credit_byline": "",
        "source_domain": "example.com",
        "discovered_at": "2026-07-03T00:00:00+00:00",
        "apparent_width": "",
        "apparent_height": "",
        "fetch_status": "candidate_metadata_extracted",
        "robots_status": "robots_allowed",
        "page_status_code": "200",
        "notes_evidence": "fixture",
        "face_likely_visible": "likely",
        "body_margin_likely": "likely",
        "four_by_five_crop_potential": "possible",
        "text_safe_negative_space": "possible",
        "jersey_text_conflict_risk": "medium",
        "source_provenance_clarity": "clear",
        "operator_fair_use_asserted": "yes",
        "fair_use_rationale_notes": "records operator posture; not legal approval",
        "transformative_use_notes": "review-only candidate scouting",
        "news_commentary_context_notes": "review-only news/commentary candidate",
        "market_substitution_risk_notes": "no download or publishing",
        "download_approved": "no",
        "rights_class": "official_team_site",
        "identity_confidence": "high",
        "intended_review_only_use": "review_only_action_photo_candidate_scout",
        "quarantine_target_hint": "",
        "manual_review_status": status,
        "manual_next_action": action,
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "none",
        "auto_approval": "false",
        "auto_publish": "false",
        "asset_downloads": "false",
        "approved_marker_writes": "false",
    }


def test_board_excludes_rejected_rows_and_keeps_downloads_off(tmp_path: Path) -> None:
    module = load_module()
    remote_csv = tmp_path / "remote.csv"
    scout_csv = tmp_path / "scout.csv"
    output_dir = tmp_path / "out"
    write_csv(
        remote_csv,
        [
            remote_row("APCS100", entity="good_player"),
            remote_row("APCS101", entity="wrong_person"),
            remote_row("APCS102", entity="p2_player", priority="P2_hold"),
        ],
    )
    write_csv(
        scout_csv,
        [
            scout_row("APCS100"),
            scout_row("APCS101", status="rejected_visual_review", action="wrong person"),
            scout_row("APCS102"),
        ],
    )

    manifest = module.build_packet(
        remote_triage_csv=remote_csv,
        scout_csv=scout_csv,
        output_dir=output_dir,
        head_commit="abc123",
        limit=12,
    )
    rows = read_csv(output_dir / "action_photo_next_candidate_board.csv")
    report = (output_dir / "action_photo_next_candidate_board_report.md").read_text(encoding="utf-8")
    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_next_candidate_board_ready"
    assert manifest_json["version"] == "hsd-action-photo-next-candidate-board-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["board_row_count"] == 1
    assert rows[0]["scout_candidate_id"] == "APCS100"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["formal_intake_ready"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["approval_state_change"] == "none"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["publishing"] == "false"
    assert "does not download images" in report
    assert "download_approved=no" in report


def test_scoring_prioritizes_likely_face_body_and_clear_provenance() -> None:
    module = load_module()
    strong = remote_row("APCS200", entity="team_strong_player")
    weak = remote_row("APCS201", entity="team_weak_marker")
    weak["candidate_image_url"] = "https://example.com/other_player.jpg"
    weak["face_likely_visible"] = "possible"
    weak["body_margin_likely"] = "unclear"
    weak["source_provenance_clarity"] = "unclear"
    strong_score = module.score_row(strong, scout_row("APCS200"))
    weak_score = module.score_row(weak, scout_row("APCS201"))

    assert strong_score > weak_score
    assert module.quality_tier(strong_score, ["none"]).startswith("A")
    assert "face_visibility_not_likely" in module.risk_flags(weak, scout_row("APCS201"))
    assert "filename_identity_mismatch" in module.risk_flags(weak, scout_row("APCS201"))
