from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text

VERSION = "hsd-operator-command-center-v3.36.0-manual-operator-decision-helper"
OUT_HTML = output_path("operator_command_center.html")
OUT_MD = output_path("operator_command_center.md")
OUT_JSON = output_path("operator_command_center.json")
OUT_RENDER_PREP_MD = output_path("render_prep_packets.md")
OUT_RENDER_PREP_CSV = output_path("render_prep_packets.csv")
OUT_RENDER_PREP_JSON = output_path("render_prep_packets.json")
OUT_RENDER_HANDOFF_DIR = output_path("render_handoff_top_packet")
OUT_RENDER_HANDOFF_README = OUT_RENDER_HANDOFF_DIR / "README.md"
OUT_RENDER_HANDOFF_COPY = OUT_RENDER_HANDOFF_DIR / "copy_sheet.md"
OUT_RENDER_HANDOFF_COPY_CSV = OUT_RENDER_HANDOFF_DIR / "copy_sheet.csv"
OUT_RENDER_HANDOFF_ASSETS = OUT_RENDER_HANDOFF_DIR / "asset_checklist.md"
OUT_RENDER_HANDOFF_ASSETS_CSV = OUT_RENDER_HANDOFF_DIR / "asset_checklist.csv"
OUT_RENDER_HANDOFF_SOURCE_PROOF = OUT_RENDER_HANDOFF_DIR / "source_proof.md"
OUT_RENDER_HANDOFF_PROMPT = OUT_RENDER_HANDOFF_DIR / "manual_renderer_prompt.md"
OUT_RENDER_HANDOFF_MANIFEST = OUT_RENDER_HANDOFF_DIR / "handoff_manifest.json"

RENDER_PREP_FIELDS = [
    "packet_id",
    "packet_status",
    "render_rank",
    "render_readiness_score",
    "render_readiness_band",
    "title",
    "recommended_path",
    "template_fit",
    "template_shape",
    "renderer_family",
    "copy_headline",
    "copy_dek",
    "copy_context",
    "source_artifact",
    "source_cue",
    "source_detail",
    "asset_requirement",
    "asset_cue",
    "format_cue",
    "manual_path",
    "manual_renderer_steps",
    "approval_gate",
    "auto_render_status",
    "publish_policy",
    "paid_api_policy",
    "blockers",
]

ARTIFACTS = [
    ("Decision", "Operator status", "operator_status.md"),
    ("Decision", "Publish guard", "publish_guard_report.md"),
    ("Decision", "BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("Decision", "BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("Decision", "Render prep packets", "render_prep_packets.md"),
    ("Decision", "Render prep packet data", "render_prep_packets.csv"),
    ("Decision", "Render prep packet manifest", "render_prep_packets.json"),
    ("Decision", "Top render handoff", "render_handoff_top_packet/README.md"),
    ("Decision", "Top render copy sheet", "render_handoff_top_packet/copy_sheet.md"),
    ("Decision", "Top render asset checklist", "render_handoff_top_packet/asset_checklist.md"),
    ("Decision", "Top render source proof", "render_handoff_top_packet/source_proof.md"),
    ("Decision", "Top render manual prompt", "render_handoff_top_packet/manual_renderer_prompt.md"),
    ("Decision", "Top render draft preview", "render_handoff_top_packet/draft_preview.png"),
    ("Decision", "Top render handoff manifest", "render_handoff_top_packet/handoff_manifest.json"),
    ("Decision", "Manual review renderer report", "manual_review_renderer_report.md"),
    ("Decision", "Manual review renderer manifest", "manual_review_renderer_manifest.json"),
    ("Decision", "Manual visual QA report", "manual_visual_qa_report.md"),
    ("Decision", "Manual visual QA manifest", "manual_visual_qa_manifest.json"),
    ("Decision", "Manual visual QA checklist", "manual_visual_qa_checklist.csv"),
    ("Decision", "Manual visual QA approval intake", "manual_visual_qa_approval_intake.md"),
    ("Decision", "Manual visual QA approval intake data", "manual_visual_qa_approval_intake.csv"),
    ("Decision", "Manual visual QA approval intake manifest", "manual_visual_qa_approval_intake.json"),
    ("Decision", "Manual visual QA operator decision draft", "manual_visual_qa_operator_decision_draft.md"),
    ("Decision", "Manual visual QA operator decision draft data", "manual_visual_qa_operator_decision_draft.csv"),
    ("Decision", "Manual visual QA operator decision draft manifest", "manual_visual_qa_operator_decision_draft.json"),
    ("Decision", "Manual post-approval render staging", "manual_post_approval_render_staging.md"),
    ("Decision", "Manual post-approval render staging data", "manual_post_approval_render_staging.csv"),
    ("Decision", "Manual post-approval render staging manifest", "manual_post_approval_render_staging.json"),
    ("Sources", "Source registry audit", "source_registry_audit.md"),
    ("Sources", "Source registry audit data", "source_registry_audit.json"),
    ("Sources", "Source registry audit table", "source_registry_audit.csv"),
    ("Sources", "Source coverage map", "source_coverage_map.csv"),
    ("Sources", "Source registry intake guide", "source_registry_intake_template.md"),
    ("Sources", "Source registry intake template", "source_registry_intake_template.csv"),
    ("Sources", "Source proposal review", "source_registry_proposal_review.md"),
    ("Sources", "Source proposal review data", "source_registry_proposal_review.csv"),
    ("Sources", "Source proposal draft", "source_registry_proposal_draft.md"),
    ("Sources", "Source proposal draft data", "source_registry_proposal_draft.csv"),
    ("Sources", "Source proposal promotion checklist", "source_registry_proposal_promotion_checklist.md"),
    ("Sources", "Source proposal promotion checklist data", "source_registry_proposal_promotion_checklist.csv"),
    ("Sources", "Source registry update worksheet", "source_registry_update_worksheet.md"),
    ("Sources", "Source registry update worksheet data", "source_registry_update_worksheet.csv"),
    ("Sources", "Source registry diff review", "source_registry_diff_review.md"),
    ("Sources", "Source registry diff review data", "source_registry_diff_review.csv"),
    ("Sources", "Source registry same-domain resolution", "source_registry_same_domain_resolution.md"),
    ("Sources", "Source registry same-domain resolution data", "source_registry_same_domain_resolution.csv"),
    ("Sources", "Source verification log", "source_registry_verification_log.md"),
    ("Sources", "Source verification log data", "source_registry_verification_log.csv"),
    ("Sources", "Source registry approval packet", "source_registry_approval_packet.md"),
    ("Sources", "Source registry approval packet data", "source_registry_approval_packet.csv"),
    ("Sources", "Source registry patch preview", "source_registry_patch_preview.md"),
    ("Sources", "Source registry patch preview data", "source_registry_patch_preview.csv"),
    ("Sources", "Source registry post-edit validation", "source_registry_post_edit_validation.md"),
    ("Sources", "Source registry post-edit validation data", "source_registry_post_edit_validation.csv"),
    ("Sources", "Trusted registry operator playbook", "trusted_registry_operator_playbook.md"),
    ("Sources", "Guided source pack readiness", "source_proposal_pack_readiness.md"),
    ("Sources", "Guided source pack readiness data", "source_proposal_pack_readiness.csv"),
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
    "render_handoff_top_packet/draft_preview.png": ".\\hsd.cmd run -Mode render",
    "manual_review_renderer_report.md": ".\\hsd.cmd run -Mode render",
    "manual_review_renderer_manifest.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_report.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_manifest.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_checklist.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.json": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.md": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.csv": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.json": ".\\hsd.cmd run -Mode render",
    "source_registry_intake_template.md": ".\\hsd.cmd run -Mode review",
    "source_registry_intake_template.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_draft.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_draft.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_promotion_checklist.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_promotion_checklist.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_update_worksheet.md": ".\\hsd.cmd run -Mode review",
    "source_registry_update_worksheet.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_diff_review.md": ".\\hsd.cmd run -Mode review",
    "source_registry_diff_review.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_same_domain_resolution.md": ".\\hsd.cmd run -Mode review",
    "source_registry_same_domain_resolution.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_verification_log.md": ".\\hsd.cmd run -Mode review",
    "source_registry_verification_log.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_approval_packet.md": ".\\hsd.cmd run -Mode review",
    "source_registry_approval_packet.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_patch_preview.md": ".\\hsd.cmd run -Mode review",
    "source_registry_patch_preview.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_post_edit_validation.md": ".\\hsd.cmd run -Mode review",
    "source_registry_post_edit_validation.csv": ".\\hsd.cmd run -Mode review",
    "trusted_registry_operator_playbook.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_pack_readiness.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_pack_readiness.csv": ".\\hsd.cmd run -Mode review",
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


def split_tokens(value: Any) -> List[str]:
    text = clean(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[;,|]", text) if part.strip()]


def clamp_score(score: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, score))


def render_readiness_band(score: int, blockers: List[str]) -> str:
    if blockers:
        if any("source" in blocker or "confirmation" in blocker for blocker in blockers):
            return "hold_for_source_confirmation"
        if any("asset" in blocker for blocker in blockers):
            return "hold_for_asset_review"
        return "hold_before_render"
    if score >= 85:
        return "render_ready_review"
    if score >= 65:
        return "render_prep_candidate"
    if score >= 45:
        return "needs_operator_review"
    return "hold_before_render"


def score_render_readiness(
    row: Dict[str, str],
    *,
    item_type: str,
    headline: str,
    artifact: str,
    artifact_exists: Dict[str, bool] | None = None,
) -> Dict[str, str]:
    artifact_exists = artifact_exists or {}
    score = 0
    blockers: List[str] = []

    source_grade = clean(first_present(row.get("source_grade"), row.get("story_opportunity_confidence_tier")))
    source_coverage = clean(row.get("story_opportunity_source_coverage"))
    confirmation = clean(row.get("story_opportunity_confirmation_cue"))
    source_count = as_int(row.get("source_count")) or len(split_tokens(row.get("story_opportunity_sources")))
    second_source = clean(first_present(row.get("story_opportunity_second_source_id"), row.get("story_opportunity_second_source_lane")))

    if source_grade in {"publish_grade", "publish_grade_candidate"}:
        score += 35
        source_cue = "source_confidence_ready"
    elif source_grade in {"review_before_publish", "needs_official_confirmation"}:
        score += 18
        source_cue = "source_confirmation_needed"
    elif source_grade in {"discovery_only", "discovery_source_only"} or source_coverage == "discovery_source_only":
        score += 8
        source_cue = "discovery_only_source"
    elif source_count >= 2:
        score += 22
        source_cue = "source_depth_present"
    else:
        score += 6
        source_cue = "source_confidence_missing"

    if source_count >= 2:
        score += 6
    if second_source and second_source != "n/a":
        score += 4
    if confirmation in {"needs_second_source", "needs_official_confirmation"}:
        blockers.append("source confirmation required")
        score = min(score, 24)
    elif confirmation in {"already_covered", "official_confirmed", "source_confidence_ready"}:
        score += 5

    asset_cue = clean(row.get("story_opportunity_asset_cue"))
    status = clean(row.get("status")).lower()
    if asset_cue in {"asset_not_required_for_news_packet", "asset_ready", "assets_ready"}:
        score += 25
        asset_readiness = asset_cue
    elif asset_cue == "asset_check_required_before_studio":
        score += 8
        blockers.append("asset review required")
        asset_readiness = asset_cue
    elif status in {"ready", "graphics ready", "allow"}:
        score += 22
        asset_readiness = "artifact_assets_ready_or_not_required"
    elif item_type.lower().startswith("news"):
        score += 20
        asset_readiness = "asset_not_required_for_news_packet"
    else:
        score += 10
        asset_readiness = "asset_readiness_review"

    recommended_path = clean(first_present(row.get("story_opportunity_recommended_path"), row.get("recommendation"), item_type))
    path_token = re.sub(r"[^a-z0-9]+", "_", recommended_path.lower()).strip("_")
    if recommended_path in {"news_packet", "manual_story_candidate", "studio_brief", "News packet", "Final result"}:
        score += 20
        format_fit = f"{path_token}_format_fit"
    elif recommended_path:
        score += 12
        format_fit = f"{path_token}_needs_format_review"
    else:
        score += 5
        format_fit = "format_path_missing"

    manual_path_exists = bool(artifact and artifact_exists.get(artifact, input_path(artifact).exists()))
    if manual_path_exists:
        score += 20
        manual_path = f"manual_review_artifact_ready:{artifact}"
    elif artifact:
        score += 8
        manual_path = f"create_manual_artifact:{artifact}"
        blockers.append("manual render path artifact missing")
    else:
        manual_path = "manual_render_path_missing"
        blockers.append("manual render path missing")

    if "source confirmation required" in blockers:
        score = min(score, 55)
    if "asset review required" in blockers:
        score = min(score, 70)
    if "manual render path artifact missing" in blockers or "manual render path missing" in blockers:
        score = min(score, 60)
    score = clamp_score(score)
    band = render_readiness_band(score, blockers)
    next_step = "Open the artifact, confirm facts visually, then prepare a manual render; publishing stays off."
    if "source confirmation required" in blockers:
        next_step = "Verify the second official, wire, or primary source before News, Studio, or render work."
    elif "asset review required" in blockers:
        next_step = "Confirm the asset path, crop, and identity before render prep."
    elif "manual render path artifact missing" in blockers:
        next_step = "Create the missing manual artifact before render prep."
    elif band == "render_prep_candidate":
        next_step = "Review the remaining cues, then move this into manual render prep."

    return {
        "render_readiness_score": str(score),
        "render_readiness_band": band,
        "render_readiness_source_cue": source_cue,
        "render_readiness_asset_cue": asset_readiness,
        "render_readiness_format_cue": format_fit,
        "render_readiness_manual_path": manual_path,
        "render_readiness_blockers": "; ".join(blockers) if blockers else "none",
        "render_readiness_next_step": next_step,
    }


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
        candidate = {
            "type": "News packet",
            "priority": first_present(row.get("urgency"), row.get("publish_recommendation"), default="Review"),
            "headline": first_present(row.get("headline"), row.get("dek")),
            "status": "Ready" if clean(row.get("production_ready")).lower() == "yes" else "Review",
            "detail": short(first_present(row.get("caption_hard_fact"), row.get("brief_120w"), row.get("dek")), 210),
            "artifact": "news_fact_packets.csv",
            "source_count": clean(row.get("source_count")),
            **source_confidence,
        }
        candidate.update(
            score_render_readiness(
                candidate,
                item_type="News packet",
                headline=candidate["headline"],
                artifact=candidate["artifact"],
            )
        )
        candidates.append(
            candidate
        )
    for row in read_csv("today_final_results.csv")[:6]:
        candidate = {
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
        candidate.update(
            score_render_readiness(
                candidate,
                item_type="Final result",
                headline=candidate["headline"],
                artifact=candidate["artifact"],
            )
        )
        candidates.append(
            candidate
        )
    return candidates


def source_discovery_board() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_source_discovery_board.csv"):
        item = {
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
        item.update(
            score_render_readiness(
                item,
                item_type="Story opportunity",
                headline=item["title"],
                artifact=item["artifact"],
            )
        )
        rows.append(item)
    return rows


def lead_promotion_recommendations() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_lead_promotion_recommendations.csv"):
        item = {
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
        item.update(
            score_render_readiness(
                item,
                item_type="Story opportunity",
                headline=item["title"],
                artifact=item["artifact"],
            )
        )
        rows.append(item)
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


def render_readiness_queue(
    candidates: List[Dict[str, str]],
    promotions: List[Dict[str, str]],
    source_board: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen: set[str] = set()

    def add_row(row: Dict[str, str], source: str, title_key: str = "headline") -> None:
        title = first_present(row.get(title_key), row.get("title"), row.get("story_opportunity_title"), default="Untitled candidate")
        key = first_present(row.get("story_opportunity_id"), title, source)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "rank": "",
                "source": source,
                "title": title,
                "recommended_path": first_present(
                    row.get("story_opportunity_recommended_path"),
                    row.get("recommendation"),
                    row.get("type"),
                    default="review",
                ),
                "score": clean(row.get("render_readiness_score")),
                "band": clean(row.get("render_readiness_band")),
                "source_cue": clean(row.get("render_readiness_source_cue")),
                "asset_cue": clean(row.get("render_readiness_asset_cue")),
                "format_cue": clean(row.get("render_readiness_format_cue")),
                "manual_path": clean(row.get("render_readiness_manual_path")),
                "blockers": clean(row.get("render_readiness_blockers")) or "none",
                "next_step": clean(row.get("render_readiness_next_step")),
                "artifact": first_present(row.get("artifact"), row.get("target"), default="operator_command_center.md"),
            }
        )

    for row in candidates:
        add_row(row, row.get("type") or "Content candidate")
    for row in promotions:
        add_row(row, "Lead promotion", title_key="title")
    for row in source_board:
        if row.get("story_opportunity_id") and row.get("story_opportunity_id") not in seen:
            add_row(row, "Source discovery", title_key="title")

    rows.sort(key=lambda item: (-as_int(item.get("score")), item.get("title", "")))
    for index, row in enumerate(rows[:12], 1):
        row["rank"] = str(index)
    return rows[:12]


def packet_slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-")
    return slug[:70] or "untitled-render-candidate"


def template_fit_for_path(path: str, source: str) -> Dict[str, str]:
    token = clean(path).lower()
    source_token = clean(source).lower()
    if token == "news_packet" or source_token == "news packet":
        return {
            "template_fit": "news_fact_card_review",
            "template_shape": "IG feed 1080x1350; Threads crop-safe summary",
            "asset_requirement": "No player asset required; use HSD brand treatment and verified source text only.",
            "renderer_family": "news_or_quality_graphics_manual_review",
        }
    if token == "studio_brief":
        return {
            "template_fit": "studio_brief_card_review",
            "template_shape": "IG feed 1080x1350 or carousel cover",
            "asset_requirement": "Confirm exact league/team/player assets before render prep; no text-logo fallback.",
            "renderer_family": "studio_bundle_manual_review",
        }
    if token == "manual_story_candidate":
        return {
            "template_fit": "manual_story_candidate_card_review",
            "template_shape": "IG feed 1080x1350 or IG story 1080x1920 after editor chooses angle",
            "asset_requirement": "Use brand-only treatment until a verified exact image or logo is approved.",
            "renderer_family": "manual_story_workflow_review",
        }
    if token == "final result" or source_token == "final result":
        return {
            "template_fit": "final_score_result_card_review",
            "template_shape": "IG story 1080x1920 or feed 1080x1350",
            "asset_requirement": "Use exact team logos from approved local registry; no placeholder badges.",
            "renderer_family": "final_score_story_manual_review",
        }
    return {
        "template_fit": "operator_review_card",
        "template_shape": "Choose feed 1080x1350 unless the operator marks story-first.",
        "asset_requirement": "Operator must decide whether verified assets are required before render prep.",
        "renderer_family": "manual_review_only",
    }


def enrich_render_row(row: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, str]:
    title = clean(row.get("title"))
    for candidate in payload.get("content_candidates", []):
        if clean(candidate.get("headline")) == title:
            return {
                "copy_headline": title,
                "copy_dek": clean(candidate.get("detail")),
                "copy_context": (
                    f"{clean(candidate.get('source_count')) or '0'} source(s); "
                    f"{clean(candidate.get('source_grade')) or 'not_scored'}"
                    f"{' score ' + clean(candidate.get('source_score')) if clean(candidate.get('source_score')) else ''}."
                ),
                "source_detail": clean(candidate.get("source_reason")),
            }
    for lead in payload.get("lead_promotion_recommendations", []):
        if clean(lead.get("title")) == title:
            return {
                "copy_headline": title,
                "copy_dek": clean(lead.get("detail")),
                "copy_context": (
                    f"Angle: {clean(lead.get('story_opportunity_angle')) or 'review'}; "
                    f"sources: {clean(lead.get('story_opportunity_sources')) or 'review'}."
                ),
                "source_detail": clean(lead.get("story_opportunity_reason")),
            }
    for lead in payload.get("source_discovery_board", []):
        if clean(lead.get("title")) == title:
            return {
                "copy_headline": title,
                "copy_dek": clean(lead.get("detail")),
                "copy_context": (
                    f"Discovery lane: {clean(lead.get('lane')) or 'review'}; "
                    f"posture: {clean(lead.get('posture')) or 'review'}."
                ),
                "source_detail": clean(lead.get("story_opportunity_reason")),
            }
    return {"copy_headline": title, "copy_dek": "", "copy_context": "", "source_detail": ""}


def manual_renderer_steps(packet: Dict[str, str]) -> str:
    steps = [
        f"Open {packet.get('source_artifact')} and confirm the source/copy fields match this packet.",
        "Open operator_command_center.html and confirm the candidate is still not held by source, asset, or format blockers.",
        f"Use template fit {packet.get('template_fit')} at {packet.get('template_shape')}.",
        f"Confirm asset requirement: {packet.get('asset_requirement')}",
        "Prepare the graphic manually in the renderer or design tool; do not auto-post or auto-publish.",
        "After visual review, record the decision in the normal manual QA or approval artifact before any human posting.",
    ]
    return " | ".join(steps)


def build_render_prep_packets(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    packets: List[Dict[str, str]] = []
    for row in payload.get("render_readiness_queue", []):
        band = clean(row.get("band"))
        blockers = clean(row.get("blockers"))
        if band.startswith("hold_") or blockers not in {"", "none"}:
            continue
        fit = template_fit_for_path(row.get("recommended_path", ""), row.get("source", ""))
        enriched = enrich_render_row(row, payload)
        packet = {
            "packet_id": f"render_prep_{clean(row.get('rank')) or len(packets) + 1}_{packet_slug(row.get('title'))}",
            "packet_status": "ready_for_manual_render_review" if band == "render_ready_review" else "review_before_manual_render",
            "render_rank": clean(row.get("rank")),
            "render_readiness_score": clean(row.get("score")),
            "render_readiness_band": band,
            "title": clean(row.get("title")),
            "recommended_path": clean(row.get("recommended_path")),
            "source_artifact": clean(row.get("artifact")),
            "source_cue": clean(row.get("source_cue")),
            "asset_cue": clean(row.get("asset_cue")),
            "format_cue": clean(row.get("format_cue")),
            "manual_path": clean(row.get("manual_path")),
            "blockers": blockers or "none",
            "copy_headline": enriched["copy_headline"],
            "copy_dek": enriched["copy_dek"],
            "copy_context": enriched["copy_context"],
            "source_detail": enriched["source_detail"],
            **fit,
            "manual_renderer_steps": "",
            "approval_gate": "human_visual_review_required_before_any_post",
            "auto_render_status": "not_rendered_by_generator",
            "publish_policy": "review_only_not_publish_ready",
            "paid_api_policy": "free_public_sources_only_no_paid_api",
        }
        packet["manual_renderer_steps"] = manual_renderer_steps(packet)
        packets.append(packet)
    return packets


def build_render_handoff_summary(render_prep_packets: List[Dict[str, str]]) -> Dict[str, Any]:
    if not render_prep_packets:
        return {
            "handoff_status": "no_render_prep_packet",
            "packet_id": "",
            "title": "",
            "folder": "render_handoff_top_packet",
            "readme": "render_handoff_top_packet/README.md",
            "files": [],
            "guardrails": {
                "review_only": True,
                "auto_render": False,
                "auto_publish": False,
                "paid_apis": False,
            },
        }
    packet = render_prep_packets[0]
    return {
        "handoff_status": "ready_for_manual_review",
        "packet_id": packet.get("packet_id", ""),
        "title": packet.get("title", ""),
        "folder": "render_handoff_top_packet",
        "readme": "render_handoff_top_packet/README.md",
        "files": [
            "render_handoff_top_packet/README.md",
            "render_handoff_top_packet/copy_sheet.md",
            "render_handoff_top_packet/copy_sheet.csv",
            "render_handoff_top_packet/asset_checklist.md",
            "render_handoff_top_packet/asset_checklist.csv",
            "render_handoff_top_packet/source_proof.md",
            "render_handoff_top_packet/manual_renderer_prompt.md",
            "render_handoff_top_packet/handoff_manifest.json",
        ],
        "guardrails": {
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "paid_apis": False,
        },
    }


def render_handoff_readme(payload: Dict[str, Any], packet: Dict[str, str] | None) -> str:
    if not packet:
        return "\n".join(
            [
                "# HSD Top Render Handoff",
                "",
                f"Generated: {payload['generated_at_utc']}",
                f"Command center version: {payload['version']}",
                "",
                "No render prep packet cleared the review gates for a top-packet handoff.",
                "",
                "Guardrails: review-only, no auto-rendering, no paid APIs, no auto-publishing.",
                "",
            ]
        )
    return "\n".join(
        [
            "# HSD Top Render Handoff",
            "",
            f"Generated: {payload['generated_at_utc']}",
            f"Command center version: {payload['version']}",
            "",
            f"Packet: `{clean(packet.get('packet_id'))}`",
            f"Story: {clean(packet.get('title'))}",
            f"Status: `{clean(packet.get('packet_status'))}`",
            f"Readiness: `{clean(packet.get('render_readiness_score'))}/100` / `{clean(packet.get('render_readiness_band'))}`",
            "",
            "## Open These Files",
            "",
            "1. `copy_sheet.md`",
            "2. `asset_checklist.md`",
            "3. `source_proof.md`",
            "4. `manual_renderer_prompt.md`",
            "5. `handoff_manifest.json`",
            "",
            "## Guardrails",
            "",
            "- Review-only handoff.",
            "- Does not render files.",
            "- Does not publish.",
            "- Does not call paid APIs.",
            "- Human visual review is required before any post.",
            "",
        ]
    )


def render_handoff_copy_sheet(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Copy Sheet",
            "",
            f"- Headline: {clean(packet.get('copy_headline'))}",
            f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
            f"- Recommended path: `{clean(packet.get('recommended_path'))}`",
            f"- Template fit: `{clean(packet.get('template_fit'))}`",
            f"- Template shape: `{clean(packet.get('template_shape'))}`",
            f"- Approval gate: `{clean(packet.get('approval_gate'))}`",
            "",
            "Copy is not approved for publishing until source proof and human visual review are complete.",
            "",
        ]
    )


def render_handoff_asset_checklist(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Asset Checklist",
            "",
            f"- Asset cue: `{clean(packet.get('asset_cue'))}`",
            f"- Asset requirement: {clean(packet.get('asset_requirement'))}",
            f"- Manual path: `{clean(packet.get('manual_path'))}`",
            f"- Renderer family: `{clean(packet.get('renderer_family'))}`",
            "",
            "## Stop/Go",
            "",
            "- GO only if exact required logos/images are approved or the packet explicitly says no player asset is required.",
            "- HOLD if any team, player, league, source, crop, or identity asset is uncertain.",
            "- Do not use text-logo fallback for public graphics.",
            "",
        ]
    )


def render_handoff_source_proof(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Source Proof",
            "",
            f"- Source artifact: `{clean(packet.get('source_artifact'))}`",
            f"- Source cue: `{clean(packet.get('source_cue'))}`",
            f"- Source detail: {clean(packet.get('source_detail')) or 'n/a'}",
            f"- Source/copy context: {clean(packet.get('copy_context')) or 'n/a'}",
            f"- Paid API policy: `{clean(packet.get('paid_api_policy'))}`",
            "",
            "## Required Human Check",
            "",
            f"1. Open {clean(packet.get('source_artifact'))} manually.",
            "2. Confirm the headline, dek, and context match verified source facts.",
            "3. Hold the render if a second source, official confirmation, or source timestamp is missing.",
            "",
        ]
    )


def render_manual_renderer_prompt(packet: Dict[str, str]) -> str:
    steps = [step.strip() for step in clean(packet.get("manual_renderer_steps")).split("|") if step.strip()]
    lines = [
        "# Manual Renderer Prompt",
        "",
        "Use this prompt manually only. Do not auto-render, auto-post, or publish.",
        "",
        "## Brief",
        "",
        f"Create a review-only HSD graphic for: {clean(packet.get('title'))}",
        "",
        "## Copy",
        "",
        f"- Headline: {clean(packet.get('copy_headline'))}",
        f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
        f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
        "",
        "## Format",
        "",
        f"- Template fit: {clean(packet.get('template_fit'))}",
        f"- Shape: {clean(packet.get('template_shape'))}",
        f"- Renderer family: {clean(packet.get('renderer_family'))}",
        "",
        "## Assets",
        "",
        f"- {clean(packet.get('asset_requirement'))}",
        "",
        "## Steps",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(steps, 1))
    lines += [
        "",
        "## Guardrail",
        "",
        "Output is for human visual review only. Nothing in this folder is publish-ready by itself.",
        "",
    ]
    return "\n".join(lines)


def write_render_handoff_outputs(payload: Dict[str, Any]) -> None:
    packets = payload.get("render_prep_packets", [])
    packet = packets[0] if packets else None
    write_text(OUT_RENDER_HANDOFF_README, render_handoff_readme(payload, packet))
    manifest = {
        "version": payload["version"],
        "generated_at_utc": payload["generated_at_utc"],
        "handoff_status": "ready_for_manual_review" if packet else "no_render_prep_packet",
        "folder": "render_handoff_top_packet",
        "guardrails": {
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "paid_apis": False,
        },
        "packet": packet or {},
        "files": [
            "README.md",
            "copy_sheet.md",
            "copy_sheet.csv",
            "asset_checklist.md",
            "asset_checklist.csv",
            "source_proof.md",
            "manual_renderer_prompt.md",
            "handoff_manifest.json",
        ],
    }
    if packet:
        write_text(OUT_RENDER_HANDOFF_COPY, render_handoff_copy_sheet(packet))
        write_csv(
            OUT_RENDER_HANDOFF_COPY_CSV,
            [
                {
                    "packet_id": packet.get("packet_id"),
                    "headline": packet.get("copy_headline"),
                    "dek": packet.get("copy_dek"),
                    "context": packet.get("copy_context"),
                    "template_fit": packet.get("template_fit"),
                    "template_shape": packet.get("template_shape"),
                    "approval_gate": packet.get("approval_gate"),
                }
            ],
            ["packet_id", "headline", "dek", "context", "template_fit", "template_shape", "approval_gate"],
        )
        write_text(OUT_RENDER_HANDOFF_ASSETS, render_handoff_asset_checklist(packet))
        write_csv(
            OUT_RENDER_HANDOFF_ASSETS_CSV,
            [
                {
                    "packet_id": packet.get("packet_id"),
                    "asset_cue": packet.get("asset_cue"),
                    "asset_requirement": packet.get("asset_requirement"),
                    "manual_path": packet.get("manual_path"),
                    "renderer_family": packet.get("renderer_family"),
                    "decision": "operator_review_required",
                }
            ],
            ["packet_id", "asset_cue", "asset_requirement", "manual_path", "renderer_family", "decision"],
        )
        write_text(OUT_RENDER_HANDOFF_SOURCE_PROOF, render_handoff_source_proof(packet))
        write_text(OUT_RENDER_HANDOFF_PROMPT, render_manual_renderer_prompt(packet))
    write_json(OUT_RENDER_HANDOFF_MANIFEST, manifest)


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
    render_queue: List[Dict[str, str]],
    render_prep_packets: List[Dict[str, str]],
    render_handoff_summary: Dict[str, Any],
    source_board: List[Dict[str, str]],
    promotions: List[Dict[str, str]],
    coverage_map: List[Dict[str, str]],
    proposal_review: List[Dict[str, str]],
    source_proposal_draft: List[Dict[str, str]],
    source_proposal_promotion_checklist: List[Dict[str, str]],
    source_registry_update_worksheet: List[Dict[str, str]],
    source_registry_diff_review: List[Dict[str, str]],
    source_registry_same_domain_resolution: List[Dict[str, str]],
    source_registry_verification_log: List[Dict[str, str]],
    source_registry_approval_packet: List[Dict[str, str]],
    source_registry_patch_preview: List[Dict[str, str]],
    source_registry_post_edit_validation: List[Dict[str, str]],
    source_proposal_pack_readiness: List[Dict[str, str]],
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

    if render_queue:
        ready_render_rows = [row for row in render_queue if row.get("band") == "render_ready_review"]
        blocked_render_rows = [row for row in render_queue if row.get("band", "").startswith("hold_")]
        prep_render_rows = [row for row in render_queue if row.get("band") == "render_prep_candidate"]
        if ready_render_rows:
            row = ready_render_rows[0]
            add_action(
                "Render ready",
                "Editor",
                f"Review render-ready story candidate: {row['title']}",
                (
                    f"Score {row.get('score')}/100. Source, asset, format, and manual path cues are ready for human review. "
                    f"{row.get('next_step')}"
                ),
                row.get("artifact") or "operator_command_center.md",
            )
        elif blocked_render_rows:
            row = blocked_render_rows[0]
            add_action(
                "Render hold",
                "Editor",
                f"Clear render-readiness blocker: {row['title']}",
                f"Score {row.get('score')}/100; blockers: {row.get('blockers')}. {row.get('next_step')}",
                row.get("artifact") or "operator_command_center.md",
            )
        elif prep_render_rows:
            row = prep_render_rows[0]
            add_action(
                "Render prep",
                "Editor",
                f"Prepare render candidate: {row['title']}",
                f"Score {row.get('score')}/100. {row.get('next_step')}",
                row.get("artifact") or "operator_command_center.md",
            )

    if render_prep_packets:
        packet = render_prep_packets[0]
        add_action(
            "Render packet",
            "Editor",
            f"Open render prep packet: {packet['title']}",
            (
                f"{packet.get('packet_status')} at score {packet.get('render_readiness_score')}/100. "
                f"Template: {packet.get('template_fit')} / {packet.get('template_shape')}. "
                "Use the packet steps for manual render prep only; publishing remains off."
            ),
            "render_prep_packets.md",
        )

    if render_handoff_summary.get("handoff_status") == "ready_for_manual_review":
        add_action(
            "Render handoff",
            "Editor",
            f"Open render handoff folder: {render_handoff_summary.get('title')}",
            (
                "Use the copy sheet, asset checklist, source proof, and manual renderer prompt as a review-only handoff. "
                "It does not render or publish anything."
            ),
            "render_handoff_top_packet/README.md",
        )

    coverage_gaps = [row for row in coverage_map if row.get("status") == "gap"]
    proposal_holds = [row for row in proposal_review if row.get("review_status") == "hold"]
    checklist_verify_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy"]
    checklist_hold_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "hold"]
    checklist_discard_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "discard"]
    registry_update_rows = [row for row in source_registry_update_worksheet if row.get("worksheet_decision") == "manual_registry_plan_after_verification"]
    registry_diff_hold_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD"]
    registry_diff_review_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW"]
    same_domain_input_rows = [
        row
        for row in source_registry_same_domain_resolution
        if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"}
    ]
    same_domain_resolved_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready"]
    same_domain_revise_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification"]
    same_domain_discard_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification"]
    verification_input_rows = [row for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required"]
    approval_packet_ready_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review"]
    approval_packet_hold_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit"]
    patch_preview_ready_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste"]
    patch_preview_hold_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch"]
    post_edit_exact_rows = [row for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match"]
    post_edit_issue_rows = [
        row
        for row in source_registry_post_edit_validation
        if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"}
    ]
    ready_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check"]
    blocked_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_")]
    duplicate_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review"]
    freshness_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check"]
    ready_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal"]
    if proposal_holds:
        held = proposal_holds[0]
        add_action(
            "Source hold",
            "Research",
            f"Resolve unsafe source proposal: {held.get('candidate_source_id') or 'missing source id'}",
            f"{held.get('safety_flags') or 'proposal issue'}; {held.get('issues') or 'Review before registry update.'}",
            "source_registry_proposal_review.md",
        )

    if checklist_verify_rows:
        row = checklist_verify_rows[0]
        add_action(
            "Promotion checklist",
            "Research",
            "Work source proposal promotion checklist",
            (
                f"{len(checklist_verify_rows)} row(s) are verify-then-copy candidates. "
                f"Start with {row.get('candidate_source_id')}: {row.get('operator_step')}. "
                "Open the URL manually before copying anything into the proposal inbox."
            ),
            "source_registry_proposal_promotion_checklist.md",
        )

    if checklist_hold_rows or checklist_discard_rows:
        row = (checklist_hold_rows + checklist_discard_rows)[0]
        add_action(
            "Checklist hold",
            "Research",
            "Resolve held or discarded source checklist rows",
            (
                f"{len(checklist_hold_rows)} hold row(s), {len(checklist_discard_rows)} discard row(s). "
                f"First item: {row.get('candidate_source_id')} / {row.get('checklist_decision')}."
            ),
            "source_registry_proposal_promotion_checklist.md",
        )

    if registry_update_rows or approval_packet_ready_rows or patch_preview_ready_rows or post_edit_issue_rows:
        add_action(
            "Playbook",
            "Research",
            "Open trusted-registry operator playbook",
            (
                "Use the step-by-step stop/go workflow before any manual registry edit. "
                "It lists exact files to open, approval gates, and rollback steps."
            ),
            "trusted_registry_operator_playbook.md",
        )

    if registry_update_rows:
        row = registry_update_rows[0]
        add_action(
            "Registry worksheet",
            "Research",
            "Review trusted-registry update worksheet",
            (
                f"{len(registry_update_rows)} review-only registry plan row(s). "
                f"Start with {row.get('source_id')}: compare proposed JSON, verify the public URL, "
                "and hand-edit config/source_registry.json only after approval."
            ),
            "source_registry_update_worksheet.md",
        )

    if registry_diff_hold_rows or registry_diff_review_rows:
        row = (registry_diff_hold_rows + registry_diff_review_rows)[0]
        add_action(
            "Registry diff",
            "Research",
            "Resolve trusted-registry diff review",
            (
                f"{len(registry_diff_hold_rows)} hold row(s), {len(registry_diff_review_rows)} review row(s). "
                f"Start with {row.get('source_id')}: {row.get('issues') or row.get('recommendation')}. "
                "Do not hand-edit the registry until this review is clear."
            ),
            "source_registry_diff_review.md",
        )

    if same_domain_input_rows or same_domain_revise_rows or same_domain_discard_rows:
        row = (same_domain_input_rows + same_domain_revise_rows + same_domain_discard_rows)[0]
        add_action(
            "Same-domain review",
            "Research",
            "Resolve same-domain source decisions",
            (
                f"{len(same_domain_input_rows)} need decision/evidence, "
                f"{len(same_domain_revise_rows)} revise, {len(same_domain_discard_rows)} discard, "
                f"{len(same_domain_resolved_rows)} same-domain OK. "
                f"Start with {row.get('source_id')}: {row.get('evidence_requirement') or row.get('verification_log_instruction')}. "
                "Do this before filling approval fields in the verification log."
            ),
            "source_registry_same_domain_resolution.md",
        )

    if verification_input_rows:
        row = verification_input_rows[0]
        add_action(
            "Verification log",
            "Research",
            "Fill manual source verification log",
            (
                f"{len(verification_input_rows)} source row(s) need operator evidence. "
                f"Start with {row.get('source_id')}: record URL checked, freshness result, "
                "duplicate decision, and approval/hold outcome before any registry edit."
            ),
            "source_registry_verification_log.md",
        )

    if approval_packet_ready_rows or approval_packet_hold_rows:
        row = (approval_packet_hold_rows + approval_packet_ready_rows)[0]
        add_action(
            "Approval packet",
            "Research",
            "Review manual registry approval packet",
            (
                f"{len(approval_packet_ready_rows)} ready row(s), {len(approval_packet_hold_rows)} held row(s). "
                f"Start with {row.get('source_id')}: {row.get('hold_reason') or 'final JSON and evidence review required'}. "
                "This packet is review-only and does not edit the trusted registry."
            ),
            "source_registry_approval_packet.md",
        )

    if patch_preview_ready_rows or patch_preview_hold_rows:
        row = (patch_preview_hold_rows + patch_preview_ready_rows)[0]
        add_action(
            "Patch preview",
            "Research",
            "Review manual registry patch preview",
            (
                f"{len(patch_preview_ready_rows)} ready copy/paste row(s), {len(patch_preview_hold_rows)} held row(s). "
                f"Start with {row.get('source_id')}: {row.get('hold_reason') or 'compare before/after and copy manually only'}. "
                "This preview does not edit the trusted registry."
            ),
            "source_registry_patch_preview.md",
        )

    if post_edit_exact_rows or post_edit_issue_rows:
        row = (post_edit_issue_rows + post_edit_exact_rows)[0]
        add_action(
            "Post-edit check",
            "Research",
            "Review post-edit registry validation",
            (
                f"{len(post_edit_exact_rows)} exact match row(s), {len(post_edit_issue_rows)} issue row(s). "
                f"Start with {row.get('source_id')}: {row.get('post_edit_validation_status')}. "
                "Hold any drift, unsafe enablement, paid/login signal, automation, or publish-policy issue."
            ),
            "source_registry_post_edit_validation.md",
        )

    if ready_draft_rows:
        row = ready_draft_rows[0]
        add_action(
            "Proposal draft",
            "Research",
            "Review manual source proposal draft",
            (
                f"{len(ready_draft_rows)} draft row(s) are ready to copy only after manual freshness review. "
                f"Start with {row.get('candidate_source_id')}: {row.get('freshness_warning') or 'Open the page manually first.'} "
                "Do not enable sources or edit the trusted registry from this draft."
            ),
            "source_registry_proposal_draft.md",
        )

    if blocked_draft_rows and not proposal_holds:
        row = blocked_draft_rows[0]
        add_action(
            "Draft hold",
            "Research",
            "Review blocked source proposal draft rows",
            (
                f"{len(blocked_draft_rows)} draft row(s) are held by duplicate or freshness warnings. "
                f"First held row: {row.get('candidate_source_id')} / {row.get('draft_action')}."
            ),
            "source_registry_proposal_draft.md",
        )

    if duplicate_pack_reviews:
        pack = duplicate_pack_reviews[0]
        add_action(
            "Pack duplicate review",
            "Research",
            f"Resolve duplicate cues in {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Duplicate source cues detected.'} "
                f"Duplicates: {pack.get('duplicate_candidate_ids') or 'see readiness report'}. "
                "Do not copy duplicate candidates into proposals until the registry match is reviewed."
            ),
            "source_proposal_pack_readiness.md",
        )
    elif freshness_pack_reviews:
        pack = freshness_pack_reviews[0]
        add_action(
            "Pack freshness check",
            "Research",
            f"Freshness-check {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Source freshness check needed.'} "
                f"Open top candidates manually: {pack.get('top_candidate_ids') or 'see readiness report'}. "
                "Keep every row disabled and proposal-only."
            ),
            "source_proposal_pack_readiness.md",
        )
    elif ready_pack_reviews and not coverage_gaps:
        pack = ready_pack_reviews[0]
        add_action(
            "Pack proposal review",
            "Research",
            f"Review ready source pack: {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Pack is ready for manual proposal review.'} "
                f"Open top candidates for freshness: {pack.get('top_candidate_ids') or 'see readiness report'}. "
                "Copy only selected rows into the manual proposal inbox after review."
            ),
            "source_proposal_pack_readiness.md",
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


def summarize_source_ids(rows: Iterable[Dict[str, str]], key: str = "source_id", limit: int = 4) -> str:
    values = [clean(row.get(key)) for row in rows if clean(row.get(key))]
    if not values:
        return "none"
    shown = values[:limit]
    suffix = f" +{len(values) - limit} more" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def build_source_registry_readiness_summary(
    coverage_map: List[Dict[str, str]],
    source_proposal_draft: List[Dict[str, str]],
    source_proposal_promotion_checklist: List[Dict[str, str]],
    source_registry_update_worksheet: List[Dict[str, str]],
    source_registry_diff_review: List[Dict[str, str]],
    source_registry_same_domain_resolution: List[Dict[str, str]],
    source_registry_verification_log: List[Dict[str, str]],
    source_registry_approval_packet: List[Dict[str, str]],
    source_registry_patch_preview: List[Dict[str, str]],
    source_registry_post_edit_validation: List[Dict[str, str]],
    source_proposal_pack_readiness: List[Dict[str, str]],
) -> Dict[str, str]:
    coverage_gaps = [row for row in coverage_map if row.get("status") == "gap"]
    ready_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check"]
    blocked_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_")]
    checklist_verify_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy"]
    checklist_hold_rows = [
        row
        for row in source_proposal_promotion_checklist
        if row.get("checklist_decision") in {"hold", "discard"}
    ]
    worksheet_rows = [row for row in source_registry_update_worksheet if row.get("worksheet_decision") == "manual_registry_plan_after_verification"]
    diff_hold_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD"]
    diff_review_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW"]
    same_domain_input_rows = [
        row
        for row in source_registry_same_domain_resolution
        if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"}
    ]
    same_domain_revise_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification"]
    same_domain_discard_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification"]
    same_domain_ok_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready"]
    verification_rows = [row for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required"]
    approval_ready_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review"]
    approval_hold_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit"]
    patch_ready_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste"]
    patch_hold_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch"]
    post_edit_exact_rows = [row for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match"]
    post_edit_issue_rows = [
        row
        for row in source_registry_post_edit_validation
        if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"}
    ]
    duplicate_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review"]
    freshness_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check"]
    ready_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal"]

    summary = {
        "readiness_status": "ready_to_start",
        "next_safest_action": "Open the trusted-registry operator playbook and start at the first incomplete stop/go gate.",
        "blockers": "none",
        "open_first_file": "trusted_registry_operator_playbook.md",
        "support_file": "trusted_registry_operator_playbook.md",
        "focus_source_ids": "none",
        "rollup": "No active manual registry change rows found.",
        "guardrail": "Manual review only; keep proposed sources disabled; no paid APIs, auto-runs, auto-enabling, or publishing.",
    }

    def set_summary(
        status: str,
        action: str,
        blockers: str,
        open_first_file: str,
        rows: List[Dict[str, str]],
        rollup: str,
        focus_key: str = "source_id",
    ) -> Dict[str, str]:
        summary.update(
            {
                "readiness_status": status,
                "next_safest_action": action,
                "blockers": blockers or "none",
                "open_first_file": open_first_file,
                "focus_source_ids": summarize_source_ids(rows, key=focus_key),
                "rollup": rollup,
            }
        )
        return summary

    if post_edit_issue_rows:
        blocker_bits = [
            f"{clean(row.get('source_id'))}: {clean(row.get('post_edit_validation_status'))}"
            f"{' (' + clean(row.get('unsafe_flags')) + ')' if clean(row.get('unsafe_flags')) else ''}"
            for row in post_edit_issue_rows[:4]
        ]
        return set_summary(
            "blocked_post_edit_validation",
            "Open source_registry_post_edit_validation.md first and hold unsafe or drifted rows before trusting any registry edit.",
            "; ".join(blocker_bits),
            "source_registry_post_edit_validation.md",
            post_edit_issue_rows,
            f"{len(post_edit_issue_rows)} post-edit issue row(s), {len(post_edit_exact_rows)} exact match row(s).",
        )
    if patch_hold_rows:
        return set_summary(
            "blocked_patch_preview",
            "Open source_registry_patch_preview.md and resolve held patch rows before any manual copy/paste registry edit.",
            f"{len(patch_hold_rows)} held patch preview row(s): {summarize_source_ids(patch_hold_rows)}",
            "source_registry_patch_preview.md",
            patch_hold_rows,
            f"{len(patch_ready_rows)} ready patch row(s), {len(patch_hold_rows)} held row(s).",
        )
    if approval_hold_rows:
        return set_summary(
            "blocked_approval_packet",
            "Open source_registry_approval_packet.md and clear held approval rows before preparing a registry patch.",
            f"{len(approval_hold_rows)} held approval row(s): {summarize_source_ids(approval_hold_rows)}",
            "source_registry_approval_packet.md",
            approval_hold_rows,
            f"{len(approval_ready_rows)} ready approval row(s), {len(approval_hold_rows)} held row(s).",
        )
    if diff_hold_rows or diff_review_rows:
        rows = diff_hold_rows + diff_review_rows
        resolution_counts = {
            action: sum(1 for row in rows if clean(row.get("resolution_action")) == action)
            for action in ["VERIFY", "REVISE", "HOLD", "DISCARD"]
        }
        resolution_rollup = ", ".join(
            f"{action.lower()} {count}"
            for action, count in resolution_counts.items()
            if count
        ) or "resolution cues not available"
        return set_summary(
            "blocked_diff_review",
            "Open source_registry_same_domain_resolution.md for HOLD rows, then follow VERIFY, REVISE, HOLD, or DISCARD cues before filling the verification log.",
            f"{len(diff_hold_rows)} hold row(s), {len(diff_review_rows)} review row(s): {summarize_source_ids(rows)}",
            "source_registry_same_domain_resolution.md" if same_domain_input_rows or same_domain_revise_rows or same_domain_discard_rows else "source_registry_diff_review.md",
            rows,
            f"{len(diff_hold_rows)} hold row(s), {len(diff_review_rows)} review row(s) before verification can be trusted; {resolution_rollup}; same-domain ok {len(same_domain_ok_rows)}, needs decision {len(same_domain_input_rows)}, revise {len(same_domain_revise_rows)}, discard {len(same_domain_discard_rows)}.",
        )
    if verification_rows:
        return set_summary(
            "needs_operator_evidence",
            "Open source_registry_verification_log.csv and record URL checked, freshness, duplicate decision, and approval/hold outcome.",
            f"{len(verification_rows)} row(s) still need operator evidence: {summarize_source_ids(verification_rows)}",
            "source_registry_verification_log.csv",
            verification_rows,
            f"{len(verification_rows)} manual verification row(s) need human evidence before approval.",
        )
    if patch_ready_rows:
        return set_summary(
            "ready_for_manual_patch_preview",
            "Open source_registry_patch_preview.md, compare the side-by-side preview, then copy/paste manually only if the playbook stop/go checks pass.",
            "none",
            "source_registry_patch_preview.md",
            patch_ready_rows,
            f"{len(patch_ready_rows)} patch preview row(s) ready for final manual copy/paste review.",
        )
    if approval_ready_rows:
        return set_summary(
            "ready_for_final_approval_review",
            "Open source_registry_approval_packet.md and review the exact disabled JSON plus evidence before creating a patch preview.",
            "none",
            "source_registry_approval_packet.md",
            approval_ready_rows,
            f"{len(approval_ready_rows)} approved row(s) ready for final manual review.",
        )
    if worksheet_rows:
        return set_summary(
            "worksheet_review_needed",
            "Open source_registry_update_worksheet.md and review disabled proposed source objects, before/after notes, and rollback coverage.",
            "none",
            "source_registry_update_worksheet.md",
            worksheet_rows,
            f"{len(worksheet_rows)} review-only registry worksheet row(s) are waiting.",
        )
    if checklist_verify_rows:
        return set_summary(
            "proposal_checklist_ready",
            "Open source_registry_proposal_promotion_checklist.md and verify ready rows manually before copying selected rows to the proposal inbox.",
            f"{len(checklist_hold_rows)} held/discarded checklist row(s)" if checklist_hold_rows else "none",
            "source_registry_proposal_promotion_checklist.md",
            checklist_verify_rows,
            f"{len(checklist_verify_rows)} verify-then-copy row(s), {len(checklist_hold_rows)} held/discarded row(s).",
        )
    if ready_draft_rows:
        return set_summary(
            "proposal_draft_ready",
            "Open source_registry_proposal_draft.md and freshness-check ready draft rows before using the promotion checklist.",
            f"{len(blocked_draft_rows)} blocked draft row(s)" if blocked_draft_rows else "none",
            "source_registry_proposal_draft.md",
            ready_draft_rows,
            f"{len(ready_draft_rows)} draft row(s) ready after freshness check, {len(blocked_draft_rows)} blocked row(s).",
        )
    if duplicate_pack_rows:
        return set_summary(
            "pack_duplicate_review_needed",
            "Open source_proposal_pack_readiness.md and resolve duplicate cues before promoting any pack rows.",
            f"{len(duplicate_pack_rows)} pack(s) need duplicate review.",
            "source_proposal_pack_readiness.md",
            duplicate_pack_rows,
            f"{len(ready_pack_rows)} ready pack(s), {len(duplicate_pack_rows)} duplicate-review pack(s), {len(freshness_pack_rows)} freshness-check pack(s).",
            focus_key="pack_key",
        )
    if freshness_pack_rows:
        return set_summary(
            "pack_freshness_check_needed",
            "Open source_proposal_pack_readiness.md and manually freshness-check top candidates before proposal drafting.",
            f"{len(freshness_pack_rows)} pack(s) need source freshness checks.",
            "source_proposal_pack_readiness.md",
            freshness_pack_rows,
            f"{len(ready_pack_rows)} ready pack(s), {len(freshness_pack_rows)} freshness-check pack(s).",
            focus_key="pack_key",
        )
    if coverage_gaps:
        return set_summary(
            "coverage_gap_intake_needed",
            "Open source_coverage_map.csv to choose the next free official, team, wire, or cross-check source gap for proposal intake.",
            f"{len(coverage_gaps)} coverage gap(s): {summarize_source_ids(coverage_gaps, key='key')}",
            "source_coverage_map.csv",
            coverage_gaps,
            f"{len(coverage_gaps)} source coverage gap(s) still need proposal intake.",
            focus_key="key",
        )
    return summary


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


def trim_actions(actions: List[Dict[str, str]], limit: int = 24) -> List[Dict[str, str]]:
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
    render_queue = render_readiness_queue(candidates, promotions, source_board)
    render_prep_packets = build_render_prep_packets(
        {
            "content_candidates": candidates,
            "lead_promotion_recommendations": promotions,
            "source_discovery_board": source_board,
            "render_readiness_queue": render_queue,
        }
    )
    render_handoff_summary = build_render_handoff_summary(render_prep_packets)
    coverage_map = source_coverage_map(source_registry)
    source_intake_rows = read_csv("source_registry_intake_template.csv")
    source_proposal_review = read_csv("source_registry_proposal_review.csv")
    source_proposal_draft = read_csv("source_registry_proposal_draft.csv")
    source_proposal_promotion_checklist = read_csv("source_registry_proposal_promotion_checklist.csv")
    source_registry_update_worksheet = read_csv("source_registry_update_worksheet.csv")
    source_registry_diff_review = read_csv("source_registry_diff_review.csv")
    source_registry_same_domain_resolution = read_csv("source_registry_same_domain_resolution.csv")
    source_registry_verification_log = read_csv("source_registry_verification_log.csv")
    source_registry_approval_packet = read_csv("source_registry_approval_packet.csv")
    source_registry_patch_preview = read_csv("source_registry_patch_preview.csv")
    source_registry_post_edit_validation = read_csv("source_registry_post_edit_validation.csv")
    source_proposal_pack_readiness = read_csv("source_proposal_pack_readiness.csv")
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
    source_registry_readiness_summary = build_source_registry_readiness_summary(
        coverage_map,
        source_proposal_draft,
        source_proposal_promotion_checklist,
        source_registry_update_worksheet,
        source_registry_diff_review,
        source_registry_same_domain_resolution,
        source_registry_verification_log,
        source_registry_approval_packet,
        source_registry_patch_preview,
        source_registry_post_edit_validation,
        source_proposal_pack_readiness,
    )

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
        metric("Proposal draft rows", len(source_proposal_draft)),
        metric("Proposal draft ready", sum(1 for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check")),
        metric("Proposal draft blocked", sum(1 for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_"))),
        metric("Checklist verify/copy", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy")),
        metric("Checklist hold", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "hold")),
        metric("Checklist discard", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "discard")),
        metric("Registry worksheet rows", len(source_registry_update_worksheet)),
        metric("Worksheet disabled plans", sum(1 for row in source_registry_update_worksheet if row.get("proposed_enabled") == "False")),
        metric("Registry diff hold", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD")),
        metric("Registry diff review", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW")),
        metric("Registry diff pass", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "PASS")),
        metric("Diff cues verify", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "VERIFY")),
        metric("Diff cues revise", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "REVISE")),
        metric("Diff cues hold", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "HOLD")),
        metric("Diff cues discard", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "DISCARD")),
        metric("Same-domain rows", len(source_registry_same_domain_resolution)),
        metric("Same-domain needs decision", sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"})),
        metric("Same-domain OK", sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready")),
        metric("Same-domain revise/discard", "/".join([
            str(sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification")),
            str(sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification")),
        ])),
        metric("Verification log rows", len(source_registry_verification_log)),
        metric("Verification input needed", sum(1 for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required")),
        metric("Approval packet rows", len(source_registry_approval_packet)),
        metric("Approval packet ready", sum(1 for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review")),
        metric("Approval packet held", sum(1 for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit")),
        metric("Patch preview rows", len(source_registry_patch_preview)),
        metric("Patch preview ready", sum(1 for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste")),
        metric("Patch preview held", sum(1 for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch")),
        metric("Post-edit validations", len(source_registry_post_edit_validation)),
        metric("Post-edit exact", sum(1 for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match")),
        metric("Post-edit issues", sum(1 for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"})),
        metric("Registry readiness", source_registry_readiness_summary["readiness_status"], source_registry_readiness_summary["blockers"]),
        metric("Source packs ready", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal")),
        metric("Source packs duplicate review", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review")),
        metric("Source packs freshness check", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check")),
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
        metric("Render readiness rows", len(render_queue)),
        metric("Render-ready review", sum(1 for row in render_queue if row.get("band") == "render_ready_review")),
        metric("Render prep candidates", sum(1 for row in render_queue if row.get("band") == "render_prep_candidate")),
        metric("Render holds", sum(1 for row in render_queue if row.get("band", "").startswith("hold_"))),
        metric("Render needs source", sum(1 for row in render_queue if "source" in row.get("blockers", ""))),
        metric("Render needs asset", sum(1 for row in render_queue if "asset" in row.get("blockers", ""))),
        metric("Render prep packets", len(render_prep_packets)),
        metric("Render packets ready", sum(1 for row in render_prep_packets if row.get("packet_status") == "ready_for_manual_render_review")),
        metric("Render handoff", render_handoff_summary.get("handoff_status", "not_created")),
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
        render_queue,
        render_prep_packets,
        render_handoff_summary,
        source_board,
        promotions,
        coverage_map,
        source_proposal_review,
        source_proposal_draft,
        source_proposal_promotion_checklist,
        source_registry_update_worksheet,
        source_registry_diff_review,
        source_registry_same_domain_resolution,
        source_registry_verification_log,
        source_registry_approval_packet,
        source_registry_patch_preview,
        source_registry_post_edit_validation,
        source_proposal_pack_readiness,
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
        "render_readiness_queue": render_queue,
        "render_prep_packets": render_prep_packets,
        "render_handoff_summary": render_handoff_summary,
        "source_discovery_board": source_board,
        "lead_promotion_recommendations": promotions,
        "source_coverage_map": coverage_map,
        "source_registry_intake_template": source_intake_rows,
        "source_registry_proposal_review": source_proposal_review,
        "source_registry_proposal_draft": source_proposal_draft,
        "source_registry_proposal_promotion_checklist": source_proposal_promotion_checklist,
        "source_registry_update_worksheet": source_registry_update_worksheet,
        "source_registry_diff_review": source_registry_diff_review,
        "source_registry_same_domain_resolution": source_registry_same_domain_resolution,
        "source_registry_verification_log": source_registry_verification_log,
        "source_registry_approval_packet": source_registry_approval_packet,
        "source_registry_patch_preview": source_registry_patch_preview,
        "source_registry_post_edit_validation": source_registry_post_edit_validation,
        "source_registry_readiness_summary": source_registry_readiness_summary,
        "source_proposal_pack_readiness": source_proposal_pack_readiness,
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


def render_source_registry_readiness_summary(summary: Dict[str, str]) -> str:
    open_first = clean(summary.get("open_first_file"))
    support_file = clean(summary.get("support_file")) or "trusted_registry_operator_playbook.md"
    return f"""
    <article class="content-row">
      <div>
        <div class="row-kicker">Source registry readiness {pill(summary.get('readiness_status') or 'review')}</div>
        <h3>{html.escape(clean(summary.get('next_safest_action')) or 'Open the trusted-registry operator playbook.')}</h3>
        <p><strong>Blockers:</strong> {html.escape(clean(summary.get('blockers')) or 'none')}</p>
        <p><strong>Focus:</strong> {html.escape(clean(summary.get('focus_source_ids')) or 'none')}</p>
        <small>{html.escape(clean(summary.get('rollup')) or 'No registry readiness rollup found.')} {html.escape(clean(summary.get('guardrail')) or '')}</small>
      </div>
      <div class="row-tool">
        {open_link(open_first, 'Open next')}
        <div style="margin-top:8px">{open_link(support_file, 'Playbook')}</div>
      </div>
    </article>
    """


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
        readiness = (
            f"render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / source: {html.escape(row.get('render_readiness_source_cue') or 'n/a')}"
            f" / assets: {html.escape(row.get('render_readiness_asset_cue') or 'n/a')}"
            f" / format: {html.escape(row.get('render_readiness_format_cue') or 'n/a')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row['type'])} {pill(row['priority'])} {pill(row['status'])}</div>
                <h3>{html.escape(row['headline'])}</h3>
                <p>{html.escape(row['detail'])}</p>
                <small>{html.escape(row.get('source_count') or '0')} source(s) / {html.escape(row.get('source_grade') or 'not_scored')} {f"({html.escape(row.get('source_score') or '')})" if row.get('source_score') else ""} / {readiness}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No content candidates found.</p>'


def render_render_readiness(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('rank')))}</td>
              <td>{pill(row.get('band') or 'not_scored')}</td>
              <td>{html.escape(clean(row.get('score')) or '0')}</td>
              <td>{html.escape(clean(row.get('title')))}</td>
              <td>{html.escape(clean(row.get('recommended_path')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('asset_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('format_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('manual_path')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('blockers')) or 'none')}</td>
              <td>{html.escape(clean(row.get('next_step')))}</td>
              <td>{open_link(clean(row.get('artifact')))}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="12" class="empty">No render-readiness candidates found.</td></tr>'


def render_render_prep_packets(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(row.get('packet_status') or 'review')}</td>
              <td>{html.escape(clean(row.get('render_readiness_score')) or '0')}</td>
              <td>{html.escape(clean(row.get('title')))}</td>
              <td>{html.escape(clean(row.get('template_fit')))}</td>
              <td>{html.escape(clean(row.get('template_shape')))}</td>
              <td>{html.escape(clean(row.get('copy_headline')))}</td>
              <td>{html.escape(clean(row.get('asset_requirement')))}</td>
              <td>{html.escape(clean(row.get('manual_renderer_steps')))}</td>
              <td>{html.escape(clean(row.get('approval_gate')))}</td>
              <td>{open_link('render_prep_packets.md', 'Open packet')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="10" class="empty">No render-prep packets cleared review gates.</td></tr>'


def render_render_handoff_summary(summary: Dict[str, Any]) -> str:
    files = summary.get("files") or []
    file_links = " ".join(open_link(clean(path), Path(clean(path)).name) for path in files[:6])
    return f"""
    <article class="content-row">
      <div>
        <div class="row-kicker">Render handoff {pill(summary.get('handoff_status') or 'not_created')}</div>
        <h3>{html.escape(clean(summary.get('title')) or 'No top render handoff ready')}</h3>
        <p>Review-only folder: <code>{html.escape(clean(summary.get('folder')) or 'render_handoff_top_packet')}</code>. Use copy sheet, asset checklist, source proof, and manual renderer prompt before any human visual review.</p>
        <small>Guardrails: no paid APIs / no auto-runs / no auto-rendering / no publishing.</small>
      </div>
      <div class="row-tool">
        {open_link(clean(summary.get('readme')) or 'render_handoff_top_packet/README.md', 'Open folder')}
        <div style="margin-top:8px">{file_links}</div>
      </div>
    </article>
    """


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
        render_note = (
            f" / render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['lane'])} {pill(row['status'])} {pill(row['posture'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('source') or '')} / {html.escape(row.get('band') or '')} / promote: {html.escape(row.get('promotion') or 'monitor_only')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}{render_note}</small>
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
        render_note = (
            f" / render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['priority'])} {pill(row['recommendation'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('lane') or '')} / target: {html.escape(row.get('target') or '')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}{render_note}</small>
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


def render_source_proposal_pack_readiness(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{pill(clean(row.get('readiness_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('candidate_rows')) or '0')}</td>
              <td>{html.escape(clean(row.get('official_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('cross_check_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('duplicate_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('review_cues')) or '-')}</td>
              <td>{html.escape(clean(row.get('top_candidate_ids')) or '-')}</td>
              <td>{html.escape(clean(row.get('next_step')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source pack readiness cues found.</td></tr>'


def render_source_proposal_draft(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('draft_selection_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('draft_action')) or '-')}</td>
              <td>{html.escape(clean(row.get('duplicate_warning')) or '-')}</td>
              <td>{html.escape(clean(row.get('freshness_warning')) or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source proposal draft rows found.</td></tr>'


def render_source_proposal_promotion_checklist(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        reason = clean(row.get("hold_reason")) or clean(row.get("discard_reason")) or clean(row.get("freshness_warning"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('checklist_decision')) or 'review')}</td>
              <td>{html.escape(clean(row.get('operator_step')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('copy_allowed')) or 'No')}</td>
              <td>{html.escape(clean(row.get('copy_target')) or '-')}</td>
              <td>{html.escape(reason or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source proposal promotion checklist rows found.</td></tr>'


def render_source_registry_update_worksheet(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('worksheet_decision')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('manual_edit_target')) or 'config/source_registry.json')}</td>
              <td>{html.escape(clean(row.get('manual_edit_allowed')) or 'manual review only')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'False')}</td>
              <td>{html.escape(clean(row.get('auto_edit_status')) or 'not_performed_by_generator')}</td>
              <td>{html.escape(clean(row.get('before_after_diff')) or '-')}</td>
              <td>{html.escape(clean(row.get('rollback_note')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source registry update worksheet rows found.</td></tr>'


def render_source_registry_diff_review(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        instruction = clean(row.get("verification_log_instruction")) or clean(row.get("recommendation")) or "-"
        label = clean(row.get("resolution_label"))
        instruction_text = f"{label}: {instruction}" if label else instruction
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('diff_review_status')) or 'review')}</td>
              <td>{pill(clean(row.get('resolution_action')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_domain')) or '-')}</td>
              <td>{html.escape(clean(row.get('flags')) or 'none')}</td>
              <td>{html.escape(clean(row.get('issues')) or 'none')}</td>
              <td>{html.escape(clean(row.get('registry_source_id_match')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_domain_match')) or 'No')}</td>
              <td>{html.escape(clean(row.get('rollback_status')) or '-')}</td>
              <td>{html.escape(instruction_text)}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="10" class="empty">No source registry diff review rows found.</td></tr>'


def render_source_registry_same_domain_resolution(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('same_domain_resolution_status')) or 'operator_input_required')}</td>
              <td>{html.escape(clean(row.get('resolution_decision')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_domain')) or '-')}</td>
              <td>{html.escape(clean(row.get('registry_domain_match')) or clean(row.get('worksheet_domain_match')) or '-')}</td>
              <td>{html.escape(clean(row.get('compared_existing_source_id')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('evidence_requirement')) or '-')}</td>
              <td>{html.escape(clean(row.get('approval_gate')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No same-domain resolution rows found.</td></tr>'


def render_source_registry_verification_log(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('verification_log_status')) or 'operator_input_required')}</td>
              <td>{pill(clean(row.get('diff_resolution_action')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('diff_review_status')) or '-')}</td>
              <td>{html.escape(clean(row.get('diff_resolution_instruction')) or 'follow diff review cue')}</td>
              <td>{html.escape(clean(row.get('url_checked')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('freshness_result')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('duplicate_decision')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('approval_outcome')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="11" class="empty">No source verification log rows found.</td></tr>'


def render_source_registry_approval_packet(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        exact_json = clean(row.get("exact_proposed_source_json"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('approval_packet_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('freshness_result')) or '-')}</td>
              <td>{html.escape(clean(row.get('duplicate_decision')) or '-')}</td>
              <td>{html.escape(clean(row.get('hold_reason')) or 'none')}</td>
              <td>{html.escape(exact_json[:160] + ('...' if len(exact_json) > 160 else ''))}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No approved source verification rows found.</td></tr>'


def render_source_registry_patch_preview(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        source_json = clean(row.get("copy_paste_source_json"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('patch_preview_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('manual_edit_target')) or '-')}</td>
              <td>{html.escape(clean(row.get('registry_before_summary')) or '-')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('hold_reason')) or 'none')}</td>
              <td>{html.escape(source_json[:180] + ('...' if len(source_json) > 180 else ''))}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="8" class="empty">No ready registry patch preview rows found.</td></tr>'


def render_source_registry_post_edit_validation(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('post_edit_validation_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('exact_match')) or '-')}</td>
              <td>{html.escape(clean(row.get('enabled_status')) or '-')}</td>
              <td>{html.escape(clean(row.get('automation_status_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('publish_policy_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('free_source_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('drift_fields')) or 'none')}</td>
              <td>{html.escape(clean(row.get('unsafe_flags')) or 'none')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No post-edit validation rows found.</td></tr>'


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
      <div class="panel" style="margin-bottom:16px">
        <h2>Render readiness</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Rank</th><th>Band</th><th>Score</th><th>Story</th><th>Path</th><th>Source</th><th>Assets</th><th>Format</th><th>Manual path</th><th>Blockers</th><th>Next step</th><th>Open</th></tr></thead>
            <tbody>{render_render_readiness(payload['render_readiness_queue'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-bottom:16px">
        <h2>Render prep packets</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Score</th><th>Story</th><th>Template</th><th>Shape</th><th>Copy headline</th><th>Assets</th><th>Manual steps</th><th>Gate</th><th>Open</th></tr></thead>
            <tbody>{render_render_prep_packets(payload['render_prep_packets'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-bottom:16px">
        <h2>Top render handoff</h2>
        <div class="content-list">{render_render_handoff_summary(payload['render_handoff_summary'])}</div>
      </div>
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
        <h2>Source registry readiness</h2>
        <div class="content-list">{render_source_registry_readiness_summary(payload['source_registry_readiness_summary'])}</div>
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
        <h2>Source registry diff review</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Cue</th><th>Source ID</th><th>Domain</th><th>Flags</th><th>Issues</th><th>ID match</th><th>Domain match</th><th>Rollback</th><th>Before verification log</th></tr></thead>
            <tbody>{render_source_registry_diff_review(payload['source_registry_diff_review'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry same-domain resolution</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Decision</th><th>Source ID</th><th>Domain</th><th>Match</th><th>Compared source</th><th>Evidence</th><th>Requirement</th><th>Gate</th></tr></thead>
            <tbody>{render_source_registry_same_domain_resolution(payload['source_registry_same_domain_resolution'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source verification log</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Cue</th><th>Source ID</th><th>URL</th><th>Diff</th><th>Instruction</th><th>URL checked</th><th>Freshness</th><th>Duplicate decision</th><th>Approval outcome</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_verification_log(payload['source_registry_verification_log'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry approval packet</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>URL</th><th>Evidence</th><th>Freshness</th><th>Duplicate</th><th>Hold reason</th><th>Exact JSON</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_approval_packet(payload['source_registry_approval_packet'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry patch preview</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>Target</th><th>Before</th><th>Evidence</th><th>Hold reason</th><th>Copy JSON</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_patch_preview(payload['source_registry_patch_preview'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry post-edit validation</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>Exact</th><th>Enabled</th><th>Automation</th><th>Publish</th><th>Free</th><th>Drift</th><th>Unsafe</th></tr></thead>
            <tbody>{render_source_registry_post_edit_validation(payload['source_registry_post_edit_validation'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry update worksheet</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Decision</th><th>Source ID</th><th>URL</th><th>Manual target</th><th>Edit allowed</th><th>Enabled</th><th>Auto edit</th><th>Before/after</th><th>Rollback</th></tr></thead>
            <tbody>{render_source_registry_update_worksheet(payload['source_registry_update_worksheet'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal promotion checklist</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Decision</th><th>Operator step</th><th>Source ID</th><th>URL</th><th>Copy allowed</th><th>Copy target</th><th>Reason</th><th>Enabled</th><th>Registry action</th></tr></thead>
            <tbody>{render_source_proposal_promotion_checklist(payload['source_registry_proposal_promotion_checklist'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal draft</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Pack</th><th>Source ID</th><th>URL</th><th>Draft action</th><th>Duplicate warning</th><th>Freshness warning</th><th>Enabled</th><th>Registry action</th></tr></thead>
            <tbody>{render_source_proposal_draft(payload['source_registry_proposal_draft'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Guided source pack readiness</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pack</th><th>Status</th><th>Rows</th><th>Official</th><th>Cross-check</th><th>Duplicates</th><th>Cues</th><th>Top candidates</th><th>Next step</th></tr></thead>
            <tbody>{render_source_proposal_pack_readiness(payload['source_proposal_pack_readiness'])}</tbody>
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
    lines += ["", "## Render readiness", ""]
    lines.extend(
        f"- {item.get('rank') or '-'} | {item.get('band') or 'not_scored'} | score: {item.get('score') or '0'} | {item.get('title') or 'Untitled candidate'} | path: {item.get('recommended_path') or 'review'} | source: {item.get('source_cue') or 'n/a'} | assets: {item.get('asset_cue') or 'n/a'} | format: {item.get('format_cue') or 'n/a'} | manual: {item.get('manual_path') or 'n/a'} | blockers: {item.get('blockers') or 'none'} | next: {item.get('next_step') or 'review manually'}"
        for item in payload["render_readiness_queue"]
    )
    lines += ["", "## Render prep packets", ""]
    lines.extend(
        f"- {item.get('packet_status') or 'review'} | score: {item.get('render_readiness_score') or '0'} | {item.get('title') or 'Untitled'} | template: {item.get('template_fit') or 'review'} | shape: {item.get('template_shape') or 'review'} | artifact: render_prep_packets.md | gate: {item.get('approval_gate') or 'human review'}"
        for item in payload["render_prep_packets"]
    )
    handoff = payload["render_handoff_summary"]
    lines += ["", "## Top render handoff", ""]
    lines.extend(
        [
            f"- Status: {clean(handoff.get('handoff_status')) or 'not_created'}",
            f"- Story: {clean(handoff.get('title')) or 'none'}",
            f"- Folder: {clean(handoff.get('folder')) or 'render_handoff_top_packet'}",
            f"- Open first: {clean(handoff.get('readme')) or 'render_handoff_top_packet/README.md'}",
            "- Guardrails: review-only, no paid APIs, no auto-runs, no auto-rendering, no publishing.",
        ]
    )
    lines += ["", "## Content candidates", ""]
    lines.extend(
        f"- {item['type']} | {item['priority']} | {item['headline']} | {item['status']} | source: {item.get('source_grade') or 'not_scored'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'}"
        for item in payload["content_candidates"]
    )
    lines += ["", "## Lead promotion recommendations", ""]
    lines.extend(
        f"- {item['rank']} | {item['priority']} | {item['recommendation']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or '1'} source(s) | angle: {item.get('story_opportunity_angle') or 'review'} | path: {item.get('story_opportunity_recommended_path') or item.get('recommendation') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'review'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | target: {item['target']} | {item.get('next_step') or item.get('reason')}"
        for item in payload["lead_promotion_recommendations"]
    )
    lines += ["", "## Morning source discovery", ""]
    lines.extend(
        f"- {item['rank']} | {item['lane']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or 'n/a'} | angle: {item.get('story_opportunity_angle') or 'n/a'} | path: {item.get('story_opportunity_recommended_path') or item.get('promotion') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'n/a'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | {item['status']} | {item['posture']} | {item.get('next_action') or item.get('detail')}"
        for item in payload["source_discovery_board"]
    )
    readiness = payload["source_registry_readiness_summary"]
    lines += ["", "## Source registry readiness", ""]
    lines.extend(
        [
            f"- Status: {clean(readiness.get('readiness_status')) or 'review'}",
            f"- Next safest action: {clean(readiness.get('next_safest_action'))}",
            f"- Blockers: {clean(readiness.get('blockers')) or 'none'}",
            f"- Open first: {clean(readiness.get('open_first_file')) or 'trusted_registry_operator_playbook.md'}",
            f"- Playbook: {clean(readiness.get('support_file')) or 'trusted_registry_operator_playbook.md'}",
            f"- Focus: {clean(readiness.get('focus_source_ids')) or 'none'}",
            f"- Guardrail: {clean(readiness.get('guardrail'))}",
        ]
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
    lines += ["", "## Source registry diff review", ""]
    lines.extend(
        f"- {clean(item.get('diff_review_status')) or 'review'} | cue: {clean(item.get('resolution_action')) or 'review'} | {clean(item.get('resolution_label')) or 'Review'} | {clean(item.get('source_id'))} | flags: {clean(item.get('flags')) or 'none'} | issues: {clean(item.get('issues')) or 'none'} | registry domain: {clean(item.get('registry_domain_match')) or 'No'} | worksheet domain: {clean(item.get('worksheet_domain_match')) or 'No'} | rollback: {clean(item.get('rollback_status')) or 'missing'} | before log: {clean(item.get('verification_log_instruction')) or clean(item.get('recommendation')) or 'review before edit'}"
        for item in payload["source_registry_diff_review"]
    )
    lines += ["", "## Source registry same-domain resolution", ""]
    lines.extend(
        f"- {clean(item.get('same_domain_resolution_status')) or 'operator_input_required'} | decision: {clean(item.get('resolution_decision')) or 'operator fill-in'} | {clean(item.get('source_id'))} | domain: {clean(item.get('candidate_domain')) or 'n/a'} | compared: {clean(item.get('compared_existing_source_id')) or clean(item.get('compared_existing_url')) or 'operator fill-in'} | evidence: {clean(item.get('evidence_url')) or 'operator fill-in'} | gate: {clean(item.get('approval_gate')) or 'same_domain_ok_with_evidence_required_before_approval'}"
        for item in payload["source_registry_same_domain_resolution"]
    )
    lines += ["", "## Source verification log", ""]
    lines.extend(
        f"- {clean(item.get('verification_log_status')) or 'operator_input_required'} | cue: {clean(item.get('diff_resolution_action')) or 'review'} | {clean(item.get('source_id'))} | diff: {clean(item.get('diff_review_status')) or 'review'} | instruction: {clean(item.get('diff_resolution_instruction')) or 'follow diff review cue'} | url_checked: {clean(item.get('url_checked')) or 'operator fill-in'} | freshness: {clean(item.get('freshness_result')) or 'operator fill-in'} | duplicate: {clean(item.get('duplicate_decision')) or 'operator fill-in'} | outcome: {clean(item.get('approval_outcome')) or 'operator fill-in'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_verification_log"]
    )
    lines += ["", "## Source registry approval packet", ""]
    lines.extend(
        f"- {clean(item.get('approval_packet_status')) or 'review'} | {clean(item.get('source_id'))} | evidence: {clean(item.get('evidence_url')) or 'missing'} | freshness: {clean(item.get('freshness_result')) or 'missing'} | duplicate: {clean(item.get('duplicate_decision')) or 'missing'} | hold: {clean(item.get('hold_reason')) or 'none'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_approval_packet"]
    )
    lines += ["", "## Source registry patch preview", ""]
    lines.extend(
        f"- {clean(item.get('patch_preview_status')) or 'review'} | {clean(item.get('source_id'))} | target: {clean(item.get('manual_edit_target')) or 'config/source_registry.json'} | hold: {clean(item.get('hold_reason')) or 'none'} | evidence: {clean(item.get('evidence_url')) or 'missing'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_patch_preview"]
    )
    lines += ["", "## Source registry post-edit validation", ""]
    lines.extend(
        f"- {clean(item.get('post_edit_validation_status')) or 'review'} | {clean(item.get('source_id'))} | exact: {clean(item.get('exact_match')) or 'No'} | enabled: {clean(item.get('enabled_status')) or 'missing'} | drift: {clean(item.get('drift_fields')) or 'none'} | unsafe: {clean(item.get('unsafe_flags')) or 'none'}"
        for item in payload["source_registry_post_edit_validation"]
    )
    lines += ["", "## Source registry update worksheet", ""]
    lines.extend(
        f"- {clean(item.get('worksheet_decision')) or 'review'} | {clean(item.get('source_id'))} | target: {clean(item.get('manual_edit_target')) or 'config/source_registry.json'} | edit: {clean(item.get('manual_edit_allowed')) or 'manual review only'} | enabled: {clean(item.get('proposed_enabled')) or 'False'} | auto: {clean(item.get('auto_edit_status')) or 'not_performed_by_generator'} | rollback: {clean(item.get('rollback_note')) or 'remove manual source object if review fails'}"
        for item in payload["source_registry_update_worksheet"]
    )
    lines += ["", "## Source proposal promotion checklist", ""]
    lines.extend(
        f"- {clean(item.get('checklist_decision')) or 'review'} | {clean(item.get('candidate_source_id'))} | step: {clean(item.get('operator_step')) or 'review'} | copy: {clean(item.get('copy_allowed')) or 'No'} | target: {clean(item.get('copy_target')) or 'none'} | reason: {clean(item.get('hold_reason')) or clean(item.get('discard_reason')) or clean(item.get('freshness_warning')) or 'manual review'} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | registry: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'}"
        for item in payload["source_registry_proposal_promotion_checklist"]
    )
    lines += ["", "## Source proposal draft", ""]
    lines.extend(
        f"- {clean(item.get('draft_selection_status')) or 'review'} | {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('candidate_source_id'))} | action: {clean(item.get('draft_action'))} | duplicate: {clean(item.get('duplicate_warning')) or 'none'} | freshness: {clean(item.get('freshness_warning')) or 'open manually'} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | registry: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'}"
        for item in payload["source_registry_proposal_draft"]
    )
    lines += ["", "## Guided source pack readiness", ""]
    lines.extend(
        f"- {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('readiness_status')) or 'review'} | rows: {clean(item.get('candidate_rows')) or '0'} | official: {clean(item.get('official_candidates')) or '0'} | cross-check: {clean(item.get('cross_check_candidates')) or '0'} | duplicates: {clean(item.get('duplicate_candidates')) or '0'} | cues: {clean(item.get('review_cues')) or 'none'} | top: {clean(item.get('top_candidate_ids')) or 'none'} | next: {clean(item.get('next_step')) or 'review manually'}"
        for item in payload["source_proposal_pack_readiness"]
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


def render_render_prep_packets_markdown(payload: Dict[str, Any]) -> str:
    packets = payload.get("render_prep_packets", [])
    lines = [
        "# HSD Render Prep Packets",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Command center version: {payload['version']}",
        "",
        "## Guardrails",
        "",
        "- Review-only packet. It does not render files.",
        "- Publishing remains off.",
        "- Paid APIs remain disabled.",
        "- Human visual review is required before any post.",
        "",
        "## Summary",
        "",
        f"- Packet rows: {len(packets)}",
        f"- Ready for manual render review: {sum(1 for row in packets if row.get('packet_status') == 'ready_for_manual_render_review')}",
        "",
    ]
    if not packets:
        lines += [
            "## No Packets",
            "",
            "No render-ready or render-prep candidates cleared the source, asset, format, and manual-path gates.",
            "",
        ]
        return "\n".join(lines).rstrip() + "\n"

    for index, packet in enumerate(packets, 1):
        steps = [step.strip() for step in clean(packet.get("manual_renderer_steps")).split("|") if step.strip()]
        lines += [
            f"## Packet {index}: {clean(packet.get('title'))}",
            "",
            f"- Packet ID: `{clean(packet.get('packet_id'))}`",
            f"- Status: `{clean(packet.get('packet_status'))}`",
            f"- Readiness: `{clean(packet.get('render_readiness_score'))}/100` / `{clean(packet.get('render_readiness_band'))}`",
            f"- Recommended path: `{clean(packet.get('recommended_path'))}`",
            f"- Source artifact: `{clean(packet.get('source_artifact'))}`",
            f"- Template fit: `{clean(packet.get('template_fit'))}`",
            f"- Template shape: `{clean(packet.get('template_shape'))}`",
            f"- Renderer family: `{clean(packet.get('renderer_family'))}`",
            f"- Asset requirement: {clean(packet.get('asset_requirement'))}",
            f"- Approval gate: `{clean(packet.get('approval_gate'))}`",
            f"- Auto-render status: `{clean(packet.get('auto_render_status'))}`",
            f"- Publish policy: `{clean(packet.get('publish_policy'))}`",
            "",
            "### Copy Fields",
            "",
            f"- Headline: {clean(packet.get('copy_headline'))}",
            f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
            f"- Source detail: {clean(packet.get('source_detail')) or 'n/a'}",
            "",
            "### Manual Renderer Steps",
            "",
        ]
        lines.extend(f"{step_index}. {step}" for step_index, step in enumerate(steps, 1))
        lines += ["", "---", ""]
    return "\n".join(lines).rstrip() + "\n"


def write_render_prep_outputs(payload: Dict[str, Any]) -> None:
    packets = payload.get("render_prep_packets", [])
    write_csv(OUT_RENDER_PREP_CSV, packets, RENDER_PREP_FIELDS)
    write_json(
        OUT_RENDER_PREP_JSON,
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "guardrails": {
                "review_only": True,
                "auto_render": False,
                "auto_publish": False,
                "paid_apis": False,
            },
            "counts": {
                "packets": len(packets),
                "ready_for_manual_render_review": sum(
                    1 for row in packets if row.get("packet_status") == "ready_for_manual_render_review"
                ),
            },
            "packets": packets,
        },
    )
    write_text(OUT_RENDER_PREP_MD, render_render_prep_packets_markdown(payload))


def write_outputs(payload: Dict[str, Any]) -> None:
    write_render_prep_outputs(payload)
    write_render_handoff_outputs(payload)
    write_json(OUT_JSON, payload)
    write_text(OUT_MD, render_markdown(payload))
    write_text(OUT_HTML, render_html(payload))


def main() -> None:
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps({"version": VERSION, "html": OUT_HTML.as_posix(), "actions": len(payload["next_actions"])}, indent=2))


if __name__ == "__main__":
    main()
