from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_research_alert_draft_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_research_alert_draft_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_builds_review_only_research_alert_email_and_prompt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    assert (
        module.main(
            [
                "--tool",
                "gemini_pro",
                "--lane",
                "renderer",
                "--short-task",
                "compare latest render to references",
                "--packet-path",
                r"C:\HSD\packet.zip",
                "--alert-name",
                "renderer-alert",
                "--head-commit",
                "abc123",
            ]
        )
        == 0
    )

    alert_dir = tmp_path / "run" / "research_alert_drafts" / "renderer-alert"
    manifest = json.loads((alert_dir / "research_alert_manifest.json").read_text(encoding="utf-8"))
    gmail_payload = json.loads((alert_dir / "research_alert_gmail_payload.json").read_text(encoding="utf-8"))
    latest = json.loads((tmp_path / "run" / "research_alert_draft_latest.json").read_text(encoding="utf-8"))
    email = (alert_dir / "research_alert_email.md").read_text(encoding="utf-8")
    prompt = (alert_dir / "prompt_to_paste.md").read_text(encoding="utf-8")

    assert manifest["version"] == "hsd-research-alert-draft-v1-review-only"
    assert manifest["status"] == "research_alert_draft_ready"
    assert manifest["tool"] == "gemini_pro"
    assert manifest["lane"] == "renderer"
    assert manifest["repo_head"] == "abc123"
    assert manifest["review_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["automatic_downloads"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["send_policy"] == "draft_by_default_no_automatic_send"
    assert "Tool to use:\nGemini Pro" in email
    assert "Packet to upload:\nC:\\HSD\\packet.zip" in email
    assert "Prompt file:" in email
    assert "Prompt to paste:" in email
    assert "You are advising HSD from a review-only research packet." in email
    assert "Five PR-sized packets" in prompt
    assert "No automatic downloads." in prompt
    assert gmail_payload["to"] == "michael@brieffactory.com"
    assert gmail_payload["attachments"] == [r"C:\HSD\packet.zip"]
    assert gmail_payload["requires_human_or_conductor_send"] is True
    assert latest["email_draft_path"] == str(alert_dir / "research_alert_email.md")


def test_research_alert_accepts_custom_prompt_without_attachment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    payload = module.build_payload(
        module.parse_args(
            [
                "--tool",
                "chatgpt_pro",
                "--lane",
                "workflow",
                "--short-task",
                "rank conductor bottlenecks",
                "--prompt",
                "Rank the top workflow stalls and return five safe packets.",
                "--why-now",
                "The conductor needs a short outside critique before opening more lanes.",
                "--alert-name",
                "workflow-alert",
                "--head-commit",
                "def456",
            ]
        )
    )
    outputs = module.write_outputs(payload)

    gmail_payload = json.loads(Path(outputs["gmail_payload"]).read_text(encoding="utf-8"))
    prompt = Path(outputs["prompt_to_paste"]).read_text(encoding="utf-8")
    email = Path(outputs["email_draft"]).read_text(encoding="utf-8")

    assert payload["tool_label"] == "ChatGPT Pro"
    assert payload["packet_path"] == ""
    assert gmail_payload["attachments"] == []
    assert "Rank the top workflow stalls and return five safe packets." in prompt
    assert "The conductor needs a short outside critique" in email
    assert "draft_by_default_no_automatic_send" == gmail_payload["send_policy"]
