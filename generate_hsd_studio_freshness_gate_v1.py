from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

VERSION = "hsd-studio-freshness-gate-v2.5-same-day-preview"

INPUT_RENDER_MANIFEST = "studio_render_manifest_v2.json"
INPUT_BUNDLE_PACKETS = "studio_bundle_packets.md"
INPUT_BUNDLE_PROMPTS = "studio_bundle_prompts_v2.md"
INPUT_QUEUE = "studio_bundle_queue.csv"
INPUT_LAUNCH_BRIEF = "launch_graphics_chat_brief.md"
INPUT_PREVIEW_SUMMARY = "preview_bundle_quality_summary.csv"
INPUT_PREVIEW_BUILD = "studio_preview_build_v2.json"
INPUT_RESULTS_MANIFESTS = [
    "results_sync_manifest.json",
    "latest_results_sync_run_summary.md",
    "results_run_history/latest/run_manifest.json",
    "news_sync_manifest.json",
    "latest_news_sync_run_summary.md",
    "news_run_history/latest/run_manifest.json",
]

OUT_GATE = "studio_freshness_gate.csv"
OUT_STALE = "studio_stale_packet_queue.csv"
OUT_REPORT = "studio_freshness_report.md"
OUT_MANIFEST = "studio_freshness_manifest.json"

FIELDS = [
    "bundle_slug", "bundle_name", "freshness_status", "freshness_decision", "event_date",
    "event_age_hours", "bundle_created_at", "source_run_timestamp", "is_carryover",
    "requires_relabel", "recommended_label", "reason", "source_evidence"
]

MAX_FRESH_HOURS = float(os.environ.get("HSD_MAX_RESULT_FRESH_HOURS", "18"))
STRICT_MISSING_EVENT_DATE = os.environ.get("HSD_STRICT_FRESHNESS_GATE", "1").lower() not in {"0", "false", "no"}
LOCAL_TZ_NAME = os.environ.get("HSD_LOCAL_TIMEZONE", "America/New_York")


def local_tz():
    if ZoneInfo:
        try:
            return ZoneInfo(LOCAL_TZ_NAME)
        except Exception:
            return ZoneInfo("America/New_York")
    return timezone.utc


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_local_date() -> str:
    return now_utc().astimezone(local_tz()).date().isoformat()


def iso(dt: Optional[datetime]) -> str:
    return dt.isoformat() if dt else ""


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


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


def parse_datetime(value: Any) -> Optional[datetime]:
    s = clean(value)
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    patterns = [
        r"\b(20\d{2})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?\b",
        r"\b(\d{1,2})/(\d{1,2})/(20\d{2})(?:[ T](\d{1,2}):(\d{2}))?\b",
    ]
    m = re.search(patterns[0], s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh = int(m.group(4) or 12)
        mm = int(m.group(5) or 0)
        ss = int(m.group(6) or 0)
        return datetime(y, mo, d, hh, mm, ss, tzinfo=timezone.utc)
    m = re.search(patterns[1], s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh = int(m.group(4) or 12)
        mm = int(m.group(5) or 0)
        return datetime(y, mo, d, hh, mm, tzinfo=timezone.utc)
    return None


def find_dates_in_text(text: str) -> List[datetime]:
    dates: List[datetime] = []
    for m in re.finditer(r"\b20\d{2}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?\b", text):
        dt = parse_datetime(m.group(0))
        if dt:
            dates.append(dt)
    for m in re.finditer(r"\b\d{1,2}/\d{1,2}/20\d{2}(?:[ T]\d{1,2}:\d{2})?\b", text):
        dt = parse_datetime(m.group(0))
        if dt:
            dates.append(dt)
    return dates


def prompt_for_bundle(prompts_md: str, bundle_name: str) -> str:
    if not prompts_md:
        return ""
    escaped = re.escape(bundle_name)
    m = re.search(rf"##\s+{escaped}\s*\n(.*?)(?=\n##\s+|\Z)", prompts_md, flags=re.S)
    if m:
        return m.group(1)
    return ""


def bundle_text(bundle: Dict[str, Any], all_text: str, prompts_md: str) -> str:
    name = clean(bundle.get("bundle_name"))
    slug = clean(bundle.get("post_slug") or bundle.get("bundle_slug"))
    prompt = prompt_for_bundle(prompts_md, name)
    source = json.dumps(bundle, ensure_ascii=False)
    lines = [name, slug, prompt, source]
    if all_text:
        key_terms = [name, slug.replace("-", " ")]
        for line in all_text.splitlines():
            low = line.lower()
            if any(k and k.lower() in low for k in key_terms):
                lines.append(line)
    return "\n".join(lines)


def get_run_timestamp() -> Tuple[Optional[datetime], str]:
    candidates = []
    for path in INPUT_RESULTS_MANIFESTS:
        p = Path(path)
        if not p.exists():
            continue
        txt = read_text(path)
        data = read_json(path)
        for key in ["generated_at_utc", "run_started_at_utc", "run_utc", "created_at", "timestamp", "completed_at_utc"]:
            dt = parse_datetime(data.get(key)) if data else None
            if dt:
                candidates.append((dt, f"{path}:{key}"))
        for dt in find_dates_in_text(txt[:5000]):
            candidates.append((dt, f"{path}:text_date"))
    if not candidates:
        return None, ""
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0]


def infer_event_date(bundle: Dict[str, Any], related_text: str) -> Tuple[Optional[datetime], str]:
    keys = [
        "event_date", "event_datetime", "game_date", "game_datetime", "date",
        "result_date", "played_at", "start_time", "completed_at"
    ]
    sources = [bundle, bundle.get("source_facts", {}) if isinstance(bundle.get("source_facts"), dict) else {}]
    for source in sources:
        for key in keys:
            dt = parse_datetime(source.get(key))
            if dt:
                return dt, key
    m = re.search(r"(?:event|game|result|played|date)\s*(?:date|time|at)?\s*[:=]\s*([^\n|]+)", related_text, flags=re.I)
    if m:
        dt = parse_datetime(m.group(1))
        if dt:
            return dt, "related_text_labeled_date"
    dates = find_dates_in_text(related_text)
    if dates:
        dates.sort()
        return dates[0], "related_text_date"
    return None, ""


def carryover_info(text: str) -> Tuple[bool, str]:
    low = text.lower()
    if any(x in low for x in ["carryover", "evergreen", "still relevant"]):
        return True, "carryover"
    if any(x in low for x in ["last night", "yesterday", "yesterday's", "yesterdays"]):
        return True, "last_night_or_yesterday"
    return False, ""


def load_preview_summary() -> Dict[str, str]:
    rows = read_csv(INPUT_PREVIEW_SUMMARY)
    if rows:
        return rows[0]
    build = read_json(INPUT_PREVIEW_BUILD)
    target = clean(build.get("target_local_date") or build.get("target_date_local") or build.get("event_date"))
    if target:
        return {"target_date_local": target[:10], "gate_status": "PASS" if build else ""}
    return {}


def is_preview_bundle(bundle: Dict[str, Any], related_text: str) -> bool:
    blob = " ".join([
        clean(bundle.get("post_slug") or bundle.get("bundle_slug")),
        clean(bundle.get("bundle_name")),
        clean(bundle.get("template_name")),
        related_text[:2000],
    ]).lower()
    return any(x in blob for x in ["tonight in the w", "tonight-in-the-w", "preview", "upcoming", "schedule"])


def same_target_date(event_dt: Optional[datetime], related_text: str, target_date: str) -> bool:
    if not target_date:
        return False
    if event_dt:
        dates = {event_dt.date().isoformat()}
        try:
            dates.add(event_dt.astimezone(local_tz()).date().isoformat())
        except Exception:
            pass
        if target_date in dates:
            return True
    if target_date in related_text:
        return True
    return False


def preview_gate_allows_same_day(bundle: Dict[str, Any], related_text: str, event_dt: Optional[datetime]) -> Tuple[bool, str]:
    summary = load_preview_summary()
    gate_status = clean(summary.get("gate_status")).upper()
    target = clean(os.environ.get("HSD_TARGET_DATE_LOCAL")) or clean(summary.get("target_date_local")) or now_local_date()
    target = target[:10]
    if not is_preview_bundle(bundle, related_text):
        return False, ""
    if gate_status and gate_status != "PASS":
        return False, f"preview gate status={gate_status}"
    if same_target_date(event_dt, related_text, target):
        return True, f"same-day preview allowed by preview gate for target_date_local={target}"
    # If the preview gate passed and the build/summary counted same-day games, allow even when no event date was inferred.
    same_day_count = clean(summary.get("source_same_day_count"))
    included_count = clean(summary.get("included_count"))
    if gate_status == "PASS" and (same_day_count not in {"", "0"} or included_count not in {"", "0"}):
        return True, f"same-day preview allowed by preview gate summary for target_date_local={target}"
    return False, ""


def decision_for_bundle(bundle: Dict[str, Any], related_text: str, source_run_dt: Optional[datetime]) -> Dict[str, Any]:
    now = now_utc()
    event_dt, event_source = infer_event_date(bundle, related_text)
    is_carry, carry_reason = carryover_info(related_text)
    preview_allow, preview_reason = preview_gate_allows_same_day(bundle, related_text, event_dt)
    rec_label = ""
    requires_relabel = "No"
    reasons: List[str] = []
    status = "fresh"
    decision = "allow"

    if preview_allow:
        age_hours = max(0.0, (now - event_dt).total_seconds() / 3600.0) if event_dt else ""
        status = "allowed_same_day_preview"
        decision = "allow"
        reasons.append(preview_reason)
        if event_dt:
            reasons.append("date-only/same-day preview timestamps are treated as the schedule date, not stale completed results")
    elif event_dt:
        age_hours = max(0.0, (now - event_dt).total_seconds() / 3600.0)
        if event_dt > now:
            status = "fresh_upcoming_event"
            decision = "allow"
            reasons.append("event start is upcoming")
        elif age_hours > MAX_FRESH_HOURS:
            if is_carry:
                status = "allowed_carryover"
                decision = "allow"
                rec_label = "Last Night / Yesterday" if "yesterday" in carry_reason or "last_night" in carry_reason else "Carryover"
                requires_relabel = "Yes"
                reasons.append(f"event age {age_hours:.1f}h exceeds {MAX_FRESH_HOURS:.1f}h but carryover/yesterday language is present")
            else:
                status = "blocked_stale_event"
                decision = "block"
                rec_label = "Refresh with newer upstream packet"
                reasons.append(f"event age {age_hours:.1f}h exceeds {MAX_FRESH_HOURS:.1f}h")
        elif event_dt.astimezone(local_tz()).date() < now.astimezone(local_tz()).date():
            status = "allowed_recent_yesterday" if is_carry else "review_yesterday_without_label"
            decision = "allow" if is_carry else "review"
            rec_label = "Last Night / Yesterday"
            requires_relabel = "Yes"
            reasons.append("event local date is before today's local date")
        else:
            reasons.append("event date is within freshness window")
    else:
        age_hours = ""
        if STRICT_MISSING_EVENT_DATE:
            status = "blocked_missing_event_date"
            decision = "block"
            rec_label = "Add event_date upstream or mark carryover"
            reasons.append("no event date found and strict freshness gate is enabled")
        else:
            status = "review_missing_event_date"
            decision = "review"
            rec_label = "Add event_date upstream"
            reasons.append("no event date found")

    if source_run_dt:
        run_age = (now - source_run_dt).total_seconds() / 3600.0
        if run_age > MAX_FRESH_HOURS and decision != "block" and status != "allowed_same_day_preview":
            status = "review_old_upstream_run"
            decision = "review"
            reasons.append(f"upstream run timestamp is {run_age:.1f}h old")
    else:
        reasons.append("no upstream results/news run timestamp found")

    return {
        "event_dt": event_dt,
        "event_source": event_source,
        "event_age_hours": f"{age_hours:.1f}" if isinstance(age_hours, float) else age_hours,
        "is_carryover": "Yes" if is_carry else "No",
        "requires_relabel": requires_relabel,
        "recommended_label": rec_label,
        "freshness_status": status,
        "freshness_decision": decision,
        "reason": "; ".join(reasons),
    }


def main() -> None:
    render_manifest = read_json(INPUT_RENDER_MANIFEST)
    bundles = render_manifest.get("bundles", [])
    queue_rows = read_csv(INPUT_QUEUE)
    prompts_md = read_text(INPUT_BUNDLE_PROMPTS)
    all_text = "\n".join([
        read_text(INPUT_BUNDLE_PACKETS),
        prompts_md,
        read_text(INPUT_LAUNCH_BRIEF),
        "\n".join(json.dumps(r, ensure_ascii=False) for r in queue_rows),
    ])
    source_run_dt, source_evidence = get_run_timestamp()

    rows: List[Dict[str, Any]] = []
    for b in bundles:
        slug = clean(b.get("post_slug")) or clean(b.get("bundle_slug"))
        name = clean(b.get("bundle_name")) or slug
        related = bundle_text(b, all_text, prompts_md)
        d = decision_for_bundle(b, related, source_run_dt)
        rows.append({
            "bundle_slug": slug,
            "bundle_name": name,
            "freshness_status": d["freshness_status"],
            "freshness_decision": d["freshness_decision"],
            "event_date": iso(d["event_dt"]),
            "event_age_hours": d["event_age_hours"],
            "bundle_created_at": clean(b.get("created_at") or b.get("generated_at_utc") or b.get("bundle_created_at")),
            "source_run_timestamp": iso(source_run_dt),
            "is_carryover": d["is_carryover"],
            "requires_relabel": d["requires_relabel"],
            "recommended_label": d["recommended_label"],
            "reason": d["reason"],
            "source_evidence": d["event_source"] or source_evidence,
        })

    stale = [r for r in rows if r.get("freshness_decision") in {"block", "review"}]
    write_csv(OUT_GATE, rows, FIELDS)
    write_csv(OUT_STALE, stale, FIELDS)

    report = [
        "# HSD Studio Freshness Gate v2.5",
        "",
        f"Generated: {iso(now_utc())}",
        "",
        f"- bundles checked: {len(rows)}",
        f"- allowed: {sum(1 for r in rows if r.get('freshness_decision') == 'allow')}",
        f"- review: {sum(1 for r in rows if r.get('freshness_decision') == 'review')}",
        f"- blocked: {sum(1 for r in rows if r.get('freshness_decision') == 'block')}",
        f"- max fresh hours for result-style packets: {MAX_FRESH_HOURS}",
        f"- strict missing event date: {'Yes' if STRICT_MISSING_EVENT_DATE else 'No'}",
        "- same-day preview override: enabled when preview quality gate passes",
        "",
    ]
    for r in rows:
        report += [
            f"## {r['bundle_name']}",
            "",
            f"- Decision: **{r['freshness_decision']}**",
            f"- Status: `{r['freshness_status']}`",
            f"- Event date: `{r['event_date'] or 'missing'}`",
            f"- Recommended label: {r['recommended_label'] or 'none'}",
            f"- Reason: {r['reason']}",
            "",
        ]
    Path(OUT_REPORT).write_text("\n".join(report), encoding="utf-8")
    Path(OUT_MANIFEST).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": iso(now_utc()),
        "counts": {
            "bundles_checked": len(rows),
            "allowed": sum(1 for r in rows if r.get("freshness_decision") == "allow"),
            "review": sum(1 for r in rows if r.get("freshness_decision") == "review"),
            "blocked": sum(1 for r in rows if r.get("freshness_decision") == "block"),
        },
        "outputs": [OUT_GATE, OUT_STALE, OUT_REPORT, OUT_MANIFEST],
    }, indent=2), encoding="utf-8")
    print("Created HSD Studio Freshness Gate v2.5 outputs")
    print(json.dumps(read_json(OUT_MANIFEST).get("counts", {}), indent=2))


if __name__ == "__main__":
    main()
