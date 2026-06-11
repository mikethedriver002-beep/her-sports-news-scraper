from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "hsd-publish-guard-v3.2.5-bebe-ops-v2.4"
OUT_JSON = Path("publish_guard_report.json")
OUT_MD = Path("publish_guard_report.md")
LEDGER = Path("audit/publish_ledger.jsonl")


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def fingerprint(row: Dict[str, str]) -> str:
    blob = "|".join([
        clean(row.get("content_type")),
        clean(row.get("headline")),
        clean(row.get("event_date")),
        clean(row.get("source_id")),
    ])
    return hashlib.sha256(blob.encode()).hexdigest()


def load_ledger() -> set[str]:
    if not LEDGER.exists():
        return set()
    vals = set()
    for line in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            j = json.loads(line)
            vals.add(j.get("publish_fingerprint", ""))
        except Exception:
            pass
    return vals


def add_issue(issues: List[Dict[str, str]], severity: str, code: str, detail: str = "", headline: str = "") -> None:
    issues.append({"severity": severity, "code": code, "detail": detail, "headline": headline})


def preview_gate_status() -> Tuple[str, str]:
    rows = read_csv("preview_bundle_quality_summary.csv")
    if not rows:
        return "not_run", "preview_bundle_quality_summary.csv missing"
    row = rows[0]
    return clean(row.get("gate_status")) or "unknown", clean(row.get("block_reason"))


def graphics_qa_status() -> Tuple[str, str]:
    rows = read_csv("graphics_qa_results.csv")
    if not rows:
        return "not_run", "graphics_qa_results.csv missing"
    decisions = sorted({clean(r.get("decision")) for r in rows if clean(r.get("decision"))})
    if any(d == "fail" for d in decisions):
        return "fail", "; ".join(decisions)
    if any(d in {"revise", "pass_with_review"} for d in decisions):
        return "review", "; ".join(decisions)
    return "pass", "; ".join(decisions)


def rendered_qa_status() -> Tuple[str, str]:
    manifest = read_json("rendered_slide_qa_manifest.json")
    counts = manifest.get("counts", {}) if isinstance(manifest, dict) else {}
    decision = clean(counts.get("decision")) or "not_run"
    files_checked = clean(counts.get("files_checked")) or "0"
    return decision, f"files_checked={files_checked}"


def main() -> None:
    publish_mode = os.environ.get("HSD_PUBLISH_MODE", "artifact_only")
    requested_publish = os.environ.get("HSD_PUBLISH_OUTPUTS", "false").lower() == "true"
    slate = read_csv("daily_slate_plan.csv")
    upload_rows = read_csv("graphics_upload_pack_status.csv")
    ready_clean = [r for r in upload_rows if r.get("upload_pack_status") == "ready"]
    ready_review = [r for r in upload_rows if r.get("upload_pack_status") == "ready_with_review"]
    blocked_packs = [r for r in upload_rows if r.get("upload_pack_status") not in {"ready", "ready_with_review"}]
    graphics_handoff_packs = ready_clean + ready_review
    ledger = load_ledger()
    issues: List[Dict[str, str]] = []
    decisions: List[Dict[str, str]] = []

    for r in slate:
        fp = fingerprint(r)
        if fp in ledger:
            add_issue(issues, "critical", "duplicate_publish_fingerprint", headline=r.get("headline", ""))
        decisions.append({
            "headline": r.get("headline", ""),
            "content_type": r.get("content_type", ""),
            "fingerprint": fp,
            "status": "candidate",
        })

    if not slate and not graphics_handoff_packs:
        add_issue(issues, "critical", "no_content_ready", "No slate items and no ready graphics upload pack.")
    if upload_rows and not graphics_handoff_packs:
        add_issue(issues, "critical", "no_ready_upload_pack", "Graphics packs exist but none are ready or ready_with_review.")
    for r in blocked_packs:
        add_issue(issues, "critical", "blocked_upload_pack", r.get("missing_asset_names") or r.get("notes") or r.get("upload_pack_status", ""), r.get("bundle_name", ""))
    for r in ready_review:
        add_issue(issues, "review", "ready_with_review_upload_pack", "Manual visual review required before graphics or posting.", r.get("bundle_name", ""))

    p_status, p_reason = preview_gate_status()
    if p_status.upper() == "FAIL":
        add_issue(issues, "critical", "preview_quality_gate_failed", p_reason or "Preview quality gate failed.")
    elif p_status not in {"PASS", "not_run"}:
        add_issue(issues, "review", "preview_quality_gate_review", p_reason or f"Preview gate status={p_status}")

    g_status, g_detail = graphics_qa_status()
    if g_status == "fail":
        add_issue(issues, "critical", "graphics_qa_failed", g_detail)
    elif g_status == "review":
        add_issue(issues, "review", "graphics_qa_review", g_detail)

    r_status, r_detail = rendered_qa_status()
    # No rendered files is normal before image generation. It blocks auto-publish, not graphics handoff.
    if r_status in {"blocked", "fail"}:
        add_issue(issues, "critical", "rendered_slide_qa_failed", r_detail)
    elif r_status in {"needs_manual_review", "not_checked_no_files", "not_run"}:
        add_issue(issues, "review", "rendered_slide_qa_pending", r_detail)

    critical = any(i["severity"] == "critical" for i in issues)
    review = any(i["severity"] == "review" for i in issues)
    graphics_handoff_allowed = bool(graphics_handoff_packs) and not critical

    # HSD is manual-first. `publish_allowed` means clean enough for a reviewed/manual publish path,
    # not that the workflow should auto-post. Artifact-only mode always keeps publish_allowed false.
    publish_allowed = (
        requested_publish
        and publish_mode == "reviewed"
        and bool(ready_clean)
        and not critical
        and not review
    )

    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "publish_mode": publish_mode,
        "requested_publish": requested_publish,
        "publish_allowed": publish_allowed,
        "graphics_handoff_allowed": graphics_handoff_allowed,
        "ready_upload_packs": len(ready_clean),
        "ready_with_review_upload_packs": len(ready_review),
        "blocked_upload_packs": len(blocked_packs),
        "slate_items": len(slate),
        "preview_gate_status": p_status,
        "graphics_qa_status": g_status,
        "rendered_qa_status": r_status,
        "issues": issues,
        "decisions": decisions,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# HSD Publish Guard",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Version: {VERSION}",
        "",
        f"- publish_mode: {publish_mode}",
        f"- requested_publish: {requested_publish}",
        f"- publish_allowed: {publish_allowed}",
        f"- graphics_handoff_allowed: {graphics_handoff_allowed}",
        f"- ready_upload_packs: {len(ready_clean)}",
        f"- ready_with_review_upload_packs: {len(ready_review)}",
        f"- blocked_upload_packs: {len(blocked_packs)}",
        f"- slate_items: {len(slate)}",
        f"- preview_gate_status: {p_status}",
        f"- graphics_qa_status: {g_status}",
        f"- rendered_qa_status: {r_status}",
        "",
    ]
    if issues:
        lines += ["## Issues / Review Notes", ""]
        lines += [f"- {i['severity']} | {i['code']} | {i.get('headline') or i.get('detail', '')}" for i in issues]
        lines.append("")
    if graphics_handoff_allowed:
        lines += [
            "## Operator decision",
            "",
            "A graphics handoff is allowed, but manual review is still required for any `ready_with_review` pack and for rendered slides after generation.",
            "",
        ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"publish_allowed": publish_allowed, "graphics_handoff_allowed": graphics_handoff_allowed, "issues": len(issues)}, indent=2))


if __name__ == "__main__":
    main()
