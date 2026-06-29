from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, run_output_dir, write_json, write_text


VERSION = "hsd-action-photo-research-bundle-v1-review-only"
DEFAULT_BUNDLE_ROOT = Path("outputs/local/latest/files/action_photo_external_research_bundles")
ACTION_PHOTO_ROOT = Path("data/asset_registry/action_photo_candidates")

REQUIRED_ARTIFACTS = [
    "review_only_action_photo_external_research_packet_prompt_v1.md",
    "review_only_action_photo_external_research_packet_manifest_v1.json",
    "review_only_action_photo_sport_entity_source_map_board_v1.md",
    "review_only_action_photo_sport_entity_source_map_board_v1.csv",
    "review_only_action_photo_sport_entity_source_map_board_v1.json",
    "review_only_action_photo_lead_return_schema_v1.md",
    "review_only_action_photo_lead_return_schema_v1.csv",
    "review_only_action_photo_lead_return_schema_v1.json",
    "review_only_action_photo_candidate_research_packet_v1.md",
    "review_only_action_photo_candidate_research_packet_v1.csv",
    "review_only_action_photo_candidate_research_packet_v1.json",
    "review_only_action_photo_research_return_intake_v1.md",
    "review_only_action_photo_research_return_intake_v1.csv",
    "review_only_action_photo_research_return_intake_v1.json",
    "review_only_action_photo_research_run_bundle_v1.md",
    "review_only_action_photo_research_run_bundle_v1.csv",
    "review_only_action_photo_research_run_bundle_v1.json",
]

DISALLOWED_PATH_PARTS = {
    ".approved",
    "approved/",
    "publish-ready",
    "publish_ready",
    "headshot.png",
    "data/assets/quarantine/review_only_candidates",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "action-photo-research-bundle"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def expected_artifact_paths() -> list[str]:
    return [(ACTION_PHOTO_ROOT / name).as_posix() for name in REQUIRED_ARTIFACTS]


def relative_to_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_review_only_artifact(raw_path: str, repo: Path) -> Path:
    normalized = Path(raw_path).as_posix()
    if normalized not in set(expected_artifact_paths()):
        raise ValueError(f"artifact_not_in_action_photo_review_only_allowlist:{normalized}")
    lowered = normalized.lower()
    for part in DISALLOWED_PATH_PARTS:
        if part in lowered:
            raise ValueError(f"disallowed_artifact_path:{normalized}")
    resolved = input_path(normalized)
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError(f"missing_required_artifact:{normalized}")
    try:
        resolved.resolve().relative_to(repo.resolve())
    except ValueError:
        run_root = run_output_dir()
        if not run_root:
            raise ValueError(f"artifact_outside_repo_or_run_output:{resolved}")
        resolved.resolve().relative_to(run_root.resolve())
    return resolved


def copy_artifacts(paths: Iterable[str], repo: Path, bundle_dir: Path) -> list[dict[str, str]]:
    included: list[dict[str, str]] = []
    for raw_path in paths:
        source = resolve_review_only_artifact(raw_path, repo)
        rel = Path(raw_path).as_posix()
        target = bundle_dir / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        included.append(
            {
                "path": rel,
                "source_path": str(source),
                "bundle_path": target.relative_to(bundle_dir).as_posix(),
                "role": artifact_role(rel),
            }
        )
    return included


def artifact_role(path: str) -> str:
    name = Path(path).name
    if "external_research_packet_prompt" in name:
        return "external_research_prompt"
    if "external_research_packet_manifest" in name:
        return "upstream_export_manifest"
    if "source_map_board" in name:
        return "source_map_board"
    if "lead_return_schema" in name:
        return "paste_back_target_schema"
    if "research_return_intake" in name:
        return "paste_back_target_intake"
    if "research_run_bundle" in name:
        return "operator_run_steps"
    if "candidate_research_packet" in name:
        return "copy_ready_research_tasks"
    return "review_only_artifact"


def render_readme(payload: dict[str, Any]) -> str:
    included = "\n".join(f"- `{item['bundle_path']}` - {item['role']}" for item in payload["included_files"])
    return f"""# HSD Action-Photo External Research Bundle

Status: review-only local packet for ChatGPT Pro, Gemini, or manual research.

Generated: `{payload['generated_at_utc']}`
Version: `{payload['version']}`
Repo HEAD: `{payload['repo_head']}`

## What This Is

This bundle copies already-generated review-only action-photo research export artifacts into one local packet. It performs no network access, source fetching, scraping, downloading, email sending, approval, asset-state mutation, headshot writes, `.approved` marker writes, publish-ready movement, or publishing.

## Operator Flow

1. Upload or paste the bundle contents into the external research tool.
2. Use `files/data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md` as the prompt.
3. Use the included source-map board and research packet as context.
4. Paste returned URL/evidence rows only into `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`.
5. Regenerate/validate before any separate human quarantine-download decision.

## Included Files

{included}

## Command Center

After generating this bundle, rerun `python generate_hsd_operator_command_center_v2.py` to expose the latest bundle manifest and zip path in the local operator surface when those files exist.

## Guardrails

- Review-only and artifact-only.
- No paid APIs.
- No external network access, source fetching, scraping, or automatic downloads.
- No email sending; this helper creates no Gmail payload.
- No source auto-enablement.
- No auto-approval or approval-state changes.
- No headshot writes.
- No `.approved` marker writes.
- No files from approved asset folders or publish-ready lanes.
- No publishing.
"""


def write_zip(bundle_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(bundle_dir.rglob("*")):
            if file_path.is_file() and file_path != zip_path and file_path.suffix != ".zip":
                archive.write(file_path, file_path.relative_to(bundle_dir))


def build_bundle(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path.cwd()
    generated_at = now_iso()
    slug = slugify(args.bundle_name or f"{generated_at.replace(':', '').split('.')[0]}-action-photo-research")
    if args.output_dir:
        bundle_dir = Path(args.output_dir).resolve()
    elif run_output_dir():
        bundle_dir = output_path(Path("action_photo_external_research_bundles") / slug).resolve()
    else:
        bundle_dir = output_path(DEFAULT_BUNDLE_ROOT / slug).resolve()
    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise FileExistsError(f"bundle_output_dir_already_exists_and_is_not_empty:{bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = expected_artifact_paths()
    included = copy_artifacts(artifact_paths, repo, bundle_dir)
    zip_path = bundle_dir.with_suffix(".zip") if args.zip else None
    payload: dict[str, Any] = {
        "version": VERSION,
        "status": "action_photo_external_research_bundle_ready",
        "generated_at_utc": generated_at,
        "repo": str(repo),
        "repo_head": clean(args.head_commit) or git_head(),
        "bundle_dir": str(bundle_dir),
        "zip_path": str(zip_path) if zip_path else "",
        "zip_created": bool(zip_path),
        "included_files": included,
        "included_file_count": len(included),
        "required_artifacts": artifact_paths,
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "external_network": False,
        "source_fetching": False,
        "source_auto_enablement": False,
        "automatic_downloads": False,
        "email_sending": False,
        "gmail_payload_created": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
    }
    payload["readme_path"] = str(write_text(bundle_dir / "README.md", render_readme(payload)))
    payload["manifest_path"] = str(write_json(bundle_dir / "packet_manifest.json", payload))
    if zip_path:
        write_zip(bundle_dir, zip_path)
    latest_payload = {
        "version": VERSION,
        "status": payload["status"],
        "generated_at_utc": generated_at,
        "bundle_dir": str(bundle_dir),
        "zip_path": str(zip_path) if zip_path else "",
        "manifest_path": payload["manifest_path"],
        "readme_path": payload["readme_path"],
        "included_file_count": len(included),
        "review_only": True,
        "artifact_only": True,
        "email_sending": False,
        "automatic_downloads": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
    }
    latest_path = write_json(output_path("action_photo_external_research_bundle_latest.json"), latest_payload)
    payload["latest_manifest_path"] = str(latest_path)
    write_json(bundle_dir / "packet_manifest.json", payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local review-only action-photo external research bundle.")
    parser.add_argument("--bundle-name", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--zip", action="store_true", help="Also create a local zip next to the bundle directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_bundle(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "bundle_dir": payload["bundle_dir"],
                "zip_path": payload["zip_path"],
                "included_file_count": payload["included_file_count"],
                "review_only": True,
                "email_sending": False,
                "automatic_downloads": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
