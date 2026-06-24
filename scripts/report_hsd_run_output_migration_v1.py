from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_json, write_text

VERSION = "v1.0-run-output-migration-audit"
DEFAULT_OUTPUT_JSON = "run_output_migration_audit_v1.json"
DEFAULT_OUTPUT_MD = "run_output_migration_audit_v1.md"

WRITE_PATTERNS = [
    ("write_text", re.compile(r"\.write_text\(")),
    ("open_write", re.compile(r"\bopen\([^#\n]*(?:'|\")w")),
    ("path_open_write", re.compile(r"\.open\([^#\n]*(?:'|\")w")),
    ("zip_write", re.compile(r"ZipFile\([^#\n]*(?:'|\")w")),
    ("copy_file", re.compile(r"shutil\.copy")),
    ("mkdir", re.compile(r"\.mkdir\(")),
]

BATCH_LABELS = {
    "batch_1_asset_graphics": "Batch 1: asset and graphics generators",
    "batch_2_support_dashboards": "Batch 2: results/news support outputs",
    "batch_3_legacy_scraper": "Batch 3: legacy scraper output",
    "already_run_scoped": "Already run-scoped or run-aware",
}

ASSET_STAGE_CAUTION = (
    "Separate generated review/upload artifacts from canonical asset registry or approved-asset data. "
    "Generated packs should move into the run folder first; source-like asset registry updates should remain explicit review decisions."
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_path(path: str) -> str:
    return path.replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def runner_stage_scripts(runner_text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    current_stage = ""
    seen: set[tuple[str, str]] = set()

    for line in runner_text.splitlines():
        stage_match = re.match(r"function Invoke-(\w+)Stage", line)
        if stage_match:
            current_stage = stage_match.group(1).lower()
            continue
        if line.startswith("function ") and "Invoke-" in line and "Stage" not in line:
            current_stage = ""

        for match in re.finditer(r'Invoke-ScriptIfPresent \$Python "([^"]+)"', line):
            script = repo_path(match.group(1))
            key = (current_stage, script)
            if key not in seen:
                seen.add(key)
                rows.append({"stage": current_stage or "unknown", "script": script})

        scraper_match = re.search(r'Invoke-ScriptIfPresent \$python "([^"]+)"', line)
        if scraper_match and '"scraper"' in line:
            script = repo_path(scraper_match.group(1))
            key = ("scraper", script)
            if key not in seen:
                seen.add(key)
                rows.append({"stage": "scraper", "script": script})

    return rows


def write_hits(text: str) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        for kind, pattern in WRITE_PATTERNS:
            if pattern.search(stripped):
                hits.append({"line": line_number, "kind": kind, "text": stripped[:220]})
                break
    return hits


def recommended_batch(stage: str, uses_run_io: bool, hits: List[Dict[str, Any]]) -> str:
    if uses_run_io or not hits:
        return "already_run_scoped"
    if stage == "asset":
        return "batch_1_asset_graphics"
    if stage in {"results", "news"}:
        return "batch_2_support_dashboards"
    if stage == "scraper":
        return "batch_3_legacy_scraper"
    return "batch_2_support_dashboards"


def scan_script(root: Path, stage: str, script: str) -> Dict[str, Any]:
    path = root / script
    text = read_text(path)
    hits = write_hits(text)
    uses_run_io = "hsd_run_io" in text or "HSD_RUN_OUTPUT_DIR" in text
    return {
        "stage": stage,
        "script": script,
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "uses_hsd_run_io": uses_run_io,
        "write_hit_count": len(hits),
        "write_hits_sample": hits[:12],
        "recommended_batch": recommended_batch(stage, uses_run_io, hits),
    }


def scan_large_legacy_generators(root: Path, runner_scripts: set[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    candidates = sorted(root.glob("generate_hsd_*.py"), key=lambda p: p.stat().st_size, reverse=True)
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        hits = write_hits(text)
        if "hsd_run_io" in text or rel in runner_scripts or not hits:
            continue
        rows.append(
            {
                "script": rel,
                "bytes": path.stat().st_size,
                "write_hit_count": len(hits),
                "write_hits_sample": hits[:8],
            }
        )
    return rows[:12]


def build_audit(root: Path) -> Dict[str, Any]:
    runner = root / "scripts/hsd_local.ps1"
    stage_rows = runner_stage_scripts(read_text(runner))
    runner_scripts = {row["script"] for row in stage_rows}
    script_rows = [scan_script(root, row["stage"], row["script"]) for row in stage_rows]

    batches: Dict[str, List[Dict[str, Any]]] = {key: [] for key in BATCH_LABELS}
    for row in script_rows:
        batches.setdefault(row["recommended_batch"], []).append(row)

    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "scope": "local runner scripts plus large non-runner generate_hsd legacy writers",
        "policy": {
            "free_source_policy_unchanged": True,
            "manual_only_default": True,
            "workflow_changes_required": False,
            "paid_api_changes_required": False,
        },
        "asset_stage_caution": ASSET_STAGE_CAUTION,
        "runner_scripts": script_rows,
        "prioritized_batches": batches,
        "large_non_runner_legacy_writers": scan_large_legacy_generators(root, runner_scripts),
    }


def render_md(report: Dict[str, Any]) -> str:
    lines = [
        "# HSD Run-Scoped Output Migration Audit",
        "",
        f"Version: `{report['version']}`",
        f"Generated: `{report['generated_at_utc']}`",
        "",
        "## Guardrails",
        "",
        "- Keep local/manual operation as the default.",
        "- Keep free-source behavior intact; no paid APIs are needed for this migration.",
        "- Do not add workflow automation or auto-publishing.",
        "- Preserve legacy root compatibility when `HSD_RUN_OUTPUT_DIR` is unset.",
        "",
    ]

    if report["prioritized_batches"].get("batch_1_asset_graphics"):
        lines += [
            "## Recommendation",
            "",
            "Move Batch 1 next: the asset and graphics generators. They are the remaining normal local-run stage with the most direct root writes and generated folders.",
            "",
            f"Asset-stage caution: {report['asset_stage_caution']}",
            "",
        ]
    else:
        lines += [
            "## Recommendation",
            "",
            "Batch 1 asset and graphics generators are now run-aware. Move Batch 2 next: the remaining results/news support scripts that still write root files.",
            "",
            f"Asset-stage caution remains: {report['asset_stage_caution']}",
            "",
        ]

    for batch_key in ["batch_1_asset_graphics", "batch_2_support_dashboards", "batch_3_legacy_scraper", "already_run_scoped"]:
        rows = report["prioritized_batches"].get(batch_key, [])
        lines += [f"## {BATCH_LABELS[batch_key]}", ""]
        if not rows:
            lines += ["No scripts in this bucket.", ""]
            continue
        for row in rows:
            status = "run-aware" if row["uses_hsd_run_io"] else "legacy-root-writer"
            lines.append(f"- `{row['script']}` ({row['stage']}): {status}; write hits `{row['write_hit_count']}`")
            for hit in row.get("write_hits_sample", [])[:3]:
                lines.append(f"  - line {hit['line']}: `{hit['kind']}`")
        lines.append("")

    large_rows = report.get("large_non_runner_legacy_writers", [])
    lines += ["## Large Non-Runner Legacy Writers", ""]
    if not large_rows:
        lines += ["No large non-runner legacy writers found by this audit.", ""]
    else:
        lines.append("These are not the next local-run batch, but they should be considered after the runner-called scripts.")
        lines.append("")
        for row in large_rows:
            lines.append(f"- `{row['script']}`: bytes `{row['bytes']}`, write hits `{row['write_hit_count']}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit remaining HSD scripts that still need run-scoped output migration.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--print-md", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_audit(root)
    md = render_md(report)
    write_json(args.output_json, report, sort_keys=True)
    write_text(args.output_md, md)
    if args.print_md:
        print(md)
    else:
        print(json.dumps({"version": VERSION, "runner_scripts": len(report["runner_scripts"]), "output_md": args.output_md}, indent=2))


if __name__ == "__main__":
    main()
