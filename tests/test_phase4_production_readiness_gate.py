from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_production_readiness_v1.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"
GITIGNORE = REPO / ".gitignore"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_production_readiness_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def seed_ready_repo(root: Path, *, source_ok: bool = True, both_logos: bool = True, stale: int = 0) -> None:
    write_json(root / "v4_source_truth_guard.json", {"status": "passed_source_truth_guard" if source_ok else "blocked_source_truth", "blockers": [] if source_ok else ["x"], "warnings": []})
    write_json(root / "source_accuracy_v5.json", {"counts": {"expected_missing": 0, "stale_observations": stale, "duplicate_groups": 0}})
    write_json(root / "results_desk_v5_manifest.json", {"counts": {"expected_games": 1, "missing_expected_games": 0}})
    write_json(root / "missing_games_alert_v5.json", {"summary": {"expected_games": 1, "missing": 0}})
    write_json(root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_logo_status.json", {"active_logo_fallbacks": 0, "recoverable_logo_warnings": 0, "effective_publish_status": "no_active_logo_fallback", "rendered_count": 1})
    write_json(root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_manifest.json", {"version": "v2.5-hsd-quality-tonight-logo-integrity-review-only", "review_only": True, "rendered_count": 1, "fallback_logo_warnings": 0})
    output = root / "outputs/latest/HSD_QUALITY_GRAPHICS/ig_feed/sample.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"fake png")
    write_csv(
        root / "hsd_quality_graphics_manifest.csv",
        [
            {
                "event_id": "event_1",
                "platform": "ig_feed",
                "row_kind": "result",
                "headline": "Sample Team beat Other Team",
                "output_path": "outputs/latest/HSD_QUALITY_GRAPHICS/ig_feed/sample.png",
                "width": "1080",
                "height": "1350",
                "used_home_logo": "yes" if both_logos else "no",
                "used_away_logo": "yes",
                "status": "rendered",
                "notes": "test",
            }
        ],
        ["event_id", "platform", "row_kind", "headline", "output_path", "width", "height", "used_home_logo", "used_away_logo", "status", "notes"],
    )
    write_csv(
        root / "outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv",
        [{"package_id": "p1", "headline": "Sample Team beat Other Team", "variant": "logos_only", "status": "ready", "player_mode": "logos_only_forced"}],
        ["package_id", "headline", "variant", "status", "player_mode"],
    )
    copy = root / "outputs/latest/production_graphics_director/copy_director/post_ready_copy.md"
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_text("# HSD Post-Ready Copy\n\n## Sample Team beat Other Team\n\nCaption text.\n", encoding="utf-8")


def test_phase4_production_readiness_passes_for_clean_post_ready_candidate(tmp_path: Path) -> None:
    module = load_module()
    seed_ready_repo(tmp_path)

    report = module.build_report(tmp_path)

    assert report["status"] == "production_review_ready"
    assert report["publish_gate"] == "human_visual_review_required_before_post"
    assert report["blockers"] == []
    assert report["quality_graphics"]["post_ready_candidates"] == 1
    assert report["quality_graphics"]["review_only"] == 0
    assert report["post_ready_assets"][0]["manual_visual_review_required"] == "Yes"


def test_phase4_blocks_when_source_truth_is_blocked(tmp_path: Path) -> None:
    module = load_module()
    seed_ready_repo(tmp_path, source_ok=False)

    report = module.build_report(tmp_path)

    assert report["status"] == "blocked"
    assert "source_truth_guard_not_passed" in report["blockers"]
    assert report["strict_exit_code"] == 2


def test_phase4_moves_missing_logo_rows_to_review_only(tmp_path: Path) -> None:
    module = load_module()
    seed_ready_repo(tmp_path, both_logos=False)

    report = module.build_report(tmp_path)

    assert report["status"] == "blocked"
    assert "no_post_ready_candidates_after_quality_gate" in report["blockers"]
    assert report["quality_graphics"]["post_ready_candidates"] == 0
    assert report["quality_graphics"]["review_only"] == 1
    assert "both_team_logos_not_confirmed" in report["review_only_assets"][0]["reasons"]


def test_phase4_blocks_stale_observations(tmp_path: Path) -> None:
    module = load_module()
    seed_ready_repo(tmp_path, stale=1)

    report = module.build_report(tmp_path)

    assert report["status"] == "blocked"
    assert "stale_observations_present" in report["blockers"]


def test_phase4_main_writes_all_artifacts(tmp_path: Path) -> None:
    module = load_module()
    seed_ready_repo(tmp_path)

    assert module.main(["--repo-root", str(tmp_path), "--strict"]) == 0
    assert (tmp_path / "production_readiness_v1.json").exists()
    assert (tmp_path / "production_readiness_v1.md").exists()
    assert (tmp_path / "post_ready_assets_v1.csv").exists()
    assert (tmp_path / "review_only_assets_v1.csv").exists()
    assert (tmp_path / "daily_operator_brief_v1.md").exists()


def test_phase4_gate_is_wired_into_sanity_workflow_and_gitignore() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    gitignore = GITIGNORE.read_text(encoding="utf-8")

    assert "Run V4 production readiness gate" in workflow
    assert "python scripts/report_hsd_production_readiness_v1.py --strict" in workflow
    assert "production_readiness_v1.json" in workflow
    assert "daily_operator_brief_v1.md" in workflow
    assert "tests/test_phase4_production_readiness_gate.py" in workflow

    assert "/production_readiness_v1.json" in gitignore
    assert "/daily_operator_brief_v1.md" in gitignore
