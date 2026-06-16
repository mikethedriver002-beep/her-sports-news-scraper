from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "v3.0-repo-state-pipeline-sanity-audit"
PAID_SECRET_NAMES = {"APISPORTS_KEY", "BING_SEARCH_API_KEY", "SERPAPI_KEY"}
DEFAULT_OUTPUT_JSON = "repo_state_v3.json"
DEFAULT_OUTPUT_MD = "repo_state_v3.md"

KEY_PATHS = [
    ".github/workflows/hsd-pipeline-control-v1.yml",
    "requirements.txt",
    "verify_hsd_install_v1.py",
    "generate_hsd_pipeline_review_lite_v1.py",
    "scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py",
    "scripts/generate_hsd_graphics_variant_packs_v1.py",
    "outputs/latest/summary.json",
    "outputs/latest/production_graphics_director/copy_director/post_ready_copy.md",
    "outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv",
    "outputs/latest/production_graphics_director/graphics_variant_packs/zips",
]

KEY_DIRS = [
    "scripts",
    "config",
    "data/asset_registry/wnba",
    ".github/workflows",
    "outputs/latest",
    "outputs/latest/review_files",
    "outputs/latest/POSTABLE_GRAPHICS",
    "outputs/latest/production_graphics_director",
    "outputs/latest/production_graphics_director/graphics_variant_packs",
]

KEY_WNBA_FILES = [
    "teams.csv",
    "team_aliases.csv",
    "logo_sources.csv",
    "team_logos.csv",
    "missing_team_logos.csv",
    "athlete_sources.csv",
    "athletes.csv",
    "athlete_aliases.csv",
    "athlete_images.csv",
    "athlete_image_candidates.csv",
    "athlete_image_match_review.csv",
    "athlete_image_decision_overrides.csv",
    "athlete_image_approved_assets.csv",
    "athlete_image_needs_fix.csv",
]

RUN_COMMANDS = [
    "python verify_hsd_install_v1.py",
    "python scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py",
    "python scripts/generate_hsd_graphics_variant_packs_v1.py",
    "python generate_hsd_pipeline_review_lite_v1.py",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def rel_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 8) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def detect_repo_root(start: Path) -> Path:
    start = start.resolve()
    candidates = [start, *start.parents]
    for candidate in candidates:
        if (candidate / ".git").exists() or (candidate / ".github").exists() or (candidate / "requirements.txt").exists():
            return candidate
    return Path.cwd().resolve()


def read_text(path: Path, limit_bytes: int = 2_000_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        data = path.read_bytes()[:limit_bytes]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def read_json(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"_non_object": data}
    except Exception as exc:
        return {"_json_error": str(exc)}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def file_info(root: Path, relative: str) -> Dict[str, Any]:
    path = root / relative
    info: Dict[str, Any] = {"path": relative, "exists": path.exists()}
    if path.is_file():
        info.update({"type": "file", "size": path.stat().st_size})
    elif path.is_dir():
        files = [p for p in path.rglob("*") if p.is_file()]
        info.update({"type": "dir", "file_count": len(files)})
    else:
        info.update({"type": "missing", "size": 0})
    return info


def list_dir_snapshot(root: Path, relative: str, max_items: int = 80) -> Dict[str, Any]:
    path = root / relative
    info = file_info(root, relative)
    if not path.exists() or not path.is_dir():
        info["items"] = []
        return info
    items = []
    for p in sorted(path.rglob("*")):
        if p.is_file():
            items.append({"path": rel_path(root, p), "size": p.stat().st_size})
        if len(items) >= max_items:
            break
    info["items"] = items
    return info


def detect_git_state(root: Path) -> Dict[str, Any]:
    branch = run_cmd(["git", "branch", "--show-current"], root)
    status = run_cmd(["git", "status", "--short"], root)
    rev = run_cmd(["git", "rev-parse", "HEAD"], root)
    remotes = run_cmd(["git", "remote", "-v"], root)
    return {
        "branch": branch.get("stdout") if branch.get("ok") else "unknown",
        "head_sha": rev.get("stdout") if rev.get("ok") else "unknown",
        "dirty": bool((status.get("stdout") or "").strip()),
        "status_short": status.get("stdout"),
        "remotes": remotes.get("stdout"),
        "commands": {"branch": branch, "status": status, "rev_parse": rev},
    }


def detect_version_assignments(path: Path) -> Dict[str, str]:
    text = read_text(path)
    versions: Dict[str, str] = {}
    for key in ["VERSION", "RENDER_VERSION", "PIPELINE_VERSION"]:
        m = re.search(rf"^\s*{re.escape(key)}\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
        if m:
            versions[key] = m.group(1)
    return versions


def detect_import_targets(path: Path) -> List[str]:
    text = read_text(path)
    imports = []
    for m in re.finditer(r"^\s*import\s+([A-Za-z0-9_\.]+)(?:\s+as\s+\w+)?", text, re.MULTILINE):
        imports.append(m.group(1))
    for m in re.finditer(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+", text, re.MULTILINE):
        imports.append(m.group(1))
    return sorted(set(imports))


def detect_script_versions(root: Path) -> Dict[str, Any]:
    scripts = {
        "production_graphics_director_v4_5": "scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py",
        "graphics_variant_packs_v1": "scripts/generate_hsd_graphics_variant_packs_v1.py",
        "render_wrapper_v3_0_1": "scripts/generate_hsd_mermaid_render_studio_v3_0_1.py",
        "render_skin_v3_0_4": "scripts/generate_hsd_mermaid_render_studio_v3_0_4.py",
        "render_approved_athletes_v3_0_2": "scripts/generate_hsd_mermaid_render_studio_v3_0_2.py",
        "render_base_v3_0": "scripts/generate_hsd_mermaid_render_studio_v3_0.py",
        "pipeline_review_lite": "generate_hsd_pipeline_review_lite_v1.py",
    }
    out: Dict[str, Any] = {}
    for name, rel in scripts.items():
        path = root / rel
        out[name] = {
            "path": rel,
            "exists": path.exists(),
            "versions": detect_version_assignments(path),
            "imports": detect_import_targets(path)[:30],
            "size": path.stat().st_size if path.exists() else 0,
        }
    return out


def workflow_paid_secret_audit(root: Path) -> Dict[str, Any]:
    rel = ".github/workflows/hsd-pipeline-control-v1.yml"
    path = root / rel
    text = read_text(path)
    found = sorted(secret for secret in PAID_SECRET_NAMES if secret in text)
    hard_required_patterns = []
    for secret in PAID_SECRET_NAMES:
        for pattern in [
            rf"if\s*\[\s*-z\s+['\"]?\$\{{?{secret}\}}?",
            rf"exit\s+1.*{secret}",
            rf"{secret}.*required",
        ]:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                hard_required_patterns.append({"secret": secret, "pattern": pattern})
    return {
        "workflow_path": rel,
        "exists": path.exists(),
        "paid_secret_names_found": found,
        "policy": "optional_references_only__not_allowed_by_default__must_not_be_required_without_user_approval",
        "hard_required_patterns_found": hard_required_patterns,
        "passes_free_only_guard": not hard_required_patterns,
    }


def requirements_audit(root: Path) -> Dict[str, Any]:
    rel = "requirements.txt"
    text = read_text(root / rel)
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    suspicious = [line for line in lines if any(token in line.lower() for token in ["apisports", "serpapi", "rapidapi", "bing", "openai", "scrapingbee", "brightdata", "browserless"])]
    return {"path": rel, "exists": (root / rel).exists(), "dependencies": lines, "paid_or_llm_dependency_warnings": suspicious, "passes_free_only_guard": not suspicious}


def wnba_registry_audit(root: Path) -> Dict[str, Any]:
    base = root / "data/asset_registry/wnba"
    team_logos = read_csv(base / "team_logos.csv")
    athletes = read_csv(base / "athletes.csv")
    athlete_images = read_csv(base / "athlete_images.csv")
    approved_assets = read_csv(base / "athlete_image_approved_assets.csv")
    needs_fix = read_csv(base / "athlete_image_needs_fix.csv")
    missing_logos = read_csv(base / "missing_team_logos.csv")
    logo_approved = [r for r in team_logos if clean(r.get("approved")).lower() == "true" and clean(r.get("file_exists")).lower() == "true"]
    approved_image_rows = [r for r in athlete_images if clean(r.get("approved")).lower() == "true"]
    return {
        "folder_exists": base.exists(),
        "key_files": [file_info(root, f"data/asset_registry/wnba/{name}") for name in KEY_WNBA_FILES],
        "team_logos_rows": len(team_logos),
        "team_logos_approved_and_existing": len(logo_approved),
        "missing_team_logos_rows": len(missing_logos),
        "missing_team_logos": [r.get("team_id") for r in missing_logos if r.get("team_id")],
        "athletes_rows": len(athletes),
        "athlete_images_rows": len(athlete_images),
        "athlete_images_approved_rows": len(approved_image_rows),
        "approved_asset_rows": len(approved_assets),
        "needs_fix_rows": len(needs_fix),
        "needs_fix_athletes": [
            {"athlete_id": r.get("athlete_id"), "display_name": r.get("display_name"), "team_id": r.get("team_id"), "reason": r.get("reason")}
            for r in needs_fix
        ],
    }


def output_acceptance_audit(root: Path) -> Dict[str, Any]:
    prod_root = root / "outputs/latest/production_graphics_director"
    copy_md = prod_root / "copy_director/post_ready_copy.md"
    variant_root = prod_root / "graphics_variant_packs"
    zips_dir = variant_root / "zips"
    manifest = variant_root / "variant_manifest.csv"
    rows = read_csv(manifest)
    package_variants: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        package_variants[row.get("package_id", "")].add(row.get("variant", ""))
    missing_pairs = [pid for pid, variants in package_variants.items() if not {"logos_only", "with_players"}.issubset(variants)]
    zip_paths = list(zips_dir.glob("*.zip")) if zips_dir.exists() else []
    logos_only_zips = [p for p in zip_paths if p.name.startswith("logos_only_")]
    with_players_zips = [p for p in zip_paths if p.name.startswith("with_players_")]
    needs_fix_rows = read_csv(root / "data/asset_registry/wnba/athlete_image_needs_fix.csv")
    needs_fix_ids = {r.get("athlete_id") for r in needs_fix_rows if r.get("athlete_id")}
    needs_fix_hits: List[str] = []
    for zp in with_players_zips:
        try:
            with zipfile.ZipFile(zp) as zf:
                names = zf.namelist()
                haystack = "\n".join(names)
                for aid in sorted(needs_fix_ids):
                    if aid and aid in haystack:
                        needs_fix_hits.append(f"{zp.name}:{aid}")
                for candidate in [name for name in names if name.endswith("content_summary.json")]:
                    try:
                        data = json.loads(zf.read(candidate).decode("utf-8", errors="replace"))
                        for player in data.get("players", []) if isinstance(data, dict) else []:
                            aid = player.get("athlete_id") if isinstance(player, dict) else None
                            if aid in needs_fix_ids:
                                needs_fix_hits.append(f"{zp.name}:{aid}:content_summary")
                    except Exception:
                        pass
        except Exception as exc:
            needs_fix_hits.append(f"{zp.name}:zip_read_error:{exc}")
    prod_report = read_text(prod_root / "production_graphics_director_report.md")
    acceptance_flags = {
        "post_ready_copy_exists": copy_md.exists(),
        "graphics_variant_zips_dir_exists": zips_dir.exists(),
        "variant_manifest_exists": manifest.exists(),
        "each_manifest_package_has_logos_only_and_with_players": not missing_pairs and bool(package_variants),
        "no_needs_fix_player_in_with_players_zips": not needs_fix_hits,
        "auto_renders_human_review_only_marker_found": "Auto-renders remain human-review only" in prod_report,
    }
    return {
        "production_graphics_director_root_exists": prod_root.exists(),
        "copy_post_ready_path": rel_path(root, copy_md),
        "variant_root": rel_path(root, variant_root),
        "logos_only_zip_count": len(logos_only_zips),
        "with_players_zip_count": len(with_players_zips),
        "variant_zip_count": len(zip_paths),
        "variant_manifest_rows": len(rows),
        "variant_packages": len(package_variants),
        "missing_variant_pairs": missing_pairs,
        "needs_fix_player_hits_in_with_players_zips": needs_fix_hits,
        "acceptance_flags": acceptance_flags,
    }


def copy_sanity_sniff(root: Path) -> Dict[str, Any]:
    copy_md = root / "outputs/latest/production_graphics_director/copy_director/post_ready_copy.md"
    text = read_text(copy_md)
    sections = re.split(r"\n##\s+", "\n" + text)
    warnings = []
    team_terms = {
        "dallas": "Dallas Wings",
        "wings": "Dallas Wings",
        "vegas": "Las Vegas Aces",
        "aces": "Las Vegas Aces",
        "golden state": "Golden State Valkyries",
        "valkyries": "Golden State Valkyries",
        "sparks": "Los Angeles Sparks",
        "los angeles": "Los Angeles Sparks",
        "lpga": "LPGA",
        "gina kim": "LPGA",
        "yana wilson": "LPGA",
    }
    for section in sections:
        section = section.strip()
        if not section or section.startswith("#"):
            continue
        headline = section.splitlines()[0].strip()
        body = section.lower()
        h = headline.lower()
        local_warnings = []
        if "sparks at golden state" in h and any(term in body for term in ["lpga", "gina kim", "yana wilson"]):
            local_warnings.append("WNBA matchup heading contains LPGA copy terms")
        if "golden state valkyries beat los angeles sparks" in h and any(term in body for term in ["dallas did", "wings put", "vegas leaves"]):
            local_warnings.append("Valkyries/Sparks result appears to contain Dallas/Aces body copy")
        if local_warnings:
            warnings.append({"headline": headline, "warnings": local_warnings})
    return {"path": rel_path(root, copy_md), "exists": copy_md.exists(), "possible_mismatches": warnings}


def config_audit(root: Path) -> Dict[str, Any]:
    cfg = root / "config"
    files = []
    if cfg.exists():
        for p in sorted(cfg.glob("*.json")):
            data = read_json(p)
            files.append({"path": rel_path(root, p), "size": p.stat().st_size, "top_level_keys": sorted(data.keys())[:20] if isinstance(data, dict) else []})
    return {"folder_exists": cfg.exists(), "json_files": files, "json_file_count": len(files)}


def build_report(root: Path) -> Dict[str, Any]:
    git = detect_git_state(root)
    scripts = detect_script_versions(root)
    workflow = workflow_paid_secret_audit(root)
    req = requirements_audit(root)
    wnba = wnba_registry_audit(root)
    outputs = output_acceptance_audit(root)
    copy = copy_sanity_sniff(root)
    config = config_audit(root)
    flags = outputs.get("acceptance_flags", {})
    failures = [key for key, value in flags.items() if not value]
    free_failures = []
    if not workflow.get("passes_free_only_guard"):
        free_failures.append("workflow_has_hard_required_paid_secret")
    if not req.get("passes_free_only_guard"):
        free_failures.append("requirements_have_paid_or_llm_dependency_warning")
    copy_warnings = copy.get("possible_mismatches") or []
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": root.as_posix(),
        "git": git,
        "inventory": {
            "key_paths": [file_info(root, rel) for rel in KEY_PATHS],
            "key_dirs": [list_dir_snapshot(root, rel, max_items=60) for rel in KEY_DIRS],
        },
        "scripts": scripts,
        "workflow_paid_secret_audit": workflow,
        "requirements_audit": req,
        "config_audit": config,
        "wnba_asset_registry_audit": wnba,
        "output_acceptance_audit": outputs,
        "copy_sanity_sniff": copy,
        "recommended_first_v3_commands": RUN_COMMANDS,
        "overall_sanity": {
            "acceptance_failures": failures,
            "free_only_failures": free_failures,
            "copy_sanity_warning_count": len(copy_warnings),
            "needs_review": bool(failures or free_failures or copy_warnings),
        },
    }


def md_bool(value: Any) -> str:
    return "✅" if value else "❌"


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines: List[str] = []
    lines.append("# HSD Repo State + Pipeline Sanity Audit v3")
    lines.append("")
    lines.append(f"Generated: `{report.get('generated_at_utc')}`")
    lines.append(f"Version: `{report.get('version')}`")
    lines.append("")
    git = report.get("git", {})
    lines.append("## Repo / branch")
    lines.append(f"- Branch: `{git.get('branch')}`")
    lines.append(f"- HEAD: `{git.get('head_sha')}`")
    lines.append(f"- Dirty working tree: `{git.get('dirty')}`")
    lines.append("")
    workflow = report.get("workflow_paid_secret_audit", {})
    req = report.get("requirements_audit", {})
    lines.append("## Free-only guard")
    lines.append(f"- Workflow file exists: {md_bool(workflow.get('exists'))}")
    lines.append(f"- Paid secret names found: `{', '.join(workflow.get('paid_secret_names_found') or []) or 'none'}`")
    lines.append(f"- Policy: `{workflow.get('policy')}`")
    lines.append(f"- Hard-required paid secret patterns: `{workflow.get('hard_required_patterns_found')}`")
    lines.append(f"- Workflow passes free-only guard: {md_bool(workflow.get('passes_free_only_guard'))}")
    lines.append(f"- requirements.txt dependencies: `{req.get('dependencies')}`")
    lines.append(f"- requirements paid/LLM warnings: `{req.get('paid_or_llm_dependency_warnings')}`")
    lines.append("")
    lines.append("## Detected script versions")
    for name, info in report.get("scripts", {}).items():
        lines.append(f"- `{name}`: exists={info.get('exists')} | path=`{info.get('path')}` | versions=`{info.get('versions')}`")
        if name.startswith("render") or name == "production_graphics_director_v4_5":
            imports = [i for i in info.get("imports", []) if "generate_hsd" in i]
            if imports:
                lines.append(f"  - imports: `{imports}`")
    lines.append("")
    wnba = report.get("wnba_asset_registry_audit", {})
    lines.append("## WNBA asset registry")
    lines.append(f"- team logo rows: `{wnba.get('team_logos_rows')}`")
    lines.append(f"- approved/existing team logos: `{wnba.get('team_logos_approved_and_existing')}`")
    lines.append(f"- missing team logo rows: `{wnba.get('missing_team_logos_rows')}` `{wnba.get('missing_team_logos')}`")
    lines.append(f"- athletes: `{wnba.get('athletes_rows')}`")
    lines.append(f"- athlete image approved rows: `{wnba.get('athlete_images_approved_rows')}`")
    lines.append(f"- approved asset rows: `{wnba.get('approved_asset_rows')}`")
    lines.append(f"- needs-fix rows: `{wnba.get('needs_fix_rows')}`")
    if wnba.get("needs_fix_athletes"):
        for row in wnba.get("needs_fix_athletes", []):
            lines.append(f"  - `{row.get('athlete_id')}` — {row.get('display_name')} ({row.get('team_id')})")
    lines.append("")
    oa = report.get("output_acceptance_audit", {})
    flags = oa.get("acceptance_flags", {})
    lines.append("## First V3 acceptance checks against current outputs")
    for key, value in flags.items():
        lines.append(f"- {key}: {md_bool(value)} `{value}`")
    lines.append(f"- logos_only zips: `{oa.get('logos_only_zip_count')}`")
    lines.append(f"- with_players zips: `{oa.get('with_players_zip_count')}`")
    lines.append(f"- variant manifest rows: `{oa.get('variant_manifest_rows')}`")
    lines.append(f"- variant packages: `{oa.get('variant_packages')}`")
    if oa.get("missing_variant_pairs"):
        lines.append(f"- Missing variant pairs: `{oa.get('missing_variant_pairs')}`")
    if oa.get("needs_fix_player_hits_in_with_players_zips"):
        lines.append("- Needs-fix player hits in with_players zips:")
        for hit in oa.get("needs_fix_player_hits_in_with_players_zips", []):
            lines.append(f"  - `{hit}`")
    lines.append("")
    lines.append("## Copy sanity warnings")
    copy = report.get("copy_sanity_sniff", {})
    mismatches = copy.get("possible_mismatches") or []
    if mismatches:
        lines.append("These are heuristic warnings for obvious cross-topic bleed; they need human review before posting.")
        for item in mismatches:
            lines.append(f"- `{item.get('headline')}`: `{', '.join(item.get('warnings') or [])}`")
    else:
        lines.append("- No obvious copy/headline mismatch warnings detected by the lightweight V3 sniff test.")
    lines.append("")
    lines.append("## Key folders")
    for info in report.get("inventory", {}).get("key_dirs", []):
        lines.append(f"- `{info.get('path')}`: {info.get('type')} | exists={info.get('exists')} | files={info.get('file_count')}")
    lines.append("")
    lines.append("## Recommended first V3 run commands")
    lines.append("```bash")
    for cmd in report.get("recommended_first_v3_commands", []):
        lines.append(cmd)
    lines.append("```")
    lines.append("")
    lines.append("## Overall sanity")
    overall = report.get("overall_sanity", {})
    for key, value in overall.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build HSD repo-state + pipeline sanity audit v3.")
    parser.add_argument("--repo-root", default=None, help="Repository root. Defaults to auto-detect from cwd/script path.")
    parser.add_argument("--json", default=DEFAULT_OUTPUT_JSON, help="Output JSON path, relative to repo root unless absolute.")
    parser.add_argument("--md", default=DEFAULT_OUTPUT_MD, help="Output Markdown path, relative to repo root unless absolute.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when current-output acceptance checks fail or paid hard requirements are found.")
    args = parser.parse_args(argv)

    if args.repo_root:
        root = Path(args.repo_root).resolve()
    else:
        here = Path(__file__).resolve() if "__file__" in globals() else Path.cwd().resolve()
        root = detect_repo_root(here.parent if here.is_file() else here)

    report = build_report(root)
    json_path = Path(args.json)
    if not json_path.is_absolute():
        json_path = root / json_path
    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = root / md_path
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)

    print(json.dumps({
        "version": VERSION,
        "repo_root": root.as_posix(),
        "json": json_path.as_posix(),
        "md": md_path.as_posix(),
        "overall_sanity": report.get("overall_sanity"),
        "acceptance_flags": report.get("output_acceptance_audit", {}).get("acceptance_flags"),
    }, indent=2))

    if args.strict and report.get("overall_sanity", {}).get("needs_review"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
