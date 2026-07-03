from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_source_quality_ranker_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_source_quality_ranker_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def candidate_row(
    candidate_id: str,
    *,
    entity_id: str,
    image_url: str,
    alt: str,
    width: str = "",
    height: str = "",
    body_margin: str = "likely",
    crop: str = "possible",
) -> dict[str, str]:
    return {
        "scout_candidate_id": candidate_id,
        "seed_id": f"seed-{candidate_id}",
        "entity_id": entity_id,
        "source_type": "official_league_recap",
        "source_page_url": "https://fixtures.test/story",
        "source_url": "https://fixtures.test/story",
        "candidate_photo_url": "https://fixtures.test/story",
        "candidate_image_url": image_url,
        "image_alt": alt,
        "image_caption": "",
        "image_title": "",
        "credit_byline": "Fixture Staff",
        "source_domain": "fixtures.test",
        "discovered_at": "2026-07-03T00:00:00+00:00",
        "apparent_width": width,
        "apparent_height": height,
        "fetch_status": "candidate_metadata_extracted",
        "robots_status": "allowed",
        "page_status_code": "200",
        "notes_evidence": alt,
        "face_likely_visible": "likely",
        "body_margin_likely": body_margin,
        "four_by_five_crop_potential": crop,
        "text_safe_negative_space": "likely",
        "jersey_text_conflict_risk": "low",
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
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/example.jpg",
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


def test_source_quality_ranker_downranks_cms_hero_and_mobile_assets(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    write_input(
        input_csv,
        [
            candidate_row(
                "APCS001",
                entity_id="ausl_texas_volts_tiare_jennings",
                image_url="https://cdn.test/images/TiareJennings_action_pitch.jpg",
                alt="Tiare Jennings pitches during the game with space above the action.",
                width="1200",
                height="1600",
            ),
            candidate_row(
                "APCS002",
                entity_id="ausl_texas_volts_tiare_jennings",
                image_url="https://cdn.test/images/TiareJennings_MobileHero.png",
                alt="Tiare Jennings hit a home run.",
                body_margin="unclear",
                crop="unclear",
            ),
            candidate_row(
                "APCS003",
                entity_id="ausl_utah_talons_bri_ellis",
                image_url="https://cdn.test/images/Screenshot-2026-06-12-at-11.16.20-AM-1024x686.png",
                alt="Bri Ellis opening series highlight.",
                width="1024",
                height="686",
            ),
        ],
    )

    manifest = module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    report = (output_dir / "action_photo_source_quality_ranker_report.md").read_text(encoding="utf-8")
    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_source_quality_ranker_ready"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["download_approved_default"] == "no"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert rows[0]["scout_candidate_id"] == "APCS001"
    assert rows[0]["source_quality_tier"].startswith("A") or rows[0]["source_quality_tier"].startswith("B")
    assert "image_filename_match" in rows[0]["positive_signals"]
    assert rows[1]["scout_candidate_id"] in {"APCS002", "APCS003"}
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert any("mobile_hero_variant" in row["risk_flags"] for row in rows)
    assert any("landscape_dimensions_weak_4x5" in row["risk_flags"] for row in rows)
    assert "does not download images" in report
    assert "download_approved=no" in report


def test_source_quality_ranker_ignores_non_review_ready_rows(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    rejected = candidate_row(
        "APCS010",
        entity_id="ausl_texas_volts_tiare_jennings",
        image_url="https://cdn.test/images/TiareJennings_action_pitch.jpg",
        alt="Tiare Jennings pitches during the game.",
    )
    rejected["fetch_status"] = "robots_denied"
    approved = candidate_row(
        "APCS011",
        entity_id="ausl_texas_volts_tiare_jennings",
        image_url="https://cdn.test/images/TiareJennings_action_pitch_2.jpg",
        alt="Tiare Jennings pitches during the game.",
    )
    approved["download_approved"] = "yes"
    ready = candidate_row(
        "APCS012",
        entity_id="ausl_texas_volts_tiare_jennings",
        image_url="https://cdn.test/images/TiareJennings_action_pitch_3.jpg",
        alt="Tiare Jennings pitches during the game.",
    )
    write_input(input_csv, [rejected, approved, ready])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert [row["scout_candidate_id"] for row in rows] == ["APCS012"]


def test_source_quality_ranker_suppresses_closed_rejects_by_candidate_and_entity(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    reject_csv = tmp_path / "recovered_decision_reject_log.csv"
    output_dir = tmp_path / "out"
    closed = candidate_row(
        "APCS023",
        entity_id="wnba_atlanta_dream_rhyne_howard",
        image_url="https://cdn.test/images/Rhyne-Howard.png",
        alt="Rhyne Howard promotional graphic.",
    )
    same_candidate_different_entity = candidate_row(
        "APCS023",
        entity_id="pwhl_minnesota_frost_kelly_pannek",
        image_url="https://cdn.test/images/KellyPannek_action.jpg",
        alt="Kelly Pannek scores during a playoff game.",
    )
    write_input(input_csv, [closed, same_candidate_different_entity])
    reject_csv.parent.mkdir(parents=True, exist_ok=True)
    with reject_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "entity_id",
                "decision",
                "manual_next_action",
                "review_only",
                "download_approved",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "APCS023",
                "entity_id": "wnba_atlanta_dream_rhyne_howard",
                "decision": "reject_bad_crop",
                "manual_next_action": "closed_rejected_do_not_download_or_formal_intake",
                "review_only": "true",
                "download_approved": "no",
            }
        )

    manifest = module.build_packet(
        input_csvs=[input_csv],
        reject_log_csvs=[reject_csv],
        output_dir=output_dir,
        head_commit="abc123",
        limit=10,
    )

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert manifest["closed_reject_keys_applied"] == 1
    assert [row["entity_id"] for row in rows] == ["pwhl_minnesota_frost_kelly_pannek"]
    assert rows[0]["scout_candidate_id"] == "APCS023"


def test_source_quality_ranker_suppresses_adapter_operator_decision_rejects(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    reject_csv = tmp_path / "rejected_or_held_review_deck_decisions.csv"
    output_dir = tmp_path / "out"
    closed = candidate_row(
        "APCS008",
        entity_id="pwhl_minnesota_frost_kelly_pannek",
        image_url="https://cdn.test/images/KellyPannek_action.jpg",
        alt="Kelly Pannek scores during a playoff game.",
    )
    open_row = candidate_row(
        "APCS009",
        entity_id="nwsl_kansas_city_current_temwa_chawinga",
        image_url="https://cdn.test/images/TemwaChawinga_action.jpg",
        alt="Temwa Chawinga scores during a match.",
    )
    write_input(input_csv, [closed, open_row])
    reject_csv.parent.mkdir(parents=True, exist_ok=True)
    with reject_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "entity_id",
                "operator_decision",
                "review_only",
                "download_approved",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "APCS008",
                "entity_id": "pwhl_minnesota_frost_kelly_pannek",
                "operator_decision": "reject_group_photo",
                "review_only": "true",
                "download_approved": "no",
            }
        )

    manifest = module.build_packet(
        input_csvs=[input_csv],
        reject_log_csvs=[reject_csv],
        output_dir=output_dir,
        head_commit="abc123",
        limit=10,
    )

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert manifest["closed_reject_keys_applied"] == 1
    assert [row["scout_candidate_id"] for row in rows] == ["APCS009"]


def test_source_quality_ranker_default_inputs_include_latest_source_packets() -> None:
    module = load_module()

    default_inputs = {path.as_posix() for path in module.DEFAULT_INPUT_CSVS}
    default_reject_logs = {path.as_posix() for path in module.DEFAULT_REJECT_LOG_CSVS}

    assert "outputs/local/latest/files/action_photo_wta_lpga_source_expansion_v1/action_photo_candidate_intake.csv" in default_inputs
    assert "outputs/local/latest/files/action_photo_nwsl_source_expansion_v4/action_photo_candidate_intake.csv" in default_inputs
    assert (
        "outputs/local/latest/files/action_photo_ranker_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"
        in default_reject_logs
    )
    assert (
        "outputs/local/latest/files/action_photo_ausl_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"
        in default_reject_logs
    )
