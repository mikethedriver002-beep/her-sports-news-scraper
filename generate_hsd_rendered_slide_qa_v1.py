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

VERSION = "hsd-rendered-slide-qa-v1.8"

INPUT_DIRS = [
    Path(os.environ.get("HSD_RENDERED_GRAPHICS_DIR", "rendered_graphics_input")),
    Path("graphics_rendered_input"),
    Path("rendered_slides"),
]
INPUT_BANNED = "graphics_banned_language.csv"
OUT_CSV = "rendered_slide_qa.csv"
OUT_MD = "rendered_slide_qa_report.md"
OUT_JSON = "rendered_slide_qa_manifest.json"

FIELDS = [
    "file_path", "slide_number", "width", "height", "dimension_status", "ocr_status",
    "banned_language_hits", "expected_copy_status", "score_status", "qa_decision", "issues"
]

EXPECTED_BY_SLIDE = {
    1: ["Dallas", "Los Angeles", "104", "96"],
    2: ["Final", "Dallas", "Los Angeles", "104", "96"],
    3: ["Jessica", "Arike", "Paige", "Kelsey", "Ariel", "Dearica"],
    4: ["Follow", "104", "96"],
}


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
        res = subprocess.run(["tesseract", str(path), "stdout"], capture_output=True, text=True, timeout=45)
        if res.returncode == 0:
            return res.stdout or "", "tesseract_cli"
    except Exception:
        pass
    return "", "unavailable"


def main() -> None:
    banned = [clean(r.get("term")) for r in read_csv(INPUT_BANNED) if clean(r.get("term"))]
    rows: List[Dict[str, Any]] = []
    for p in image_files():
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
                    issues.append(f"dimension mismatch {width}x{height}")
            except Exception as e:
                dimension_status = f"error:{type(e).__name__}"

        text, method = ocr(p)
        low = clean(text).lower()
        hits = [term for term in banned if term.lower() in low]
        if hits:
            issues.append("banned language: " + ", ".join(hits))
        expected = EXPECTED_BY_SLIDE.get(slide_num, [])
        missing = [term for term in expected if term.lower() not in low] if low else []
        expected_status = "pass"
        if method == "unavailable":
            expected_status = "not_checked_ocr_unavailable"
            issues.append("OCR unavailable")
        elif expected and len(missing) >= max(1, len(expected) // 2):
            expected_status = "review"
            issues.append("likely missing expected copy: " + ", ".join(missing[:6]))

        score_status = "pass"
        if low:
            has_104 = "104" in low
            has_96 = "96" in low
            if slide_num in {1, 2, 4} and not (has_104 and has_96):
                score_status = "review"
                issues.append("expected 104 and 96 not both detected")

        decision = "fail" if hits or dimension_status == "fail" else "review" if issues else "pass"
        rows.append({
            "file_path": p.as_posix(),
            "slide_number": slide_num,
            "width": width,
            "height": height,
            "dimension_status": dimension_status,
            "ocr_status": method,
            "banned_language_hits": "; ".join(hits),
            "expected_copy_status": expected_status,
            "score_status": score_status,
            "qa_decision": decision,
            "issues": "; ".join(issues),
        })

    write_csv(OUT_CSV, rows, FIELDS)
    report = [
        "# HSD Rendered Slide QA v1.8",
        "",
        f"Generated: {now()}",
        "",
        f"- rendered image files found: {len(rows)}",
        f"- pass: {sum(1 for r in rows if r['qa_decision'] == 'pass')}",
        f"- review: {sum(1 for r in rows if r['qa_decision'] == 'review')}",
        f"- fail: {sum(1 for r in rows if r['qa_decision'] == 'fail')}",
        "",
    ]
    if not rows:
        report += [
            "No rendered slide files were found.",
            "",
            "To use this gate, upload finished images into `rendered_graphics_input/` in the repo and rerun Asset Visual QA.",
            "",
        ]
    for r in rows:
        report += [
            f"## {Path(r['file_path']).name}",
            "",
            f"- Decision: **{r['qa_decision']}**",
            f"- Dimensions: {r['width']}x{r['height']} ({r['dimension_status']})",
            f"- OCR: {r['ocr_status']}",
            f"- Issues: {r['issues'] or 'none'}",
            "",
        ]
    Path(OUT_MD).write_text("\n".join(report), encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "counts": {
            "files_checked": len(rows),
            "pass": sum(1 for r in rows if r["qa_decision"] == "pass"),
            "review": sum(1 for r in rows if r["qa_decision"] == "review"),
            "fail": sum(1 for r in rows if r["qa_decision"] == "fail"),
        },
        "outputs": [OUT_CSV, OUT_MD, OUT_JSON],
    }, indent=2), encoding="utf-8")
    print("Created HSD Rendered Slide QA outputs")
    print(json.dumps(json.loads(Path(OUT_JSON).read_text()).get("counts", {}), indent=2))


if __name__ == "__main__":
    main()
