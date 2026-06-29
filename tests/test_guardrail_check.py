from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.guardrail_check as guardrail


def test_diff_scan_allows_guardrail_prohibition_text() -> None:
    config = guardrail.load_guardrails()
    diff = """diff --git a/docs/example.md b/docs/example.md
--- a/docs/example.md
+++ b/docs/example.md
@@ -0,0 +1,2 @@
+- No publish-ready lane.
+- `download_approved=yes` remains human-edited only.
"""
    assert guardrail.scan_diff_content(diff, config) == []


def test_diff_scan_blocks_truthy_guardrail_assignment() -> None:
    config = guardrail.load_guardrails()
    diff = """diff --git a/bad.py b/bad.py
--- a/bad.py
+++ b/bad.py
@@ -0,0 +1,2 @@
+auto_approval = True
+paid_apis = "yes"
"""
    violations = guardrail.scan_diff_content(diff, config)
    assert [v.code for v in violations] == ["truthy_guardrail_diff", "truthy_guardrail_diff"]


def test_diff_scan_allows_truthy_guardrail_examples_in_tests_and_docs() -> None:
    config = guardrail.load_guardrails()
    diff = """diff --git a/tests/example.py b/tests/example.py
--- a/tests/example.py
+++ b/tests/example.py
@@ -0,0 +1,2 @@
+auto_approval = True
diff --git a/docs/example.md b/docs/example.md
--- a/docs/example.md
+++ b/docs/example.md
@@ -0,0 +1,2 @@
+Example blocked value: `paid_apis=true`.
"""
    assert guardrail.scan_diff_content(diff, config) == []


def test_changed_path_scan_blocks_publish_ready_and_approved_marker() -> None:
    config = guardrail.load_guardrails()
    violations = guardrail.scan_changed_paths(
        [
            "outputs/local/publish-ready/card.png",
            "assets/leagues/wnba/athletes/example/headshot.png.approved",
        ],
        config,
    )
    codes = [v.code for v in violations]
    assert "blocked_path" in codes
    assert "blocked_marker" in codes
    assert "protected_asset_write" in codes


def test_changed_path_scan_allows_safe_docs_and_tests_examples() -> None:
    config = guardrail.load_guardrails()
    violations = guardrail.scan_changed_paths(
        [
            "docs/no-publish-ready-lane-example.md",
            "docs/examples/assets/headshots/path-example.md",
            "tests/fixtures/example.approved",
            "tests/fixtures/assets/headshots/example.png",
        ],
        config,
    )

    assert violations == []


def test_scan_directory_blocks_truthy_generated_csv(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.csv"
    artifact.write_text("row_id,review_only,auto_publish\n1,true,true\n", encoding="utf-8")
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    assert [(v.code, v.path, v.line) for v in violations] == [
        ("truthy_guardrail_csv", str(artifact).replace("\\", "/"), 2)
    ]


def test_scan_directory_blocks_truthy_generated_json(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({"rows": [{"publish_ready": True}]}), encoding="utf-8")
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    assert len(violations) == 1
    assert violations[0].code == "truthy_guardrail_json"
    assert "publish_ready" in violations[0].message


def test_cli_scan_dir_outputs_json(tmp_path: Path) -> None:
    relative = tmp_path.relative_to(guardrail.ROOT) if tmp_path.is_relative_to(guardrail.ROOT) else tmp_path
    result = subprocess.run(
        [
            sys.executable,
            "scripts/guardrail_check.py",
            "--scan-dir",
            str(relative),
            "--format",
            "json",
        ],
        cwd=guardrail.ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASSED"
