from __future__ import annotations

import argparse, csv, json, re
from pathlib import Path
from typing import Any

VERSION = "v1.1-production-output-alignment"
PROD = Path("production_readiness_v1.json")
VARIANTS = Path("outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv")
POST_CSV = Path("post_ready_assets_v1.csv")
REVIEW_CSV = Path("review_only_assets_v1.csv")
MD = Path("production_readiness_v1.md")
BRIEF = Path("daily_operator_brief_v1.md")


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def as_int(v: Any) -> int:
    try:
        return int(float(str(v))) if clean(v) else 0
    except Exception:
        return 0


def write_rows(path: Path, data: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in fields})


def variant_logo_headlines() -> set[str]:
    out = set()
    for r in rows(VARIANTS):
        if clean(r.get("variant")) == "logos_only" and clean(r.get("status")) == "ready" and as_int(r.get("team_assets")) >= 2 and as_int(r.get("player_assets")) == 0 and "logos_only" in clean(r.get("player_mode")).lower():
            out.add(clean(r.get("headline")))
    return out


def split_reasons(v: Any) -> list[str]:
    return [x for x in clean(v).split(";") if x]


def align(report: dict[str, Any]) -> dict[str, Any]:
    proof = variant_logo_headlines()
    post = list(report.get("post_ready_assets") or [])
    review = []
    promoted = 0
    for r0 in report.get("review_only_assets") or []:
        r = dict(r0)
        reasons = split_reasons(r.get("reasons"))
        if clean(r.get("headline")) in proof and "both_team_logos_not_confirmed" in reasons:
            reasons = [x for x in reasons if x != "both_team_logos_not_confirmed"]
            r["logo_proof_source"] = "variant_manifest_logos_only"
        else:
            r.setdefault("logo_proof_source", "missing" if "both_team_logos_not_confirmed" in reasons else "quality_manifest")
        r["reasons"] = ";".join(reasons)
        if not reasons and clean(r.get("copy_found")) == "Yes":
            r["readiness_status"] = "post_ready_candidate"
            r["manual_visual_review_required"] = "Yes"
            post.append(r)
            promoted += 1
        else:
            r["readiness_status"] = "review_only"
            review.append(r)
    blockers = [b for b in (report.get("blockers") or []) if b != "no_post_ready_candidates_after_quality_gate"]
    if (report.get("quality_graphics") or {}).get("rows") and not post:
        blockers.append("no_post_ready_candidates_after_quality_gate")
    report["version"] = VERSION
    report["post_ready_assets"] = post
    report["review_only_assets"] = review
    report["blockers"] = sorted(set(blockers))
    report["status"] = "blocked" if blockers else "production_review_ready"
    report["publish_gate"] = "blocked_manual_review_required" if blockers else "human_visual_review_required_before_post"
    report["strict_exit_code"] = 2 if blockers else 0
    report["quality_graphics"] = {**(report.get("quality_graphics") or {}), "post_ready_candidates": len(post), "review_only": len(review)}
    report["variant_alignment"] = {"version": VERSION, "logo_proof_headlines": sorted(proof), "promoted_from_review_only": promoted}
    warns = set(report.get("warnings") or [])
    if promoted:
        warns.add("phase4b_promoted_candidates_using_variant_logo_proof")
    if review:
        warns.add("some_quality_graphics_require_review")
    report["warnings"] = sorted(warns)
    return report


def write_text_reports(report: dict[str, Any]) -> None:
    q = report.get("quality_graphics") or {}
    lines = ["# HSD Production Readiness Gate v1", "", f"Version: `{report.get('version')}`", f"Status: `{report.get('status')}`", f"Publish gate: `{report.get('publish_gate')}`", "", "## Counts", "", f"- Post-ready candidates: `{q.get('post_ready_candidates')}`", f"- Review-only assets: `{q.get('review_only')}`", "", "## Blockers", ""]
    lines += [f"- `{b}`" for b in report.get("blockers", [])] or ["- None"]
    lines += ["", "## Post-ready candidates", ""]
    lines += [f"- `{r.get('platform')}` | {r.get('headline')} | `{r.get('output_path')}`" for r in report.get("post_ready_assets", [])] or ["- None"]
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    BRIEF.write_text("\n".join(["# HSD Daily Operator Brief", "", f"Production readiness: `{report.get('status')}`", "", "Use post-ready candidates for final human visual review only."]) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)
    report = json.loads(PROD.read_text(encoding="utf-8")) if PROD.exists() else {"blockers": ["production_readiness_report_missing"], "post_ready_assets": [], "review_only_assets": [], "quality_graphics": {"rows": 0}}
    report = align(report)
    PROD.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_rows(POST_CSV, report.get("post_ready_assets", []), ["headline", "platform", "row_kind", "output_path", "width", "height", "readiness_status", "manual_visual_review_required", "copy_found", "logo_proof_source", "notes"])
    write_rows(REVIEW_CSV, report.get("review_only_assets", []), ["headline", "platform", "row_kind", "output_path", "width", "height", "readiness_status", "reasons", "copy_found", "logo_proof_source", "notes"])
    write_text_reports(report)
    print(json.dumps({"version": VERSION, "status": report.get("status"), "blockers": report.get("blockers"), "post_ready_candidates": report.get("quality_graphics", {}).get("post_ready_candidates")}, indent=2))
    return 2 if args.strict and report.get("blockers") else 0


if __name__ == "__main__":
    raise SystemExit(main())
