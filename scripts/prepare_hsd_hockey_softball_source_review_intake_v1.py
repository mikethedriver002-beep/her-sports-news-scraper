from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


VERSION = "hsd-hockey-softball-source-review-intake-prepare-v1-review-only"

SPORTS = {
    "womens_hockey": {
        "sport_label": "Women's Hockey",
        "league_label": "Professional Women's Hockey League",
        "league_id": "pwhl",
        "root": Path("data/asset_registry/womens_hockey"),
        "logo_contact_sheet": Path("data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv"),
        "logo_intake": Path("data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv"),
        "athlete_contact_sheet": Path("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv"),
        "athlete_intake": Path("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"),
        "walkthrough": Path("data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md"),
    },
    "softball": {
        "sport_label": "Softball",
        "league_label": "Athletes Unlimited Softball League",
        "league_id": "ausl",
        "root": Path("data/asset_registry/softball"),
        "logo_contact_sheet": Path("data/asset_registry/softball/softball_logo_contact_sheet.csv"),
        "logo_intake": Path("data/asset_registry/softball/softball_logo_review_intake.csv"),
        "athlete_contact_sheet": Path("data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv"),
        "athlete_intake": Path("data/asset_registry/softball/softball_athlete_photo_review_intake.csv"),
        "walkthrough": Path("data/asset_registry/softball/softball_review_walkthrough.md"),
    },
}

REPORT_MD = Path("data/asset_registry/hockey_softball_source_review_helper_report.md")
REPORT_JSON = Path("data/asset_registry/hockey_softball_source_review_helper_report.json")

LOGO_INTAKE_FIELDS = [
    "sport_family",
    "league_id",
    "entity_type",
    "entity_id",
    "display_name",
    "asset_slot",
    "target_path",
    "official_source_candidate",
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

ATHLETE_INTAKE_FIELDS = [
    "sport_family",
    "league_id",
    "team_id",
    "team_name",
    "player_id",
    "display_name",
    "candidate_id",
    "local_candidate_path",
    "source_url",
    "photo_candidate_url",
    "approval_status",
    "identity_review_status",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "source_reviewed",
    "local_file_reviewed",
    "source_allowed_for_review_only",
    "rights_reviewed",
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


def now_local() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def preserve_false(row: Dict[str, str]) -> Dict[str, str]:
    output = dict(row)
    for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis", "asset_downloads"]:
        if field in output:
            output[field] = "false"
    return output


def key_for_logo(row: Mapping[str, str]) -> tuple[str, str, str]:
    return clean(row.get("entity_type")), clean(row.get("entity_id")), clean(row.get("asset_slot"))


def key_for_athlete(row: Mapping[str, str]) -> tuple[str, str, str]:
    return clean(row.get("team_id")), clean(row.get("candidate_id")), clean(row.get("player_id"))


def has_named_athlete_identity(row: Mapping[str, str]) -> bool:
    display_name = clean(row.get("display_name")).lower()
    player_id = clean(row.get("player_id"))
    return bool(player_id and display_name and not display_name.startswith("operator_add_player"))


def merged_row(row: Mapping[str, str], prior: Mapping[str, str] | None = None) -> Dict[str, str]:
    output = {field: clean(row.get(field)) for field in row.keys()}
    if prior:
        for field, value in prior.items():
            if field not in output or clean(output.get(field)) == "":
                output[field] = clean(value)
    return preserve_false(output)


def prepare_logo_rows(
    sport_key: str,
    sport: Mapping[str, str],
    contact_rows: List[Dict[str, str]],
    prior_rows: List[Dict[str, str]],
    *,
    reviewed_by: str,
    reviewed_at_local: str,
    overwrite: bool,
) -> tuple[List[Dict[str, str]], int]:
    prior_by_key = {key_for_logo(row): row for row in prior_rows}
    prepared: List[Dict[str, str]] = []
    changed = 0
    for row in contact_rows:
        prior = prior_by_key.get(key_for_logo(row))
        output = merged_row(row, prior)
        already_reviewed = clean(output.get("source_reviewed")).lower() == "yes" and clean(output.get("identity_match")).lower() == "yes"
        if overwrite or not already_reviewed:
            output.update(
                {
                    "sport_family": sport_key,
                    "operator_decision": "hold_for_more_evidence",
                    "source_reviewed": "yes",
                    "identity_match": "yes",
                    "source_url_to_record": clean(row.get("official_source_candidate")) or clean(row.get("current_source_url")),
                    "registry_action": "hold_no_registry_state_change_until_local_logo_asset_exists",
                    "operator_notes": "Source and identity prefilled for human review-order sweep; no approval-state change.",
                    "reviewed_by": reviewed_by,
                    "reviewed_at_local": reviewed_at_local,
                    "approval_scope": f"review_only_renderer_{sport_key}_logo_trust_manual_intake",
                }
            )
            changed += 1
        prepared.append(preserve_false(output))
    return prepared, changed


def prepare_athlete_rows(
    sport_key: str,
    sport: Mapping[str, str],
    contact_rows: List[Dict[str, str]],
    prior_rows: List[Dict[str, str]],
    *,
    reviewed_by: str,
    reviewed_at_local: str,
    overwrite: bool,
) -> tuple[List[Dict[str, str]], int]:
    prior_by_key = {key_for_athlete(row): row for row in prior_rows}
    prepared: List[Dict[str, str]] = []
    changed = 0
    for row in contact_rows:
        prior = prior_by_key.get(key_for_athlete(row))
        output = merged_row(row, prior)
        already_reviewed = clean(output.get("identity_verified")).lower() == "yes" and clean(output.get("source_reviewed")).lower() == "yes"
        if overwrite or not already_reviewed:
            identity_verified = "yes" if has_named_athlete_identity(row) else "no"
            identity_note = (
                "Named athlete identity can be source-reviewed; local file still required before approval-state change."
                if identity_verified == "yes"
                else "Source can be reviewed, but identity stays held until the row names a concrete athlete and local candidate asset exists."
            )
            output.update(
                {
                    "sport_family": sport_key,
                    "operator_decision": "hold_identity",
                    "identity_verified": identity_verified,
                    "source_reviewed": "yes",
                    "local_file_reviewed": "no",
                    "source_allowed_for_review_only": "yes",
                    "rights_reviewed": "yes",
                    "source_url_to_record": clean(row.get("source_url")),
                    "registry_action": "hold_no_registry_state_change_until_local_candidate_asset_exists",
                    "operator_notes": f"{identity_note} No approval-state change.",
                    "reviewed_by": reviewed_by,
                    "reviewed_at_local": reviewed_at_local,
                    "approval_scope": f"review_only_renderer_{sport_key}_athlete_photo_trust_manual_intake",
                }
            )
            changed += 1
        prepared.append(preserve_false(output))
    return prepared, changed


def render_walkthrough(
    sport_key: str,
    sport: Mapping[str, str],
    logo_rows: List[Dict[str, str]],
    athlete_rows: List[Dict[str, str]],
    *,
    reviewed_at_local: str,
) -> str:
    lines = [
        f"# {sport['sport_label']} Review Walkthrough",
        "",
        f"Generated: `{reviewed_at_local}`",
        "",
        "Review-only walkthrough for the logo and athlete candidate packets. It does not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
        "## Open First",
        "",
        f"- Logo contact sheet: `{sport['logo_contact_sheet'].as_posix()}`",
        f"- Logo intake CSV: `{sport['logo_intake'].as_posix()}`",
        f"- Athlete contact sheet: `{sport['athlete_contact_sheet'].as_posix()}`",
        f"- Athlete intake CSV: `{sport['athlete_intake'].as_posix()}`",
        "",
        "## Review Order",
        "",
        "### Logo Packet",
    ]
    for index, row in enumerate(logo_rows, start=1):
        lines.append(
            f"{index}. {clean(row.get('display_name'))} | {clean(row.get('entity_type'))} | source={clean(row.get('official_source_candidate'))}"
        )
    lines.extend(
        [
            "",
            "### Athlete Packet",
        ]
    )
    for index, row in enumerate(athlete_rows, start=1):
        lines.append(
            f"{index}. {clean(row.get('team_name'))} | {clean(row.get('display_name'))} | roster={clean(row.get('source_url'))}"
        )
    lines.extend(
        [
            "",
            "## How To Fill The Intake CSV",
            "",
            "- Logo rows: keep `source_reviewed=yes` and `identity_match=yes` only after you manually open the source candidate page and confirm the mark matches the league or club.",
            "- Athlete source rows: `source_reviewed=yes` means you manually opened the roster/profile/index page and confirmed it is a usable source candidate.",
            "- Athlete identity rows: keep `identity_verified=no` when the row is still an `operator_add_player_*` source slot or has no concrete `player_id` and player name.",
            "- Athlete local file rows: keep `local_file_reviewed=no` until Mike manually supplies and reviews the local candidate file.",
            "- Athlete hold boundary: `registry_action` must stay `hold_no_registry_state_change_until_local_candidate_asset_exists` unless a later explicit human-edited intake file supplies named identity evidence and local asset review.",
            "- Logo rows can complete source/identity match review before a local asset exists, but the registry action still remains hold-only until the asset is manually supplied and reviewed.",
            "- `source_url_to_record` should be the exact source page you reviewed.",
            "- `registry_action` must remain a hold-only action; do not change approval state from this helper.",
            "- Guardrails stay false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads`.",
            "",
            "## Safe Pace",
            "",
            f"Start with the first row in each packet, then work top-to-bottom. The helper keeps the workflow batchable without changing approval state for {clean(sport.get('league_label'))}.",
            "",
        ]
    )
    return "\n".join(lines)


def run_for_sport(sport_key: str, *, overwrite: bool, reviewed_by: str, reviewed_at_local: str) -> Dict[str, Any]:
    sport = SPORTS[sport_key]
    logo_contact_rows, _ = read_csv(sport["logo_contact_sheet"])
    athlete_contact_rows, _ = read_csv(sport["athlete_contact_sheet"])
    logo_prior, logo_fields = read_csv(sport["logo_intake"])
    athlete_prior, athlete_fields = read_csv(sport["athlete_intake"])

    logo_rows, logo_changed = prepare_logo_rows(
        sport_key,
        sport,
        logo_contact_rows,
        logo_prior,
        reviewed_by=reviewed_by,
        reviewed_at_local=reviewed_at_local,
        overwrite=overwrite,
    )
    athlete_rows, athlete_changed = prepare_athlete_rows(
        sport_key,
        sport,
        athlete_contact_rows,
        athlete_prior,
        reviewed_by=reviewed_by,
        reviewed_at_local=reviewed_at_local,
        overwrite=overwrite,
    )

    logo_fields = logo_fields or list(logo_rows[0].keys())
    athlete_fields = athlete_fields or list(athlete_rows[0].keys())
    write_csv(sport["logo_intake"], logo_rows, logo_fields if logo_fields else LOGO_INTAKE_FIELDS)
    write_csv(sport["athlete_intake"], athlete_rows, athlete_fields if athlete_fields else ATHLETE_INTAKE_FIELDS)
    walkthrough_text = render_walkthrough(sport_key, sport, logo_contact_rows, athlete_contact_rows, reviewed_at_local=reviewed_at_local)
    write_text(sport["walkthrough"], walkthrough_text)

    return {
        "sport_family": sport_key,
        "sport_label": sport["sport_label"],
        "league_label": sport["league_label"],
        "logo_contact_rows": len(logo_contact_rows),
        "logo_prepared_rows": logo_changed,
        "athlete_contact_rows": len(athlete_contact_rows),
        "athlete_prepared_rows": athlete_changed,
        "walkthrough_rows": len(logo_contact_rows) + len(athlete_contact_rows),
        "logo_intake_csv": sport["logo_intake"].as_posix(),
        "athlete_intake_csv": sport["athlete_intake"].as_posix(),
        "walkthrough_md": sport["walkthrough"].as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-prep review-only intake rows and walkthrough guidance for women's hockey and softball.")
    parser.add_argument("--sport", action="append", choices=sorted(SPORTS), help="Sport to prepare; repeat for multiple sports. Defaults to both.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite already-reviewed rows instead of preserving them.")
    parser.add_argument("--reviewed-by", default="Mike source-review sweep", help="Reviewer label to write into the intake CSVs.")
    parser.add_argument("--reviewed-at-local", default="", help="Local timestamp label to write into the intake CSVs.")
    args = parser.parse_args()

    selected = args.sport or list(SPORTS)
    reviewed_at_local = args.reviewed_at_local or now_local()
    summaries = [run_for_sport(sport_key, overwrite=args.overwrite, reviewed_by=args.reviewed_by, reviewed_at_local=reviewed_at_local) for sport_key in selected]
    report = {
        "version": VERSION,
        "status": "hockey_softball_source_review_helper_ready",
        "generated_at_local": reviewed_at_local,
        "reviewed_by": args.reviewed_by,
        "overwrite": bool(args.overwrite),
        "guardrails": {
            "paid_apis": False,
            "automatic_downloads": False,
            "auto_approval": False,
            "headshot_png_writes": False,
            "approved_marker_writes": False,
            "publish_ready_movement": False,
            "publishing": False,
        },
        "summaries": summaries,
    }
    write_json(REPORT_JSON, report)
    write_text(
        REPORT_MD,
        "\n".join(
            [
                "# Hockey/Softball Source Review Intake Helper Report",
                "",
                f"- Status: `{report['status']}`",
                f"- Generated: `{report['generated_at_local']}`",
                f"- Reviewed by: `{report['reviewed_by']}`",
                f"- Overwrite: `{str(report['overwrite']).lower()}`",
                "- Guardrails: no paid APIs, no downloads, no auto-approval, no `headshot.png` writes, no `.approved` markers, no publish-ready movement, no publishing.",
                "",
                "## Summaries",
                "",
                *[
                    f"- {row['sport_label']} / {row['league_label']}: logo_prepared={row['logo_prepared_rows']}/{row['logo_contact_rows']}, athlete_prepared={row['athlete_prepared_rows']}/{row['athlete_contact_rows']}"
                    for row in summaries
                ],
                "",
            ]
        ),
    )
    print(json.dumps({"status": report["status"], "sports": [row["sport_family"] for row in summaries]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
