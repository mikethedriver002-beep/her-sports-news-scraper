from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import input_path, output_path, write_json, write_text

VERSION = "hsd-operator-command-center-v3.15.0-league-proposal-packs"
OUT_HTML = output_path("operator_command_center.html")
OUT_MD = output_path("operator_command_center.md")
OUT_JSON = output_path("operator_command_center.json")

ARTIFACTS = [
    ("Decision", "Operator status", "operator_status.md"),
    ("Decision", "Publish guard", "publish_guard_report.md"),
    ("Decision", "BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("Decision", "BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("Sources", "Source registry audit", "source_registry_audit.md"),
    ("Sources", "Source registry audit data", "source_registry_audit.json"),
    ("Sources", "Source registry audit table", "source_registry_audit.csv"),
    ("Sources", "Source coverage map", "source_coverage_map.csv"),
    ("Sources", "Source registry intake guide", "source_registry_intake_template.md"),
    ("Sources", "Source registry intake template", "source_registry_intake_template.csv"),
    ("Sources", "Source proposal review", "source_registry_proposal_review.md"),
    ("Sources", "Source proposal review data", "source_registry_proposal_review.csv"),
    ("Sources", "Guided source proposal packs", "source_proposal_packs.md"),
    ("Sources", "Guided source proposal pack data", "source_proposal_packs.csv"),
    ("Sources", "WNBA source proposal pack", "wnba_source_proposal_pack.md"),
    ("Sources", "WNBA source proposal pack data", "wnba_source_proposal_pack.csv"),
    ("Sources", "NWSL source proposal pack", "nwsl_source_proposal_pack.md"),
    ("Sources", "NWSL source proposal pack data", "nwsl_source_proposal_pack.csv"),
    ("Sources", "LPGA source proposal pack", "lpga_source_proposal_pack.md"),
    ("Sources", "LPGA source proposal pack data", "lpga_source_proposal_pack.csv"),
    ("Sources", "PWHL source proposal pack", "pwhl_source_proposal_pack.md"),
    ("Sources", "PWHL source proposal pack data", "pwhl_source_proposal_pack.csv"),
    ("Sources", "Manual story intake report", "manual_story_inbox_report.md"),
    ("Sources", "Manual story intake data", "story_candidates_manual.csv"),
    ("Sources", "Discovery intake report", "discovery_sources_report.md"),
    ("Sources", "Discovery intake data", "story_candidates_discovery.csv"),
    ("Sources", "Morning source discovery board", "morning_source_discovery_board.md"),
    ("Sources", "Morning source discovery data", "morning_source_discovery_board.csv"),
    ("Sources", "Morning source discovery manifest", "morning_source_discovery_board.json"),
    ("Sources", "Lead promotion recommendations", "morning_lead_promotion_recommendations.md"),
    ("Sources", "Lead promotion recommendation data", "morning_lead_promotion_recommendations.csv"),
    ("Sources", "Lead promotion recommendation manifest", "morning_lead_promotion_recommendations.json"),
    ("Results", "Results manifest", "results_desk_v5_manifest.json"),
    ("Results", "Results report", "results_desk_v5_report.md"),
    ("Results", "Source accuracy", "source_accuracy_v5.md"),
    ("Results", "Missing games alert", "missing_games_alert_v5.md"),
    ("Results", "Top women's results", "top_womens_results.csv"),
    ("Results", "Final results", "today_final_results.csv"),
    ("Results", "Results drill-down dashboard", "results_dashboard/index.html"),
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
    ("Studio", "Studio drill-down dashboard", "studio_dashboard/index.html"),
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

RUN_COMMANDS = {
    "results_dashboard/index.html": ".\\hsd.cmd run -Mode dashboards",
    "studio_dashboard/index.html": ".\\hsd.cmd run -Mode dashboards",
    "graphics_upload_pack_status.csv": ".\\hsd.cmd run -Mode asset",
    "rendered_slide_qa_report.md": ".\\hsd.cmd run -Mode asset",
    "ig_story_results_queue.csv": ".\\hsd.cmd run -Mode stories",
    "ig_story_results_upload_pack_status.csv": ".\\hsd.cmd run -Mode stories",
    "final_score_story_guard_report.md": ".\\hsd.cmd run -Mode stories",
    "manual_workflow_handoff.md": ".\\hsd.cmd run -Mode handoff",
    "manual_workflow_pack_status.csv": ".\\hsd.cmd run -Mode handoff",
    "multi_post_daily_board.md": ".\\hsd.cmd run -Mode posts",
    "post_slot_status.csv": ".\\hsd.cmd run -Mode posts",
    "ig_feed_queue.csv": ".\\hsd.cmd run -Mode posts",
    "ig_story_queue.csv": ".\\hsd.cmd run -Mode posts",
    "threads_queue.csv": ".\\hsd.cmd run -Mode posts",
    "caption_bank.md": ".\\hsd.cmd run -Mode posts",
    "first_comment_hooks.md": ".\\hsd.cmd run -Mode posts",
    "manual_story_inbox_report.md": ".\\hsd.cmd run -Mode review",
    "story_candidates_manual.csv": ".\\hsd.cmd run -Mode review",
    "discovery_sources_report.md": ".\\hsd.cmd run -Mode review",
    "story_candidates_discovery.csv": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.md": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.csv": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.json": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.md": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.csv": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.json": ".\\hsd.cmd run -Mode review",
    "source_registry_intake_template.md": ".\\hsd.cmd run -Mode review",
    "source_registry_intake_template.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.csv": ".\\hsd.cmd run -Mode review",
    "source_proposal_packs.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_packs.csv": ".\\hsd.cmd run -Mode review",
    "wnba_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "wnba_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "nwsl_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "nwsl_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "lpga_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "lpga_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "pwhl_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "pwhl_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "launch_daily_runbook.md": ".\\hsd.cmd run -Mode launch",
    "launch_graphics_chat_brief.md": ".\\hsd.cmd run -Mode launch",
    "launch_daily_operator_checklist.md": ".\\hsd.cmd run -Mode launch",
    "launch_7_day_performance_dashboard.md": ".\\hsd.cmd run -Mode launch",
    "launch_manifest.json": ".\\hsd.cmd run -Mode launch",
    "launch_dashboard/index.html": ".\\hsd.cmd run -Mode launch",
    "launch_analytics_dashboard/index.html": ".\\hsd.cmd run -Mode launch",
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


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


def as_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def packet_source_confidence(row: Dict[str, Any]) -> Dict[str, str]:
    explicit_grade = first_present(row.get("source_publish_grade"), row.get("source_confidence_tier"))
    if explicit_grade:
        return {
            "source_grade": explicit_grade,
            "source_score": clean(row.get("source_confidence_score")),
            "source_reason": short(clean(row.get("source_confidence_reason")), 160),
        }

    source_count = as_int(row.get("source_count"))
    primary_count = as_int(row.get("primary_source_count"))
    if yes(row.get("production_ready")) and primary_count:
        grade = "publish_grade"
        reason = "Legacy packet inferred from production-ready status and primary source count"
    elif yes(row.get("production_ready")) and source_count >= 2:
        grade = "review_before_publish"
        reason = "Legacy packet inferred from production-ready status and multiple sources"
    elif source_count:
        grade = "discovery_only"
        reason = "Legacy packet has source depth but no confidence fields"
    else:
        grade = "not_scored"
        reason = "No source confidence fields found"

    return {"source_grade": grade, "source_score": "", "source_reason": reason}


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
                "run_command": "" if p.exists() else RUN_COMMANDS.get(path, ""),
                "status_detail": "Ready to open" if p.exists() else missing_artifact_detail(path),
            }
        )
    return entries


def missing_artifact_detail(path: str) -> str:
    command = RUN_COMMANDS.get(path, "")
    if command:
        return f"Create with `{command}`"
    return "Not created in this run"


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


def source_coverage_map(source_registry: Dict[str, Any]) -> List[Dict[str, str]]:
    coverage = source_registry.get("coverage_map", [])
    if not isinstance(coverage, list):
        return []
    out: List[Dict[str, str]] = []
    for row in coverage:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "key": clean(row.get("coverage_key")),
                "name": clean(row.get("display_name")),
                "status": clean(row.get("coverage_status")) or "review",
                "official": clean(row.get("official_sources")),
                "team": clean(row.get("team_sources")),
                "wire": clean(row.get("wire_sources")),
                "cross_check": clean(row.get("cross_check_sources")),
                "gap": clean(row.get("coverage_gap")),
                "next_step": clean(row.get("operator_next_step")),
            }
        )
    return out


def content_candidates() -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for row in read_csv("news_fact_packets.csv")[:8]:
        source_confidence = packet_source_confidence(row)
        candidates.append(
            {
                "type": "News packet",
                "priority": first_present(row.get("urgency"), row.get("publish_recommendation"), default="Review"),
                "headline": first_present(row.get("headline"), row.get("dek")),
                "status": "Ready" if clean(row.get("production_ready")).lower() == "yes" else "Review",
                "detail": short(first_present(row.get("caption_hard_fact"), row.get("brief_120w"), row.get("dek")), 210),
                "artifact": "news_fact_packets.csv",
                "source_count": clean(row.get("source_count")),
                **source_confidence,
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
                "source_grade": "publish_grade" if clean(row.get("manual_review")).lower() != "true" and clean(row.get("manual_review")).lower() != "yes" else "review_before_publish",
                "source_score": clean(row.get("confidence")),
                "source_reason": short(clean(row.get("confidence_reason_json")), 160),
            }
        )
    return candidates


def source_discovery_board() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_source_discovery_board.csv"):
        rows.append(
            {
                "rank": clean(row.get("rank")),
                "lane": first_present(row.get("lane"), default="source_review"),
                "status": first_present(row.get("review_status"), default="review"),
                "posture": first_present(row.get("publish_posture"), default="discovery_only"),
                "band": first_present(row.get("source_band"), default="yellow"),
                "source": first_present(row.get("source_name"), row.get("source_type"), default="Unknown source"),
                "title": first_present(row.get("title"), row.get("source_url"), default="Untitled source lead"),
                "detail": short(first_present(row.get("evidence_preview"), row.get("summary"), row.get("reason"), row.get("next_action")), 260),
                "next_action": short(clean(row.get("next_action")), 180),
                "artifact": first_present(row.get("source_artifact"), default="morning_source_discovery_board.csv"),
                "url": clean(row.get("source_url")),
                "evidence_title": clean(row.get("evidence_title")),
                "evidence_published_at": clean(row.get("evidence_published_at")),
                "evidence_description": short(clean(row.get("evidence_description")), 260),
                "evidence_preview": short(clean(row.get("evidence_preview")), 260),
                "evidence_source": clean(row.get("evidence_source")),
                "story_opportunity_id": clean(row.get("story_opportunity_id")),
                "story_opportunity_title": clean(row.get("story_opportunity_title")),
                "story_opportunity_size": clean(row.get("story_opportunity_size")),
                "story_opportunity_sources": clean(row.get("story_opportunity_sources")),
                "story_opportunity_urls": clean(row.get("story_opportunity_urls")),
                "story_opportunity_reason": short(clean(row.get("story_opportunity_reason")), 220),
                "story_opportunity_angle": clean(row.get("story_opportunity_angle")),
                "story_opportunity_recommended_path": clean(row.get("story_opportunity_recommended_path")),
                "story_opportunity_path_reason": short(clean(row.get("story_opportunity_path_reason")), 220),
                "story_opportunity_confidence_tier": clean(row.get("story_opportunity_confidence_tier")),
                "story_opportunity_source_coverage": clean(row.get("story_opportunity_source_coverage")),
                "story_opportunity_confirmation_cue": clean(row.get("story_opportunity_confirmation_cue")),
                "story_opportunity_asset_cue": clean(row.get("story_opportunity_asset_cue")),
                "story_opportunity_readiness_note": short(clean(row.get("story_opportunity_readiness_note")), 220),
                "story_opportunity_second_source_id": clean(row.get("story_opportunity_second_source_id")),
                "story_opportunity_second_source_url": clean(row.get("story_opportunity_second_source_url")),
                "story_opportunity_second_source_lane": clean(row.get("story_opportunity_second_source_lane")),
                "story_opportunity_second_source_reason": short(clean(row.get("story_opportunity_second_source_reason")), 220),
                "story_opportunity_second_source_action": short(clean(row.get("story_opportunity_second_source_action")), 220),
                "promotion": first_present(row.get("promotion_recommendation"), default="monitor_only"),
                "promotion_priority": first_present(row.get("promotion_priority"), default="P4"),
                "promotion_target": clean(row.get("promotion_target")),
                "promotion_next_step": short(clean(row.get("promotion_next_step")), 180),
                "quality_score": clean(row.get("quality_score")),
                "freshness_label": clean(row.get("freshness_label")),
                "freshness_source": clean(row.get("freshness_source")),
                "freshness_score": clean(row.get("freshness_score")),
                "quality_reason": short(clean(row.get("quality_reason")), 190),
            }
        )
    return rows


def lead_promotion_recommendations() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_lead_promotion_recommendations.csv"):
        rows.append(
            {
                "rank": clean(row.get("promotion_rank")),
                "priority": first_present(row.get("promotion_priority"), default="P?"),
                "recommendation": first_present(row.get("promotion_recommendation"), default="review"),
                "title": first_present(row.get("story_opportunity_title"), row.get("title"), row.get("source_url"), default="Untitled lead"),
                "status": first_present(row.get("review_status"), default="review"),
                "lane": first_present(row.get("lane"), default="source_review"),
                "target": first_present(row.get("promotion_target"), default="morning_source_discovery_board.csv"),
                "detail": short(first_present(row.get("evidence_preview"), row.get("summary"), row.get("reason")), 260),
                "reason": short(clean(row.get("promotion_reason")), 190),
                "next_step": short(clean(row.get("promotion_next_step")), 190),
                "evidence_title": clean(row.get("evidence_title")),
                "evidence_published_at": clean(row.get("evidence_published_at")),
                "evidence_description": short(clean(row.get("evidence_description")), 260),
                "evidence_preview": short(clean(row.get("evidence_preview")), 260),
                "evidence_source": clean(row.get("evidence_source")),
                "story_opportunity_id": clean(row.get("story_opportunity_id")),
                "story_opportunity_title": clean(row.get("story_opportunity_title")),
                "story_opportunity_size": clean(row.get("story_opportunity_size")),
                "story_opportunity_sources": clean(row.get("story_opportunity_sources")),
                "story_opportunity_urls": clean(row.get("story_opportunity_urls")),
                "story_opportunity_reason": short(clean(row.get("story_opportunity_reason")), 220),
                "story_opportunity_angle": clean(row.get("story_opportunity_angle")),
                "story_opportunity_recommended_path": clean(row.get("story_opportunity_recommended_path")),
                "story_opportunity_path_reason": short(clean(row.get("story_opportunity_path_reason")), 220),
                "story_opportunity_confidence_tier": clean(row.get("story_opportunity_confidence_tier")),
                "story_opportunity_source_coverage": clean(row.get("story_opportunity_source_coverage")),
                "story_opportunity_confirmation_cue": clean(row.get("story_opportunity_confirmation_cue")),
                "story_opportunity_asset_cue": clean(row.get("story_opportunity_asset_cue")),
                "story_opportunity_readiness_note": short(clean(row.get("story_opportunity_readiness_note")), 220),
                "story_opportunity_second_source_id": clean(row.get("story_opportunity_second_source_id")),
                "story_opportunity_second_source_url": clean(row.get("story_opportunity_second_source_url")),
                "story_opportunity_second_source_lane": clean(row.get("story_opportunity_second_source_lane")),
                "story_opportunity_second_source_reason": short(clean(row.get("story_opportunity_second_source_reason")), 220),
                "story_opportunity_second_source_action": short(clean(row.get("story_opportunity_second_source_action")), 220),
                "quality_score": clean(row.get("quality_score")),
                "freshness_label": clean(row.get("freshness_label")),
                "freshness_source": clean(row.get("freshness_source")),
                "freshness_score": clean(row.get("freshness_score")),
                "quality_reason": short(clean(row.get("quality_reason")), 190),
                "artifact": "morning_lead_promotion_recommendations.csv",
            }
        )
    return rows


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
    source_board: List[Dict[str, str]],
    promotions: List[Dict[str, str]],
    coverage_map: List[Dict[str, str]],
    proposal_review: List[Dict[str, str]],
    source_proposal_packs: List[Dict[str, str]],
    artifacts: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    artifact_exists = {row["path"]: bool(row["exists"]) for row in artifacts}
    artifact_commands = {row["path"]: clean(row.get("run_command")) for row in artifacts}
    actions: List[Dict[str, str]] = []
    issues = operator.get("issues") or guard.get("issues") or []
    critical = [issue for issue in issues if clean(issue.get("severity")).lower() == "critical"] if isinstance(issues, list) else []

    def add_action(status: str, owner: str, title: str, detail: str, artifact: str, command: str = "") -> None:
        if not title or any(existing.get("title") == title for existing in actions):
            return
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": status,
                "owner": owner,
                "title": title,
                "detail": detail,
                "artifact": artifact,
                "command": command,
            }
        )

    if studio and not artifact_exists.get("graphics_upload_pack_status.csv"):
        command = artifact_commands.get("graphics_upload_pack_status.csv") or RUN_COMMANDS["graphics_upload_pack_status.csv"]
        add_action(
            "Build next",
            "Graphics",
            f"Build graphics pack for {studio[0]['name']}",
            (
                "This is the fastest unblocker: the publish guard has no ready graphics upload pack. "
                f"Use the top Studio bundle: {studio[0]['detail']}"
            ),
            "studio_bundle_queue.csv",
            command,
        )

    ready_candidates = [item for item in candidates if item.get("status") in {"Ready", "Graphics ready"}]
    if ready_candidates:
        item = ready_candidates[0]
        source_note = f"{item.get('source_count') or '0'} source(s)" if item.get("source_count") else "source count not reported"
        grade_note = f"Source grade: {item.get('source_grade') or 'not_scored'}"
        if item.get("source_score"):
            grade_note += f" ({item['source_score']})"
        add_action(
            "Editorial check",
            "Editor",
            f"Review top candidate: {item['headline']}",
            f"{item['detail']} Confirm facts, headline, and source posture before it becomes a manual post. {source_note}. {grade_note}.",
            item["artifact"],
        )

    if promotions:
        promo = promotions[0]
        freshness_note = f"{promo.get('freshness_label') or 'undated'}"
        if promo.get("freshness_source"):
            freshness_note += f" via {promo['freshness_source']}"
        evidence_note = f"{promo.get('detail')}. " if promo.get("detail") else ""
        opportunity_note = ""
        if as_int(promo.get("story_opportunity_size")) > 1:
            opportunity_note = (
                f"Grouped opportunity with {promo.get('story_opportunity_size')} related official/wire leads "
                f"from {promo.get('story_opportunity_sources')}. "
            )
        angle_note = ""
        if promo.get("story_opportunity_angle") or promo.get("story_opportunity_recommended_path"):
            angle_note = (
                f"Angle: {promo.get('story_opportunity_angle') or 'review'}; "
                f"path: {promo.get('story_opportunity_recommended_path') or promo.get('recommendation')}. "
            )
        readiness_bits = [
            promo.get("story_opportunity_confidence_tier"),
            promo.get("story_opportunity_source_coverage"),
            promo.get("story_opportunity_confirmation_cue"),
            promo.get("story_opportunity_asset_cue"),
        ]
        readiness_note = " / ".join(bit for bit in readiness_bits if bit)
        if readiness_note:
            readiness_note = f"Readiness: {readiness_note}. "
        if promo.get("story_opportunity_readiness_note"):
            readiness_note += f"{promo['story_opportunity_readiness_note']} "
        second_source_note = ""
        if promo.get("story_opportunity_second_source_id"):
            second_source_note = (
                f"Suggested second source: {promo['story_opportunity_second_source_id']} "
                f"({promo.get('story_opportunity_second_source_lane') or 'source_review'}). "
            )
        elif promo.get("story_opportunity_second_source_lane") == "already_covered":
            second_source_note = "Second-source status: already covered by distinct free sources. "
        add_action(
            "Lead promotion",
            "Editor",
            f"Promote source lead toward {promo['recommendation']}: {promo['title']}",
            f"{promo['priority']} / {promo['lane']} / quality {promo.get('quality_score') or 'n/a'} / {freshness_note}. {opportunity_note}{angle_note}{readiness_note}{second_source_note}{evidence_note}{promo.get('next_step') or promo.get('reason')}",
            promo["artifact"],
        )

    coverage_gaps = [row for row in coverage_map if row.get("status") == "gap"]
    proposal_holds = [row for row in proposal_review if row.get("review_status") == "hold"]
    if proposal_holds:
        held = proposal_holds[0]
        add_action(
            "Source hold",
            "Research",
            f"Resolve unsafe source proposal: {held.get('candidate_source_id') or 'missing source id'}",
            f"{held.get('safety_flags') or 'proposal issue'}; {held.get('issues') or 'Review before registry update.'}",
            "source_registry_proposal_review.md",
        )

    if coverage_gaps:
        gap = coverage_gaps[0]
        pack_rows = [
            row
            for row in source_proposal_packs
            if row.get("pack_key") == gap.get("key") or row.get("coverage_key") == gap.get("key")
        ]
        pack_count = len(pack_rows)
        pack_name = first_present(pack_rows[0].get("pack_name") if pack_rows else "", default=f"{gap['name']} source proposal pack")
        artifact = "source_proposal_packs.csv" if pack_count else "source_registry_intake_template.csv"
        pack_note = (
            f"Use the guided {pack_name} with {pack_count} free official/team/cross-check candidates; "
            if pack_count
            else "Use the intake template; "
        )
        add_action(
            "Source gap",
            "Research",
            f"Propose free source coverage for {gap['name']}",
            (
                f"{gap.get('gap') or 'coverage gap'}; "
                f"{gap.get('next_step') or 'Add a free official, team, wire, or reputable cross-check source manually.'} "
                f"{pack_note}proposals stay disabled until the registry is deliberately reviewed."
            ),
            artifact,
        )

    source_leads = [
        row
        for row in source_board
        if row.get("status") in {"editor_review", "needs_green_confirmation", "verify_with_primary"}
        and row.get("artifact") != "config/source_registry.json"
    ]
    if source_leads:
        lead = source_leads[0]
        add_action(
            "Source review",
            "Research",
            f"Review morning source lead: {lead['title']}",
            (
                f"{lead['lane']} / {lead['posture']}. "
                f"{lead.get('story_opportunity_reason') + ' ' if lead.get('story_opportunity_reason') else ''}"
                f"{'Angle: ' + lead.get('story_opportunity_angle') + '. ' if lead.get('story_opportunity_angle') else ''}"
                f"{'Readiness: ' + lead.get('story_opportunity_confidence_tier') + ' / ' + lead.get('story_opportunity_source_coverage') + ' / ' + lead.get('story_opportunity_confirmation_cue') + '. ' if lead.get('story_opportunity_confidence_tier') else ''}"
                f"{'Suggested second source: ' + lead.get('story_opportunity_second_source_id') + '. ' if lead.get('story_opportunity_second_source_id') else ''}"
                f"{lead.get('detail') or ''} {lead.get('next_action') or ''}"
            ).strip(),
            lead["artifact"],
        )
    elif source_board:
        lead = source_board[0]
        add_action(
            "Research scan",
            "Research",
            "Scan the morning source board",
            f"Start with {lead['source']}: {lead.get('detail') or lead.get('next_action')}",
            "morning_source_discovery_board.md",
        )

    if (candidates or studio) and (
        not artifact_exists.get("results_dashboard/index.html") or not artifact_exists.get("studio_dashboard/index.html")
    ):
        add_action(
            "Optional drill-down",
            "Operator",
            "Create Results and Studio drill-down dashboards",
            "Use this when you want the close-up Results/Studio pages behind the daily command center.",
            "results_desk_v5_report.md",
            RUN_COMMANDS["results_dashboard/index.html"],
        )

    if ready_candidates and not artifact_exists.get("multi_post_daily_board.md"):
        add_action(
            "Plan slots",
            "Operator",
            "Build the multi-post board after content is chosen",
            "Turns reviewed candidates and handoff/story artifacts into IG Feed, IG Stories, and Threads queues.",
            "news_fact_packets.csv",
            RUN_COMMANDS["multi_post_daily_board.md"],
        )

    handled_issue_codes = {"no_content_ready"} if studio or ready_candidates else set()
    for issue in critical:
        code = clean(issue.get("code"))
        if code in handled_issue_codes:
            continue
        detail = first_present(issue.get("detail"), issue.get("headline"), default="Open the operator status report and resolve the blocker.")
        title = "Create or refresh content inputs" if code == "no_content_ready" else first_present(code, default="Resolve blocking issue")
        command = ".\\hsd.cmd run -Mode full" if code == "no_content_ready" else ""
        add_action("Blocked", "Operator", title, detail, "operator_status.md", command)

    rendered_status = clean(guard.get("rendered_qa_status")).lower()
    if rendered_status in {"", "not_run"}:
        if artifact_exists.get("graphics_upload_pack_status.csv"):
            add_action(
                "QA pending",
                "Operator",
                "Run rendered-slide QA before posting",
                "Rendered graphics need source, crop, and copy checks before any manual post.",
                "rendered_slide_qa_report.md",
                artifact_commands.get("rendered_slide_qa_report.md"),
            )
        else:
            add_action(
                "Waiting",
                "Operator",
                "Run rendered-slide QA after graphics exist",
                "This is not runnable yet; first build or review the graphics pack.",
                "rendered_slide_qa_report.md",
            )

    if not yes(guard.get("publish_allowed")):
        add_action(
            "Manual only",
            "Publisher",
            "Keep publishing off",
            "Use artifacts for review and manual posting only. No auto-publishing path is enabled.",
            "publish_guard_report.md",
        )

    return trim_actions(actions)


def metric(label: str, value: Any, detail: str = "") -> Dict[str, str]:
    text = clean(value)
    return {"label": label, "value": text, "detail": clean(detail), "tone": status_tone(text)}


def source_registry_status(counts: Dict[str, Any]) -> str:
    total = as_int(counts.get("sources"))
    if not total:
        return "not_run"
    fail = as_int(counts.get("fail"))
    review = as_int(counts.get("review"))
    if fail:
        return "FAIL"
    if review:
        return "REVIEW"
    return "PASS"


def source_registry_detail(counts: Dict[str, Any]) -> str:
    total = as_int(counts.get("sources"))
    if not total:
        return "No source registry audit found."
    return (
        f"{as_int(counts.get('pass'))} pass, "
        f"{as_int(counts.get('review'))} review, "
        f"{as_int(counts.get('fail'))} fail across {total} sources."
    )


def decision_callout(
    overall: str,
    guard: Dict[str, Any],
    candidates: List[Dict[str, str]],
    studio: List[Dict[str, str]],
    artifacts: List[Dict[str, Any]],
    source_registry_counts: Dict[str, Any],
) -> str:
    artifact_exists = {row["path"]: bool(row["exists"]) for row in artifacts}
    source_status = source_registry_status(source_registry_counts)
    if as_int(source_registry_counts.get("fail")):
        return "Hold: source registry has failing sources. Review source health before choosing a post."
    if not artifact_exists.get("graphics_upload_pack_status.csv") and studio:
        return f"{overall}: source registry is {source_status}, but no graphics upload pack is ready. Build the top Studio pack before handoff or posting."
    if candidates and not yes(guard.get("publish_allowed")):
        return f"{overall}: content candidates exist, but publishing remains artifact-only and manual review is still required."
    if yes(guard.get("graphics_handoff_allowed")):
        return "Graphics handoff is allowed for review, but publishing stays manual until rendered QA and operator approval."
    return "Manual review required before any post leaves the system."


def trim_actions(actions: List[Dict[str, str]], limit: int = 7) -> List[Dict[str, str]]:
    trimmed = list(actions)
    for status in ["Waiting", "Plan slots", "Optional drill-down"]:
        if len(trimmed) <= limit:
            break
        for index, action in enumerate(trimmed):
            if action.get("status") == status:
                del trimmed[index]
                break
    if len(trimmed) > limit:
        manual = [action for action in trimmed if action.get("status") == "Manual only"]
        trimmed = trimmed[:limit]
        if manual and all(action.get("status") != "Manual only" for action in trimmed):
            trimmed[-1] = manual[0]
    for index, action in enumerate(trimmed, 1):
        action["rank"] = str(index)
    return trimmed


def build_payload() -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    operator = read_json("operator_status.json")
    guard = read_json("publish_guard_report.json")
    manifest = read_json("results_desk_v5_manifest.json")
    source_registry = read_json("source_registry_audit.json")
    ops = read_json("bebe_daily_ops_status.json")
    handoff = read_json("assignment_handoff_publisher_manifest.json")
    render = read_json("rendered_slide_qa_manifest.json")
    artifacts = artifact_entries()
    candidates = content_candidates()
    news_packets = read_csv("news_fact_packets.csv")
    source_board = source_discovery_board()
    promotions = lead_promotion_recommendations()
    studio = studio_queue()
    schedule = schedule_rows()
    coverage_map = source_coverage_map(source_registry)
    source_intake_rows = read_csv("source_registry_intake_template.csv")
    source_proposal_review = read_csv("source_registry_proposal_review.csv")
    source_proposal_packs = read_csv("source_proposal_packs.csv")
    wnba_source_proposal_pack = read_csv("wnba_source_proposal_pack.csv")
    nwsl_source_proposal_pack = read_csv("nwsl_source_proposal_pack.csv")
    lpga_source_proposal_pack = read_csv("lpga_source_proposal_pack.csv")
    pwhl_source_proposal_pack = read_csv("pwhl_source_proposal_pack.csv")
    if not source_proposal_packs:
        source_proposal_packs = (
            wnba_source_proposal_pack
            + nwsl_source_proposal_pack
            + lpga_source_proposal_pack
            + pwhl_source_proposal_pack
        )
    counts = manifest.get("counts", {}) if isinstance(manifest.get("counts"), dict) else {}
    source_registry_counts = source_registry.get("counts", {}) if isinstance(source_registry.get("counts"), dict) else {}
    handoff_counts = handoff.get("counts", {}) if isinstance(handoff.get("counts"), dict) else {}
    render_counts = render.get("counts", {}) if isinstance(render.get("counts"), dict) else {}

    decision = {
        "overall": first_present(operator.get("overall"), default="NO-GO"),
        "publish_allowed": bool(guard.get("publish_allowed")),
        "graphics_handoff_allowed": bool(guard.get("graphics_handoff_allowed")),
        "publish_mode": first_present(guard.get("publish_mode"), default="artifact_only"),
        "automation": "OFF / artifact-only",
        "free_source_mode": "Free public sources only",
    }
    decision["callout"] = decision_callout(decision["overall"], guard, candidates, studio, artifacts, source_registry_counts)
    story_opportunity_ids = {row.get("story_opportunity_id") for row in source_board if row.get("story_opportunity_id")}
    grouped_story_opportunities = {
        row.get("story_opportunity_id")
        for row in source_board
        if row.get("story_opportunity_id") and as_int(row.get("story_opportunity_size")) > 1
    }
    opportunity_representatives = {
        row.get("story_opportunity_id"): row
        for row in source_board
        if row.get("story_opportunity_id") and row.get("story_opportunity_id") not in {""}
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
        metric("News packets", len(news_packets)),
        metric("Publish-grade packets", sum(1 for row in news_packets if packet_source_confidence(row)["source_grade"] == "publish_grade")),
        metric("Discovery-only packets", sum(1 for row in news_packets if packet_source_confidence(row)["source_grade"] == "discovery_only")),
        metric("Morning source rows", len(source_board)),
        metric("Story opportunities", len(story_opportunity_ids)),
        metric("Grouped opportunities", len(grouped_story_opportunities)),
        metric(
            "Publish-grade opportunities",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_confidence_tier") == "publish_grade_candidate"),
        ),
        metric(
            "Needs source check",
            sum(
                1
                for row in opportunity_representatives.values()
                if row.get("story_opportunity_confirmation_cue") in {"needs_second_source", "needs_official_confirmation"}
            ),
        ),
        metric(
            "Second-source suggestions",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_second_source_id")),
        ),
        metric("Source coverage gaps", sum(1 for row in coverage_map if row.get("status") == "gap")),
        metric("Source coverage watch", sum(1 for row in coverage_map if row.get("status") == "watch")),
        metric("Source intake proposals", len(source_intake_rows)),
        metric("Source proposal holds", sum(1 for row in source_proposal_review if row.get("review_status") == "hold")),
        metric("Source proposals ready", sum(1 for row in source_proposal_review if row.get("review_status") == "ready_for_registry_review")),
        metric("Guided source pack rows", len(source_proposal_packs)),
        metric("WNBA proposal pack", len(wnba_source_proposal_pack)),
        metric("NWSL proposal pack", len(nwsl_source_proposal_pack)),
        metric("LPGA proposal pack", len(lpga_source_proposal_pack)),
        metric("PWHL proposal pack", len(pwhl_source_proposal_pack)),
        metric(
            "Studio asset checks",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_asset_cue") == "asset_check_required_before_studio"),
        ),
        metric("Gray/social leads", sum(1 for row in source_board if row.get("lane") in {"gray_area_review", "social_discovery"})),
        metric("Lead promotions", len(promotions)),
        metric("High-quality leads", sum(1 for row in promotions if as_int(row.get("quality_score")) >= 70)),
        metric("Fresh leads", sum(1 for row in promotions if row.get("freshness_label") in {"today", "last_48_hours"})),
        metric("News/Manual/Studio", "/".join([
            str(sum(1 for row in promotions if row.get("recommendation") == "news_packet")),
            str(sum(1 for row in promotions if row.get("recommendation") == "manual_story_candidate")),
            str(sum(1 for row in promotions if row.get("recommendation") == "studio_brief")),
        ])),
        metric("Studio bundles", len(studio)),
        metric("Handoff packets", handoff_counts.get("handoff_packets") or "0"),
        metric("Source registry", source_registry_status(source_registry_counts), source_registry_detail(source_registry_counts)),
        metric("Day type", first_present(ops.get("day_type"), default="normal_day")),
    ]
    next_actions = build_next_actions(
        operator,
        guard,
        candidates,
        studio,
        source_board,
        promotions,
        coverage_map,
        source_proposal_review,
        source_proposal_packs,
        artifacts,
    )
    if as_int(source_registry_counts.get("fail")) or as_int(source_registry_counts.get("review")):
        next_actions.insert(
            0,
            {
                "rank": "1",
                "status": "Source review",
                "owner": "Operator",
                "title": "Review source registry audit",
                "detail": source_registry_detail(source_registry_counts),
                "artifact": "source_registry_audit.md",
            },
        )
        next_actions = trim_actions(next_actions)
    source_rows = source_health(manifest)
    source_state = source_registry_detail(source_registry_counts) if source_registry_counts else f"{sum(1 for row in source_rows if clean(row.get('ok')).lower() == 'yes')} source check(s) OK"
    briefing = {
        "best_candidate": candidates[0]["headline"] if candidates else "No content candidate found",
        "studio_lane": studio[0]["name"] if studio else "No studio bundle found",
        "source_state": source_state,
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
        "source_discovery_board": source_board,
        "lead_promotion_recommendations": promotions,
        "source_coverage_map": coverage_map,
        "source_registry_intake_template": source_intake_rows,
        "source_registry_proposal_review": source_proposal_review,
        "source_proposal_packs": source_proposal_packs,
        "wnba_source_proposal_pack": wnba_source_proposal_pack,
        "nwsl_source_proposal_pack": nwsl_source_proposal_pack,
        "lpga_source_proposal_pack": lpga_source_proposal_pack,
        "pwhl_source_proposal_pack": pwhl_source_proposal_pack,
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


def command_hint(command: str) -> str:
    command = clean(command)
    if not command:
        return ""
    return f'<div class="command-line"><span>Run next</span><code>{html.escape(command)}</code></div>'


def artifact_tool(row: Dict[str, Any]) -> str:
    if row.get("exists"):
        return open_link(row["path"])
    command = clean(row.get("run_command"))
    if command:
        return f'<code>{html.escape(command)}</code>'
    return '<span class="muted">Missing</span>'


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
                {command_hint(action.get('command', ''))}
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
                <small>{html.escape(row.get('source_count') or '0')} source(s) / {html.escape(row.get('source_grade') or 'not_scored')} {f"({html.escape(row.get('source_score') or '')})" if row.get('source_score') else ""}</small>
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


def render_source_discovery(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        detail = html.escape(row.get("detail") or "")
        next_action = html.escape(row.get("next_action") or "")
        detail_html = f"<p>{detail}</p>" if detail else ""
        next_html = f"<p>Next: {next_action}</p>" if next_action and next_action != detail else ""
        opportunity_note = ""
        if row.get("story_opportunity_id"):
            opportunity_note = (
                f" / opportunity: {html.escape(row.get('story_opportunity_size') or '1')} source(s)"
                f" from {html.escape(row.get('story_opportunity_sources') or row.get('source') or '')}"
            )
        angle_note = ""
        if row.get("story_opportunity_angle") or row.get("story_opportunity_recommended_path"):
            angle_note = (
                f" / angle: {html.escape(row.get('story_opportunity_angle') or 'review')}"
                f" / path: {html.escape(row.get('story_opportunity_recommended_path') or row.get('promotion') or 'review')}"
            )
        readiness_note = ""
        if row.get("story_opportunity_confidence_tier") or row.get("story_opportunity_source_coverage"):
            readiness_note = (
                f" / confidence: {html.escape(row.get('story_opportunity_confidence_tier') or 'review')}"
                f" / coverage: {html.escape(row.get('story_opportunity_source_coverage') or 'n/a')}"
                f" / cue: {html.escape(row.get('story_opportunity_confirmation_cue') or 'n/a')}"
                f" / assets: {html.escape(row.get('story_opportunity_asset_cue') or 'n/a')}"
            )
        second_source_note = ""
        if row.get("story_opportunity_second_source_id") or row.get("story_opportunity_second_source_lane"):
            second_source_note = (
                f" / second source: {html.escape(row.get('story_opportunity_second_source_id') or row.get('story_opportunity_second_source_lane') or 'n/a')}"
            )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['lane'])} {pill(row['status'])} {pill(row['posture'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('source') or '')} / {html.escape(row.get('band') or '')} / promote: {html.escape(row.get('promotion') or 'monitor_only')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No morning source rows found.</p>'


def render_lead_promotions(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        detail = html.escape(row.get("detail") or "")
        next_step = html.escape(row.get("next_step") or row.get("reason") or "")
        detail_html = f"<p>{detail}</p>" if detail else ""
        next_html = f"<p>Next: {next_step}</p>" if next_step and next_step != detail else ""
        opportunity_note = ""
        if row.get("story_opportunity_id"):
            opportunity_note = (
                f" / opportunity: {html.escape(row.get('story_opportunity_size') or '1')} source(s)"
                f" from {html.escape(row.get('story_opportunity_sources') or '')}"
            )
        angle_note = ""
        if row.get("story_opportunity_angle") or row.get("story_opportunity_recommended_path"):
            angle_note = (
                f" / angle: {html.escape(row.get('story_opportunity_angle') or 'review')}"
                f" / path: {html.escape(row.get('story_opportunity_recommended_path') or row.get('recommendation') or 'review')}"
            )
        readiness_note = ""
        if row.get("story_opportunity_confidence_tier") or row.get("story_opportunity_source_coverage"):
            readiness_note = (
                f" / confidence: {html.escape(row.get('story_opportunity_confidence_tier') or 'review')}"
                f" / coverage: {html.escape(row.get('story_opportunity_source_coverage') or 'n/a')}"
                f" / cue: {html.escape(row.get('story_opportunity_confirmation_cue') or 'n/a')}"
                f" / assets: {html.escape(row.get('story_opportunity_asset_cue') or 'n/a')}"
            )
        second_source_note = ""
        if row.get("story_opportunity_second_source_id") or row.get("story_opportunity_second_source_lane"):
            second_source_note = (
                f" / second source: {html.escape(row.get('story_opportunity_second_source_id') or row.get('story_opportunity_second_source_lane') or 'n/a')}"
            )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['priority'])} {pill(row['recommendation'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('lane') or '')} / target: {html.escape(row.get('target') or '')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No lead promotion recommendations found.</p>'


def render_source_coverage(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['name'])}</td>
              <td>{pill(row['status'])}</td>
              <td>{html.escape(row.get('official') or '-')}</td>
              <td>{html.escape(row.get('team') or '-')}</td>
              <td>{html.escape(row.get('wire') or '-')}</td>
              <td>{html.escape(row.get('cross_check') or '-')}</td>
              <td>{html.escape(row.get('gap') or 'none')}</td>
              <td>{html.escape(row.get('next_step') or '')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="8" class="empty">No source coverage map found.</td></tr>'


def render_source_intake(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('needed_source_type')))}</td>
              <td>{html.escape(clean(row.get('coverage_gap')))}</td>
              <td>{html.escape(clean(row.get('source_type')))}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')))}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="7" class="empty">No source intake proposals found.</td></tr>'


def render_source_proposal_packs(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('candidate_group')))}</td>
              <td>{html.escape(clean(row.get('suggested_priority')))}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_source_name')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
              <td>{html.escape(clean(row.get('registry_presence')) or 'not_checked')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No guided source proposal packs found.</td></tr>'


def render_source_proposal_review(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{pill(clean(row.get('review_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('safety_flags')) or 'none')}</td>
              <td>{html.escape(clean(row.get('issues')) or 'none')}</td>
              <td>{html.escape(clean(row.get('recommendation')))}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No manual source proposal rows found.</td></tr>'


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
        search_text = " ".join([row["group"], row["title"], row["path"], clean(row.get("run_command")), clean(row.get("status_detail"))])
        body.append(
            f"""
            <tr data-artifact-row data-group="{html.escape(row['group'].lower())}" data-search="{html.escape(search_text.lower())}">
              <td>{html.escape(row['group'])}</td>
              <td>{html.escape(row['title'])}</td>
              <td><code>{html.escape(row['path'])}</code></td>
              <td>{pill('found' if row['exists'] else 'missing')}</td>
              <td>{html.escape(clean(row.get('status_detail')))}</td>
              <td>{artifact_tool(row)}</td>
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
    .command-line {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:9px; color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; }}
    .command-line code {{ text-transform:none; font-weight:700; overflow-wrap:anywhere; }}
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
      <button class="tab-button" type="button" data-tab-target="sources" aria-selected="false">Sources</button>
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

    <section id="sources" class="tab-panel">
      <div class="two-col">
        <div class="panel">
          <h2>Lead promotion recommendations</h2>
          <div class="content-list">{render_lead_promotions(payload['lead_promotion_recommendations'])}</div>
        </div>
        <div class="panel">
          <h2>Morning source discovery</h2>
          <div class="content-list">{render_source_discovery(payload['source_discovery_board'])}</div>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source coverage map</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>League</th><th>Status</th><th>Official</th><th>Team</th><th>Wire</th><th>Cross-check</th><th>Gap</th><th>Next step</th></tr></thead>
            <tbody>{render_source_coverage(payload['source_coverage_map'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry intake template</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>League</th><th>Need</th><th>Gap</th><th>Type</th><th>Enabled</th><th>Action</th><th>Candidate URL</th></tr></thead>
            <tbody>{render_source_intake(payload['source_registry_intake_template'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Guided source proposal packs</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pack</th><th>Group</th><th>Priority</th><th>Source ID</th><th>Name</th><th>URL</th><th>Enabled</th><th>Action</th><th>Registry</th></tr></thead>
            <tbody>{render_source_proposal_packs(payload['source_proposal_packs'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal review</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Candidate</th><th>URL</th><th>Status</th><th>Flags</th><th>Issues</th><th>Recommendation</th></tr></thead>
            <tbody>{render_source_proposal_review(payload['source_registry_proposal_review'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source health</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Source</th><th>League</th><th>Date</th><th>OK</th><th>Events</th><th>Notes</th></tr></thead>
            <tbody>{render_sources(payload['source_health'])}</tbody>
          </table>
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
            <thead><tr><th>Group</th><th>Artifact</th><th>Path</th><th>Status</th><th>Next step</th><th>Open</th></tr></thead>
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
        (
            f"{action['rank']}. [{action['status']}] {action['title']} - {action['detail']} "
            f"({action['artifact']})"
            f"{' Run: `' + action['command'] + '`.' if action.get('command') else ''}"
        )
        for action in payload["next_actions"]
    )
    lines += ["", "## Content candidates", ""]
    lines.extend(
        f"- {item['type']} | {item['priority']} | {item['headline']} | {item['status']} | source: {item.get('source_grade') or 'not_scored'}"
        for item in payload["content_candidates"]
    )
    lines += ["", "## Lead promotion recommendations", ""]
    lines.extend(
        f"- {item['rank']} | {item['priority']} | {item['recommendation']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or '1'} source(s) | angle: {item.get('story_opportunity_angle') or 'review'} | path: {item.get('story_opportunity_recommended_path') or item.get('recommendation') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'review'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | target: {item['target']} | {item.get('next_step') or item.get('reason')}"
        for item in payload["lead_promotion_recommendations"]
    )
    lines += ["", "## Morning source discovery", ""]
    lines.extend(
        f"- {item['rank']} | {item['lane']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or 'n/a'} | angle: {item.get('story_opportunity_angle') or 'n/a'} | path: {item.get('story_opportunity_recommended_path') or item.get('promotion') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'n/a'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | {item['status']} | {item['posture']} | {item.get('next_action') or item.get('detail')}"
        for item in payload["source_discovery_board"]
    )
    lines += ["", "## Source coverage map", ""]
    lines.extend(
        f"- {item['name']} | {item['status']} | official: {item.get('official') or 'none'} | team: {item.get('team') or 'none'} | wire: {item.get('wire') or 'none'} | cross-check: {item.get('cross_check') or 'none'} | gap: {item.get('gap') or 'none'} | {item.get('next_step') or ''}"
        for item in payload["source_coverage_map"]
    )
    lines += ["", "## Source registry intake template", ""]
    lines.extend(
        f"- {clean(item.get('display_name'))} | {clean(item.get('needed_source_type'))} | {clean(item.get('coverage_gap'))} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | action: {clean(item.get('registry_action'))}"
        for item in payload["source_registry_intake_template"]
    )
    lines += ["", "## Guided source proposal packs", ""]
    lines.extend(
        f"- {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('suggested_priority'))} | {clean(item.get('candidate_group'))} | {clean(item.get('candidate_source_id'))} | {clean(item.get('candidate_url'))} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | action: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'} | registry: {clean(item.get('registry_presence')) or 'not_checked'}"
        for item in payload["source_proposal_packs"]
    )
    lines += ["", "## Source proposal review", ""]
    lines.extend(
        f"- {clean(item.get('candidate_source_id')) or 'missing_id'} | {clean(item.get('review_status')) or 'review'} | flags: {clean(item.get('safety_flags')) or 'none'} | {clean(item.get('issues')) or 'none'}"
        for item in payload["source_registry_proposal_review"]
    )
    lines += ["", "## Studio queue", ""]
    lines.extend(f"- {item['priority']} | {item['name']} | {item['status']} | {item['detail']}" for item in payload["studio_queue"])
    lines += ["", "## Artifacts", ""]
    lines.extend(
        (
            f"- [{'found' if item['exists'] else 'missing'}] `{item['path']}` - {item['title']}"
            f"{' - ' + item['status_detail'] if item.get('status_detail') else ''}"
        )
        for item in payload["artifacts"]
    )
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
