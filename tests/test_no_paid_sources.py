from __future__ import annotations

import ast
import csv
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
REQUIRED_WNBA_LOGO_SOURCE_TEAMS = {
    "atlanta_dream",
    "chicago_sky",
    "connecticut_sun",
    "indiana_fever",
    "new_york_liberty",
    "toronto_tempo",
    "washington_mystics",
    "dallas_wings",
    "golden_state_valkyries",
    "las_vegas_aces",
    "los_angeles_sparks",
    "minnesota_lynx",
    "phoenix_mercury",
    "portland_fire",
    "seattle_storm",
}


def read(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def csv_rows(path: str) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def test_python_files_compile() -> None:
    for path in ["generate_hsd_results_desk_v5.py", "generate_hsd_results_desk_v4.py", "generate_hsd_results_contract_v1.py", "scripts/report_hsd_repo_state_v3.py"]:
        ast.parse(read(path), filename=path)


def test_requirements_do_not_add_paid_or_llm_dependencies() -> None:
    text = read("requirements.txt").lower()
    hits = sorted(token for token in PAID_DEPENDENCY_TOKENS if token in text)
    assert not hits, f"Paid/LLM dependencies are not allowed by default: {hits}"


def test_workflow_paid_secret_refs_are_optional_only() -> None:
    text = read(".github/workflows/hsd-pipeline-control-v1.yml")
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


def test_results_desk_v5_is_active_free_only_path() -> None:
    v5 = read("generate_hsd_results_desk_v5.py")
    v4 = read("generate_hsd_results_desk_v4.py")
    assert "VERSION = \"v5.0-free-public-source-accuracy\"" in v5
    assert "from generate_hsd_results_desk_v5 import main" in v4
    assert "api-sports.io" not in v5.lower()
    assert "x-apisports-key" not in v5.lower()
    assert "apisports_key" not in v5.lower()
    assert "rapidapi" not in v5.lower()
    assert '"paid_sources_required": False' in v5
    assert "espn_wnba_public" in v5
    assert "duplicate_game_audit_v5.csv" in v5
    assert "stale_source_audit_v5.csv" in v5
    assert "missing_games_alert_v5" in v5


def test_results_contract_uses_timestamp_freshness_and_excludes_box_score_context_sources() -> None:
    text = read("generate_hsd_results_contract_v1.py")
    assert "reference_dt(row, event_date)" in text
    assert "scheduled_start_utc" in text
    assert "today_box_scores.csv" not in text
    assert "Box-score enrichment files are intentionally not contract sources" in text
    assert "hsd-results-contract-v3.3.0-v5-source-accuracy-freshness" in text


def test_v3_repo_state_audit_is_wired_into_lite_review() -> None:
    assert Path("scripts/report_hsd_repo_state_v3.py").exists()
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    assert "scripts/report_hsd_repo_state_v3.py" in lite
    assert "scripts/generate_hsd_graphics_variant_packs_v1.py" in lite
    assert "scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py" in lite
    assert "repo_state_v3.md" in lite
    assert "repo_state_v3.json" in lite


def test_v3_sanity_workflow_builds_upstream_before_acceptance_commands() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    assert "Build upstream packets for V3 sanity" in workflow
    assert "python generate_hsd_final_score_stories_v1.py" in workflow
    assert "python generate_hsd_manual_workflow_merge_v1.py" in workflow
    assert "python generate_hsd_mermaid_upper_echelon_v2.py" in workflow
    assert "V3 first-run acceptance commands" in workflow
    assert workflow.index("Build upstream packets for V3 sanity") < workflow.index("V3 first-run acceptance commands")


def test_v3_sanity_workflow_runs_wnba_logo_registry_fix_before_packets() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    assert "Build and validate WNBA asset registry" in workflow
    assert "python scripts/fetch_hsd_wnba_logo_sources_v1.py" in workflow
    assert "python scripts/build_hsd_wnba_asset_registry_v1.py" in workflow
    assert workflow.index("Build and validate WNBA asset registry") < workflow.index("Build upstream packets for V3 sanity")


def test_wnba_logo_sources_cover_every_team_with_free_public_sources() -> None:
    rows = csv_rows("data/asset_registry/wnba/logo_sources.csv")
    teams = {row.get("team_id") for row in rows if row.get("team_id")}
    missing = sorted(REQUIRED_WNBA_LOGO_SOURCE_TEAMS - teams)
    assert not missing, f"logo_sources.csv missing teams: {missing}"
    by_team = {row.get("team_id"): row for row in rows}
    for team_id in sorted(REQUIRED_WNBA_LOGO_SOURCE_TEAMS):
        row = by_team[team_id]
        assert row.get("source_url", "").startswith("https://"), team_id
        assert row.get("target_path", "").startswith(f"assets/leagues/wnba/teams/{team_id}/"), team_id
    assert "Atlanta_Dream_logo" in by_team["atlanta_dream"].get("source_url", "")
    assert "Toronto_Tempo_logo" in by_team["toronto_tempo"].get("source_url", "")


def test_logo_fetcher_synthesizes_fallbacks_for_unlisted_teams() -> None:
    text = read("scripts/fetch_hsd_wnba_logo_sources_v1.py")
    assert "def complete_source_rows" in text
    assert "synthesized_official_wnba_favicon_fallback" in text
    assert "TEAMS = ROOT / \"teams.csv\"" in text


def test_production_director_preview_copy_cannot_fall_through_to_lpga_feature_copy() -> None:
    text = read("scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py")
    assert "def preview_copy" in text
    assert "return preview_copy(row)" in text
    assert "Preview copy stays WNBA-specific" in text
    package_block = text[text.index("def package_copy"): text.index("def prompt_text")]
    assert "wnba_game_preview" in package_block
    assert package_block.index("return preview_copy(row)") < package_block.index("return feature_copy(row)")
