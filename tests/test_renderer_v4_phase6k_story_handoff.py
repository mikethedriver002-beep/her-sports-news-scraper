from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper_module():
    return load_module(ROOT / "scripts" / "hsd_phase6k_story_handoff.py", "phase6k_story_helper")


def fake_base():
    return SimpleNamespace(
        event_date=lambda row: row.get("date", ""),
        event_location=lambda row: row.get("location", ""),
        event_league=lambda row: row.get("league", "WNBA"),
        final_teams=lambda row: (row.get("winner", ""), row.get("loser", "")),
        score_margin=lambda winner, loser: int(winner) - int(loser),
        short_team=lambda value: value,
    )


def test_story_context_omits_unknown_location_instead_of_rendering_tba():
    module = helper_module()
    context = module.build_story_context(
        {"date": "JUNE 20, 2026", "location": "LOCATION TBA", "league": "WNBA"},
        fake_base(),
    )
    assert context["segments"] == ["JUNE 20, 2026", "WNBA"]
    assert "TBA" not in context["story_context_copy"]
    assert context["story_context_status"] == module.CONTEXT_PASS
    assert context["story_context_mode"] == "verified_date_league"


def test_story_prompt_is_matchup_specific_for_every_margin_band():
    module = helper_module()
    row = {"winner": "Phoenix Mercury", "loser": "Seattle Storm"}
    close = module.build_story_prompt(row, "93", "91", fake_base())
    clear = module.build_story_prompt(row, "93", "73", fake_base())
    assert "PHOENIX MERCURY" in close["prompt"]
    assert "SEATTLE STORM" in close["prompt"]
    assert "PHOENIX MERCURY" in clear["prompt"]
    assert "SEATTLE STORM" in clear["prompt"]
    assert close["story_cta_status"] == module.CTA_PASS
    assert clear["story_cta_status"] == module.CTA_PASS
    assert close["prompt"] not in module.GENERIC_PROMPTS


def test_manifest_patch_reads_meta_from_eighth_positional_argument():
    module = helper_module()

    def original_manifest(*args, **kwargs):
        return {
            "template_id": "hsd_game_recap_final_score_c_story",
            "placeholder_layer_count": 0,
            "zone_overflow_count": 0,
            "near_post_ready_candidate": "true",
        }

    base = SimpleNamespace(
        render_final_c=lambda row, aliases, logos: (None, {}),
        make_manifest_item=original_manifest,
        story_prompt_for=lambda row, winner, loser: "OLD",
        MANIFEST_FIELDS=[],
        PLACEHOLDER_TOKENS=set(),
    )
    module.install_patch(base)
    meta = {
        "render_patch_version": module.PATCH_VERSION,
        "story_context_status": module.CONTEXT_PASS,
        "story_context_score": "1.000",
        "story_context_reasons": "",
        "story_context_mode": "verified_date_league",
        "story_context_copy": "JUNE 20, 2026 • WNBA",
        "story_cta_status": module.CTA_PASS,
        "story_cta_score": "1.000",
        "story_cta_reasons": "",
        "story_cta_prompt": "WHAT DROVE PHOENIX'S WIN OVER SEATTLE?",
    }
    item = base.make_manifest_item({}, "id", "stories", "C", "vertical", Path("out.png"), None, meta)
    assert item["render_patch_version"] == module.PATCH_VERSION
    assert item["story_context_copy"] == "JUNE 20, 2026 • WNBA"
    assert item["near_post_ready_candidate"] == "true"


def test_phase6k_policy_keeps_all_publish_safeties_closed():
    policy = json.loads((
        ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_phase6k_v4.json"
    ).read_text(encoding="utf-8"))
    assert policy["version"] == "v1.4-phase6k-final-score-story-handoff-policy"
    assert policy["phase6k_final_score_story_handoff_required"] is True
    assert policy["human_visual_approval_required"] is True
    assert policy["production_cutover_allowed"] is False
    assert policy["auto_publish_allowed"] is False
    assert "LOCATION TBA" in policy["final_score_story_forbidden_tokens"]


def test_phase6k_wrappers_and_dedicated_gate_exist():
    renderer = (ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6k.py").read_text(encoding="utf-8")
    live_gate = (ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py").read_text(encoding="utf-8")
    story_gate = load_module(
        ROOT / "scripts" / "validate_hsd_final_score_story_handoff_v4.py",
        "phase6k_story_gate",
    )
    assert "install_patch" in renderer
    assert "phase6k_story_patch_missing" in live_gate
    assert story_gate.VERSION == "v1.0-phase6k-final-score-story-handoff-gate"
    assert story_gate.STORY_TEMPLATE == "hsd_game_recap_final_score_c_story"
