from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "align_hsd_production_readiness_v1.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("align_hsd_production_readiness_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_phase4b_variant_logo_proof_promotes_copy_backed_review_row(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    report = {
        "version": "v1.0-production-readiness-gate",
        "status": "blocked",
        "publish_gate": "blocked_manual_review_required",
        "blockers": ["no_post_ready_candidates_after_quality_gate"],
        "warnings": [],
        "quality_graphics": {"rows": 1, "post_ready_candidates": 0, "review_only": 1},
        "post_ready_assets": [],
        "review_only_assets": [
            {
                "headline": "Golden State Valkyries beat Dallas Wings",
                "platform": "ig_feed",
                "row_kind": "result",
                "output_path": "outputs/x.png",
                "width": "1080",
                "height": "1350",
                "readiness_status": "review_only",
                "manual_visual_review_required": "Yes",
                "copy_found": "Yes",
                "reasons": "both_team_logos_not_confirmed",
                "notes": "test",
            }
        ],
    }
    module.PROD.write_text(json.dumps(report), encoding="utf-8")
    write_csv(
        module.VARIANTS,
        [
            {
                "package_id": "p1",
                "headline": "Golden State Valkyries beat Dallas Wings",
                "variant": "logos_only",
                "team_assets": "2",
                "player_assets": "0",
                "player_mode": "logos_only_forced",
                "status": "ready",
            }
        ],
        ["package_id", "headline", "variant", "team_assets", "player_assets", "player_mode", "status"],
    )

    assert module.main(["--strict"]) == 0
    updated = json.loads(module.PROD.read_text(encoding="utf-8"))

    assert updated["status"] == "production_review_ready"
    assert updated["blockers"] == []
    assert updated["quality_graphics"]["post_ready_candidates"] == 1
    assert updated["quality_graphics"]["review_only"] == 0
    assert updated["post_ready_assets"][0]["logo_proof_source"] == "variant_manifest_logos_only"
    assert updated["variant_alignment"]["promoted_from_review_only"] == 1


def test_phase4b_without_variant_logo_proof_remains_blocked(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    report = {
        "version": "v1.0-production-readiness-gate",
        "status": "blocked",
        "publish_gate": "blocked_manual_review_required",
        "blockers": ["no_post_ready_candidates_after_quality_gate"],
        "warnings": [],
        "quality_graphics": {"rows": 1, "post_ready_candidates": 0, "review_only": 1},
        "post_ready_assets": [],
        "review_only_assets": [
            {"headline": "New York Liberty beat Chicago Sky", "platform": "ig_feed", "row_kind": "result", "output_path": "outputs/y.png", "width": "1080", "height": "1350", "readiness_status": "review_only", "copy_found": "Yes", "reasons": "both_team_logos_not_confirmed", "notes": "test"}
        ],
    }
    module.PROD.write_text(json.dumps(report), encoding="utf-8")
    write_csv(
        module.VARIANTS,
        [{"package_id": "p1", "headline": "Other Headline", "variant": "logos_only", "team_assets": "2", "player_assets": "0", "player_mode": "logos_only_forced", "status": "ready"}],
        ["package_id", "headline", "variant", "team_assets", "player_assets", "player_mode", "status"],
    )

    assert module.main(["--strict"]) == 2
    updated = json.loads(module.PROD.read_text(encoding="utf-8"))

    assert updated["status"] == "blocked"
    assert "no_post_ready_candidates_after_quality_gate" in updated["blockers"]
    assert updated["quality_graphics"]["post_ready_candidates"] == 0
    assert updated["review_only_assets"][0]["logo_proof_source"] == "missing"


def test_phase4b_workflow_is_wired() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/align_hsd_production_readiness_v1.py --strict" in workflow
    assert "tests/test_phase4b_production_output_alignment.py" in workflow
