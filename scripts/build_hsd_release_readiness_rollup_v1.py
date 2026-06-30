from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, run_output_dir, write_csv, write_json, write_text
from scripts import guardrail_check


ROOT = Path(__file__).resolve().parents[1]
VERSION = "hsd-release-readiness-rollup-v1-review-only"
DEFAULT_OUTPUT_STEM = "release_readiness_guardrail_rollup"
DEFAULT_SCAN_DIR = "outputs/local/latest/files"
ROLLUP_FIELDS = [
    "check_id",
    "status",
    "detail",
    "evidence",
    "operator_next_step",
    "review_only",
    "publish_ready",
    "auto_publish",
    "paid_apis",
    "source_fetching",
    "asset_downloads",
    "automatic_downloads",
    "auto_approval",
    "approval_state_change",
    "headshot_writes",
    "approved_marker_writes",
    "publishing",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_scan_path(scan_dir: str) -> tuple[Path, str]:
    if scan_dir == DEFAULT_SCAN_DIR:
        active_run_dir = run_output_dir()
        if active_run_dir:
            return active_run_dir, repo_relative(active_run_dir)
    path = Path(scan_dir)
    resolved = path if path.is_absolute() else ROOT / path
    return resolved.resolve(), scan_dir


def git_value(args: list[str], default: str = "unknown") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return default
    if result.returncode != 0 or not result.stdout.strip():
        return default
    return result.stdout.splitlines()[0].strip() or default


def false_guardrail_fields() -> dict[str, str]:
    return {
        "publish_ready": "false",
        "auto_publish": "false",
        "paid_apis": "false",
        "source_fetching": "false",
        "asset_downloads": "false",
        "automatic_downloads": "false",
        "auto_approval": "false",
        "approval_state_change": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "publishing": "false",
    }


def row(
    check_id: str,
    status: str,
    detail: str,
    evidence: str,
    operator_next_step: str,
) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "operator_next_step": operator_next_step,
        "review_only": "true",
        **false_guardrail_fields(),
    }


def scan_latest_artifacts(scan_dir: str, config: dict[str, Any]) -> dict[str, Any]:
    path, evidence_path = resolve_scan_path(scan_dir)
    if not path.exists():
        return {
            "status": "not_found",
            "scan_dir": evidence_path,
            "scan_files_checked": 0,
            "violation_count": 0,
            "violations": [],
            "detail": "latest artifact directory is missing; run the local review workflow before release review",
        }
    scan_files_checked = sum(1 for item in path.rglob("*") if item.is_file())
    violations = guardrail_check.scan_directory(path, config)
    return {
        "status": "blocked" if violations else "passed",
        "scan_dir": evidence_path,
        "scan_files_checked": scan_files_checked,
        "violation_count": len(violations),
        "violations": [violation.as_dict() for violation in violations],
        "detail": "generated latest artifacts scanned for publish, approval, download, source-fetch, and paid-API guardrail fields",
    }


def load_conductor_audit() -> dict[str, Any]:
    path = input_path("conductor_workspace_audit.json")
    if not path.exists():
        return {
            "status": "not_found",
            "collision_blocker_count": 0,
            "workspace_hash": "",
            "detail": "conductor workspace audit artifact is missing",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return {
            "status": "blocked",
            "collision_blocker_count": 1,
            "workspace_hash": "",
            "detail": f"conductor workspace audit JSON could not be parsed: {exc}",
        }
    return {
        "status": payload.get("status") or "unknown",
        "collision_blocker_count": int(payload.get("collision_blocker_count") or 0),
        "workspace_hash": payload.get("workspace_hash") or "",
        "detail": "conductor workspace audit loaded",
    }


def load_workflow_lane_status() -> dict[str, Any]:
    path = input_path("workflow_lane_status_dashboard.json")
    if not path.exists():
        return {
            "status": "not_found",
            "stale_lane_count": 0,
            "restart_needed_lane_count": 0,
            "lifecycle_action_lane_count": 0,
            "missing_durable_lane_count": 0,
            "detail": "workflow lane status dashboard artifact is missing",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return {
            "status": "blocked",
            "stale_lane_count": 1,
            "restart_needed_lane_count": 0,
            "lifecycle_action_lane_count": 0,
            "missing_durable_lane_count": 0,
            "detail": f"workflow lane status JSON could not be parsed: {exc}",
        }
    return {
        "status": payload.get("status") or "unknown",
        "stale_lane_count": int(payload.get("stale_lane_count") or 0),
        "restart_needed_lane_count": int(payload.get("restart_needed_lane_count") or 0),
        "lifecycle_action_lane_count": int(payload.get("lifecycle_action_lane_count") or 0),
        "missing_durable_lane_count": int(payload.get("missing_durable_lane_count") or 0),
        "detail": "workflow lane status loaded",
    }


def build_payload(scan_dir: str = DEFAULT_SCAN_DIR) -> dict[str, Any]:
    config = guardrail_check.load_guardrails()
    latest_scan = scan_latest_artifacts(scan_dir, config)
    conductor_audit = load_conductor_audit()
    workflow_lane_status = load_workflow_lane_status()
    guardrail_config = {
        "version": config.get("version", "unknown"),
        "truthy_guardrail_fields": len(config.get("truthy_guardrail_fields", [])),
        "blocked_path_fragments": len(config.get("blocked_path_fragments", [])),
        "blocked_marker_suffixes": len(config.get("blocked_marker_suffixes", [])),
        "protected_asset_write_fragments": len(config.get("protected_asset_write_fragments", [])),
    }
    workflow_stale_count = int(workflow_lane_status.get("stale_lane_count") or 0)
    blocker_count = (
        latest_scan["violation_count"]
        + int(conductor_audit.get("collision_blocker_count") or 0)
        + workflow_stale_count
    )
    missing_inputs = [name for name, status in {
        "latest_artifact_scan": latest_scan["status"],
        "conductor_workspace_audit": conductor_audit["status"],
    }.items() if status == "not_found"]
    status = "blocked" if blocker_count else "needs_operator_review" if missing_inputs else "passed"
    rows = [
        row(
            "deterministic_guardrail_config",
            "passed",
            f"config_version={guardrail_config['version']}; truthy_fields={guardrail_config['truthy_guardrail_fields']}",
            "config/hsd_guardrails.json",
            "Keep deterministic guardrail config in the release evidence bundle.",
        ),
        row(
            "latest_artifact_guardrail_scan",
            latest_scan["status"],
            f"scan_files_checked={latest_scan['scan_files_checked']}; violations={latest_scan['violation_count']}",
            latest_scan["scan_dir"],
            "Run local review artifacts, then rerun this rollup." if latest_scan["status"] == "not_found" else "Stop on any violation before release review." if latest_scan["violation_count"] else "No generated latest-artifact guardrail violations found.",
        ),
        row(
            "conductor_workspace_audit",
            conductor_audit["status"],
            f"collision_blocker_count={conductor_audit['collision_blocker_count']}; workspace_hash={conductor_audit['workspace_hash'] or 'missing'}",
            "conductor_workspace_audit.json",
            "Run conductor workspace audit before release review." if conductor_audit["status"] == "not_found" else "Fix conductor collision blockers before release review." if conductor_audit["collision_blocker_count"] else "Conductor collision audit is clear.",
        ),
        row(
            "workflow_lane_stale_brake",
            "blocked" if workflow_stale_count else workflow_lane_status["status"],
            (
                f"stale_lane_count={workflow_stale_count}; "
                f"restart_needed={workflow_lane_status['restart_needed_lane_count']}; "
                f"lifecycle_actions={workflow_lane_status['lifecycle_action_lane_count']}; "
                f"missing_durable_lanes={workflow_lane_status['missing_durable_lane_count']}"
            ),
            "workflow_lane_status_dashboard.json",
            "Resolve or manually lifecycle active stale lanes before release review." if workflow_stale_count else "Run workflow lane status before release review." if workflow_lane_status["status"] == "not_found" else "No active workflow stale-lane brakes found.",
        ),
        row(
            "hard_release_guardrail_posture",
            "passed",
            "review-only artifact-only; no paid APIs, downloads, source auto-enablement, approvals, asset writes, publish-ready movement, or publishing",
            "AGENTS.md; release_readiness_guardrail_rollup.json",
            "Use this rollup as evidence only; it does not change approval, asset, source, render, or publish state.",
        ),
    ]
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "review_only": True,
        "branch": git_value(["branch", "--show-current"], "detached"),
        "head_commit": git_value(["rev-parse", "--short", "HEAD"]),
        "head_subject": git_value(["log", "-1", "--pretty=%s"]),
        "scan_dir": scan_dir,
        "blocker_count": blocker_count,
        "missing_inputs": missing_inputs,
        "guardrail_config": guardrail_config,
        "latest_artifact_scan": latest_scan,
        "conductor_workspace_audit": conductor_audit,
        "workflow_lane_status": workflow_lane_status,
        "workflow_missing_durable_lanes": int(workflow_lane_status.get("missing_durable_lane_count") or 0),
        "guardrails": {
            "review_only": True,
            "paid_apis": False,
            "source_fetching": False,
            "asset_downloads": False,
            "automatic_downloads": False,
            "auto_approval": False,
            "approval_state_change": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "publish_ready": False,
            "publishing": False,
        },
        "checks": rows,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# HSD Release-Readiness Guardrail Rollup",
        "",
        "Status: review-only release-readiness evidence artifact.",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{payload['version']}`",
        f"Audit status: `{payload['status']}`",
        f"Branch: `{payload['branch']}`",
        f"HEAD: `{payload['head_commit']}` - {payload['head_subject']}",
        f"Blocker count: `{payload['blocker_count']}`",
        "",
        "## Evidence Checks",
        "",
    ]
    for item in payload["checks"]:
        lines.append(f"- `{item['check_id']}`: `{item['status']}` - {item['detail']} ({item['evidence']})")
    lines.extend(
        [
            "",
            "## Hard Guardrail Posture",
            "",
            "- Review-only and artifact-only.",
            "- No paid APIs.",
            "- No source fetching or source auto-enablement.",
            "- No automatic downloads.",
            "- No auto-approval or approval-state changes.",
            "- No headshot writes or `.approved` marker writes.",
            "- No publish-ready lane or movement.",
            "- No publishing.",
            "",
            "## Operator Next Step",
            "",
            "Open this rollup with `conductor_workspace_audit.md` and the deterministic guardrail check output before release review. A blocked row means stop and fix the evidence issue before continuing.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_stem: str) -> dict[str, str]:
    md_path = write_text(f"{output_stem}.md", render_markdown(payload))
    json_path = write_json(f"{output_stem}.json", payload)
    csv_path = write_csv(f"{output_stem}.csv", payload["checks"], ROLLUP_FIELDS)
    return {"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the review-only HSD release-readiness guardrail rollup.")
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--scan-dir", default=DEFAULT_SCAN_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.scan_dir)
    outputs = write_outputs(payload, args.output_stem)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "blocker_count": payload["blocker_count"],
                "missing_inputs": payload["missing_inputs"],
                "outputs": outputs,
                "review_only": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["blocker_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
