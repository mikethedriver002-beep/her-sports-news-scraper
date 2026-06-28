from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "hsd_review_only_asset_download_policy_v1.json"
DOC_PATH = ROOT / "docs" / "HSD_REVIEW_ONLY_ASSET_DOWNLOAD_POLICY.md"
INTAKE_PATH = ROOT / "operator" / "inbox" / "review_only_asset_download_intake.csv"
QUARANTINE_README = ROOT / "data" / "assets" / "quarantine" / "review_only_candidates" / "README.md"
AGENTS_PATH = ROOT / "AGENTS.md"

REQUIRED_FIELDS = {
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_review_only_asset_download_policy_requires_human_intake_and_quarantine_only() -> None:
    policy = json.loads(read_text(POLICY_PATH))

    assert policy["automatic_asset_downloads_allowed"] is False
    assert policy["human_intake_required"] is True
    assert policy["canonical_intake_path"] == "operator/inbox/review_only_asset_download_intake.csv"
    assert policy["sanctioned_quarantine_dir"] == "data/assets/quarantine/review_only_candidates"
    assert set(policy["required_human_intake_fields"]) >= REQUIRED_FIELDS
    assert policy["download_gate"]["download_approved_value"] == "yes"
    assert policy["download_gate"]["missing_required_metadata_action"] == "block_download"
    assert policy["download_gate"]["non_quarantine_destination_action"] == "block_download"
    assert policy["allowed_destination_roots"] == ["data/assets/quarantine/review_only_candidates"]

    blocked_roots = set(policy["blocked_destination_roots"])
    assert "data/assets/approved" in blocked_roots
    assert "assets/leagues" in blocked_roots
    assert "operator/assets/player_images" in blocked_roots


def test_review_only_asset_download_policy_keeps_download_and_approval_separate() -> None:
    policy = json.loads(read_text(POLICY_PATH))
    approval = policy["approval_separation"]

    assert approval["download_approval_is_asset_approval"] is False
    assert approval["auto_approve_assets"] is False
    assert approval["create_approved_markers"] is False
    assert approval["write_headshot_files"] is False
    assert approval["write_team_logo_files"] is False
    assert approval["move_to_publish_ready_lane"] is False
    assert approval["publish"] is False
    assert approval["auto_publish"] is False


def test_review_only_asset_download_intake_template_has_required_gate_fields() -> None:
    with INTAKE_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert set(reader.fieldnames or []) >= REQUIRED_FIELDS
    assert rows, "Template should keep one non-actionable example row."
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["source_url"].startswith("https://")
    assert rows[0]["rights_class"] == "operator_review_required"
    assert rows[0]["identity_confidence"] == "operator_fill_required"


def test_review_only_asset_download_law_is_visible_to_agents_docs_and_quarantine_readme() -> None:
    agents = read_text(AGENTS_PATH)
    doc = read_text(DOC_PATH)
    readme = read_text(QUARANTINE_README)

    combined = "\n".join([agents, doc, readme])
    assert "download_approved=yes" in combined
    assert "source_url" in combined
    assert "entity_id" in combined
    assert "rights_class" in combined
    assert "identity_confidence" in combined
    assert "intended_review_only_use" in combined
    assert "data/assets/quarantine/review_only_candidates/" in combined
    assert "Download approval is not asset approval" in combined
    assert ".approved" in combined
    assert "publish-ready" in combined
