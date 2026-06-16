from __future__ import annotations

import re
from pathlib import Path

PAID_SECRET_NAMES = {"APISPORTS_KEY", "BING_SEARCH_API_KEY", "SERPAPI_KEY"}
PAID_DEPENDENCY_TOKENS = {
    "apisports",
    "serpapi",
    "rapidapi",
    "bing-search",
    "bing_search",
    "scrapingbee",
    "brightdata",
    "browserless",
    "zyte",
    "openai",
}


def read(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def test_requirements_do_not_add_paid_or_llm_dependencies() -> None:
    text = read("requirements.txt").lower()
    hits = sorted(token for token in PAID_DEPENDENCY_TOKENS if token in text)
    assert not hits, f"Paid/LLM dependencies are not allowed by default: {hits}"


def test_workflow_paid_secret_refs_are_optional_only() -> None:
    text = read(".github/workflows/hsd-pipeline-control-v1.yml")
    # The V2 workflow may expose optional secret names, but V3 must not hard-require them.
    hard_required_patterns = []
    for secret in PAID_SECRET_NAMES:
        patterns = [
            rf"if\s*\[\s*-z\s+['\"]?\$\{{?{secret}\}}?",
            rf"exit\s+1.*{secret}",
            rf"{secret}.*required",
        ]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                hard_required_patterns.append((secret, pattern))
    assert not hard_required_patterns, f"Paid-source secrets must stay optional/not allowed by default: {hard_required_patterns}"


def test_v3_repo_state_audit_is_wired_into_lite_review() -> None:
    assert Path("scripts/report_hsd_repo_state_v3.py").exists()
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    assert "scripts/report_hsd_repo_state_v3.py" in lite
    assert "scripts/generate_hsd_graphics_variant_packs_v1.py" in lite
    assert "scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py" in lite
    assert "repo_state_v3.md" in lite
    assert "repo_state_v3.json" in lite
