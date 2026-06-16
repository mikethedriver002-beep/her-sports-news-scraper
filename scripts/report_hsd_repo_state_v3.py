from __future__ import annotations

import ast
import csv
import json
import os
import re
import subprocess
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "v3.0-repo-state-pipeline-sanity-audit"
ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
WORKFLOW = ROOT / ".github" / "workflows" / "hsd-pipeline-control-v1.yml"
REQUIREMENTS = ROOT / "requirements.txt"
VARIANT_SCRIPT = ROOT / "scripts" / "generate_hsd_graphics_variant_packs_v1.py"
PRODUCTION_ROOT = ROOT / "outputs" / "latest" / "production_graphics_director"
VARIANT_ROOT = PRODUCTION_ROOT / "graphics_variant_packs"
VARIANT_ZIPS = VARIANT_ROOT / "zips"
VARIANT_MANIFEST = VARIANT_ROOT / "variant_manifest.csv"
COPY_READY = PRODUCTION_ROOT / "copy_director" / "post_ready_copy.md"
NEEDS_FIX = ROOT / "data" / "asset_registry" / "wnba" / "athlete_image_needs_fix.csv"
SUMMARY = ROOT / "outputs" / "latest" / "summary.json"

PAID_SECRET_NAMES = ["APISPORTS_KEY", "BING_SEARCH_API_KEY", "SERPAPI_KEY"]
KEY_PATHS = [
    ".github/workflows",
    "scripts",
    "config",
    "data/asset_registry/wnba",
    "outputs/latest",
    "outputs/latest/review_files",
    "outputs/latest/POSTABLE_GRAPHICS",
    "outputs/latest/production_graphics_director",
    "outputs/latest/production_graphics_director/copy_director",
    "outputs/latest/production_graphics_director/graphics_variant_packs",
    "outputs/latest/production_graphics_director/graphics_variant_packs/zips",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(read_text(path)) if path.exists() else {}
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def run_git(args: List[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""


def count_files(path: Path) -> int:
    if path.is_file():
        return 1
    if not path.exists():
        return 0
    try:
        return sum(1 for p in path.rglob("*") if p.is_file())
    except Exception:
        return 0


def list_sample_files(path: Path, limit: int = 30) -> List[str]:
    if not path.exists():
        return []
    if path.is_file():
        return [rel(path)]
    files: List[str] = []
    try:
        for p in sorted(path.rglob("*")):
            if p.is_file():
                files.append(rel(p))
            if len(files) >= limit:
                break
    except Exception:
        return files
    return files


def path_state(path_text: str) -> Dict[str, Any]:
    path = ROOT / path_text
    return {
        "path": path_text,
        "exists": path.exists(),
        "type": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
        "file_count": count_files(path),
        "sample_files": list_sample_files(path),
    }


def literal_version(path: Path) -> str:
    text = read_text(path)
    if not text:
        return ""
    try:
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "VERSION":
                        if isinstance(node.value, ast.Constant):
                            return str(node.value.value)
    except Exception:
        pass
    match = re.search(r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']', text, flags=re.M)
    return match.group(1) if match else ""


def import_targets(path: Path) -> List[str]:
    text = read_text(path)
    targets: List[str] = []
    for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_\.]+)(?:\s+as\s+([A-Za-z0-9_]+))?", text, flags=re.M):
        module = match.group(1)
        alias = match.group(2) or ""
        if module.startswith("generate_hsd_"):
            targets.append(f"{module}" + (f" as {alias}" if alias else ""))
    for match in re.finditer(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+(.+)$", text, flags=re.M):
        module = match.group(1)
        names = match.group(2).strip()
        if module.startswith("generate_hsd_"):
            targets.append(f"from {module} import {names}")
    return targets


def version_key(path: Path) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", path.stem)
    return tuple(int(n) for n in nums) if nums else (0,)


def detect_versioned_scripts(pattern: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted((ROOT / "scripts").glob(pattern), key=version_key):
        rows.append({
            "path": rel(path),
            "exists": path.exists(),
            "version_constant": literal_version(path),
            "import_targets": import_targets(path),
        })
    return rows


def detect_paid_secret_policy() -> Dict[str, Any]:
    workflow_text = read_text(WORKFLOW)
    refs: Dict[str, Any] = {}
    for name in PAID_SECRET_NAMES:
        secret_expr = f"secrets.{name}"
        env_declared = bool(re.search(rf"^\s*{re.escape(name)}\s*:\s*\$\{{\{{\s*secrets\.{re.escape(name)}\s*\}}\}}", workflow_text, flags=re.M))
        refs[name] = {
            "workflow_reference_present": name in workflow_text,
            "workflow_secret_expression_present": secret_expr in workflow_text,
            "workflow_env_declared": env_declared,
            "policy": "optional_not_allowed_by_default" if name in workflow_text else "not_referenced",
            "required_by_default": False,
        }

    hard_required_hits: List[Dict[str, str]] = []
    scan_roots = [ROOT / "scripts", ROOT]
    seen: set[Path] = set()
    required_patterns = [
        r"os\.environ\[['\"]{name}['\"]\]",
        r"environ\[['\"]{name}['\"]\]",
        r"raise\s+.*{name}",
        r"required.*{name}",
    ]
    for base in scan_roots:
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else list(base.glob("*.py")) + list(base.glob("*.yml")) + list(base.glob("*.yaml"))
        if base.name == "scripts":
            candidates = list(base.rglob("*.py"))
        for path in candidates:
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            text = read_text(path)
            for name in PAID_SECRET_NAMES:
                for pat in required_patterns:
                    if re.search(pat.format(name=re.escape(name)), text, flags=re.I):
                        hard_required_hits.append({"path": rel(path), "secret": name, "pattern": pat.format(name=name)})
    return {
        "workflow_path": rel(WORKFLOW),
        "workflow_exists": WORKFLOW.exists(),
        "secrets": refs,
        "hard_required_pattern_hits": hard_required_hits,
        "no_paid_source_required_by_default": len(hard_required_hits) == 0,
        "v3_policy": "Free-only. Paid/source API secrets may be present as historical optional env names, but must not be required or used unless explicitly approved.",
    }


def variant_pair_audit() -> Dict[str, Any]:
    manifest_rows = read_csv(VARIANT_MANIFEST)
    zip_files = sorted(p.name for p in VARIANT_ZIPS.glob("*.zip")) if VARIANT_ZIPS.exists() else []
    packages: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"variants": set(), "team_assets": 0, "player_assets": 0, "statuses": []})
    for row in manifest_rows:
        pid = row.get("package_id", "")
        variant = row.get("variant", "")
        if not pid or not variant:
            continue
        packages[pid]["variants"].add(variant)
        packages[pid]["team_assets"] = max(packages[pid]["team_assets"], int(row.get("team_assets") or 0))
        packages[pid]["player_assets"] = max(packages[pid]["player_assets"], int(row.get("player_assets") or 0))
        packages[pid]["statuses"].append(row.get("status", ""))
    missing_pairs = []
    for pid, info in sorted(packages.items()):
        variants = info["variants"]
        if not {"logos_only", "with_players"}.issubset(variants):
            missing_pairs.append({"package_id": pid, "variants_found": sorted(variants)})

    # Fallback check from zip names when the CSV is unavailable.
    zip_pairs: Dict[str, set[str]] = defaultdict(set)
    for name in zip_files:
        if name.startswith("logos_only_"):
            zip_pairs[name[len("logos_only_"):-4]].add("logos_only")
        elif name.startswith("with_players_"):
            zip_pairs[name[len("with_players_"):-4]].add("with_players")
    missing_zip_pairs = [
        {"zip_slug": slug, "variants_found": sorted(variants)}
        for slug, variants in sorted(zip_pairs.items())
        if not {"logos_only", "with_players"}.issubset(variants)
    ]

    return {
        "variant_root_exists": VARIANT_ROOT.exists(),
        "zip_dir_exists": VARIANT_ZIPS.exists(),
        "variant_manifest_exists": VARIANT_MANIFEST.exists(),
        "manifest_rows": len(manifest_rows),
        "zip_count": len(zip_files),
        "zip_samples": zip_files[:30],
        "package_count_from_manifest": len(packages),
        "packages_with_player_assets": sum(1 for info in packages.values() if info["player_assets"] > 0),
        "missing_manifest_pairs": missing_pairs,
        "missing_zip_pairs": missing_zip_pairs,
        "pairs_ok": (not missing_pairs if manifest_rows else not missing_zip_pairs),
    }


def needs_fix_player_audit() -> Dict[str, Any]:
    needs_fix_rows = read_csv(NEEDS_FIX)
    needs_fix_ids = {row.get("athlete_id", "") for row in needs_fix_rows if row.get("athlete_id")}
    player_hits: List[Dict[str, str]] = []
    summaries = sorted((VARIANT_ROOT / "with_players").glob("*/content_summary.json")) if VARIANT_ROOT.exists() else []
    for summary_path in summaries:
        data = read_json(summary_path)
        for player in data.get("players", []) or []:
            aid = str(player.get("athlete_id", ""))
            if aid in needs_fix_ids:
                player_hits.append({"path": rel(summary_path), "athlete_id": aid, "display_name": str(player.get("display_name", ""))})
        for asset_path in data.get("player_assets", []) or []:
            for aid in needs_fix_ids:
                if aid and aid in str(asset_path):
                    player_hits.append({"path": rel(summary_path), "athlete_id": aid, "display_name": "asset_path_hit"})

    # Inspect ZIP member names when local ZIPs are available.
    zip_hits: List[Dict[str, str]] = []
    if VARIANT_ZIPS.exists():
        for zip_path in sorted(VARIANT_ZIPS.glob("with_players_*.zip")):
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    names = zf.namelist()
                for aid in needs_fix_ids:
                    if any(aid in member for member in names):
                        zip_hits.append({"zip_path": rel(zip_path), "athlete_id": aid})
            except Exception as exc:
                zip_hits.append({"zip_path": rel(zip_path), "athlete_id": "zip_read_error", "error": type(exc).__name__})

    return {
        "needs_fix_registry_exists": NEEDS_FIX.exists(),
        "needs_fix_count": len(needs_fix_ids),
        "needs_fix_ids": sorted(needs_fix_ids),
        "with_players_content_summaries": len(summaries),
        "content_summary_hits": player_hits,
        "zip_member_hits": zip_hits,
        "no_needs_fix_players_in_variant_packs": len(player_hits) == 0 and len([h for h in zip_hits if h.get("athlete_id") != "zip_read_error"]) == 0,
    }


def auto_render_review_policy() -> Dict[str, Any]:
    texts = {
        "outputs/latest/README.md": read_text(ROOT / "outputs" / "latest" / "README.md"),
        "production_graphics_director_report.md": read_text(PRODUCTION_ROOT / "production_graphics_director_report.md"),
        "hsd_pipeline_lite_review/README.md": read_text(ROOT / "hsd_pipeline_lite_review" / "README.md"),
    }
    markers = ["review before posting", "human-review only", "human review", "does not publish", "auto-renders remain human-review only"]
    found = []
    for path, text in texts.items():
        lower = text.lower()
        for marker in markers:
            if marker in lower:
                found.append({"path": path, "marker": marker})
    workflow_text = read_text(WORKFLOW).lower()
    publish_defaults_safe = "default: \"false\"" in workflow_text and "artifact_only" in workflow_text
    return {
        "markers_found": found,
        "workflow_publish_defaults_safe": publish_defaults_safe,
        "auto_renders_human_review_only": bool(found) and publish_defaults_safe,
    }


def acceptance_tests() -> Dict[str, Any]:
    pair = variant_pair_audit()
    needs = needs_fix_player_audit()
    render_policy = auto_render_review_policy()
    paid = detect_paid_secret_policy()
    tests = {
        "post_ready_copy_exists": COPY_READY.exists(),
        "graphics_variant_zip_dir_exists": VARIANT_ZIPS.exists(),
        "variant_pairs_ok": pair["pairs_ok"],
        "no_needs_fix_player_image_in_player_packs": needs["no_needs_fix_players_in_variant_packs"],
        "auto_renders_remain_human_review_only": render_policy["auto_renders_human_review_only"],
        "no_paid_api_source_required": paid["no_paid_source_required_by_default"],
    }
    return {
        "tests": tests,
        "passed": all(tests.values()),
        "details": {
            "variant_pair_audit": pair,
            "needs_fix_player_audit": needs,
            "auto_render_review_policy": render_policy,
            "paid_secret_policy": paid,
        },
    }


def build_report() -> Dict[str, Any]:
    prod_scripts = detect_versioned_scripts("generate_hsd_mermaid_production_graphics_director_v*.py")
    render_scripts = detect_versioned_scripts("generate_hsd_mermaid_render_studio_v*.py")
    variant_version = literal_version(VARIANT_SCRIPT)
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": str(ROOT),
        "git": {
            "current_branch": run_git(["branch", "--show-current"]),
            "head_sha": run_git(["rev-parse", "HEAD"]),
            "default_branch_guess": run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]).replace("origin/", "") or "main",
            "status_short": run_git(["status", "--short"]),
        },
        "requirements": {
            "path": "requirements.txt",
            "exists": REQUIREMENTS.exists(),
            "lines": [line.strip() for line in read_text(REQUIREMENTS).splitlines() if line.strip() and not line.strip().startswith("#")],
        },
        "workflow": {
            "path": rel(WORKFLOW),
            "exists": WORKFLOW.exists(),
        },
        "key_paths": [path_state(path) for path in KEY_PATHS],
        "production_graphics_directors": prod_scripts,
        "latest_production_graphics_director": prod_scripts[-1] if prod_scripts else {},
        "render_wrappers": render_scripts,
        "render_entrypoint": next((row for row in render_scripts if row["path"].endswith("generate_hsd_mermaid_render_studio_v3_0_1.py")), render_scripts[-1] if render_scripts else {}),
        "graphics_variant_packs_script": {
            "path": rel(VARIANT_SCRIPT),
            "exists": VARIANT_SCRIPT.exists(),
            "version_constant": variant_version,
            "import_targets": import_targets(VARIANT_SCRIPT),
        },
        "outputs_summary": read_json(SUMMARY),
    }
    report["acceptance"] = acceptance_tests()
    return report


def md_bool(value: Any) -> str:
    return "PASS" if value else "FAIL"


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines: List[str] = []
    lines.append("# HSD Repo State V3 Audit")
    lines.append("")
    lines.append(f"Generated: `{report['generated_at_utc']}`")
    lines.append(f"Version: `{report['version']}`")
    lines.append("")
    lines.append("## Git state")
    lines.append("")
    git = report.get("git", {})
    lines.append(f"- current branch: `{git.get('current_branch') or 'unknown'}`")
    lines.append(f"- default branch guess: `{git.get('default_branch_guess') or 'unknown'}`")
    lines.append(f"- HEAD: `{git.get('head_sha') or 'unknown'}`")
    status = git.get("status_short") or "clean/unknown"
    lines.append("- status short:")
    lines.append("```text")
    lines.append(status)
    lines.append("```")
    lines.append("")

    lines.append("## Requirements")
    lines.append("")
    req = report.get("requirements", {})
    lines.append(f"- requirements.txt exists: `{req.get('exists')}`")
    lines.append(f"- active requirements: `{', '.join(req.get('lines') or []) or 'none'}`")
    lines.append("")

    lines.append("## Key paths")
    lines.append("")
    lines.append("| Path | Type | Exists | File count |")
    lines.append("|---|---:|---:|---:|")
    for item in report.get("key_paths", []):
        lines.append(f"| `{item['path']}` | {item['type']} | {item['exists']} | {item['file_count']} |")
    lines.append("")

    lines.append("## Detected Production Graphics Director versions")
    lines.append("")
    for row in report.get("production_graphics_directors", []):
        lines.append(f"- `{row['path']}` — VERSION `{row.get('version_constant') or 'not declared'}`")
    lines.append("")

    lines.append("## Detected render wrappers")
    lines.append("")
    for row in report.get("render_wrappers", []):
        targets = "; ".join(row.get("import_targets") or []) or "no local import target detected"
        lines.append(f"- `{row['path']}` — VERSION `{row.get('version_constant') or 'not declared'}` — imports: {targets}")
    lines.append("")

    lines.append("## Graphics Variant Packs v1 script")
    lines.append("")
    variant = report.get("graphics_variant_packs_script", {})
    lines.append(f"- path: `{variant.get('path')}`")
    lines.append(f"- exists: `{variant.get('exists')}`")
    lines.append(f"- VERSION: `{variant.get('version_constant') or 'not declared'}`")
    lines.append("")

    lines.append("## Paid-source secret policy")
    lines.append("")
    paid = report["acceptance"]["details"]["paid_secret_policy"]
    lines.append("V3 policy: paid/API/search/sports-data secrets are optional historical references only and are not allowed by default.")
    lines.append("")
    lines.append("| Secret | Workflow ref | Secret expression | Required by default | Policy |")
    lines.append("|---|---:|---:|---:|---|")
    for name, info in paid.get("secrets", {}).items():
        lines.append(f"| `{name}` | {info['workflow_reference_present']} | {info['workflow_secret_expression_present']} | {info['required_by_default']} | `{info['policy']}` |")
    if paid.get("hard_required_pattern_hits"):
        lines.append("")
        lines.append("Hard-required pattern hits:")
        for hit in paid["hard_required_pattern_hits"]:
            lines.append(f"- `{hit['path']}` references `{hit['secret']}` via `{hit['pattern']}`")
    else:
        lines.append("")
        lines.append("No hard-required paid-secret patterns detected by this audit.")
    lines.append("")

    lines.append("## First V3 acceptance checks")
    lines.append("")
    tests = report.get("acceptance", {}).get("tests", {})
    lines.append("| Check | Result |")
    lines.append("|---|---:|")
    for name, value in tests.items():
        lines.append(f"| `{name}` | **{md_bool(value)}** |")
    lines.append("")
    lines.append(f"Overall: **{md_bool(report.get('acceptance', {}).get('passed'))}**")
    lines.append("")

    pair = report["acceptance"]["details"]["variant_pair_audit"]
    lines.append("## Variant pack detail")
    lines.append("")
    lines.append(f"- manifest rows: `{pair['manifest_rows']}`")
    lines.append(f"- package count from manifest: `{pair['package_count_from_manifest']}`")
    lines.append(f"- packages with player assets: `{pair['packages_with_player_assets']}`")
    lines.append(f"- zip count: `{pair['zip_count']}`")
    lines.append(f"- missing manifest pairs: `{len(pair['missing_manifest_pairs'])}`")
    lines.append(f"- missing zip pairs: `{len(pair['missing_zip_pairs'])}`")
    lines.append("")

    needs = report["acceptance"]["details"]["needs_fix_player_audit"]
    lines.append("## Needs-fix player audit")
    lines.append("")
    lines.append(f"- needs-fix count: `{needs['needs_fix_count']}`")
    lines.append(f"- needs-fix IDs: `{', '.join(needs['needs_fix_ids']) or 'none'}`")
    lines.append(f"- content summary hits: `{len(needs['content_summary_hits'])}`")
    lines.append(f"- zip member hits: `{len(needs['zip_member_hits'])}`")
    lines.append("")

    lines.append("## Commands to run next")
    lines.append("")
    lines.append("```bash")
    lines.append("python verify_hsd_install_v1.py")
    lines.append("python scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py")
    lines.append("python scripts/generate_hsd_graphics_variant_packs_v1.py")
    lines.append("python generate_hsd_pipeline_review_lite_v1.py")
    lines.append("python scripts/report_hsd_repo_state_v3.py")
    lines.append("```")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = build_report()
    json_path = ROOT / "repo_state_v3.json"
    md_path = ROOT / "repo_state_v3.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(json.dumps({
        "version": VERSION,
        "generated_at_utc": report["generated_at_utc"],
        "repo_state_v3_json": rel(json_path),
        "repo_state_v3_md": rel(md_path),
        "acceptance_passed": report["acceptance"]["passed"],
        "tests": report["acceptance"]["tests"],
    }, indent=2))


if __name__ == "__main__":
    main()
