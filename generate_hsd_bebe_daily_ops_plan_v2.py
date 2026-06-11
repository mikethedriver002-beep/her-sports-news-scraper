from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

VERSION = "hsd-bebe-daily-ops-plan-v2"
LOCAL_TZ = os.environ.get("HSD_LOCAL_TIMEZONE", "America/New_York")
DAY_TYPE = os.environ.get("HSD_DESK_DAY_TYPE", "normal_day").strip() or "normal_day"
CADENCE_PATH = Path(os.environ.get("HSD_DAILY_CADENCE_CONFIG", "config/hsd_daily_cadence_v2.json"))
PRIORITY_PATH = Path(os.environ.get("HSD_PRIORITY_SPORTS_CONFIG", "config/hsd_priority_sports_14d_v2.json"))

OUT_MD = Path("bebe_daily_ops_plan.md")
OUT_CSV = Path("bebe_daily_ops_plan.csv")
OUT_JSON = Path("bebe_daily_ops_status.json")
OUT_PRIORITY_MD = Path("bebe_priority_board.md")
OUT_SCHEDULE_MD = Path("bebe_posting_schedule_today.md")

FIELDS = [
    "time_et", "platform", "post_type", "purpose", "recommended_action", "status", "source_artifact", "notes",
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def local_zone():
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(LOCAL_TZ)
    except Exception:
        return timezone.utc


def now_local() -> datetime:
    return datetime.now(local_zone())


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def first_value(row: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        if clean(row.get(k)):
            return clean(row.get(k))
    return ""


def best_slate_title() -> str:
    rows = read_csv("daily_slate_plan.csv")
    ready = []
    for r in rows:
        title = first_value(r, ["title", "story_title", "headline", "post_title", "source_headline"])
        status = first_value(r, ["status", "slot_status", "publish_status", "recommendation"])
        kind = first_value(r, ["story_kind", "content_family", "post_type", "type"])
        if title:
            ready.append((status.lower(), kind, title))
    if ready:
        return ready[0][2]
    manual = [r for r in read_csv("story_candidates_manual.csv") if r.get("publish_eligible") == "Yes"]
    if manual:
        return clean(manual[0].get("title") or manual[0].get("source_url"))
    discovery = [r for r in read_csv("story_candidates_discovery.csv") if r.get("publish_eligible") == "Yes"]
    if discovery:
        return clean(discovery[0].get("title") or discovery[0].get("source_url"))
    return "Choose best verified story from research scan"


def preview_gate_status() -> Dict[str, str]:
    summary = read_csv("preview_bundle_quality_summary.csv")
    if summary:
        return summary[0]
    rows = read_csv("preview_bundle_quality.csv")
    if not rows:
        return {"gate_status": "NOT_RUN", "block_reason": "preview gate has not run"}
    fail = [r for r in rows if r.get("severity") == "FAIL" and r.get("status") == "FAIL"]
    warn = [r for r in rows if r.get("status") == "WARN"]
    return {
        "gate_status": "BLOCKED" if fail else "REVIEW" if warn else "PASS",
        "block_reason": "; ".join(r.get("details", "") for r in fail),
    }


def graphics_pack_status() -> str:
    rows = read_csv("graphics_upload_pack_status.csv")
    if not rows:
        return "not_created"
    statuses = [clean(r.get("upload_pack_status")) for r in rows]
    if any(s == "ready" for s in statuses):
        return "ready"
    if any(s == "ready_with_review" for s in statuses):
        return "ready_with_review"
    if any(s.startswith("blocked") for s in statuses):
        return "blocked"
    return statuses[0] or "unknown"


def action_for_slot(item: Dict[str, str], noon_story: str, preview: Dict[str, str], pack_status: str) -> Dict[str, str]:
    time_et = item.get("time_et", "")
    platform = item.get("platform", "")
    post_type = item.get("post_type", "")
    purpose = item.get("purpose", "")
    notes = ""
    status = "operator_action"
    action = purpose
    artifact = ""

    if time_et == "09:00":
        status = "draft_needed"
        action = "Post morning board using top WNBA + tennis/soccer/golf watch items."
        artifact = "bebe_priority_board.md"
    elif time_et == "12:00":
        status = "ready_with_review" if noon_story != "Choose best verified story from research scan" else "needs_research"
        action = f"Main IG post 1: {noon_story}"
        artifact = "daily_slate_plan.md"
    elif time_et == "12:10":
        status = "operator_action"
        action = "Add first comment with a debate hook tied to the noon post."
        artifact = "bebe_daily_ops_plan.md"
    elif time_et == "16:45":
        gate = clean(preview.get("gate_status")) or "NOT_RUN"
        if gate == "PASS" and pack_status in {"ready", "ready_with_review"}:
            status = pack_status
            action = "Use Tonight in the W upload pack for Main Post 2."
            artifact = "graphics_chat_direct_handoff.md"
        elif gate == "PASS":
            status = "needs_assets"
            action = "Tonight in the W passed slate QA, but graphics pack is not ready yet."
            artifact = "preview_bundle_quality.md"
        elif gate == "REVIEW":
            status = "review"
            action = "Preview gate has warnings. Review before using Tonight in the W."
            artifact = "preview_bundle_quality.md"
        else:
            status = "blocked_or_not_run"
            action = "Do not use Tonight in the W yet. Use Stories or a verified non-WNBA fallback if needed."
            artifact = "preview_bundle_quality.md"
            notes = clean(preview.get("block_reason"))[:240]
    elif "19:00" in time_et:
        status = "manual_live_desk"
        action = "Threads live desk: pregame question, halftime/mid-event take, final reaction, debate reply, verified follow-up."
    elif time_et == "23:30":
        status = "manual_after_results"
        action = "Nightcap only if there is a clear story of the night. No filler."
    elif time_et == "10:30":
        status = "operator_action"
        action = "Post 2 to 4 IG Story frames: poll, question, schedule, or quick take."
    elif time_et == "14:30":
        status = "draft_needed"
        action = "One sharp Threads opinion/question. Use WNBA, tennis, soccer, or business angle."
    elif time_et.startswith("Next day"):
        status = "candidate_only"
        action = "Create next-morning recap only if a strong verified result/story emerges."
    elif time_et == "08:15":
        status = "operator_action"
        action = "Research scan: find 5 to 10 candidates; add manual links to story inbox if needed."

    return {
        "time_et": time_et,
        "platform": platform,
        "post_type": post_type,
        "purpose": purpose,
        "recommended_action": action,
        "status": status,
        "source_artifact": artifact,
        "notes": notes,
    }


def priority_lines(priority: Dict[str, Any]) -> List[str]:
    lines = [
        "# BeBe Priority Board",
        "",
        f"Version: {priority.get('version', '')}",
        f"Effective: {priority.get('effective_start_et', '')} to {priority.get('effective_end_et', '')} ET",
        "",
        "## Priority order",
        "",
    ]
    for item in priority.get("priority_order", []):
        lines.append(f"- {item}")
    lines += ["", "## League rules", ""]
    for lg in priority.get("leagues", []):
        lines += [
            f"### {lg.get('rank')}. {lg.get('name')}",
            "",
            f"- Priority: {lg.get('priority')}",
            f"- Frequency: {lg.get('posting_frequency')}",
            f"- Rule: {lg.get('daily_rule')}",
            f"- Best formats: {', '.join(lg.get('best_formats', []))}",
            f"- Angle bank: {', '.join(lg.get('angle_bank', []))}",
            "",
        ]
    lines += ["## Formula", "", *[f"- {x}" for x in priority.get("formula", [])], ""]
    return lines


def main() -> None:
    cadence = read_json(CADENCE_PATH)
    priority = read_json(PRIORITY_PATH)
    today = now_local()
    weekday = today.strftime("%A")
    volume = cadence.get("daily_volume", {}).get(DAY_TYPE) or cadence.get("daily_volume", {}).get("normal_day", {})
    rhythm = cadence.get("weekly_rhythm", {}).get(weekday, {})
    preview = preview_gate_status()
    pack_status = graphics_pack_status()
    noon_story = best_slate_title()

    schedule_rows = [action_for_slot(item, noon_story, preview, pack_status) for item in cadence.get("daily_baseline", [])]
    write_csv(OUT_CSV, schedule_rows)

    status = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_at_local": today.isoformat(),
        "weekday": weekday,
        "day_type": DAY_TYPE,
        "volume_targets": volume,
        "weekly_rhythm": rhythm,
        "preview_gate_status": preview,
        "graphics_pack_status": pack_status,
        "noon_story_recommendation": noon_story,
        "outputs": [OUT_MD.as_posix(), OUT_CSV.as_posix(), OUT_PRIORITY_MD.as_posix(), OUT_SCHEDULE_MD.as_posix()],
    }
    OUT_JSON.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# BeBe Daily Ops Plan",
        "",
        f"Generated local: {today.strftime('%Y-%m-%d %I:%M %p %Z')}",
        f"Day: {weekday}",
        f"Day type: {DAY_TYPE}",
        "Platforms: Instagram + Threads",
        "Publish automation: OFF / artifact-only",
        "",
        "## Today’s volume target",
        "",
    ]
    for k, v in volume.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Weekly rhythm", ""]
    if rhythm:
        for k, v in rhythm.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- No rhythm configured for today.")
    lines += [
        "",
        "## Hard rules",
        "",
        f"- {cadence.get('fixed_templates', {}).get('daily_rule', 'IG quality over volume. Threads can carry volume.')}",
        "- WNBA gets at least one daily touch.",
        "- No auto-posting. Use artifacts for review and post manually to Instagram/Threads.",
        "- No Tonight in the W graphic unless preview gate and graphics upload pack are acceptable.",
        "",
        "## Posting schedule",
        "",
        "| Time ET | Platform | Slot | Status | Recommended action | Artifact |",
        "|---|---|---|---|---|---|",
    ]
    for r in schedule_rows:
        lines.append(f"| {r['time_et']} | {r['platform']} | {r['post_type']} | {r['status']} | {r['recommended_action']} | {r['source_artifact']} |")
    lines += [
        "",
        "## Morning Threads template",
        "",
        "```text",
        cadence.get("fixed_templates", {}).get("morning_threads", "Today in women’s sports 👀"),
        "```",
        "",
        "## Current gate notes",
        "",
        f"- Preview gate: {preview.get('gate_status', 'NOT_RUN')}",
        f"- Preview block/review reason: {preview.get('block_reason', '') or 'none'}",
        f"- Graphics upload pack: {pack_status}",
        f"- Noon recommendation: {noon_story}",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_SCHEDULE_MD.write_text("\n".join(lines[lines.index("## Posting schedule"):]) if "## Posting schedule" in lines else "", encoding="utf-8")
    OUT_PRIORITY_MD.write_text("\n".join(priority_lines(priority)), encoding="utf-8")
    print(json.dumps({"rows": len(schedule_rows), "preview_gate": preview.get("gate_status", "NOT_RUN"), "pack_status": pack_status}, indent=2))


if __name__ == "__main__":
    main()
