from __future__ import annotations

import argparse, csv, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "v1.0-post-ready-visual-qa-handoff"
POST_READY = Path("post_ready_assets_v1.csv")
QA_JSON = Path("post_ready_visual_qa_v1.json")
QA_MD = Path("post_ready_visual_qa_v1.md")
APPROVED = Path("visual_qa_approved_assets_v1.csv")
BLOCKED = Path("visual_qa_blocked_assets_v1.csv")
HANDOFF = Path("operator_posting_handoff_v1.md")
VISUAL_APPROVAL = Path(os.environ.get("HSD_VISUAL_QA_APPROVAL_FILE", "config/visual_qa_approved_assets_v1.csv"))

FIELDS = ["headline", "platform", "output_path", "visual_status", "visual_reasons", "operator_action"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, data: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in fields})


def approval_keys() -> set[tuple[str, str, str]]:
    out = set()
    for r in rows(VISUAL_APPROVAL):
        if clean(r.get("approved")).lower() not in {"yes", "true", "1", "approved"}:
            continue
        out.add((clean(r.get("headline")), clean(r.get("platform")), clean(r.get("output_path"))))
    return out


def image_ok(path: Path, platform: str) -> tuple[bool, str]:
    if not path.exists():
        return False, "file_missing"
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception as exc:
        return False, f"image_open_failed:{type(exc).__name__}"
    expected = (1080, 1920) if "stor" in clean(platform).lower() else (1080, 1350)
    if (w, h) != expected:
        return False, f"bad_dimensions:{w}x{h}:expected_{expected[0]}x{expected[1]}"
    return True, "image_file_valid"


def audit() -> dict[str, Any]:
    post = rows(POST_READY)
    approvals = approval_keys()
    approved, blocked = [], []
    mode = clean(os.environ.get("HSD_VISUAL_QA_MODE", "hold_for_human_review")).lower()
    for r in post:
        key = (clean(r.get("headline")), clean(r.get("platform")), clean(r.get("output_path")))
        ok, image_reason = image_ok(Path(clean(r.get("output_path"))), clean(r.get("platform")))
        reasons = [] if ok else [image_reason]
        if mode != "auto_approve" and key not in approvals:
            reasons.append("human_visual_approval_missing")
        status = "approved_for_operator_handoff" if not reasons else "visual_review_blocked"
        out = {"headline": key[0], "platform": key[1], "output_path": key[2], "visual_status": status, "visual_reasons": ";".join(reasons), "operator_action": "final_human_posting_review" if status.startswith("approved") else "do_not_post"}
        (approved if status.startswith("approved") else blocked).append(out)
    return {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "mode": mode, "approval_file": VISUAL_APPROVAL.as_posix(), "post_ready_input_count": len(post), "approved_count": len(approved), "blocked_count": len(blocked), "status": "visual_qa_passed" if approved and not blocked else "visual_qa_blocked", "strict_exit_code": 0 if approved and not blocked else 2, "approved_assets": approved, "blocked_assets": blocked}


def write_md(report: dict[str, Any]) -> None:
    lines = ["# HSD Post-Ready Visual QA", "", f"Version: `{report['version']}`", f"Status: `{report['status']}`", f"Mode: `{report['mode']}`", "", "## Counts", "", f"- Input post-ready assets: `{report['post_ready_input_count']}`", f"- Approved: `{report['approved_count']}`", f"- Blocked: `{report['blocked_count']}`", "", "## Blocked", ""]
    lines += [f"- `{r['platform']}` | {r['headline']} | `{r['visual_reasons']}`" for r in report["blocked_assets"]] or ["- None"]
    lines += ["", "## Approved", ""]
    lines += [f"- `{r['platform']}` | {r['headline']} | `{r['output_path']}`" for r in report["approved_assets"]] or ["- None"]
    QA_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    HANDOFF.write_text("\n".join(["# HSD Operator Posting Handoff", "", "Use only approved assets from `visual_qa_approved_assets_v1.csv`.", "Do not post blocked assets."]) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)
    report = audit()
    QA_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_rows(APPROVED, report["approved_assets"], FIELDS)
    write_rows(BLOCKED, report["blocked_assets"], FIELDS)
    write_md(report)
    print(json.dumps({"version": VERSION, "status": report["status"], "approved": report["approved_count"], "blocked": report["blocked_count"]}, indent=2))
    return 2 if args.strict and report["strict_exit_code"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
