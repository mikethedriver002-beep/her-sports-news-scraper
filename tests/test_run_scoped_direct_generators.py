from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

import hsd_run_io


REPO = Path(__file__).resolve().parents[1]


def test_run_io_writes_to_env_folder_and_reads_run_first(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    Path("artifact.md").write_text("legacy", encoding="utf-8")
    hsd_run_io.write_text("artifact.md", "fresh")

    assert (run_dir / "artifact.md").read_text(encoding="utf-8") == "fresh"
    assert hsd_run_io.read_text("artifact.md") == "fresh"
    assert hsd_run_io.input_path("artifact.md") == run_dir / "artifact.md"
    assert hsd_run_io.output_path("nested/status.json") == run_dir / "nested" / "status.json"


def test_write_json_skips_timestamp_only_rewrite(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "status.json"

    hsd_run_io.write_json(
        target,
        {"generated_at_utc": "2026-06-30T10:00:00+00:00", "status": "ready", "rows": [{"entity": "wnba", "count": 4}]},
        sort_keys=True,
    )
    hsd_run_io.write_json(
        target,
        {"generated_at_utc": "2026-06-30T11:00:00+00:00", "status": "ready", "rows": [{"entity": "wnba", "count": 4}]},
        sort_keys=True,
    )

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["generated_at_utc"] == "2026-06-30T10:00:00+00:00"
    assert payload["status"] == "ready"


def test_write_json_rewrites_when_nonvolatile_payload_changes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "status.json"

    hsd_run_io.write_json(
        target,
        {"generated_at_utc": "2026-06-30T10:00:00+00:00", "status": "ready", "rows": [{"entity": "wnba", "count": 4}]},
        sort_keys=True,
    )
    hsd_run_io.write_json(
        target,
        {"generated_at_utc": "2026-06-30T11:00:00+00:00", "status": "ready", "rows": [{"entity": "wnba", "count": 5}]},
        sort_keys=True,
    )

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["generated_at_utc"] == "2026-06-30T11:00:00+00:00"
    assert payload["rows"][0]["count"] == 5


def test_write_text_can_ignore_generated_line_when_requested(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "report.md"

    def strip_generated_line(text: str) -> str:
        return "\n".join(line for line in text.splitlines() if not line.startswith("Generated:"))

    hsd_run_io.write_text(target, "# Report\n\nGenerated: 2026-06-30T10:00:00+00:00\n\nStable body.\n")
    hsd_run_io.write_text(
        target,
        "# Report\n\nGenerated: 2026-06-30T11:00:00+00:00\n\nStable body.\n",
        normalize=strip_generated_line,
    )

    assert target.read_text(encoding="utf-8") == "# Report\n\nGenerated: 2026-06-30T10:00:00+00:00\n\nStable body.\n"


def test_write_csv_can_ignore_reviewed_at_field_when_requested(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "intake.csv"
    fieldnames = ["asset_id", "operator_decision", "reviewed_at_local"]

    hsd_run_io.write_csv(
        target,
        [{"asset_id": "APQ001", "operator_decision": "hold", "reviewed_at_local": "2026-06-30T10:00:00-04:00"}],
        fieldnames,
    )
    hsd_run_io.write_csv(
        target,
        [{"asset_id": "APQ001", "operator_decision": "hold", "reviewed_at_local": "2026-06-30T11:00:00-04:00"}],
        fieldnames,
        volatile_fields=["reviewed_at_local"],
    )

    rows = list(csv.DictReader(target.read_text(encoding="utf-8").splitlines()))
    assert rows == [{"asset_id": "APQ001", "operator_decision": "hold", "reviewed_at_local": "2026-06-30T10:00:00-04:00"}]


def test_direct_run_generators_are_wired_to_shared_run_io() -> None:
    required = {
        "generate_hsd_results_desk_v5.py": ["from hsd_run_io import", "write_text(BOX_SCORE_SUMMARY_FILE", "write_json(MANIFEST_FILE"],
        "generate_hsd_news_sync_v1.py": ["from hsd_run_io import", "input_candidates(path)", "write_run_json(NEWS_MANIFEST_JSON"],
        "normalize_hsd_manual_story_inbox_v1.py": ["from hsd_run_io import", 'OUT_CSV = "story_candidates_manual.csv"', "write_csv(OUT_CSV"],
        "ingest_hsd_discovery_sources_v1.py": ["from hsd_run_io import", 'OUT_CSV = "story_candidates_discovery.csv"', "write_csv(OUT_CSV"],
        "scripts/generate_hsd_expected_games_v5.py": ["from hsd_run_io import", 'OUTPUT_FILE = output_path("config/hsd_expected_games_v5.csv")', "canonical_config_note"],
        "scripts/verify_hsd_wnba_schedule_independent_v5.py": ["from hsd_run_io import", 'OUT_JSON = output_path("independent_schedule_verification_v5.json")', "write_json(OUT_JSON"],
        "generate_news_dashboard_v1.py": ["from hsd_run_io import", 'OUTPUT_DIR = output_path("news_dashboard")', "write_text(OUTPUT_FILE"],
        "generate_results_dashboard_v4.py": ["from hsd_run_io import", 'OUTPUT_DIR = output_path("results_dashboard")', "write_text(OUTPUT_FILE"],
        "generate_hsd_studio_dashboard_v1.py": ["from hsd_run_io import", 'OUT_DIR = output_path("studio_dashboard")', "write_text(OUT_FILE"],
        "generate_hsd_studio_bridge_v1.py": ["from hsd_run_io import", "input_candidates(path)", "write_run_json(OUT_MANIFEST"],
        "generate_hsd_tonight_preview_bridge_v1.py": ["from hsd_run_io import", 'write_json("studio_preview_build_v2.json"', 'write_csv("studio_bundle_queue.csv"'],
        "generate_hsd_preview_quality_gate_v1.py": ["from hsd_run_io import", "write_text(\"preview_bundle_quality.md\""],
        "scripts/build_hsd_render_visual_qa_contact_sheet_refresh_v1.py": ["from hsd_run_io import", 'OUT_DIR_REL = Path("render_visual_qa_contact_sheet_refresh")', "write_json(out_json"],
        "publish_hsd_guard_v1.py": ["from hsd_run_io import", "OUT_JSON = output_path("],
        "generate_hsd_operator_status_v1.py": ["from hsd_run_io import", 'output_path("operator_status.csv")'],
        "generate_hsd_bebe_daily_ops_plan_v2.py": ["from hsd_run_io import", "OUT_MD = output_path("],
        "generate_hsd_source_registry_audit_v2.py": ["from hsd_run_io import", 'OUT_CSV = "source_registry_audit.csv"', "write_json(OUT_JSON"],
        "generate_hsd_morning_source_discovery_board_v1.py": ["from hsd_run_io import", 'OUT_CSV = output_path("morning_source_discovery_board.csv")', "write_json(OUT_JSON"],
        "generate_hsd_operator_command_center_v2.py": ["from hsd_run_io import", "OUT_HTML = output_path("],
        "generate_hsd_pipeline_review_lite_v1.py": ["from hsd_run_io import", "OUT_DIR = output_path("],
    }

    for rel, needles in required.items():
        text = (REPO / rel).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {rel}"


def test_operator_command_center_writes_outputs_inside_run_folder(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    (run_dir / "operator_status.json").write_text(json.dumps({"overall": "READY_FOR_GRAPHICS"}), encoding="utf-8")
    (run_dir / "publish_guard_report.json").write_text(
        json.dumps({"publish_mode": "artifact_only", "publish_allowed": False, "graphics_handoff_allowed": True}),
        encoding="utf-8",
    )
    with (run_dir / "news_fact_packets.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["urgency", "headline", "production_ready", "caption_hard_fact", "source_count"])
        writer.writeheader()
        writer.writerow({"urgency": "P1", "headline": "Run scoped packet", "production_ready": "Yes", "caption_hard_fact": "Verified.", "source_count": "2"})

    import generate_hsd_operator_command_center_v2 as command_center

    try:
        command_center = importlib.reload(command_center)
        payload = command_center.build_payload()
        command_center.write_outputs(payload)

        assert payload["briefing"]["best_candidate"] == "Run scoped packet"
        assert (run_dir / "operator_command_center.html").exists()
        assert (run_dir / "operator_command_center.json").exists()
        assert (run_dir / "operator_command_center.md").exists()
        assert (run_dir / "render_prep_packets.md").exists()
        assert (run_dir / "render_prep_packets.csv").exists()
        assert (run_dir / "render_prep_packets.json").exists()
        assert (run_dir / "render_handoff_top_packet" / "README.md").exists()
        assert (run_dir / "render_handoff_top_packet" / "active_asset_review_queue.md").exists()
        assert (run_dir / "render_handoff_top_packet" / "active_asset_review_queue.csv").exists()
        assert (run_dir / "render_handoff_top_packet" / "manual_renderer_prompt.md").exists()
        assert (run_dir / "render_handoff_top_packet" / "handoff_manifest.json").exists()
        assert not Path("operator_command_center.html").exists()
        assert not Path("render_prep_packets.md").exists()
        assert not Path("render_handoff_top_packet").exists()
    finally:
        monkeypatch.delenv("HSD_RUN_OUTPUT_DIR", raising=False)
        importlib.reload(command_center)
