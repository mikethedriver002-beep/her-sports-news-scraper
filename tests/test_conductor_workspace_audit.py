from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_hsd_conductor_workspace_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_hsd_conductor_workspace_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conductor_workspace_audit_writes_review_only_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    assert module.main([]) == 0

    manifest = json.loads((tmp_path / "run" / "conductor_workspace_audit.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((tmp_path / "run" / "conductor_workspace_audit.csv").open(newline="", encoding="utf-8")))
    markdown = (tmp_path / "run" / "conductor_workspace_audit.md").read_text(encoding="utf-8")

    assert manifest["version"] == "hsd-conductor-workspace-audit-v1-review-only"
    assert manifest["status"] == "passed"
    assert manifest["collision_blocker_count"] == 0
    assert manifest["origin_main_alignment"]["status"] == "passed"
    assert manifest["origin_main_alignment"]["blocker_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["guardrails"]["paid_apis"] is False
    assert manifest["guardrails"]["source_fetching"] is False
    assert manifest["guardrails"]["automatic_downloads"] is False
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["approval_state_change"] is False
    assert manifest["guardrails"]["headshot_writes"] is False
    assert manifest["guardrails"]["approved_marker_writes"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert manifest["guardrails"]["publishing"] is False
    assert {row["check_id"] for row in rows} >= {
        "directive_schema_and_example",
        "current_origin_main_alignment",
        "shared_mutable_directive_paths",
        "committed_runtime_state",
    }
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert "Status: review-only conductor reliability artifact." in markdown
    assert "Current origin/main alignment: `passed`" in markdown
    assert "No automatic downloads." in markdown
    assert "No publish-ready lane." in markdown


def test_conductor_workspace_audit_detects_forbidden_shared_directive_file(tmp_path: Path) -> None:
    module = load_module()
    conductor = tmp_path / "conductor"
    conductor.mkdir()
    (conductor / "directive.json").write_text("{}", encoding="utf-8")

    audit = module.collect_shared_directive_audit(tmp_path)

    assert audit["present_shared_directive_paths"] == ["conductor/directive.json"]
    assert audit["present_shared_directive_count"] == 1


def test_conductor_workspace_audit_blocks_committed_runtime_state(monkeypatch) -> None:
    module = load_module()

    def fake_git_lines(args: list[str]) -> list[str]:
        if args == ["ls-files", "conductor/runtime"]:
            return [
                "conductor/runtime/.gitkeep",
                "conductor/runtime/workflow-overhaul-status.json",
            ]
        return []

    monkeypatch.setattr(module, "git_lines", fake_git_lines)

    audit = module.collect_runtime_tracking_audit()

    assert audit["tracked_runtime_state_paths"] == ["conductor/runtime/workflow-overhaul-status.json"]
    assert audit["tracked_runtime_state_count"] == 1


def test_conductor_workspace_audit_blocks_stale_origin_main_alignment(monkeypatch) -> None:
    module = load_module()

    def fake_git_value(args: list[str], default: str = "unknown") -> str:
        values = {
            ("rev-parse", "--short", "HEAD"): "feature123",
            ("rev-parse", "--short", "origin/main"): "main999",
            ("merge-base", "HEAD", "origin/main"): "oldbase1000000000000000000000000000000000000",
        }
        return values.get(tuple(args), default)

    monkeypatch.setattr(module, "git_value", fake_git_value)

    alignment = module.collect_origin_main_alignment()

    assert alignment["status"] == "blocked"
    assert alignment["blocker_count"] == 1
    assert alignment["head_commit"] == "feature123"
    assert alignment["origin_main_commit"] == "main999"
    assert alignment["merge_base_commit"] == "oldbase1"
    assert "rebase or recreate" in alignment["detail"]


def test_conductor_workspace_hash_is_stable_for_same_audit_payload(monkeypatch) -> None:
    module = load_module()
    payload = {
        "version": module.VERSION,
        "git_state": {"branch": "codex/workflow-test", "head_commit": "abc123", "dirty_count": 0},
        "origin_main_alignment": {
            "status": "passed",
            "blocker_count": 0,
            "head_commit": "abc123",
            "origin_main_commit": "abc123",
            "merge_base_commit": "abc123",
            "detail": "branch contains current origin/main",
        },
        "directive_validation": {"status": "passed", "blockers": []},
        "shared_directive_audit": {"present_shared_directive_paths": [], "present_shared_directive_count": 0},
        "runtime_tracking_audit": {"tracked_runtime_state_paths": [], "tracked_runtime_state_count": 0},
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

    assert module.workspace_hash(payload) == module.workspace_hash(dict(reversed(list(payload.items()))))


def test_local_runner_and_command_center_collect_conductor_workspace_audit() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")

    assert "scripts\\audit_hsd_conductor_workspace_v1.py" in runner
    assert "conductor_workspace_audit.md" in runner
    assert "conductor_workspace_audit.csv" in runner
    assert "conductor_workspace_audit.json" in runner
    assert "(\"Decision\", \"Conductor workspace audit\", \"conductor_workspace_audit.md\")" in command_center
