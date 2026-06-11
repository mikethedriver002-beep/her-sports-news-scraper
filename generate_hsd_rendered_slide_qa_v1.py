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

VERSION = "hsd-rendered-slide-qa-v2.4-bebe-dynamic-preview"

INPUT_DIRS = [
    Path(os.environ.get("HSD_RENDERED_GRAPHICS_DIR", "rendered_graphics_input")),
    Path("graphics_rendered_input"),
    Path("rendered_slides"),
]
INPUT_BANNED = "graphics_banned_language.csv"
POLICY_PATH = Path("config/graphics_rendered_qa_policy_v2.json")
PREVIEW_BUILD = Path("studio_preview_build_v2.json")
OUT_CSV = "rendered_slide_qa.csv"
OUT_MD = "rendered_slide_qa_report.md"
OUT_JSON = "rendered_slide_qa_manifest.json"
OUT_TEMPLATE = "rendered_graphics_manual_review_template.csv"

FIELDS = [
    "file_path", "slide_number", "width", "height", "dimension_status", "ocr_status",
    "banned_language_hits", "preview_score_language_status", "expected_matchup_status", "qa_decision", "issues",
]
TEMPLATE_FIELDS = [
    "slide_number", "file_path", "dimensions_ok", "correct_date", "correct_teams", "complete_slate",
    "no_extra_games", "no_banned_terms", "player_images_correct", "logos_or_badges_correct", "legibility", "visual_grade", "post_ready", "required_edits",
]

BUILTIN_BANNED = [
    "Verified Final", "Winner", "Loser", "BUNDLE LOCKED FACTS", "source-safe context", "graphics-safe context",
    "Do not alter", "Accuracy lock",
]
SCORE_PATTERNS = [
    re.compile(r"(?<!\d{4}-)\b\d{2,3}\s*[-–—]\s*\d{2,3}\b(?!-\d{2})"),
    re.compile(r"\bfinal\b", flags=re.I),
    re.compile(r"\bwon\b|\blost\b|\bbeats?\b|\bdefeats?\b", flags=re.I),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: str) -> List[Dict[str, str]]:
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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def image_files() -> List[Path]:
    files: List[Path] = []
    for d in INPUT_DIRS:
        if d.exists():
            files.extend([p for p in d.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}])
    return sorted(set(files))


def infer_slide_number(path: Path) -> int:
    s = path.stem.lower()
    m = re.search(r"(?:slide|slid|s)[_\-\s]*(\d+)", s)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d)\b", s)
    if m:
        return int(m.group(1))
    return 0


def ocr(path: Path) -> Tuple[str, str]:
    if pytesseract and Image:
        try:
            return pytesseract.image_to_string(Image.open(path)) or "", "pytesseract"
        except Exception:
            pass
    try:
        res = subprocess.run(["tesseract", str(path), "stdout"], capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            return res.stdout or "", "tesseract_cli"
    except Exception:
        pass
    return "", "unavailable"


def banned_terms() -> List[str]:
    terms = BUILTIN_BANNED[:]
    for r in read_csv(INPUT_BANNED):
        term = clean(r.get("term"))
        if term:
            terms.append(term)
    policy = read_json(POLICY_PATH)
    for term in policy.get("banned_rendered_terms", []):
        if clean(term):
            terms.append(clean(term))
    out: List[str] = []
    for term in terms:
        if term not in out:
            out.append(term)
    return out


def expected_terms_from_preview() -> Dict[str, Any]:
    build = read_json(PREVIEW_BUILD)
    games = build.get("games", []) if isinstance(build.get("games"), list) else []
    terms: List[str] = []
    matchups: List[str] = []
    for g in games:
        matchup = clean(g.get("matchup")) if isinstance(g, dict) else clean(g)
        if not matchup:
            continue
        matchups.append(matchup)
        pieces = re.split(r"\s+(?:at|vs\.?|@)\s+", matchup, flags=re.I)
        for piece in pieces:
            piece = clean(piece)
            if piece and piece not in terms:
                terms.append(piece)
    target_date = clean(build.get("target_date_local"))
    return {"target_date": target_date, "terms": terms, "matchups": matchups, "is_preview": bool(games)}


def score_language_hit(text: str) -> str:
    scrubbed = re.sub(r"\bno\s+final\s+scores?\b", "", text, flags=re.I)
    scrubbed = re.sub(r"\bno\s+scores?\b", "", scrubbed, flags=re.I)
    scrubbed = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", "", scrubbed)
    for pat in SCORE_PATTERNS:
        m = pat.search(scrubbed)
        if m:
            return m.group(0)
    return ""


def create_manual_template(files: List[Path], expected_slide_count: int) -> None:
    rows: List[Dict[str, str]] = []
    for idx in range(1, max(expected_slide_count, len(files), 4) + 1):
        file_path = files[idx - 1].as_posix() if idx <= len(files) else ""
        rows.append({
            "slide_number": str(idx),
            "file_path": file_path,
            "dimensions_ok": "",
            "correct_date": "",
            "correct_teams": "",
            "complete_slate": "",
            "no_extra_games": "",
            "no_banned_terms": "",
            "player_images_correct": "",
            "logos_or_badges_correct": "",
            "legibility": "",
            "visual_grade": "",
            "post_ready": "",
            "required_edits": "",
        })
    write_csv(OUT_TEMPLATE, rows, TEMPLATE_FIELDS)


def main() -> None:
    banned = banned_terms()
    expected = expected_terms_from_preview()
    files = image_files()
    rows: List[Dict[str, Any]] = []

    for p in files:
        issues: List[str] = []
        slide_num = infer_slide_number(p)
        width = height = ""
        dimension_status = "not_checked"
        if Image:
            try:
                im = Image.open(p)
                width, height = im.size
                dimension_status = "pass" if (width, height) == (1080, 1350) else "fail"
                if dimension_status == "fail":
                    issues.append(f"dimension mismatch {width}x{height}; expected 1080x1350")
            except Exception as e:
                dimension_status = f"error:{type(e).__name__}"
                issues.append(f"image open error {type(e).__name__}")

        text, method = ocr(p)
        low = clean(text).lower()
        hits = [term for term in banned if term.lower() in low]
        if hits:
            issues.append("banned language: " + ", ".join(hits))

        score_status = "pass"
        if expected.get("is_preview"):
            hit = score_language_hit(low)
            if hit:
                score_status = "fail"
                issues.append(f"preview slide appears to include result/score language: {hit}")
        elif not low and method == "unavailable":
            score_status = "not_checked_ocr_unavailable"

        expected_status = "not_checked_ocr_unavailable" if method == "unavailable" else "pass"
        if expected.get("is_preview") and method != "unavailable":
            terms = expected.get("terms", [])
            present = [t for t in terms if t.lower() in low]
            if terms and slide_num in {1, 3} and len(present) < max(1, len(terms) // 2):
                expected_status = "review"
                issues.append("slate/team terms not strongly detected on slate slide")

        decision = "fail" if hits or dimension_status == "fail" or score_status == "fail" else "review" if issues or method == "unavailable" else "pass"
        rows.append({
            "file_path": p.as_posix(),
            "slide_number": slide_num,
            "width": width,
            "height": height,
            "dimension_status": dimension_status,
            "ocr_status": method,
            "banned_language_hits": "; ".join(hits),
            "preview_score_language_status": score_status,
            "expected_matchup_status": expected_status,
            "qa_decision": decision,
            "issues": "; ".join(issues),
        })

    expected_slide_count = 4 if expected.get("is_preview") else max(4, len(files))
    create_manual_template(files, expected_slide_count)

    slide_count_status = "not_checked_no_files"
    global_issues: List[str] = []
    if files:
        slide_count_status = "pass" if len(files) == expected_slide_count else "fail"
        if slide_count_status == "fail":
            global_issues.append(f"expected {expected_slide_count} slide files; found {len(files)}")
    if expected.get("is_preview") and not expected.get("matchups"):
        global_issues.append("preview build found, but no expected matchups parsed")

    fail_count = sum(1 for r in rows if r["qa_decision"] == "fail")
    review_count = sum(1 for r in rows if r["qa_decision"] == "review")
    pass_count = sum(1 for r in rows if r["qa_decision"] == "pass")
    final_decision = "blocked" if fail_count or slide_count_status == "fail" else "needs_manual_review" if review_count or not rows else "post_ready"

    write_csv(OUT_CSV, rows, FIELDS)
    report = [
        "# HSD Rendered Slide QA",
        "",
        f"Generated: {now()}",
        f"Version: {VERSION}",
        "",
        f"- rendered image files found: {len(rows)}",
        f"- expected slide count: {expected_slide_count}",
        f"- slide count status: {slide_count_status}",
        f"- pass: {pass_count}",
        f"- review: {review_count}",
        f"- fail: {fail_count}",
        f"- final decision: **{final_decision}**",
        "",
    ]
    if expected.get("is_preview"):
        report += [
            "## Preview expectation",
            "",
            f"- target date: {expected.get('target_date') or 'missing'}",
            f"- matchups: {' | '.join(expected.get('matchups', [])) or 'none parsed'}",
            "- preview rule: no final scores or result language",
            "",
        ]
    if not rows:
        report += [
            "No rendered slide files were found.",
            "",
            "To use this gate, upload finished graphics into `rendered_graphics_input/` in the repo and rerun Asset Visual QA.",
            "A manual checklist template was still created at `rendered_graphics_manual_review_template.csv`.",
            "",
        ]
    if global_issues:
        report += ["## Global issues", "", *[f"- {x}" for x in global_issues], ""]
    for r in rows:
        report += [
            f"## {Path(r['file_path']).name}",
            "",
            f"- Decision: **{r['qa_decision']}**",
            f"- Slide number: {r['slide_number'] or 'unknown'}",
            f"- Dimensions: {r['width']}x{r['height']} ({r['dimension_status']})",
            f"- OCR: {r['ocr_status']}",
            f"- Preview score language: {r['preview_score_language_status']}",
            f"- Expected matchup/team status: {r['expected_matchup_status']}",
            f"- Banned terms: {r['banned_language_hits'] or 'none detected'}",
            f"- Issues: {r['issues'] or 'none'}",
            "",
        ]
    Path(OUT_MD).write_text("\n".join(report), encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "counts": {
            "files_checked": len(rows),
            "expected_slide_count": expected_slide_count,
            "pass": pass_count,
            "review": review_count,
            "fail": fail_count,
            "slide_count_status": slide_count_status,
            "decision": final_decision,
        },
        "expected": expected,
        "global_issues": global_issues,
        "outputs": [OUT_CSV, OUT_MD, OUT_JSON, OUT_TEMPLATE],
    }, indent=2), encoding="utf-8")
    print("Created HSD Rendered Slide QA outputs")
    print(json.dumps(json.loads(Path(OUT_JSON).read_text()).get("counts", {}), indent=2))


if __name__ == "__main__":
    main()
