from __future__ import annotations

import csv
import json
from pathlib import Path

import generate_hsd_operator_command_center_v2 as command_center

REPO = Path(__file__).resolve().parents[1]


def write_json(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def write_csv(path: str, rows: list[dict[str, str]]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def seed_daily_ops_files() -> None:
    write_json(
        "operator_status.json",
        {
            "overall": "NO-GO",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "publish_guard_report.json",
        {
            "publish_mode": "artifact_only",
            "publish_allowed": False,
            "graphics_handoff_allowed": False,
            "preview_gate_status": "PASS",
            "rendered_qa_status": "not_run",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "results_desk_v5_manifest.json",
        {
            "counts": {"women_events": 8, "graphics_ready": 1},
            "source_health": [
                {
                    "source_name": "espn_wnba_public",
                    "sport_or_league": "WNBA",
                    "date": "20260624",
                    "ok": "Yes",
                    "events_found": 4,
                    "notes": "free public source ok",
                }
            ],
        },
    )
    write_csv(
        "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "headline": "New York Liberty beat Las Vegas Aces",
                "production_ready": "Yes",
                "caption_hard_fact": "Verified final: New York Liberty 87, Las Vegas Aces 76.",
                "source_count": "4",
            }
        ],
    )
    write_csv(
        "studio_bundle_queue.csv",
        [
            {
                "production_priority": "POST FIRST",
                "bundle_name": "Tonight in the W",
                "bundle_type": "wnba_preview_premium",
                "asset_shape": "1080x1350",
                "freshness_decision": "allow",
                "source_headlines": "Phoenix Mercury at Indiana Fever",
            }
        ],
    )
    Path("bebe_posting_schedule_today.md").write_text(
        "\n".join(
            [
                "## Posting schedule",
                "",
                "| Time ET | Platform | Slot | Status | Recommended action | Artifact |",
                "|---|---|---|---|---|---|",
                "| 12:00 | IG Feed | Main post 1 | needs_assets | Build the post manually. | studio_bundle_queue.csv |",
            ]
        ),
        encoding="utf-8",
    )
    Path("operator_status.md").write_text("# Operator status\n", encoding="utf-8")
    Path("publish_guard_report.md").write_text("# Publish guard\n", encoding="utf-8")
    write_json(
        "source_registry_audit.json",
        {
            "counts": {"sources": 3, "pass": 2, "review": 1, "fail": 0},
            "output_scope": "run_scoped",
        },
    )
    Path("source_registry_audit.md").write_text("# Source registry audit\n", encoding="utf-8")
    Path("studio_bundle_queue.csv").touch()


def test_operator_command_center_builds_daily_ops_view(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()

    payload = command_center.build_payload()
    html = command_center.render_html(payload)
    markdown = command_center.render_markdown(payload)

    assert payload["version"] == "hsd-operator-command-center-v3.0.0-daily-ops"
    assert payload["decision"]["automation"] == "OFF / artifact-only"
    assert payload["decision"]["free_source_mode"] == "Free public sources only"
    assert payload["briefing"]["best_candidate"] == "New York Liberty beat Las Vegas Aces"
    assert payload["briefing"]["studio_lane"] == "Tonight in the W"
    assert any(action["status"] == "Manual only" for action in payload["next_actions"])
    assert any(action["title"] == "Review source registry audit" for action in payload["next_actions"])
    assert any(action["title"] == "Build graphics pack for Tonight in the W" for action in payload["next_actions"])
    assert any(item["label"] == "Source registry" and item["value"] == "REVIEW" for item in payload["metrics"])
    assert payload["briefing"]["source_state"] == "2 pass, 1 review, 0 fail across 3 sources."

    assert "HSD Daily Operator Command Center" in html
    assert 'data-tab-target="today"' in html
    assert 'data-tab-target="content"' in html
    assert 'data-tab-target="safety"' in html
    assert 'data-tab-target="artifacts"' in html
    assert 'id="artifactSearch"' in html
    assert "Paid APIs and auto-publishing are off" in html
    assert "Next actions" in markdown

    command_center.write_outputs(payload)
    assert Path("operator_command_center.html").exists()
    assert Path("operator_command_center.json").exists()
    assert Path("operator_command_center.md").exists()


def test_operator_command_center_does_not_refresh_handoff_as_side_effect(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    Path("generate_hsd_mermaid_handoff_publisher_v2_6_1.py").write_text(
        "from pathlib import Path\nPath('unexpected_refresh_marker.txt').write_text('ran')\n",
        encoding="utf-8",
    )

    command_center.write_outputs(command_center.build_payload())

    assert not Path("unexpected_refresh_marker.txt").exists()


def test_local_runner_collects_daily_command_center_artifacts() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    assert "operator_command_center.html" in runner
    assert "operator_command_center.md" in runner
    assert "operator_command_center.json" in runner
    assert "bebe_posting_schedule_today.md" in runner
    assert "preview_bundle_quality_summary.csv" in runner
    assert "publish_guard_report.json" in runner
    assert "source_registry_audit.md" in runner
    assert "source_registry_audit.json" in runner
    assert "manual_workflow_handoff.md" in runner
    assert "manual_workflow_pack_status.csv" in runner
    assert "ig_story_results_queue.csv" in runner
    assert "ig_story_results_upload_pack_status.csv" in runner
    assert "final_score_story_guard_report.md" in runner
    assert "multi_post_daily_board.md" in runner
    assert "post_slot_status.csv" in runner
    assert "ig_feed_queue.csv" in runner
    assert "threads_queue.csv" in runner
    assert "launch_command_center.md" in runner
    assert "launch_instagram_publish_queue.csv" in runner
    assert "launch_quality_gate.csv" in runner
    assert "launch_manifest.json" in runner
    assert "results_dashboard/index.html" in runner
    assert "studio_dashboard/index.html" in runner
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")
    assert "Results drill-down dashboard" in command_center
    assert "Studio drill-down dashboard" in command_center
