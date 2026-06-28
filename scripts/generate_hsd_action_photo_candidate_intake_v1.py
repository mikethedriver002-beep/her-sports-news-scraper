from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-action-photo-candidate-intake-v1-review-only"
ROOT = Path("data/asset_registry/action_photo_candidates")
OUT_CSV = output_path(ROOT / "review_only_action_photo_candidate_intake.csv")
OUT_MD = output_path(ROOT / "review_only_action_photo_candidate_intake.md")
OUT_JSON = output_path(ROOT / "review_only_action_photo_candidate_intake.json")
QUARANTINE_ROOT = "data/assets/quarantine/review_only_candidates"
REQUIRED_DOWNLOAD_FIELDS = [
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
]

FIELDS = [
    "intake_rank",
    "intake_status",
    "sport",
    "league",
    "team",
    "player",
    "event_context",
    "candidate_subject_type",
    "entity_id",
    "source_url",
    "source_domain",
    "source_type",
    "rights_class",
    "identity_confidence",
    "action_photo_relevance",
    "intended_review_only_use",
    "download_approved",
    "download_status",
    "quarantine_folder",
    "quarantine_target_hint",
    "required_if_download_approved",
    "manual_next_action",
    "approval_state_change",
    "approval_status",
    "publish_action",
    "research_prompt_note",
    "research_notes",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")
    return out or "operator_fill_required"


def source_domain(source_url: str) -> str:
    match = re.match(r"https?://([^/]+)", clean(source_url), re.IGNORECASE)
    return match.group(1).lower() if match else ""


def template_rows() -> List[Dict[str, str]]:
    base = {
        "intake_status": "operator_fill_required",
        "sport": "",
        "league": "",
        "team": "",
        "player": "",
        "event_context": "",
        "candidate_subject_type": "action_photo",
        "entity_id": "",
        "source_url": "",
        "source_domain": "",
        "rights_class": "",
        "identity_confidence": "",
        "action_photo_relevance": "",
        "intended_review_only_use": "",
        "download_approved": "no",
        "download_status": "not_requested",
        "quarantine_folder": QUARANTINE_ROOT,
        "required_if_download_approved": "download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use",
        "manual_next_action": "Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review.",
        "approval_state_change": "none",
        "approval_status": "not_approved",
        "publish_action": "none_artifact_only",
        "research_prompt_note": "Collect candidate URLs, source domains, rights class, player identity proof, event context, action relevance, and why useful for future render review; do not download images or claim approval.",
        "research_notes": "",
        "operator_notes": "",
        "reviewed_by": "",
        "reviewed_at_local": "",
        "review_only": "true",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
    }
    source_types = [
        ("official_or_league_public_page", "official/team/league source candidate; still not approval"),
        ("reputable_media_or_wire_lead", "AP/Reuters/Getty/news/public media lead; research-only until reviewed"),
        ("gray_area_public_lead", "gray-area public lead; park for manual review only"),
    ]
    rows: List[Dict[str, str]] = []
    for index, (source_type, note) in enumerate(source_types, start=1):
        row = dict(base)
        row["intake_rank"] = f"AP{index:02d}"
        row["source_type"] = source_type
        row["research_notes"] = note
        row["quarantine_target_hint"] = f"{QUARANTINE_ROOT}/action_photo_candidates/operator_fill_required/{source_type}/operator_fill_required.jpg"
        rows.append(row)
    return rows


def normalize_row(row: Mapping[str, str]) -> Dict[str, str]:
    out = {field: clean(row.get(field)) for field in FIELDS}
    out["download_approved"] = clean(out.get("download_approved")).lower() or "no"
    out["download_status"] = out.get("download_status") or "not_requested"
    out["source_domain"] = out.get("source_domain") or source_domain(out.get("source_url", ""))
    out["quarantine_folder"] = out.get("quarantine_folder") or QUARANTINE_ROOT
    if not out.get("quarantine_target_hint"):
        entity = slug(out.get("entity_id") or out.get("player") or out.get("team") or "operator_fill_required")
        source_type = slug(out.get("source_type") or "source_candidate")
        out["quarantine_target_hint"] = f"{QUARANTINE_ROOT}/action_photo_candidates/{entity}/{source_type}/operator_fill_required.jpg"
    return out


def validate_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen = set()
    for index, raw in enumerate(rows, start=2):
        row = normalize_row(raw)
        key = (
            row.get("sport"),
            row.get("league"),
            row.get("team"),
            row.get("player"),
            row.get("event_context"),
            row.get("source_url"),
        )
        if key in seen and any(key):
            issues.append({"row": str(index), "field": "source_url", "issue": "duplicate_action_photo_candidate_key"})
        seen.add(key)
        if row["download_approved"] == "yes":
            for field in REQUIRED_DOWNLOAD_FIELDS:
                if not row.get(field):
                    issues.append({"row": str(index), "field": field, "issue": "required_when_download_approved_yes"})
            if not row.get("quarantine_target_hint", "").startswith(QUARANTINE_ROOT + "/"):
                issues.append({"row": str(index), "field": "quarantine_target_hint", "issue": "download_target_must_stay_in_quarantine"})
        elif row["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "must_be_no_or_human_yes"})
        for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis", "asset_downloads", "headshot_writes", "approved_marker_writes"]:
            if clean(row.get(field)).lower() == "true":
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_must_remain_false"})
        if row.get("approval_state_change") not in {"", "none"}:
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "generated_intake_must_not_change_approval_state"})
        if row.get("publish_action") not in {"", "none_artifact_only"}:
            issues.append({"row": str(index), "field": "publish_action", "issue": "generated_intake_must_not_publish"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    source_counts: Dict[str, int] = {}
    for row in rows:
        source_counts[clean(row.get("source_type")) or "operator_fill_required"] = source_counts.get(clean(row.get("source_type")) or "operator_fill_required", 0) + 1
    lines = [
        "# Review-Only Action Photo Candidate Intake",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Human-editable intake for future action/moment photo candidates. This packet stores research metadata only. It does not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or create a publish-ready lane.",
        "",
        "## Local Download Law",
        "",
        "- A future download is eligible only when a human-edited row has `download_approved=yes` plus `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` filled.",
        f"- Any future file must land under `{QUARANTINE_ROOT}/`.",
        "- Download approval is not asset approval; separate human visual/identity/rights approval is still required.",
        "- Generated rows default to `download_approved=no` and are not render-ready.",
        "",
        "## Deep Research Paste Note",
        "",
        "Ask ChatGPT Pro or Gemini to collect candidate URLs, source domains, source type, rights class, player/team identity proof, event context, action relevance, and why the moment would help future review renders. Do not ask it to download images, scrape photo files, fill approval fields, or claim publish readiness.",
        "",
        "## Summary",
        "",
        f"- Intake template rows: `{len(rows)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Quarantine root: `{QUARANTINE_ROOT}`",
        "",
        "## Source Types",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(source_counts.items()))
    lines += [
        "",
        "## Board Preview",
        "",
        "| Rank | Source Type | Sport | League | Team | Player | Source URL | Download Approved | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:20]:
        lines.append(
            "| {rank} | {source_type} | {sport} | {league} | {team} | {player} | {source_url} | {approved} | {action} |".format(
                rank=clean(row.get("intake_rank")),
                source_type=clean(row.get("source_type")),
                sport=clean(row.get("sport")),
                league=clean(row.get("league")),
                team=clean(row.get("team")).replace("|", "/"),
                player=clean(row.get("player")).replace("|", "/"),
                source_url=clean(row.get("source_url")).replace("|", "%7C"),
                approved=clean(row.get("download_approved")),
                action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    rows = [normalize_row(row) for row in template_rows()]
    issues = validate_rows(rows)
    write_csv(OUT_CSV, rows, FIELDS)
    write_text(OUT_MD, render_markdown(rows, issues, generated_at))
    write_json(
        OUT_JSON,
        {
            "version": VERSION,
            "status": "action_photo_candidate_intake_ready" if not issues else "action_photo_candidate_intake_has_validation_issues",
            "generated_at_utc": generated_at,
            "intake_rows": len(rows),
            "download_approved_yes_rows": sum(1 for row in rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in rows if not clean(row.get("source_url"))),
            "quarantine_root": QUARANTINE_ROOT,
            "required_download_fields": REQUIRED_DOWNLOAD_FIELDS,
            "validation_issue_count": len(issues),
            "validation_issues": issues,
            "worksheet_md": OUT_MD.as_posix(),
            "worksheet_csv": OUT_CSV.as_posix(),
            "review_only": True,
            "approval_state_change": False,
            "candidate_state_change": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    print(json.dumps({"version": VERSION, "status": "ok", "intake_rows": len(rows), "validation_issue_count": len(issues), "csv": OUT_CSV.as_posix()}, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
