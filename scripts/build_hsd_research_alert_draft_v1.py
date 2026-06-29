from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, write_json, write_text


VERSION = "hsd-research-alert-draft-v1-review-only"
DEFAULT_RECIPIENT = "michael@brieffactory.com"
DEFAULT_OUTPUT_ROOT = Path("outputs/local/latest/files/research_alert_drafts")

TOOL_LABELS = {
    "chatgpt_pro": "ChatGPT Pro",
    "gemini_pro": "Gemini Pro",
}

LANE_LABELS = {
    "renderer": "renderer",
    "womens_soccer_assets": "women's soccer assets",
    "hockey_softball_assets": "hockey/softball assets",
    "workflow": "workflow",
    "games_stats": "games/stats",
    "breaking_public_signal": "breaking/public signal",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "research-alert"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def default_why_now(tool: str, lane: str) -> str:
    if tool == "gemini_pro" and lane == "renderer":
        return "A visual critique would improve the next renderer polish decision without blocking active Codex work."
    if lane.endswith("_assets"):
        return "External source and identity review would help rank the next manual asset workflow packet."
    if lane == "workflow":
        return "External review would help rank conductor workflow improvements and prevent orchestration drift."
    return "External research would materially improve the next HSD implementation packet."


def default_prompt(tool: str, lane: str, short_task: str) -> str:
    if lane == "renderer":
        return (
            f"Review the attached HSD packet for {short_task}. Return ranked visual findings, blocked ideas, "
            "and five PR-sized renderer packets that stay review-only."
        )
    if lane.endswith("_assets"):
        return (
            f"Review the attached HSD packet for {short_task}. Separate official, reputable public, gray-area, "
            "and blocked leads. Return five PR-sized asset workflow packets and any human intake needed."
        )
    if lane == "workflow":
        return (
            f"Review the attached HSD workflow packet for {short_task}. Identify bottlenecks, missing alerts, "
            "stale-lane risks, and five PR-sized workflow/tooling packets."
        )
    return (
        f"Review the attached HSD packet for {short_task}. Return ranked findings, guardrail-safe recommendations, "
        "blocked recommendations, and five PR-sized packets."
    )


def render_prompt(payload: dict[str, Any]) -> str:
    return f"""You are advising HSD from a review-only research packet.

Task:
{payload['prompt']}

Expected output:
1. Ranked findings.
2. Guardrail-safe recommendations.
3. Risky or blocked recommendations.
4. Five PR-sized packets with lane owner, scope, likely files, validation, and artifact expectations.
5. Human decision prompts, if any.

Guardrails:
- Review-only.
- No paid APIs by default.
- No automatic downloads.
- No auto-approval.
- No approval-state changes without human-edited intake.
- No headshot writes.
- No `.approved` markers.
- No publish-ready lane.
- No publishing.
"""


def render_email(payload: dict[str, Any]) -> str:
    prompt = render_prompt(payload).strip()
    return f"""Mike,

Research alert:

Tool to use:
{payload['tool_label']}

Why now:
{payload['why_now']}

Packet to upload:
{payload['packet_path']}

Prompt file:
{payload['prompt_to_paste_path']}

Prompt to paste:
{prompt}

Expected output:
Ranked findings, risks, and five PR-sized packets with lane owner, scope, files likely touched, validation, and artifact expectations.

Codex continues:
{payload['codex_continues']}

Guardrails:
- review-only
- no paid APIs by default
- no auto-approval
- no publishing
- no publish-ready lane
- no asset-state changes without human-edited intake
- downloads only through approved quarantine intake
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    short_task = clean(args.short_task)
    packet_path = clean(args.packet_path)
    alert_slug = args.alert_name or f"{generated_at.replace(':', '').split('.')[0]}-{args.tool}-{args.lane}-{short_task}"
    alert_slug = slugify(alert_slug)
    if args.output_dir:
        alert_dir = Path(args.output_dir).resolve()
    elif run_output_dir():
        alert_dir = output_path(Path("research_alert_drafts") / alert_slug).resolve()
    else:
        alert_dir = output_path(DEFAULT_OUTPUT_ROOT / alert_slug).resolve()
    prompt = clean(args.prompt) or default_prompt(args.tool, args.lane, short_task)
    payload: dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "status": "research_alert_draft_ready",
        "tool": args.tool,
        "tool_label": TOOL_LABELS[args.tool],
        "lane": args.lane,
        "lane_label": LANE_LABELS[args.lane],
        "short_task": short_task,
        "why_now": clean(args.why_now) or default_why_now(args.tool, args.lane),
        "packet_path": packet_path,
        "recipient": args.recipient,
        "subject": f"HSD research alert: {TOOL_LABELS[args.tool]} - {LANE_LABELS[args.lane]} - {short_task}",
        "prompt": prompt,
        "codex_continues": clean(args.codex_continues)
        or "yes; active Codex lanes continue while Mike runs the external research.",
        "repo_head": args.head_commit or git_head(),
        "alert_dir": str(alert_dir),
        "email_draft_path": str(alert_dir / "research_alert_email.md"),
        "prompt_to_paste_path": str(alert_dir / "prompt_to_paste.md"),
        "gmail_payload_path": str(alert_dir / "research_alert_gmail_payload.json"),
        "review_only": True,
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "publish_ready": False,
        "publishing": False,
        "send_policy": "draft_by_default_no_automatic_send",
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> dict[str, str]:
    alert_dir = Path(payload["alert_dir"])
    alert_dir.mkdir(parents=True, exist_ok=True)
    prompt_text = render_prompt(payload)
    payload["prompt_to_paste_path"] = str(write_text(alert_dir / "prompt_to_paste.md", prompt_text))
    email_text = render_email(payload)
    payload["email_draft_path"] = str(write_text(alert_dir / "research_alert_email.md", email_text))
    payload["gmail_payload_path"] = str(
        write_json(
            alert_dir / "research_alert_gmail_payload.json",
            {
                "to": payload["recipient"],
                "subject": payload["subject"],
                "body_markdown": email_text,
                "attachments": [payload["packet_path"]] if payload["packet_path"] else [],
                "send_policy": payload["send_policy"],
                "review_only": True,
                "requires_human_or_conductor_send": True,
            },
        )
    )
    manifest_path = write_json(alert_dir / "research_alert_manifest.json", payload)
    latest_path = write_json(
        output_path("research_alert_draft_latest.json"),
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "tool": payload["tool"],
            "lane": payload["lane"],
            "short_task": payload["short_task"],
            "alert_dir": payload["alert_dir"],
            "email_draft_path": payload["email_draft_path"],
            "prompt_to_paste_path": payload["prompt_to_paste_path"],
            "gmail_payload_path": payload["gmail_payload_path"],
            "packet_path": payload["packet_path"],
            "review_only": True,
            "send_policy": payload["send_policy"],
        },
    )
    return {
        "manifest": str(manifest_path),
        "latest": str(latest_path),
        "email_draft": payload["email_draft_path"],
        "prompt_to_paste": payload["prompt_to_paste_path"],
        "gmail_payload": payload["gmail_payload_path"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only HSD research alert email draft.")
    parser.add_argument("--tool", choices=sorted(TOOL_LABELS), required=True)
    parser.add_argument("--lane", choices=sorted(LANE_LABELS), required=True)
    parser.add_argument("--short-task", required=True)
    parser.add_argument("--packet-path", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--why-now", default="")
    parser.add_argument("--codex-continues", default="")
    parser.add_argument("--recipient", default=DEFAULT_RECIPIENT)
    parser.add_argument("--alert-name", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    outputs = write_outputs(payload)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "tool": payload["tool"],
                "lane": payload["lane"],
                "email_draft_path": outputs["email_draft"],
                "prompt_to_paste_path": outputs["prompt_to_paste"],
                "gmail_payload_path": outputs["gmail_payload"],
                "review_only": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
