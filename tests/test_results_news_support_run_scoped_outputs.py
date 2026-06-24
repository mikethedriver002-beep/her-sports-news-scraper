from __future__ import annotations

import csv
import importlib.util
import json
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


def test_results_news_support_scripts_are_wired_to_run_io() -> None:
    required = {
        "scripts/generate_hsd_expected_games_v5.py": [
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
            "from hsd_run_io import",
            'OUTPUT_FILE = output_path("config/hsd_expected_games_v5.csv")',
            "canonical_config_note",
        ],
        "scripts/verify_hsd_wnba_schedule_independent_v5.py": [
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
            "from hsd_run_io import",
            'OUT_JSON = output_path("independent_schedule_verification_v5.json")',
            "write_json(OUT_JSON",
        ],
        "generate_news_dashboard_v1.py": [
            "from hsd_run_io import",
            'OUTPUT_DIR = output_path("news_dashboard")',
            "write_text(OUTPUT_FILE",
        ],
    }

    for rel, needles in required.items():
        text = (REPO / rel).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {rel}"


def test_expected_games_outputs_are_run_scoped_review_copies(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    module = load_module(REPO / "scripts" / "generate_hsd_expected_games_v5.py", "expected_games_run_scoped")
    monkeypatch.setattr(module, "fetch_espn_expected", lambda compact_dates: ([], []))
    monkeypatch.setattr(
        module,
        "manual_seed_rows",
        lambda: (
            [
                module.row_from_game(
                    "2026-06-24",
                    "New York Liberty",
                    "Indiana Fever",
                    "manual_reviewed_expected_seed",
                    "manual-1",
                    "manual",
                )
            ],
            ["manual_expected_games.csv"],
        ),
    )

    module.main()

    assert (run_dir / "config" / "hsd_expected_games_v5.csv").exists()
    assert (run_dir / "expected_games_v5_manifest.json").exists()
    assert (run_dir / "expected_games_v5_report.md").exists()
    assert not (tmp_path / "config" / "hsd_expected_games_v5.csv").exists()
    manifest = json.loads((run_dir / "expected_games_v5_manifest.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"
    assert "Promote it to canonical config only after manual review" in manifest["canonical_config_note"]


def test_independent_verifier_reads_run_expected_games_and_writes_run_reports(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    module = load_module(REPO / "scripts" / "verify_hsd_wnba_schedule_independent_v5.py", "verifier_run_scoped")
    expected_key = module.key_for("2026-06-24", "New York Liberty", "Indiana Fever")
    write_csv(
        run_dir / "config" / "hsd_expected_games_v5.csv",
        [
            {
                "date": "2026-06-24",
                "league": "WNBA",
                "sport": "basketball",
                "home_team": "New York Liberty",
                "away_team": "Indiana Fever",
                "expected_key": expected_key,
                "source_name": "manual_reviewed_expected_seed",
                "source_event_id": "manual-1",
                "source_url": "manual",
                "source_role": "external_expected_schedule_baseline",
            }
        ],
        [
            "date",
            "league",
            "sport",
            "home_team",
            "away_team",
            "expected_key",
            "source_name",
            "source_event_id",
            "source_url",
            "source_role",
        ],
    )
    monkeypatch.setattr(
        module,
        "fetch_all_sources",
        lambda dates: (
            [module.verification_row("2026-06-24", "New York Liberty", "Indiana Fever", "espn_wnba_public_scoreboard_verify", "401", "fixture")],
            [module.source_health("espn_wnba_public_scoreboard_verify", "2026-06-24", True, 200, 1, 1, "ok")],
        ),
    )

    module.main()

    assert (run_dir / "independent_schedule_verification_v5.csv").exists()
    assert (run_dir / "independent_schedule_verification_v5.json").exists()
    assert (run_dir / "independent_schedule_verification_v5.md").exists()
    assert not (tmp_path / "independent_schedule_verification_v5.json").exists()
    summary = json.loads((run_dir / "independent_schedule_verification_v5.json").read_text(encoding="utf-8"))
    assert summary["output_scope"] == "run_scoped"
    assert summary["matched"] == 1


def test_news_dashboard_reads_run_inputs_and_writes_run_dashboard(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    write_csv(
        run_dir / "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "content_family": "results",
                "manual_review": "No",
                "headline": "Run scoped headline",
                "publish_recommendation": "Post",
                "sport": "basketball",
                "league": "WNBA",
                "source_count": "2",
                "primary_source_count": "1",
                "source_confidence_score": "88",
                "source_confidence_tier": "publish_grade",
                "source_publish_grade": "publish_grade",
                "source_confidence_reason": "official source plus free cross-check",
                "context_quality": "strong",
                "quality_score": "91",
                "production_ready": "Yes",
                "content_format_recommendation": "carousel",
                "context_signal": "verified",
                "brief_120w": "Run folder story context.",
                "caption_voice": "sharp",
                "review_flags": "",
            }
        ],
        [
            "urgency",
            "content_family",
            "manual_review",
            "headline",
            "publish_recommendation",
            "sport",
            "league",
            "source_count",
            "primary_source_count",
            "source_confidence_score",
            "source_confidence_tier",
            "source_publish_grade",
            "source_confidence_reason",
            "context_quality",
            "quality_score",
            "production_ready",
            "content_format_recommendation",
            "context_signal",
            "brief_120w",
            "caption_voice",
            "review_flags",
        ],
    )
    write_csv(run_dir / "news_source_observations.csv", [], ["source_name", "source_type", "fetch_status", "usable_context", "title", "url"])
    write_csv(run_dir / "news_input_status_report.csv", [], ["input_name", "resolved_path", "exists", "size_bytes", "has_result_graphic", "has_must_post", "notes"])
    (run_dir / "news_sync_hub.md").write_text("Run hub", encoding="utf-8")
    (run_dir / "news_brief_queue.md").write_text("Run queue", encoding="utf-8")
    (run_dir / "news_daily_plan.md").write_text("Run plan", encoding="utf-8")

    module = load_module(REPO / "generate_news_dashboard_v1.py", "news_dashboard_run_scoped")
    module.main()

    dashboard = run_dir / "news_dashboard" / "index.html"
    assert dashboard.exists()
    dashboard_text = dashboard.read_text(encoding="utf-8")
    assert "Run scoped headline" in dashboard_text
    assert "publish_grade" in dashboard_text
    assert "official source plus free cross-check" in dashboard_text
    assert not (tmp_path / "news_dashboard" / "index.html").exists()
