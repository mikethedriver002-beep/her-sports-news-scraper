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


def test_scan_directory_allows_complete_human_action_photo_download_intake_row(tmp_path: Path) -> None:
    artifact = (
        tmp_path
        / "data"
        / "asset_registry"
        / "action_photo_candidates"
        / "review_only_action_photo_research_return_intake_v1.csv"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "\n".join(
            [
                "candidate_queue_id,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,download_approved,quarantine_target_hint,review_only,publish_ready",
                "APQ001,https://example.com/source,wnba:caitlin-clark,official_review_needed,confirmed_official,review_only_action_photo_candidate_quarantine_decision_prep,yes,data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/operator_fill_required.jpg,true,false",
            ]
        ),
        encoding="utf-8",
    )
    config = guardrail.load_guardrails()

    assert guardrail.scan_directory(tmp_path, config) == []


def test_scan_directory_blocks_incomplete_human_action_photo_download_intake_row(tmp_path: Path) -> None:
    artifact = (
        tmp_path
        / "data"
        / "asset_registry"
        / "action_photo_candidates"
        / "review_only_action_photo_research_return_intake_v1.csv"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "\n".join(
            [
                "candidate_queue_id,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,download_approved,quarantine_target_hint,review_only,publish_ready",
                "APQ001,,wnba:caitlin-clark,official_review_needed,confirmed_official,review_only_action_photo_candidate_quarantine_decision_prep,yes,assets/not-quarantine/apq001.jpg,true,false",
            ]
        ),
        encoding="utf-8",
    )
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    assert [(violation.code, violation.line) for violation in violations] == [("truthy_guardrail_csv", 2)]


def test_scan_directory_blocks_truthy_generated_json(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({"rows": [{"publish_ready": True}]}), encoding="utf-8")
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    assert len(violations) == 1
    assert violations[0].code == "truthy_guardrail_json"
    assert "publish_ready" in violations[0].message


def test_scan_directory_blocks_truthy_generated_markdown_and_html(tmp_path: Path) -> None:
    markdown = tmp_path / "artifact.md"
    markdown.write_text(
        "\n".join(
            [
                "# Generated Artifact",
                "publish_ready: true",
                "download_approved yes",
            ]
        ),
        encoding="utf-8",
    )
    html = tmp_path / "artifact.html"
    html.write_text("<p>auto_publish = true</p><p>move_files true</p>", encoding="utf-8")
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    codes = [violation.code for violation in violations]
    assert codes.count("truthy_guardrail_text") == 4
    assert {violation.path for violation in violations} == {
        str(markdown).replace("\\", "/"),
        str(html).replace("\\", "/"),
    }


def test_scan_directory_blocks_generated_text_path_fragments_and_markers(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.md"
    artifact.write_text(
        "\n".join(
            [
                "publish_path: outputs/local/publish-ready/card.png",
                "marker_path: assets/leagues/wnba/athletes/example/headshot.png.approved",
                "write_target: assets/headshots/example.png",
            ]
        ),
        encoding="utf-8",
    )
    config = guardrail.load_guardrails()

    violations = guardrail.scan_directory(tmp_path, config)

    codes = [violation.code for violation in violations]
    assert "blocked_path_text" in codes
    assert "blocked_marker_text" in codes
    assert "protected_asset_text" in codes


def test_scan_directory_text_scan_allows_docs_tests_and_quarantine_exceptions(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "example.md"
    docs.parent.mkdir()
    docs.write_text("Example blocked value: publish_ready: true\n", encoding="utf-8")
    tests = tmp_path / "tests" / "fixture.html"
    tests.parent.mkdir()
    tests.write_text("marker_path: assets/leagues/wnba/example.png.approved\n", encoding="utf-8")
    quarantine = tmp_path / "artifact.md"
    quarantine.write_text("candidate: data/assets/quarantine/review_only_candidates/example.jpg\n", encoding="utf-8")
    config = guardrail.load_guardrails()

    assert guardrail.scan_directory(tmp_path, config) == []


def test_scan_directory_text_scan_allows_documented_human_intake_asset_registry_examples(tmp_path: Path) -> None:
    intake = tmp_path / "data" / "asset_registry" / "manual_intake.md"
    intake.parent.mkdir(parents=True)
    intake.write_text(
        "\n".join(
            [
                "- `download_approved=yes` without all local-download-law fields is rejected.",
                "- Keep `approved_marker_path` blank until human review; do not create `.approved` markers.",
                "- `publish_ready=true` in pasted notes must be rejected.",
            ]
        ),
        encoding="utf-8",
    )
    config = guardrail.load_guardrails()

    assert guardrail.scan_directory(tmp_path, config) == []


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
