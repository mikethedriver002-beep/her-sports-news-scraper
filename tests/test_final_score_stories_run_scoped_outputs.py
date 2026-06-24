from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_final_score_stories_v1.py"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_svg(path: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><title>{label}</title><rect width="100" height="100"/></svg>',
        encoding="utf-8",
    )


def test_final_score_stories_write_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    policy = work_dir / "config" / "hsd_final_score_stories_policy_v1.json"
    policy.parent.mkdir(parents=True)
    policy.write_text(
        json.dumps(
            {
                "max_result_age_hours": 999999,
                "espn_fetch": {"enabled": False, "mode": "backfill_only", "days_back": 0},
                "min_contract_finals_before_skip_espn": 1,
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        run_dir / "results_contract_v2.csv",
        [
            {
                "row_kind": "result",
                "status": "Final",
                "content_eligibility": "eligible",
                "freshness_reason": "final_only",
                "event_date_local": "2026-06-24",
                "score_display": "New York Liberty 87 - Las Vegas Aces 76",
                "winner_team_name": "New York Liberty",
                "loser_team_name": "Las Vegas Aces",
                "headline": "New York Liberty beat Las Vegas Aces",
                "event_id": "game-1",
                "source_id": "manual_verified_result",
                "source_url": "https://example.com/box-score",
            }
        ],
        [
            "row_kind",
            "status",
            "content_eligibility",
            "freshness_reason",
            "event_date_local",
            "score_display",
            "winner_team_name",
            "loser_team_name",
            "headline",
            "event_id",
            "source_id",
            "source_url",
        ],
    )
    write_svg(work_dir / "operator" / "assets" / "brand_logos" / "new-york-liberty.svg", "New York Liberty")
    write_svg(work_dir / "operator" / "assets" / "brand_logos" / "las-vegas-aces.svg", "Las Vegas Aces")

    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    env["HSD_FINAL_SCORE_STORIES_NETWORK"] = "0"
    env["HSD_FINAL_SCORE_STORIES_POLICY"] = str(policy)
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["output_scope"] == "run_scoped"
    assert payload["final_score_story_status"] == "ready_with_review"
    assert (run_dir / "ig_story_results_queue.csv").exists()
    assert (run_dir / "ig_story_results_frames.md").exists()
    assert (run_dir / "final_score_story_guard_report.json").exists()
    assert (run_dir / "ig_story_results_upload_pack" / "last-night-in-the-w" / "00_PROMPT_TO_PASTE.md").exists()
    assert any((run_dir / "ig_story_results_upload_pack_zips").glob("*.zip"))
    assert not (work_dir / "ig_story_results_queue.csv").exists()
    assert not (work_dir / "ig_story_results_upload_pack_zips").exists()
    guard = json.loads((run_dir / "final_score_story_guard_report.json").read_text(encoding="utf-8"))
    assert guard["output_scope"] == "run_scoped"
    assert guard["games_selected"] == 1
    assert guard["logos_missing"] == []


def test_final_score_stories_preserve_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    env = os.environ.copy()
    env["HSD_FINAL_SCORE_STORIES_NETWORK"] = "0"
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["output_scope"] == "legacy_root"
    assert (work_dir / "ig_story_results_queue.csv").exists()
    assert (work_dir / "final_score_story_guard_report.json").exists()
    assert (work_dir / "ig_story_results_upload_pack").exists()
