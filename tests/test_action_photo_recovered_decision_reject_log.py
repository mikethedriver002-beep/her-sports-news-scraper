from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_recovered_decision_reject_log_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_recovered_decision_reject_log_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_manual_rejects(path: Path, *, download_approved: str = "no") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_id",
        "entity_id",
        "identity_read",
        "image_type",
        "face_visibility",
        "body_margin_4x5",
        "text_overlay_space",
        "visual_strength",
        "decision",
        "notes",
        "review_only",
        "download_approved",
        "asset_downloads",
        "approval_state_change",
        "publish_ready",
        "publishing",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "candidate_id": "APCS007",
                "entity_id": "wnba_indiana_fever_aliyah_boston",
                "identity_read": "likely",
                "image_type": "near_solo_action",
                "face_visibility": "usable",
                "body_margin_4x5": "weak",
                "text_overlay_space": "weak",
                "visual_strength": "weak",
                "decision": "reject_bad_crop",
                "notes": "Horizontal frame lacks vertical depth.",
                "review_only": "true",
                "download_approved": download_approved,
                "asset_downloads": "false",
                "approval_state_change": "none",
                "publish_ready": "false",
                "publishing": "false",
            }
        )


def test_recovered_decision_reject_log_closes_rejected_rows(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "manual_rejects.csv"
    output_dir = tmp_path / "out"
    write_manual_rejects(input_csv)

    manifest = module.build_packet(input_csv=input_csv, output_dir=output_dir, head_commit="abc123")

    rows = read_csv(output_dir / "recovered_decision_reject_log.csv")
    invalid = read_csv(output_dir / "invalid_recovered_decision_reject_rows.csv")
    report = (output_dir / "recovered_decision_reject_log_report.md").read_text(encoding="utf-8")
    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "recovered_decision_reject_log_ready"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["rejected_rows"] == 1
    assert manifest_json["invalid_rows"] == 0
    assert manifest_json["closed_candidate_ids"] == ["APCS007"]
    assert manifest_json["download_approved_default"] == "no"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert rows[0]["candidate_id"] == "APCS007"
    assert rows[0]["manual_next_action"] == "closed_rejected_do_not_download_or_formal_intake"
    assert rows[0]["reject_category"] == "reject_bad_crop_or_layout_fit"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["approval_state_change"] == "none"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["publishing"] == "false"
    assert invalid == []
    assert "does not download" in report
    assert "download_approved=no" in report


def test_recovered_decision_reject_log_blocks_truthy_downloads(tmp_path: Path) -> None:
    module = load_module()
    input_csv = tmp_path / "manual_rejects.csv"
    output_dir = tmp_path / "out"
    write_manual_rejects(input_csv, download_approved="yes")

    manifest = module.build_packet(input_csv=input_csv, output_dir=output_dir, head_commit="abc123")
    rows = read_csv(output_dir / "recovered_decision_reject_log.csv")
    invalid = read_csv(output_dir / "invalid_recovered_decision_reject_rows.csv")

    assert manifest["rejected_rows"] == 0
    assert rows == []
    assert invalid[0]["validation_issues"] == "download_approved_must_remain_no"
