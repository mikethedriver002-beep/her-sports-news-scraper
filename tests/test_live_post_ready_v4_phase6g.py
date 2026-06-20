from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_hsd_live_post_ready_v4.py"
ASSET_SCRIPT = REPO / "scripts" / "prepare_hsd_renderer_v4_live_assets.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v4-phase6g-live-post-ready.yml"
POLICY = REPO / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4.json"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_hsd_live_post_ready_v4", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def seed_root(root: Path, *, fixture: bool, logos: bool, fidelity: float = 0.95, player: bool = False) -> dict:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    write_json(root / module_path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4.json"), policy)
    output = root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/renders/ig_feed/test.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1080, 1350), (10, 10, 10)).save(output)
    item_id = "fixture-event::ig_feed::template" if fixture else "401999999::ig_feed::template"
    item = {
        "item_id": item_id,
        "source_id": "fixture-event" if fixture else "401999999",
        "template_id": "hsd_tonight_in_the_w_a",
        "platform": "ig_feed",
        "variant": "A",
        "module_mode": "player" if player else "watch_point",
        "headline": "Atlanta Dream at Indiana Fever",
        "output_path": output.relative_to(root).as_posix(),
        "width": 1080,
        "height": 1350,
        "team_logo_count": 2 if logos else 0,
        "team_logo_modes": "approved_logo;approved_logo" if logos else "approved_text_fallback;approved_text_fallback",
        "player_assets_used": 1 if player else 0,
        "player_names": "Real Player" if player else "",
        "player_asset_kind": "headshot" if player else "",
        "fixture_only_player_asset": "false",
        "placeholder_layer_count": 0,
        "zone_overflow_count": 0,
        "review_only": "true",
        "near_post_ready_candidate": "true",
        "status": "rendered_near_post_ready_review",
        "notes": "real content",
    }
    write_json(root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json", {"version": "v4.2-phase6e-clean-plate-near-post-ready", "items": [item]})
    write_json(root / "near_post_ready_v4_report.json", {"rows": [{**item, "mask_compliance_status": "passed_mask_compliance"}]})
    write_json(root / "template_fidelity_v4_report.json", {"rows": [{"item_id": item_id, "overall_score": fidelity}]})
    write_json(root / "v4_source_truth_guard.json", {"status": "passed_source_truth_guard", "blockers": []})
    write_json(root / "live_asset_preparation_v4_report.json", {"status": "passed_live_asset_preparation"})
    return item


def module_path(value: str) -> Path:
    return Path(value)


def test_fixture_approvals_cannot_escape_live_lane(tmp_path: Path) -> None:
    module = load_module()
    seed_root(tmp_path, fixture=True, logos=True)
    report = module.evaluate(tmp_path, "fixture_audit")
    assert report["status"] == "passed_fixture_separation_audit"
    assert report["technical_candidate_count"] == 0
    assert report["approved_live_count"] == 0


def test_text_logo_fallback_blocks_live_candidate(tmp_path: Path) -> None:
    module = load_module()
    seed_root(tmp_path, fixture=False, logos=False)
    report = module.evaluate(tmp_path, "live_data")
    assert report["status"] == "blocked_live_post_ready_technical_gate"
    reasons = report["rows"][0]["technical_reasons"]
    assert "insufficient_exact_team_logos" in reasons
    assert "text_or_unapproved_logo_fallback" in reasons


def test_real_live_candidate_waits_for_hash_approval(tmp_path: Path) -> None:
    module = load_module()
    seed_root(tmp_path, fixture=False, logos=True)
    report = module.evaluate(tmp_path, "live_data")
    assert report["status"] == "waiting_for_live_visual_approval"
    assert report["technical_candidate_count"] == 1
    assert report["approved_live_count"] == 0


def test_exact_live_hash_approval_builds_limited_handoff(tmp_path: Path) -> None:
    module = load_module()
    seed_root(tmp_path, fixture=False, logos=True)
    first = module.evaluate(tmp_path, "live_data")
    candidate_path = tmp_path / module.CANDIDATES_CSV
    candidate = list(csv.DictReader(candidate_path.open()))[0]
    decisions = tmp_path / "config/graphics/v4/live_post_ready/live_visual_approval_decisions_v4.csv"
    write_csv(decisions, [{
        "live_approval_id": candidate["live_approval_id"],
        "decision": "approved",
        "reviewer": "HSD Test Reviewer",
        "reviewed_at": "2026-06-20T00:00:00+00:00",
        "reason": "test approval",
        "render_sha256": candidate["render_sha256"],
    }], module.DECISION_FIELDS)
    second = module.evaluate(tmp_path, "live_data")
    assert second["status"] == "live_post_ready_handoff_ready"
    assert second["approved_live_count"] == 1
    assert second["limited_live_operator_handoff_allowed"] is True
    assert second["production_cutover_allowed"] is False
    assert (tmp_path / module.HANDOFF_MANIFEST).exists()


def test_phase6g_contract_and_workflow_wiring() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    asset_script = ASSET_SCRIPT.read_text(encoding="utf-8")
    assert policy["text_logo_fallback_allowed_for_live"] is False
    assert policy["production_cutover_allowed"] is False
    assert "fixture_audit" in workflow and "live_data" in workflow
    assert "prepare_hsd_renderer_v4_live_assets.py" in workflow
    assert "validate_hsd_live_post_ready_v4.py" in workflow
    assert "HSD_LIVE_POST_READY" in script
    assert "fetch_hsd_wnba_logo_sources_v1.py" in asset_script
