from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def test_renderer_v4_contract_first_and_review_only() -> None:
    text = read("scripts/generate_hsd_template_renderer_v4.py")
    assert "v4.5-phase6j-final-score-content-modules" in text
    assert "config/graphics/v4/approved" in text
    assert "renderer_cutover_allowed" in text
    assert "content_module_status" in text
    assert "hsd_tonight_in_the_w_a" in text
    assert "hsd_game_recap_final_score_a" in text
    assert "hsd_game_recap_final_score_b" in text
    assert "hsd_game_recap_final_score_c_story" in text


def test_renderer_v4_validator_contract() -> None:
    text = read("scripts/validate_hsd_template_renderer_v4.py")
    assert "v1.4-phase6j-renderer-v4-validator" in text
    assert "missing_template" in text
    assert "renderer_cutover_must_remain_blocked" in text
    assert "final_score_content_module_not_passed" in text
    assert "passed_renderer_v4_validation" in text


def test_phase6b_workflow_wires_renderer_validation_and_artifacts() -> None:
    workflow = read(".github/workflows/hsd-v4-phase6b-renderer-v4.yml")
    assert "Run Renderer v4 fixtures" in workflow
    assert "python scripts/generate_hsd_template_renderer_v4.py --fixtures --strict" in workflow
    assert "python scripts/validate_hsd_template_renderer_v4.py --strict" in workflow
    assert "tests/test_template_renderer_v4_phase6b.py" in workflow
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/**" in workflow


def test_renderer_v4_has_no_paid_dependencies() -> None:
    combined = read("scripts/generate_hsd_template_renderer_v4.py") + read("scripts/validate_hsd_template_renderer_v4.py")
    banned = ["openai", "anthropic", "serpapi", "rapidapi", "brightdata", "scrapingbee", "paid_api"]
    for token in banned:
        assert token not in combined.lower()
