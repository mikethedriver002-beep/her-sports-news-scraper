from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v1.0-template-renderer-logo-status"
DEFAULT_LOGO_AUDIT_JSON = "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_logo_audit.json"
DEFAULT_MANIFEST_JSON = "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_manifest.json"
DEFAULT_OUTPUT_JSON = "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_logo_status.json"
DEFAULT_OUTPUT_MD = "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_logo_status.md"


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


def rows_from_audit(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []


def team_key(row: Dict[str, Any]) -> str:
    return str(row.get("team_id") or row.get("team") or "").strip()


def build_report(logo_audit_path: Path, manifest_path: Path) -> Dict[str, Any]:
    audit_payload = read_json(logo_audit_path)
    manifest = read_json(manifest_path)
    rows = rows_from_audit(audit_payload)

    warning_rows = [r for r in rows if str(r.get("status")) == "warning_fallback"]
    active_fallback_rows = [
        r for r in warning_rows
        if str(r.get("source")) == "fallback" and str(r.get("path_or_url")) == "team_name_badge"
    ]
    recoverable_warning_rows = [r for r in warning_rows if r not in active_fallback_rows]
    loaded_rows = [r for r in rows if str(r.get("status")) == "loaded"]

    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "logo_audit_json": logo_audit_path.as_posix(),
        "renderer_manifest_json": manifest_path.as_posix(),
        "renderer_version": manifest.get("version"),
        "rendered_count": manifest.get("rendered_count"),
        "logo_audit_rows": len(rows),
        "loaded_logo_rows": len(loaded_rows),
        "logo_warning_rows": len(warning_rows),
        "recoverable_logo_warnings": len(recoverable_warning_rows),
        "active_logo_fallbacks": len(active_fallback_rows),
        "effective_publish_status": "blocked_active_logo_fallback" if active_fallback_rows else "no_active_logo_fallback",
        "recoverable_warning_teams": sorted({team_key(r) for r in recoverable_warning_rows if team_key(r)}),
        "active_fallback_teams": sorted({team_key(r) for r in active_fallback_rows if team_key(r)}),
        "recoverable_warning_rows": recoverable_warning_rows,
        "active_fallback_rows": active_fallback_rows,
        "policy": {
            "active_logo_fallback_definition": "source=fallback and path_or_url=team_name_badge",
            "recoverable_warning_definition": "a failed local/remote attempt that later may still load through another approved source",
            "human_review_required": True,
        },
    }


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# HSD Template Renderer Logo Status",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Version: `{report.get('version')}`",
        "",
        "## Summary",
        "",
        f"- Renderer version: `{report.get('renderer_version')}`",
        f"- Rendered count: `{report.get('rendered_count')}`",
        f"- Logo audit rows: `{report.get('logo_audit_rows')}`",
        f"- Loaded logo rows: `{report.get('loaded_logo_rows')}`",
        f"- Logo warning rows: `{report.get('logo_warning_rows')}`",
        f"- Recoverable logo warnings: `{report.get('recoverable_logo_warnings')}`",
        f"- Active logo fallbacks: `{report.get('active_logo_fallbacks')}`",
        f"- Effective publish status: `{report.get('effective_publish_status')}`",
        "",
        "## Recoverable warnings",
        "",
    ]
    teams = report.get("recoverable_warning_teams") or []
    lines += [f"- `{team}`" for team in teams] if teams else ["- None"]
    lines += ["", "## Active fallbacks", ""]
    teams = report.get("active_fallback_teams") or []
    lines += [f"- `{team}`" for team in teams] if teams else ["- None"]
    lines += [
        "",
        "Policy: a recoverable warning is not the same as an active fallback. An active fallback means the renderer used a text/team-name badge because no approved logo loaded.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize HSD Template Renderer v2 logo status.")
    parser.add_argument("--logo-audit-json", default=DEFAULT_LOGO_AUDIT_JSON)
    parser.add_argument("--manifest-json", default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when active logo fallbacks exist.")
    args = parser.parse_args(argv)

    report = build_report(Path(args.logo_audit_json), Path(args.manifest_json))
    out_json = Path(args.json)
    out_md = Path(args.md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, out_md)

    print(json.dumps({
        "version": VERSION,
        "active_logo_fallbacks": report.get("active_logo_fallbacks"),
        "recoverable_logo_warnings": report.get("recoverable_logo_warnings"),
        "effective_publish_status": report.get("effective_publish_status"),
        "json": out_json.as_posix(),
        "md": out_md.as_posix(),
    }, indent=2))

    if args.strict and report.get("active_logo_fallbacks"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
