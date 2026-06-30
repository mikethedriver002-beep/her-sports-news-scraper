from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_external_research_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_external_research_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str = "fixture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_builds_review_only_gemini_renderer_packet_with_email_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    write(tmp_path / "docs/HSD_OPERATING_WORKFLOW_V1.md", "# Workflow")
    write(tmp_path / "docs/HSD_EXTERNAL_RESEARCH_PACKET_TEMPLATE.md", "# Template")
    write(tmp_path / "docs/HSD_RESEARCH_ALERT_EMAIL_TEMPLATE.md", "# Email")
    write(tmp_path / "docs/HSD_REVIEW_ONLY_ASSET_DOWNLOAD_POLICY.md", "# Download policy")
    write(tmp_path / "launch_operating_sop.md", "# SOP")
    write(tmp_path / "launch_command_center.md", "# Command")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.html", "<html>center</html>")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.md", "# Center")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.json", '{"status":"ok"}')
    write(tmp_path / "outputs/local/latest/files/render_handoff_top_packet/draft_preview.png", "png-bytes")
    write(tmp_path / "outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_visual_contact_sheet.png", "sheet")
    write(tmp_path / "outputs/local/latest/files/manual_review_renderer_manifest.json", '{"version":"renderer"}')

    module = load_module()
    assert (
        module.main(
            [
                "--tool",
                "gemini_pro",
                "--lane",
                "renderer",
                "--packet-name",
                "renderer-research",
                "--short-task",
                "compare latest render",
                "--question",
                "Critique the latest render and return five packets.",
                "--head-commit",
                "abc123",
            ]
        )
        == 0
    )

    packet_dir = tmp_path / "run/external_research_packets/renderer-research"
    manifest = json.loads((packet_dir / "packet_manifest.json").read_text(encoding="utf-8"))
    email = (packet_dir / "research_alert_email.md").read_text(encoding="utf-8")
    gmail_payload = json.loads((packet_dir / "research_alert_gmail_payload.json").read_text(encoding="utf-8"))
    latest = json.loads((tmp_path / "run/external_research_packet_latest.json").read_text(encoding="utf-8"))
    archive = packet_dir.with_suffix(".zip")

    assert manifest["version"] == "hsd-external-research-packet-v1-review-only"
    assert manifest["tool"] == "gemini_pro"
    assert manifest["lane"] == "renderer"
    assert manifest["head_commit"] == "abc123"
    assert manifest["review_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["automatic_downloads"] is False
    assert manifest["auto_approval"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["included_file_count"] >= 10
    assert archive.exists()
    assert "Tool to use:\nGemini Pro" in email
    assert "Packet to upload:" in email
    assert "Critique the latest render and return five packets." in email
    assert gmail_payload["to"] == "michael@brieffactory.com"
    assert gmail_payload["send_policy"] == "draft_by_default_send_only_when_time_sensitive"
    assert gmail_payload["attachments"] == [str(archive)]
    assert latest["zip_path"] == str(archive)
    with zipfile.ZipFile(archive) as zipped:
        names = set(zipped.namelist())
    assert "README.md" in names
    assert "research_alert_email.md" in names
    assert "research_alert_gmail_payload.json" in names
    assert "files/outputs/local/latest/files/render_handoff_top_packet/draft_preview.png" in names
    assert "files/outputs/local/latest/files/operator_command_center.html" in names


def test_packet_builder_accepts_manual_include_and_keeps_missing_visible(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    write(tmp_path / "docs/HSD_OPERATING_WORKFLOW_V1.md", "# Workflow")
    write(tmp_path / "custom/context.md", "# Custom")

    module = load_module()
    payload = module.build_packet(
        module.parse_args(
            [
                "--tool",
                "chatgpt_pro",
                "--lane",
                "workflow",
                "--packet-name",
                "workflow-packet",
                "--include",
                "custom/context.md",
                "--include",
                "missing/file.md",
            ]
        )
    )

    packet_dir = Path(payload["packet_dir"])
    manifest = json.loads((packet_dir / "packet_manifest.json").read_text(encoding="utf-8"))
    readme = (packet_dir / "README.md").read_text(encoding="utf-8")

    assert "custom/context.md" in {item["path"] for item in manifest["included_files"]}
    assert "missing/file.md" in manifest["missing_files"]
    assert "- `missing/file.md`" in readme
    assert manifest["send_policy"] == "draft_by_default_send_only_when_time_sensitive"


def test_external_research_packet_skips_timestamp_only_readme_rewrites(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    write(tmp_path / "docs/HSD_OPERATING_WORKFLOW_V1.md", "# Workflow")
    write(tmp_path / "docs/HSD_EXTERNAL_RESEARCH_PACKET_TEMPLATE.md", "# Template")
    write(tmp_path / "docs/HSD_RESEARCH_ALERT_EMAIL_TEMPLATE.md", "# Email")
    write(tmp_path / "docs/HSD_REVIEW_ONLY_ASSET_DOWNLOAD_POLICY.md", "# Download policy")
    write(tmp_path / "launch_operating_sop.md", "# SOP")
    write(tmp_path / "launch_command_center.md", "# Command")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.html", "<html>center</html>")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.md", "# Center")
    write(tmp_path / "outputs/local/latest/files/operator_command_center.json", '{"status":"ok"}')

    module = load_module()
    args = module.parse_args(
        [
            "--tool",
            "chatgpt_pro",
            "--lane",
            "workflow",
            "--packet-name",
            "workflow-packet",
            "--head-commit",
            "abc123",
        ]
    )

    payload = module.build_packet(args)
    packet_dir = Path(payload["packet_dir"])
    readme_path = packet_dir / "README.md"
    first_readme = readme_path.read_text(encoding="utf-8")

    payload = module.build_packet(args)

    assert Path(payload["packet_dir"]) == packet_dir
    assert readme_path.read_text(encoding="utf-8") == first_readme
