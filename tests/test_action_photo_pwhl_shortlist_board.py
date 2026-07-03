from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_pwhl_shortlist_board_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_pwhl_shortlist_board_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pwhl_row(candidate_id: str, *, entity: str, alt: str, image: str) -> dict[str, str]:
    return {
        "scout_candidate_id": candidate_id,
        "seed_id": f"seed-{candidate_id}",
        "entity_id": entity,
        "source_type": "official_league_recap",
        "source_page_url": "https://www.thepwhl.com/en/news/fixture",
        "source_url": "https://www.thepwhl.com/en/news/fixture",
        "candidate_photo_url": "https://www.thepwhl.com/en/news/fixture",
        "candidate_image_url": image,
        "image_alt": alt,
        "image_caption": "",
        "image_title": "",
        "credit_byline": "",
        "source_domain": "www.thepwhl.com",
        "discovered_at": "2026-07-03T00:00:00+00:00",
        "apparent_width": "",
        "apparent_height": "",
        "fetch_status": "candidate_metadata_extracted",
        "robots_status": "allowed",
        "page_status_code": "200",
        "notes_evidence": alt,
        "face_likely_visible": "likely",
        "body_margin_likely": "unclear",
        "four_by_five_crop_potential": "possible",
        "text_safe_negative_space": "possible",
        "jersey_text_conflict_risk": "medium",
        "source_provenance_clarity": "clear",
        "operator_fair_use_asserted": "yes",
        "fair_use_rationale_notes": "review-only",
        "transformative_use_notes": "review-only",
        "news_commentary_context_notes": "review-only",
        "market_substitution_risk_notes": "no download",
        "download_approved": "no",
        "rights_class": "official_league_site",
        "identity_confidence": "medium",
        "intended_review_only_use": "review_only_action_photo_candidate_scout",
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/pwhl/example.jpg",
        "manual_review_status": "not_reviewed",
        "manual_next_action": "review",
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "none",
        "auto_approval": "false",
        "auto_publish": "false",
        "asset_downloads": "false",
        "approved_marker_writes": "false",
    }


def write_input(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_pwhl_shortlist_board_ranks_review_only_candidates(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "pwhl.csv"
    output_dir = tmp_path / "out"
    write_input(
        input_csv,
        [
            pwhl_row(
                "APCS001",
                entity="pwhl_minnesota_frost_sidney_morin",
                alt="Sidney Morin scored twice as Minnesota wins a playoff game.",
                image="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/sidney_morin_goal",
            ),
            pwhl_row(
                "APCS002",
                entity="pwhl_ottawa_charge_gwyneth_philips",
                alt="Highlights and press conferences available after the game.",
                image="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/team_photo",
            ),
        ],
    )

    manifest = module.build_packet(input_csv=input_csv, output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_pwhl_shortlist_board.csv")
    report = (output_dir / "action_photo_pwhl_shortlist_board_report.md").read_text(encoding="utf-8")
    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_pwhl_shortlist_board_ready"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["download_approved_default"] == "no"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert rows[0]["scout_candidate_id"] == "APCS001"
    assert rows[0]["quality_tier"].startswith("B")
    assert rows[0]["shortlist_recommendation"] == "manual_visual_review_first"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["approval_state_change"] == "none"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["publishing"] == "false"
    assert "does not download images" in report
    assert "download_approved=no" in report


def test_pwhl_shortlist_scoring_penalizes_unverified_context() -> None:
    module = load_module()
    strong = pwhl_row(
        "APCS010",
        entity="pwhl_toronto_sceptres_daryl_watts",
        alt="Daryl Watts scored the overtime winner in a Toronto victory.",
        image="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/daryl_watts_winner",
    )
    weak = pwhl_row(
        "APCS011",
        entity="pwhl_toronto_sceptres_daryl_watts",
        alt="Post-game coverage available on team YouTube channels.",
        image="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/team_context",
    )

    assert module.score_row(strong) > module.score_row(weak)
    assert "named_context_match" in module.scoring_reasons(strong)
    assert "named_context_unverified" in module.risk_flags(weak)
