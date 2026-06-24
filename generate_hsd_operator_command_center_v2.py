from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import input_path, output_path, write_json, write_text

VERSION = "hsd-operator-command-center-v3.0.0-daily-ops"
OUT_HTML = output_path("operator_command_center.html")
OUT_MD = output_path("operator_command_center.md")
OUT_JSON = output_path("operator_command_center.json")

ARTIFACTS = [
    ("Decision", "Operator status", "operator_status.md"),
    ("Decision", "Publish guard", "publish_guard_report.md"),
    ("Decision", "BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("Decision", "BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("Results", "Results manifest", "results_desk_v5_manifest.json"),
    ("Results", "Results report", "results_desk_v5_report.md"),
    ("Results", "Source accuracy", "source_accuracy_v5.md"),
    ("Results", "Missing games alert", "missing_games_alert_v5.md"),
    ("Results", "Top women's results", "top_womens_results.csv"),
    ("Results", "Final results", "today_final_results.csv"),
    ("News", "News fact packets", "news_fact_packets.csv"),
    ("News", "News daily plan", "news_daily_plan.md"),
    ("News", "News sync hub", "news_sync_hub.md"),
    ("Planning", "Multi-post daily board", "multi_post_daily_board.md"),
    ("Planning", "Post slot status", "post_slot_status.csv"),
    ("Planning", "IG feed queue", "ig_feed_queue.csv"),
    ("Planning", "IG story queue", "ig_story_queue.csv"),
    ("Planning", "Threads queue", "threads_queue.csv"),
    ("Planning", "Caption bank", "caption_bank.md"),
    ("Planning", "First comment hooks", "first_comment_hooks.md"),
    ("Launch", "Launch command center", "launch_command_center.md"),
    ("Launch", "Launch daily runbook", "launch_daily_runbook.md"),
    ("Launch", "Launch graphics brief", "launch_graphics_chat_brief.md"),
    ("Launch", "Launch publish queue", "launch_instagram_publish_queue.csv"),
    ("Launch", "Launch quality gate", "launch_quality_gate.csv"),
    ("Launch", "Launch operator checklist", "launch_daily_operator_checklist.md"),
    ("Launch", "Launch metrics input", "launch_metrics_manual_input.csv"),
    ("Launch", "Launch performance dashboard", "launch_7_day_performance_dashboard.md"),
    ("Launch", "Launch manifest", "launch_manifest.json"),
    ("Launch", "Launch dashboard", "launch_dashboard/index.html"),
    ("Launch", "Launch analytics dashboard", "launch_analytics_dashboard/index.html"),
    ("Studio", "Studio queue", "studio_bundle_queue.csv"),
    ("Studio", "Studio packets", "studio_bundle_packets.md"),
    ("Studio", "Preview quality", "preview_bundle_quality.md"),
    ("Studio", "Preview player focus", "preview_player_focus.csv"),
    ("Graphics", "Graphics upload status", "graphics_upload_pack_status.csv"),
    ("Graphics", "Rendered slide QA", "rendered_slide_qa_report.md"),
    ("Graphics", "Final score story queue", "ig_story_results_queue.csv"),
    ("Graphics", "Final score story status", "ig_story_results_upload_pack_status.csv"),
    ("Graphics", "Final score story guard", "final_score_story_guard_report.md"),
    ("Graphics", "Manual workflow handoff", "manual_workflow_handoff.md"),
    ("Graphics", "Manual workflow pack status", "manual_workflow_pack_status.csv"),
    ("Review", "Lite review zip", "hsd_pipeline_lite_review.zip"),
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "ready"}


def read_text(path: str, max_chars: int | None = None) -> str:
    p = input_path(path)
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars] if max_chars else text


def read_json(path: str) -> Dict[str, Any]:
    p = input_path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_csv(path: str) -> List[Dict[str, str]]:
    p = input_path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def first_present(*values: Any, default: str = "") -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return default


def short(text: str, limit: int = 180) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def status_tone(value: Any) -> str:
    text = clean(value).lower()
    if not text:
        return "neutral"
    if any(token in text for token in ["pass", "ready", "ok", "allow", "yes", "true", "complete", "high"]):
        return "good"
    if any(token in text for token in ["fail", "blocked", "missing", "error", "no-go", "false", "critical", "hold"]):
        return "bad"
    if any(token in text for token in ["review", "pending", "not_run", "not created", "not_created", "draft", "needed"]):
        return "warn"
    return "neutral"


def display_bool(value: Any) -> str:
    return "Yes" if yes(value) else "No"


def parse_markdown_table(path: str) -> List[Dict[str, str]]:
    text = read_text(path)
    rows: List[Dict[str, str]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return rows
    headers = [clean(cell) for cell in lines[0].strip("|").split("|")]
    for line in lines[2:]:
        cells = [clean(cell) for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def artifact_entries() -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for group, title, path in ARTIFACTS:
        p = input_path(path)
        snippet = ""
        if p.suffix.lower() in {".csv", ".json", ".md", ".txt"}:
            snippet = short(read_text(path, 480), 260)
        elif p.exists():
            snippet = f"Binary artifact ({p.stat().st_size} bytes)"
        entries.append(
            {
                "group": group,
                "title": title,
                "path": path,
                "exists": p.exists(),
                "size": p.stat().st_size if p.exists() and p.is_file() else 0,
                "snippet": snippet,
            }
        )
    return entries


def source_health(manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    health = manifest.get("source_health", [])
    if not isinstance(health, list):
        return []
    out: List[Dict[str, str]] = []
    for row in health:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "source": clean(row.get("source_name")),
                "league": clean(row.get("sport_or_league")),
                "date": clean(row.get("date")),
                "ok": clean(row.get("ok")),
                "events": clean(row.get("events_found")),
                "notes": clean(row.get("notes")),
            }
        )
    return out


def content_candidates() -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for row in read_csv("news_fact_packets.csv")[:8]:
        candidates.append(
            {
                "type": "News packet",
                "priority": first_present(row.get("urgency"), row.get("publish_recommendation"), default="Review"),
                "headline": first_present(row.get("headline"), row.get("dek")),
                "status": "Ready" if clean(row.get("production_ready")).lower() == "yes" else "Review",
                "detail": short(first_present(row.get("caption_hard_fact"), row.get("brief_120w"), row.get("dek")), 210),
                "artifact": "news_fact_packets.csv",
                "source_count": clean(row.get("source_count")),
            }
        )
    for row in read_csv("today_final_results.csv")[:6]:
        candidates.append(
            {
                "type": "Final result",
                "priority": first_present(row.get("posting_priority"), row.get("editorial_bucket"), default="Review"),
                "headline": first_present(row.get("graphics_headline"), row.get("caption_seed")),
                "status": "Graphics ready" if clean(row.get("include_in_graphics")).lower() == "yes" else "Review",
                "detail": short(first_present(row.get("graphics_subhead"), row.get("final_score_display"), row.get("caption_seed")), 210),
                "artifact": "today_final_results.csv",
                "source_count": clean(row.get("source_count")),
            }
        )
    return candidates


def studio_queue() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("studio_bundle_queue.csv")[:8]:
        rows.append(
            {
                "priority": first_present(row.get("production_priority"), row.get("bundle_rank"), default="Review"),
                "name": first_present(row.get("bundle_name"), row.get("content_family"), default="Untitled bundle"),
                "type": first_present(row.get("bundle_type"), row.get("asset_type")),
                "shape": first_present(row.get("asset_shape"), row.get("slide_count")),
                "status": first_present(row.get("freshness_decision"), row.get("freshness_status"), default="Review"),
                "detail": short(first_present(row.get("source_headlines"), row.get("caption_seed")), 260),
                "artifact": "studio_bundle_queue.csv",
            }
        )
    return rows


def schedule_rows() -> List[Dict[str, str]]:
    rows = parse_markdown_table("bebe_posting_schedule_today.md")
    normalized: List[Dict[str, str]] = []
    for row in rows[:12]:
        normalized.append(
            {
                "time": first_present(row.get("Time ET"), row.get("Time")),
                "platform": first_present(row.get("Platform")),
                "slot": first_present(row.get("Slot")),
                "status": first_present(row.get("Status"), default="operator_action"),
                "action": first_present(row.get("Recommended action"), row.get("Action")),
                "artifact": first_present(row.get("Artifact")),
            }
        )
    return normalized


def build_next_actions(
    operator: Dict[str, Any],
    guard: Dict[str, Any],
    candidates: List[Dict[str, str]],
    studio: List[Dict[str, str]],
    artifacts: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    artifact_exists = {row["path"]: bool(row["exists"]) for row in artifacts}
    actions: List[Dict[str, str]] = []
    issues = operator.get("issues") or guard.get("issues") or []
    critical = [issue for issue in issues if clean(issue.get("severity")).lower() == "critical"] if isinstance(issues, list) else []

    if critical:
        issue = critical[0]
        actions.append(
            {
                "rank": "1",
                "status": "Blocked",
                "owner": "Operator",
                "title": first_present(issue.get("code"), default="Resolve blocking issue"),
                "detail": first_present(issue.get("detail"), issue.get("headline")),
                "artifact": "operator_status.md",
            }
        )

    if studio and not artifact_exists.get("graphics_upload_pack_status.csv"):
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": "Needs assets",
                "owner": "Graphics",
                "title": f"Build graphics pack for {studio[0]['name']}",
                "detail": studio[0]["detail"],
                "artifact": "studio_bundle_queue.csv",
            }
        )

    ready_candidates = [item for item in candidates if item.get("status") in {"Ready", "Graphics ready"}]
    if ready_candidates:
        item = ready_candidates[0]
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": "Review ready",
                "owner": "Editor",
                "title": item["headline"],
                "detail": item["detail"],
                "artifact": item["artifact"],
            }
        )

    if clean(guard.get("rendered_qa_status")).lower() in {"", "not_run"}:
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": "QA pending",
                "owner": "Operator",
                "title": "Run rendered-slide QA after graphics exist",
                "detail": "Do not post until rendered graphics are checked against the source packet and public-facing copy.",
                "artifact": "rendered_slide_qa_report.md",
            }
        )

    if not yes(guard.get("publish_allowed")):
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": "Manual only",
                "owner": "Publisher",
                "title": "Keep publishing off",
                "detail": "Use artifacts for review and manual posting only. No auto-publishing path is enabled.",
                "artifact": "publish_guard_report.md",
            }
        )

    for index, action in enumerate(actions, 1):
        action["rank"] = str(index)
    return actions[:6]


def metric(label: str, value: Any, detail: str = "") -> Dict[str, str]:
    text = clean(value)
    return {"label": label, "value": text, "detail": clean(detail), "tone": status_tone(text)}


def build_payload() -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    operator = read_json("operator_status.json")
    guard = read_json("publish_guard_report.json")
    manifest = read_json("results_desk_v5_manifest.json")
    ops = read_json("bebe_daily_ops_status.json")
    handoff = read_json("assignment_handoff_publisher_manifest.json")
    render = read_json("rendered_slide_qa_manifest.json")
    artifacts = artifact_entries()
    candidates = content_candidates()
    studio = studio_queue()
    schedule = schedule_rows()
    counts = manifest.get("counts", {}) if isinstance(manifest.get("counts"), dict) else {}
    handoff_counts = handoff.get("counts", {}) if isinstance(handoff.get("counts"), dict) else {}
    render_counts = render.get("counts", {}) if isinstance(render.get("counts"), dict) else {}

    decision = {
        "overall": first_present(operator.get("overall"), default="NO-GO"),
        "publish_allowed": bool(guard.get("publish_allowed")),
        "graphics_handoff_allowed": bool(guard.get("graphics_handoff_allowed")),
        "publish_mode": first_present(guard.get("publish_mode"), default="artifact_only"),
        "automation": "OFF / artifact-only",
        "free_source_mode": "Free public sources only",
        "callout": "Manual review required before any post leaves the system.",
    }
    metrics = [
        metric("Current call", decision["overall"]),
        metric("Publish allowed", display_bool(decision["publish_allowed"])),
        metric("Graphics handoff", display_bool(decision["graphics_handoff_allowed"])),
        metric("Preview gate", first_present(guard.get("preview_gate_status"), default="not_run")),
        metric("Graphics pack", "ready" if input_path("graphics_upload_pack_status.csv").exists() else "not_created"),
        metric("Rendered QA", first_present(guard.get("rendered_qa_status"), render_counts.get("decision"), default="not_run")),
        metric("Women's events", counts.get("women_events", "0")),
        metric("Graphics-ready results", counts.get("graphics_ready", "0")),
        metric("News packets", len(read_csv("news_fact_packets.csv"))),
        metric("Studio bundles", len(studio)),
        metric("Handoff packets", handoff_counts.get("handoff_packets") or "0"),
        metric("Day type", first_present(ops.get("day_type"), default="normal_day")),
    ]
    next_actions = build_next_actions(operator, guard, candidates, studio, artifacts)
    source_rows = source_health(manifest)
    briefing = {
        "best_candidate": candidates[0]["headline"] if candidates else "No content candidate found",
        "studio_lane": studio[0]["name"] if studio else "No studio bundle found",
        "source_state": f"{sum(1 for row in source_rows if clean(row.get('ok')).lower() == 'yes')} source check(s) OK",
        "next_manual_move": next_actions[0]["title"] if next_actions else "Review local artifacts",
    }

    return {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "decision": decision,
        "briefing": briefing,
        "metrics": metrics,
        "next_actions": next_actions,
        "schedule": schedule,
        "content_candidates": candidates,
        "studio_queue": studio,
        "source_health": source_rows,
        "issues": operator.get("issues") or guard.get("issues") or [],
        "artifacts": artifacts,
        "counts": counts,
    }


def pill(value: Any, tone: str | None = None) -> str:
    text = clean(value)
    return f'<span class="pill {html.escape(tone or status_tone(text))}">{html.escape(text)}</span>'


def open_link(path: str, label: str = "Open") -> str:
    if not path or not input_path(path).exists():
        return '<span class="muted">Missing</span>'
    return f'<a class="tool-link" href="{html.escape(path)}">{html.escape(label)}</a>'


def render_action_rows(actions: Iterable[Dict[str, str]]) -> str:
    rows = []
    for action in actions:
        rows.append(
            f"""
            <article class="action-row">
              <div class="rank">{html.escape(action['rank'])}</div>
              <div>
                <div class="row-kicker">{html.escape(action['owner'])} {pill(action['status'])}</div>
                <h3>{html.escape(action['title'])}</h3>
                <p>{html.escape(action['detail'])}</p>
              </div>
              <div class="row-tool">{open_link(action.get('artifact', ''))}</div>
            </article>
            """
        )
    return "".join(rows) or '<p class="empty">No next actions found.</p>'


def render_schedule(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['time'])}</td>
              <td>{html.escape(row['platform'])}</td>
              <td>{html.escape(row['slot'])}</td>
              <td>{pill(row['status'])}</td>
              <td>{html.escape(row['action'])}</td>
              <td>{open_link(row['artifact']) if row['artifact'] else '<span class="muted">-</span>'}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No posting schedule found.</td></tr>'


def render_content(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row['type'])} {pill(row['priority'])} {pill(row['status'])}</div>
                <h3>{html.escape(row['headline'])}</h3>
                <p>{html.escape(row['detail'])}</p>
                <small>{html.escape(row.get('source_count') or '0')} source(s)</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No content candidates found.</p>'


def render_studio(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row['priority'])} {pill(row['status'])}</div>
                <h3>{html.escape(row['name'])}</h3>
                <p>{html.escape(row['detail'])}</p>
                <small>{html.escape(row['type'])} / {html.escape(row['shape'])}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No studio bundles found.</p>'


def render_sources(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['source'])}</td>
              <td>{html.escape(row['league'])}</td>
              <td>{html.escape(row['date'])}</td>
              <td>{pill(row['ok'])}</td>
              <td>{html.escape(row['events'])}</td>
              <td>{html.escape(row['notes'])}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No source health rows found.</td></tr>'


def render_issues(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for issue in rows:
        body.append(
            f"""
            <article class="issue-row">
              <div>{pill(clean(issue.get('severity')) or 'review')}</div>
              <div>
                <h3>{html.escape(clean(issue.get('code')) or 'Review note')}</h3>
                <p>{html.escape(first_present(issue.get('detail'), issue.get('headline')))}</p>
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No blocking issues reported.</p>'


def render_artifacts(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr data-artifact-row data-group="{html.escape(row['group'].lower())}" data-search="{html.escape((row['group'] + ' ' + row['title'] + ' ' + row['path']).lower())}">
              <td>{html.escape(row['group'])}</td>
              <td>{html.escape(row['title'])}</td>
              <td><code>{html.escape(row['path'])}</code></td>
              <td>{pill('found' if row['exists'] else 'missing')}</td>
              <td>{open_link(row['path'])}</td>
            </tr>
            """
        )
    return "".join(body)


def render_html(payload: Dict[str, Any]) -> str:
    decision = payload["decision"]
    metrics = "".join(
        f"""
        <section class="metric {html.escape(item['tone'])}">
          <span>{html.escape(item['label'])}</span>
          <strong>{html.escape(item['value'])}</strong>
          {f"<small>{html.escape(item['detail'])}</small>" if item.get("detail") else ""}
        </section>
        """
        for item in payload["metrics"]
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>HSD Daily Operator Command Center</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --ink:#171719;
      --muted:#696b73;
      --line:#dedfe6;
      --paper:#ffffff;
      --wash:#f4f5f8;
      --green:#1f7a4d;
      --green-bg:#dff5e8;
      --red:#9c211a;
      --red-bg:#fde2df;
      --amber:#806400;
      --amber-bg:#fff0b8;
      --blue:#255f9f;
      --blue-bg:#e2effc;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--wash); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif; line-height:1.45; }}
    header {{ background:#171719; color:#fff; padding:24px 28px; border-bottom:5px solid #f0c84b; }}
    header h1 {{ margin:0; font-size:28px; line-height:1.1; letter-spacing:0; }}
    header p {{ margin:8px 0 0; color:#d9d9df; max-width:900px; overflow-wrap:anywhere; }}
    main {{ max-width:1320px; margin:0 auto; padding:22px 24px 48px; }}
    h2 {{ margin:0 0 12px; font-size:20px; }}
    h3 {{ margin:4px 0 6px; font-size:16px; }}
    p {{ margin:0; }}
    code {{ background:#eceef4; padding:2px 5px; border-radius:4px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:10px 8px; vertical-align:top; }}
    th {{ color:#555861; font-size:12px; text-transform:uppercase; }}
    .top-grid {{ display:grid; grid-template-columns:1.15fr .85fr; gap:16px; align-items:stretch; }}
    .panel {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(20,20,30,.05); min-width:0; }}
    .decision {{ display:grid; gap:14px; grid-template-columns:1fr auto; }}
    .decision-call strong {{ display:block; font-size:34px; line-height:1; margin:8px 0; }}
    .safety-strip {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
    .brief-list {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:18px; }}
    .brief-list div {{ border-top:1px solid var(--line); padding-top:10px; }}
    .brief-list span {{ display:block; color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; }}
    .brief-list strong {{ display:block; margin-top:4px; font-size:14px; line-height:1.35; overflow-wrap:anywhere; }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:16px 0; }}
    .metric {{ background:#fff; border:1px solid var(--line); border-left:5px solid #aeb2bd; border-radius:8px; padding:12px; min-height:78px; }}
    .metric span {{ display:block; color:#5e616a; font-size:12px; font-weight:700; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:5px; font-size:19px; overflow-wrap:anywhere; }}
    .metric.good {{ border-left-color:var(--green); }}
    .metric.bad {{ border-left-color:var(--red); }}
    .metric.warn {{ border-left-color:#d7a900; }}
    .metric.neutral {{ border-left-color:var(--blue); }}
    .tabs {{ display:flex; gap:6px; flex-wrap:wrap; margin:14px 0; }}
    .tab-button {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:9px 12px; font-weight:700; cursor:pointer; }}
    .tab-button[aria-selected="true"] {{ background:#171719; color:white; border-color:#171719; }}
    .tab-panel {{ display:none; }}
    .tab-panel.active {{ display:block; }}
    .action-list,.content-list,.issue-list {{ display:grid; gap:10px; }}
    .action-row,.content-row,.issue-row {{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:12px; align-items:start; background:#fff; border:1px solid var(--line); border-radius:8px; padding:12px; min-width:0; }}
    .content-row,.issue-row {{ grid-template-columns:1fr auto; }}
    .action-row > *,.content-row > *,.issue-row > * {{ min-width:0; }}
    .rank {{ width:32px; height:32px; border-radius:50%; background:#171719; color:#fff; display:grid; place-items:center; font-weight:800; }}
    .row-kicker {{ color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; display:flex; gap:6px; align-items:center; flex-wrap:wrap; }}
    .row-tool {{ align-self:center; }}
    .pill {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:12px; font-weight:800; background:#eceef4; color:#333640; }}
    .pill.good {{ background:var(--green-bg); color:var(--green); }}
    .pill.bad {{ background:var(--red-bg); color:var(--red); }}
    .pill.warn {{ background:var(--amber-bg); color:var(--amber); }}
    .pill.neutral {{ background:var(--blue-bg); color:var(--blue); }}
    .tool-link {{ display:inline-block; border:1px solid #c8cbd4; border-radius:6px; padding:7px 10px; color:#171719; text-decoration:none; font-weight:800; background:#fff; }}
    .tool-link:hover {{ border-color:#171719; }}
    .muted,.empty {{ color:var(--muted); }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .artifact-toolbar {{ display:flex; gap:10px; align-items:center; margin-bottom:12px; flex-wrap:wrap; }}
    .artifact-toolbar input {{ min-width:280px; flex:1; border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; }}
    .artifact-toolbar select {{ border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; background:#fff; }}
    .table-wrap {{ overflow:auto; background:#fff; border:1px solid var(--line); border-radius:8px; max-width:100%; }}
    @media (max-width: 900px) {{
      header {{ padding:20px; }}
      main {{ padding:16px; }}
      .top-grid,.two-col {{ grid-template-columns:1fr; }}
      .decision {{ grid-template-columns:1fr; }}
      .metric-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .brief-list {{ grid-template-columns:1fr; }}
      .action-row,.content-row,.issue-row {{ grid-template-columns:1fr; }}
      .rank {{ width:28px; height:28px; }}
    }}
    @media (max-width: 560px) {{
      .metric-grid {{ grid-template-columns:1fr; }}
      header h1 {{ font-size:23px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>HSD Daily Operator Command Center</h1>
    <p>Generated {html.escape(payload['generated_at_utc'])}. Local/manual operation is the default. Paid APIs and auto-publishing are off.</p>
  </header>
  <main>
    <section class="top-grid">
      <div class="panel decision">
        <div class="decision-call">
          <span class="row-kicker">Current call</span>
          <strong>{html.escape(decision['overall'])}</strong>
          <p>{html.escape(decision['callout'])}</p>
          <div class="safety-strip">
            {pill(decision['free_source_mode'], 'good')}
            {pill(f"Publish allowed: {display_bool(decision['publish_allowed'])}")}
            {pill(f"Graphics handoff: {display_bool(decision['graphics_handoff_allowed'])}")}
            {pill(decision['automation'])}
          </div>
          <div class="brief-list">
            <div><span>Best candidate</span><strong>{html.escape(payload['briefing']['best_candidate'])}</strong></div>
            <div><span>Studio lane</span><strong>{html.escape(payload['briefing']['studio_lane'])}</strong></div>
            <div><span>Source state</span><strong>{html.escape(payload['briefing']['source_state'])}</strong></div>
            <div><span>Next manual move</span><strong>{html.escape(payload['briefing']['next_manual_move'])}</strong></div>
          </div>
        </div>
        <div>{open_link('publish_guard_report.md', 'Open guard')}</div>
      </div>
      <div class="panel">
        <h2>Top next actions</h2>
        <div class="action-list">{render_action_rows(payload['next_actions'][:3])}</div>
      </div>
    </section>

    <section class="metric-grid">{metrics}</section>

    <nav class="tabs" aria-label="Command center views">
      <button class="tab-button" type="button" data-tab-target="today" aria-selected="true">Today</button>
      <button class="tab-button" type="button" data-tab-target="content" aria-selected="false">Content</button>
      <button class="tab-button" type="button" data-tab-target="safety" aria-selected="false">Safety</button>
      <button class="tab-button" type="button" data-tab-target="artifacts" aria-selected="false">Artifacts</button>
    </nav>

    <section id="today" class="tab-panel active">
      <div class="two-col">
        <div class="panel">
          <h2>Action queue</h2>
          <div class="action-list">{render_action_rows(payload['next_actions'])}</div>
        </div>
        <div class="panel">
          <h2>Posting schedule</h2>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Time ET</th><th>Platform</th><th>Slot</th><th>Status</th><th>Action</th><th>Artifact</th></tr></thead>
              <tbody>{render_schedule(payload['schedule'])}</tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section id="content" class="tab-panel">
      <div class="two-col">
        <div class="panel">
          <h2>Content candidates</h2>
          <div class="content-list">{render_content(payload['content_candidates'])}</div>
        </div>
        <div class="panel">
          <h2>Studio queue</h2>
          <div class="content-list">{render_studio(payload['studio_queue'])}</div>
        </div>
      </div>
    </section>

    <section id="safety" class="tab-panel">
      <div class="two-col">
        <div class="panel">
          <h2>Blocks and review notes</h2>
          <div class="issue-list">{render_issues(payload['issues'])}</div>
        </div>
        <div class="panel">
          <h2>Source health</h2>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Source</th><th>League</th><th>Date</th><th>OK</th><th>Events</th><th>Notes</th></tr></thead>
              <tbody>{render_sources(payload['source_health'])}</tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section id="artifacts" class="tab-panel">
      <div class="panel">
        <h2>Artifact desk</h2>
        <div class="artifact-toolbar">
          <input id="artifactSearch" type="search" placeholder="Filter artifacts">
          <select id="artifactGroup" aria-label="Artifact group">
            <option value="">All groups</option>
            <option value="decision">Decision</option>
            <option value="results">Results</option>
            <option value="news">News</option>
            <option value="studio">Studio</option>
            <option value="graphics">Graphics</option>
            <option value="review">Review</option>
          </select>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Group</th><th>Artifact</th><th>Path</th><th>Status</th><th>Open</th></tr></thead>
            <tbody>{render_artifacts(payload['artifacts'])}</tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
  <script>
    const buttons = Array.from(document.querySelectorAll("[data-tab-target]"));
    const panels = Array.from(document.querySelectorAll(".tab-panel"));
    buttons.forEach((button) => {{
      button.addEventListener("click", () => {{
        const target = button.getAttribute("data-tab-target");
        buttons.forEach((b) => b.setAttribute("aria-selected", String(b === button)));
        panels.forEach((panel) => panel.classList.toggle("active", panel.id === target));
      }});
    }});
    const search = document.getElementById("artifactSearch");
    const group = document.getElementById("artifactGroup");
    const rows = Array.from(document.querySelectorAll("[data-artifact-row]"));
    function filterArtifacts() {{
      const q = (search.value || "").trim().toLowerCase();
      const g = (group.value || "").trim().toLowerCase();
      rows.forEach((row) => {{
        const text = row.getAttribute("data-search") || "";
        const rowGroup = row.getAttribute("data-group") || "";
        row.style.display = (!q || text.includes(q)) && (!g || rowGroup === g) ? "" : "none";
      }});
    }}
    search.addEventListener("input", filterArtifacts);
    group.addEventListener("change", filterArtifacts);
  </script>
</body>
</html>
"""
    return html_doc


def render_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# HSD Daily Operator Command Center",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {payload['version']}",
        "",
        "## Decision",
        "",
        f"- Current call: {payload['decision']['overall']}",
        f"- Publish allowed: {display_bool(payload['decision']['publish_allowed'])}",
        f"- Graphics handoff allowed: {display_bool(payload['decision']['graphics_handoff_allowed'])}",
        f"- Automation: {payload['decision']['automation']}",
        f"- Source mode: {payload['decision']['free_source_mode']}",
        "",
        "## Next actions",
        "",
    ]
    lines.extend(
        f"{action['rank']}. [{action['status']}] {action['title']} - {action['detail']} ({action['artifact']})"
        for action in payload["next_actions"]
    )
    lines += ["", "## Content candidates", ""]
    lines.extend(f"- {item['type']} | {item['priority']} | {item['headline']} | {item['status']}" for item in payload["content_candidates"])
    lines += ["", "## Studio queue", ""]
    lines.extend(f"- {item['priority']} | {item['name']} | {item['status']} | {item['detail']}" for item in payload["studio_queue"])
    lines += ["", "## Artifacts", ""]
    lines.extend(f"- [{'found' if item['exists'] else 'missing'}] `{item['path']}` - {item['title']}" for item in payload["artifacts"])
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(payload: Dict[str, Any]) -> None:
    write_json(OUT_JSON, payload)
    write_text(OUT_MD, render_markdown(payload))
    write_text(OUT_HTML, render_html(payload))


def main() -> None:
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps({"version": VERSION, "html": OUT_HTML.as_posix(), "actions": len(payload["next_actions"])}, indent=2))


if __name__ == "__main__":
    main()
