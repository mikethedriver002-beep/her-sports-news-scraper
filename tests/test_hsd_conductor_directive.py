from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.validate_hsd_conductor_directive_v1 as validator


def test_example_directive_passes_collision_and_review_only_guards() -> None:
    result = validator.validate_files(validator.DEFAULT_SCHEMA, validator.DEFAULT_DIRECTIVE)

    assert result["status"] == "passed"
    assert result["blockers"] == []


def test_shared_mutable_directive_paths_are_rejected() -> None:
    assert validator.validate_directive_path("conductor/directive.json") == [
        "shared_mutable_directive_path_forbidden:conductor/directive.json",
        "directive_path_not_immutable_snapshot:conductor/directive.json",
    ]
    assert validator.validate_directive_path("conductor/runtime/directive.json") == [
        "shared_mutable_directive_path_forbidden:conductor/runtime/directive.json",
        "directive_path_not_immutable_snapshot:conductor/runtime/directive.json",
    ]


def test_branch_scoped_and_run_scoped_directive_paths_are_allowed() -> None:
    assert validator.validate_directive_path(
        "conductor/directives/runs/20260629T120000Z-workflow-brake.json"
    ) == []
    assert validator.validate_directive_path(
        "conductor/directives/branches/codex/hsd-conductor-directive-brake/20260629T120000Z-workflow-brake.json"
    ) == []


def test_directive_cannot_flip_review_only_guardrails(tmp_path: Path) -> None:
    directive = json.loads(validator.DEFAULT_DIRECTIVE.read_text(encoding="utf-8"))
    directive["guardrails"]["paid_apis"] = True
    directive["guardrails"]["publish_ready"] = True
    directive_path = tmp_path / "bad_directive.json"
    directive_path.write_text(json.dumps(directive), encoding="utf-8")

    result = validator.validate_files(validator.DEFAULT_SCHEMA, directive_path)

    assert result["status"] == "blocked"
    assert "directive_guardrail_mismatch:paid_apis" in result["blockers"]
    assert "directive_guardrail_mismatch:publish_ready" in result["blockers"]


def test_validator_cli_outputs_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_hsd_conductor_directive_v1.py",
            "--format",
            "json",
        ],
        cwd=validator.ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "passed"
    assert payload["blockers"] == []
