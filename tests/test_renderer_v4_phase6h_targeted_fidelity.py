from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_phase6h_score_parts_parse_espn_final_score_display() -> None:
    renderer = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6h")
    row = {
        "kind": "final",
        "winner": "Washington Mystics",
        "loser": "Connecticut Sun",
        "home_team_display": "Connecticut Sun",
        "away_team_display": "Washington Mystics",
        "home_score": "81",
        "away_score": "88",
        "final_score_display": "Washington Mystics 88 · Connecticut Sun 81",
    }
    assert renderer.score_parts(row) == ("88", "81")


def test_phase6h_derived_headline_prevents_blank_final_headlines() -> None:
    renderer = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6h_headline")
    row = {
        "kind": "final",
        "event_uid": "event_abc",
        "winner": "New York Liberty",
        "loser": "Chicago Sky",
        "final_score_display": "New York Liberty 96 · Chicago Sky 95",
    }
    headline = renderer.headline_for(row, "hsd_game_recap_final_score_a")
    assert headline == "New York Liberty 96, Chicago Sky 95"
    assert renderer.render_slug(row, "final_a") != "item"


def test_phase6h_live_policy_has_separate_technical_floor() -> None:
    policy = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4.json").read_text())
    assert policy["version"] == "v1.1-phase6h-live-post-ready-policy"
    assert policy["release_recommendation_required_for_handoff"] is True
    assert policy["technical_fidelity_floor_by_template"]["hsd_game_recap_final_score_a"] < policy["minimum_fidelity_by_template"]["hsd_game_recap_final_score_a"]
    assert policy["technical_fidelity_floor_by_template"]["hsd_tonight_in_the_w_a"] <= 0.928


def test_phase6h_live_gate_reports_polish_not_hard_block_for_floor_pass() -> None:
    gate = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4.py", "live_gate_phase6h")
    policy = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4.json").read_text())
    item = {
        "template_id": "hsd_game_recap_final_score_a",
        "fidelity_score": "0.8341",
    }
    floor, release, status, reason = gate.fidelity_policy(item, policy)
    assert floor == 0.83
    assert release == 0.89
    assert status == "needs_visual_polish_before_handoff"
    assert "fidelity_below_release_recommendation" in reason
