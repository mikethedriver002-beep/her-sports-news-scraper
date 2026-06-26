from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_wnba_athlete_identity_resolution_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_wnba_athlete_identity_resolution_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_identity_resolution_groups_audit_issues_into_manual_rows() -> None:
    module = load_module()

    rows = module.summarize_issues([
        {
            "severity": "high",
            "issue_code": "default_approval_requires_identity_recheck",
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "1630993",
            "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
            "evidence": "decision_source=default",
        },
        {
            "severity": "medium",
            "issue_code": "missing_provider_player_id_in_image_registry",
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "1630993",
            "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
            "evidence": "athlete_images.csv provider_player_id is blank",
        },
    ])

    assert len(rows) == 1
    assert rows[0]["athlete_id"] == "new_york_liberty_breanna_stewart"
    assert rows[0]["highest_severity"] == "high"
    assert rows[0]["issue_count"] == "2"
    assert rows[0]["recommended_operator_action"] == "hold_identity_review_required_before_any_photo_renderer_use"
    assert rows[0]["allowed_decisions"] == "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only"
    assert rows[0]["operator_decision"] == ""
    assert rows[0]["copy_target"] == "operator/inbox/wnba_athlete_identity_resolution.csv"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["move_files"] == "false"
    assert rows[0]["paid_apis"] == "false"

    packet_rows = module.review_packet_rows(rows)

    assert len(packet_rows) == 1
    assert packet_rows[0]["identity_review_status"] == "hold_identity_review_required"
    assert packet_rows[0]["review_required"] == "true"
    assert packet_rows[0]["identity_hold"] == "true"
    assert packet_rows[0]["default_approval_present"] == "true"
    assert packet_rows[0]["allowed_decisions"].startswith("hold_identity|")
    assert packet_rows[0]["publish_ready"] == "false"
    assert packet_rows[0]["auto_approval"] == "false"


def test_identity_resolution_main_writes_run_scoped_outputs(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    audit_dir = run_dir / "data" / "asset_registry" / "wnba"
    audit_dir.mkdir(parents=True)
    (audit_dir / "athlete_identity_audit.json").write_text(
        json.dumps(
            {
                "issues": [
                    {
                        "severity": "high",
                        "issue_code": "default_approval_requires_identity_recheck",
                        "athlete_id": "new_york_liberty_breanna_stewart",
                        "display_name": "Breanna Stewart",
                        "team_id": "new_york_liberty",
                        "provider_player_id": "1630993",
                        "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
                        "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
                        "evidence": "decision_source=default",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    module.main()

    base = run_dir / "data" / "asset_registry" / "wnba"
    assert (base / "athlete_identity_resolution_workflow.md").exists()
    assert (base / "athlete_identity_resolution_candidates.csv").exists()
    assert (base / "athlete_identity_review_packet.csv").exists()
    assert (base / "athlete_identity_resolution_template.csv").exists()
    manifest = json.loads((base / "athlete_identity_resolution_manifest.json").read_text(encoding="utf-8"))
    assert manifest["report"]["status"] == "identity_resolution_required"
    assert manifest["report"]["candidate_rows"] == 1
    assert manifest["report"]["identity_hold_rows"] == 1
    assert manifest["report"]["default_approval_rows"] == 1
    assert manifest["review_packet_rows"][0]["identity_hold"] == "true"
    assert manifest["report"]["guardrails"]["auto_approval"] is False
    assert not (tmp_path / "data" / "asset_registry" / "wnba" / "athlete_identity_resolution_template.csv").exists()
