from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple


ROOT = Path("data/asset_registry/womens_soccer")
CONTACT_SHEET = ROOT / "womens_soccer_logo_contact_sheet.csv"
INTAKE = ROOT / "womens_soccer_logo_review_intake.csv"
REPORT_JSON = ROOT / "womens_soccer_logo_source_review_intake_prepare_report.json"
REPORT_MD = ROOT / "womens_soccer_logo_source_review_intake_prepare_report.md"

HOLD_DECISION = "hold_for_more_evidence"
REGISTRY_ACTION = "hold_no_registry_state_change_until_local_logo_asset_exists"
APPROVAL_SCOPE = "review_only_renderer_womens_soccer_logo_trust_manual_intake"
GUARDRAIL_FALSE_FIELDS = [
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

INTAKE_FIELDS = [
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


def clean(value: Any) -> str:
    return str(value or "").strip()


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


def row_key(row: Mapping[str, str]) -> tuple[str, str, str]:
    return clean(row.get("scope_id")), clean(row.get("entity_type")), clean(row.get("entity_id"))


def selected(row: Mapping[str, str], groups: set[str], scopes: set[str], leagues: set[str]) -> bool:
    if groups:
        # Priority groups are not stored in the contact sheet. Use the stable league/scope ids.
        row_group_keys = {
            clean(row.get("scope_id")),
            clean(row.get("league_id")),
            f"{clean(row.get('scope_id'))}:{clean(row.get('league_id'))}",
        }
        return bool(groups & row_group_keys)
    if scopes and clean(row.get("scope_id")) not in scopes:
        return False
    if leagues and clean(row.get("league_id")) not in leagues:
        return False
    return True


def copy_contact_fields(row: Mapping[str, str], prior: Mapping[str, str] | None = None) -> Dict[str, str]:
    prior = prior or {}
    output = {field: clean(row.get(field)) for field in INTAKE_FIELDS}
    for field in ["operator_decision", "source_reviewed", "identity_match", "source_url_to_record", "registry_action", "operator_notes", "reviewed_by", "reviewed_at_local"]:
        output[field] = clean(prior.get(field))
    output["approval_scope"] = APPROVAL_SCOPE
    for field in GUARDRAIL_FALSE_FIELDS:
        output[field] = "false"
    return output


def prepare_rows(
    contact_rows: List[Dict[str, str]],
    prior_rows: List[Dict[str, str]],
    *,
    groups: set[str],
    scopes: set[str],
    leagues: set[str],
    reviewed_by: str,
    reviewed_at_local: str,
    overwrite: bool,
    create_dirs: bool,
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    prior_by_key = {row_key(row): row for row in prior_rows}
    prepared: List[Dict[str, str]] = []
    changed: List[Dict[str, str]] = []
    dirs_created = 0
    dirs_seen: set[Path] = set()

    for row in contact_rows:
        prior = prior_by_key.get(row_key(row))
        output = copy_contact_fields(row, prior)
        should_prepare = selected(row, groups, scopes, leagues)
        already_reviewed = clean(output.get("source_reviewed")).lower() == "yes" and clean(output.get("identity_match")).lower() == "yes"
        if should_prepare and (overwrite or not already_reviewed):
            output.update(
                {
                    "operator_decision": HOLD_DECISION,
                    "source_reviewed": "yes",
                    "identity_match": "yes",
                    "source_url_to_record": clean(row.get("official_source_candidate")) or clean(row.get("current_source_url")),
                    "registry_action": REGISTRY_ACTION,
                    "operator_notes": "Source and identity prefilled for human source-review sweep; local logo asset still required before approval.",
                    "reviewed_by": reviewed_by,
                    "reviewed_at_local": reviewed_at_local,
                }
            )
            changed.append({"scope_id": output["scope_id"], "league_id": output["league_id"], "entity_type": output["entity_type"], "entity_id": output["entity_id"], "display_name": output["display_name"]})
        if create_dirs and clean(row.get("local_logo_path")):
            target_dir = Path(clean(row.get("local_logo_path"))).parent
            if target_dir not in dirs_seen:
                existed = target_dir.exists()
                target_dir.mkdir(parents=True, exist_ok=True)
                if not existed:
                    dirs_created += 1
                dirs_seen.add(target_dir)
        prepared.append(output)

    report = {
        "version": "hsd-womens-soccer-logo-source-review-intake-prepare-v1",
        "generated_at_local": reviewed_at_local,
        "contact_rows": len(contact_rows),
        "intake_rows": len(prepared),
        "prepared_rows": len(changed),
        "created_local_logo_directories": dirs_created,
        "operator_decision": HOLD_DECISION,
        "registry_action": REGISTRY_ACTION,
        "approval_state_changed": False,
        "asset_files_created": False,
        "guardrails": {
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
            "asset_downloads": False,
        },
        "prepared": changed,
    }
    return prepared, report


def write_report(report: Mapping[str, Any]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Women's Soccer Logo Source Review Intake Prepare Report",
        "",
        f"Generated local: `{report['generated_at_local']}`",
        "",
        "## Counts",
        "",
        f"- contact rows: `{report['contact_rows']}`",
        f"- intake rows: `{report['intake_rows']}`",
        f"- prepared rows: `{report['prepared_rows']}`",
        f"- created local logo directories: `{report['created_local_logo_directories']}`",
        "",
        "## Guardrails",
        "",
        "- Approval state changed: `false`",
        "- Asset files created: `false`",
        "- Guardrail fields remain false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, `asset_downloads`",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prefill women soccer logo source-review intake rows without approval-state changes.")
    parser.add_argument("--scope", action="append", default=[], help="Scope id to prepare, such as nwsl or europe_top_flight. Repeatable.")
    parser.add_argument("--league", action="append", default=[], help="League id to prepare. Repeatable.")
    parser.add_argument("--group", action="append", default=[], help="Alias for scope/league group selection. Repeatable.")
    parser.add_argument("--reviewed-by", default="Mike source-review sweep", help="Reviewer text to write into reviewed_by.")
    parser.add_argument("--reviewed-at-local", default=datetime.now().strftime("%Y-%m-%d %H:%M local"), help="Local review timestamp text.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing source_reviewed/identity_match yes rows.")
    parser.add_argument("--create-dirs", action="store_true", help="Create missing parent directories for sanctioned local logo paths.")
    args = parser.parse_args()

    contact_rows, _ = read_csv(CONTACT_SHEET)
    prior_rows, _ = read_csv(INTAKE)
    prepared, report = prepare_rows(
        contact_rows,
        prior_rows,
        groups={clean(value) for value in args.group if clean(value)},
        scopes={clean(value) for value in args.scope if clean(value)},
        leagues={clean(value) for value in args.league if clean(value)},
        reviewed_by=args.reviewed_by,
        reviewed_at_local=args.reviewed_at_local,
        overwrite=args.overwrite,
        create_dirs=args.create_dirs,
    )
    write_csv(INTAKE, prepared, INTAKE_FIELDS)
    write_report(report)
    print(json.dumps({key: report[key] for key in ["contact_rows", "prepared_rows", "created_local_logo_directories", "approval_state_changed", "asset_files_created"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
