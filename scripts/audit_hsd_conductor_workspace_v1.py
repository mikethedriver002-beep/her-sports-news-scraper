from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_csv, write_json, write_text
from scripts import validate_hsd_conductor_directive_v1 as directive_validator


ROOT = Path(__file__).resolve().parents[1]
VERSION = "hsd-conductor-workspace-audit-v1-review-only"
DEFAULT_OUTPUT_STEM = "conductor_workspace_audit"
FORBIDDEN_SHARED_DIRECTIVE_PATHS = sorted(directive_validator.FORBIDDEN_SHARED_DIRECTIVE_PATHS)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_relative(path: str | Path, root: Path = ROOT) -> str:
    value = str(path).replace("\\", "/")
    root_value = str(root).replace("\\", "/")
    if value.startswith(root_value + "/"):
        value = value[len(root_value) + 1 :]
    return value.lstrip("./")


def run_command(args: list[str], cwd: Path = ROOT) -> tuple[int, str]:
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


def git_lines(args: list[str]) -> list[str]:
    code, output = run_command(["git", *args])
    if code != 0 or not output:
        return []
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def collect_git_state() -> dict[str, Any]:
    status_lines = git_lines(["status", "--short"])
    untracked = git_lines(["ls-files", "--others", "--exclude-standard"])
    return {
        "branch": git_value(["branch", "--show-current"], "detached"),
        "head_commit": git_value(["rev-parse", "--short", "HEAD"]),
        "head_subject": git_value(["log", "-1", "--pretty=%s"]),
        "dirty": bool(status_lines),
        "dirty_count": len(status_lines),
        "dirty_paths": status_lines,
        "untracked_count": len(untracked),
    }


def collect_runtime_tracking_audit() -> dict[str, Any]:
    tracked_runtime = [
        path
        for path in git_lines(["ls-files", "conductor/runtime"])
        if path != "conductor/runtime/.gitkeep"
    ]
    return {
        "tracked_runtime_state_paths": tracked_runtime,
        "tracked_runtime_state_count": len(tracked_runtime),
    }


def collect_shared_directive_audit(root: Path = ROOT) -> dict[str, Any]:
    present = [path for path in FORBIDDEN_SHARED_DIRECTIVE_PATHS if (root / path).exists()]
    return {
        "forbidden_shared_directive_paths": FORBIDDEN_SHARED_DIRECTIVE_PATHS,
        "present_shared_directive_paths": present,
        "present_shared_directive_count": len(present),
    }


def collect_directive_validation() -> dict[str, Any]:
    return directive_validator.validate_files(
        directive_validator.DEFAULT_SCHEMA,
        directive_validator.DEFAULT_DIRECTIVE,
    )


def workspace_hash(payload: dict[str, Any]) -> str:
    hash_payload = {
        "version": payload["version"],
        "git_state": payload["git_state"],
        "directive_validation": payload["directive_validation"],
        "shared_directive_audit": payload["shared_directive_audit"],
        "runtime_tracking_audit": payload["runtime_tracking_audit"],
        "guardrails": payload["guardrails"],
    }
    encoded = json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def build_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    directive_blockers = payload["directive_validation"].get("blockers", [])
    shared_paths = payload["shared_directive_audit"]["present_shared_directive_paths"]
    runtime_paths = payload["runtime_tracking_audit"]["tracked_runtime_state_paths"]
    dirty_count = payload["git_state"]["dirty_count"]
    status = payload["status"]
    return [
        {
            "check_id": "git_workspace",
            "status": "needs_operator_review" if dirty_count else "passed",
            "detail": f"branch={payload['git_state']['branch']}; head={payload['git_state']['head_commit']}; dirty_count={dirty_count}",
            "blocker_count": "0",
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "check_id": "directive_schema_and_example",
            "status": "blocked" if directive_blockers else "passed",
            "detail": ";".join(directive_blockers) or "directive schema and example keep immutable brake guardrails",
            "blocker_count": str(len(directive_blockers)),
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "check_id": "shared_mutable_directive_paths",
            "status": "blocked" if shared_paths else "passed",
            "detail": ";".join(shared_paths) or "no forbidden shared directive file exists",
            "blocker_count": str(len(shared_paths)),
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "check_id": "committed_runtime_state",
            "status": "blocked" if runtime_paths else "passed",
            "detail": ";".join(runtime_paths) or "no committed conductor runtime state beyond .gitkeep",
            "blocker_count": str(len(runtime_paths)),
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "check_id": "conductor_workspace_audit_summary",
            "status": status,
            "detail": f"workspace_hash={payload['workspace_hash']}; collision_blocker_count={payload['collision_blocker_count']}",
            "blocker_count": str(payload["collision_blocker_count"]),
            "review_only": "true",
            "publish_ready": "false",
        },
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    git_state = payload["git_state"]
    lines = [
        "# HSD Conductor Workspace Audit",
        "",
        "Status: review-only conductor reliability artifact.",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{payload['version']}`",
        f"Workspace hash: `{payload['workspace_hash']}`",
        f"Audit status: `{payload['status']}`",
        "",
        "## Repo State",
        "",
        f"- Branch: `{git_state['branch']}`",
        f"- HEAD: `{git_state['head_commit']}` - {git_state['head_subject']}",
        f"- Dirty paths: `{git_state['dirty_count']}`",
        f"- Untracked paths: `{git_state['untracked_count']}`",
        "",
        "## Collision Brakes",
        "",
        f"- Directive validation: `{payload['directive_validation']['status']}`",
        f"- Directive blockers: `{len(payload['directive_validation']['blockers'])}`",
        f"- Forbidden shared directive files present: `{payload['shared_directive_audit']['present_shared_directive_count']}`",
        f"- Committed runtime state files: `{payload['runtime_tracking_audit']['tracked_runtime_state_count']}`",
        f"- Total collision blockers: `{payload['collision_blocker_count']}`",
        "",
        "## Guardrail Posture",
        "",
        "- Review-only conductor audit.",
        "- No paid APIs.",
        "- No source fetching.",
        "- No automatic downloads.",
        "- No auto-approval.",
        "- No approval-state changes.",
        "- No headshot writes.",
        "- No `.approved` markers.",
        "- No publish-ready lane.",
        "- No publishing.",
        "",
        "## Operator Cue",
        "",
        "Use this audit before opening or continuing workflow-overhaul conductor lanes. A blocked row means stop and fix the repo-visible brake/collision issue before starting a concurrent lane.",
    ]
    if git_state["dirty_paths"]:
        lines.extend(["", "## Dirty Path Snapshot", ""])
        lines.extend(f"- `{path}`" for path in git_state["dirty_paths"][:25])
        if len(git_state["dirty_paths"]) > 25:
            lines.append(f"- ... {len(git_state['dirty_paths']) - 25} more")
    return "\n".join(lines) + "\n"


def build_payload() -> dict[str, Any]:
    directive_validation = collect_directive_validation()
    shared_directive_audit = collect_shared_directive_audit()
    runtime_tracking_audit = collect_runtime_tracking_audit()
    collision_blocker_count = (
        len(directive_validation.get("blockers", []))
        + shared_directive_audit["present_shared_directive_count"]
        + runtime_tracking_audit["tracked_runtime_state_count"]
    )
    payload: dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "blocked" if collision_blocker_count else "passed",
        "review_only": True,
        "git_state": collect_git_state(),
        "directive_validation": directive_validation,
        "shared_directive_audit": shared_directive_audit,
        "runtime_tracking_audit": runtime_tracking_audit,
        "collision_blocker_count": collision_blocker_count,
        "guardrails": {
            "review_only": True,
            "paid_apis": False,
            "source_fetching": False,
            "automatic_downloads": False,
            "auto_approval": False,
            "approval_state_change": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "publish_ready": False,
            "publishing": False,
        },
    }
    payload["workspace_hash"] = workspace_hash(payload)
    payload["checks"] = build_rows(payload)
    return payload


def write_outputs(payload: dict[str, Any], output_stem: str) -> dict[str, str]:
    md_path = write_text(f"{output_stem}.md", render_markdown(payload))
    json_path = write_json(f"{output_stem}.json", payload)
    csv_path = write_csv(
        f"{output_stem}.csv",
        payload["checks"],
        ["check_id", "status", "detail", "blocker_count", "review_only", "publish_ready"],
    )
    return {"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only HSD conductor workspace audit.")
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    outputs = write_outputs(payload, args.output_stem)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "workspace_hash": payload["workspace_hash"],
                "collision_blocker_count": payload["collision_blocker_count"],
                "dirty_count": payload["git_state"]["dirty_count"],
                "outputs": outputs,
                "review_only": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["collision_blocker_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
