from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_json, write_text


VERSION = "hsd-action-photo-handoff-draft-copy-v1-review-only"
DEFAULT_LATEST_MANIFEST = Path("action_photo_external_research_bundle_latest.json")
DEFAULT_OUTPUT_STEM = "action_photo_external_research_handoff_draft_copy"
PROMPT_RELATIVE_PATH = Path(
    "data/asset_registry/action_photo_candidates/"
    "review_only_action_photo_external_research_packet_prompt_v1.md"
)
RETURN_INTAKE_RELATIVE_PATH = Path(
    "data/asset_registry/action_photo_candidates/"
    "review_only_action_photo_research_return_intake_v1.csv"
)
SOURCE_MAP_RELATIVE_PATH = Path(
    "data/asset_registry/action_photo_candidates/"
    "review_only_action_photo_sport_entity_source_map_board_v1.md"
)
RESEARCH_PACKET_RELATIVE_PATH = Path(
    "data/asset_registry/action_photo_candidates/"
    "review_only_action_photo_candidate_research_packet_v1.md"
)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"missing_latest_action_photo_research_bundle_manifest:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest_payload_is_not_object:{path}")
    return payload


def path_text(value: Any) -> str:
    return str(value or "").strip()


def bundle_file_path(bundle_dir: str, rel_path: Path) -> str:
    if not bundle_dir:
        return ""
    return str(Path(bundle_dir) / "files" / rel_path)


def guardrails() -> dict[str, bool]:
    return {
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "external_network": False,
        "source_fetching": False,
        "source_scraping": False,
        "source_auto_enablement": False,
        "automatic_downloads": False,
        "email_sending": False,
        "gmail_api_calls": False,
        "gmail_draft_creation": False,
        "gmail_payload_created": False,
        "recipient_auto_send": False,
        "attachments_sent": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
    }


def render_subject() -> str:
    return "HSD review-only action-photo research handoff"


def render_body(paths: dict[str, str], bundle_status: str, generated_at_utc: str) -> str:
    return f"""Hi,

I have a review-only HSD action-photo external research packet ready for manual use in ChatGPT, Gemini, or a human research pass.

Important: this local helper does not send email, create Gmail drafts, call the Gmail API, attach files, download assets, fetch sources, scrape sources, approve anything, move anything into a publish-ready lane, or publish anything. It only writes local copy/paste text artifacts for Mike to review.

Subject to use:
{render_subject()}

Latest bundle status: {bundle_status or "unknown"}
Draft-copy generated at UTC: {generated_at_utc}

Exact local paths:
- Latest bundle manifest: {paths["latest_manifest_path"]}
- Bundle packet manifest: {paths["packet_manifest_path"]}
- Bundle directory: {paths["bundle_dir"]}
- Bundle zip, if created: {paths["zip_path"] or "not created"}
- Bundle prompt to paste/upload: {paths["bundle_prompt_path"]}
- Source prompt path in repo/run output: {paths["source_prompt_path"]}
- Source-map board: {paths["source_map_path"]}
- Research packet: {paths["research_packet_path"]}
- Human paste-back target: {paths["return_intake_path"]}

Operator instructions:
1. Open the bundle prompt path above and paste it into ChatGPT Pro, Gemini, or the manual research surface.
2. Attach or reference the local bundle directory or zip manually if you choose to use an external tool.
3. Ask for source leads only. Do not ask the tool to download images, approve assets, enable sources, create render-ready rows, or publish.
4. Paste returned evidence only into the human-edited return intake CSV listed above.
5. Regenerate the HSD review artifacts and quarantine preflight before any separate human download decision.

Guardrail summary:
- Review-only and artifact-only.
- No paid APIs.
- No automatic downloads, source fetching, or source scraping.
- No source auto-enablement.
- No email sending, Gmail API calls, Gmail draft creation, recipient auto-send, or sent attachments.
- No auto-approval, approval-state changes, headshot writes, or .approved marker writes.
- No publish-ready movement and no publishing.
"""


def render_markdown(payload: dict[str, Any]) -> str:
    paths = payload["paths"]
    body = payload["body"]
    return f"""# HSD Action-Photo Local Handoff Draft Copy

Status: `{payload["status"]}`

This is a local text/Markdown artifact only. It does not send email, create Gmail drafts, call the Gmail API, attach files, download assets, approve assets, enable sources, move files into a publish-ready lane, or publish.

## Subject

{payload["subject"]}

## Body

```text
{body.rstrip()}
```

## Exact Local Paths

- Latest bundle manifest: `{paths["latest_manifest_path"]}`
- Bundle packet manifest: `{paths["packet_manifest_path"]}`
- Bundle directory: `{paths["bundle_dir"]}`
- Bundle zip: `{paths["zip_path"] or "not created"}`
- Bundle prompt: `{paths["bundle_prompt_path"]}`
- Source prompt: `{paths["source_prompt_path"]}`
- Source-map board: `{paths["source_map_path"]}`
- Research packet: `{paths["research_packet_path"]}`
- Human paste-back target: `{paths["return_intake_path"]}`

## Guardrails

- Review-only and artifact-only.
- No paid APIs.
- No automatic downloads, source fetching, or source scraping.
- No source auto-enablement.
- No email sending, Gmail API calls, Gmail draft creation, recipient auto-send, or sent attachments.
- No auto-approval, approval-state changes, headshot writes, or `.approved` marker writes.
- No publish-ready movement and no publishing.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = input_path(args.latest_manifest or DEFAULT_LATEST_MANIFEST)
    latest = read_json_file(manifest_path)
    packet_manifest_path = path_text(latest.get("manifest_path")) or str(Path(path_text(latest.get("bundle_dir"))) / "packet_manifest.json")
    bundle_dir = path_text(latest.get("bundle_dir"))
    zip_path = path_text(latest.get("zip_path"))
    generated_at = now_iso()
    paths = {
        "latest_manifest_path": str(manifest_path),
        "packet_manifest_path": packet_manifest_path,
        "bundle_dir": bundle_dir,
        "zip_path": zip_path,
        "bundle_prompt_path": bundle_file_path(bundle_dir, PROMPT_RELATIVE_PATH),
        "source_prompt_path": str(input_path(PROMPT_RELATIVE_PATH)),
        "source_map_path": str(input_path(SOURCE_MAP_RELATIVE_PATH)),
        "research_packet_path": str(input_path(RESEARCH_PACKET_RELATIVE_PATH)),
        "return_intake_path": str(input_path(RETURN_INTAKE_RELATIVE_PATH)),
    }
    subject = render_subject()
    body = render_body(paths, clean(latest.get("status")), generated_at)
    output_stem = clean(args.output_stem) or DEFAULT_OUTPUT_STEM
    payload: dict[str, Any] = {
        "version": VERSION,
        "status": "action_photo_external_research_handoff_draft_copy_ready",
        "generated_at_utc": generated_at,
        "subject": subject,
        "body": body,
        "paths": paths,
        "latest_bundle_status": clean(latest.get("status")),
        "review_only": True,
        "artifact_only": True,
        "guardrails": guardrails(),
        "email_sending": False,
        "gmail_api_calls": False,
        "gmail_draft_creation": False,
        "gmail_payload_created": False,
        "recipient_auto_send": False,
        "attachments_sent": False,
        "approval_state_change": False,
        "automatic_downloads": False,
        "source_fetching": False,
        "source_scraping": False,
        "source_auto_enablement": False,
        "publish_ready": False,
        "publishing": False,
    }
    md_path = write_text(f"{output_stem}.md", render_markdown(payload))
    txt_path = write_text(f"{output_stem}.txt", body)
    payload["markdown_path"] = str(md_path)
    payload["text_path"] = str(txt_path)
    json_path = write_json(f"{output_stem}.json", payload)
    payload["json_path"] = str(json_path)
    write_json(f"{output_stem}.json", payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local review-only handoff draft copy for the latest action-photo research bundle.")
    parser.add_argument("--latest-manifest", default=str(DEFAULT_LATEST_MANIFEST))
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "markdown_path": payload["markdown_path"],
                "text_path": payload["text_path"],
                "json_path": payload["json_path"],
                "email_sending": False,
                "gmail_api_calls": False,
                "gmail_draft_creation": False,
                "gmail_payload_created": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
