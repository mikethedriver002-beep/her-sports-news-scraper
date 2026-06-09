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

VERSION = "hsd-graphics-qa-scorer-v1.8.1-event-date-bridge"
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


def expected_terms_for_main_slide(slide_num: int) -> List[str]:
    if slide_num == 1:
        return ["Dallas", "Sparks", "104", "96"]
    if slide_num == 2:
        return ["Final", "Dallas", "Sparks", "104", "96"]
    if slide_num == 3:
        return ["Jessica", "Arike", "Paige", "Kelsey", "Ariel", "Dearica"]
    if slide_num == 4:
        return ["Follow", "Her Sports Daily", "104", "96"]
    return []


def infer_slide_number(render_path: str) -> int:
    name = Path(render_path).stem.lower()
    m = re.search(r"(?:slide|slid|s)(\d+)", name)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 0
    return 0


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
    bundles = manifest.get("bundles", [])
    rows: List[Dict[str, Any]] = []
    run = "qa_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for b in bundles:
        issues: List[Dict[str, str]] = []
        score = 100
        post_slug = clean(b.get("post_slug"))
        template_name = clean(b.get("template_name"))

        if not clean(b.get("source_facts", {}).get("accuracy_lock")) and not clean(b.get("source_facts", {}).get("source_headlines")):
            issues.append({"code": "MISSING_FACT_LOCK", "severity": "major", "message": "No source facts or accuracy lock."})
            score -= 20
        for aid in b.get("asset_ids", []):
            if aid and aid not in approved:
                issues.append({"code": "UNAPPROVED_ASSET", "severity": "critical", "message": aid})
                score -= 40
        if b.get("fact_warning_count", 0):
            issues.append({"code": "FACT_WARNING_PRESENT", "severity": "critical", "message": f"{b.get('fact_warning_count')} fact warnings present"})
            score -= 35
        if not any("watermark" in clean(x.get("layer_id")).lower() for x in b.get("all_layers", [])):
            issues.append({"code": "MISSING_WATERMARK", "severity": "critical", "message": "No watermark layer."})
            score -= 40
        if post_slug == "main-wnba-result" and missing_required_players:
            issues.append({"code": "MISSING_REQUIRED_PLAYER_IMAGES", "severity": "critical", "message": ", ".join([r.get("player_name", "") for r in missing_required_players])})
            score -= 45

        upload_row = upload_status_rows.get(post_slug)
        if upload_row and upload_row.get("upload_pack_status") not in {"ready", "ready_with_review"}:
            status = upload_row.get("upload_pack_status", "")
            if status == "blocked_freshness_gate":
                code = "UPLOAD_PACK_BLOCKED_BY_FRESHNESS"
            elif status == "blocked_player_image_fit":
                code = "UPLOAD_PACK_BLOCKED_BY_PLAYER_IMAGE_FIT"
            elif status == "blocked_missing_required_assets":
                code = "UPLOAD_PACK_INCOMPLETE"
            else:
                code = "UPLOAD_PACK_BLOCKED"
            msg = upload_row.get("missing_asset_names") or status or "upload pack blocked"
            issues.append({"code": code, "severity": "critical", "message": msg})
            score -= 45
        if not upload_row:
            issues.append({"code": "UPLOAD_PACK_STATUS_MISSING", "severity": "major", "message": "graphics_upload_pack_status.csv has no row for this bundle"})
            score -= 10

        freshness = freshness_rows.get(post_slug)
        if freshness:
            if freshness.get("freshness_decision") == "block":
                issues.append({"code": "FRESHNESS_GATE_BLOCKED", "severity": "critical", "message": freshness.get("reason", "stale or missing event date")})
                score -= 45
            elif freshness.get("freshness_decision") == "review":
                issues.append({"code": "FRESHNESS_GATE_REVIEW", "severity": "major", "message": freshness.get("reason", "freshness review required")})
                score -= 12
        elif post_slug == "main-wnba-result":
            issues.append({"code": "FRESHNESS_GATE_MISSING", "severity": "major", "message": "studio_freshness_gate.csv missing row for main bundle"})
            score -= 10

        fit_for_bundle = [r for r in player_fit_rows if r.get("bundle_slug") == post_slug]
        blocked_fit = [r for r in fit_for_bundle if r.get("fit_status", "").startswith("blocked")]
        review_fit = [r for r in fit_for_bundle if r.get("fit_status") == "review"]
        if blocked_fit:
            issues.append({"code": "PLAYER_IMAGE_FIT_BLOCKED", "severity": "critical", "message": ", ".join(r.get("player_name", "") for r in blocked_fit)})
            score -= 35
        elif review_fit:
            issues.append({"code": "PLAYER_IMAGE_FIT_REVIEW", "severity": "review", "message": "Use tight crop rules for: " + ", ".join(r.get("player_name", "") for r in review_fit)})
            score -= 3

        for language_file in [
            "graphics_copy_style_guide.md",
            "graphics_display_copy.csv",
            "graphics_banned_language.csv",
            "graphics_asset_usage_map.csv",
            "graphics_layout_blueprint.csv",
        ]:
            if post_slug == "main-wnba-result" and not Path(language_file).exists():
                issues.append({"code": "LANGUAGE_PACK_MISSING", "severity": "major", "message": language_file})
                score -= 8

        prompt_pack_path = Path("graphics_chat_upload_pack") / post_slug / "00_PROMPT_TO_PASTE.md"
        render_path = clean(b.get("render_path"))

        if prompt_pack_path.exists():
            prompt_text = prompt_pack_path.read_text(encoding="utf-8", errors="replace")
            prompt_hits = [term for term in banned_terms if clean(term).lower() in clean(prompt_text).lower()]
            if prompt_hits:
                issues.append({"code": "PROMPT_NOT_SANITIZED", "severity": "critical", "message": ", ".join(prompt_hits)})
                score -= 35
        else:
            issues.append({"code": "UPLOAD_PROMPT_MISSING", "severity": "major", "message": str(prompt_pack_path)})
            score -= 10
        if render_path and Path(render_path).exists():
            if Image:
                try:
                    width, height = Image.open(render_path).size
                    if (width, height) != (1080, 1350):
                        issues.append({"code": "DIMENSION_MISMATCH", "severity": "major", "message": f"Expected 1080x1350, got {width}x{height}"})
                        score -= 10
                except Exception:
                    pass

            ocr, ocr_method = ocr_text(render_path)
            ocr_clean = clean(ocr).lower()
            if ocr_method == "unavailable":
                issues.append({"code": "OCR_UNAVAILABLE", "severity": "review", "message": "No OCR engine available. Render QA partially skipped."})
                score -= 2
            if ocr_clean:
                hits = [term for term in banned_terms if clean(term).lower() in ocr_clean]
                if hits:
                    issues.append({"code": "BANNED_LANGUAGE_RENDERED", "severity": "critical", "message": ", ".join(hits)})
                    score -= 35

                slide_num = infer_slide_number(render_path)
                expected_terms = expected_terms_for_main_slide(slide_num) if post_slug == "main-wnba-result" else []
                missing_terms = [t for t in expected_terms if t.lower() not in ocr_clean]
                if expected_terms and len(missing_terms) >= max(1, len(expected_terms) // 2):
                    issues.append({"code": "EXPECTED_COPY_MISSING", "severity": "major", "message": f"Likely missing expected terms: {', '.join(missing_terms[:6])}"})
                    score -= 15

                if post_slug == "main-wnba-result" and slide_num == 3:
                    if not any(x in ocr_clean for x in ["kelsey", "ariel", "dearica", "nneka", "cameron"]):
                        issues.append({"code": "SPARKS_PERFORMERS_MISSING", "severity": "critical", "message": "Top performers slide appears to miss Sparks-side performers."})
                        score -= 30
                if post_slug == "main-wnba-result" and slide_num == 2:
                    if any(x in ocr_clean for x in ["winner", "loser", "verified final"]):
                        issues.append({"code": "ROBOTIC_SCOREBOARD_LANGUAGE", "severity": "critical", "message": "Scoreboard render contains banned robotic result language."})
                        score -= 25
            else:
                issues.append({"code": "OCR_NO_TEXT", "severity": "review", "message": "Rendered image found but OCR extracted no text."})
                score -= 3
        else:
            issues.append({"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."})
            score -= 5

        score = max(0, score)
        decision = "fail" if any(i["severity"] == "critical" for i in issues) or score < 70 else "revise" if score < 88 else "pass_with_review" if issues else "pass"
        remediation = []
        codes = {i["code"] for i in issues}
        if "BANNED_LANGUAGE_RENDERED" in codes or "ROBOTIC_SCOREBOARD_LANGUAGE" in codes or "PROMPT_NOT_SANITIZED" in codes:
            remediation.append("Strip banned terms with the prompt sanitizer and rerender.")
        if "SPARKS_PERFORMERS_MISSING" in codes:
            remediation.append("Rebuild slide 3 as a true two-team performer comparison.")
        if "DIMENSION_MISMATCH" in codes:
            remediation.append("Export 1080x1350 portrait slides.")
        if not remediation:
            remediation.append("Resolve flagged issues and rerun QA.")

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

    report = ["# HSD Graphics QA Scorer v1.8.1 Report", "", f"Generated: {now()}", "", f"Bundles scored: {len(rows)}", ""]
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
        "counts": {"bundles_scored": len(rows), "upload_status_rows": len(upload_status_rows), "freshness_rows": len(freshness_rows), "player_fit_rows": len(player_fit_rows)},
    }, indent=2), encoding="utf-8")
    Path("graphics_qa_dashboard/index.html").write_text(
        f"<html><body><h1>Graphics QA v1.8.1</h1><p>Bundles scored: {len(rows)}</p></body></html>",
        encoding="utf-8",
    )
    print("Created HSD Graphics QA v1.8.1 outputs")


if __name__ == "__main__":
    main()
