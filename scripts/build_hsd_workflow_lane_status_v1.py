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
DEFAULT_NUDGE_STEM = "workflow_lane_nudge_synthesis"
DEFAULT_RECOVERY_STEM = "workflow_durable_lane_recovery_packet"

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

EXPECTED_DURABLE_LANE_IDS = {
    "games_schedule_stats",
    "breaking_public_signal",
}

INTAKE_FIELDS = [
    "lane_id",
    "status",
    "branch",
    "pr",
    "pending_thread",
    "lane_owner_thread",
    "last_pr_merged",
    "restart_needed",
    "next_packet",
    "lifecycle_action",
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
NUDGE_FIELDS = [
    "rank",
    "lane_id",
    "lane",
    "nudge_type",
    "priority",
    "status",
    "activity_status",
    "activity_age_hours",
    "last_known_branch",
    "last_known_head",
    "pr",
    "pending_thread",
    "lane_owner_thread",
    "last_pr_merged",
    "next_packet",
    "lifecycle_action",
    "manual_conductor_prompt",
    "guardrail_note",
    "review_only",
    "automatic_changes",
]

RECOVERY_FIELDS = [
    "rank",
    "lane_id",
    "lane",
    "durable_lane_thread_status",
    "exact_start_prompt",
    "exact_recover_prompt",
    "anchor_artifacts",
    "owner_thread",
    "last_pr_merged",
    "next_conductor_action",
    "guardrail_note",
    "review_only",
    "automatic_changes",
]

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
    "If an expected durable lane thread is missing, recover or recreate it explicitly instead of assuming invisible work is active.",
    "Open operator_next_action_synthesis.md and conductor_workspace_audit.md if present.",
    "Keep the next packet workflow/conductor visibility-only and review-only.",
    "Do not fetch sources, download assets, approve assets, move publish-ready files, or publish.",
]
STALE_LANE_AFTER_HOURS = 48
STALE_EXEMPT_STATUS_TOKENS = ("completed", "merged", "done")
STALE_REVIEW_STATUS_TOKENS = ("active", "progress", "pr_open", "review", "blocked", "needs", "detected")
MANUAL_LIFECYCLE_ACTIONS = {
    "nudge": "Nudge owner thread with one current-main next step; do not create another lane until conductor checks current PR/worktree state.",
    "replace_reboot": "Replace/reboot from current origin/main in a fresh branch or thread after conductor confirms the old lane is no longer active.",
    "pause": "Pause lane and keep it visible; do not nudge or merge until blocker changes.",
    "archive": "Recommend manual archive/cleanup after conductor confirms no active branch or PR remains.",
    "merge_ready": "Check PR freshness, focused tests, and guardrails before conductor merge review.",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: str) -> datetime | None:
    clean = (value or "").strip()
    if not clean:
        return None
    if clean.endswith("Z"):
        clean = f"{clean[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_stale_exempt_status(status: str) -> bool:
    normalized = status.lower()
    return any(token in normalized for token in STALE_EXEMPT_STATUS_TOKENS)


def needs_stale_lane_check(status: str, branch: str, pr: str, blocker: str) -> bool:
    normalized = status.lower()
    if is_stale_exempt_status(normalized):
        return False
    if any(token in normalized for token in STALE_REVIEW_STATUS_TOKENS):
        return True
    return bool(branch or pr or blocker)


def lane_staleness(
    intake: dict[str, str],
    status: str,
    branch: str,
    pr: str,
    blocker: str,
    as_of_utc: datetime,
    stale_after_hours: int,
) -> dict[str, str]:
    if not intake or not needs_stale_lane_check(status, branch, pr, blocker):
        return {
            "staleness_status": "not_applicable",
            "stale_lane_brake": "false",
            "stale_age_hours": "",
            "stale_threshold_hours": str(stale_after_hours),
            "stale_warning": "",
        }

    last_update = parse_utc(intake.get("last_update_utc", ""))
    if not last_update:
        return {
            "staleness_status": "missing_last_update_needs_conductor_check",
            "stale_lane_brake": "true",
            "stale_age_hours": "",
            "stale_threshold_hours": str(stale_after_hours),
            "stale_warning": "manual_intake_active_without_last_update_utc",
        }

    age_hours = max(0.0, (as_of_utc - last_update).total_seconds() / 3600)
    if age_hours > stale_after_hours:
        return {
            "staleness_status": "stale_lane_needs_conductor_check",
            "stale_lane_brake": "true",
            "stale_age_hours": f"{age_hours:.1f}",
            "stale_threshold_hours": str(stale_after_hours),
            "stale_warning": f"last_update_utc_older_than_{stale_after_hours}h",
        }

    return {
        "staleness_status": "fresh_enough",
        "stale_lane_brake": "false",
        "stale_age_hours": f"{age_hours:.1f}",
        "stale_threshold_hours": str(stale_after_hours),
        "stale_warning": "",
    }


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


def boolish(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}


def durable_lane_thread_status(
    lane_id: str,
    status: str,
    pending_thread: str,
    lane_owner_thread: str,
) -> str:
    if lane_id not in EXPECTED_DURABLE_LANE_IDS:
        return ""
    if pending_thread or lane_owner_thread:
        return "thread_reference_present"
    normalized = status.lower()
    if is_stale_exempt_status(normalized):
        return "completed_lane_thread_reference_missing"
    if normalized in {"unreported", ""}:
        return "missing_lane_thread_needs_conductor_recover"
    return "active_lane_thread_reference_missing"


def durable_lane_recovery_cue(thread_status: str, next_packet: str, lane_owner_thread: str) -> str:
    if thread_status == "thread_reference_present":
        return ""
    if thread_status == "completed_lane_thread_reference_missing":
        return (
            "RECOVER_THREAD_REFERENCE: add a lane_owner_thread or pending_thread for this durable lane so the merge-wave "
            "history stays visible; restart from current origin/main only if a fresh packet is needed."
        )
    if thread_status == "active_lane_thread_reference_missing":
        return (
            "RECOVER_THREAD_REFERENCE: add a lane_owner_thread or pending_thread before assuming invisible work is active."
        )
    if thread_status == "missing_lane_thread_needs_conductor_recover":
        return (
            "RECOVER_THREAD_REFERENCE: recreate or relink this durable lane explicitly from current origin/main before "
            "assuming a quiet thread exists."
        )
    return next_packet or lane_owner_thread


def durable_lane_exact_start_prompt(lane_id: str) -> str:
    if lane_id == "games_schedule_stats":
        return (
            "Open `game_source_confirmation_next_action_v1.csv`, `game_source_research_worksheet_v1.csv`, and "
            "`game_fact_confirmation_status_v1.csv`, then continue the first incomplete games/stats confirmation row "
            "from current `origin/main`."
        )
    if lane_id == "breaking_public_signal":
        return (
            "Open `breaking_public_signal_clusters.md` and `breaking_public_signal_confirmation_intake.csv`, then "
            "fill the first missing confirmation row before any story path."
        )
    return "Open the lane-specific confirmation artifact from current `origin/main`."


def durable_lane_exact_recover_prompt(lane_id: str) -> str:
    if lane_id == "games_schedule_stats":
        return (
            "If the lane thread is missing, recover or relink the durable games/stats lane explicitly, then use the "
            "confirmation next-action and research worksheet rows before any story or render path."
        )
    if lane_id == "breaking_public_signal":
        return (
            "If the lane thread is missing, recover or relink the durable breaking/public-signal lane explicitly, "
            "then continue from the clusters and confirmation intake rows."
        )
    return "If the lane thread is missing, recover or relink the durable lane explicitly before continuing."


def durable_lane_anchor_artifacts(lane_id: str) -> str:
    if lane_id == "games_schedule_stats":
        return (
            "game_source_confirmation_next_action_v1.csv; game_source_research_worksheet_v1.csv; "
            "game_fact_confirmation_status_v1.csv; story_proof_card_v1.csv; final_score_stat_proof_v1.csv"
        )
    if lane_id == "breaking_public_signal":
        return (
            "breaking_public_signal_clusters.md; breaking_public_signal_confirmation_intake.csv; "
            "breaking_public_signal_next_action_v1.csv; breaking_public_signal_return_summary_v1.csv"
        )
    return ""


def restart_status(status: str, restart_needed: str, next_packet: str, lane_owner_thread: str) -> str:
    if boolish(restart_needed):
        return "restart_ready_from_current_main" if next_packet else "restart_needed_missing_next_packet"
    if is_stale_exempt_status(status):
        if next_packet or lane_owner_thread:
            return "completed_restart_context_available"
        return "completed_no_restart_requested"
    return "not_applicable"


def activity_age_hours(last_update_utc: str, as_of_utc: datetime) -> str:
    last_update = parse_utc(last_update_utc)
    if not last_update:
        return ""
    return f"{max(0.0, (as_of_utc - last_update).total_seconds() / 3600):.1f}"


def activity_status(staleness: dict[str, str], restart_needed: str, status: str, last_update_utc: str) -> str:
    if staleness.get("stale_lane_brake") == "true":
        return "stale_brake"
    if boolish(restart_needed):
        return "restart_needed"
    if is_stale_exempt_status(status):
        return "completed_or_merged"
    if last_update_utc:
        return "active_recent_or_waiting"
    return "no_manual_activity_timestamp"


def conductor_action_for_row(
    lifecycle_action: str,
    staleness: dict[str, str],
    restart_needed: str,
    next_packet: str,
    heartbeat: bool,
    default_next_action: str,
) -> str:
    normalized_action = (lifecycle_action or "").strip().lower()
    if normalized_action in MANUAL_LIFECYCLE_ACTIONS:
        return MANUAL_LIFECYCLE_ACTIONS[normalized_action]
    if staleness.get("stale_lane_brake") == "true":
        return "STALE_BRAKE: refresh current origin/main, open PR/worktree/thread state, then nudge, pause, replace/reboot, archive, or merge-ready manually."
    if boolish(restart_needed):
        return f"RESTART_NEEDED: {next_packet or 'define next_packet, then restart from current origin/main.'}"
    if heartbeat:
        return WORKFLOW_HEARTBEAT_NEXT_ACTION
    return default_next_action


def nudge_type_for_row(row: dict[str, str]) -> str:
    if row.get("durable_lane_thread_status") and row.get("durable_lane_thread_status") != "thread_reference_present":
        return "missing_durable_lane_thread"
    if row.get("stale_lane_brake") == "true":
        return "stale_brake"
    if boolish(row.get("restart_needed", "")):
        return "restart_needed"
    if row.get("lifecycle_action"):
        return "manual_lifecycle_action"
    if row.get("heartbeat") == "true":
        return "workflow_heartbeat"
    if row.get("status_source") == "worktree_hint":
        return "worktree_hint_check"
    return ""


def nudge_priority(nudge_type: str) -> str:
    priorities = {
        "missing_durable_lane_thread": "P2",
        "stale_brake": "P1",
        "restart_needed": "P2",
        "manual_lifecycle_action": "P2",
        "workflow_heartbeat": "P3",
        "worktree_hint_check": "P3",
    }
    return priorities.get(nudge_type, "")


def nudge_sort_key(row: dict[str, str]) -> tuple[int, float, str]:
    priority_order = {"P1": 1, "P2": 2, "P3": 3}
    age_raw = row.get("activity_age_hours") or row.get("stale_age_hours") or "0"
    try:
        age = float(age_raw)
    except ValueError:
        age = 0.0
    return (priority_order.get(row.get("priority", ""), 9), -age, row.get("lane_id", ""))


def build_nudge_rows(lanes: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lane in lanes:
        nudge_type = nudge_type_for_row(lane)
        if not nudge_type:
            continue
        row = {
            "rank": "",
            "lane_id": lane["lane_id"],
            "lane": lane["lane"],
            "nudge_type": nudge_type,
            "priority": nudge_priority(nudge_type),
            "status": lane["status"],
            "activity_status": lane["activity_status"],
            "activity_age_hours": lane["activity_age_hours"],
            "last_known_branch": lane["last_known_branch"],
            "last_known_head": lane["last_known_head"],
            "pr": lane["pr"],
            "pending_thread": lane["pending_thread"],
            "lane_owner_thread": lane["lane_owner_thread"],
            "last_pr_merged": lane["last_pr_merged"],
            "next_packet": lane["next_packet"],
            "lifecycle_action": lane["lifecycle_action"],
            "manual_conductor_prompt": lane["next_conductor_action"],
            "guardrail_note": "Manual cue only; do not delete worktrees, close branches, archive user-owned threads, rebase/rewrite branches, approve assets, enable sources, download assets, move publish-ready files, or publish.",
            "review_only": "true",
            "automatic_changes": "false",
        }
        rows.append(row)
    rows.sort(key=nudge_sort_key)
    for index, row in enumerate(rows, 1):
        row["rank"] = str(index)
    return rows


def build_recovery_rows(lanes: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lane in lanes:
        status = lane.get("durable_lane_thread_status", "")
        if not status or status == "thread_reference_present":
            continue
        rows.append(
            {
                "rank": "",
                "lane_id": lane["lane_id"],
                "lane": lane["lane"],
                "durable_lane_thread_status": status,
                "exact_start_prompt": durable_lane_exact_start_prompt(lane["lane_id"]),
                "exact_recover_prompt": durable_lane_exact_recover_prompt(lane["lane_id"]),
                "anchor_artifacts": durable_lane_anchor_artifacts(lane["lane_id"]),
                "owner_thread": lane["lane_owner_thread"] or lane["pending_thread"] or "",
                "last_pr_merged": lane["last_pr_merged"],
                "next_conductor_action": lane["durable_lane_recovery_cue"],
                "guardrail_note": "Manual recovery prompt only; do not create threads, close branches, delete worktrees, rebase branches, change approval/download/source/publish state, or publish.",
                "review_only": "true",
                "automatic_changes": "false",
            }
        )
    rows.sort(key=lambda row: row["lane_id"])
    for index, row in enumerate(rows, 1):
        row["rank"] = str(index)
    return rows


def lane_rows(
    intake_rows: list[dict[str, str]],
    open_prs: list[dict[str, str]],
    git_state: dict[str, Any],
    worktrees: list[dict[str, str]] | None = None,
    as_of_utc: datetime | None = None,
    stale_after_hours: int = STALE_LANE_AFTER_HOURS,
) -> list[dict[str, str]]:
    intake_by_lane = normalize_intake(intake_rows)
    pr_by_branch = {pr["branch"]: pr for pr in open_prs if pr.get("branch")}
    hints_by_lane = worktree_hints_by_lane(worktrees or [])
    rows: list[dict[str, str]] = []
    current_branch = str(git_state.get("branch") or "")
    stale_as_of = as_of_utc or datetime.now(timezone.utc)
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
        pr_value = intake.get("pr", "") or matching_pr.get("url", "")
        last_pr_merged = intake.get("last_pr_merged", "") or intake.get("completed_merge_pr", "")
        lane_owner_thread = intake.get("lane_owner_thread", "")
        restart_needed = intake.get("restart_needed", "")
        next_packet = intake.get("next_packet", "")
        lifecycle_action = intake.get("lifecycle_action", "")
        durable_thread_status = durable_lane_thread_status(
            lane_id,
            status,
            intake.get("pending_thread", ""),
            lane_owner_thread,
        )
        staleness = lane_staleness(
            intake,
            status,
            branch,
            pr_value,
            intake.get("blocker", ""),
            stale_as_of,
            stale_after_hours,
        )
        heartbeat_active = status == WORKFLOW_HEARTBEAT_STATUS
        default_next_action = intake.get("next_action", "") or lane["default_next_action"]
        row = {
            "lane_id": lane_id,
            "lane": lane["lane"],
            "owns": lane["owns"],
            "status": status,
            "status_tone": status_tone(status),
            "branch": branch,
            "pr": pr_value,
            "pending_thread": intake.get("pending_thread", ""),
            "lane_owner_thread": lane_owner_thread,
            "last_pr_merged": last_pr_merged,
            "restart_needed": restart_needed,
            "next_packet": next_packet,
            "restart_status": restart_status(status, restart_needed, next_packet, lane_owner_thread),
            "lifecycle_action": lifecycle_action,
            "durable_lane_thread_status": durable_thread_status,
            "durable_lane_recovery_cue": durable_lane_recovery_cue(durable_thread_status, next_packet, lane_owner_thread),
            "activity_age_hours": activity_age_hours(intake.get("last_update_utc", ""), stale_as_of),
            "activity_status": activity_status(staleness, restart_needed, status, intake.get("last_update_utc", "")),
            "last_known_branch": branch,
            "last_known_head": first_hint.get("head", "") or intake.get("completed_merge_commit", ""),
            "owner": intake.get("owner", ""),
            "last_update_utc": intake.get("last_update_utc", ""),
            "completed_merge_pr": intake.get("completed_merge_pr", ""),
            "completed_merge_commit": intake.get("completed_merge_commit", ""),
            "blocker": intake.get("blocker", ""),
            "next_action": default_next_action,
            "next_conductor_action": conductor_action_for_row(
                lifecycle_action,
                staleness,
                restart_needed,
                next_packet,
                heartbeat_active,
                default_next_action,
            ),
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
            "heartbeat": "true" if heartbeat_active else "false",
            "heartbeat_cue": WORKFLOW_HEARTBEAT_CUE if heartbeat_active else "",
            "heartbeat_next_action": WORKFLOW_HEARTBEAT_NEXT_ACTION if heartbeat_active else "",
            "guardrail_warnings": ";".join(guardrail_warnings),
        }
        row.update(staleness)
        if status == WORKFLOW_HEARTBEAT_STATUS:
            row["next_action"] = intake.get("next_action", "") or WORKFLOW_HEARTBEAT_NEXT_ACTION
            row["next_conductor_action"] = WORKFLOW_HEARTBEAT_NEXT_ACTION
        elif durable_thread_status and durable_thread_status != "thread_reference_present":
            row["next_conductor_action"] = row["durable_lane_recovery_cue"]
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
        f"- Stale lane brakes: `{payload['stale_lane_count']}`",
        f"- Missing durable lane thread refs: `{payload['missing_durable_lane_count']}`",
        f"- Restart-needed lanes: `{payload['restart_needed_lane_count']}`",
        f"- Lifecycle-action lanes: `{payload['lifecycle_action_lane_count']}`",
        f"- Intake file: `{payload['intake_path']}`",
        "",
        "## Lane Dashboard",
        "",
        "| Lane | Status | Activity | Age h | Stale brake | Restart | Lifecycle | Durable thread | Last known branch | Last known head | PR | Pending thread | Owner thread | Last merged PR | Next conductor action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["lanes"]:
        pr = row["pr"] or "-"
        pending_thread = row["pending_thread"] or "-"
        lane_owner_thread = row["lane_owner_thread"] or "-"
        last_known_branch = row["last_known_branch"] or "-"
        last_known_head = row["last_known_head"] or "-"
        last_pr_merged = row["last_pr_merged"] or "-"
        lifecycle_action = row["lifecycle_action"] or "-"
        durable_thread_status = row["durable_lane_thread_status"] or "-"
        activity_age = row["activity_age_hours"] or "-"
        lines.append(
            f"| {row['lane']} | `{row['status']}` | `{row['activity_status']}` | `{activity_age}` | `{row['staleness_status']}` | `{row['restart_status']}` | `{lifecycle_action}` | `{durable_thread_status}` | {last_known_branch} | {last_known_head} | {pr} | {pending_thread} | {lane_owner_thread} | {last_pr_merged} | {row['next_conductor_action']} |"
        )
    durable_rows = [row for row in payload["lanes"] if row.get("durable_lane_thread_status")]
    if durable_rows:
        lines.extend(
            [
                "",
                "## Durable Lane Roster",
                "",
                f"- Expected durable lanes tracked: `{len(EXPECTED_DURABLE_LANE_IDS)}`",
                f"- Durable lanes missing thread references: `{payload['missing_durable_lane_count']}`",
                "- Missing thread references are conductor recovery cues only; they do not create threads, branches, PRs, or publish state.",
            ]
        )
        for row in durable_rows:
            recovery = row["durable_lane_recovery_cue"] or "Thread reference present."
            lines.append(
                f"- `{row['lane_id']}`: `{row['durable_lane_thread_status']}`; last merged PR: `{row['last_pr_merged'] or '-'}`; owner thread: `{row['lane_owner_thread'] or '-'}`; cue: {recovery}"
            )
    restart_rows = [row for row in payload["lanes"] if row.get("restart_needed", "").lower() == "true"]
    lines.extend(
        [
            "",
            "## Restart Cues",
            "",
            f"- Restart-needed lanes: `{len(restart_rows)}`",
            "- Restart cues are manual conductor prompts only; start any resumed packet from current `origin/main`.",
        ]
    )
    for row in restart_rows:
        packet = row["next_packet"] or "missing next_packet"
        owner = row["lane_owner_thread"] or row["pending_thread"] or "missing lane_owner_thread"
        lines.append(f"- `{row['lane_id']}`: {packet}; owner thread: `{owner}`; last merged PR: `{row['last_pr_merged'] or '-'}`")
    stale_rows = [row for row in payload["lanes"] if row.get("stale_lane_brake") == "true"]
    lines.extend(
        [
            "",
            "## Stale Lane Brake",
            "",
            f"- Active stale or missing-update lanes: `{len(stale_rows)}`",
            f"- Threshold: `{payload['stale_lane_threshold_hours']}` hours since `last_update_utc`.",
            "- Brake only informs conductor review; it does not edit branches, PRs, sources, assets, approvals, or publish state.",
        ]
    )
    for row in stale_rows:
        age = f"{row['stale_age_hours']}h" if row["stale_age_hours"] else "unknown age"
        lines.append(f"- `{row['lane_id']}`: `{row['staleness_status']}` ({age}); warning: `{row['stale_warning']}`")
    lifecycle_rows = [row for row in payload["lanes"] if row.get("lifecycle_action")]
    lines.extend(
        [
            "",
            "## Manual Lifecycle Actions",
            "",
            f"- Lanes with manual lifecycle action: `{len(lifecycle_rows)}`",
            "- Allowed cues: `nudge`, `replace_reboot`, `pause`, `archive`, `merge_ready`.",
            "- These cues are review-only text; they do not mutate branches, worktrees, PRs, threads, sources, assets, approvals, or publish state.",
        ]
    )
    for row in lifecycle_rows:
        lines.append(f"- `{row['lane_id']}`: `{row['lifecycle_action']}` - {row['next_conductor_action']}")
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
            "`lane_id,status,branch,pr,pending_thread,lane_owner_thread,last_pr_merged,restart_needed,next_packet,lifecycle_action,owner,last_update_utc,completed_merge_pr,completed_merge_commit,blocker,next_action,notes,review_only,paid_apis,source_fetching,automatic_downloads,auto_approval,approval_state_change,headshot_writes,approved_marker_writes,publish_ready,publishing`",
            "",
            "A starter example lives at `operator/inbox/workflow_lane_status_intake.example.csv`; copy rows into the real intake only after conductor review.",
            "",
            "Use `pending_thread` for a delegated Codex thread id or URL that has work in progress but no PR yet.",
            "",
            "Use `lane_owner_thread`, `last_pr_merged`, `restart_needed`, and `next_packet` to make merged durable lanes restartable from current main after a merge wave.",
            "",
            "Use `lifecycle_action` only for manual conductor cues: `nudge`, `replace_reboot`, `pause`, `archive`, or `merge_ready`.",
            "",
            "If no intake row exists, the dashboard adds best-effort worktree hints from local `codex/` branches and marks them for conductor check.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_recovery_markdown(payload: dict[str, Any]) -> str:
    rows = payload.get("durable_lane_recovery", [])
    lines = [
        "# HSD Durable Lane Recovery Packet",
        "",
        "Status: review-only conductor operator prompt packet.",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{payload['version']}`",
        "",
        "## Summary",
        "",
        f"- Missing durable lanes: `{payload['missing_durable_lane_count']}`",
        f"- Recovery rows: `{len(rows)}`",
        "",
        "## Exact Recovery Prompts",
        "",
        "| Rank | Lane | Thread status | Start prompt | Recover prompt | Anchor artifacts | Owner thread | Next conductor action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not rows:
        lines.append("| - | - | - | - | - | - | - | No missing durable lane thread refs need recovery. |")
    for row in rows:
        lines.append(
            "| {rank} | {lane} | `{status}` | {start} | {recover} | {anchors} | {owner} | {action} |".format(
                rank=row["rank"],
                lane=row["lane"],
                status=row["durable_lane_thread_status"],
                start=row["exact_start_prompt"],
                recover=row["exact_recover_prompt"],
                anchors=row["anchor_artifacts"] or "-",
                owner=row["owner_thread"] or "-",
                action=row["next_conductor_action"],
            )
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review-only and artifact-only.",
            "- Manual recovery cues only; do not create, close, archive, rebase, or rewrite threads or branches automatically.",
            "- No approval, download, source, publish-ready, or publishing state changes.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_nudge_markdown(payload: dict[str, Any]) -> str:
    rows = payload.get("nudge_synthesis", [])
    lines = [
        "# HSD Workflow Lane Nudge Synthesis",
        "",
        "Status: review-only conductor nudge artifact.",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{payload['version']}`",
        "",
        "## Summary",
        "",
        f"- Nudge rows: `{len(rows)}`",
        f"- Stale brakes: `{payload['stale_lane_count']}`",
        f"- Restart-needed lanes: `{payload['restart_needed_lane_count']}`",
        f"- Lifecycle-action lanes: `{payload['lifecycle_action_lane_count']}`",
        "",
        "## Manual Nudge Queue",
        "",
        "| Rank | Priority | Lane | Type | Age h | Branch | PR | Owner thread | Prompt |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not rows:
        lines.append("| - | - | - | - | - | - | - | - | No stale, restart-needed, lifecycle, heartbeat, durable-thread, or worktree-hint rows need a conductor nudge. |")
    for row in rows:
        lines.append(
            "| {rank} | `{priority}` | {lane} | `{nudge_type}` | `{age}` | `{branch}` | {pr} | {owner} | {prompt} |".format(
                rank=row["rank"],
                priority=row["priority"],
                lane=row["lane"],
                nudge_type=row["nudge_type"],
                age=row["activity_age_hours"] or "-",
                branch=row["last_known_branch"] or "-",
                pr=row["pr"] or "-",
                owner=row["lane_owner_thread"] or row["pending_thread"] or "-",
                prompt=row["manual_conductor_prompt"],
            )
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review-only and artifact-only.",
            "- Manual cues only: nudge, replace/reboot, pause, archive recommendation, or merge-ready review.",
            "- No force-deleting worktrees.",
            "- No closing branches automatically.",
            "- No archiving user-owned threads automatically.",
            "- No rebasing or rewriting lane branches automatically.",
            "- No approval, download, source, publish-ready, or publishing state changes.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    intake_rows = read_csv(args.intake)
    generated_at_utc = args.as_of_utc or now_iso()
    as_of = parse_utc(generated_at_utc) or datetime.now(timezone.utc)
    git_state = collect_git_state()
    open_prs = collect_open_prs() if not args.skip_pr_lookup else []
    worktrees = collect_worktree_branches() if not args.skip_worktree_lookup else []
    rows = lane_rows(intake_rows, open_prs, git_state, worktrees, as_of, args.stale_after_hours)
    nudge_rows = build_nudge_rows(rows)
    recovery_rows = build_recovery_rows(rows)
    workflow_row = next((row for row in rows if row["lane_id"] == "workflow_overhaul"), {})
    missing_durable_lane_rows = [
        row
        for row in rows
        if row.get("durable_lane_thread_status") and row.get("durable_lane_thread_status") != "thread_reference_present"
    ]
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
        "generated_at_utc": generated_at_utc,
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
        "nudge_synthesis": nudge_rows,
        "nudge_synthesis_count": len(nudge_rows),
        "nudge_synthesis_p1_count": sum(1 for row in nudge_rows if row["priority"] == "P1"),
        "durable_lane_recovery": recovery_rows,
        "durable_lane_recovery_count": len(recovery_rows),
        "lane_count": len(rows),
        "missing_durable_lane_count": len(missing_durable_lane_rows),
        "missing_durable_lane_ids": [row["lane_id"] for row in missing_durable_lane_rows],
        "unreported_lane_count": sum(1 for row in rows if row["status"] == "unreported"),
        "completed_lane_count": sum(1 for row in rows if row["status_tone"] == "completed"),
        "worktree_hint_lane_count": sum(1 for row in rows if row["status_source"] == "worktree_hint"),
        "heartbeat_lane_count": sum(1 for row in rows if row["heartbeat"] == "true"),
        "workflow_overhaul_heartbeat": workflow_heartbeat,
        "restart_needed_lane_count": sum(1 for row in rows if boolish(row.get("restart_needed", ""))),
        "lifecycle_action_lane_count": sum(1 for row in rows if row.get("lifecycle_action")),
        "stale_lane_count": sum(1 for row in rows if row["stale_lane_brake"] == "true"),
        "stale_lane_threshold_hours": args.stale_after_hours,
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
            "pending_thread",
            "lane_owner_thread",
            "last_pr_merged",
            "restart_needed",
            "next_packet",
            "restart_status",
            "lifecycle_action",
            "durable_lane_thread_status",
            "durable_lane_recovery_cue",
            "activity_age_hours",
            "activity_status",
            "last_known_branch",
            "last_known_head",
            "owner",
            "last_update_utc",
            "completed_merge_pr",
            "completed_merge_commit",
            "blocker",
            "next_action",
            "next_conductor_action",
            "notes",
            "status_source",
            "detected_worktree",
            "detected_worktree_dirty",
            "heartbeat",
            "heartbeat_cue",
            "heartbeat_next_action",
            "staleness_status",
            "stale_lane_brake",
            "stale_age_hours",
            "stale_threshold_hours",
            "stale_warning",
            *GUARDRAIL_FIELDS,
            "guardrail_warnings",
        ],
    )
    nudge_md_path = write_text(f"{DEFAULT_NUDGE_STEM}.md", render_nudge_markdown(payload))
    nudge_json_path = write_json(
        f"{DEFAULT_NUDGE_STEM}.json",
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "status": "workflow_lane_nudge_synthesis_ready",
            "review_only": True,
            "automatic_changes": False,
            "counts": {
                "rows": payload["nudge_synthesis_count"],
                "p1": payload["nudge_synthesis_p1_count"],
                "stale_lane_count": payload["stale_lane_count"],
                "restart_needed_lane_count": payload["restart_needed_lane_count"],
                "lifecycle_action_lane_count": payload["lifecycle_action_lane_count"],
            },
            "guardrails": {
                "review_only": True,
                "automatic_changes": False,
                "worktree_deletion": False,
                "branch_closure": False,
                "thread_archival": False,
                "branch_rewrite": False,
                "approval_state_change": False,
                "source_enablement": False,
                "asset_downloads": False,
                "publish_ready_movement": False,
                "publishing": False,
            },
            "rows": payload["nudge_synthesis"],
        },
    )
    nudge_csv_path = write_csv(f"{DEFAULT_NUDGE_STEM}.csv", payload["nudge_synthesis"], NUDGE_FIELDS)
    recovery_md_path = write_text(f"{DEFAULT_RECOVERY_STEM}.md", render_recovery_markdown(payload))
    recovery_json_path = write_json(
        f"{DEFAULT_RECOVERY_STEM}.json",
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "status": "workflow_durable_lane_recovery_ready",
            "review_only": True,
            "automatic_changes": False,
            "counts": {
                "rows": payload["durable_lane_recovery_count"],
                "missing_durable_lane_count": payload["missing_durable_lane_count"],
            },
            "guardrails": {
                "review_only": True,
                "automatic_changes": False,
                "thread_creation": False,
                "thread_closure": False,
                "branch_closure": False,
                "branch_rewrite": False,
                "approval_state_change": False,
                "source_enablement": False,
                "asset_downloads": False,
                "publish_ready_movement": False,
                "publishing": False,
            },
            "rows": payload["durable_lane_recovery"],
        },
    )
    recovery_csv_path = write_csv(f"{DEFAULT_RECOVERY_STEM}.csv", payload["durable_lane_recovery"], RECOVERY_FIELDS)
    return {
        "markdown": str(md_path),
        "json": str(json_path),
        "csv": str(csv_path),
        "nudge_markdown": str(nudge_md_path),
        "nudge_json": str(nudge_json_path),
        "nudge_csv": str(nudge_csv_path),
        "recovery_markdown": str(recovery_md_path),
        "recovery_json": str(recovery_json_path),
        "recovery_csv": str(recovery_csv_path),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only HSD workflow lane status dashboard.")
    parser.add_argument("--intake", default=DEFAULT_INTAKE)
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--skip-pr-lookup", action="store_true")
    parser.add_argument("--skip-worktree-lookup", action="store_true")
    parser.add_argument("--stale-after-hours", type=int, default=STALE_LANE_AFTER_HOURS)
    parser.add_argument("--as-of-utc", default="", help="Testing hook for deterministic stale-lane checks")
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
                "missing_durable_lane_count": payload["missing_durable_lane_count"],
                "restart_needed_lane_count": payload["restart_needed_lane_count"],
                "lifecycle_action_lane_count": payload["lifecycle_action_lane_count"],
                "stale_lane_count": payload["stale_lane_count"],
                "nudge_synthesis_count": payload["nudge_synthesis_count"],
                "nudge_synthesis_p1_count": payload["nudge_synthesis_p1_count"],
                "durable_lane_recovery_count": payload["durable_lane_recovery_count"],
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
