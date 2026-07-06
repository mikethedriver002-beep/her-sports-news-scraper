from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=repo_root(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def require_ok(step_name: str, result: dict[str, Any]) -> None:
    if result["returncode"] == 0:
        return
    payload = {
        "ok": False,
        "failed_step": step_name,
        "result": result,
    }
    print(json.dumps(payload, indent=2))
    raise SystemExit(1)


def current_branch() -> str:
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    require_ok("git rev-parse --abbrev-ref HEAD", result)
    return result["stdout"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run common git and gh repo actions in a shell-safe sequence."
    )
    parser.add_argument(
        "--add",
        action="append",
        default=[],
        help="Path to stage. Repeat to stage multiple paths.",
    )
    parser.add_argument(
        "--message",
        default="",
        help="Commit message. If omitted, no commit is created.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the current branch after a successful commit or as a standalone step.",
    )
    parser.add_argument(
        "--create-draft-pr",
        action="store_true",
        help="Create a draft PR with gh after push or on an already-pushed branch.",
    )
    parser.add_argument(
        "--base",
        default="main",
        help="Base branch for gh pr create. Defaults to main.",
    )
    parser.add_argument(
        "--title",
        default="",
        help="PR title for gh pr create.",
    )
    parser.add_argument(
        "--body",
        default="",
        help="Inline PR body for gh pr create.",
    )
    parser.add_argument(
        "--body-file",
        default="",
        help="Optional file containing the PR body.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    steps: list[dict[str, Any]] = []

    if args.body and args.body_file:
        raise SystemExit("Use either --body or --body-file, not both.")

    if args.create_draft_pr and not args.title:
        raise SystemExit("--create-draft-pr requires --title.")

    branch = current_branch()

    if args.add:
        add_result = run_command(["git", "add", "--", *args.add])
        steps.append({"step": "git_add", "result": add_result})
        require_ok("git add", add_result)

    if args.message:
        commit_result = run_command(["git", "commit", "-m", args.message])
        steps.append({"step": "git_commit", "result": commit_result})
        require_ok("git commit", commit_result)

    if args.push:
        push_result = run_command(["git", "push", "-u", "origin", branch])
        steps.append({"step": "git_push", "result": push_result})
        require_ok("git push", push_result)

    if args.create_draft_pr:
        pr_command = [
            "gh",
            "pr",
            "create",
            "--draft",
            "--base",
            args.base,
            "--head",
            branch,
            "--title",
            args.title,
        ]
        if args.body_file:
            pr_command.extend(["--body-file", args.body_file])
        else:
            pr_command.extend(["--body", args.body])
        pr_result = run_command(pr_command)
        steps.append({"step": "gh_pr_create", "result": pr_result})
        require_ok("gh pr create", pr_result)

    payload = {
        "ok": True,
        "branch": branch,
        "steps": steps,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
