from __future__ import annotations

import csv
import json
import re
import subprocess
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v3.0-repo-state-pipeline-sanity-audit"
ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
WORKFLOW = ROOT / ".github/workflows/hsd-pipeline-control-v1.yml"
REQUIREMENTS = ROOT / "requirements.txt"
VARIANT_SCRIPT = ROOT / "scripts/generate_hsd_graphics_variant_packs_v1.py"
PROD_ROOT = ROOT / "outputs/latest/production_graphics_director"
COPY_READY = PROD_ROOT / "copy_director/post_ready_copy.md"
VARIANT_ROOT = PROD_ROOT / "graphics_variant_packs"
VARIANT_ZIPS = VARIANT_ROOT / "zips"
VARIANT_MANIFEST = VARIANT_ROOT / "variant_manifest.csv"
NEEDS_FIX = ROOT / "data/asset_registry/wnba/athlete_image_needs_fix.csv"
SUMMARY = ROOT / "outputs/latest/summary.json"
PAID_SECRETS = ["APISPORTS_KEY", "BING_SEARCH_API_KEY", "SERPAPI_KEY"]
KEY_PATHS = [
    ".github/workflows",
    "requirements.txt",
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


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(text(path)) if path.exists() else {}
    except Exception:
        return {}


def git(args: List[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def version_const(path: Path) -> str:
    m = re.search(r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']', text(path), flags=re.M)
    return m.group(1) if m else ""


def imports(path: Path) -> List[str]:
    out: List[str] = []
    for m in re.finditer(r"^\s*import\s+(generate_hsd_[A-Za-z0-9_]+)(?:\s+as\s+([A-Za-z0-9_]+))?", text(path), flags=re.M):
        out.append(m.group(1) + (f" as {m.group(2)}" if m.group(2) else ""))
    return out


def vkey(path: Path) -> List[int]:
    nums = re.findall(r"\d+", path.stem)
    return [int(n) for n in nums] or [0]


def scan_scripts(pattern: str) -> List[Dict[str, Any]]:
    return [
        {"path": rel(p), "version_constant": version_const(p), "import_targets": imports(p)}
        for p in sorted((ROOT / "scripts").glob(pattern), key=vkey)
    ]


def sample(path: Path, limit: int = 25) -> List[str]:
    if not path.exists():
        return []
    if path.is_file():
        return [rel(path)]
    out: List[str] = []
    for p in sorted(path.rglob("*")):
        if p.is_file():
            out.append(rel(p))
        if len(out) >= limit:
            break
    return out


def file_count(path: Path) -> int:
    if path.is_file():
        return 1
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def path_report(path_text: str) -> Dict[str, Any]:
    path = ROOT / path_text
    return {
        "path": path_text,
        "exists": path.exists(),
        "type": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
        "file_count": file_count(path),
        "sample_files": sample(path),
    }


def paid_secret_audit() -> Dict[str, Any]:
    wf = text(WORKFLOW)
    secrets: Dict[str, Any] = {}
    for name in PAID_SECRETS:
        present = name in wf
        secrets[name] = {
            "workflow_reference_present": present,
            "secret_expression_present": f"secrets.{name}" in wf,
            "policy": "optional_not_allowed_by_default" if present else "not_referenced",
            "required_by_default": False,
        }
    hard_hits = []
    for base in [ROOT, ROOT / "scripts"]:
        if not base.exists():
            continue
        paths = list(base.glob("*.py")) if base == ROOT else list(base.rglob("*.py"))
        for path in paths:
            body = text(path)
            for name in PAID_SECRETS:
                if re.search(rf"os\.environ\[['\"]{re.escape(name)}['\"]\]", body):
                    hard_hits.append({"path": rel(path), "secret": name, "pattern": "os.environ[...]"})
    return {
        "workflow_path": rel(WORKFLOW),
        "workflow_exists": WORKFLOW.exists(),
        "secrets": secrets,
        "hard_required_pattern_hits": hard_hits,
        "no_paid_source_required_by_default": not hard_hits,
        "policy_note": "Free-only: paid APIs/sources are not allowed by default; historical secret names must remain optional unless explicitly approved.",
    }


def variant_pair_audit() -> Dict[str, Any]:
    manifest = rows(VARIANT_MANIFEST)
    packages: Dict[str, set[str]] = defaultdict(set)
    packages_with_player_assets = set()
    for row in manifest:
        pid = row.get("package_id", "")
        variant = row.get("variant", "")
        if pid and variant:
            packages[pid].add(variant)
        if pid and int(row.get("player_assets") or 0) > 0:
            packages_with_player_assets.add(pid)
    missing_manifest_pairs = [
        {"package_id": pid, "variants_found": sorted(found)}
        for pid, found in sorted(packages.items())
        if not {"logos_only", "with_players"}.issubset(found)
    ]

    zip_files = sorted(p.name for p in VARIANT_ZIPS.glob("*.zip")) if VARIANT_ZIPS.exists() else []
    zip_pairs: Dict[str, set[str]] = defaultdict(set)
    for name in zip_files:
        if name.startswith("logos_only_"):
            zip_pairs[name[len("logos_only_"):-4]].add("logos_only")
        if name.startswith("with_players_"):
            zip_pairs[name[len("with_players_"):-4]].add("with_players")
    missing_zip_pairs = [
        {"zip_slug": slug, "variants_found": sorted(found)}
        for slug, found in sorted(zip_pairs.items())
        if not {"logos_only", "with_players"}.issubset(found)
    ]
    return {
        "variant_manifest_exists": VARIANT_MANIFEST.exists(),
        "zip_dir_exists": VARIANT_ZIPS.exists(),
        "manifest_rows": len(manifest),
        "package_count_from_manifest": len(packages),
        "packages_with_player_assets": len(packages_with_player_assets),
        "zip_count": len(zip_files),
        "zip_samples": zip_files[:30],
        "missing_manifest_pairs": missing_manifest_pairs,
        "missing_zip_pairs": missing_zip_pairs,
        "pairs_ok": not missing_manifest_pairs if manifest else not missing_zip_pairs,
    }


def needs_fix_audit() -> Dict[str, Any]:
    blocked = {r.get("athlete_id", "") for r in rows(NEEDS_FIX) if r.get("athlete_id")}
    hits = []
    summaries = sorted((VARIANT_ROOT / "with_players").glob("*/content_summary.json")) if VARIANT_ROOT.exists() else []
    for path in summaries:
        data = load_json(path)
        for player in data.get("players", []) or []:
            aid = str(player.get("athlete_id", ""))
            if aid in blocked:
                hits.append({"path": rel(path), "athlete_id": aid, "display_name": player.get("display_name", "")})
        for asset in data.get("player_assets", []) or []:
            for aid in blocked:
                if aid and aid in str(asset):
                    hits.append({"path": rel(path), "athlete_id": aid, "display_name": "asset_path_hit"})
    zip_hits = []
    for zp in sorted(VARIANT_ZIPS.glob("with_players_*.zip")) if VARIANT_ZIPS.exists() else []:
        try:
            names = zipfile.ZipFile(zp).namelist()
            for aid in blocked:
                if any(aid in name for name in names):
                    zip_hits.append({"zip_path": rel(zp), "athlete_id": aid})
        except Exception as exc:
            zip_hits.append({"zip_path": rel(zp), "error": type(exc).__name__})
    return {
        "needs_fix_registry_exists": NEEDS_FIX.exists(),
        "needs_fix_count": len(blocked),
        "needs_fix_ids": sorted(blocked),
        "with_players_content_summaries": len(summaries),
        "content_summary_hits": hits,
        "zip_member_hits": [h for h in zip_hits if h.get("athlete_id")],
        "zip_read_errors": [h for h in zip_hits if h.get("error")],
        "no_needs_fix_players_in_variant_packs": not hits and not [h for h in zip_hits if h.get("athlete_id")],
    }


def review_policy_audit() -> Dict[str, Any]:
    markers = []
    for path in [ROOT / "outputs/latest/README.md", PROD_ROOT / "production_graphics_director_report.md"]:
        body = text(path).lower()
        for phrase in ["review before posting", "human-review only", "does not publish", "auto-renders remain human-review only"]:
            if phrase in body:
                markers.append({"path": rel(path), "marker": phrase})
    wf = text(WORKFLOW).lower()
    publish_safe = "default: \"false\"" in wf and "artifact_only" in wf
    return {"markers_found": markers, "workflow_publish_defaults_safe": publish_safe, "auto_renders_human_review_only": bool(markers) and publish_safe}


def acceptance() -> Dict[str, Any]:
    pairs = variant_pair_audit()
    needs = needs_fix_audit()
    review = review_policy_audit()
    paid = paid_secret_audit()
    tests = {
        "post_ready_copy_exists": COPY_READY.exists(),
        "graphics_variant_zip_dir_exists": VARIANT_ZIPS.exists(),
        "variant_pairs_ok": pairs["pairs_ok"],
        "no_needs_fix_player_image_in_player_packs": needs["no_needs_fix_players_in_variant_packs"],
        "auto_renders_remain_human_review_only": review["auto_renders_human_review_only"],
        "no_paid_api_source_required": paid["no_paid_source_required_by_default"],
    }
    return {"passed": all(tests.values()), "tests": tests, "details": {"variant_pairs": pairs, "needs_fix_players": needs, "review_policy": review, "paid_secret_policy": paid}}


def build() -> Dict[str, Any]:
    prod = scan_scripts("generate_hsd_mermaid_production_graphics_director_v*.py")
    render = scan_scripts("generate_hsd_mermaid_render_studio_v*.py")
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": str(ROOT),
        "git": {
            "current_branch": git(["branch", "--show-current"]),
            "head_sha": git(["rev-parse", "HEAD"]),
            "default_branch_guess": git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]).replace("origin/", "") or "main",
            "status_short": git(["status", "--short"]),
        },
        "workflow": {"path": rel(WORKFLOW), "exists": WORKFLOW.exists()},
        "requirements": {"path": rel(REQUIREMENTS), "exists": REQUIREMENTS.exists(), "lines": [x.strip() for x in text(REQUIREMENTS).splitlines() if x.strip() and not x.strip().startswith("#")]},
        "key_paths": [path_report(p) for p in KEY_PATHS],
        "production_graphics_directors": prod,
        "latest_production_graphics_director": prod[-1] if prod else {},
        "render_wrappers": render,
        "render_entrypoint": next((r for r in render if r["path"].endswith("generate_hsd_mermaid_render_studio_v3_0_1.py")), render[-1] if render else {}),
        "graphics_variant_packs_script": {"path": rel(VARIANT_SCRIPT), "exists": VARIANT_SCRIPT.exists(), "version_constant": version_const(VARIANT_SCRIPT), "import_targets": imports(VARIANT_SCRIPT)},
        "outputs_summary": load_json(SUMMARY),
        "acceptance": acceptance(),
    }


def yes(value: Any) -> str:
    return "PASS" if value else "FAIL"


def write_md(report: Dict[str, Any], path: Path) -> None:
    lines = ["# HSD Repo State V3 Audit", "", f"Generated: `{report['generated_at_utc']}`", f"Version: `{report['version']}`", ""]
    git_state = report["git"]
    lines += ["## Git state", "", f"- current branch: `{git_state.get('current_branch') or 'unknown'}`", f"- default branch guess: `{git_state.get('default_branch_guess') or 'main'}`", f"- HEAD: `{git_state.get('head_sha') or 'unknown'}`", ""]
    lines += ["## Requirements", "", f"- requirements.txt exists: `{report['requirements']['exists']}`", f"- requirements: `{', '.join(report['requirements']['lines']) or 'none'}`", ""]
    lines += ["## Key paths", "", "| Path | Type | Exists | File count |", "|---|---:|---:|---:|"]
    for item in report["key_paths"]:
        lines.append(f"| `{item['path']}` | {item['type']} | {item['exists']} | {item['file_count']} |")
    lines.append("")
    lines += ["## Production Graphics Director versions", ""]
    for item in report["production_graphics_directors"]:
        lines.append(f"- `{item['path']}` — VERSION `{item.get('version_constant') or 'not declared'}`")
    lines += ["", "## Render wrappers", ""]
    for item in report["render_wrappers"]:
        lines.append(f"- `{item['path']}` — VERSION `{item.get('version_constant') or 'not declared'}` — imports: `{'; '.join(item.get('import_targets') or []) or 'none detected'}`")
    variant = report["graphics_variant_packs_script"]
    lines += ["", "## Graphics Variant Packs v1 script", "", f"- exists: `{variant['exists']}`", f"- path: `{variant['path']}`", f"- VERSION: `{variant.get('version_constant') or 'not declared'}`", ""]
    paid = report["acceptance"]["details"]["paid_secret_policy"]
    lines += ["## Paid-source secret policy", "", paid["policy_note"], "", "| Secret | Workflow ref | Secret expression | Required by default | Policy |", "|---|---:|---:|---:|---|"]
    for name, info in paid["secrets"].items():
        lines.append(f"| `{name}` | {info['workflow_reference_present']} | {info['secret_expression_present']} | {info['required_by_default']} | `{info['policy']}` |")
    lines.append("")
    lines += ["## First V3 acceptance checks", "", "| Check | Result |", "|---|---:|"]
    for name, result in report["acceptance"]["tests"].items():
        lines.append(f"| `{name}` | **{yes(result)}** |")
    lines += ["", f"Overall: **{yes(report['acceptance']['passed'])}**", ""]
    details = report["acceptance"]["details"]
    pair = details["variant_pairs"]
    lines += ["## Variant pack detail", "", f"- manifest rows: `{pair['manifest_rows']}`", f"- packages from manifest: `{pair['package_count_from_manifest']}`", f"- packages with player assets: `{pair['packages_with_player_assets']}`", f"- zip count: `{pair['zip_count']}`", f"- missing manifest pairs: `{len(pair['missing_manifest_pairs'])}`", f"- missing zip pairs: `{len(pair['missing_zip_pairs'])}`", ""]
    needs = details["needs_fix_players"]
    lines += ["## Needs-fix player audit", "", f"- needs-fix count: `{needs['needs_fix_count']}`", f"- needs-fix IDs: `{', '.join(needs['needs_fix_ids']) or 'none'}`", f"- content summary hits: `{len(needs['content_summary_hits'])}`", f"- zip member hits: `{len(needs['zip_member_hits'])}`", ""]
    lines += ["## Commands to run next", "", "```bash", "python verify_hsd_install_v1.py", "python scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py", "python scripts/generate_hsd_graphics_variant_packs_v1.py", "python generate_hsd_pipeline_review_lite_v1.py", "python scripts/report_hsd_repo_state_v3.py", "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = build()
    (ROOT / "repo_state_v3.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_md(report, ROOT / "repo_state_v3.md")
    print(json.dumps({"version": VERSION, "repo_state_v3_json": "repo_state_v3.json", "repo_state_v3_md": "repo_state_v3.md", "acceptance_passed": report["acceptance"]["passed"], "tests": report["acceptance"]["tests"]}, indent=2))


if __name__ == "__main__":
    main()
