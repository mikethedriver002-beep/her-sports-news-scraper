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
        "branch_hints": ["renderer", "render", "lower-third", "visual", "photo-first"],
    },
    {
        "lane_id": "asset_registry_contact_sheets",
        "lane": "Asset registry/contact sheets",
        "owns": "Logo/photo source candidates, contact sheets, human intake worksheets",
        "default_next_action": "Keep candidate packets review-only and wait for human-edited intake before any asset-state change.",
        "branch_hints": [
            "asset",
            "photo",
            "logo",
            "contact-sheet",
            "contact_sheets",
            "registry",
            "source-map",
            "hockey",
            "softball",
        ],
    },
    {
        "lane_id": "games_schedule_stats",
        "lane": "Games/schedule/stats",
        "owns": "Results, schedules, game intelligence, stats evidence",
        "default_next_action": "Prefer free/public confirmation boards and exact source-proof cues before render or story promotion.",
        "branch_hints": ["game", "games", "schedule", "stats", "results", "score"],
    },
    {
        "lane_id": "breaking_public_signal",
        "lane": "Breaking/public signal",
        "owns": "News discovery, public-signal queue, confirmation evidence",
        "default_next_action": "Surface why a story looks urgent plus the exact manual confirmation row to open.",
        "branch_hints": ["breaking", "public-signal", "signal", "news"],
    },
    {
        "lane_id": "copy_editorial_polish",
        "lane": "Copy/editorial polish",
        "owns": "Titles, deks, captions, tone, visual copy fit",
        "default_next_action": "Keep suggestions sharp and editorial while preserving review-only language.",
        "branch_hints": ["copy", "editorial", "language", "dek", "title"],
    },
    {
        "lane_id": "qa_release_readiness",
        "lane": "QA/release readiness",
        "owns": "Guardrail scans, artifact freshness, merge safety",
        "default_next_action": "Run no-fix audits unless a focused repo-visible QA improvement is clearly warranted.",
        "branch_hints": ["qa", "release", "readiness", "guardrail", "audit"],
    },
    {
        "lane_id": "workflow_overhaul",
        "lane": "Workflow overhaul",
        "owns": "Conductor systems, lane orchestration, research packets, local tooling, status visibility",
        "default_next_action": "Improve operating visibility, alerts, and deterministic guardrails without changing product behavior.",
        "branch_hints": ["workflow", "conductor", "lane-status", "research-alert", "aider", "model-routing"],
    },
]

INTAKE_FIELDS = [
    "lane_id",
    "status",
    "branch",
    "pr",
    "owner",
    "last_update_utc",
    "completed_merge_pr",
    "completed_merge_commit",
    "blocker",
    "next_action",
    "notes",
    "review_only",
    "paid_apis",
    "source_fetching",
    "automatic_downloads",
    "auto_approval",
    "approval_state_change",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "publishing",
]

GUARDRAIL_DEFAULTS = {
    "review_only": "true",
    "paid_apis": "false",
    "source_fetching": "false",
    "automatic_downloads": "false",
    "auto_approval": "false",
    "approval_state_change": "false",
    "headshot_writes": "false",
    "approved_marker_writes": "false",
    "publish_ready": "false",
    "publishing": "false",
}

GUARDRAIL_FIELDS = list(GUARDRAIL_DEFAULTS)

WORKFLOW_HEARTBEAT_STATUS = "heartbeat_visible_needs_conductor_check"
WORKFLOW_HEARTBEAT_NEXT_ACTION = (
    "Refresh workflow/conductor artifacts, confirm no open PRs or active worktree hints, "
    "then nudge one review-only workflow-overhaul packet if the lane is still idle."
)
WORKFLOW_HEARTBEAT_CUE = (
    "Continuous visibility heartbeat: workflow-overhaul stays visible even when no manual intake, "
    "open PR, current branch, or worktree hint is present."
)
WORKFLOW_HEARTBEAT_CHECKLIST = [
    "Confirm current branch is based on origin/main.",
    "Confirm open PR count and worktree hint count before nudging new workflow work.",
    "Open operator_next_action_synthesis.md and conductor_workspace_audit.md if present.",
    "Keep the next packet workflow/conductor visibility-only and review-only.",
    "Do not fetch sources, download assets, approve assets, move publish-ready files, or publish.",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
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


def is_merged_to_main(commit: str) -> bool:
    if not commit:
        return False
    for ref in ("origin/main", "main"):
        code, _ = run_command(["git", "merge-base", "--is-ancestor", commit, ref])
        if code == 0:
            return True
    return False


def branch_has_merged_pr(branch: str) -> bool:
    if not branch or branch in {"main", "detached"}:
        return False
    code, output = run_command(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "merged",
            "--head",
            branch,
            "--limit",
            "1",
            "--json",
            "number",
        ]
    )
    if code != 0 or not output:
        return False
    try:
        rows = json.loads(output)
    except json.JSONDecodeError:
        return False
    return bool(rows)


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


def collect_worktree_branches() -> list[dict[str, str]]:
    code, output = run_command(["git", "worktree", "list", "--porcelain"])
    if code != 0 or not output:
        return []
    rows: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in output.splitlines():
        if not line.strip():
            if current:
                rows.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value.strip()
        elif key == "HEAD":
            current["head"] = value.strip()
        elif key == "branch":
            current["branch"] = value.strip().removeprefix("refs/heads/")
        elif key == "detached":
            current["branch"] = "detached"
    if current:
        rows.append(current)
    for row in rows:
        path = row.get("path", "")
        if path:
            dirty_code, dirty_output = run_command(["git", "status", "--short"], cwd=Path(path))
            row["dirty"] = "true" if dirty_code == 0 and dirty_output else "false"
            row["dirty_count"] = str(len([line for line in dirty_output.splitlines() if line.strip()])) if dirty_code == 0 else "unknown"
        row["merged_to_main"] = "true" if is_merged_to_main(row.get("head", "")) else "false"
        row["merged_pr"] = "true" if branch_has_merged_pr(row.get("branch", "")) else "false"
    return rows


def branch_matches_lane(branch: str, lane: dict[str, Any]) -> bool:
    normalized = branch.lower().replace("_", "-")
    if not normalized.startswith("codex/"):
        return False
    return any(hint in normalized for hint in lane.get("branch_hints", []))


def worktree_hints_by_lane(worktrees: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    hints: dict[str, list[dict[str, str]]] = {lane["lane_id"]: [] for lane in LANE_ROSTER}
    for worktree in worktrees:
        branch = worktree.get("branch", "")
        if worktree.get("merged_to_main") == "true":
            continue
        if worktree.get("merged_pr") == "true":
            continue
        if not branch or branch == "detached":
            continue
        for lane in LANE_ROSTER:
            if branch_matches_lane(branch, lane):
                hints[lane["lane_id"]].append(worktree)
                break
    return hints


def normalize_intake(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    by_lane: dict[str, dict[str, str]] = {}
    for row in rows:
        lane_id = (row.get("lane_id") or "").strip()
        if not lane_id:
            continue
        by_lane[lane_id] = {field: (row.get(field) or "").strip() for field in INTAKE_FIELDS}
    return by_lane


def normalized_guardrails(intake: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    warnings: list[str] = []
    for field, expected in GUARDRAIL_DEFAULTS.items():
        value = (intake.get(field) or expected).strip().lower()
        values[field] = value
        if value != expected:
            warnings.append(f"{field}_expected_{expected}_got_{value}")
    return values, warnings


def status_tone(status: str) -> str:
    normalized = status.lower()
    if any(token in normalized for token in ("blocked", "stale", "needs_human", "needs-human")):
        return "blocked"
    if any(token in normalized for token in ("active", "in_progress", "pr_open", "review", "detected")):
        return "active"
    if any(token in normalized for token in ("completed", "merged", "done")):
        return "completed"
    if "heartbeat" in normalized:
        return "idle"
    if any(token in normalized for token in ("idle", "queued", "ready")):
        return "idle"
    return "unknown"


def lane_rows(
    intake_rows: list[dict[str, str]],
    open_prs: list[dict[str, str]],
    git_state: dict[str, Any],
    worktrees: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    intake_by_lane = normalize_intake(intake_rows)
    pr_by_branch = {pr["branch"]: pr for pr in open_prs if pr.get("branch")}
    hints_by_lane = worktree_hints_by_lane(worktrees or [])
    rows: list[dict[str, str]] = []
    current_branch = str(git_state.get("branch") or "")
    for lane in LANE_ROSTER:
        lane_id = lane["lane_id"]
        intake = intake_by_lane.get(lane_id, {})
        lane_hints = hints_by_lane.get(lane_id, [])
        first_hint = lane_hints[0] if lane_hints else {}
        branch = intake.get("branch", "")
        matching_pr = pr_by_branch.get(branch, {}) if branch else pr_by_branch.get(first_hint.get("branch", ""), {})
        status = intake.get("status", "")
        if not status and branch and matching_pr:
            status = "pr_open"
        elif not status and branch:
            status = "active_or_needs_conductor_check"
        elif not status and lane_id == "workflow_overhaul" and "codex/workflow-" in current_branch:
            status = "active_current_lane"
            branch = current_branch
        elif not status and first_hint and matching_pr:
            status = "pr_open_from_worktree_hint"
            branch = first_hint.get("branch", "")
        elif not status and first_hint:
            status = "worktree_branch_detected_needs_conductor_check"
            branch = first_hint.get("branch", "")
        elif not status and lane_id == "workflow_overhaul":
            status = WORKFLOW_HEARTBEAT_STATUS
        elif not status:
            status = "unreported"
        guardrails, guardrail_warnings = normalized_guardrails(intake)
        notes = intake.get("notes", "")
        if first_hint and not notes:
            notes = f"worktree={first_hint.get('path', '')}; dirty={first_hint.get('dirty', 'unknown')}; dirty_count={first_hint.get('dirty_count', 'unknown')}"
        row = {
            "lane_id": lane_id,
            "lane": lane["lane"],
            "owns": lane["owns"],
            "status": status,
            "status_tone": status_tone(status),
            "branch": branch,
            "pr": intake.get("pr", "") or matching_pr.get("url", ""),
            "owner": intake.get("owner", ""),
            "last_update_utc": intake.get("last_update_utc", ""),
            "completed_merge_pr": intake.get("completed_merge_pr", ""),
            "completed_merge_commit": intake.get("completed_merge_commit", ""),
            "blocker": intake.get("blocker", ""),
            "next_action": intake.get("next_action", "") or lane["default_next_action"],
            "notes": notes,
            "status_source": "manual_intake"
            if intake
            else "current_branch"
            if status == "active_current_lane"
            else "workflow_heartbeat"
            if status == WORKFLOW_HEARTBEAT_STATUS
            else "worktree_hint"
            if first_hint
            else "default",
            "detected_worktree": first_hint.get("path", ""),
            "detected_worktree_dirty": first_hint.get("dirty", ""),
            "heartbeat": "true" if status == WORKFLOW_HEARTBEAT_STATUS else "false",
            "heartbeat_cue": WORKFLOW_HEARTBEAT_CUE if status == WORKFLOW_HEARTBEAT_STATUS else "",
            "heartbeat_next_action": WORKFLOW_HEARTBEAT_NEXT_ACTION if status == WORKFLOW_HEARTBEAT_STATUS else "",
            "guardrail_warnings": ";".join(guardrail_warnings),
        }
        if status == WORKFLOW_HEARTBEAT_STATUS:
            row["next_action"] = intake.get("next_action", "") or WORKFLOW_HEARTBEAT_NEXT_ACTION
        row.update(guardrails)
        rows.append(row)
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
        "| Lane | Status | Source | Branch | PR | Completed merge | Blocker | Next action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["lanes"]:
        pr = row["pr"] or "-"
        branch = row["branch"] or "-"
        completed = row["completed_merge_pr"] or row["completed_merge_commit"] or "-"
        if row["completed_merge_pr"] and row["completed_merge_commit"]:
            completed = f"{row['completed_merge_pr']} / `{row['completed_merge_commit']}`"
        blocker = row["blocker"] or "-"
        lines.append(
            f"| {row['lane']} | `{row['status']}` | `{row['status_source']}` | `{branch}` | {pr} | {completed} | {blocker} | {row['next_action']} |"
        )
    heartbeat = payload.get("workflow_overhaul_heartbeat", {})
    if heartbeat:
        lines.extend(
            [
                "",
                "## Workflow Overhaul Heartbeat",
                "",
                f"- Status: `{heartbeat['status']}`",
                f"- Source: `{heartbeat['status_source']}`",
                f"- Next action: {heartbeat['next_action']}",
                f"- Cue: {heartbeat['cue']}",
                "",
                "Checklist:",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in heartbeat["checklist"])
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
            "`lane_id,status,branch,pr,owner,last_update_utc,completed_merge_pr,completed_merge_commit,blocker,next_action,notes,review_only,paid_apis,source_fetching,automatic_downloads,auto_approval,approval_state_change,headshot_writes,approved_marker_writes,publish_ready,publishing`",
            "",
            "A starter example lives at `operator/inbox/workflow_lane_status_intake.example.csv`; copy rows into the real intake only after conductor review.",
            "",
            "If no intake row exists, the dashboard adds best-effort worktree hints from local `codex/` branches and marks them for conductor check.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    intake_rows = read_csv(args.intake)
    git_state = collect_git_state()
    open_prs = collect_open_prs() if not args.skip_pr_lookup else []
    worktrees = collect_worktree_branches() if not args.skip_worktree_lookup else []
    rows = lane_rows(intake_rows, open_prs, git_state, worktrees)
    workflow_row = next((row for row in rows if row["lane_id"] == "workflow_overhaul"), {})
    workflow_heartbeat = {
        "status": workflow_row.get("status", ""),
        "status_source": workflow_row.get("status_source", ""),
        "active": workflow_row.get("heartbeat") == "true",
        "next_action": workflow_row.get("heartbeat_next_action") or workflow_row.get("next_action", ""),
        "cue": workflow_row.get("heartbeat_cue", ""),
        "checklist": WORKFLOW_HEARTBEAT_CHECKLIST,
        "guardrails": {
            "review_only": True,
            "artifact_only": True,
            "paid_apis": False,
            "source_fetching": False,
            "automatic_downloads": False,
            "source_auto_enablement": False,
            "auto_approval": False,
            "approval_state_change": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "publish_ready_movement": False,
            "publishing": False,
        },
    }
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
        "worktrees": worktrees,
        "lanes": rows,
        "lane_count": len(rows),
        "unreported_lane_count": sum(1 for row in rows if row["status"] == "unreported"),
        "completed_lane_count": sum(1 for row in rows if row["status_tone"] == "completed"),
        "worktree_hint_lane_count": sum(1 for row in rows if row["status_source"] == "worktree_hint"),
        "heartbeat_lane_count": sum(1 for row in rows if row["heartbeat"] == "true"),
        "workflow_overhaul_heartbeat": workflow_heartbeat,
        "blocked_lane_count": sum(1 for row in rows if row["status_tone"] == "blocked"),
        "guardrail_warning_count": sum(1 for row in rows if row["guardrail_warnings"]),
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
            "completed_merge_pr",
            "completed_merge_commit",
            "blocker",
            "next_action",
            "notes",
            "status_source",
            "detected_worktree",
            "detected_worktree_dirty",
            "heartbeat",
            "heartbeat_cue",
            "heartbeat_next_action",
            *GUARDRAIL_FIELDS,
            "guardrail_warnings",
        ],
    )
    return {"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only HSD workflow lane status dashboard.")
    parser.add_argument("--intake", default=DEFAULT_INTAKE)
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--skip-pr-lookup", action="store_true")
    parser.add_argument("--skip-worktree-lookup", action="store_true")
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
                "completed_lane_count": payload["completed_lane_count"],
                "worktree_hint_lane_count": payload["worktree_hint_lane_count"],
                "heartbeat_lane_count": payload["heartbeat_lane_count"],
                "blocked_lane_count": payload["blocked_lane_count"],
                "guardrail_warning_count": payload["guardrail_warning_count"],
                "outputs": outputs,
                "review_only": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
