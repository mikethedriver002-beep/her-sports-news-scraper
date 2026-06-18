from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

VERSION = "v1.1-phase2g-authoritative-closure-no-workflow-push"
INSTALL_REPORT_JSON = "phase2g_install_report.json"
INSTALL_REPORT_MD = "phase2g_install_report.md"
CLOSURE_JSON = "phase2_closure_v1.json"
CLOSURE_MD = "phase2_closure_v1.md"
DELETED_PATHS_TXT = "phase2g_deleted_paths.txt"

SOURCE_TRUTH_JSON = "v4_source_truth_guard.json"
LOGO_STATUS_JSON = (
    "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/"
    "hsd_template_renderer_v2_logo_status.json"
)
SANITY_WORKFLOW = Path(".github/workflows/hsd-v3-repo-state-sanity.yml")
LEGACY_WORKFLOWS = (
    Path(".github/workflows/results-desk.yml"),
    Path(".github/workflows/news-scraper.yml"),
    Path(".github/workflows/results-source-audit.yml"),
)
REQUIREMENT_FILES = (
    Path("requirements.txt"),
    Path("requirements-news-sync.txt"),
    Path("requirements-asset-visual-qa.txt"),
)
BLOCKED_DEPENDENCY_TOKENS = (
    "apisports", "serpapi", "rapidapi", "scrapingbee", "brightdata",
    "zyte", "browserless", "openai", "anthropic", "perplexity",
)
ALLOWED_PHASE3_SOURCE_BLOCKERS = {
    "expected_games_baseline_is_observation_derived",
    "independent_schedule_verification_inconclusive",
}

PROTECTED_PREFIXES = (
    ".github/", "assets/", "brand_assets/", "brand_system/", "config/",
    "contracts/", "data/", "docs/", "scripts/", "studio_templates_v2/",
    "tests/", "VISIBLE_COPY_OF_GITHUB_WORKFLOW/",
)
PROTECTED_EXACT = {
    ".gitignore", "CHANGELOG.md", "BEBE_OPS_V2_3_STABILITY_FIX.md",
    "FILES_TO_VERIFY_AFTER_COPY.md", "GITHUB_WEB_INSTALL_BACKUP.md",
    "NEWS_SYNC_V1_8_1_PUBLISH_FIX.md", "PATCH_MANIFEST.json",
    "PATCH_MANIFEST.md", "requirements.txt", "requirements-news-sync.txt",
    "requirements-asset-visual-qa.txt", "studio_bridge_v1_3_notes.md",
}
PROTECTED_ROOT_INPUTS = {
    "manual_story_inbox.csv", "manual_story_inbox.json",
    "manual_results_seed.csv", "source_registry.csv", "source_registry.json",
    "story_candidates_manual.csv", "story_candidates_manual.jsonl",
}
DEFERRED_PHASE3_EXACT = {"config/hsd_expected_games_v5.csv"}

GENERATED_TOP_LEVEL_DIRS = {
    "__pycache__", "asset_desk_dashboard", "asset_run_history",
    "assignment_handoff_packets", "assignment_handoff_zips",
    "chatgpt_review_pack", "dashboard", "generated_graphics",
    "graphics_chat_upload_pack", "graphics_chat_upload_pack_zips",
    "graphics_clean_prompts", "graphics_qa_dashboard",
    "hsd_pipeline_lite_review", "ig_story_results_upload_pack",
    "ig_story_results_upload_pack_zips", "launch_analytics_dashboard",
    "launch_dashboard", "launch_run_history", "manual_workflow_handoff_packs",
    "manual_workflow_packets", "mermaid_assignment_compiled_packets",
    "mermaid_assignment_final_packets", "mermaid_compiled_packets",
    "mermaid_director_compiled_packets", "mermaid_quality_compiled_packets",
    "mermaid_quality_compiled_packets_v2_2", "news_dashboard",
    "news_run_history", "outputs", "rendered_handoff_graphics",
    "rendered_handoff_zips", "results_dashboard", "results_run_history",
    "run_history", "runs", "studio_dashboard", "studio_run_history",
    "visual_upgrade_dashboard",
}
GENERATED_PREFIXES = ("operator/inbox/",)

ROOT_GENERATED_EXACT = {
    "approved_graphics_assets.csv", "approved_graphics_assets.json",
    "asset_candidates_review.md", "asset_desk_manifest.json",
    "asset_manifest.csv", "asset_manifest.json", "asset_rights_review.csv",
    "asset_source_seed_list.csv", "caption_bank.md", "caption_bank_v2.csv",
    "daily_command_file.csv", "daily_content_brief.csv",
    "daily_content_command_center.csv", "daily_results_recommendations.md",
    "dirty_tree_v1.json", "dirty_tree_v1.md", "discovery_sources_report.md",
    "duplicate_game_audit_v5.csv", "expected_games_v5_manifest.json",
    "expected_games_v5_report.md", "fact_warning_queue.csv",
    "first_comment_hooks.md", "generated_output_pollution_v1.json",
    "generated_output_pollution_v1.md", "graphic_copy_rules.csv",
    "graphics_copy_package.md", "graphics_language_manifest.json",
    "graphics_production_specs.json", "graphics_prompt_sanitizer_rules.md",
    "graphics_slide_blueprints.md", "hsd_current_run.json",
    "hsd_daily_content_hub.md", "hsd_graphics_system_hub.md",
    "hsd_pipeline_lite_review.zip", "hsd_publish_system_hub.md",
    "hsd_quality_graphics.zip", "hsd_quality_graphics_manifest.csv",
    "hsd_quality_graphics_report.md", "hsd_quality_graphics_zip_manifest.json",
    "image_generation_prompts.csv", "independent_schedule_verification_v5.csv",
    "independent_schedule_verification_v5.json",
    "independent_schedule_verification_v5.md",
    "launch_integration_points.csv", "latest_news_sync_run_summary.md",
    "latest_results_run_summary.md", "latest_run_summary.md",
    "master_posting_dashboard.csv", "missing_games_alert_v5.csv",
    "missing_games_alert_v5.json", "missing_games_alert_v5.md",
    "multi_post_daily_board.json", "multi_post_daily_board.md",
    "multisport_results_modules_v5.json", "multisport_results_modules_v5.md",
    "multisport_results_observations_v5.csv", "must_post_carousels.csv",
    "news_fact_packets.csv", "operator_status.md", "phase2_closure_v1.json",
    "phase2_closure_v1.md", "phase2g_install_report.json",
    "phase2g_install_report.md", "pipeline_stop_reason.md",
    "player_assets.csv", "player_assets.json", "player_image_candidates.csv",
    "player_image_fit_gate.csv", "player_image_fit_report.md",
    "player_image_requirements.csv", "player_image_sourcing_report.md",
    "post_slot_status.csv", "post_template_mapper.csv",
    "publish_guard_report.md", "ready_to_post_graphic_copy.csv",
    "reconciled_events.csv", "reel_script_package.md",
    "render_integrity_report.md", "rendered_slide_qa.csv",
    "rendered_slide_qa_manifest.json", "rendered_slide_qa_report.md",
    "repo_state_v3.json", "repo_state_v3.md", "results_contract_report.md",
    "results_contract_v2.csv", "results_contract_v2.jsonl",
    "results_dashboard_seed.csv", "results_desk_v5_manifest.json",
    "results_desk_v5_report.md", "results_graphics_queue.md",
    "results_system_hub.md", "run_manifest.json", "source_accuracy_v5.json",
    "source_accuracy_v5.md", "source_health_report.csv",
    "source_observations.csv", "stale_source_audit_v5.csv",
    "story_context_enriched.csv", "story_poll_package.csv",
    "studio_accuracy_checklist.csv", "studio_bundle_caption_bank.md",
    "studio_bundle_packets.md", "studio_bundle_prompts.md",
    "studio_bundle_prompts_v2.md", "studio_bundle_queue.csv",
    "studio_caption_bank.md", "studio_command_center.md",
    "studio_fresh_packet_gate.csv", "studio_fresh_packet_report.md",
    "studio_freshness_gate.csv", "studio_freshness_report.md",
    "studio_graphics_queue.csv", "studio_image_prompts.md",
    "studio_manual_review_graphics.csv", "studio_post_schedule.md",
    "studio_preview_fallback_report.md", "studio_stale_packet_queue.csv",
    "studio_top_graphic_packets.md", "studio_visual_upgrade_v2.md",
    "team_assets.csv", "team_assets.json", "threads_queue.csv",
    "threads_queue_v2.csv", "today_box_scores.csv",
    "today_final_results.csv", "today_graphics_queue.csv",
    "today_graphics_queue.md", "today_results_board.csv",
    "today_womens_results.csv", "tonight_in_the_w_graphic_templates.csv",
    "tonight_in_the_w_package.csv", "tonight_in_the_w_visual_specs.csv",
    "top_3_graphic_packets.md", "top_performers.csv",
    "top_womens_results.csv", "v4_source_truth_guard.json",
    "v4_source_truth_guard.md", "wnba_box_score_audit.csv",
    "wnba_box_score_summary.md", "womens_sports_articles.csv",
}

ROOT_GENERATED_PATTERNS = (
    "assignment_*.csv", "assignment_*.json", "assignment_*.md",
    "bebe_*.csv", "bebe_*.json", "bebe_*.md",
    "breaking_news_queue*.csv", "content_director_*.csv",
    "content_director_*.json", "content_director_*.md",
    "contract_validation_*.json", "contract_validation_*.md",
    "daily_slate_*.csv", "daily_slate_*.md",
    "final_score_story_guard_report.*", "graphics_*.csv",
    "graphics_*.json", "graphics_*.md", "ig_feed_*.csv",
    "ig_story_*.csv", "ig_story_*.json", "ig_story_*.md",
    "install_report.*", "manual_workflow_*.csv",
    "manual_workflow_*.json", "manual_workflow_*.jsonl",
    "manual_workflow_*.md", "mermaid_*.csv", "mermaid_*.json",
    "mermaid_*.jsonl", "mermaid_*.md", "multisport_*.csv",
    "multisport_*.json", "multisport_*.md",
    "official_player_headshot_*.csv", "official_player_headshot_*.md",
    "operator_*.csv", "operator_*.json", "operator_*.md",
    "player_asset_*.csv", "player_image_*.csv", "player_image_*.md",
    "player_registry_*.json", "player_registry_*.md", "player_assets.*",
    "rendered_handoff_*.csv", "rendered_handoff_*.jpg",
    "rendered_handoff_*.json", "rendered_handoff_*.md",
    "rendered_slide_qa.*", "rumor_watch_queue*.csv",
    "social_rumor_*.csv", "social_rumor_*.json", "social_rumor_*.md",
    "source_registry_audit.*", "story_candidates_*.csv",
    "story_candidates_*.jsonl", "studio_*.csv", "studio_*.json",
    "studio_*.md", "threads_*.csv",
)

WRITE_PATTERNS = (
    re.compile(r"""write_(?:csv|json|jsonl|text)\(\s*["']([^"']+)["']"""),
    re.compile(r"""Path\(\s*["']([^"']+)["']\s*\)\.(?:write_text|write_bytes|mkdir)"""),
    re.compile(r"""open\(\s*["']([^"']+)["']\s*,\s*["'][wax]"""),
    re.compile(r"""ZipFile\(\s*["']([^"']+)["']\s*,\s*["']w"""),
)
GENERATED_MARKERS = (
    re.compile(r'(?m)^\s*Generated:\s*20\d{2}-\d{2}-\d{2}'),
    re.compile(r'"generated_at_utc"\s*:'),
    re.compile(r'(?m)^\s*Run timestamp UTC:\s*`?20\d{2}-\d{2}-\d{2}'),
    re.compile(r'(?m)^\s*Archive folder:\s*`?'),
)
TEXT_EXTENSIONS = {".json", ".md", ".txt", ".html", ".csv"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def run(cmd: Sequence[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd), check=check, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def git_ls_files() -> List[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return [p for p in proc.stdout.decode("utf-8", errors="replace").split("\0") if p]


def git_status_short() -> str:
    return run(["git", "status", "--short"], check=True).stdout


def read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        if path.is_file() and path.stat().st_size <= limit:
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return ""


def read_json(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    if not text:
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {"_non_object": value}
    except Exception as exc:
        return {"_json_error": f"{type(exc).__name__}: {exc}"}


def protected_root_input(path: str) -> bool:
    base = Path(path).name
    if path in PROTECTED_ROOT_INPUTS:
        return True
    if "_inbox" in base and Path(path).parent == Path("."):
        return True
    if base.endswith("_seed.csv") and base not in ROOT_GENERATED_EXACT:
        return True
    return False


def extract_static_outputs(paths: Iterable[str]) -> Set[str]:
    outputs: Set[str] = set()
    for rel in paths:
        if not rel.endswith(".py"):
            continue
        text = read_text(Path(rel))
        if not text:
            continue
        for pattern in WRITE_PATTERNS:
            for match in pattern.finditer(text):
                candidate = norm(match.group(1))
                if not candidate or candidate.startswith(("http://", "https://")):
                    continue
                suffix = Path(candidate).suffix.lower()
                if suffix in {".py", ".yml", ".yaml", ".toml"}:
                    continue
                if candidate in DEFERRED_PHASE3_EXACT:
                    continue
                if candidate in PROTECTED_EXACT or any(candidate.startswith(p) for p in PROTECTED_PREFIXES):
                    continue
                outputs.add(candidate)
    return outputs


def classify_tracked(path: str, static_outputs: Set[str]) -> Optional[str]:
    path = norm(path)
    top = path.split("/", 1)[0]
    if path in DEFERRED_PHASE3_EXACT:
        return None
    if path in PROTECTED_EXACT or protected_root_input(path):
        return None
    if any(path.startswith(p) for p in PROTECTED_PREFIXES):
        return None
    if top in GENERATED_TOP_LEVEL_DIRS or top.endswith("_dashboard") or top.endswith("_run_history"):
        return "generated_top_level"
    if any(path.startswith(p) for p in GENERATED_PREFIXES):
        return "generated_prefix"
    if path.endswith(".pyc") or "__pycache__/" in path:
        return "runtime_cache"
    if "/" not in path:
        if path in ROOT_GENERATED_EXACT:
            return "generated_root_exact"
        if any(fnmatch.fnmatch(path, pattern) for pattern in ROOT_GENERATED_PATTERNS):
            return "generated_root_pattern"
        if path in static_outputs:
            return "static_write_target"
        suffix = Path(path).suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            text = read_text(Path(path))
            if text and any(marker.search(text[:32_768]) for marker in GENERATED_MARKERS):
                return "generated_content_marker"
        if suffix == ".zip":
            return "generated_archive"
    return None


def scan_generated() -> Tuple[List[str], Dict[str, int], Set[str]]:
    tracked = git_ls_files()
    static_outputs = extract_static_outputs(tracked)
    rows: List[Tuple[str, str]] = []
    for path in tracked:
        category = classify_tracked(path, static_outputs)
        if category:
            rows.append((path, category))
    counts = Counter(category for _, category in rows)
    return [path for path, _ in rows], dict(sorted(counts.items())), static_outputs


def classify_dirty(path: str) -> str:
    path = norm(path)
    top = path.split("/", 1)[0]
    if path.startswith("assets/leagues/wnba/athletes/") and path.endswith(".approved"):
        return "asset_runtime"
    if path.startswith("assets/leagues/wnba/teams/"):
        return "asset_runtime"
    if path.startswith("data/asset_registry/wnba/"):
        return "asset_registry_runtime"
    if path == "config/hsd_expected_games_v5.csv":
        return "phase3_expected_games_runtime"
    if path.startswith("config/"):
        return "config_source"
    if path.startswith(("scripts/", "tests/", ".github/workflows/")) or path.endswith(".py"):
        return "source_test_workflow"
    if top in GENERATED_TOP_LEVEL_DIRS or top.endswith("_dashboard") or top.endswith("_run_history"):
        return "generated_runtime"
    if any(path.startswith(p) for p in GENERATED_PREFIXES):
        return "generated_runtime"
    if "/" not in path and (
        path in ROOT_GENERATED_EXACT
        or any(fnmatch.fnmatch(path, pattern) for pattern in ROOT_GENERATED_PATTERNS)
    ):
        return "generated_runtime"
    if path.endswith(".pyc") or "__pycache__/" in path:
        return "generated_runtime"
    return "unclassified"


def dirty_summary() -> Dict[str, Any]:
    rows = []
    counts: Counter[str] = Counter()
    for line in git_status_short().splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        category = classify_dirty(path)
        counts[category] += 1
        rows.append({"status": status, "path": path, "category": category})
    return {"count": len(rows), "category_counts": dict(sorted(counts.items())), "rows": rows}


def delete_generated(paths: List[str]) -> None:
    if not paths:
        return
    top_dirs = sorted({
        p.split("/", 1)[0] for p in paths
        if "/" in p and (
            p.split("/", 1)[0] in GENERATED_TOP_LEVEL_DIRS
            or p.split("/", 1)[0].endswith("_dashboard")
            or p.split("/", 1)[0].endswith("_run_history")
        )
    })
    for directory in top_dirs:
        subprocess.run(["git", "rm", "-r", "-f", "--ignore-unmatch", "--", directory], check=True)
    remaining = [p for p in paths if p.split("/", 1)[0] not in top_dirs]
    for start in range(0, len(remaining), 100):
        chunk = remaining[start:start + 100]
        subprocess.run(["git", "rm", "-r", "-f", "--ignore-unmatch", "--", *chunk], check=True)


def patch_gitignore(deleted_paths: Iterable[str]) -> None:
    path = Path(".gitignore")
    text = read_text(path)
    marker = "# HSD Phase 2G authoritative closure"
    before = text.split(marker, 1)[0].rstrip() if marker in text else text.rstrip()
    root_files = sorted({p for p in deleted_paths if "/" not in p})
    lines = [
        "", marker,
        "# Runtime products are artifacts, never repository state.",
        "/phase2_closure_v1.json", "/phase2_closure_v1.md",
        "/phase2g_install_report.json", "/phase2g_install_report.md",
        "/phase2g_deleted_paths.txt",
        "/*_dashboard/", "/*_run_history/",
        "/asset_desk_dashboard/", "/chatgpt_review_pack/", "/outputs/",
        "/operator/inbox/", "/hsd_pipeline_lite_review/",
        "!/studio_bridge_v1_3_notes.md",
    ]
    lines.extend(f"/{name}" for name in root_files)
    path.write_text(before + "\n" + "\n".join(dict.fromkeys(lines)) + "\n", encoding="utf-8")


def patch_sanity_workflow() -> None:
    path = SANITY_WORKFLOW
    text = read_text(path)
    if not text:
        raise RuntimeError(f"Missing {path}")
    test_name = "tests/test_v4_phase2g_phase2_closure.py"
    if test_name not in text:
        needle = "tests/test_v4_phase2e_dirty_tree_hygiene.py"
        if needle not in text:
            raise RuntimeError("Could not find Phase 2E test marker in sanity workflow")
        text = text.replace(needle, needle + " " + test_name, 1)
    step_name = "Run V4 Phase 2 closure gate"
    if step_name not in text:
        marker = "      - name: Upload V3 sanity artifact\n"
        closure_step = (
            "      - name: Run V4 Phase 2 closure gate\n"
            "        if: always()\n"
            "        shell: bash\n"
            "        run: |\n"
            "          python scripts/report_hsd_phase2_closure_v1.py --audit --strict\n\n"
        )
        if marker not in text:
            raise RuntimeError("Could not find artifact upload marker in sanity workflow")
        text = text.replace(marker, closure_step + marker, 1)
    if "            phase2_closure_v1.md\n" not in text:
        marker = "            dirty_tree_v1.json\n"
        text = text.replace(
            marker,
            marker + "            phase2_closure_v1.md\n            phase2_closure_v1.json\n",
            1,
        )
    path.write_text(text, encoding="utf-8")


def append_ignore_for_generated(paths: Iterable[str]) -> None:
    patch_gitignore(paths)


def legacy_workflow_audit() -> Dict[str, Any]:
    rows = []
    for path in LEGACY_WORKFLOWS:
        text = read_text(path)
        problems: List[str] = []
        if not text:
            problems.append("missing")
        if "workflow_dispatch:" not in text:
            problems.append("not_manual")
        if re.search(r"(?m)^\s*push:\s*$", text):
            problems.append("push_trigger")
        if re.search(r"(?m)^\s*schedule:\s*$", text):
            problems.append("schedule_trigger")
        if "contents: write" in text:
            problems.append("contents_write")
        if "git push" in text or "git commit" in text:
            problems.append("git_write_command")
        rows.append({"path": str(path), "passes": not problems, "problems": problems})
    return {"passes": all(row["passes"] for row in rows), "rows": rows}


def dependency_audit() -> Dict[str, Any]:
    hits = []
    for path in REQUIREMENT_FILES:
        for line in read_text(path).splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue
            lower = clean.lower()
            for token in BLOCKED_DEPENDENCY_TOKENS:
                if token in lower:
                    hits.append({"path": str(path), "line": clean, "token": token})
    return {"passes": not hits, "hits": hits}


def build_closure_report(installer_mode: bool = False) -> Dict[str, Any]:
    generated, generated_counts, static_outputs = scan_generated()
    dirty = dirty_summary()
    legacy = legacy_workflow_audit()
    deps = dependency_audit()
    source_truth = read_json(Path(SOURCE_TRUTH_JSON))
    logo = read_json(Path(LOGO_STATUS_JSON))

    blockers: List[str] = []
    warnings: List[str] = []
    if generated:
        blockers.append(f"tracked_generated_output_remaining:{len(generated)}")
    for category in ("source_test_workflow", "config_source", "unclassified"):
        count = int(dirty["category_counts"].get(category, 0))
        if count:
            blockers.append(f"dirty_{category}:{count}")
    if not legacy["passes"]:
        blockers.append("legacy_workflow_quarantine_failed")
    if not deps["passes"]:
        blockers.append("paid_or_llm_dependency_detected")

    source_blockers = sorted(set(source_truth.get("blockers") or []))
    unexpected_source = sorted(set(source_blockers) - ALLOWED_PHASE3_SOURCE_BLOCKERS)
    if source_truth:
        if unexpected_source:
            blockers.append("unexpected_source_truth_blocker")
        if source_blockers:
            warnings.append("source_truth_remediation_deferred_to_phase3")
    elif installer_mode:
        warnings.append("runtime_source_truth_report_not_generated_in_installer")
    else:
        blockers.append("source_truth_report_missing")

    active_fallbacks = int(logo.get("active_logo_fallbacks") or 0) if logo else 0
    if logo:
        if active_fallbacks:
            blockers.append(f"active_logo_fallbacks:{active_fallbacks}")
        recoverable = int(logo.get("recoverable_logo_warnings") or 0)
        if recoverable:
            warnings.append(f"recoverable_logo_warnings:{recoverable}")
    elif installer_mode:
        warnings.append("runtime_logo_report_not_generated_in_installer")
    else:
        blockers.append("renderer_logo_status_missing")

    status = "phase2_closed" if not blockers else "phase2_open"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "phase2_closed": not blockers,
        "installer_mode": installer_mode,
        "blockers": blockers,
        "warnings": warnings,
        "tracked_generated_output_count": len(generated),
        "tracked_generated_output_categories": generated_counts,
        "tracked_generated_output_sample": generated[:200],
        "static_output_target_count": len(static_outputs),
        "dirty_tree": dirty,
        "legacy_workflows": legacy,
        "dependency_audit": deps,
        "deferred_to_phase3": {
            "source_truth_blockers": sorted(set(source_blockers) & ALLOWED_PHASE3_SOURCE_BLOCKERS),
            "unexpected_source_truth_blockers": unexpected_source,
            "expected_games_config": "config/hsd_expected_games_v5.csv",
        },
        "renderer": {
            "active_logo_fallbacks": active_fallbacks,
            "review_only": logo.get("review_only") if logo else None,
        },
        "policy": {
            "free_only": True,
            "artifact_only": True,
            "source_and_config_prefixes_protected": True,
            "root_wildcards_never_apply_inside_config": True,
        },
    }


def write_report(report: Dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD V4 Phase 2 Closure",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Version: `{report['version']}`",
        f"Status: `{report['status']}`",
        f"Phase 2 closed: `{report['phase2_closed']}`",
        "",
        "## Evidence",
        "",
        f"- Tracked generated outputs: `{report['tracked_generated_output_count']}`",
        f"- Dirty entries: `{report['dirty_tree']['count']}`",
        f"- Legacy workflows quarantined: `{report['legacy_workflows']['passes']}`",
        f"- Free-only dependencies: `{report['dependency_audit']['passes']}`",
        f"- Active logo fallbacks: `{report['renderer']['active_logo_fallbacks']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["blockers"])
    if not report["blockers"]:
        lines.append("- None")
    lines += ["", "## Warnings", ""]
    lines.extend(f"- `{item}`" for item in report["warnings"])
    if not report["warnings"]:
        lines.append("- None")
    lines += ["", "## Deferred to Phase 3", ""]
    for item in report["deferred_to_phase3"]["source_truth_blockers"]:
        lines.append(f"- `{item}`")
    if not report["deferred_to_phase3"]["source_truth_blockers"]:
        lines.append("- None")
    lines += [
        "",
        "Phase 2 closes repository hygiene, workflow truthfulness, free-only enforcement, "
        "and closure gating. Phase 3 replaces the circular expected-games baseline and "
        "strengthens independent schedule verification.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def install() -> int:
    initial, initial_counts, _ = scan_generated()
    deleted: List[str] = []
    for _ in range(4):
        candidates, _, _ = scan_generated()
        if not candidates:
            break
        delete_generated(candidates)
        deleted.extend(candidates)
    remaining, remaining_counts, _ = scan_generated()

    patch_gitignore(deleted)
    # IMPORTANT: Do not modify .github/workflows/* during the installer run.
    # GitHub Actions GITHUB_TOKEN cannot push workflow changes unless it has the
    # workflows permission. The first Phase 2G run proved this by cleaning the repo
    # successfully, then failing only when the commit included a workflow edit.
    # Keep workflow wiring as a separate manual/web upload after Phase 2 closes.

    install_report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "initial_generated_count": len(initial),
        "initial_categories": initial_counts,
        "deleted_count": len(set(deleted)),
        "remaining_generated_count": len(remaining),
        "remaining_categories": remaining_counts,
        "remaining_sample": remaining[:200],
        "iterations_max": 4,
        "status": "ready_to_commit" if not remaining else "blocked_remaining_generated_output",
        "installer_patches_workflows": False,
        "workflow_patch_deferred": ".github/workflows/hsd-v3-repo-state-sanity.yml",
    }
    Path(INSTALL_REPORT_JSON).write_text(
        json.dumps(install_report, indent=2, sort_keys=True), encoding="utf-8"
    )
    Path(DELETED_PATHS_TXT).write_text(
        "\n".join(sorted(set(deleted))) + ("\n" if deleted else ""),
        encoding="utf-8",
    )
    Path(INSTALL_REPORT_MD).write_text(
        "\n".join([
            "# HSD Phase 2G Install Report",
            "",
            f"Generated: `{install_report['generated_at_utc']}`",
            f"Initial generated paths: `{install_report['initial_generated_count']}`",
            f"Deleted paths: `{install_report['deleted_count']}`",
            f"Remaining generated paths: `{install_report['remaining_generated_count']}`",
            f"Status: `{install_report['status']}`",
            "",
        ]),
        encoding="utf-8",
    )
    print(json.dumps(install_report, indent=2))
    return 0 if not remaining else 2


def self_test() -> int:
    assert classify_tracked("config/graphics_rendered_qa_policy_v2.json", set()) is None
    assert classify_tracked("studio_bridge_v1_3_notes.md", set()) is None
    assert classify_tracked("studio_run_history/x.md", set()) == "generated_top_level"
    assert classify_tracked("news_dashboard/index.html", set()) == "generated_top_level"
    assert classify_tracked("team_assets.csv", set()) == "generated_root_exact"
    assert classify_tracked("operator/inbox/template.csv", set()) == "generated_prefix"
    assert classify_dirty("scripts/example.py") == "source_test_workflow"
    assert classify_dirty("data/asset_registry/wnba/team_logos.csv") == "asset_registry_runtime"
    print("Phase 2G self-test passed")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="HSD V4 Phase 2G cleanup and closure gate.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--installer-mode", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.install:
        return install()

    report = build_closure_report(installer_mode=args.installer_mode)
    write_report(report, Path(CLOSURE_JSON), Path(CLOSURE_MD))
    print(json.dumps({
        "version": VERSION,
        "status": report["status"],
        "phase2_closed": report["phase2_closed"],
        "blockers": report["blockers"],
        "warnings": report["warnings"],
        "json": CLOSURE_JSON,
        "md": CLOSURE_MD,
    }, indent=2))
    if args.strict and report["blockers"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
