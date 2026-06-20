from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def make_fixture_root(tmp_path: Path) -> Path:
    root = tmp_path
    render_dir = root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/renders/ig_feed"
    render_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1080, 1350), (10, 10, 14))
    img.save(render_dir / "candidate.png")
    report = {
        "status": "passed_near_post_ready_setup",
        "rows": [
            {
                "item_id": "fixture::ig_feed::a",
                "template_id": "hsd_game_recap_final_score_a",
                "platform": "ig_feed",
                "variant": "A",
                "module_mode": "logos_only",
                "headline": "Fixture Final",
                "output_path": "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/renders/ig_feed/candidate.png",
                "width": 1080,
                "height": 1350,
                "near_post_ready_candidate": "true",
                "fixture_only_player_asset": "false",
                "placeholder_layer_count": "0",
                "zone_overflow_count": "0",
                "team_logo_count": "2",
                "team_logo_modes": "approved_logo;approved_logo",
                "player_assets_used": "0",
                "player_names": "",
                "player_asset_kind": "",
                "mask_compliance_status": "passed_mask_compliance",
                "outside_changed_ratio": "0.003",
                "inside_changed_ratio": "0.22",
                "notes": "fixture",
                "reasons": "",
            }
        ],
    }
    (root / "near_post_ready_v4_report.json").write_text(json.dumps(report), encoding="utf-8")
    fidelity = {"rows": [{"item_id": "fixture::ig_feed::a", "overall_score": 0.94}]}
    (root / "template_fidelity_v4_report.json").write_text(json.dumps(fidelity), encoding="utf-8")
    return root


def test_prepare_visual_approval_packet(tmp_path: Path) -> None:
    root = make_fixture_root(tmp_path)
    subprocess.run([sys.executable, "scripts/prepare_hsd_visual_approval_packet_v4.py", "--root", str(root), "--strict"], check=True)
    approval = root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/approval"
    assert (approval / "visual_approval_candidates_v4.csv").exists()
    assert (approval / "visual_approval_packet_v4.md").exists()
    assert (approval / "visual_approval_contact_sheet_v4.jpg").exists()
    report = json.loads((approval / "visual_approval_packet_v4_report.json").read_text())
    assert report["status"] == "visual_approval_packet_ready"
    assert report["approval_candidates"] == 1


def test_validate_without_decisions_waits_for_human_approval(tmp_path: Path) -> None:
    root = make_fixture_root(tmp_path)
    subprocess.run([sys.executable, "scripts/prepare_hsd_visual_approval_packet_v4.py", "--root", str(root), "--strict"], check=True)
    subprocess.run([sys.executable, "scripts/validate_hsd_visual_approval_v4.py", "--root", str(root), "--strict"], check=True)
    report = json.loads((root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/approval/visual_approval_validation_v4_report.json").read_text())
    assert report["status"] == "waiting_for_human_visual_approval"
    assert report["production_cutover_allowed"] is False


def test_validate_approved_decision_allows_limited_handoff(tmp_path: Path) -> None:
    root = make_fixture_root(tmp_path)
    subprocess.run([sys.executable, "scripts/prepare_hsd_visual_approval_packet_v4.py", "--root", str(root), "--strict"], check=True)
    approval = root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/approval"
    candidates = list(csv.DictReader((approval / "visual_approval_candidates_v4.csv").open()))
    row = candidates[0]
    decisions = root / "config/graphics/v4/approval/visual_approval_decisions_v4.csv"
    write_csv(decisions, [{
        "approval_id": row["approval_id"],
        "decision": "approved",
        "reviewer": "test",
        "reviewed_at": "2026-06-20T00:00:00Z",
        "reason": "fixture test approval",
        "render_sha256": row["render_sha256"],
    }], ["approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"])
    subprocess.run([sys.executable, "scripts/validate_hsd_visual_approval_v4.py", "--root", str(root), "--strict"], check=True)
    report = json.loads((approval / "visual_approval_validation_v4_report.json").read_text())
    assert report["status"] == "visual_approval_validated_with_approved_assets"
    assert report["approved_count"] == 1
    assert report["limited_operator_handoff_allowed"] is True
    assert report["production_cutover_allowed"] is False


def test_fixture_only_candidate_cannot_be_approved(tmp_path: Path) -> None:
    root = make_fixture_root(tmp_path)
    data = json.loads((root / "near_post_ready_v4_report.json").read_text())
    data["rows"][0]["fixture_only_player_asset"] = "true"
    (root / "near_post_ready_v4_report.json").write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/prepare_hsd_visual_approval_packet_v4.py", "--root", str(root), "--strict"], check=False)
    assert result.returncode == 2
    approval = root / "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/approval"
    candidates = list(csv.DictReader((approval / "visual_approval_candidates_v4.csv").open()))
    assert candidates[0]["approval_status"] == "review_only_fixture_player"
