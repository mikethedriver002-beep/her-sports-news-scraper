from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase6k_renderer_context_omits_unknown_location():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_context")
    row = {
        "date": "JUNE 20, 2026",
        "location": "LOCATION TBA",
        "league": "WNBA",
    }
    meta = module.rendered_context_metadata(row)
    assert meta["context_date"] == "JUNE 20, 2026"
    assert meta["context_location"] == ""
    assert meta["context_location_status"] == "omitted_missing"
    assert "LOCATION TBA" not in meta["context_segments"]
    assert meta["context_placeholder_count"] == 0


def test_phase6k_renderer_preserves_verified_location():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_verified_context")
    row = {
        "date": "JUNE 20, 2026",
        "location": "TARGET CENTER",
        "league": "WNBA",
    }
    meta = module.rendered_context_metadata(row)
    assert meta["context_location"] == "TARGET CENTER"
    assert meta["context_location_status"] == "verified"
    assert meta["context_segment_count"] == 3


def test_final_a_metadata_does_not_claim_location_was_rendered():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_final_a_context")
    meta = module.final_a_context_metadata({
        "date": "JUNE 20, 2026",
        "location": "TARGET CENTER",
        "league": "WNBA",
    })
    assert meta["context_location"] == ""
    assert meta["context_location_status"] == "not_rendered"
    assert meta["context_segments"] == "FINAL • WNBA • JUNE 20, 2026"


def test_context_boxes_support_two_and_three_segments():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_boxes")
    box = (80, 380, 920, 70)
    for count in [2, 3]:
        boxes = module.context_segment_boxes(box, count)
        assert len(boxes) == count
        assert all(width > 0 and height > 0 for _x, _y, width, height in boxes)
        assert boxes[0][0] >= box[0]
        assert boxes[-1][0] + boxes[-1][2] <= box[0] + box[2]


def test_story_prompts_are_matchup_specific_for_every_margin_bucket():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_prompts")
    row = {"winner_team_name": "Minnesota Lynx", "loser_team_name": "Golden State Valkyries"}
    prompts = [
        module.story_prompt_for(row, "80", "78"),
        module.story_prompt_for(row, "82", "76"),
        module.story_prompt_for(row, "96", "70"),
    ]
    for prompt in prompts:
        assert "LYNX" in prompt
        assert prompt not in module.GENERIC_STORY_PROMPTS


def test_story_prompt_possessive_is_grammatical_for_team_ending_in_s():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_possessive")
    row = {"winner_team_name": "Washington Mystics", "loser_team_name": "New York Liberty"}
    prompt = module.story_prompt_for(row, "91", "88")
    assert "MYSTICS'" in prompt
    assert "MYSTICS'S" not in prompt


def test_story_cta_metadata_passes_only_with_team_specific_prompt():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_cta")
    row = {"winner_team_name": "Phoenix Mercury", "loser_team_name": "Seattle Storm"}
    passed = module.story_cta_metadata(row, "WHAT FUELED MERCURY'S SEPARATION?")
    assert passed["story_cta_status"] == "passed_story_context_cta"
    assert passed["story_cta_score"] == "1.000"
    blocked = module.story_cta_metadata(row, "WHERE DID THE GAME TURN?")
    assert blocked["story_cta_status"] == "needs_story_context_cta"


def test_tonight_context_omits_missing_time_and_network_instead_of_tba():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_tonight")
    meta = module.tonight_context_metadata({"preview_label": "MATCHUP PREVIEW"})
    assert meta["context_time_status"] == "omitted_missing"
    assert meta["context_network_status"] == "omitted_missing"
    assert meta["context_segments"] == "MATCHUP PREVIEW"
    assert "TBA" not in meta["context_segments"]


def test_filtered_source_tba_does_not_remain_a_false_placeholder_layer():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_manifest_copy")
    row = {
        "event_id": "event-1",
        "kind": "final",
        "headline": "Phoenix Mercury beat Seattle Storm",
        "winner_team_name": "Phoenix Mercury",
        "loser_team_name": "Seattle Storm",
        "score_display": "90-82",
        "date": "JUNE 20, 2026",
        "location": "LOCATION TBA",
        "league": "WNBA",
    }
    context = module.rendered_context_metadata(row)
    cta = module.story_cta_metadata(row, "WHAT FUELED MERCURY'S SEPARATION?")

    def fake_original(*_args, **_kwargs):
        return {
            "item_id": "event-1::stories::story::vertical",
            "source_id": "event-1",
            "template_id": "hsd_game_recap_final_score_c_story",
            "platform": "stories",
            "module_mode": "vertical_quick_final",
            "headline": row["headline"],
            "placeholder_layer_count": 1,
            "zone_overflow_count": 0,
            "fixture_only_player_asset": "false",
            "notes": "",
        }

    item = module._manifest_item(
        fake_original,
        row,
        "hsd_game_recap_final_score_c_story",
        "stories",
        "C",
        "vertical_quick_final",
        Path("story.png"),
        Image.new("RGBA", (1080, 1920)),
        {
            **context,
            **cta,
            "content_module_title": "GAME EDGE",
            "content_module_body": "Phoenix finished with an eight-point advantage.",
            "content_module_prompt": cta["story_prompt"],
            "player_names": "",
            "route_decision": "rendered_final_c_story_phase6k_context_cta",
        },
    )
    assert item["placeholder_layer_count"] == 0
    assert item["rendered_copy_placeholder_count"] == 0
    assert "LOCATION TBA" not in item["rendered_copy"]


def _downgrade_manifest() -> dict:
    return {
        "items": [
            {"template_id": "hsd_game_recap_final_score_a", "source_id": "game-1", "headline": "Game 1"},
            {"template_id": "hsd_game_recap_final_score_a", "source_id": "game-2", "headline": "Game 2"},
        ],
        "final_score_b_routing": [
            {"source_id": "game-1", "rendered": False, "route_decision": "downgraded_to_final_a_missing_matching_player"},
            {"source_id": "game-2", "rendered": False, "route_decision": "downgraded_to_final_a_missing_verified_player_stats"},
        ],
    }


def test_renderer_validator_requires_complete_recorded_final_b_downgrade():
    module = load_module(ROOT / "scripts" / "validate_hsd_template_renderer_v4_phase6k.py", "renderer_gate_phase6k")
    manifest = _downgrade_manifest()
    assert module.intentional_final_b_downgrade(manifest) is True
    manifest["final_score_b_routing"].pop()
    assert module.intentional_final_b_downgrade(manifest) is False


def test_fidelity_gate_only_excuses_final_b_for_complete_intentional_downgrade():
    module = load_module(ROOT / "scripts" / "validate_hsd_template_fidelity_v4_phase6k.py", "fidelity_gate_phase6k")
    report = {
        "missing_required_templates": [module.FINAL_B],
        "blockers": ["missing_required_phase6b_template_render"],
        "warnings": [],
        "status": "blocked_fidelity_setup",
        "strict_exit_code": 2,
    }
    adjusted = module.adjust_report(report, _downgrade_manifest())
    assert adjusted["status"] == "passed_fidelity_setup"
    assert adjusted["blockers"] == []


def test_live_gate_is_fail_closed_on_every_prerequisite_report(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_phase6k")
    assert {"clean_plate", "live_asset_preparation", "renderer_validation", "fidelity", "near_post_ready", "final_score_content", "story_context_cta"} == set(module.PREREQUISITES)
    for _name, (path, status) in module.PREREQUISITES.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(json.dumps({"status": status, "strict_exit_code": 0, "blockers": []}), encoding="utf-8")
    blockers, _evidence = module.prerequisite_blockers(tmp_path)
    assert blockers == []
    bad_path, _expected = module.PREREQUISITES["fidelity"]
    (tmp_path / bad_path).write_text(json.dumps({"status": "blocked_fidelity_setup", "strict_exit_code": 2}), encoding="utf-8")
    blockers, _evidence = module.prerequisite_blockers(tmp_path)
    assert any(value.startswith("prerequisite_not_passed:fidelity") for value in blockers)


def test_live_gate_ignores_legacy_decisions_without_exact_current_hash(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_phase6k_decisions")
    policy_path = tmp_path / module.POLICY
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps({"live_decisions_path": "config/graphics/v4/live_post_ready/live_visual_approval_decisions_v4.csv"}), encoding="utf-8")
    decision_path = tmp_path / "config/graphics/v4/live_post_ready/live_visual_approval_decisions_v4.csv"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    with decision_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["live_approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"])
        writer.writeheader()
        writer.writerow({
            "live_approval_id": "old-id",
            "decision": "approved",
            "reviewer": "Mick",
            "reviewed_at": "2026-06-21T00:00:00Z",
            "reason": "old hash",
            "render_sha256": "old-hash",
        })
    report = {"rows": [{
        "technical_status": "live_technical_candidate",
        "live_approval_id": "new-id",
        "render_sha256": "new-hash",
    }]}
    summary = module.current_decision_summary(tmp_path, report)
    assert summary["stored_decision_rows"] == 1
    assert summary["current_render_decision_rows"] == 0
    assert summary["unmatched_prior_decision_rows"] == 1
    assert summary["current_render_unreviewed_rows"] == 1

    with decision_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["live_approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"])
        writer.writeheader()
        writer.writerow({
            "live_approval_id": "new-id",
            "decision": "approved",
            "reviewer": "Mick",
            "reviewed_at": "2026-06-21T01:00:00Z",
            "reason": "current hash reviewed",
            "render_sha256": "new-hash",
        })
    summary = module.current_decision_summary(tmp_path, report)
    assert summary["current_render_hash_match_rows"] == 1
    assert summary["current_render_decision_rows"] == 1
    assert summary["current_render_approved_decision_rows"] == 1
    assert summary["current_render_unreviewed_rows"] == 0


def test_live_gate_clears_stale_handoff_outputs_before_evaluation(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_phase6k_stale")
    live_root = tmp_path / module.base.LIVE_ROOT
    live_root.mkdir(parents=True)
    (live_root / "stale.png").write_bytes(b"stale")
    module.clear_stale_live_outputs(tmp_path)
    assert not live_root.exists()


def test_phase6k_policy_preserves_safety_invariants():
    policy = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4_phase6k.json").read_text())
    assert policy["version"] == "v1.4-phase6k-story-context-cta-policy"
    assert policy["rendered_copy_metadata_required"] is True
    assert policy["phase6k_story_context_cta_required"] is True
    assert policy["human_visual_approval_required"] is True
    assert policy["production_cutover_allowed"] is False
    assert policy["auto_publish_allowed"] is False
    assert "LOCATION TBA" in policy["forbidden_live_copy_tokens"]
    assert "TIME TBA" in policy["forbidden_live_copy_tokens"]
    assert policy["prerequisite_reports_required"]["clean_plate_v4_report.json"] == "passed_clean_plate_build"
    assert policy["prerequisite_reports_required"]["live_asset_preparation_v4_report.json"] == "passed_live_asset_preparation"


def test_phase6k_workflow_uploads_raw_renders_for_visual_review():
    text = (ROOT / ".github" / "workflows" / "hsd-v4-phase6k-story-context-cta-polish.yml").read_text()
    assert "template_renderer_v4/renders/**" in text
    assert "validate_hsd_live_post_ready_v4_phase6k.py" in text
    assert "HSD_PUBLISH_OUTPUTS: \"false\"" in text
    assert "tests/test_renderer_v4_phase6j_content_modules.py" in text


def test_blank_current_hash_decision_is_still_unreviewed(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_decisions_phase6k")
    decision_path = tmp_path / "decisions.csv"
    module.base.read_json = lambda _path: {}
    module.base.locate_decisions = lambda _root, _policy: decision_path
    module.base.read_csv = lambda _path: [{
        "live_approval_id": "current-id",
        "render_sha256": "current-sha",
        "decision": "",
    }]
    report = {"rows": [{
        "technical_status": "live_technical_candidate",
        "live_approval_id": "current-id",
        "render_sha256": "current-sha",
    }]}
    summary = module.current_decision_summary(tmp_path, report)
    assert summary["current_render_hash_match_rows"] == 1
    assert summary["current_render_decision_rows"] == 0
    assert summary["current_render_blank_decision_rows"] == 1
    assert summary["current_render_unreviewed_rows"] == 1


def test_phase6k_manifest_exposes_context_placeholder_tokens():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_fields")
    assert "context_placeholder_tokens" in module.EXTRA_MANIFEST_FIELDS
    text = (ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py").read_text()
    assert "base.PLACEHOLDER_TOKENS.update(CONTEXT_FORBIDDEN_TOKENS)" not in text


def test_rendered_copy_audit_includes_combined_placeholder_score():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py", "renderer_phase6k_score_audit")
    row = {
        "headline": "Final result",
        "winner_team_name": "Phoenix Mercury",
        "loser_team_name": "Seattle Storm",
        "score_display": "00-00",
    }
    item = {
        "headline": "Final result",
        "context_segments": "FINAL • WNBA",
        "content_module_title": "GAME EDGE",
        "content_module_body": "Final result",
    }
    rendered = module.rendered_copy_for(row, "hsd_game_recap_final_score_a", item)
    assert "00-00" in rendered
    assert "00-00" in module.LIVE_COPY_FORBIDDEN_TOKENS


def test_partial_current_hash_approvals_are_deferred_until_all_candidates_reviewed(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_phase6k_partial")
    live_root = tmp_path / module.base.LIVE_ROOT
    live_root.mkdir(parents=True)
    (live_root / "premature.png").write_bytes(b"premature")
    report = {
        "status": "live_post_ready_handoff_ready",
        "strict_exit_code": 0,
        "technical_candidate_count": 2,
        "approved_live_count": 1,
        "limited_live_operator_handoff_allowed": True,
        "blockers": [],
        "rows": [
            {"live_post_ready": "true", "live_output_path": "old/approved.png"},
            {"live_post_ready": "false", "live_output_path": ""},
        ],
    }
    summary = {
        "current_render_decision_rows": 1,
        "current_render_approved_decision_rows": 1,
        "current_render_unreviewed_rows": 1,
    }
    changed = module.defer_incomplete_visual_review(tmp_path, report, summary, "live_data")
    assert changed is True
    assert report["status"] == "waiting_for_remaining_live_visual_approval"
    assert report["strict_exit_code"] == 2
    assert report["approved_live_count"] == 0
    assert report["deferred_current_hash_approval_count"] == 1
    assert report["limited_live_operator_handoff_allowed"] is False
    assert all(row["live_post_ready"] == "false" for row in report["rows"])
    assert not live_root.exists()
    approved_csv = tmp_path / module.APPROVED_CSV
    assert approved_csv.exists()
    assert approved_csv.read_text(encoding="utf-8").count("\n") == 1


def test_complete_current_hash_review_does_not_defer_handoff(tmp_path: Path):
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py", "live_gate_phase6k_complete")
    report = {
        "status": "live_post_ready_handoff_ready",
        "strict_exit_code": 0,
        "technical_candidate_count": 2,
        "approved_live_count": 1,
        "limited_live_operator_handoff_allowed": True,
        "blockers": [],
        "rows": [],
    }
    summary = {
        "current_render_decision_rows": 2,
        "current_render_approved_decision_rows": 1,
        "current_render_unreviewed_rows": 0,
    }
    changed = module.defer_incomplete_visual_review(tmp_path, report, summary, "live_data")
    assert changed is False
    assert report["status"] == "live_post_ready_handoff_ready"
    assert report["approved_live_count"] == 1
