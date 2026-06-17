from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v4.1-merge-source-truth-into-repo-state"
DEFAULT_REPO_STATE_JSON = "repo_state_v3.json"
DEFAULT_REPO_STATE_MD = "repo_state_v3.md"
DEFAULT_GUARD_JSON = "v4_source_truth_guard.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {"_non_object": data}
    except Exception as exc:
        return {"_json_error": f"{type(exc).__name__}: {exc}"}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value in (None, ""):
        return []
    return [str(value)]


def merge_report(repo_state: Dict[str, Any], guard: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(repo_state)
    blockers = normalize_list(guard.get("blockers"))
    warnings = normalize_list(guard.get("warnings"))
    status = str(guard.get("status") or "missing")
    publish_gate = str(guard.get("publish_gate") or "unknown")
    source_truth = {
        "version": VERSION,
        "merged_at_utc": now_iso(),
        "guard_version": guard.get("version"),
        "guard_status": status,
        "publish_gate": publish_gate,
        "blockers": blockers,
        "warnings": warnings,
        "expected_games": guard.get("expected_games", {}),
        "independent_schedule": guard.get("independent_schedule", {}),
        "needs_review": bool(blockers),
        "policy": guard.get("policy", {}),
    }
    merged["v4_source_truth_guard"] = source_truth
    overall = dict(merged.get("overall_sanity") or {})
    overall["source_truth_blockers"] = blockers
    overall["source_truth_warnings"] = warnings
    overall["source_truth_blocker_count"] = len(blockers)
    overall["source_truth_warning_count"] = len(warnings)
    overall["source_truth_needs_review"] = bool(blockers)
    overall["needs_review"] = bool(overall.get("needs_review") or blockers)
    merged["overall_sanity"] = overall
    return merged


def markdown_section(guard: Dict[str, Any]) -> str:
    blockers = normalize_list(guard.get("blockers"))
    warnings = normalize_list(guard.get("warnings"))
    expected = guard.get("expected_games") if isinstance(guard.get("expected_games"), dict) else {}
    independent = guard.get("independent_schedule") if isinstance(guard.get("independent_schedule"), dict) else {}
    lines = [
        "",
        "## V4 source truth guard",
        "",
        f"- Guard status: `{guard.get('status') or 'missing'}`",
        f"- Publish gate: `{guard.get('publish_gate') or 'unknown'}`",
        f"- Expected-games baseline: `{expected.get('internal_completeness_status')}`",
        f"- Independent slate status: `{independent.get('independent_slate_status')}`",
        f"- Source available: `{independent.get('source_available')}`",
        f"- Verification inconclusive: `{independent.get('verification_inconclusive')}`",
        "",
        "### Source-truth blockers",
        "",
    ]
    if blockers:
        lines += [f"- `{item}`" for item in blockers]
    else:
        lines.append("- None")
    lines += ["", "### Source-truth warnings", ""]
    if warnings:
        lines += [f"- `{item}`" for item in warnings]
    else:
        lines.append("- None")
    lines += [
        "",
        "V4 note: expected games generated from observed source rows are treated as internal consistency only, not independent slate verification.",
        "",
    ]
    return "\n".join(lines)


def merge_markdown(existing_md: str, guard: Dict[str, Any], merged_report: Dict[str, Any]) -> str:
    text = existing_md or "# HSD Repo State + Pipeline Sanity Audit v3\n"
    text = re.split(r"\n## V4 source truth guard\n", text, maxsplit=1)[0].rstrip() + "\n"
    overall = merged_report.get("overall_sanity") or {}
    if overall.get("needs_review"):
        text = re.sub(r"(- needs_review: `)(False|false)(`)", r"\1True\3", text)
    return text.rstrip() + "\n" + markdown_section(guard)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Merge V4 source-truth guard into repo_state_v3 outputs.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--repo-state-json", default=DEFAULT_REPO_STATE_JSON)
    parser.add_argument("--repo-state-md", default=DEFAULT_REPO_STATE_MD)
    parser.add_argument("--guard-json", default=DEFAULT_GUARD_JSON)
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    repo_json_path = root / args.repo_state_json
    repo_md_path = root / args.repo_state_md
    guard_path = root / args.guard_json

    repo_state = read_json(repo_json_path)
    guard = read_json(guard_path)
    if not repo_state:
        repo_state = {
            "version": "repo_state_v3_missing_bridge_seed",
            "generated_at_utc": now_iso(),
            "overall_sanity": {"needs_review": True},
        }
    if not guard:
        guard = {
            "version": "missing_v4_source_truth_guard",
            "status": "missing",
            "publish_gate": "blocked_manual_review_required",
            "blockers": ["v4_source_truth_guard_missing"],
            "warnings": [],
        }

    merged = merge_report(repo_state, guard)
    write_json(repo_json_path, merged)

    existing_md = repo_md_path.read_text(encoding="utf-8", errors="replace") if repo_md_path.exists() else ""
    repo_md_path.write_text(merge_markdown(existing_md, guard, merged), encoding="utf-8")

    print(json.dumps({
        "version": VERSION,
        "repo_state_json": repo_json_path.as_posix(),
        "repo_state_md": repo_md_path.as_posix(),
        "guard_json": guard_path.as_posix(),
        "source_truth_blockers": merged.get("overall_sanity", {}).get("source_truth_blockers"),
        "needs_review": merged.get("overall_sanity", {}).get("needs_review"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
