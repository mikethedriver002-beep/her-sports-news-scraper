from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts import download_hsd_review_only_quarantine_candidate_v1 as module


FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "download_approved",
    "quarantine_target_hint",
    "review_only",
    "publish_ready",
]


def intake_row(**overrides: str) -> dict[str, str]:
    row = {
        "candidate_queue_id": "APQ001",
        "candidate_photo_url": "https://fever.wnba.com/news/source-page",
        "evidence_url": "https://fever.wnba.com/news/source-page",
        "evidence_summary": "Official source page.",
        "identity_anchor_url": "https://www.wnba.com/player/1642286/caitlin-clark",
        "source_url": "https://fever.wnba.com/news/source-page",
        "entity_id": "wnba:caitlin-clark",
        "rights_class": "official_review_needed",
        "identity_confidence": "confirmed_official",
        "intended_review_only_use": "review_only_action_photo_candidate_quarantine_decision_prep",
        "notes": "Review-only.",
        "operator_verify_required": "yes",
        "manual_reviewer": "Mike",
        "manual_review_status": "ready_for_human_download_decision",
        "manual_next_action": "Human requested quarantine-only download.",
        "download_approved": "yes",
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/operator_fill_required.jpg",
        "review_only": "true",
        "publish_ready": "false",
    }
    row.update(overrides)
    return row


def write_intake(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def fake_fetcher(url: str, accept: str, max_bytes: int) -> module.FetchedBytes:
    if "source-page" in url:
        html = b'<html><head><meta property="og:image" content="/media/apq001-lead.jpg"></head></html>'
        return module.FetchedBytes(url="https://fever.wnba.com/news/source-page", content_type="text/html", body=html)
    return module.FetchedBytes(url=url, content_type="image/jpeg", body=b"fake-jpeg-bytes")


def test_dry_run_requires_human_intake_and_writes_review_only_manifest(tmp_path: Path) -> None:
    intake = tmp_path / "intake.csv"
    manifest = tmp_path / "manifest.json"
    report = tmp_path / "report.md"
    write_intake(intake, [intake_row()])

    payload = module.download_candidate(
        candidate_id="APQ001",
        intake_csv=intake,
        manifest_path=manifest,
        report_path=report,
        dry_run=True,
        overwrite=False,
        fetcher=fake_fetcher,
    )

    assert payload["status"] == "dry_run_ok"
    assert payload["quarantine_path"] == "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
    assert payload["review_only"] is True
    assert payload["publish_ready"] is False
    assert payload["approval_state_change"] is False
    assert payload["approved_marker_writes"] is False
    assert json.loads(manifest.read_text(encoding="utf-8"))["sha256"]
    assert "does not approve the asset" in report.read_text(encoding="utf-8")


def test_blocks_rows_without_download_permission(tmp_path: Path) -> None:
    intake = tmp_path / "intake.csv"
    write_intake(intake, [intake_row(download_approved="no")])

    with pytest.raises(module.DownloadBlocked, match="download_approved is not yes"):
        module.download_candidate(
            candidate_id="APQ001",
            intake_csv=intake,
            manifest_path=tmp_path / "manifest.json",
            report_path=tmp_path / "report.md",
            dry_run=True,
            overwrite=False,
            fetcher=fake_fetcher,
        )


def test_blocks_non_quarantine_destinations(tmp_path: Path) -> None:
    intake = tmp_path / "intake.csv"
    write_intake(intake, [intake_row(quarantine_target_hint="assets/leagues/wnba/logo.png")])

    with pytest.raises(module.DownloadBlocked, match="Quarantine target must stay under"):
        module.download_candidate(
            candidate_id="APQ001",
            intake_csv=intake,
            manifest_path=tmp_path / "manifest.json",
            report_path=tmp_path / "report.md",
            dry_run=True,
            overwrite=False,
            fetcher=fake_fetcher,
        )


def test_blocks_missing_required_metadata(tmp_path: Path) -> None:
    intake = tmp_path / "intake.csv"
    write_intake(intake, [intake_row(identity_confidence="")])

    with pytest.raises(module.DownloadBlocked, match="Missing required quarantine download fields"):
        module.download_candidate(
            candidate_id="APQ001",
            intake_csv=intake,
            manifest_path=tmp_path / "manifest.json",
            report_path=tmp_path / "report.md",
            dry_run=True,
            overwrite=False,
            fetcher=fake_fetcher,
        )
