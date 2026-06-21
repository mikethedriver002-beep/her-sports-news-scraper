from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_renderer_version_and_manifest_fields_are_phase6j():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6j")
    assert module.VERSION == "v4.5-phase6j-final-score-content-modules"
    for field in [
        "content_module_status", "content_module_score", "content_module_reasons",
        "content_module_mode", "content_module_title", "content_module_body",
        "content_module_stat_count", "content_module_prompt",
    ]:
        assert field in module.MANIFEST_FIELDS


def test_game_edge_copy_is_factual_and_not_score_only():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6j_edge")
    row = {
        "kind": "final",
        "winner_team_name": "Minnesota Lynx",
        "loser_team_name": "Golden State Valkyries",
        "winner_score": "81",
        "loser_score": "75",
    }
    edge = module.game_edge_module(row, "81", "75")
    assert edge["title"] == "GAME EDGE"
    assert edge["margin"] == "+6"
    assert "6-point" in edge["body"]
    assert "FINAL SCORE CONFIRMED" not in edge["body"].upper()
    assert module.summary_for(row) == edge["body"]


def test_story_prompt_changes_with_margin():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6j_prompt")
    row = {"winner_team_name": "Phoenix Mercury", "loser_team_name": "Seattle Storm"}
    close = module.story_prompt_for(row, "93", "91")
    clear = module.story_prompt_for(row, "93", "73")
    assert close == "WHO MADE THE DIFFERENCE LATE?"
    assert "MERCURY" in clear
    assert close != "WHAT CHANGED THE GAME?"
    assert clear != "WHAT CHANGED THE GAME?"


def test_final_score_b_requires_verified_stats():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6j_stats")
    row = {"stat_points": "24", "stat_rebounds": "8"}
    stats = module.verified_stat_values(row, {"name": "Verified Player"})
    assert stats[:2] == [("24", "PTS"), ("8", "REB")]
    meta = module.final_score_content_meta(
        row, {}, "hsd_game_recap_final_score_b", "verified_player_stats",
        "PLAYER SPOTLIGHT", "Verified Player • 24 PTS", len(stats), player_name="Verified Player",
    )
    assert meta["content_module_status"] == "passed_final_score_content_modules"
    blocked = module.final_score_content_meta(
        {}, {}, "hsd_game_recap_final_score_b", "verified_player_stats",
        "PLAYER SPOTLIGHT", "Decorative player card", 0, player_name="",
    )
    assert blocked["content_module_status"] == "needs_final_score_content_modules"


def test_phase6j_policy_and_live_gate_remain_safe():
    policy = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4.json").read_text())
    assert policy["version"] == "v1.3-phase6j-final-score-content-module-policy"
    assert policy["phase6j_final_score_content_modules_required"] is True
    assert policy["phase6j_final_score_content_modules_release_review"] is True
    assert policy["minimum_final_score_content_module_score"] == 0.95
    assert policy["production_cutover_allowed"] is False
    assert policy["auto_publish_allowed"] is False
    live = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4.py", "live_gate_v4_phase6j")
    assert live.VERSION == "v1.3-phase6j-final-score-content-module-live-gate"
    assert "content_module_status" in live.FIELDS
    assert "content_module_stat_count" in live.FIELDS


def test_dedicated_content_module_validator_exists():
    module = load_module(ROOT / "scripts" / "validate_hsd_final_score_content_modules_v4.py", "content_gate_phase6j")
    assert module.VERSION == "v1.0-phase6j-final-score-content-module-gate"
    assert "hsd_game_recap_final_score_b" in module.FINAL_TEMPLATES


def test_near_post_ready_validator_accepts_phase6j_renderer():
    text = (ROOT / "scripts" / "validate_hsd_near_post_ready_v4.py").read_text()
    assert "v4.5-phase6j-final-score-content-modules" in text
    assert "renderer_not_supported_phase6e_or_later" in text
