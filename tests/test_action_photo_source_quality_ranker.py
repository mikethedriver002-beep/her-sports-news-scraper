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


def test_source_quality_ranker_dedupes_duplicate_image_urls_after_scoring(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    duplicate_low = candidate_row(
        "APCS020",
        entity_id="nwsl_kansas_city_current_temwa_chawinga",
        image_url="https://cdn.test/images/shared-action.jpg",
        alt="Match recap image.",
        body_margin="unclear",
    )
    duplicate_high = candidate_row(
        "APCS021",
        entity_id="nwsl_kansas_city_current_temwa_chawinga",
        image_url="https://cdn.test/images/shared-action.jpg",
        alt="Temwa Chawinga scores the winner during the match.",
        width="1200",
        height="1600",
    )
    distinct = candidate_row(
        "APCS022",
        entity_id="wta_elena_rybakina",
        image_url="https://cdn.test/images/Rybakina_action.jpg",
        alt="Elena Rybakina celebrates after match point.",
    )
    write_input(input_csv, [duplicate_low, duplicate_high, distinct])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert [row["scout_candidate_id"] for row in rows].count("APCS021") == 1
    assert "APCS020" not in {row["scout_candidate_id"] for row in rows}
    assert len({row["candidate_image_url"] for row in rows}) == len(rows)


def test_source_quality_ranker_dedupes_same_filename_across_cdn_variants(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    source_cdn = candidate_row(
        "APCS025",
        entity_id="au_volleyball_molly_mccage",
        image_url="https://auprosports.com/wp-content/uploads/2025/10/Molly_McCage_AU_Pro_Volleyball.png",
        alt="Molly McCage celebrates during AU Pro Volleyball.",
    )
    imgix_cdn = candidate_row(
        "APCS026",
        entity_id="au_volleyball_molly_mccage",
        image_url="https://au.imgix.net/2025/10/Molly_McCage_AU_Pro_Volleyball.png?w=1920&s=example",
        alt="Molly McCage celebrates during AU Pro Volleyball.",
    )
    distinct = candidate_row(
        "APCS027",
        entity_id="au_volleyball_jordan_thompson",
        image_url="https://au.imgix.net/2025/11/Jordan_Thompson_AU_Pro_Volleyball.png",
        alt="Jordan Thompson attacks during AU Pro Volleyball.",
    )
    write_input(input_csv, [source_cdn, imgix_cdn, distinct])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert {row["scout_candidate_id"] for row in rows} == {"APCS025", "APCS027"}
    assert len(rows) == 2


def test_source_quality_ranker_keeps_distinct_generic_cdn_filenames(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    first_original = candidate_row(
        "APCS031",
        entity_id="unrivaled_mist_arike_ogunbowale",
        image_url="https://cdn.test/images/dlccjspq4yym/original.png",
        alt="Arike Ogunbowale celebrates after a record scoring game.",
    )
    second_original = candidate_row(
        "APCS032",
        entity_id="unrivaled_rose_chelsea_gray",
        image_url="https://cdn.test/images/h690wbqgihym/original.png",
        alt="Chelsea Gray drives during the Rose game.",
    )
    first_size_name = candidate_row(
        "APCS033",
        entity_id="unrivaled_hive_paige_bueckers",
        image_url="https://cdn.test/images/kvmcgu1zmlpg/jpg/16x9/720x405.jpg",
        alt="Paige Bueckers passes during an Unrivaled game.",
    )
    second_size_name = candidate_row(
        "APCS034",
        entity_id="unrivaled_laces_kelsey_plum",
        image_url="https://cdn.test/images/6y7u5jo2qpuu/jpg/16x9/720x405.jpg",
        alt="Kelsey Plum shoots during an Unrivaled game.",
    )
    write_input(input_csv, [first_original, second_original, first_size_name, second_size_name])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    assert {row["scout_candidate_id"] for row in rows} == {"APCS031", "APCS032", "APCS033", "APCS034"}


def test_source_quality_ranker_downranks_url_declared_landscape_and_thumbnail_dimensions(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    strong_vertical = candidate_row(
        "APCS040",
        entity_id="ausl_texas_volts_tiare_jennings",
        image_url="https://cdn.test/images/TiareJennings_action_pitch.jpg",
        alt="Tiare Jennings pitches during the game with clean vertical room.",
        width="1200",
        height="1600",
    )
    tiny_landscape_query = candidate_row(
        "APCS041",
        entity_id="wta_elena_rybakina",
        image_url="https://photoresources.wtatennis.com/photo-resources/2026/03/14/RybakinaSabalenka.png?width=185&height=105",
        alt="Elena Rybakina celebrates after match point.",
    )
    cloudinary_landscape = candidate_row(
        "APCS042",
        entity_id="pwhl_minnesota_frost_kelly_pannek",
        image_url="https://res.cloudinary.com/pwhl-low/image/upload/c_fill,g_faces:auto,h_630,w_1200/q_auto/f_jpg/4.4_Pannek_W",
        alt="Kelly Pannek scores during a playoff game.",
    )
    filename_landscape = candidate_row(
        "APCS043",
        entity_id="ausl_utah_talons_bri_ellis",
        image_url="https://cdn.test/images/Screenshot-2026-06-12-at-11.16.20-AM-1024x686.png",
        alt="Bri Ellis highlight.",
    )
    write_input(input_csv, [tiny_landscape_query, cloudinary_landscape, filename_landscape, strong_vertical])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    by_candidate = {row["scout_candidate_id"]: row for row in rows}

    assert rows[0]["scout_candidate_id"] == "APCS040"
    assert "image_url_thumbnail_or_card_size" in by_candidate["APCS041"]["risk_flags"]
    assert "image_url_landscape_dimensions_weak_4x5" in by_candidate["APCS041"]["risk_flags"]
    assert "image_url_landscape_dimensions_weak_4x5" in by_candidate["APCS042"]["risk_flags"]
    assert "image_url_landscape_dimensions_weak_4x5" in by_candidate["APCS043"]["risk_flags"]
    assert by_candidate["APCS041"]["source_quality_tier"] == "D_fast_reject_or_low_priority"
    assert by_candidate["APCS042"]["source_quality_tier"] == "D_fast_reject_or_low_priority"


def test_source_quality_ranker_does_not_treat_generic_sport_terms_as_filename_identity(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    output_dir = tmp_path / "out"
    wrong_athlete_filename = candidate_row(
        "APCS030",
        entity_id="au_volleyball_jordan_thompson",
        image_url="https://au.imgix.net/2025/10/Reagan_Cooper_AU_Pro_Volleyball.png",
        alt="Jordan Thompson celebrates during the championship run.",
        body_margin="unclear",
    )
    correct_athlete_filename = candidate_row(
        "APCS031",
        entity_id="au_volleyball_jordan_thompson",
        image_url="https://au.imgix.net/2025/11/Jordan_Thompson_AU_Pro_Volleyball.png",
        alt="Jordan Thompson attacks during the championship run.",
        body_margin="unclear",
    )
    write_input(input_csv, [wrong_athlete_filename, correct_athlete_filename])

    module.build_packet(input_csvs=[input_csv], output_dir=output_dir, head_commit="abc123", limit=10)

    rows = read_csv(output_dir / "action_photo_source_quality_ranker.csv")
    by_candidate = {row["scout_candidate_id"]: row for row in rows}
    assert rows[0]["scout_candidate_id"] == "APCS031"
    assert "image_filename_match" in by_candidate["APCS031"]["positive_signals"]
    assert "image_filename_match" not in by_candidate["APCS030"]["positive_signals"]
    assert "image_filename_unverified" in by_candidate["APCS030"]["risk_flags"]


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


def test_source_quality_ranker_suppresses_rejected_source_entity_siblings(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "action_photo_candidate_intake.csv"
    reject_csv = tmp_path / "rejected_or_held_review_deck_decisions.csv"
    output_dir = tmp_path / "out"
    rejected_exact = candidate_row(
        "APCS029",
        entity_id="wnba_atlanta_dream_allisha_gray",
        image_url="https://cdn.test/images/allisha-gray-group-photo.png",
        alt="Allisha Gray group celebration.",
    )
    rejected_sibling = candidate_row(
        "APCS030",
        entity_id="wnba_atlanta_dream_allisha_gray",
        image_url="https://cdn.test/images/allisha-gray-story-photo.png",
        alt="Allisha Gray group photo from the same recap.",
    )
    same_source_different_entity = candidate_row(
        "APCS031",
        entity_id="wnba_atlanta_dream_rhyne_howard",
        image_url="https://cdn.test/images/rhyne-howard-action.png",
        alt="Rhyne Howard drives during the game.",
    )
    same_entity_different_source = candidate_row(
        "APCS032",
        entity_id="wnba_atlanta_dream_allisha_gray",
        image_url="https://cdn.test/images/allisha-gray-other-recap-action.png",
        alt="Allisha Gray drives during another game.",
    )
    same_entity_different_source["source_url"] = "https://fixtures.test/other-story"
    same_entity_different_source["source_page_url"] = "https://fixtures.test/other-story"
    write_input(input_csv, [rejected_exact, rejected_sibling, same_source_different_entity, same_entity_different_source])
    reject_csv.parent.mkdir(parents=True, exist_ok=True)
    with reject_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "entity_id",
                "source_url",
                "operator_decision",
                "review_only",
                "download_approved",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "APCS029",
                "entity_id": "wnba_atlanta_dream_allisha_gray",
                "source_url": "https://fixtures.test/story",
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
    assert manifest["closed_reject_family_keys_applied"] == 1
    assert {row["scout_candidate_id"] for row in rows} == {"APCS031", "APCS032"}


def test_source_quality_ranker_default_inputs_include_latest_source_packets() -> None:
    module = load_module()

    default_inputs = {path.as_posix() for path in module.DEFAULT_INPUT_CSVS}
    default_reject_logs = {path.as_posix() for path in module.DEFAULT_REJECT_LOG_CSVS}

    assert "outputs/local/latest/files/action_photo_wta_lpga_source_expansion_v1/action_photo_candidate_intake.csv" in default_inputs
    assert "outputs/local/latest/files/action_photo_nwsl_source_expansion_v4/action_photo_candidate_intake.csv" in default_inputs
    assert "outputs/local/latest/files/action_photo_volleyball_source_expansion_v1/action_photo_candidate_intake.csv" in default_inputs
    assert "outputs/local/latest/files/action_photo_unrivaled_source_expansion_v1/action_photo_candidate_intake.csv" in default_inputs
    assert (
        "outputs/local/latest/files/action_photo_ranker_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"
        in default_reject_logs
    )
    assert (
        "outputs/local/latest/files/action_photo_ranker_manual_decision_intake_adapter_v2/rejected_or_held_review_deck_decisions.csv"
        in default_reject_logs
    )
    assert (
        "outputs/local/latest/files/action_photo_ausl_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"
        in default_reject_logs
    )
