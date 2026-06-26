from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

ROOT = Path("data/asset_registry/wnba")
INTAKE = ROOT / "wnba_athlete_photo_review_intake.csv"
ATHLETES = ROOT / "athletes.csv"
ATHLETE_IMAGES = ROOT / "athlete_images.csv"
APPROVED_ASSETS = ROOT / "athlete_image_approved_assets.csv"
MATCH_REVIEW = ROOT / "athlete_image_match_review.csv"
REPORT_JSON = ROOT / "wnba_athlete_photo_review_intake_apply_report.json"
REPORT_MD = ROOT / "wnba_athlete_photo_review_intake_apply_report.md"

APPROVE_DECISION = "approve_for_review_only_renderer_use"
REVISE_DECISION = "revise_asset"
DECISION_SOURCE = "human_reviewed_wnba_athlete_photo_contact_sheet"
REVIEW_ONLY_POLICY = "manual_intake_only_no_downloads_no_file_movement_no_publish_ready_lane"
GUARDRAIL_FIELDS = [
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def truthy_yes(value: Any) -> bool:
    return clean(value).lower() in {"yes", "y", "true", "1"}


def false_flag(value: Any) -> bool:
    return clean(value).lower() in {"false", "0", "no", "n", ""}


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def rows_by_athlete(rows: Iterable[Mapping[str, str]]) -> Dict[str, Mapping[str, str]]:
    return {clean(row.get("athlete_id")): row for row in rows if clean(row.get("athlete_id"))}


def approved_asset_key(row: Mapping[str, str]) -> Tuple[str, str]:
    return clean(row.get("athlete_id")), clean(row.get("approved_file"))


def image_key(row: Mapping[str, str]) -> Tuple[str, str]:
    return clean(row.get("athlete_id")), clean(row.get("image_type"))


def approved_intake_rows(rows: Iterable[Mapping[str, str]]) -> List[Mapping[str, str]]:
    return [
        row
        for row in rows
        if clean(row.get("operator_decision")) == APPROVE_DECISION
    ]


def held_intake_rows(rows: Iterable[Mapping[str, str]]) -> List[Mapping[str, str]]:
    return [
        row
        for row in rows
        if clean(row.get("operator_decision")) == REVISE_DECISION
    ]


def explicit_approval_ready(row: Mapping[str, str]) -> tuple[bool, List[str]]:
    problems: List[str] = []
    if clean(row.get("operator_decision")) != APPROVE_DECISION:
        problems.append("operator_decision_not_approve")
    for field in ["identity_verified", "source_reviewed", "local_file_reviewed", "provider_player_id_verified"]:
        if not truthy_yes(row.get(field)):
            problems.append(f"{field}_not_yes")
    for field in GUARDRAIL_FIELDS:
        if not false_flag(row.get(field)):
            problems.append(f"{field}_must_remain_false")
    if not clean(row.get("source_url_to_record")):
        problems.append("source_url_to_record_missing")
    if not clean(row.get("provider_player_id")):
        problems.append("provider_player_id_missing")
    return not problems, problems


def update_marker(marker_path: Path, intake_row: Mapping[str, str], applied_at_utc: str) -> tuple[bool, str]:
    if not marker_path.exists():
        return False, "approved_marker_missing_no_marker_created"
    payload = read_json(marker_path)
    if not payload:
        return False, "approved_marker_unreadable_no_marker_rewritten"
    payload.update(
        {
            "approved_at_utc": applied_at_utc,
            "provider_player_id": clean(intake_row.get("provider_player_id")),
            "source_file": clean(intake_row.get("source_url_to_record")),
            "decision_source": DECISION_SOURCE,
            "operator_decision": APPROVE_DECISION,
            "human_reviewed_by": clean(intake_row.get("reviewed_by")),
            "human_reviewed_at_local": clean(intake_row.get("reviewed_at_local")),
            "human_intake_file": INTAKE.as_posix(),
            "approval_scope": clean(intake_row.get("approval_scope")),
            "review_only_policy": REVIEW_ONLY_POLICY,
        }
    )
    write_json(marker_path, payload)
    return True, "marker_metadata_updated"


def apply_intake(
    intake_rows: List[Dict[str, str]],
    athlete_rows: List[Dict[str, str]],
    image_rows: List[Dict[str, str]],
    approved_rows: List[Dict[str, str]],
    match_review_rows: List[Dict[str, str]] | None = None,
    *,
    applied_at_utc: str,
) -> Dict[str, Any]:
    athletes = rows_by_athlete(athlete_rows)
    images = {image_key(row): row for row in image_rows}
    approved = {approved_asset_key(row): row for row in approved_rows}
    match_reviews = rows_by_athlete(match_review_rows or [])

    applied: List[Dict[str, str]] = []
    failed: List[Dict[str, str]] = []
    held: List[Dict[str, str]] = []

    for row in approved_intake_rows(intake_rows):
        athlete_id = clean(row.get("athlete_id"))
        local_path = clean(row.get("local_headshot_path"))
        ready, problems = explicit_approval_ready(row)
        approved_row = approved.get((athlete_id, local_path))
        marker_path = Path(clean(row.get("approved_marker_path")) or f"{local_path}.approved")
        if not approved_row:
            problems.append("approved_assets_registry_row_missing")
        if ready and approved_row:
            athlete = athletes.get(athlete_id)
            image = images.get((athlete_id, "headshot"))
            if athlete:
                athlete["provider_player_id"] = clean(row.get("provider_player_id"))
                athlete["source_url"] = clean(row.get("source_url_to_record"))
                athlete["last_verified_utc"] = applied_at_utc
                athlete["notes"] = "human_sweep_review_only_source_verified"
            if image:
                image["provider_player_id"] = clean(row.get("provider_player_id"))
                image["source_note"] = "human_sweep_review_only_source_verified"
                image["last_verified_utc"] = applied_at_utc
            review = match_reviews.get(athlete_id)
            if review:
                review["provider_player_id"] = clean(row.get("provider_player_id"))
                review["image_url"] = clean(row.get("official_roster_photo_candidate_url")) or clean(row.get("source_url_to_record"))
                review["match_method"] = "human_verified_contact_sheet_review"
                review["confidence"] = "1.00"
                review["status"] = "human_verified_review_only"
                review["notes"] = (
                    "closed_by_human_athlete_photo_contact_sheet_sweep; "
                    "review_only_renderer_use; no_downloads_no_file_movement_no_publish_ready_lane"
                )
            approved_row["provider_player_id"] = clean(row.get("provider_player_id"))
            approved_row["source_file"] = clean(row.get("source_url_to_record"))
            approved_row["approved_at_utc"] = applied_at_utc
            approved_row["decision_source"] = DECISION_SOURCE
            marker_updated, marker_status = update_marker(marker_path, row, applied_at_utc)
            if marker_updated:
                applied.append(
                    {
                        "athlete_id": athlete_id,
                        "athlete_name": clean(row.get("athlete_name")),
                        "team_id": clean(row.get("team_id")),
                        "provider_player_id": clean(row.get("provider_player_id")),
                        "source_url_to_record": clean(row.get("source_url_to_record")),
                        "status": "applied_review_only_metadata",
                        "marker_status": marker_status,
                    }
                )
            else:
                failed.append(
                    {
                        "athlete_id": athlete_id,
                        "athlete_name": clean(row.get("athlete_name")),
                        "team_id": clean(row.get("team_id")),
                        "status": marker_status,
                    }
                )
        else:
            failed.append(
                {
                    "athlete_id": athlete_id,
                    "athlete_name": clean(row.get("athlete_name")),
                    "team_id": clean(row.get("team_id")),
                    "status": "|".join(problems),
                }
            )

    for row in held_intake_rows(intake_rows):
        held.append(
            {
                "athlete_id": clean(row.get("athlete_id")),
                "athlete_name": clean(row.get("athlete_name")),
                "team_id": clean(row.get("team_id")),
                "operator_decision": REVISE_DECISION,
                "registry_action": clean(row.get("registry_action")),
                "source_url_to_record": clean(row.get("source_url_to_record")),
                "status": "held_no_registry_metadata_change",
            }
        )

    return {
        "version": "hsd-wnba-athlete-photo-review-intake-apply-v1",
        "generated_at_utc": applied_at_utc,
        "review_only": True,
        "policy": REVIEW_ONLY_POLICY,
        "intake_rows": len(intake_rows),
        "approved_intake_rows": len(approved_intake_rows(intake_rows)),
        "revise_asset_rows": len(held),
        "applied_review_only_metadata": len(applied),
        "failed_rows": len(failed),
        "applied_rows": applied,
        "held_rows": held,
        "failed": failed,
        "guardrails": {
            "paid_apis": False,
            "asset_downloads": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
        },
    }


def write_report_md(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# WNBA Athlete Photo Review Intake Apply Report",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        "",
        "## Policy",
        "",
        "- Review-only metadata application from the human-edited WNBA athlete photo intake CSV.",
        "- No athlete image was downloaded, copied, moved, published, or made publish-ready.",
        "- Existing approved marker sidecars were updated only for rows with explicit approve decisions and verification fields set to yes.",
        "",
        "## Counts",
        "",
        f"- intake rows: {report.get('intake_rows')}",
        f"- approved intake rows: {report.get('approved_intake_rows')}",
        f"- applied review-only metadata: {report.get('applied_review_only_metadata')}",
        f"- revise_asset rows held: {report.get('revise_asset_rows')}",
        f"- failed rows: {report.get('failed_rows')}",
        "",
        "## Held Revise Rows",
        "",
    ]
    held = report.get("held_rows") or []
    if held:
        for row in held:
            lines.append(
                f"- {row.get('athlete_name')} | {row.get('team_id')} | action: {row.get('registry_action')} | source candidate: {row.get('source_url_to_record')}"
            )
    else:
        lines.append("- None")
    if report.get("failed"):
        lines += ["", "## Failed Rows", ""]
        for row in report.get("failed") or []:
            lines.append(f"- {row.get('athlete_name') or row.get('athlete_id')} | {row.get('status')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    intake_rows, _ = read_csv(INTAKE)
    athlete_rows, athlete_fields = read_csv(ATHLETES)
    image_rows, image_fields = read_csv(ATHLETE_IMAGES)
    approved_rows, approved_fields = read_csv(APPROVED_ASSETS)
    match_review_rows, match_review_fields = read_csv(MATCH_REVIEW)

    report = apply_intake(
        intake_rows,
        athlete_rows,
        image_rows,
        approved_rows,
        match_review_rows,
        applied_at_utc=now_iso(),
    )
    if report["failed_rows"]:
        write_json(REPORT_JSON, report)
        write_report_md(REPORT_MD, report)
        raise SystemExit(f"Refusing partial metadata apply; failed_rows={report['failed_rows']}")

    write_csv(ATHLETES, athlete_rows, athlete_fields)
    write_csv(ATHLETE_IMAGES, image_rows, image_fields)
    write_csv(APPROVED_ASSETS, approved_rows, approved_fields)
    write_csv(MATCH_REVIEW, match_review_rows, match_review_fields)
    write_json(REPORT_JSON, report)
    write_report_md(REPORT_MD, report)
    print(json.dumps({key: report[key] for key in ["version", "applied_review_only_metadata", "revise_asset_rows", "failed_rows"]}, indent=2))


if __name__ == "__main__":
    main()
