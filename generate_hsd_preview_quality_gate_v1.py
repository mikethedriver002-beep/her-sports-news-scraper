from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "hsd-preview-quality-gate-v3.2.4-bebe-ops-v2.3"

REQUIRE_PEOPLE = os.environ.get("HSD_REQUIRE_PREVIEW_PEOPLE", "0").strip().lower() in {"1", "true", "yes"}
TARGET_DATE_ENV = os.environ.get("HSD_TARGET_DATE_LOCAL", "").strip()
FIELDS = ["check_name", "severity", "status", "details"]
SUMMARY_FIELDS = [
    "target_date_local", "gate_status", "block_reason", "source_same_day_count", "included_count",
    "missing_games", "mixed_dates", "source_event_dates", "preview_player_focus_count", "prompt_policy_status",
]

BUILTIN_BANNED_TERMS = [
    "verified final", "winner", "loser", "bundle locked facts", "source-safe context", "graphics-safe context",
    "do not alter", "accuracy lock",
]
SCORE_PATTERNS = [
    re.compile(r"(?<!\d{4}-)\b\d{2,3}\s*[-–—]\s*\d{2,3}\b(?!-\d{2})"),
    re.compile(r"\bfinal\b", flags=re.I),
    re.compile(r"\bwon\b|\blost\b|\bbeats?\b|\bdefeats?\b", flags=re.I),
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, str]], fields: List[str]) -> None:
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


def add(rows: List[Dict[str, str]], name: str, severity: str, ok: bool, details_ok: str, details_fail: str) -> None:
    rows.append({
        "check_name": name,
        "severity": severity,
        "status": "PASS" if ok else "FAIL" if severity == "FAIL" else "WARN",
        "details": details_ok if ok else details_fail,
    })


def json_list(value: str) -> List[str]:
    try:
        parsed = json.loads(value or "[]")
        if isinstance(parsed, list):
            return [clean(x) for x in parsed if clean(x)]
    except Exception:
        pass
    return []


def has_score_or_result_language(text: str) -> Tuple[bool, str]:
    text = clean(text)
    # Allow guardrail phrases such as "No final scores" without treating them as result copy.
    scrubbed = re.sub(r"\bno\s+final\s+scores?\b", "", text, flags=re.I)
    scrubbed = re.sub(r"\bno\s+scores?\b", "", scrubbed, flags=re.I)
    scrubbed = re.sub(r"\bdo\s+not\s+(?:include|use|render)\s+[^.]{0,60}?(?:final|score|result)[^.]*", "", scrubbed, flags=re.I)
    scrubbed = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", "", scrubbed)
    for pat in SCORE_PATTERNS:
        m = pat.search(scrubbed)
        if m:
            return True, m.group(0)
    return False, ""


def prompt_strength(prompt: str) -> Tuple[bool, List[str]]:
    low = prompt.lower()
    required = ["premium", "editorial", "do not include tomorrow", "all must be represented", "no final scores"]
    missing = [x for x in required if x not in low]
    return not missing, missing


def main() -> None:
    rows: List[Dict[str, str]] = []
    bundle_rows = read_csv("studio_bundle_queue.csv")
    tonight = None
    for r in bundle_rows:
        title = clean(r.get("bundle_name") or r.get("content_family")).lower()
        if title.startswith("tonight in the w"):
            tonight = r
            break

    build = read_json("studio_preview_build_v2.json")
    focus = read_csv("preview_player_focus.csv")
    prompt = clean((tonight or {}).get("bundle_prompt"))
    caption = clean((tonight or {}).get("caption_seed"))
    date_list = json_list((tonight or {}).get("source_event_dates_json") if tonight else "[]")

    build_target = clean(build.get("target_date_local"))
    target_date = build_target or clean((tonight or {}).get("event_date")) or TARGET_DATE_ENV
    source_same_day_count = int(build.get("source_same_day_count") or 0) if str(build.get("source_same_day_count") or "").isdigit() else 0
    included_count = int(build.get("included_count") or 0) if str(build.get("included_count") or "").isdigit() else 0
    missing_games = [clean(x) for x in build.get("missing_games", []) if clean(x)] if isinstance(build.get("missing_games"), list) else []
    mixed_dates = bool(build.get("mixed_dates", False))
    completeness_ok = bool(build.get("completeness_ok", True))

    add(rows, "bundle_exists", "FAIL", tonight is not None, "Tonight in the W bundle exists.", "Tonight in the W bundle was not created.")
    add(rows, "preview_build_json_exists", "FAIL", bool(build), "studio_preview_build_v2.json exists.", "studio_preview_build_v2.json is missing or unreadable.")
    add(rows, "target_date_present", "FAIL", bool(target_date), f"Target date locked to {target_date}.", "No target date was found for the preview bundle.")

    if tonight is not None:
        single_date_ok = len(set(date_list)) <= 1 and (not target_date or not date_list or set(date_list) == {target_date})
        add(rows, "same_date_only", "FAIL", single_date_ok, "Only the target local date is present in the bundle.", f"Bundle date mismatch. target={target_date}; source_event_dates={date_list}")
        add(rows, "no_robot_language", "FAIL", not any(term in prompt.lower() for term in BUILTIN_BANNED_TERMS), "Prompt is sanitized for public-facing language.", "Prompt still contains robotic or internal workflow language.")
        slate_ok = completeness_ok and not missing_games and (included_count == source_same_day_count if source_same_day_count else included_count >= 0)
        add(rows, "complete_slate", "FAIL", slate_ok, "All detected target-date games are represented.", f"Preview bundle may be missing games. source={source_same_day_count}; included={included_count}; missing={missing_games}")
        add(rows, "mixed_dates", "FAIL", not mixed_dates, "No mixed-date issue detected.", "Preview bundle mixed games from more than one date.")
        has_result, hit = has_score_or_result_language(prompt + " " + caption)
        add(rows, "preview_has_no_scores_or_results", "FAIL", not has_result, "Preview copy does not contain score/final-result language.", f"Preview copy contains result/score language: {hit}")
        add(rows, "slide_spec", "FAIL", clean(tonight.get("slide_count")) == "4" and "1080x1350" in clean(tonight.get("asset_shape")), "Slide count and dimensions are locked to 4 x 1080x1350.", f"Unexpected slide spec: slide_count={tonight.get('slide_count')}; asset_shape={tonight.get('asset_shape')}")
        add(rows, "player_focus_present", "WARN" if not REQUIRE_PEOPLE else "FAIL", bool(focus), "Preview player focus rows are present.", "No preview player focus rows were created. Team-first design fallback may be used.")
        strong, missing_terms = prompt_strength(prompt)
        add(rows, "premium_prompt", "WARN", strong, "Prompt includes premium visual, slate-lock, and no-score instructions.", "Prompt may still be weak/generic; missing: " + ", ".join(missing_terms))

    write_csv("preview_bundle_quality.csv", rows, FIELDS)
    fail_rows = [r for r in rows if r["severity"] == "FAIL" and r["status"] == "FAIL"]
    warn_rows = [r for r in rows if r["status"] == "WARN"]
    gate_status = "BLOCKED" if fail_rows else "REVIEW" if warn_rows else "PASS"
    block_reason = "; ".join(f"{r['check_name']}: {r['details']}" for r in fail_rows)[:1000]
    prompt_policy_status = "blocked" if any(r["check_name"] in {"no_robot_language", "preview_has_no_scores_or_results"} and r["status"] == "FAIL" for r in rows) else "review" if warn_rows else "pass"

    summary = [{
        "target_date_local": target_date,
        "gate_status": gate_status,
        "block_reason": block_reason,
        "source_same_day_count": str(source_same_day_count),
        "included_count": str(included_count),
        "missing_games": "; ".join(missing_games),
        "mixed_dates": "Yes" if mixed_dates else "No",
        "source_event_dates": "; ".join(date_list),
        "preview_player_focus_count": str(len(focus)),
        "prompt_policy_status": prompt_policy_status,
    }]
    write_csv("preview_bundle_quality_summary.csv", summary, SUMMARY_FIELDS)

    md = [
        "# HSD Preview Quality Gate",
        "",
        f"Version: {VERSION}",
        f"Gate status: **{gate_status}**",
        f"Target local date: {target_date or 'missing'}",
        "",
    ]
    if block_reason:
        md += ["## Block reason", "", block_reason, ""]
    md += ["## Checks", ""]
    for r in rows:
        md.append(f"- **{r['check_name']}** [{r['status']}] - {r['details']}")
    md += [
        "",
        "## Summary CSV",
        "",
        "See `preview_bundle_quality_summary.csv` for the hard gate status used by BeBe Ops.",
    ]
    Path("preview_bundle_quality.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"gate_status": gate_status, "failures": len(fail_rows), "warnings": len(warn_rows)}, indent=2))


if __name__ == "__main__":
    main()
