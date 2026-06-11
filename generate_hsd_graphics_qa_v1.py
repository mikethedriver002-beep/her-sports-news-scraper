from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import pytesseract
except Exception:
    pytesseract = None

VERSION = "hsd-graphics-qa-scorer-v1.9-bebe-ops-v2.2"
INPUT_RENDER_MANIFEST = os.environ.get("HSD_RENDER_MANIFEST", "studio_render_manifest_v2.json")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_BANNED = "graphics_banned_language.csv"
FIELDS = [
    "qa_run_id",
    "bundle_id",
    "post_slug",
    "template_name",
    "render_path",
    "score_total",
    "critical_fail",
    "decision",
    "issues_json",
    "remediation_suggestions",
    "checked_utc",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv_any(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ocr_text(image_path: str) -> Tuple[str, str]:
    p = Path(image_path)
    if not p.exists():
        return "", "missing"
    if pytesseract and Image:
        try:
            txt = pytesseract.image_to_string(Image.open(p))
            return txt or "", "pytesseract"
        except Exception:
            pass
    try:
        res = subprocess.run(["tesseract", str(p), "stdout"], capture_output=True, text=True, timeout=45)
        if res.returncode == 0:
            return res.stdout or "", "tesseract_cli"
    except Exception:
        pass
    return "", "unavailable"


def infer_slide_number(render_path: str) -> int:
    name = Path(render_path).stem.lower()
    m = re.search(r"(?:slide|slid|s)[_\-\s]?(\d+)", name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 0
    return 0


def issue(issues: List[Dict[str, str]], code: str, severity: str, message: str = "") -> None:
    issues.append({"code": code, "severity": severity, "message": message})


def has_critical(issues: List[Dict[str, str]]) -> bool:
    return any(i.get("severity") == "critical" for i in issues)


def has_review_or_major(issues: List[Dict[str, str]]) -> bool:
    return any(i.get("severity") in {"review", "major"} for i in issues)


def main() -> None:
    Path("graphics_qa_dashboard").mkdir(exist_ok=True)
    player_reqs = read_csv_any("player_image_requirements.csv")
    missing_required_players = [r for r in player_reqs if r.get("required") == "Yes" and not r.get("approved_asset_id")]
    manifest = read_json(INPUT_RENDER_MANIFEST)
    approved = {r.get("approved_asset_id") for r in read_csv_any(INPUT_APPROVED_ASSETS) if r.get("approved_asset_id")}
    banned_terms = [clean(r.get("term")) for r in read_csv_any(INPUT_BANNED) if clean(r.get("term"))]
    upload_status_rows = {r.get("post_slug"): r for r in read_csv_any("graphics_upload_pack_status.csv") if r.get("post_slug")}
    freshness_rows = {r.get("bundle_slug"): r for r in read_csv_any("studio_freshness_gate.csv") if r.get("bundle_slug")}
    player_fit_rows = read_csv_any("player_image_fit_gate.csv")
    preview_summary = read_csv_any("preview_bundle_quality_summary.csv")
    preview_status = clean(preview_summary[0].get("gate_status")) if preview_summary else ""
    bundles = manifest.get("bundles", [])
    rows: List[Dict[str, Any]] = []
    run = "qa_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for b in bundles:
        issues: List[Dict[str, str]] = []
        score = 100
        post_slug = clean(b.get("post_slug"))
        template_name = clean(b.get("template_name"))
        bundle_type = clean(b.get("bundle_type") or b.get("template_name") or b.get("content_family"))
        is_preview = "preview" in (post_slug + " " + template_name + " " + bundle_type).lower() or post_slug == "tonight-in-the-w"

        if is_preview and preview_status and preview_status.upper() != "PASS":
            issue(issues, "PREVIEW_GATE_NOT_PASSING", "critical", f"preview_gate={preview_status}")
            score -= 50

        if not clean(b.get("source_facts", {}).get("accuracy_lock")) and not clean(b.get("source_facts", {}).get("source_headlines")):
            issue(issues, "MISSING_FACT_LOCK", "major", "No source facts or accuracy lock.")
            score -= 15

        for aid in b.get("asset_ids", []):
            if aid and aid not in approved:
                issue(issues, "UNAPPROVED_ASSET", "critical", aid)
                score -= 40
        if b.get("fact_warning_count", 0):
            issue(issues, "FACT_WARNING_PRESENT", "critical", f"{b.get('fact_warning_count')} fact warnings present")
            score -= 35
        if not any("watermark" in clean(x.get("layer_id")).lower() for x in b.get("all_layers", [])):
            issue(issues, "MISSING_WATERMARK", "major", "No watermark layer detected in render manifest.")
            score -= 10
        if not is_preview and post_slug == "main-wnba-result" and missing_required_players:
            issue(issues, "MISSING_REQUIRED_PLAYER_IMAGES", "critical", ", ".join([r.get("player_name", "") for r in missing_required_players]))
            score -= 45

        upload_row = upload_status_rows.get(post_slug)
        upload_status = clean(upload_row.get("upload_pack_status")) if upload_row else ""
        if upload_row:
            if upload_status == "ready_with_review":
                issue(issues, "UPLOAD_PACK_READY_WITH_REVIEW", "review", "Upload pack complete, but public player images/crop rules require manual visual review.")
                score -= 2
            elif upload_status != "ready":
                issue(issues, "UPLOAD_PACK_BLOCKED", "critical", upload_row.get("missing_asset_names") or upload_status)
                score -= 45
        else:
            issue(issues, "UPLOAD_PACK_STATUS_MISSING", "major", "graphics_upload_pack_status.csv has no row for this bundle")
            score -= 10

        freshness = freshness_rows.get(post_slug)
        if freshness:
            if freshness.get("freshness_decision") == "block":
                issue(issues, "FRESHNESS_GATE_BLOCKED", "critical", freshness.get("reason", "stale or missing event date"))
                score -= 45
            elif freshness.get("freshness_decision") == "review":
                issue(issues, "FRESHNESS_GATE_REVIEW", "major", freshness.get("reason", "freshness review required"))
                score -= 10
        elif post_slug == "main-wnba-result":
            issue(issues, "FRESHNESS_GATE_MISSING", "major", "studio_freshness_gate.csv missing row for main bundle")
            score -= 8

        fit_for_bundle = [r for r in player_fit_rows if r.get("bundle_slug") == post_slug]
        blocked_fit = [r for r in fit_for_bundle if r.get("fit_status", "").startswith("blocked")]
        review_fit = [r for r in fit_for_bundle if r.get("fit_status") == "review"]
        if blocked_fit:
            issue(issues, "PLAYER_IMAGE_FIT_BLOCKED", "critical", ", ".join(r.get("player_name", "") for r in blocked_fit))
            score -= 35
        elif review_fit:
            issue(issues, "PLAYER_IMAGE_FIT_REVIEW", "review", "Use tight crop rules for: " + ", ".join(r.get("player_name", "") for r in review_fit))
            score -= 3

        prompt_pack_path = Path("graphics_chat_upload_pack") / post_slug / "00_PROMPT_TO_PASTE.md"
        render_path = clean(b.get("render_path"))
        if prompt_pack_path.exists():
            prompt_text = prompt_pack_path.read_text(encoding="utf-8", errors="replace")
            prompt_hits = [term for term in banned_terms if clean(term).lower() in clean(prompt_text).lower()]
            if prompt_hits:
                issue(issues, "PROMPT_NOT_SANITIZED", "critical", ", ".join(prompt_hits))
                score -= 35
            if is_preview and any(x in clean(prompt_text).lower() for x in [" final ", " winner ", " loser ", "verified final"]):
                issue(issues, "PREVIEW_PROMPT_HAS_RESULT_LANGUAGE", "critical", "Preview prompt appears to include result language.")
                score -= 35
        else:
            issue(issues, "UPLOAD_PROMPT_MISSING", "major", str(prompt_pack_path))
            score -= 10

        if render_path and Path(render_path).exists():
            if Image:
                try:
                    width, height = Image.open(render_path).size
                    if (width, height) != (1080, 1350):
                        issue(issues, "DIMENSION_MISMATCH", "major", f"Expected 1080x1350, got {width}x{height}")
                        score -= 10
                except Exception:
                    pass
            ocr, ocr_method = ocr_text(render_path)
            ocr_clean = clean(ocr).lower()
            if ocr_method == "unavailable":
                issue(issues, "OCR_UNAVAILABLE", "review", "No OCR engine available. Render QA partially skipped.")
                score -= 2
            if ocr_clean:
                hits = [term for term in banned_terms if clean(term).lower() in ocr_clean]
                if hits:
                    issue(issues, "BANNED_LANGUAGE_RENDERED", "critical", ", ".join(hits))
                    score -= 35
                if is_preview and any(x in ocr_clean for x in ["verified final", "winner", "loser"]):
                    issue(issues, "ROBOTIC_PREVIEW_LANGUAGE", "critical", "Preview render contains banned robotic/result language.")
                    score -= 25
            else:
                issue(issues, "OCR_NO_TEXT", "review", "Rendered image found but OCR extracted no text.")
                score -= 3
        else:
            issue(issues, "RENDER_NOT_FOUND", "review", "Graphic file not exported yet. Manifest/upload-pack QA only.")
            score -= 3

        score = max(0, score)
        if has_critical(issues) or score < 70:
            decision = "fail"
        elif has_review_or_major(issues) or score < 92:
            decision = "pass_with_review"
        else:
            decision = "pass"

        remediation: List[str] = []
        codes = {i["code"] for i in issues}
        if "UPLOAD_PACK_READY_WITH_REVIEW" in codes or "PLAYER_IMAGE_FIT_REVIEW" in codes:
            remediation.append("Visually verify public player images, crop tightly, and avoid wrong-team jersey/context before generation.")
        if "RENDER_NOT_FOUND" in codes:
            remediation.append("Generate separate 1080x1350 slide files, upload them to rendered_graphics_input/, and rerun rendered-slide QA.")
        if "UPLOAD_PACK_BLOCKED" in codes or "UPLOAD_PACK_STATUS_MISSING" in codes:
            remediation.append("Resolve upload pack status before graphics handoff.")
        if any(c in codes for c in {"BANNED_LANGUAGE_RENDERED", "ROBOTIC_PREVIEW_LANGUAGE", "PROMPT_NOT_SANITIZED", "PREVIEW_PROMPT_HAS_RESULT_LANGUAGE"}):
            remediation.append("Strip banned/result/internal terms and rerender.")
        if "DIMENSION_MISMATCH" in codes:
            remediation.append("Export 1080x1350 portrait slides.")
        if not remediation:
            remediation.append("Proceed to manual review and rendered-slide QA before posting.")

        rows.append({
            "qa_run_id": run,
            "bundle_id": b.get("bundle_id"),
            "post_slug": post_slug,
            "template_name": template_name,
            "render_path": render_path,
            "score_total": score,
            "critical_fail": "Yes" if decision == "fail" else "No",
            "decision": decision,
            "issues_json": json.dumps(issues),
            "remediation_suggestions": " ".join(remediation),
            "checked_utc": now(),
        })

    write_csv("graphics_qa_results.csv", rows, FIELDS)
    report = ["# HSD Graphics QA Scorer v1.9 BeBe Ops v2.2 Report", "", f"Generated: {now()}", "", f"Bundles scored: {len(rows)}", ""]
    if not rows:
        report += ["No bundles found in render manifest. Run Visual Upgrade first."]
    for r in rows:
        report += [
            f"## {r['post_slug']}",
            "",
            f"- Decision: **{r['decision']}**",
            f"- Score: {r['score_total']}",
            f"- Render path: `{r['render_path']}`",
            f"- Issues: `{r['issues_json']}`",
            f"- Remediation: {r['remediation_suggestions']}",
            "",
        ]
    Path("graphics_qa_report.md").write_text("\n".join(report), encoding="utf-8")
    Path("graphics_qa_manifest.json").write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "counts": {
            "bundles_scored": len(rows),
            "upload_status_rows": len(upload_status_rows),
            "freshness_rows": len(freshness_rows),
            "player_fit_rows": len(player_fit_rows),
            "fail": sum(1 for r in rows if r.get("decision") == "fail"),
            "pass_with_review": sum(1 for r in rows if r.get("decision") == "pass_with_review"),
            "pass": sum(1 for r in rows if r.get("decision") == "pass"),
        },
    }, indent=2), encoding="utf-8")
    Path("graphics_qa_dashboard/index.html").write_text(
        f"<html><body><h1>Graphics QA v1.9</h1><p>Bundles scored: {len(rows)}</p></body></html>",
        encoding="utf-8",
    )
    print("Created HSD Graphics QA v1.9 BeBe outputs")


if __name__ == "__main__":
    main()
