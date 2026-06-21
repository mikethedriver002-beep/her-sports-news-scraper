from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper():
    return load_module(ROOT / "scripts" / "hsd_phase6l_editorial_language.py", "phase6l_language")


def test_close_game_language_is_short_and_hsd_style():
    module = helper()
    language = module.hsd_result_language("Dallas Wings", "Chicago Sky", "93", "92")
    assert language["editorial_headline"] == "Dallas Survives"
    assert language["editorial_body"] == "Wings 93, Sky 92."
    assert "survived the finish" not in language["public_copy"].lower()
    assert language["public_copy_quality_status"] == module.PUBLIC_COPY_PASS


def test_blowout_language_does_not_use_margin_or_point_victory():
    module = helper()
    language = module.hsd_result_language("Phoenix Mercury", "Seattle Storm", "93", "73")
    assert language["editorial_headline"] == "Phoenix Rolls"
    assert "20-point victory" not in language["public_copy"].lower()
    assert "margin" not in language["public_copy"].lower()
    assert language["public_copy_quality_status"] == module.PUBLIC_COPY_PASS


def test_public_copy_gate_catches_old_fallback_phrases():
    module = helper()
    bad = module.validate_public_copy_fields({
        "content_module_body": "Phoenix Mercury closed with a 20-point victory.",
        "content_module_prompt": "WHAT FUELED MERCURY'S SEPARATION?",
    })
    assert bad["public_copy_quality_status"] == module.PUBLIC_COPY_NEEDS_FIX
    assert int(bad["public_copy_banned_count"]) >= 2


def test_public_date_formats_iso_dates_for_graphics():
    module = helper()
    assert module.public_date("2026-06-20") == "JUNE 20, 2026"


def test_phase6l_policy_keeps_publish_safeties_closed():
    policy = json.loads((
        ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_phase6l_v4.json"
    ).read_text(encoding="utf-8"))
    assert policy["version"] == "v1.5-phase6l-editorial-language-policy"
    assert policy["phase6l_public_copy_quality_required"] is True
    assert policy["production_cutover_allowed"] is False
    assert policy["auto_publish_allowed"] is False


def test_phase6l_wrappers_exist_and_reference_public_copy_quality():
    renderer = (ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6l.py").read_text(encoding="utf-8")
    live_gate = (ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6l.py").read_text(encoding="utf-8")
    copy_gate = load_module(ROOT / "scripts" / "validate_hsd_public_copy_quality_v4.py", "copy_gate")
    assert "phase6k.configure" in renderer
    assert "public_copy_quality" in live_gate
    assert copy_gate.VERSION == "v1.0-phase6l-public-copy-quality-gate"
