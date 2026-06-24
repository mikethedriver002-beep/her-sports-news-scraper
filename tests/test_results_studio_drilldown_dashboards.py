from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_results_dashboard_reads_run_inputs_and_writes_run_dashboard(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    result_fields = [
        "sport_norm",
        "status_norm",
        "editorial_bucket",
        "editorial_rank",
        "graphics_headline",
        "league_norm",
        "final_score_display",
        "outcome_type",
        "content_family",
        "all_sources_json",
        "editorial_tier",
        "content_action",
        "confidence",
        "manual_review",
        "selected_source",
        "gender_scope",
        "include_in_graphics",
        "include_in_dashboard",
    ]
    write_csv(
        run_dir / "reconciled_events.csv",
        [
            {
                "sport_norm": "basketball",
                "status_norm": "final",
                "editorial_bucket": "Must Post",
                "editorial_rank": "1",
                "graphics_headline": "Run scoped result headline",
                "league_norm": "WNBA",
                "final_score_display": "Liberty 88, Aces 77",
                "outcome_type": "win",
                "content_family": "Tonight in the W",
                "all_sources_json": '["espn_wnba_public"]',
                "editorial_tier": "Tier 1",
                "content_action": "Review",
                "confidence": "0.92",
                "manual_review": "Yes",
                "selected_source": "espn_wnba_public",
                "gender_scope": "women",
                "include_in_graphics": "Yes",
                "include_in_dashboard": "Yes",
            }
        ],
        result_fields,
    )
    write_csv(
        run_dir / "source_health_report.csv",
        [
            {
                "source_name": "espn_wnba_public",
                "sport_or_league": "WNBA",
                "date": "2026-06-24",
                "ok": "Yes",
                "events_found": "3",
                "observations_emitted": "3",
                "notes": "run scoped source ok",
            }
        ],
        ["source_name", "sport_or_league", "date", "ok", "events_found", "observations_emitted", "notes"],
    )
    (run_dir / "results_system_hub.md").write_text("Run scoped results hub", encoding="utf-8")
    (run_dir / "results_graphics_queue.md").write_text("Run scoped graphics queue", encoding="utf-8")

    module = load_module(REPO / "generate_results_dashboard_v4.py", "results_dashboard_run_scoped")
    module.main()

    dashboard = run_dir / "results_dashboard" / "index.html"
    assert dashboard.exists()
    text = dashboard.read_text(encoding="utf-8")
    assert "Run scoped result headline" in text
    assert "Run scoped results hub" in text
    assert "run scoped source ok" in text
    assert not (tmp_path / "results_dashboard" / "index.html").exists()


def test_studio_dashboard_reads_run_inputs_and_writes_run_dashboard(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    write_csv(
        run_dir / "studio_bundle_queue.csv",
        [
            {
                "production_priority": "POST FIRST",
                "bundle_type": "carousel",
                "source_items_count": "2",
                "bundle_rank": "1",
                "bundle_name": "Run scoped bundle",
                "source_headlines": "Two verified WNBA notes",
                "caption_seed": "Run scoped caption",
                "bundle_prompt": "Run scoped bundle prompt",
            }
        ],
        [
            "production_priority",
            "bundle_type",
            "source_items_count",
            "bundle_rank",
            "bundle_name",
            "source_headlines",
            "caption_seed",
            "bundle_prompt",
        ],
    )
    write_csv(
        run_dir / "studio_graphics_queue.csv",
        [
            {
                "production_bucket": "today",
                "asset_type": "feed",
                "graphics_safety_mode": "review",
                "studio_rank": "1",
                "headline": "Run scoped studio headline",
                "final_score": "Liberty 88, Aces 77",
                "template": "result_slide_v2",
                "caption_seed": "Studio caption",
                "graphic_prompt": "Studio prompt",
            }
        ],
        [
            "production_bucket",
            "asset_type",
            "graphics_safety_mode",
            "studio_rank",
            "headline",
            "final_score",
            "template",
            "caption_seed",
            "graphic_prompt",
        ],
    )
    write_csv(
        run_dir / "studio_accuracy_checklist.csv",
        [{"headline": "Run scoped studio headline", "check_type": "score", "status": "review", "instruction": "Verify score."}],
        ["headline", "check_type", "status", "instruction"],
    )
    (run_dir / "studio_command_center.md").write_text("Run scoped studio command center", encoding="utf-8")
    (run_dir / "studio_top_graphic_packets.md").write_text("Run scoped top packets", encoding="utf-8")
    (run_dir / "studio_post_schedule.md").write_text("Run scoped schedule", encoding="utf-8")

    module = load_module(REPO / "generate_hsd_studio_dashboard_v1.py", "studio_dashboard_run_scoped")
    module.main()

    dashboard = run_dir / "studio_dashboard" / "index.html"
    assert dashboard.exists()
    text = dashboard.read_text(encoding="utf-8")
    assert "Run scoped bundle" in text
    assert "Run scoped studio headline" in text
    assert "Run scoped studio command center" in text
    assert not (tmp_path / "studio_dashboard" / "index.html").exists()


def test_drilldown_dashboards_preserve_direct_legacy_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HSD_RUN_OUTPUT_DIR", raising=False)

    write_csv(
        tmp_path / "reconciled_events.csv",
        [{"graphics_headline": "Legacy result", "gender_scope": "women", "status_norm": "final", "include_in_dashboard": "Yes"}],
        ["graphics_headline", "gender_scope", "status_norm", "include_in_dashboard"],
    )
    write_csv(
        tmp_path / "studio_bundle_queue.csv",
        [{"bundle_name": "Legacy bundle", "bundle_rank": "1"}],
        ["bundle_name", "bundle_rank"],
    )

    results = load_module(REPO / "generate_results_dashboard_v4.py", "results_dashboard_legacy")
    studio = load_module(REPO / "generate_hsd_studio_dashboard_v1.py", "studio_dashboard_legacy")

    results.main()
    studio.main()

    assert (tmp_path / "results_dashboard" / "index.html").exists()
    assert (tmp_path / "studio_dashboard" / "index.html").exists()
