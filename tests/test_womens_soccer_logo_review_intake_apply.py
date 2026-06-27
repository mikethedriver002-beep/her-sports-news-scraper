from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "apply_hsd_womens_soccer_logo_review_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_hsd_womens_soccer_logo_review_intake_v1", SCRIPT)
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


def make_logo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (120, 120), (25, 90, 140, 255))
    image.save(path)


def test_womens_soccer_logo_review_intake_apply_updates_only_logo_scope(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.ROOT = Path("data/asset_registry/womens_soccer")
    module.CONTACT_SHEET = module.ROOT / "womens_soccer_logo_contact_sheet.csv"
    module.INTAKE = module.ROOT / "womens_soccer_logo_review_intake.csv"
    module.REPORT_JSON = module.ROOT / "womens_soccer_logo_review_intake_apply_report.json"
    module.REPORT_MD = module.ROOT / "womens_soccer_logo_review_intake_apply_report.md"

    logo_path = Path("assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png")
    make_logo(logo_path)
    contact_fields = [
        "scope_id",
        "league_id",
        "league_name",
        "entity_type",
        "entity_id",
        "display_name",
        "country",
        "asset_slot",
        "local_logo_path",
        "logo_image_path",
        "logo_file_exists",
        "current_source_url",
        "official_source_candidate",
        "current_approval_status",
        "manual_review_status",
        "operator_action",
        "allowed_decisions",
        "human_intake_file",
        "review_only",
        "publish_ready",
        "auto_approval",
        "auto_publish",
        "move_files",
        "paid_apis",
        "asset_downloads",
    ]
    intake_fields = [
        "scope_id",
        "league_id",
        "entity_type",
        "entity_id",
        "display_name",
        "local_logo_path",
        "current_source_url",
        "official_source_candidate",
        "current_approval_status",
        "allowed_decisions",
        "operator_decision",
        "source_reviewed",
        "identity_match",
        "source_url_to_record",
        "registry_action",
        "operator_notes",
        "reviewed_by",
        "reviewed_at_local",
        "approval_scope",
        "publish_ready",
        "auto_approval",
        "auto_publish",
        "move_files",
        "paid_apis",
        "asset_downloads",
    ]
    write_csv(
        module.CONTACT_SHEET,
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "country": "US",
                "asset_slot": "primary_logo",
                "local_logo_path": logo_path.as_posix(),
                "logo_image_path": logo_path.as_posix(),
                "logo_file_exists": "true",
                "current_source_url": "https://www.angelcity.com/",
                "official_source_candidate": "https://www.angelcity.com/",
                "current_approval_status": "not_approved",
                "manual_review_status": "review_required",
                "operator_action": "manual_logo_or_mark_review_required",
                "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                "human_intake_file": module.INTAKE.as_posix(),
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        contact_fields,
    )
    write_csv(
        module.INTAKE,
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "local_logo_path": logo_path.as_posix(),
                "current_source_url": "https://www.angelcity.com/",
                "official_source_candidate": "https://www.angelcity.com/",
                "current_approval_status": "not_approved",
                "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                "operator_decision": "approve_for_review_only_renderer_use",
                "source_reviewed": "yes",
                "identity_match": "yes",
                "source_url_to_record": "https://www.angelcity.com/",
                "registry_action": "apply_human_review_only_logo_approval",
                "operator_notes": "Mike approved full contact sheet",
                "reviewed_by": "Mike",
                "reviewed_at_local": "2026-06-27",
                "approval_scope": "review_only_renderer_womens_soccer_logo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        intake_fields,
    )
    write_csv(
        module.ROOT / "nwsl" / "asset_slots.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "asset_slot": "primary_logo",
                "intended_use": "team identity reference",
                "target_path": logo_path.as_posix(),
                "source_url_required": "true",
                "local_file_path": "",
                "file_exists": "false",
                "approval_status": "not_approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": "manual review required",
            }
        ],
        module.ASSET_SLOT_FIELDS,
    )
    write_csv(
        module.ROOT / "nwsl" / "approval_status.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "approval_scope": "team_identity",
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "identity still not approved",
            },
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "approval_scope": "team_logo",
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "manual review required",
            },
        ],
        module.APPROVAL_FIELDS,
    )

    contact_rows = module.read_csv(module.CONTACT_SHEET)[0]
    intake_rows = module.read_csv(module.INTAKE)[0]
    asset_rows = module.read_csv(module.ROOT / "nwsl" / "asset_slots.csv")[0]
    approval_rows = module.read_csv(module.ROOT / "nwsl" / "approval_status.csv")[0]
    report = module.apply_intake(
        contact_rows,
        intake_rows,
        {"nwsl": asset_rows},
        {"nwsl": approval_rows},
        applied_at_utc="2026-06-27T00:00:00+00:00",
    )

    assert report["applied_review_only_metadata"] == 1
    assert report["failed_rows"] == 0
    logo_row = [row for row in approval_rows if row["approval_scope"] == "team_logo"][0]
    identity_row = [row for row in approval_rows if row["approval_scope"] == "team_identity"][0]
    assert logo_row["approval_status"] == "approved"
    assert logo_row["approved_by"] == "Mike"
    assert logo_row["render_enabled"] == "false"
    assert logo_row["publish_ready"] == "false"
    assert identity_row["approval_status"] == "not_approved"
    assert asset_rows[0]["approval_status"] == "approved"
    assert asset_rows[0]["file_exists"] == "true"
    assert asset_rows[0]["render_enabled"] == "false"
    assert asset_rows[0]["publish_ready"] == "false"


def test_womens_soccer_logo_review_intake_apply_preserves_extra_registry_columns(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.ROOT = Path("data/asset_registry/womens_soccer")
    module.CONTACT_SHEET = module.ROOT / "womens_soccer_logo_contact_sheet.csv"
    module.INTAKE = module.ROOT / "womens_soccer_logo_review_intake.csv"
    module.REPORT_JSON = module.ROOT / "womens_soccer_logo_review_intake_apply_report.json"
    module.REPORT_MD = module.ROOT / "womens_soccer_logo_review_intake_apply_report.md"

    logo_path = Path("assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png")
    make_logo(logo_path)
    contact_fields = [
        "scope_id",
        "league_id",
        "entity_type",
        "entity_id",
        "display_name",
        "asset_slot",
        "local_logo_path",
    ]
    intake_fields = [
        "scope_id",
        "league_id",
        "entity_type",
        "entity_id",
        "display_name",
        "local_logo_path",
        "operator_decision",
        "source_reviewed",
        "identity_match",
        "source_url_to_record",
        "reviewed_by",
        "publish_ready",
        "auto_approval",
        "auto_publish",
        "move_files",
        "paid_apis",
        "asset_downloads",
    ]
    write_csv(
        module.CONTACT_SHEET,
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "asset_slot": "primary_logo",
                "local_logo_path": logo_path.as_posix(),
            }
        ],
        contact_fields,
    )
    write_csv(
        module.INTAKE,
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "local_logo_path": logo_path.as_posix(),
                "operator_decision": "approve_for_review_only_renderer_use",
                "source_reviewed": "yes",
                "identity_match": "yes",
                "source_url_to_record": "https://www.angelcity.com/",
                "reviewed_by": "Mike",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        intake_fields,
    )
    write_csv(
        module.ROOT / "nwsl" / "asset_slots.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "asset_slot": "primary_logo",
                "intended_use": "team identity reference",
                "target_path": logo_path.as_posix(),
                "source_url_required": "true",
                "local_file_path": "",
                "file_exists": "false",
                "approval_status": "not_approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": "manual review required",
                "source_review_path": "operator/source/path",
            }
        ],
        module.ASSET_SLOT_FIELDS + ["source_review_path"],
    )
    write_csv(
        module.ROOT / "nwsl" / "approval_status.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "approval_scope": "team_logo",
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "manual review required",
                "source_decision_path": "operator/decision/path",
            }
        ],
        module.APPROVAL_FIELDS + ["source_decision_path"],
    )

    assert module.main() == 0

    asset_rows, asset_fields = module.read_csv(module.ROOT / "nwsl" / "asset_slots.csv")
    approval_rows, approval_fields = module.read_csv(module.ROOT / "nwsl" / "approval_status.csv")
    assert "source_review_path" in asset_fields
    assert "source_decision_path" in approval_fields
    assert asset_rows[0]["source_review_path"] == "operator/source/path"
    assert approval_rows[0]["source_decision_path"] == "operator/decision/path"


def test_womens_soccer_logo_review_intake_apply_rejects_missing_audit_fields(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.ROOT = Path("data/asset_registry/womens_soccer")

    logo_path = Path("assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png")
    make_logo(logo_path)
    contact_row = {
        "scope_id": "nwsl",
        "league_id": "nwsl",
        "league_name": "National Women's Soccer League",
        "entity_type": "team",
        "entity_id": "angel_city_fc",
        "display_name": "Angel City FC",
        "asset_slot": "primary_logo",
        "local_logo_path": logo_path.as_posix(),
    }
    intake_row = {
        "scope_id": "nwsl",
        "league_id": "nwsl",
        "entity_type": "team",
        "entity_id": "angel_city_fc",
        "display_name": "Angel City FC",
        "local_logo_path": logo_path.as_posix(),
        "operator_decision": "approve_for_review_only_renderer_use",
        "source_reviewed": "yes",
        "identity_match": "yes",
        "source_url_to_record": "",
        "reviewed_by": "Mike",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
    }
    asset_row = {
        "entity_type": "team",
        "entity_id": "angel_city_fc",
        "league_id": "nwsl",
        "team_id": "angel_city_fc",
        "asset_slot": "primary_logo",
        "intended_use": "team identity reference",
        "target_path": logo_path.as_posix(),
        "source_url_required": "true",
        "local_file_path": "",
        "file_exists": "false",
        "approval_status": "not_approved",
        "render_enabled": "false",
        "auto_download_allowed": "false",
        "publish_ready": "false",
        "notes": "manual review required",
    }
    approval_row = {
        "entity_type": "team",
        "entity_id": "angel_city_fc",
        "approval_scope": "team_logo",
        "approval_status": "not_approved",
        "approved_by": "",
        "approved_at_utc": "",
        "auto_approval_allowed": "false",
        "render_enabled": "false",
        "publish_ready": "false",
        "notes": "manual review required",
    }

    report = module.apply_intake(
        [contact_row],
        [intake_row],
        {"nwsl": [asset_row]},
        {"nwsl": [approval_row]},
        applied_at_utc="2026-06-27T00:00:00+00:00",
    )

    assert report["applied_review_only_metadata"] == 0
    assert report["failed_rows"] == 1
    assert report["failed"][0]["status"] == "source_url_to_record_missing"
    assert approval_row["approval_status"] == "not_approved"
