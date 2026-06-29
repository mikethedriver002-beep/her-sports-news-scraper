from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, read_csv, write_csv, write_json, write_text


VERSION = "hsd-workflow-lane-status-v1-review-only"
DEFAULT_INTAKE = "operator/inbox/workflow_lane_status_intake.csv"
DEFAULT_OUTPUT_STEM = "workflow_lane_status_dashboard"

LANE_ROSTER = [
    {
        "lane_id": "renderer_quality",
        "lane": "Renderer quality",
        "owns": "Manual review renderer visuals, preview QA, comparison boards",
        "default_next_action": "Nudge only after a current render QA artifact or external visual critique identifies one PR-sized lift.",
    },
    {
        "lane_id": "asset_registry_contact_sheets",
        "lane": "Asset registry/contact sheets",
        "owns": "Logo/photo source candidates, contact sheets, human intake worksheets",
        "default_next_action": "Keep candidate packets review-only and wait for human-edited intake before any asset-state change.",
    },
    {
        "lane_id": "games_schedule_stats",
        "lane": "Games/schedule/stats",
        "owns": "Results, schedules, game intelligence, stats evidence",
        "default_next_action": "Prefer free/public confirmation boards and exact source-proof cues before render or story promotion.",
    },
    {
        "lane_id": "breaking_public_signal",
        "lane": "Breaking/public signal",
        "owns": "News discovery, public-signal queue, confirmation evidence",
        "default_next_action": "Surface why a story looks urgent plus the exact manual confirmation row to open.",
    },
    {
        "lane_id": "copy_editorial_polish",
        "lane": "Copy/editorial polish",
        "owns": "Titles, deks, captions, tone, visual copy fit",
        "default_next_action": "Keep suggestions sharp and editorial while preserving review-only language.",
    },
    {
        "lane_id": "qa_release_readiness",
        "lane": "QA/release readiness",
        "owns": "Guardrail scans, artifact freshness, merge safety",
        "default_next_action": "Run no-fix audits unless a focused repo-visible QA improvement is clearly warranted.",
    },
    {
        "lane_id": "workflow_overhaul",
        "lane": "Workflow overhaul",
        "owns": "Conductor systems, lane orchestration, research packets, local tooling, status visibility",
        "default_next_action": "Improve operating visibility, alerts, and deterministic guardrails without changing product behavior.",
    },
]

INTAKE_FIELDS = [
    "lane_id",
    "status",
    "branch",
    "pr",
    "owner",
    "last_update_utc",
    "blocker",
    "next_action",
    "notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def git_value(args: list[str], default: str = "unknown") -> str:
    code, output = run_command(["git", *args])
    if code != 0 or not output:
        return default
    return output.splitlines()[0].strip() or default


def collect_git_state() -> dict[str, Any]:
    status_code, status_output = run_command(["git", "status", "--short", "--branch"])
    status_lines = [line for line in status_output.splitlines() if line.strip()] if status_code == 0 else []
    branch_line = status_lines[0] if status_lines else "unknown"
    dirty_lines = [line for line in status_lines[1:] if line.strip()]
    return {
        "head_commit": git_value(["rev-parse", "--short", "HEAD"]),
        "head_subject": git_value(["log", "-1", "--pretty=%s"]),
        "branch": branch_line.replace("## ", "", 1),
        "dirty": bool(dirty_lines),
        "dirty_count": len(dirty_lines),
        "dirty_paths": dirty_lines,
    }


def collect_open_prs() -> list[dict[str, str]]:
    code, output = run_command(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "50",
            "--json",
            "number,title,headRefName,isDraft,url",
        ]
    )
    if code != 0 or not output:
        return []
    try:
        rows = json.loads(output)
    except json.JSONDecodeError:
        return []
    prs: list[dict[str, str]] = []
    for row in rows:
        prs.append(
            {
                "number": str(row.get("number", "")),
                "title": str(row.get("title", "")),
                "branch": str(row.get("headRefName", "")),
                "state": "draft" if row.get("isDraft") else "ready",
                "url": str(row.get("url", "")),
            }
        )
    return prs


def normalize_intake(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    by_lane: dict[str, dict[str, str]] = {}
    for row in rows:
        lane_id = (row.get("lane_id") or "").strip()
        if not lane_id:
            continue
        by_lane[lane_id] = {field: (row.get(field) or "").strip() for field in INTAKE_FIELDS}
    return by_lane


def status_tone(status: str) -> str:
    normalized = status.lower()
    if any(token in normalized for token in ("blocked", "stale", "needs_human", "needs-human")):
        return "blocked"
    if any(token in normalized for token in ("active", "in_progress", "pr_open", "review")):
        return "active"
    if any(token in normalized for token in ("idle", "queued", "ready")):
        return "idle"
    return "unknown"


def lane_rows(intake_rows: list[dict[str, str]], open_prs: list[dict[str, str]], git_state: dict[str, Any]) -> list[dict[str, str]]:
    intake_by_lane = normalize_intake(intake_rows)
    pr_by_branch = {pr["branch"]: pr for pr in open_prs if pr.get("branch")}
    rows: list[dict[str, str]] = []
    current_branch = str(git_state.get("branch") or "")
    for lane in LANE_ROSTER:
        lane_id = lane["lane_id"]
        intake = intake_by_lane.get(lane_id, {})
        branch = intake.get("branch", "")
        matching_pr = pr_by_branch.get(branch, {}) if branch else {}
        status = intake.get("status", "")
        if not status and branch and matching_pr:
            status = "pr_open"
        elif not status and branch:
            status = "active_or_needs_conductor_check"
        elif lane_id == "workflow_overhaul" and "codex/workflow-" in current_branch:
            status = "active_current_lane"
            branch = current_branch
        elif not status:
            status = "unreported"
        rows.append(
            {
                "lane_id": lane_id,
                "lane": lane["lane"],
                "owns": lane["owns"],
                "status": status,
                "status_tone": status_tone(status),
                "branch": branch,
                "pr": intake.get("pr", "") or matching_pr.get("url", ""),
                "owner": intake.get("owner", ""),
                "last_update_utc": intake.get("last_update_utc", ""),
                "blocker": intake.get("blocker", ""),
                "next_action": intake.get("next_action", "") or lane["default_next_action"],
                "notes": intake.get("notes", ""),
            }
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    git_state = payload["git_state"]
    lines = [
        "# HSD Workflow Lane Status",
        "",
        "Status: review-only conductor visibility artifact.",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{payload['version']}`",
        "",
        "## Repo State",
        "",
        f"- Branch: `{git_state['branch']}`",
        f"- HEAD: `{git_state['head_commit']}` - {git_state['head_subject']}",
        f"- Dirty state: `{git_state['dirty_count']}` changed/untracked paths",
        f"- Open PRs detected: `{len(payload['open_prs'])}`",
        f"- Intake file: `{payload['intake_path']}`",
        "",
        "## Lane Dashboard",
        "",
        "| Lane | Status | Branch | PR | Blocker | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["lanes"]:
        pr = row["pr"] or "-"
        branch = row["branch"] or "-"
        blocker = row["blocker"] or "-"
        lines.append(
            f"| {row['lane']} | `{row['status']}` | `{branch}` | {pr} | {blocker} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrail Posture",
            "",
            "- Review-only conductor artifact.",
            "- No paid APIs.",
            "- No automatic downloads.",
            "- No auto-approval.",
            "- No approval-state changes.",
            "- No headshot writes.",
            "- No `.approved` markers.",
            "- No publish-ready lane.",
            "- No publishing.",
            "",
            "## Manual Intake",
            "",
            "Optional intake rows can live in `operator/inbox/workflow_lane_status_intake.csv` with these columns:",
            "",
            "`lane_id,status,branch,pr,owner,last_update_utc,blocker,next_action,notes`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    intake_rows = read_csv(args.intake)
    git_state = collect_git_state()
    open_prs = collect_open_prs() if not args.skip_pr_lookup else []
    rows = lane_rows(intake_rows, open_prs, git_state)
    payload = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "workflow_lane_status_ready",
        "review_only": True,
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "publishing": False,
        "publish_ready": False,
        "intake_path": args.intake,
        "git_state": git_state,
        "open_prs": open_prs,
        "lanes": rows,
        "lane_count": len(rows),
        "unreported_lane_count": sum(1 for row in rows if row["status"] == "unreported"),
        "blocked_lane_count": sum(1 for row in rows if row["status_tone"] == "blocked"),
    }
    return payload


def write_outputs(payload: dict[str, Any], output_stem: str) -> dict[str, str]:
    md_path = write_text(f"{output_stem}.md", render_markdown(payload))
    json_path = write_json(f"{output_stem}.json", payload)
    csv_path = write_csv(
        f"{output_stem}.csv",
        payload["lanes"],
        [
            "lane_id",
            "lane",
            "owns",
            "status",
            "status_tone",
            "branch",
            "pr",
            "owner",
            "last_update_utc",
            "blocker",
            "next_action",
            "notes",
        ],
    )
    return {"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only HSD workflow lane status dashboard.")
    parser.add_argument("--intake", default=DEFAULT_INTAKE)
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--skip-pr-lookup", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    outputs = write_outputs(payload, args.output_stem)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "lane_count": payload["lane_count"],
                "unreported_lane_count": payload["unreported_lane_count"],
                "blocked_lane_count": payload["blocked_lane_count"],
                "outputs": outputs,
                "review_only": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
