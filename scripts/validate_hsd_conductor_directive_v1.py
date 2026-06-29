from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "conductor" / "directive.schema.json"
DEFAULT_DIRECTIVE = ROOT / "conductor" / "directive.example.json"
VERSION = "hsd-conductor-directive-validator-v1"

FORBIDDEN_SHARED_DIRECTIVE_PATHS = {
    "conductor/directive.json",
    "conductor/runtime/directive.json",
    "directive.json",
}

DIRECTIVE_PATH_RE = re.compile(
    r"^conductor/directives/"
    r"(runs/[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]*|"
    r"branches/[a-z0-9][a-z0-9._/-]*/[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9-]*)"
    r"\.json$"
)

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "directive_id",
    "directive_path",
    "created_at_utc",
    "target_branch",
    "base_ref",
    "lane",
    "branch_collision_policy",
    "guardrails",
    "operator_notes",
}

REQUIRED_GUARDRAILS = {
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
}


def repo_relative(path: str | Path) -> str:
    value = str(path).replace("\\", "/")
    root = str(ROOT).replace("\\", "/")
    if value.startswith(root + "/"):
        value = value[len(root) + 1 :]
    return value.lstrip("./")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_directive_path(path: str | Path) -> list[str]:
    normalized = repo_relative(path)
    blockers: list[str] = []
    if normalized in FORBIDDEN_SHARED_DIRECTIVE_PATHS:
        blockers.append(f"shared_mutable_directive_path_forbidden:{normalized}")
    if not DIRECTIVE_PATH_RE.match(normalized):
        blockers.append(f"directive_path_not_immutable_snapshot:{normalized}")
    return blockers


def validate_schema_file(schema: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED_TOP_LEVEL - required)
    if missing:
        blockers.append(f"schema_missing_required_fields:{','.join(missing)}")

    path_schema = schema.get("properties", {}).get("directive_path", {})
    forbidden = set(path_schema.get("not", {}).get("enum", []))
    missing_forbidden = sorted(FORBIDDEN_SHARED_DIRECTIVE_PATHS - forbidden)
    if missing_forbidden:
        blockers.append(f"schema_missing_forbidden_shared_paths:{','.join(missing_forbidden)}")

    guardrail_props = schema.get("properties", {}).get("guardrails", {}).get("properties", {})
    for key, expected in REQUIRED_GUARDRAILS.items():
        actual = guardrail_props.get(key, {}).get("const")
        if actual is not expected:
            blockers.append(f"schema_guardrail_const_mismatch:{key}")

    collision_policy = schema.get("properties", {}).get("branch_collision_policy", {}).get("properties", {})
    if collision_policy.get("shared_mutable_directive_path_allowed", {}).get("const") is not False:
        blockers.append("schema_allows_shared_mutable_directive_path")
    return blockers


def validate_directive(directive: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(directive))
    if missing:
        blockers.append(f"directive_missing_required_fields:{','.join(missing)}")

    if directive.get("schema_version") != "hsd-conductor-directive-v1":
        blockers.append("directive_schema_version_invalid")

    blockers.extend(validate_directive_path(str(directive.get("directive_path", ""))))

    branch_policy = directive.get("branch_collision_policy", {})
    if branch_policy.get("shared_mutable_directive_path_allowed") is not False:
        blockers.append("directive_allows_shared_mutable_directive_path")
    if branch_policy.get("runtime_state") != "conductor/runtime_only_not_committed":
        blockers.append("directive_runtime_state_not_uncommitted")
    if branch_policy.get("required_git_start") != "current_origin_main":
        blockers.append("directive_missing_current_origin_main_start")

    guardrails = directive.get("guardrails", {})
    for key, expected in REQUIRED_GUARDRAILS.items():
        if guardrails.get(key) is not expected:
            blockers.append(f"directive_guardrail_mismatch:{key}")

    return blockers


def validate_files(schema_path: Path, directive_path: Path) -> dict[str, Any]:
    blockers: list[str] = []
    schema = load_json(schema_path)
    directive = load_json(directive_path)
    blockers.extend(validate_schema_file(schema))
    blockers.extend(validate_directive(directive))
    return {
        "version": VERSION,
        "schema_path": repo_relative(schema_path),
        "directive_path": repo_relative(directive_path),
        "status": "blocked" if blockers else "passed",
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HSD conductor directive schema and immutable snapshots.")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Directive schema JSON path")
    parser.add_argument("--directive", default=str(DEFAULT_DIRECTIVE), help="Directive snapshot JSON path")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    result = validate_files(Path(args.schema), Path(args.directive))
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["blockers"]:
        print(f"{VERSION}: blocked")
        for blocker in result["blockers"]:
            print(f"- {blocker}")
    else:
        print(f"{VERSION}: passed")
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
