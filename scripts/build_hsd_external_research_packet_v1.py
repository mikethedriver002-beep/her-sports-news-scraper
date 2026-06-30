from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_json, write_text


VERSION = "hsd-external-research-packet-v1-review-only"
DEFAULT_RECIPIENT = "michael@brieffactory.com"
DEFAULT_PACKET_ROOT = Path("outputs/local/latest/files/external_research_packets")

ALWAYS_INCLUDE = [
    "docs/HSD_OPERATING_WORKFLOW_V1.md",
    "docs/HSD_EXTERNAL_RESEARCH_PACKET_TEMPLATE.md",
    "docs/HSD_RESEARCH_ALERT_EMAIL_TEMPLATE.md",
    "docs/HSD_REVIEW_ONLY_ASSET_DOWNLOAD_POLICY.md",
    "launch_operating_sop.md",
    "launch_command_center.md",
    "outputs/local/latest/files/operator_command_center.html",
    "outputs/local/latest/files/operator_command_center.md",
    "outputs/local/latest/files/operator_command_center.json",
]

LANE_INCLUDE: dict[str, list[str]] = {
    "renderer": [
        "outputs/local/latest/files/render_handoff_top_packet/README.md",
        "outputs/local/latest/files/render_handoff_top_packet/draft_preview.png",
        "outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_story.png",
        "outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_square.png",
        "outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_visual_contact_sheet.png",
        "outputs/local/latest/files/manual_review_renderer_manifest.json",
        "outputs/local/latest/files/manual_review_renderer_report.md",
        "outputs/local/latest/files/manual_visual_qa_manifest.json",
        "outputs/local/latest/files/manual_visual_qa_report.md",
        "outputs/local/latest/files/render_visual_delta_manifest.json",
        "outputs/local/latest/files/render_visual_delta_report.md",
        "outputs/local/latest/files/render_visual_revision_plan.md",
        "assets/graphics/v4/approved/layout_references",
    ],
    "womens_soccer_assets": [
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md",
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv",
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json",
        "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md",
        "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv",
        "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json",
        "data/asset_registry/womens_soccer/external_research",
        "outputs/local/latest/files/data/asset_registry/womens_soccer",
    ],
    "hockey_softball_assets": [
        "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md",
        "data/asset_registry/hockey_softball_asset_workflow_readiness_report.json",
        "data/asset_registry/hockey_softball_asset_review_action_queue.md",
        "data/asset_registry/hockey_softball_asset_review_action_queue.csv",
        "data/asset_registry/hockey_softball_asset_review_triage.md",
        "data/asset_registry/hockey_softball_asset_review_triage.csv",
        "data/asset_registry/hockey_softball_source_priority_worksheet.md",
        "data/asset_registry/hockey_softball_source_priority_worksheet.csv",
        "data/asset_registry/hockey_softball_asset_next_action_cards.md",
        "data/asset_registry/hockey_softball_asset_next_action_cards.csv",
        "data/asset_registry/hockey_softball_asset_next_action_cards.json",
        "data/asset_registry/hockey_softball_quarantine_download_intake.md",
        "data/asset_registry/hockey_softball_quarantine_download_intake.csv",
        "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md",
        "data/asset_registry/softball/softball_asset_workflow_board.md",
        "outputs/local/latest/files/data/asset_registry/womens_hockey",
        "outputs/local/latest/files/data/asset_registry/softball",
    ],
    "workflow": [
        "outputs/local/latest/files/workflow_lane_status_dashboard.md",
        "outputs/local/latest/files/workflow_lane_status_dashboard.csv",
        "outputs/local/latest/files/workflow_lane_status_dashboard.json",
        "docs/HSD_LANE_PACKET_CONTRACT.md",
        "docs/HSD_COMMAND_CENTER_DECISION_AUDIT.md",
        "config/hsd_durable_lane_thread_roster.json",
        "config/workflow_policy.json",
        "config/hsd_manual_workflow_policy_v1.json",
        "config/hsd_daily_cadence_v2.json",
    ],
    "games_stats": [
        "outputs/local/latest/files/game_intelligence_board_v1.md",
        "outputs/local/latest/files/game_intelligence_board_v1.csv",
        "outputs/local/latest/files/game_intelligence_board_v1.json",
    ],
    "breaking_public_signal": [
        "outputs/local/latest/files/breaking_public_signal_board.md",
        "outputs/local/latest/files/breaking_public_signal_board.csv",
        "outputs/local/latest/files/breaking_public_signal_board.json",
    ],
}

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
    return slug or "research-packet"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative_to_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file():
                yield child


def unique_existing_files(paths: Iterable[str], repo: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    seen: set[Path] = set()
    for raw in paths:
        candidate = Path(raw)
        path = candidate if candidate.is_absolute() else repo / candidate
        if not path.exists():
            missing.append(raw)
            continue
        for file_path in iter_files(path):
            resolved = file_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(file_path)
    return files, missing


def research_questions(tool: str, lane: str, question: str) -> list[str]:
    if question:
        return [question]
    if lane == "renderer":
        return [
            "Critique the latest HSD render against premium sports-editorial social graphics.",
            "Identify the highest-impact visual upgrades for athlete-first composition, text hierarchy, number placement, background depth, and emotional focal point.",
            "Return five PR-sized renderer packets that stay review-only and avoid paid APIs or publishing.",
        ]
    if lane in {"womens_soccer_assets", "hockey_softball_assets"}:
        return [
            "Audit the included asset/source boards for the fastest path to manual photo or logo review readiness.",
            "Separate official, reputable public, gray-area, and blocked leads without promoting any source to approval.",
            "Return five PR-sized asset workflow packets with exact guardrails and validation.",
        ]
    if lane == "workflow":
        return [
            "Audit the HSD conductor workflow for bottlenecks and missing operating glue.",
            "Suggest concrete repo-visible improvements that make external research, PR packets, and email alerts easier to run.",
            "Return five PR-sized workflow packets with merge order.",
        ]
    return [
        "Rank the highest-impact improvements available from the included HSD artifacts.",
        "Identify which ideas are safe under current review-only guardrails.",
        "Return five PR-sized implementation packets with lane owner, files, validation, and artifact expectations.",
    ]


def render_readme(payload: Mapping[str, Any]) -> str:
    questions = "\n".join(f"{index}. {question}" for index, question in enumerate(payload["research_questions"], start=1))
    included = "\n".join(f"| `{item['path']}` | {item['why']} |" for item in payload["included_files"])
    missing = "\n".join(f"- `{item}`" for item in payload["missing_files"]) or "- None"
    return f"""# HSD External Research Packet

Status: review-only external research packet.

Generated: `{payload['generated_at_utc']}`
Version: `{payload['version']}`

## Research Alert

Tool: {payload['tool_label']}

Lane: {payload['lane_label']}

Why now: {payload['why_now']}

Codex continues while this runs: {payload['codex_continues']}

Expected output: ranked findings, risks, and five PR-sized implementation packets.

## Current Repo State

- Repo: `{payload['repo']}`
- Main/HEAD commit: `{payload['head_commit']}`
- Packet zip: `{payload['zip_path']}`
- Email draft: `{payload['email_draft_path']}`
- Gmail payload: `{payload['gmail_payload_path']}`

## Guardrails

- Review-only unless human-edited intake explicitly says otherwise.
- No paid APIs.
- No automatic downloads.
- Local downloads require `download_approved=yes` and required quarantine metadata.
- No auto-approval.
- No asset approval-state changes without explicit human-edited intake.
- No `headshot.png` writes.
- No `.approved` marker writes.
- No publish-ready lane.
- No publishing.

## Files Included

| File | Why included |
| --- | --- |
{included}

## Missing Expected Files

{missing}

## Research Questions

{questions}

## Required Output Format

Return:

1. Ranked findings.
2. Guardrail-safe recommendations.
3. Risky or blocked recommendations.
4. Five PR-sized packets with lane owner, scope, files likely touched, validation, and artifact expectations.
5. Any suggested human decision prompts.

## Notes For External Tools

- Do not propose paid APIs as the default path.
- Do not propose automatic publishing.
- Do not propose auto-approval.
- Do not ask Codex to download assets without the quarantine intake policy.
- Gray-area public/fair-use-tolerant source candidates may be suggested as candidates, but approval remains human and review-only.
"""


def render_email_body(payload: Mapping[str, Any]) -> str:
    prompt = "\n".join(f"{index}. {question}" for index, question in enumerate(payload["research_questions"], start=1))
    return f"""Mike,

Research alert:

Tool to use:
{payload['tool_label']}

Why now:
{payload['why_now']}

Packet to upload:
{payload['zip_path']}

Prompt to paste:
You are advising HSD from the attached review-only research packet. Review the README and included artifacts, then answer:
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


def copy_packet_files(files: Iterable[Path], repo: Path, packet_dir: Path) -> list[dict[str, str]]:
    included: list[dict[str, str]] = []
    file_root = packet_dir / "files"
    for file_path in files:
        rel = relative_to_repo(file_path, repo)
        target = file_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
        included.append({"path": rel, "why": why_included(rel)})
    return included


def why_included(path: str) -> str:
    lower = path.lower()
    if "operator_command_center" in lower:
        return "Current operator surface and artifact index."
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "Current visual artifact for external critique."
    if "manifest" in lower or lower.endswith(".json"):
        return "Machine-readable status, counts, freshness, or validation context."
    if lower.endswith(".csv"):
        return "Structured candidate, source, or review queue rows."
    if "workflow" in lower or "template" in lower or lower.startswith("docs/"):
        return "Operating rules, packet template, or guardrail context."
    return "Relevant HSD review-only artifact."


def zip_packet(packet_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(packet_dir.rglob("*")):
            if file_path == zip_path or file_path.suffix == ".zip":
                continue
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(packet_dir))


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path.cwd()
    generated_at = now_iso()
    stamp = generated_at.replace(":", "").replace("+", "Z").split(".")[0]
    packet_slug = args.packet_name or f"{stamp}-{args.tool}-{args.lane}"
    packet_slug = slugify(packet_slug)
    if args.output_dir:
        packet_dir = Path(args.output_dir).resolve()
    elif run_output_dir():
        packet_dir = output_path(Path("external_research_packets") / packet_slug).resolve()
    else:
        packet_dir = output_path(DEFAULT_PACKET_ROOT / packet_slug).resolve()
    packet_dir.mkdir(parents=True, exist_ok=True)

    wanted = list(ALWAYS_INCLUDE) + LANE_INCLUDE.get(args.lane, []) + list(args.include)
    files, missing = unique_existing_files(wanted, repo)
    included = copy_packet_files(files, repo, packet_dir)

    head_commit = args.head_commit or "unknown"
    if head_commit == "unknown":
        import subprocess

        try:
            head_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        except Exception:
            head_commit = "unknown"

    zip_path = packet_dir.with_suffix(".zip")
    email_draft_path = packet_dir / "research_alert_email.md"
    gmail_payload_path = packet_dir / "research_alert_gmail_payload.json"
    why_now = args.why_now or default_why_now(args.tool, args.lane)
    codex_continues = args.codex_continues or "yes; active Codex lanes continue while Mike runs the external research."
    payload: dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "tool": args.tool,
        "tool_label": TOOL_LABELS[args.tool],
        "lane": args.lane,
        "lane_label": LANE_LABELS[args.lane],
        "repo": str(repo),
        "head_commit": head_commit,
        "recipient": args.recipient,
        "subject": f"HSD research alert: {TOOL_LABELS[args.tool]} - {LANE_LABELS[args.lane]} - {args.short_task}",
        "why_now": why_now,
        "codex_continues": codex_continues,
        "research_questions": research_questions(args.tool, args.lane, clean(args.question)),
        "included_files": included,
        "included_file_count": len(included),
        "missing_files": missing,
        "packet_dir": str(packet_dir),
        "zip_path": str(zip_path),
        "email_draft_path": str(email_draft_path),
        "gmail_payload_path": str(gmail_payload_path),
        "review_only": True,
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
        "send_policy": "draft_by_default_send_only_when_time_sensitive",
    }
    readme = render_readme(payload)
    body = render_email_body(payload)
    write_text(packet_dir / "README.md", readme, normalize=strip_volatile_markdown_lines)
    write_text(email_draft_path, body)
    write_json(
        gmail_payload_path,
        {
            "to": args.recipient,
            "subject": payload["subject"],
            "body_markdown": body,
            "attachments": [str(zip_path)],
            "send_policy": payload["send_policy"],
            "review_only": True,
            "requires_human_or_conductor_send": True,
        },
    )
    write_json(packet_dir / "packet_manifest.json", payload)
    zip_packet(packet_dir, zip_path)
    write_json(
        output_path("external_research_packet_latest.json"),
        {
            "version": VERSION,
            "generated_at_utc": generated_at,
            "tool": args.tool,
            "lane": args.lane,
            "packet_dir": str(packet_dir),
            "zip_path": str(zip_path),
            "email_draft_path": str(email_draft_path),
            "gmail_payload_path": str(gmail_payload_path),
            "included_file_count": len(included),
            "missing_file_count": len(missing),
            "review_only": True,
            "send_policy": payload["send_policy"],
        },
    )
    return payload


def default_why_now(tool: str, lane: str) -> str:
    if tool == "gemini_pro" and lane == "renderer":
        return "The latest renderer needs external visual critique against sports-editorial references before the next polish packet."
    if lane.endswith("_assets"):
        return "The asset workflow has enough review-only candidate data for external source/identity strategy to improve the next packet."
    if lane == "workflow":
        return "The operating workflow needs an outside audit for bottlenecks and automation gaps before more orchestration work piles up."
    return "External research would materially improve the next implementation packet."


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only HSD external research packet and Gmail-ready alert draft.")
    parser.add_argument("--tool", choices=sorted(TOOL_LABELS), required=True)
    parser.add_argument("--lane", choices=sorted(LANE_LABELS), required=True)
    parser.add_argument("--short-task", default="run external research packet")
    parser.add_argument("--question", default="")
    parser.add_argument("--why-now", default="")
    parser.add_argument("--codex-continues", default="")
    parser.add_argument("--recipient", default=DEFAULT_RECIPIENT)
    parser.add_argument("--packet-name", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--include", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_packet(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": "external_research_packet_ready",
                "tool": payload["tool"],
                "lane": payload["lane"],
                "zip_path": payload["zip_path"],
                "email_draft_path": payload["email_draft_path"],
                "gmail_payload_path": payload["gmail_payload_path"],
                "included_file_count": payload["included_file_count"],
                "missing_file_count": len(payload["missing_files"]),
                "review_only": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
