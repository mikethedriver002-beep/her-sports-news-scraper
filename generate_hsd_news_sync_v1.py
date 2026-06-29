from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from hsd_run_io import input_candidates, input_path, output_path, write_json as write_run_json, write_text as write_run_text


VERSION = "news-sync-v1.9.9-breaking-confirmation-row-cues"

INPUT_RESULTS_QUEUE = os.environ.get("HSD_RESULTS_GRAPHICS_QUEUE", "results_graphics_queue.md")
INPUT_RESULTS_RECS = os.environ.get("HSD_RESULTS_RECOMMENDATIONS", "daily_results_recommendations.md")
INPUT_WNBA_BOX = os.environ.get("HSD_WNBA_BOX_SUMMARY", "wnba_box_score_summary.md")
INPUT_RESULTS_HUB = os.environ.get("HSD_RESULTS_HUB", "results_system_hub.md")
INPUT_RESULTS_TOP_CSV = os.environ.get("HSD_RESULTS_TOP_CSV", "top_womens_results.csv")
INPUT_RESULTS_RECONCILED_CSV = os.environ.get("HSD_RESULTS_RECONCILED_CSV", "reconciled_events.csv")
INPUT_RESULTS_FINALS_CSV = os.environ.get("HSD_RESULTS_FINALS_CSV", "today_final_results.csv")
INPUT_GAME_INTELLIGENCE_CSV = os.environ.get("HSD_GAME_INTELLIGENCE_BOARD", "game_intelligence_board_v1.csv")
INPUT_STATS_EVIDENCE_CSV = os.environ.get("HSD_STATS_EVIDENCE_GAP_BOARD", "stats_evidence_gap_board_v1.csv")
INPUT_FINAL_SCORE_STAT_PROOF_CSV = os.environ.get("HSD_FINAL_SCORE_STAT_PROOF", "final_score_stat_proof_v1.csv")
INPUT_FINAL_SCORE_STAT_PROOF_CONFIRMATION_CSV = os.environ.get(
    "HSD_FINAL_SCORE_STAT_PROOF_CONFIRMATION_INTAKE",
    "final_score_stat_proof_confirmation_intake_v1.csv",
)
INPUT_FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_CSV = os.environ.get(
    "HSD_FINAL_SCORE_STAT_PROOF_REVIEW_ORDER",
    "final_score_stat_proof_review_order_v1.csv",
)
INPUT_GAME_FACT_CONFIRMATION_STATUS_CSV = os.environ.get(
    "HSD_GAME_FACT_CONFIRMATION_STATUS",
    "game_fact_confirmation_status_v1.csv",
)
INPUT_STORY_PROOF_CARD_CSV = os.environ.get(
    "HSD_STORY_PROOF_CARD",
    "story_proof_card_v1.csv",
)
FINAL_SCORE_STAT_PROOF_REVIEW_WALKTHROUGH_MD = "final_score_stat_proof_review_walkthrough_v1.md"

SOURCE_REGISTRY_FILE = os.environ.get("HSD_NEWS_SOURCE_REGISTRY", "news_source_registry.json")
ANGLE_RULES_FILE = os.environ.get("HSD_NEWS_ANGLE_RULES", "news_angle_rules.json")

MAX_MUST_POST = int(os.environ.get("HSD_NEWS_MAX_MUST_POST", "5"))
MAX_STRONG_MAYBE = int(os.environ.get("HSD_NEWS_MAX_STRONG_MAYBE", "5"))
MAX_DIVERSITY_PROMOTIONS = int(os.environ.get("HSD_NEWS_MAX_DIVERSITY_PROMOTIONS", "4"))
MAX_SOCCER_DIVERSITY = int(os.environ.get("HSD_NEWS_MAX_SOCCER_DIVERSITY", "3"))
FETCH_TIMEOUT = int(os.environ.get("HSD_NEWS_FETCH_TIMEOUT", "15"))
REQUEST_SLEEP_SECONDS = float(os.environ.get("HSD_NEWS_REQUEST_SLEEP_SECONDS", "0.35"))
ENABLE_FETCH = os.environ.get("HSD_NEWS_ENABLE_FETCH", "true").lower() != "false"

NEWS_CANDIDATES_CSV = "news_candidate_queue.csv"
NEWS_SOURCE_OBS_CSV = "news_source_observations.csv"
NEWS_FACT_PACKETS_CSV = "news_fact_packets.csv"
NEWS_BRIEF_QUEUE_MD = "news_brief_queue.md"
NEWS_SOCIAL_PACKETS_MD = "news_social_packets.md"
NEWS_GRAPHICS_HANDOFF_MD = "news_graphics_handoff.md"
NEWS_DAILY_PLAN_MD = "news_daily_plan.md"
NEWS_MANUAL_REVIEW_CSV = "news_manual_review_queue.csv"
BREAKING_PUBLIC_SIGNAL_CSV = "breaking_public_signal_queue.csv"
BREAKING_PUBLIC_SIGNAL_MD = "breaking_public_signal_queue.md"
BREAKING_PUBLIC_SIGNAL_JSON = "breaking_public_signal_manifest.json"
BREAKING_CONFIRMATION_INTAKE_CSV = "breaking_public_signal_confirmation_intake.csv"
BREAKING_CONFIRMATION_INTAKE_MD = "breaking_public_signal_confirmation_intake.md"
BREAKING_SIGNAL_CLUSTERS_CSV = "breaking_public_signal_clusters.csv"
BREAKING_SIGNAL_CLUSTERS_MD = "breaking_public_signal_clusters.md"
BREAKING_SIGNAL_NEXT_ACTION_CSV = "breaking_public_signal_next_action_v1.csv"
BREAKING_SIGNAL_NEXT_ACTION_MD = "breaking_public_signal_next_action_v1.md"
BREAKING_SIGNAL_NEXT_ACTION_JSON = "breaking_public_signal_next_action_v1.json"
BREAKING_SIGNAL_RETURN_SUMMARY_CSV = "breaking_public_signal_return_summary_v1.csv"
BREAKING_SIGNAL_RETURN_SUMMARY_MD = "breaking_public_signal_return_summary_v1.md"
BREAKING_SIGNAL_RETURN_SUMMARY_JSON = "breaking_public_signal_return_summary_v1.json"
GAME_SOURCE_CONFIRMATION_BRIDGE_CSV = "game_source_confirmation_bridge_v1.csv"
GAME_SOURCE_CONFIRMATION_BRIDGE_MD = "game_source_confirmation_bridge_v1.md"
GAME_SOURCE_CONFIRMATION_BRIDGE_JSON = "game_source_confirmation_bridge_v1.json"
NEWS_SYNC_HUB_MD = "news_sync_hub.md"
NEWS_MANIFEST_JSON = "news_sync_manifest.json"
NEWS_INPUT_STATUS_CSV = "news_input_status_report.csv"
NEWS_SETUP_ERROR_MD = "news_setup_error.md"

USER_AGENT = "Mozilla/5.0 (compatible; HerSportsDailyNewsSync/1.0; +https://hersportsdaily.example)"


CANDIDATE_FIELDS = [
    "run_id", "candidate_id", "queue_section", "content_action", "sport", "league",
    "editorial_tier", "editorial_bucket", "template", "selected_source", "all_sources",
    "confidence", "manual_review", "editorial_rank", "outcome_type", "matchup",
    "final_score", "winner", "loser", "game_status", "date", "source_url",
    "graphics_headline", "graphics_subhead", "slide1_hook", "slide2_result",
    "slide3_context", "slide4_cta", "raw_block",
    "event_date",
    "event_datetime",
    "result_date",
    "freshness_label",
    "freshness_source",
    "source_run_timestamp",
    "event_date_confidence"
]

SOURCE_OBS_FIELDS = [
    "run_id", "candidate_id", "source_id", "source_name", "source_priority",
    "source_type", "url", "domain", "fetch_status", "http_status", "title",
    "description", "matched_terms", "published_hint", "usable_context",
    "context_signal", "source_trust_band", "publish_use", "fetched_at_utc", "review_flag", "notes",
]

PACKET_FIELDS = [
    "run_id", "candidate_id", "queue_section", "sport", "league", "editorial_bucket",
    "content_family", "publish_recommendation", "urgency", "headline", "dek",
    "brief_120w", "caption_hard_fact", "caption_voice", "story_text",
    "slide3_context", "graphics_handoff", "source_count", "primary_source_count",
    "source_confidence_score", "source_confidence_tier", "source_publish_grade",
    "source_confidence_reason",
    "source_urls_json", "context_signal", "top_performers", "review_flags",
    "context_quality", "quality_score", "production_ready",
    "content_format_recommendation", "result_record_source",
    "manual_review", "score_accuracy_check", "rights_safe_note",
    "event_date",
    "event_datetime",
    "result_date",
    "freshness_label",
    "freshness_source",
    "source_run_timestamp",
    "event_date_confidence",
    "event_date_required"
]

BREAKING_PUBLIC_SIGNAL_FIELDS = [
    "run_id", "candidate_id", "headline", "sport", "league", "queue_section",
    "breaking_score", "urgency_band", "why_urgent", "source_confidence_score",
    "source_confidence_tier", "source_publish_grade", "source_confidence_reason",
    "public_signal_status", "public_signal_confidence", "public_signal_count",
    "public_signal_summary", "signal_timestamp_utc", "source_urls",
    "source_domains", "retrieval_method", "limitations", "human_review_cue",
    "manual_review_required", "review_only", "publish_ready", "auto_publish",
    "auto_source_enablement", "approval_state_change",
]

BREAKING_CONFIRMATION_INTAKE_FIELDS = [
    "confirmation_id", "run_id", "candidate_id", "headline", "urgency_band",
    "breaking_score", "required_confirmation_type", "confirmation_status",
    "source_confidence_tier", "source_publish_grade", "public_signal_status",
    "public_signal_confidence", "source_domains", "source_urls",
    "official_source_search_hint", "wire_source_search_hint",
    "operator_checked_url", "operator_checked_domain",
    "operator_confirmation_result", "operator_confirmed_at_utc",
    "operator_notes", "limitations", "manual_review_required", "review_only",
    "publish_ready", "auto_publish", "auto_source_enablement",
    "approval_state_change",
]

BREAKING_SIGNAL_CLUSTER_FIELDS = [
    "cluster_id", "run_id", "cluster_headline", "story_count", "candidate_ids",
    "urgency_band", "max_breaking_score", "official_confirmation_status",
    "matching_official_evidence_status", "matching_official_evidence_count",
    "matching_official_evidence_sources", "matching_official_evidence_urls",
    "matching_official_evidence_artifacts", "manual_confirmation_gap",
    "exact_source_or_intake_row_to_open",
    "score_stat_proof_status", "named_player_stat_proof_count",
    "named_player_stat_proof_examples", "score_stat_proof_source_urls",
    "score_stat_proof_artifacts", "score_stat_manual_confirmation_cue",
    "exact_score_stat_proof_row_or_source_to_open",
    "breaking_claim_confirmation_target", "score_proof_confirmation_target",
    "named_player_stat_proof_confirmation_targets",
    "score_stat_confirmation_status", "exact_human_confirmation_next_action",
    "score_stat_review_order_status", "score_stat_review_order_targets",
    "first_score_stat_review_order_target", "score_stat_review_walkthrough_target",
    "exact_review_walkthrough_next_action",
    "corroboration_ladder_status", "corroboration_ladder_summary",
    "official_source_corroboration", "reputable_source_corroboration",
    "public_signal_corroboration", "missing_confirmation_cue",
    "corroboration_evidence_urls",
    "urgency_review_reason", "source_proof_readiness_status",
    "source_proof_readiness_summary", "story_proof_card_target",
    "game_fact_confirmation_target", "source_proof_readiness_next_action",
    "verification_priority_status", "verification_priority_summary",
    "verification_priority_target", "verification_priority_next_action",
    "public_signal_limitations_cue",
    "game_source_confirmation_tier", "game_source_confirmation_limitations",
    "game_source_confirmation_tier_target", "game_source_confirmation_tier_cue",
    "game_source_freshness_status", "game_source_freshness_age_minutes",
    "game_source_retrieved_at_utc", "game_source_freshness_note",
    "game_source_freshness_target", "game_source_freshness_cue",
    "source_diversity", "source_domain_count", "source_domains", "source_urls",
    "public_signal_count", "public_signal_confidence", "freshness_status",
    "oldest_signal_timestamp_utc", "newest_signal_timestamp_utc",
    "limitations", "exact_manual_next_action", "manual_review_required",
    "review_only", "publish_ready", "auto_publish", "auto_source_enablement",
    "approval_state_change",
]

BREAKING_SIGNAL_NEXT_ACTION_FIELDS = [
    "action_rank", "cluster_id", "cluster_headline", "urgency_band",
    "review_priority", "verification_priority_status",
    "confirmation_state", "official_reputable_gray_area_cue",
    "source_confirmation_tier", "source_freshness_status",
    "source_freshness_age_minutes", "source_domain_lead",
    "why_story_looks_urgent", "source_confidence_tier",
    "source_confidence_reason", "signal_timestamp_utc", "retrieval_method",
    "public_signal_type", "public_signal_confidence", "public_signal_count",
    "public_signal_limitations_cue", "confirmation_gap",
    "evidence_urls", "source_or_intake_row_to_open",
    "freshness_or_proof_row_to_open", "manual_confirmation_artifact",
    "manual_confirmation_row_ref", "manual_confirmation_target",
    "manual_return_fields_to_complete", "manual_return_operator_checked_url",
    "manual_return_operator_confirmation_result",
    "manual_return_operator_confirmed_at_utc", "manual_return_operator_notes",
    "manual_return_guardrail_cue",
    "operator_next_action", "review_limitations",
    "review_only", "approval_state_change", "source_enablement",
    "publish_action",
]

BREAKING_SIGNAL_RETURN_SUMMARY_FIELDS = [
    "summary_rank", "cluster_id", "cluster_headline", "review_priority",
    "verification_priority_status", "manual_confirmation_artifact",
    "manual_confirmation_row_ref", "operator_checked_url_present",
    "operator_confirmation_result_present", "operator_confirmed_at_utc_present",
    "operator_notes_present", "source_confidence_tier_present",
    "source_domain_lead_present", "manual_return_status",
    "missing_return_fields", "manual_next_step",
    "source_or_intake_row_to_open", "freshness_or_proof_row_to_open",
    "review_only", "approval_state_change", "source_enablement",
    "publish_action",
]

GAME_SOURCE_CONFIRMATION_BRIDGE_FIELDS = [
    "bridge_id", "run_id", "game_row_ref", "game_date", "league", "matchup",
    "final_score", "recap_candidate", "official_free_game_evidence_status",
    "game_source_url", "game_source_domain", "stats_evidence_status",
    "stats_row_ref", "stats_source_url", "top_performers",
    "cross_signal_status", "cluster_row_ref", "news_packet_ref",
    "news_or_cluster_source_urls", "manual_confirmation_needed",
    "exact_next_row_or_source_to_open", "operator_confirmation_target",
    "limitations", "manual_review_required", "review_only", "publish_ready",
    "auto_publish", "auto_source_enablement", "approval_state_change",
]

INPUT_STATUS_FIELDS = [
    "input_name", "resolved_path", "exists", "size_bytes", "line_count",
    "has_result_graphic", "has_must_post", "has_strong_maybe", "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value: Any) -> str:
    return clean(value).lower()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]



def parse_event_datetime(value: Any) -> Optional[datetime]:
    s = clean(value)
    if not s:
        return None
    s2 = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s2)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    patterns = [
        r"\b(20\d{2})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?\b",
        r"\b(\d{1,2})/(\d{1,2})/(20\d{2})(?:[ T](\d{1,2}):(\d{2}))?\b",
    ]
    m = re.search(patterns[0], s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm, ss = int(m.group(4) or 12), int(m.group(5) or 0), int(m.group(6) or 0)
        return datetime(y, mo, d, hh, mm, ss, tzinfo=timezone.utc)
    m = re.search(patterns[1], s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm = int(m.group(4) or 12), int(m.group(5) or 0)
        return datetime(y, mo, d, hh, mm, tzinfo=timezone.utc)
    return None


def event_date_payload(row: Dict[str, Any]) -> Dict[str, str]:
    """
    Produce a clear event-date payload for every candidate/packet.

    The goal is not to guess stale content into freshness. The goal is to
    carry the actual event date from Results Desk CSVs into News Sync and
    Studio Bridge so Asset Visual QA can prove freshness.
    """
    raw = row.get("raw_block", "")
    raw_json: Dict[str, Any] = {}
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            raw_json = json.loads(raw)
        except Exception:
            raw_json = {}

    keys = [
        "event_datetime", "event_date", "result_date", "scheduled_datetime_local",
        "scheduled_date_local", "game_datetime", "game_date", "start_time",
        "date_utc", "date", "played_at", "completed_at"
    ]

    source = ""
    dt: Optional[datetime] = None
    for key in keys:
        for obj_name, obj in [("candidate", row), ("raw_record", raw_json)]:
            value = obj.get(key) if isinstance(obj, dict) else ""
            dt = parse_event_datetime(value)
            if dt:
                source = f"{obj_name}.{key}"
                break
        if dt:
            break

    if not dt:
        source_hint = " ".join([clean(row.get("_result_record_source")), clean(row.get("result_record_source")), clean(row.get("status_norm")), clean(row.get("game_status"))]).lower()
        if any(token in source_hint for token in ["top_womens", "today_final", "reconciled", "final"]):
            dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
            return {
                "event_date": dt.date().isoformat(),
                "event_datetime": dt.isoformat(),
                "result_date": dt.date().isoformat(),
                "freshness_label": "run_date_fallback",
                "freshness_source": "news_sync_run_date_fallback",
                "source_run_timestamp": utc_now(),
                "event_date_confidence": "run_date_fallback",
            }
        return {
            "event_date": "",
            "event_datetime": "",
            "result_date": "",
            "freshness_label": "missing_event_date",
            "freshness_source": "",
            "source_run_timestamp": utc_now(),
            "event_date_confidence": "missing",
        }

    event_date = dt.date().isoformat()
    return {
        "event_date": event_date,
        "event_datetime": dt.isoformat(),
        "result_date": event_date,
        "freshness_label": "dated_result",
        "freshness_source": source,
        "source_run_timestamp": utc_now(),
        "event_date_confidence": "exact_from_results_record" if source.startswith("raw_record") else "candidate_field",
    }


def apply_event_date_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = event_date_payload(row)
    for k, v in payload.items():
        if not clean(row.get(k)):
            row[k] = v
    return row


def load_json(path: str, default: Any) -> Any:
    p = input_path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def candidate_input_paths(path: str) -> List[Path]:
    """
    News Sync searches current run outputs, latest local artifacts, root outputs,
    and archived results outputs in freshness order.

    This avoids local mode attaching stale root-level results after the runner
    has already collected a fresher Results Desk run under outputs/local/latest.
    """
    p = Path(path)
    if p.is_absolute():
        return [p]

    names: List[Path] = []
    run_root = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_root:
        names.append(Path(run_root) / p)
    names.append(Path("outputs") / "local" / "latest" / "files" / p)
    names.extend(input_candidates(path))
    if not p.is_absolute():
        names.extend([
            Path("results_run_history") / "latest" / path,
            Path("results_run_history") / "latest" / p.name,
            Path("results_run_history") / p.name,
        ])

    deduped: List[Path] = []
    seen = set()
    for candidate in names:
        key = candidate.as_posix()
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def resolve_input(path: str) -> Tuple[Path, str]:
    for p in candidate_input_paths(path):
        if p.exists() and p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                text = p.read_text(encoding="utf-8", errors="replace")
            return p, text
    return input_path(path), ""


def read_text(path: str) -> str:
    _, txt = resolve_input(path)
    return txt


def input_status_row(input_name: str, path: str, text_value: str, resolved_path: Path) -> Dict[str, Any]:
    exists = resolved_path.exists() and resolved_path.is_file()
    return {
        "input_name": input_name,
        "resolved_path": resolved_path.as_posix(),
        "exists": "Yes" if exists else "No",
        "size_bytes": resolved_path.stat().st_size if exists else 0,
        "line_count": len(text_value.splitlines()) if text_value else 0,
        "has_result_graphic": "Yes" if "## RESULT GRAPHIC" in text_value else "No",
        "has_must_post": "Yes" if "MUST POST" in text_value or "## Make First" in text_value else "No",
        "has_strong_maybe": "Yes" if "STRONG MAYBE" in text_value or "## Strong Maybe" in text_value else "No",
        "notes": "",
    }


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            out = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                out[field] = value
            w.writerow(out)


def parse_key_value_line(line: str) -> Tuple[str, str]:
    line = line.strip()
    line = re.sub(r"^\*\*", "", line)
    line = re.sub(r"\*\*$", "", line)
    if ":" not in line:
        return "", ""
    k, v = line.split(":", 1)
    k = k.replace("**", "").strip().lower()
    v = v.replace("**", "").strip()
    return k, v


def infer_queue_section_from_fields(row: Dict[str, Any]) -> str:
    section = clean(row.get("queue_section"))
    if section:
        upper = section.upper()
        if "DIVERSITY" in upper:
            return "DIVERSITY WATCH"
        if "MUST" in upper or "MAKE FIRST" in upper:
            return "MUST POST"
        if "STRONG" in upper:
            return "STRONG MAYBE"
        if "WATCH" in upper:
            return "WATCHLIST"

    bucket = clean(row.get("editorial_bucket")).lower()
    action = clean(row.get("content_action")).lower()

    if "diversity" in bucket or "diversity" in action:
        return "DIVERSITY WATCH"
    if "must" in bucket or "make first" in action:
        return "MUST POST"
    if "strong" in bucket or "strong maybe" in action:
        return "STRONG MAYBE"
    if "watch" in bucket or "watch" in action:
        return "WATCHLIST"
    return ""


def extract_final_score_from_text(text_value: str) -> str:
    text_value = clean(text_value)
    if not text_value:
        return ""

    patterns = [
        r"Final:\s*([^|\\n\\.]+?\\b\\d+\\s*-\\s*[^|\\n\\.]+?\\b\\d+)",
        r"final listed as\s*([^|\\n\\.]+?\\b\\d+\\s*-\\s*[^|\\n\\.]+?\\b\\d+)",
        r"Caption seed:.*?,\\s*([^|\\n\\.]+?\\b\\d+\\s*-\\s*[^|\\n\\.]+?\\b\\d+)",
        r"Verified final:\\s*([^|\\n\\.]+?\\b\\d+\\s*-\\s*[^|\\n\\.]+?\\b\\d+)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text_value, flags=re.I)
        if m:
            return clean(m.group(1)).rstrip(".")
    return ""


def infer_winner_loser_from_headline(headline: str) -> Tuple[str, str]:
    m = re.match(r"(.+?)\\s+beat\\s+(.+)$", clean(headline), flags=re.I)
    if m:
        return clean(m.group(1)), clean(m.group(2))
    return "", ""


def normalize_candidate_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    row["queue_section"] = infer_queue_section_from_fields(row)

    if not clean(row.get("final_score")):
        row["final_score"] = extract_final_score_from_text(" ".join([
            row.get("graphics_subhead", ""),
            row.get("slide2_result", ""),
            row.get("slide3_context", ""),
            row.get("raw_block", ""),
        ]))

    if not clean(row.get("winner")) or not clean(row.get("loser")):
        winner, loser = infer_winner_loser_from_headline(row.get("graphics_headline", ""))
        row["winner"] = clean(row.get("winner")) or winner
        row["loser"] = clean(row.get("loser")) or loser

    if not clean(row.get("outcome_type")) and clean(row.get("winner")) and clean(row.get("loser")):
        row["outcome_type"] = "win"

    if not clean(row.get("matchup")) and clean(row.get("winner")) and clean(row.get("loser")):
        row["matchup"] = f"{row.get('winner')} vs {row.get('loser')}"

    row = apply_event_date_payload(row)
    return row



def load_csv_rows_from_path(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def resolve_csv_input(path: str) -> Tuple[Path, List[Dict[str, str]]]:
    for p in candidate_input_paths(path):
        rows = load_csv_rows_from_path(p)
        if rows:
            return p, rows
    return input_path(path), []


def input_status_row_csv(input_name: str, path: str, rows: List[Dict[str, str]], resolved_path: Path) -> Dict[str, Any]:
    exists = resolved_path.exists() and resolved_path.is_file()
    notes = ""
    if rows:
        notes = f"Loaded {len(rows)} CSV rows."
    elif exists:
        notes = "CSV exists but loaded 0 rows."
    else:
        notes = "CSV not found."
    return {
        "input_name": input_name,
        "resolved_path": resolved_path.as_posix(),
        "exists": "Yes" if exists else "No",
        "size_bytes": resolved_path.stat().st_size if exists else 0,
        "line_count": len(rows) + (1 if rows else 0),
        "has_result_graphic": "No",
        "has_must_post": "Yes" if any("must" in clean(r.get("editorial_bucket", "")).lower() or "make first" in clean(r.get("content_action", "")).lower() for r in rows) else "No",
        "has_strong_maybe": "Yes" if any("strong" in clean(r.get("editorial_bucket", "")).lower() or "strong" in clean(r.get("content_action", "")).lower() for r in rows) else "No",
        "notes": notes,
    }


def result_record_final_score(record: Dict[str, str]) -> str:
    for key in ["final_score_display", "final_score", "score_display", "score"]:
        if clean(record.get(key)):
            return clean(record.get(key))

    away_team = clean(record.get("away_team_display") or record.get("away_team_raw") or record.get("away_team_norm"))
    home_team = clean(record.get("home_team_display") or record.get("home_team_raw") or record.get("home_team_norm"))
    away_score = clean(record.get("away_score"))
    home_score = clean(record.get("home_score"))
    if away_team and home_team and away_score and home_score:
        return f"{away_team} {away_score} - {home_team} {home_score}"
    if away_score and home_score:
        return f"{away_score}-{home_score}"
    return ""


def result_record_headline(record: Dict[str, str]) -> str:
    return clean(
        record.get("graphics_headline")
        or record.get("headline")
        or record.get("caption_seed")
        or record.get("matchup")
    )


def token_set(value: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9']+", clean(value).lower())
    return {t for t in tokens if len(t) >= 3 and t not in {"the", "and", "beat", "draw", "with", "final"}}


def result_record_match_score(candidate: Dict[str, Any], record: Dict[str, str]) -> int:
    cand_blob = " ".join([
        candidate.get("graphics_headline", ""),
        candidate.get("matchup", ""),
        candidate.get("winner", ""),
        candidate.get("loser", ""),
        candidate.get("league", ""),
    ])
    rec_blob = " ".join([
        result_record_headline(record),
        record.get("matchup", ""),
        record.get("winner", ""),
        record.get("loser", ""),
        record.get("home_team_display", ""),
        record.get("away_team_display", ""),
        record.get("home_team_norm", ""),
        record.get("away_team_norm", ""),
        record.get("league_norm", ""),
    ])

    c = token_set(cand_blob)
    r = token_set(rec_blob)
    if not c or not r:
        return 0

    overlap = len(c & r)
    score = overlap * 10

    if clean(candidate.get("graphics_headline")).lower() == result_record_headline(record).lower():
        score += 100
    if clean(candidate.get("date")) and clean(record.get("scheduled_date_local")) and clean(candidate.get("date")) == clean(record.get("scheduled_date_local")):
        score += 15
    if clean(candidate.get("sport")).lower() and clean(candidate.get("sport")).lower() == clean(record.get("sport_norm")).lower():
        score += 10
    if result_record_final_score(record):
        score += 8
    return score


def best_result_record(candidate: Dict[str, Any], records: List[Dict[str, str]]) -> Tuple[Optional[Dict[str, str]], int]:
    best = None
    best_score = 0
    for record in records:
        score = result_record_match_score(candidate, record)
        if score > best_score:
            best = record
            best_score = score
    if best_score >= 25:
        return best, best_score
    return None, best_score


def enrich_candidate_from_record(candidate: Dict[str, Any], record: Dict[str, str], source_name: str) -> Dict[str, Any]:
    candidate = dict(candidate)

    final_score = result_record_final_score(record)
    if final_score:
        candidate["final_score"] = final_score

    for src_key, dest_key in [
        ("sport_norm", "sport"),
        ("league_norm", "league"),
        ("editorial_bucket", "editorial_bucket"),
        ("content_action", "content_action"),
        ("content_family", "content_family"),
        ("posting_priority", "posting_priority"),
        ("confidence", "confidence"),
        ("editorial_rank", "editorial_rank"),
        ("outcome_type", "outcome_type"),
        ("winner", "winner"),
        ("loser", "loser"),
        ("source_url", "source_url"),
        ("scheduled_date_local", "date"),
        ("scheduled_date_local", "event_date"),
        ("scheduled_datetime_local", "event_datetime"),
        ("event_date", "event_date"),
        ("event_datetime", "event_datetime"),
        ("result_date", "result_date"),
        ("date_utc", "event_datetime"),
    ]:
        if clean(record.get(src_key)) and not clean(candidate.get(dest_key)):
            candidate[dest_key] = clean(record.get(src_key))

    headline = result_record_headline(record)
    if headline and not clean(candidate.get("graphics_headline")):
        candidate["graphics_headline"] = headline

    if not clean(candidate.get("matchup")):
        away = clean(record.get("away_team_display") or record.get("away_team_norm"))
        home = clean(record.get("home_team_display") or record.get("home_team_norm"))
        if away and home:
            candidate["matchup"] = f"{away} vs {home}"

    if clean(record.get("caption_seed")) and not clean(candidate.get("graphics_subhead")):
        candidate["graphics_subhead"] = clean(record.get("caption_seed"))

    candidate["result_record_source"] = source_name
    return normalize_candidate_fields(candidate)


def enrich_candidates_from_result_csvs(candidates: List[Dict[str, Any]], csv_sources: List[Tuple[str, List[Dict[str, str]]]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, str]] = []
    source_by_id: Dict[int, str] = {}
    for source_name, rows in csv_sources:
        for row in rows:
            records.append(row)
            source_by_id[id(row)] = source_name

    if not records:
        return candidates

    enriched = []
    for candidate in candidates:
        record, score = best_result_record(candidate, records)
        if record:
            enriched.append(enrich_candidate_from_record(candidate, record, source_by_id.get(id(record), "results_csv")))
        else:
            enriched.append(normalize_candidate_fields(candidate))
    return enriched



def result_unique_key_from_record(record: Dict[str, str]) -> str:
    for key in ["canonical_key", "event_uid", "source_event_id"]:
        value = clean(record.get(key))
        if value:
            return f"{key}:{value.lower()}"

    headline = result_record_headline(record).lower()
    final_score = result_record_final_score(record).lower()
    date_value = clean(record.get("scheduled_date_local") or record.get("date")).lower()
    return "fallback:" + stable_id(headline, final_score, date_value)


def record_source_weight(source_name: str) -> int:
    source_name = clean(source_name).lower()
    if "top_womens" in source_name:
        return 300
    if "reconciled" in source_name:
        return 200
    if "today_final" in source_name:
        return 100
    return 0


def record_rank_value(record: Dict[str, str]) -> float:
    try:
        return float(record.get("editorial_rank") or 0)
    except Exception:
        return 0.0


def dedupe_result_records(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    best_by_key: Dict[str, Dict[str, str]] = {}

    for row in rows:
        key = result_unique_key_from_record(row)
        existing = best_by_key.get(key)
        if not existing:
            best_by_key[key] = row
            continue

        row_score = record_source_weight(row.get("_result_record_source", "")) + record_rank_value(row)
        existing_score = record_source_weight(existing.get("_result_record_source", "")) + record_rank_value(existing)

        row_richness = sum(1 for v in row.values() if clean(v))
        existing_richness = sum(1 for v in existing.values() if clean(v))

        if row_score > existing_score or (row_score == existing_score and row_richness > existing_richness):
            best_by_key[key] = row

    return list(best_by_key.values())


def candidate_unique_key(candidate: Dict[str, Any]) -> str:
    raw = clean(candidate.get("raw_block"))
    try:
        data = json.loads(raw) if raw.startswith("{") else {}
        for key in ["canonical_key", "event_uid", "source_event_id"]:
            if clean(data.get(key)):
                return f"{key}:{clean(data.get(key)).lower()}"
    except Exception:
        pass

    headline = clean(candidate.get("graphics_headline") or candidate.get("headline")).lower()
    final_score = clean(candidate.get("final_score")).lower()
    date_value = clean(candidate.get("date")).lower()
    return "fallback:" + stable_id(headline, final_score, date_value)


def dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_key: Dict[str, Dict[str, Any]] = {}

    for candidate in candidates:
        key = candidate_unique_key(candidate)
        existing = best_by_key.get(key)
        if not existing:
            best_by_key[key] = candidate
            continue

        def cand_score(c: Dict[str, Any]) -> float:
            score = 0.0
            if clean(c.get("queue_section")) == "MUST POST":
                score += 1000
            if clean(c.get("final_score")):
                score += 100
            if clean(c.get("winner")) and clean(c.get("loser")):
                score += 50
            try:
                score += float(c.get("editorial_rank") or 0)
            except Exception:
                pass
            score += sum(1 for v in c.values() if clean(v)) / 100
            return score

        if cand_score(candidate) > cand_score(existing):
            best_by_key[key] = candidate

    deduped = list(best_by_key.values())

    def sort_key(c: Dict[str, Any]):
        section = clean(c.get("queue_section"))
        pri = 0 if section == "MUST POST" else 1 if section == "STRONG MAYBE" else 2
        try:
            rank = -float(c.get("editorial_rank") or 0)
        except Exception:
            rank = 0
        return (pri, rank, clean(c.get("graphics_headline")))

    deduped.sort(key=sort_key)
    return deduped



MAJOR_SOCCER_TERMS = {
    "usa", "uswnt", "england", "spain", "france", "germany", "netherlands",
    "sweden", "japan", "canada", "brazil", "australia", "norway", "denmark",
    "italy", "portugal", "mexico", "colombia", "argentina", "china", "korea",
    "nwsl", "wsl", "champions league", "uwcl", "world cup", "euro"
}


def row_bucket_text(record: Dict[str, str]) -> str:
    return clean(" ".join([
        record.get("editorial_bucket", ""),
        record.get("content_action", ""),
        record.get("posting_priority", ""),
    ])).lower()


def row_is_final(record: Dict[str, str]) -> bool:
    status = clean(record.get("status_norm") or record.get("game_state") or record.get("game_status")).lower()
    return status in {"", "final"} or "final" in status


def row_is_news_safe(record: Dict[str, str]) -> bool:
    gender = clean(record.get("gender_scope")).lower()
    source_name = clean(record.get("_result_record_source")).lower()
    women_source = any(token in source_name for token in ["top_womens", "women", "today_final", "reconciled"])
    if gender and gender not in {"women", "w", "female", "girls"}:
        return False
    if not gender and not women_source:
        return False
    if not row_is_final(record):
        return False
    if not result_record_final_score(record):
        return False
    if clean(record.get("manual_review")).lower() == "yes":
        return False
    return True


def row_is_must(record: Dict[str, str]) -> bool:
    txt = row_bucket_text(record)
    return "must" in txt or "make first" in txt


def row_is_strong(record: Dict[str, str]) -> bool:
    txt = row_bucket_text(record)
    return "strong" in txt


def row_sport(record: Dict[str, str]) -> str:
    return clean(record.get("sport_norm") or record.get("sport")).lower()


def row_has_major_soccer_signal(record: Dict[str, str]) -> bool:
    blob = " ".join([
        result_record_headline(record),
        record.get("league_norm", ""),
        record.get("competition_id", ""),
        record.get("home_team_display", ""),
        record.get("away_team_display", ""),
        record.get("winner", ""),
        record.get("loser", ""),
    ]).lower()
    return any(term in blob for term in MAJOR_SOCCER_TERMS)


def diversity_rank(record: Dict[str, str]) -> float:
    rank = record_rank_value(record)
    sport = row_sport(record)
    blob = " ".join([
        result_record_headline(record),
        record.get("league_norm", ""),
        record.get("competition_id", ""),
        record.get("winner", ""),
        record.get("loser", ""),
    ]).lower()

    if sport == "soccer":
        rank += 70
        if row_has_major_soccer_signal(record):
            rank += 40
    elif sport == "volleyball":
        rank += 20
    elif sport == "basketball":
        rank += 10
    else:
        rank += 15

    if "world cup" in blob or "nations league" in blob or "champions league" in blob:
        rank += 25

    return rank


def selected_keys_from_rows(rows: List[Dict[str, str]]) -> set[str]:
    return {result_unique_key_from_record(r) for r in rows}


def select_diversity_rows(all_rows: List[Dict[str, str]], selected_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Adds diversity candidates from safe lower-bucket rows.

    This is the fix for the "no women's soccer" problem. News Sync no longer
    relies only on Must Post / Strong Maybe. It can promote high-confidence
    soccer and other non-WNBA results into a P2 diversity lane.
    """
    selected = selected_keys_from_rows(selected_rows)
    pool = [r for r in all_rows if result_unique_key_from_record(r) not in selected and row_is_news_safe(r)]
    pool.sort(key=diversity_rank, reverse=True)

    diversity: List[Dict[str, str]] = []

    # Soccer-first lane.
    soccer_rows = [r for r in pool if row_sport(r) == "soccer"]
    diversity.extend(soccer_rows[:MAX_SOCCER_DIVERSITY])

    selected_extra = selected | selected_keys_from_rows(diversity)

    # Fill remaining diversity slots with non-basketball if possible.
    for r in pool:
        if len(diversity) >= MAX_DIVERSITY_PROMOTIONS:
            break
        if result_unique_key_from_record(r) in selected_extra:
            continue
        if row_sport(r) == "basketball":
            continue
        diversity.append(r)
        selected_extra.add(result_unique_key_from_record(r))

    return diversity[:MAX_DIVERSITY_PROMOTIONS]


def candidate_from_record(run_id: str, r: Dict[str, str], queue: str, template: str, forced_action: str = "") -> Dict[str, Any]:
    headline = result_record_headline(r)
    candidate = {
        "run_id": run_id,
        "candidate_id": stable_id(run_id, headline, queue, result_unique_key_from_record(r)),
        "queue_section": queue,
        "content_action": forced_action or clean(r.get("content_action")),
        "sport": clean(r.get("sport_norm") or r.get("sport")),
        "league": clean(r.get("league_norm")),
        "editorial_tier": clean(r.get("editorial_tier")),
        "editorial_bucket": clean(r.get("editorial_bucket")),
        "template": template,
        "selected_source": clean(r.get("selected_source")),
        "all_sources": clean(r.get("all_sources_json")),
        "confidence": clean(r.get("confidence")),
        "manual_review": clean(r.get("manual_review")),
        "editorial_rank": clean(r.get("editorial_rank")),
        "outcome_type": clean(r.get("outcome_type")),
        "matchup": clean(r.get("matchup")),
        "final_score": result_record_final_score(r),
        "winner": clean(r.get("winner")),
        "loser": clean(r.get("loser")),
        "game_status": clean(r.get("status_norm")),
        "date": clean(r.get("scheduled_date_local") or r.get("date")),
        "source_url": clean(r.get("source_url")),
        "graphics_headline": headline,
        "graphics_subhead": clean(r.get("caption_seed") or r.get("graphics_subhead")),
        "slide1_hook": headline,
        "slide2_result": result_record_final_score(r),
        "slide3_context": clean(r.get("angle_tag") or r.get("slide3_context") or r.get("caption_seed")),
        "slide4_cta": "",
        "raw_block": json.dumps(r, ensure_ascii=False),
        "result_record_source": clean(r.get("_result_record_source")),
    }
    candidate.update(event_date_payload(candidate))
    return normalize_candidate_fields(candidate)


def candidates_from_result_csvs(run_id: str, csv_sources: List[Tuple[str, List[Dict[str, str]]]]) -> List[Dict[str, Any]]:
    """
    Candidate builder directly from Results Desk CSVs.

    v1.6 adds a diversity lane so high-confidence women's soccer and other
    non-WNBA results can enter News Sync even when Results Desk ranks WNBA and
    volleyball above them.
    """
    rows: List[Dict[str, str]] = []
    for source_name, source_rows in csv_sources:
        for r in source_rows:
            rr = dict(r)
            rr["_result_record_source"] = source_name
            if not clean(rr.get("gender_scope")) and any(token in source_name.lower() for token in ["top_womens", "today_final", "reconciled"]):
                rr["gender_scope"] = "women"
            if not clean(rr.get("editorial_bucket")):
                if "top_womens" in source_name.lower():
                    rr["editorial_bucket"] = "Must Post"
                    rr["content_action"] = rr.get("content_action") or "Make First"
                elif "today_final" in source_name.lower() or "reconciled" in source_name.lower():
                    rr["editorial_bucket"] = "Strong Maybe"
            if not row_is_news_safe(rr):
                continue
            rows.append(rr)

    rows = dedupe_result_records(rows)

    must_rows = [r for r in rows if row_is_must(r)]
    strong_rows = [r for r in rows if row_is_strong(r) and not row_is_must(r)]
    if not must_rows and rows:
        must_rows = [r for r in rows if "top_womens" in clean(r.get("_result_record_source")).lower()][:MAX_MUST_POST]
    if not strong_rows and rows:
        must_keys = {result_unique_key_from_record(r) for r in must_rows}
        strong_rows = [r for r in rows if result_unique_key_from_record(r) not in must_keys]

    must_rows.sort(key=record_rank_value, reverse=True)
    strong_rows.sort(key=record_rank_value, reverse=True)

    selected_rows: List[Dict[str, str]] = []
    candidates: List[Dict[str, Any]] = []

    for r in must_rows[:MAX_MUST_POST]:
        selected_rows.append(r)
        candidates.append(candidate_from_record(run_id, r, "MUST POST", "News Sync CSV primary"))

    selected = selected_keys_from_rows(selected_rows)
    strong_selected = []
    for r in strong_rows:
        if len(strong_selected) >= MAX_STRONG_MAYBE:
            break
        if result_unique_key_from_record(r) in selected:
            continue
        strong_selected.append(r)
        selected_rows.append(r)
        selected.add(result_unique_key_from_record(r))

    for r in strong_selected:
        candidates.append(candidate_from_record(run_id, r, "STRONG MAYBE", "News Sync CSV primary"))

    diversity_rows = select_diversity_rows(rows, selected_rows)
    for r in diversity_rows:
        candidates.append(candidate_from_record(
            run_id,
            r,
            "DIVERSITY WATCH",
            "News Sync diversity promotion",
            forced_action="Diversity Promote",
        ))

    return dedupe_candidates(candidates)



def extract_team_score(score_text: str, team_name: str) -> str:
    score_text = clean(score_text)
    team_name = clean(team_name)
    if not score_text or not team_name:
        return ""
    pattern = re.escape(team_name) + r"\s+(\d+)"
    m = re.search(pattern, score_text, flags=re.I)
    if m:
        return m.group(1)
    pieces = re.split(r"\s+-\s+|,\s*", score_text)
    target_tokens = token_set(team_name)
    best_score = ""
    best_overlap = 0
    for piece in pieces:
        nums = re.findall(r"\b\d+\b", piece)
        if not nums:
            continue
        piece_tokens = token_set(re.sub(r"\b\d+\b", "", piece))
        overlap = len(target_tokens & piece_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_score = nums[-1]
    return best_score


def copy_score_phrase(candidate: Dict[str, Any]) -> str:
    final_score = clean(candidate.get("final_score"))
    winner = clean(candidate.get("winner"))
    loser = clean(candidate.get("loser"))
    if final_score and winner and loser:
        winner_score = extract_team_score(final_score, winner)
        loser_score = extract_team_score(final_score, loser)
        if winner_score and loser_score:
            sport = norm(candidate.get("sport"))
            if sport == "basketball":
                return f"{winner} {winner_score}, {loser} {loser_score}"
            return f"{winner} {winner_score} - {loser} {loser_score}"
    return final_score


def compact_top_performers(value: str, max_players: int = 3) -> str:
    value = clean_top_performer_text(value)
    if not value:
        return ""
    value = re.sub(r"^\d+\.\s*", "", value)
    value = re.sub(r"^.*?\bESPN event:\s*\d+\s*-\s*Status:\s*found\s*-\s*", "", value, flags=re.I)
    value = re.sub(r"^.*?\bTop performers:\s*", "", value, flags=re.I)
    value = value.replace(" | ", "; ")
    value = re.sub(r"\s+", " ", value).strip()
    chunks = [clean(x) for x in value.split(";") if clean(x)]
    cleaned = []
    for chunk in chunks:
        chunk = re.sub(r"^Top performers:\s*", "", chunk, flags=re.I).strip()
        if chunk and chunk not in cleaned:
            cleaned.append(chunk)
    return "; ".join(cleaned[:max_players])


def clean_top_performer_text(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    value = value.replace("**", "")
    value = re.sub(r"^\d+\.\s*", "", value)
    matches = list(re.finditer(r"Top performers:\s*", value, flags=re.I))
    if matches:
        value = value[matches[-1].end():]
    value = re.sub(r"^.*?ESPN event:\s*\d+\s*-\s*", "", value, flags=re.I)
    value = re.sub(r"^.*?Status:\s*found\s*-\s*", "", value, flags=re.I)
    value = value.replace(" | ", "; ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


BOX_SCORE_TEAM_NAMES = (
    "Atlanta Dream",
    "Chicago Sky",
    "Connecticut Sun",
    "Dallas Wings",
    "Golden State Valkyries",
    "Indiana Fever",
    "Las Vegas Aces",
    "Los Angeles Sparks",
    "Minnesota Lynx",
    "New York Liberty",
    "Phoenix Mercury",
    "Portland Fire",
    "Seattle Storm",
    "Toronto Tempo",
    "Washington Mystics",
)



def parse_graphics_queue(text: str, run_id: str) -> List[Dict[str, Any]]:
    """
    Robust Results Desk queue parser.

    v1.2 fixes the v1.1 issue where a valid graphics queue could contain
    result blocks but still parse 0 candidates because the section heading
    was not in the same split block or used a slightly different label.
    """
    if not text.strip() or "## RESULT GRAPHIC" not in text:
        return []

    starts = [m.start() for m in re.finditer(r"^## RESULT GRAPHIC\s+\d+:", text, flags=re.M)]
    blocks: List[str] = []
    for i, start_pos in enumerate(starts):
        end_pos = starts[i + 1] if i + 1 < len(starts) else len(text)
        # include some preceding context to catch section headings
        context_start = max(0, text.rfind("\n#", 0, start_pos))
        block = text[context_start:end_pos] if context_start >= 0 else text[start_pos:end_pos]
        blocks.append(block)

    candidates: List[Dict[str, Any]] = []

    for block in blocks:
        lines = [ln.rstrip() for ln in block.splitlines()]
        row: Dict[str, Any] = {"run_id": run_id, "raw_block": block.strip()}

        first = next((ln for ln in lines if ln.startswith("## RESULT GRAPHIC")), "")
        row["graphics_headline"] = clean(re.sub(r"^## RESULT GRAPHIC\s+\d+:\s*", "", first))
        row["candidate_id"] = stable_id(run_id, row["graphics_headline"], "graphics_queue")

        in_verified = False
        in_slide_copy = False
        slide_key = None

        for ln in lines:
            # section hints
            if ln.strip().startswith("#"):
                upper = ln.upper()
                if "MUST POST" in upper or "MAKE FIRST" in upper:
                    row["queue_section"] = "MUST POST"
                elif "STRONG MAYBE" in upper:
                    row["queue_section"] = "STRONG MAYBE"
                elif "WATCHLIST" in upper:
                    row["queue_section"] = "WATCHLIST"

            k, v = parse_key_value_line(ln)
            if k:
                mapped = {
                    "queue section": "queue_section",
                    "sport": "sport",
                    "league": "league",
                    "editorial tier": "editorial_tier",
                    "editorial bucket": "editorial_bucket",
                    "content action": "content_action",
                    "content family": "content_family",
                    "posting priority": "posting_priority",
                    "template": "template",
                    "selected source": "selected_source",
                    "all sources": "all_sources",
                    "confidence": "confidence",
                    "manual review": "manual_review",
                    "editorial rank": "editorial_rank",
                    "outcome type": "outcome_type",
                }.get(k)
                if mapped:
                    row[mapped] = clean(v)

            if ln.startswith("### Verified result context"):
                in_verified = True
                in_slide_copy = False
                continue
            if ln.startswith("### Slide copy"):
                in_verified = False
                in_slide_copy = True
                continue
            if ln.startswith("### ") and not ln.startswith("### Verified") and not ln.startswith("### Slide"):
                in_verified = False
                in_slide_copy = False

            if in_verified and ln.strip().startswith("- "):
                item = ln.strip()[2:]
                k2, v2 = parse_key_value_line(item)
                mapped2 = {
                    "matchup": "matchup",
                    "final score": "final_score",
                    "winner": "winner",
                    "loser": "loser",
                    "outcome": "outcome_type",
                    "game status": "game_status",
                    "date": "date",
                    "source url/api": "source_url",
                }.get(k2)
                if mapped2:
                    row[mapped2] = clean(v2)

            if in_slide_copy:
                if ln.startswith("**Slide 1"):
                    slide_key = "slide1_hook"
                    row[slide_key] = clean(ln.split("**", 2)[-1])
                    continue
                if ln.startswith("**Slide 2"):
                    slide_key = "slide2_result"
                    continue
                if ln.startswith("**Slide 3"):
                    slide_key = "slide3_context"
                    continue
                if ln.startswith("**Slide 4"):
                    slide_key = "slide4_cta"
                    continue
                if slide_key and ln.strip() and not ln.startswith("###"):
                    existing = row.get(slide_key, "")
                    row[slide_key] = clean((existing + " " + ln.strip()).strip())

        for f in CANDIDATE_FIELDS:
            row.setdefault(f, "")

        row = normalize_candidate_fields(row)

        if row.get("queue_section") in {"MUST POST", "STRONG MAYBE"}:
            candidates.append(row)

    must = [c for c in candidates if c.get("queue_section") == "MUST POST"][:MAX_MUST_POST]
    maybe = [c for c in candidates if c.get("queue_section") == "STRONG MAYBE"][:MAX_STRONG_MAYBE]
    return must + maybe



def parse_recommendations_fallback(text: str, run_id: str) -> List[Dict[str, Any]]:
    """
    Fallback parser for `daily_results_recommendations.md`.

    It is less rich than the graphics queue, but prevents a silent zero-output run
    when the graphics queue path changes or is missing.
    """
    if not text.strip():
        return []

    candidates: List[Dict[str, Any]] = []
    section = ""
    current: Optional[Dict[str, Any]] = None

    for raw in text.splitlines():
        line = raw.rstrip()

        if line.startswith("## Make First"):
            section = "MUST POST"
            current = None
            continue
        if line.startswith("## Strong Maybe"):
            section = "STRONG MAYBE"
            current = None
            continue
        if line.startswith("## Watchlist") or line.startswith("## Manual Review"):
            section = ""
            current = None
            continue

        if section and re.match(r"^\d+\.\s+\*\*", line):
            if current:
                candidates.append(current)

            headline = re.sub(r"^\d+\.\s+\*\*", "", line)
            headline = re.sub(r"\*\*.*$", "", headline).strip()
            current = {
                "run_id": run_id,
                "candidate_id": stable_id(run_id, headline, section),
                "queue_section": section,
                "content_action": "Make First" if section == "MUST POST" else "Strong Maybe",
                "sport": "",
                "league": "",
                "editorial_tier": "",
                "editorial_bucket": "Must Post" if section == "MUST POST" else "Strong Maybe",
                "template": "News Sync fallback",
                "selected_source": "results_recommendations",
                "all_sources": "",
                "confidence": "",
                "manual_review": "No",
                "editorial_rank": "",
                "outcome_type": "",
                "matchup": headline,
                "final_score": "",
                "winner": "",
                "loser": "",
                "game_status": "final",
                "date": "",
                "source_url": "",
                "graphics_headline": headline,
                "graphics_subhead": "",
                "slide1_hook": headline,
                "slide2_result": "",
                "slide3_context": "",
                "slide4_cta": "",
                "raw_block": line,
            }
            continue

        if current and line.strip().startswith("- "):
            detail = clean(line.strip()[2:])
            current["raw_block"] = clean((current.get("raw_block", "") + " " + detail).strip())

            # Typical v4.3 rec line:
            # basketball | WNBA | confidence 1.00 | rank 292.7
            if "|" in detail:
                parts = [clean(p) for p in detail.split("|")]
                if len(parts) >= 1 and not current.get("sport"):
                    current["sport"] = parts[0]
                if len(parts) >= 2 and not current.get("league"):
                    current["league"] = parts[1]
                for part in parts:
                    m = re.search(r"confidence\s+([0-9.]+)", part, re.I)
                    if m:
                        current["confidence"] = m.group(1)
                    m = re.search(r"rank\s+([0-9.]+)", part, re.I)
                    if m:
                        current["editorial_rank"] = m.group(1)
            else:
                if not current.get("graphics_subhead"):
                    current["graphics_subhead"] = detail
                elif not current.get("slide3_context"):
                    current["slide3_context"] = detail

    if current:
        candidates.append(current)

    normalized = [normalize_candidate_fields(c) for c in candidates]

    must = [c for c in normalized if c.get("queue_section") == "MUST POST"][:MAX_MUST_POST]
    maybe = [c for c in normalized if c.get("queue_section") == "STRONG MAYBE"][:MAX_STRONG_MAYBE]
    return must + maybe


def parse_box_score_summary(text: str) -> Dict[str, str]:
    """
    Best-effort parser for `wnba_box_score_summary.md`.
    Returns matchup/headline-ish key -> top performer text.
    """
    out: Dict[str, str] = {}
    if not text.strip():
        return out

    # Parse by game section so one event's stats cannot bleed into another.
    chunks = re.split(r"\n(?=(?:##\s+|\d+\.\s+\*\*))", text)
    for chunk in chunks:
        ch = clean(chunk)
        if not ch:
            continue

        performer_match = re.search(r"\bTop performers:\s*(.+?)(?=\n\s*\n|\Z)", chunk, flags=re.I | re.S)
        if not performer_match:
            continue

        title_match = re.search(r"^\s*(?:\d+\.\s*)?\*\*(.+?)\*\*", chunk, flags=re.M)
        if not title_match:
            title_match = re.search(r"^\s*##\s+(.+)$", chunk, flags=re.M)
        title = clean(title_match.group(1)) if title_match else ""
        team_hits = [team for team in BOX_SCORE_TEAM_NAMES if team.lower() in ch.lower()]
        key = clean(" ".join([title, " ".join(team_hits)])).lower()
        if not key:
            key = clean(ch[:120]).lower()
        out[key] = clean_top_performer_text(performer_match.group(1))

    return out


def candidate_team_token_groups(candidate: Dict[str, Any]) -> List[set[str]]:
    team_values = [clean(candidate.get("winner")), clean(candidate.get("loser"))]
    if not all(team_values):
        headline_winner, headline_loser = infer_winner_loser_from_headline(candidate.get("graphics_headline", ""))
        team_values = [clean(headline_winner), clean(headline_loser)]
    if not all(team_values):
        matchup = clean(candidate.get("matchup"))
        pieces = [clean(part) for part in re.split(r"\s+(?:vs\.?|at|beat)\s+", matchup, maxsplit=1, flags=re.I)]
        if len(pieces) == 2:
            team_values = pieces
    return [token_set(value) for value in team_values if token_set(value)]


def find_top_performers(candidate: Dict[str, Any], box_map: Dict[str, str]) -> str:
    blob = " ".join([
        candidate.get("graphics_headline", ""),
        candidate.get("matchup", ""),
        candidate.get("final_score", ""),
        candidate.get("slide3_context", ""),
    ]).lower()
    team_groups = candidate_team_token_groups(candidate)

    best = ""
    best_score = 0
    for key, val in box_map.items():
        key_tokens = token_set(key)
        if len(team_groups) >= 2:
            if not all(group & key_tokens for group in team_groups[:2]):
                continue
            score = sum(len(group & key_tokens) for group in team_groups[:2])
        else:
            score = sum(1 for token in key_tokens if len(token) >= 4 and token in blob)
            if score < 2:
                continue
        if score > best_score:
            best_score = score
            best = val

    if best_score >= 2:
        return clean_top_performer_text(best)
    return ""


def source_registry_defaults() -> Dict[str, Any]:
    return {
        "sources": [
            {
                "source_id": "wnba",
                "name": "WNBA official",
                "priority": 100,
                "type": "official_league",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://www.wnba.com/"],
                "notes": "Official WNBA league source. Use for schedule, stats, news, transactions, injuries."
            },
            {
                "source_id": "espn_wnba",
                "name": "ESPN WNBA",
                "priority": 75,
                "type": "scoreboard_backup",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://www.espn.com/wnba/scoreboard"],
                "notes": "Backup box score and story-link source."
            },
            {
                "source_id": "ap_wnba",
                "name": "AP WNBA hub",
                "priority": 70,
                "type": "wire_context",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://apnews.com/hub/wnba-basketball"],
                "notes": "Use for wire-style context, never copied prose."
            },
            {
                "source_id": "ap_womens_sports",
                "name": "AP women's sports hub",
                "priority": 70,
                "type": "wire_context",
                "sports": ["basketball", "soccer", "tennis", "golf", "softball", "volleyball"],
                "leagues_contains": ["Women", "WNBA", "NWSL", "WTA", "LPGA", "Softball", "Volleyball"],
                "urls": ["https://apnews.com/hub/womens-sports"],
                "notes": "Free AP women's sports context. Use facts, links, and evidence notes only."
            },
            {
                "source_id": "reuters_sports",
                "name": "Reuters sports",
                "priority": 68,
                "type": "wire_context",
                "sports": ["basketball", "soccer", "tennis", "golf", "softball", "volleyball"],
                "leagues_contains": ["Women", "WNBA", "NWSL", "WTA", "LPGA", "World Cup", "Olympics"],
                "urls": ["https://www.reuters.com/sports/"],
                "notes": "Free public Reuters sports context when reachable. Never copy article prose."
            },
            {
                "source_id": "wta_official",
                "name": "WTA official",
                "priority": 95,
                "type": "official_league",
                "sports": ["tennis"],
                "leagues_contains": ["WTA", "Tennis"],
                "urls": ["https://www.wtatennis.com/"],
                "notes": "Official WTA source for tournaments, draws, results, rankings, and player context."
            },
            {
                "source_id": "lpga_official",
                "name": "LPGA official",
                "priority": 92,
                "type": "official_league",
                "sports": ["golf"],
                "leagues_contains": ["LPGA", "Golf"],
                "urls": ["https://www.lpga.com/"],
                "notes": "Official LPGA source for tournament, leaderboard, and player context."
            },
            {
                "source_id": "ncaa_softball_official",
                "name": "NCAA softball official",
                "priority": 88,
                "type": "official_competition",
                "sports": ["softball"],
                "leagues_contains": ["NCAA", "Softball", "College World Series"],
                "urls": ["https://www.ncaa.com/sports/softball/d1"],
                "notes": "Official NCAA softball source for championship, schedule, and recap context."
            },
            {
                "source_id": "us_soccer_uswnt",
                "name": "US Soccer USWNT official",
                "priority": 88,
                "type": "official_team",
                "sports": ["soccer"],
                "leagues_contains": ["USWNT", "United States", "USA", "Soccer"],
                "urls": ["https://www.ussoccer.com/teams/uswnt"],
                "notes": "Official USWNT source for roster, match, and national-team context."
            },
            {
                "source_id": "fifa_womens_football",
                "name": "FIFA Women's Football",
                "priority": 95,
                "type": "official_global",
                "sports": ["soccer"],
                "leagues_contains": ["World Cup", "FIFA", "Women"],
                "urls": ["https://www.fifa.com/en/womens-football"],
                "notes": "Official global women's soccer context source."
            },
            {
                "source_id": "uefa_womens_football",
                "name": "UEFA Women's Football",
                "priority": 92,
                "type": "official_confederation",
                "sports": ["soccer"],
                "leagues_contains": ["UEFA", "Euro", "Champions League", "UWCL"],
                "urls": ["https://www.uefa.com/womenschampionsleague/"],
                "notes": "Official UEFA women's soccer context source."
            },
            {
                "source_id": "nwsl",
                "name": "NWSL official",
                "priority": 95,
                "type": "official_league",
                "sports": ["soccer"],
                "leagues_contains": ["NWSL", "National Women's Soccer League"],
                "urls": ["https://www.nwslsoccer.com/"],
                "notes": "Official NWSL source."
            },
            {
                "source_id": "espn_soccer",
                "name": "ESPN Soccer",
                "priority": 70,
                "type": "mainstream_context",
                "sports": ["soccer"],
                "leagues_contains": ["Soccer", "Women", "NWSL", "World Cup", "Euro"],
                "urls": ["https://www.espn.com/soccer/"],
                "notes": "Mainstream soccer context source."
            },
            {
                "source_id": "guardian_womens_football",
                "name": "The Guardian women's football",
                "priority": 65,
                "type": "mainstream_context",
                "sports": ["soccer"],
                "leagues_contains": ["Women", "Women's football", "Soccer"],
                "urls": ["https://www.theguardian.com/football/womens-football"],
                "notes": "Mainstream women's football context source."
            },
            {
                "source_id": "bbc_womens_football",
                "name": "BBC women's football",
                "priority": 65,
                "type": "mainstream_context",
                "sports": ["soccer"],
                "leagues_contains": ["Women", "Women's football", "Soccer"],
                "urls": ["https://www.bbc.com/sport/football/womens"],
                "notes": "Mainstream women's football context source."
            },
            {
                "source_id": "volleyball_world",
                "name": "Volleyball World",
                "priority": 95,
                "type": "official_competition",
                "sports": ["volleyball"],
                "leagues_contains": ["VNL", "Nations League", "Volleyball"],
                "urls": ["https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/"],
                "notes": "Official VNL and global volleyball narrative source."
            },
            {
                "source_id": "cev",
                "name": "CEV",
                "priority": 85,
                "type": "official_confederation",
                "sports": ["volleyball"],
                "leagues_contains": ["CEV", "European"],
                "urls": ["https://www.cev.eu/"],
                "notes": "Official European volleyball context source."
            },
            {
                "source_id": "ehf",
                "name": "EHF Champions League Women",
                "priority": 85,
                "type": "official_competition",
                "sports": ["handball"],
                "leagues_contains": ["EHF", "Champions League"],
                "urls": ["https://ehfcl.eurohandball.com/women/"],
                "notes": "Official women's handball competition source."
            }
        ],
        "team_sources": {
            "atlanta dream": ["https://dream.wnba.com/"],
            "chicago sky": ["https://sky.wnba.com/"],
            "connecticut sun": ["https://sun.wnba.com/"],
            "dallas wings": ["https://wings.wnba.com/"],
            "golden state valkyries": ["https://valkyries.wnba.com/"],
            "indiana fever": ["https://fever.wnba.com/"],
            "las vegas aces": ["https://aces.wnba.com/"],
            "los angeles sparks": ["https://sparks.wnba.com/"],
            "minnesota lynx": ["https://lynx.wnba.com/"],
            "new york liberty": ["https://liberty.wnba.com/"],
            "phoenix mercury": ["https://mercury.wnba.com/"],
            "portland fire": ["https://fire.wnba.com/"],
            "seattle storm": ["https://storm.wnba.com/"],
            "toronto tempo": ["https://tempo.wnba.com/"],
            "washington mystics": ["https://mystics.wnba.com/"]
        }
    }



def merge_source_registry(user_registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge repo-level news_source_registry.json with built-in defaults.

    This prevents old config files from blocking newly added source coverage.
    In v1.6, soccer source defaults existed in code, but an older registry JSON
    in the repo could override them, leaving soccer with 0 source observations.
    """
    defaults = source_registry_defaults()
    if not isinstance(user_registry, dict):
        return defaults

    merged = {
        "sources": [],
        "team_sources": {},
    }

    seen_source_ids = set()
    for src in defaults.get("sources", []):
        sid = clean(src.get("source_id"))
        if sid and sid not in seen_source_ids:
            merged["sources"].append(src)
            seen_source_ids.add(sid)

    for src in user_registry.get("sources", []):
        sid = clean(src.get("source_id"))
        if sid and sid not in seen_source_ids:
            merged["sources"].append(src)
            seen_source_ids.add(sid)

    merged["team_sources"].update(defaults.get("team_sources", {}))
    merged["team_sources"].update(user_registry.get("team_sources", {}))

    return merged


def angle_rules_defaults() -> Dict[str, Any]:
    return {
        "basketball": {
            "close_margin_max": 6,
            "statement_margin_min": 15,
            "high_score_min": 95,
            "default_family": "Tonight in the W",
        },
        "volleyball": {
            "five_set_scores": ["3-2", "2-3"],
            "default_family": "Around Women's Sports",
        },
        "soccer": {
            "close_scorelines": ["1-0", "2-1", "1-1", "0-0"],
            "default_family": "Around Women's Sports",
        },
        "context_fallbacks": {
            "basketball": "This result stands out because the verified box score gives it a real player-performance angle.",
            "volleyball": "This result matters most when paired with tournament context, rankings, or an official competition recap.",
            "default": "This result belongs in today's wider women's sports conversation, but it needs one more sourced context signal before being treated as a full story."
        }
    }


def registry_sources_for_candidate(candidate: Dict[str, Any], registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    sport = norm(candidate.get("sport"))
    league = norm(candidate.get("league"))
    matchup = norm(candidate.get("matchup"))
    result: List[Dict[str, Any]] = []

    for src in registry.get("sources", []):
        sports = [s.lower() for s in src.get("sports", [])]
        league_terms = [s.lower() for s in src.get("leagues_contains", [])]

        # v1.8: sport-strict matching.
        # Do not let generic terms like "women" attach soccer sources
        # to volleyball, basketball, or other sports.
        if sports and sport and sport not in sports:
            continue

        if sport in sports or any(term and term in league for term in league_terms):
            result.append(src)

    # team site sources for WNBA
    if sport == "basketball" or "wnba" in league or "nba w" in league:
        for team_slug, urls in registry.get("team_sources", {}).items():
            if team_slug in matchup or team_slug in norm(candidate.get("graphics_headline")):
                result.append({
                    "source_id": "team_" + team_slug.replace(" ", "_"),
                    "name": team_slug.title() + " official",
                    "priority": 90,
                    "type": "official_team",
                    "sports": ["basketball"],
                    "urls": urls,
                    "notes": "Official team site."
                })

    # de-dupe by source_id/url
    seen = set()
    deduped = []
    for src in sorted(result, key=lambda s: int(s.get("priority", 0)), reverse=True):
        key = src.get("source_id", "") + "|" + "|".join(src.get("urls", []))
        if key not in seen:
            seen.add(key)
            deduped.append(src)
    return deduped


def fetch_page_metadata(url: str) -> Dict[str, Any]:
    result = {
        "url": url,
        "domain": urlparse(url).netloc,
        "fetch_status": "not_run",
        "http_status": "",
        "title": "",
        "description": "",
        "published_hint": "",
        "notes": "",
    }
    if not ENABLE_FETCH:
        result["fetch_status"] = "disabled"
        return result

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT)
        result["http_status"] = str(r.status_code)
        if r.status_code >= 400:
            result["fetch_status"] = "http_error"
            result["notes"] = f"HTTP {r.status_code}"
            return result

        soup = BeautifulSoup(r.text, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = clean(soup.title.string)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = clean(og_title.get("content"))

        desc = ""
        for attrs in [
            {"name": "description"},
            {"property": "og:description"},
            {"name": "twitter:description"},
        ]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                desc = clean(tag.get("content"))
                break

        published = ""
        for attrs in [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"name": "date"},
            {"itemprop": "datePublished"},
        ]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                published = clean(tag.get("content"))
                break

        result.update({
            "fetch_status": "ok",
            "title": title[:240],
            "description": desc[:500],
            "published_hint": published[:100],
        })
    except Exception as exc:
        result["fetch_status"] = "error"
        result["notes"] = str(exc)[:240]
    return result


def terms_for_candidate(candidate: Dict[str, Any]) -> List[str]:
    terms = []
    for field in ["winner", "loser", "matchup", "graphics_headline", "league"]:
        val = clean(candidate.get(field))
        if not val:
            continue
        for part in re.split(r"\bvs\b|,| and | beat | over |\|", val, flags=re.I):
            part = clean(part)
            if len(part) >= 4:
                terms.append(part.lower())
    # remove scores and short tokens
    cleaned = []
    for term in terms:
        term = re.sub(r"\b\d+\b", "", term).strip()
        if len(term) >= 4 and term not in cleaned:
            cleaned.append(term)
    return cleaned[:12]


def source_observations_for_candidate(candidate: Dict[str, Any], registry: Dict[str, Any], run_id: str) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    terms = terms_for_candidate(candidate)
    sources = registry_sources_for_candidate(candidate, registry)

    for source in sources:
        for url in source.get("urls", []):
            trust_band = source_trust_band(source.get("type"))
            publish_use = publish_use_for_source(source.get("type"))
            meta = fetch_page_metadata(url)
            hay = norm(" ".join([meta.get("title", ""), meta.get("description", ""), meta.get("url", "")]))
            matched = [t for t in terms if t and t in hay]

            usable_context = "No"
            context_signal = ""
            review_flag = ""
            if meta.get("fetch_status") == "ok":
                if matched:
                    usable_context = "Yes"
                    context_signal = f"Matched source metadata terms: {', '.join(matched[:4])}"
                elif source.get("type", "").startswith("official"):
                    usable_context = "Partial"
                    context_signal = f"Official source available: {source.get('name')}"
                else:
                    usable_context = "Partial"
                    context_signal = f"Secondary source available: {source.get('name')}"
            else:
                review_flag = "source_fetch_failed"

            observations.append({
                "run_id": run_id,
                "candidate_id": candidate.get("candidate_id"),
                "source_id": source.get("source_id", ""),
                "source_name": source.get("name", ""),
                "source_priority": source.get("priority", ""),
                "source_type": source.get("type", ""),
                "url": url,
                "domain": meta.get("domain", ""),
                "fetch_status": meta.get("fetch_status", ""),
                "http_status": meta.get("http_status", ""),
                "title": meta.get("title", ""),
                "description": meta.get("description", ""),
                "matched_terms": ", ".join(matched),
                "published_hint": meta.get("published_hint", ""),
                "usable_context": usable_context,
                "context_signal": context_signal,
                "source_trust_band": trust_band,
                "publish_use": publish_use,
                "fetched_at_utc": utc_now(),
                "review_flag": review_flag,
                "notes": meta.get("notes", "") or source.get("notes", ""),
            })
            time.sleep(REQUEST_SLEEP_SECONDS)

    return observations


def source_trust_band(source_type: Any) -> str:
    text = norm(source_type)
    if any(token in text for token in ["prohibited", "paid", "private", "paywall", "restricted"]):
        return "red"
    if any(token in text for token in ["social", "community", "discovery", "fan"]):
        return "yellow"
    if any(token in text for token in ["official", "wire", "primary"]):
        return "green"
    if any(token in text for token in ["scoreboard", "mainstream", "context", "backup", "cross_check"]):
        return "green_cross_check"
    return "yellow"


def publish_use_for_source(source_type: Any) -> str:
    band = source_trust_band(source_type)
    if band == "green":
        return "publish_grade"
    if band == "green_cross_check":
        return "cross_check"
    if band == "yellow":
        return "discovery_only"
    return "blocked"


def source_confidence_summary(
    candidate: Dict[str, Any],
    observations: List[Dict[str, Any]],
    src_count: int,
    primary_count: int,
    final_score: str,
    top_performers: str,
    results_desk_final: bool,
    event_date_confidence: str,
    review_flags: List[str],
) -> Dict[str, Any]:
    usable = [o for o in observations if o.get("usable_context") in {"Yes", "Partial"}]
    use_for = lambda observation: clean(observation.get("publish_use")) or publish_use_for_source(observation.get("source_type"))
    publish_grade = [o for o in usable if use_for(o) == "publish_grade"]
    cross_checks = [o for o in usable if use_for(o) == "cross_check"]
    discovery = [o for o in usable if use_for(o) == "discovery_only"]
    blocked = [o for o in usable if use_for(o) == "blocked"]

    score = 0
    reasons: List[str] = []
    if results_desk_final:
        score += 55
        reasons.append("Results Desk final score")
    if final_score:
        score += 20
        reasons.append("final score present")
    if publish_grade:
        score += 40
        reasons.append(f"{len(publish_grade)} publish-grade source(s)")
    if primary_count:
        score += 15
        reasons.append(f"{primary_count} primary source(s)")
    if cross_checks:
        score += min(15, 8 + len(cross_checks) * 2)
        reasons.append(f"{len(cross_checks)} free cross-check source(s)")
    if src_count >= 2:
        score += 8
        reasons.append("multiple usable free sources")
    if top_performers:
        score += 5
        reasons.append("sourced player context")
    if event_date_confidence == "missing":
        score -= 25
        reasons.append("event date missing")
    if "source_fetch_failed" in review_flags and src_count == 0:
        score -= 20
        reasons.append("source fetch failed with no usable context")
    if discovery and not (publish_grade or results_desk_final):
        score -= 15
        reasons.append("discovery-only source requires confirmation")
    if blocked:
        score -= 40
        reasons.append("blocked source present")

    score = max(0, min(100, score))
    if blocked:
        tier = "blocked"
        grade = "blocked"
    elif (
        (score >= 75 and publish_grade and event_date_confidence != "missing")
        or (results_desk_final and final_score and event_date_confidence != "missing" and score >= 70)
    ):
        tier = "publish_grade"
        grade = "publish_grade"
    elif score >= 60 and (publish_grade or results_desk_final or cross_checks):
        tier = "review_grade"
        grade = "review_before_publish"
    elif discovery or src_count:
        tier = "discovery_only"
        grade = "discovery_only"
    else:
        tier = "insufficient"
        grade = "discovery_only"

    return {
        "score": score,
        "tier": tier,
        "publish_grade": grade,
        "reason": "; ".join(reasons) if reasons else "No usable free-source confidence signal",
    }


def parse_score(candidate: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    # final score display usually like "dallas wings 104 - los angeles sparks 96"
    s = clean(candidate.get("final_score"))
    nums = [int(x) for x in re.findall(r"\b\d+\b", s)]
    if len(nums) >= 2:
        return nums[0], nums[1]  # away, home based on Results Desk display
    return None, None


def infer_angle(candidate: Dict[str, Any], top_performers: str, angle_rules: Dict[str, Any]) -> Tuple[str, str, str]:
    sport = norm(candidate.get("sport"))
    headline = candidate.get("graphics_headline", "")
    outcome = norm(candidate.get("outcome_type"))
    final_score = candidate.get("final_score", "")
    away_score, home_score = parse_score(candidate)
    margin = None
    if away_score is not None and home_score is not None:
        margin = abs(away_score - home_score)

    if sport == "basketball":
        family = angle_rules.get("basketball", {}).get("default_family", "Tonight in the W")
        if away_score is not None and home_score is not None and max(away_score, home_score) >= angle_rules.get("basketball", {}).get("high_score_min", 95):
            return family, "high-scoring WNBA result", "The scoreline and top-performer data give this game a clear offensive hook."
        if margin is not None and margin <= angle_rules.get("basketball", {}).get("close_margin_max", 6):
            return family, "close WNBA finish", "The margin makes this one useful as a close-finish WNBA brief."
        if margin is not None and margin >= angle_rules.get("basketball", {}).get("statement_margin_min", 15):
            return family, "statement WNBA win", "The margin gives this result a stronger team-form angle than a routine score post."
        if top_performers:
            return family, "player-led WNBA result", "The verified top-performer line gives this result a player-first angle."
        return family, "WNBA result watch", angle_rules.get("context_fallbacks", {}).get("basketball")

    if sport == "soccer":
        blob = " ".join([
            candidate.get("graphics_headline", ""),
            candidate.get("league", ""),
            candidate.get("matchup", ""),
            candidate.get("winner", ""),
            candidate.get("loser", ""),
        ]).lower()
        family = "Around Women's Sports"
        if any(term in blob for term in MAJOR_SOCCER_TERMS):
            if outcome == "draw":
                return family, "major women's soccer draw", "This is a stronger soccer item because it involves a major team, competition, or women's soccer signal."
            return family, "major women's soccer result", "This is a stronger soccer item because it involves a major team, competition, or women's soccer signal."
        if outcome == "draw":
            return family, "women's soccer draw", "The result is valid as a soccer draw and works best inside an Around Women's Sports roundup."
        return family, "women's soccer result", "This belongs in the women's soccer lane and can work as a short roundup item with official source support."

    if sport == "volleyball":
        family = angle_rules.get("volleyball", {}).get("default_family", "Around Women's Sports")
        fs = final_score.lower()
        if "3-2" in fs or "2-3" in fs:
            return family, "five-set volleyball result", "A five-set final gives this result enough tension for a short tournament brief."
        if "3-0" in fs or "0-3" in fs:
            return family, "straight-sets volleyball result", "The clean scoreline works best when paired with ranking, stage, or official competition context."
        return family, "volleyball results watch", angle_rules.get("context_fallbacks", {}).get("volleyball")

    if outcome == "draw":
        return "Around Women's Sports", "draw result", "A draw is valid here, but it needs competition context before becoming a full news brief."

    return "Around Women's Sports", "results watch", angle_rules.get("context_fallbacks", {}).get("default")


def source_summary(observations: List[Dict[str, Any]]) -> Tuple[int, int, List[str], str, List[str]]:
    usable = [o for o in observations if o.get("usable_context") in {"Yes", "Partial"}]
    primary = [o for o in usable if "official" in norm(o.get("source_type"))]
    urls = [o.get("url", "") for o in usable if o.get("url")]
    signals = [o.get("context_signal", "") for o in usable if o.get("context_signal")]
    flags = [o.get("review_flag", "") for o in observations if o.get("review_flag")]
    return len(usable), len(primary), urls, (signals[0] if signals else ""), flags


def make_brief(candidate: Dict[str, Any], top_performers: str, context_signal: str, angle_tag: str) -> Tuple[str, str, str, str, str, str, str]:
    winner = clean(candidate.get("winner"))
    loser = clean(candidate.get("loser"))
    final_score = clean(candidate.get("final_score"))
    score_phrase = copy_score_phrase(candidate) or "score pending parser review"
    headline_base = clean(candidate.get("graphics_headline")) or f"{winner} beat {loser}"
    sport = norm(candidate.get("sport"))
    content_family = "Tonight in the W" if sport == "basketball" else "Around Women's Sports"

    performer_sentence = compact_top_performers(top_performers)

    if performer_sentence:
        dek = f"{score_phrase}. Top performers: {performer_sentence}"
        context_line = f"Top performers: {performer_sentence}"
    else:
        dek = clean(candidate.get("graphics_subhead")) or score_phrase
        context_line = context_signal or clean(candidate.get("slide3_context"))

    if winner and loser and final_score:
        lede = f"{winner} beat {loser}, with the verified final listed as {score_phrase}."
    elif winner and loser:
        lede = f"{winner} beat {loser}."
    elif clean(candidate.get("outcome_type")) == "draw" and final_score:
        lede = f"{headline_base}, with the verified final listed as {score_phrase}."
    else:
        lede = f"{headline_base}."

    if performer_sentence:
        second = f"The best production angle is {angle_tag}: {context_line}."
    elif context_signal:
        second = f"The strongest current context signal is source-backed: {context_signal}."
    else:
        second = "The result is verified, but richer narrative context still needs an official recap, stat page, or competition note."

    close = "Her Sports Daily will keep player or milestone claims limited to sourced fields."
    brief = f"{lede} {second} {close}"

    words = brief.split()
    if len(words) > 155:
        brief = " ".join(words[:155]).rstrip(",.;") + "."

    caption_hard = f"{headline_base}. Verified final: {score_phrase}."
    if performer_sentence:
        caption_voice = f"{headline_base}. {context_line}."
    elif "five-set" in angle_tag:
        caption_voice = f"{headline_base}. Five sets, one result, and a clean Around Women's Sports angle."
    else:
        caption_voice = f"{headline_base}. Verified final: {score_phrase}."

    story_text = f"{headline_base}\n\nVerified final: {score_phrase}\n\nAngle: {angle_tag}"
    slide3 = context_line if context_line else clean(candidate.get("slide3_context"))
    graphics_handoff = (
        f"Use as {content_family}. Headline: {headline_base}. "
        f"Final score: {score_phrase}. Slide 3 context: {slide3}. "
        "Do not invent player stats beyond the packet."
    )
    return headline_base, dek, brief, caption_hard, caption_voice, story_text, graphics_handoff



def context_quality(top_performers: str, src_count: int, primary_count: int, final_score: str) -> str:
    if final_score and top_performers and primary_count >= 1:
        return "High"
    if final_score and primary_count >= 1:
        return "Medium"
    if final_score and src_count >= 1:
        return "Low"
    return "Unsafe"


def quality_score(top_performers: str, src_count: int, primary_count: int, final_score: str, queue_section: str) -> int:
    score = 0
    if final_score:
        score += 35
    if primary_count >= 1:
        score += 20
    if src_count >= 2:
        score += 10
    if top_performers:
        score += 25
    if queue_section == "MUST POST":
        score += 10
    return min(score, 100)


def format_recommendation(packet_context_quality: str, content_family: str, queue_section: str, top_performers: str) -> str:
    if packet_context_quality == "High" and content_family == "Tonight in the W":
        return "Carousel or short brief"
    if packet_context_quality in {"High", "Medium"} and queue_section == "MUST POST":
        return "Short brief plus story"
    if content_family == "Around Women's Sports":
        return "Roundup item"
    return "Hold or use as note only"


def build_fact_packet(candidate: Dict[str, Any], observations: List[Dict[str, Any]], box_map: Dict[str, str], angle_rules: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    top_performers = compact_top_performers(find_top_performers(candidate, box_map))
    content_family, angle_tag, angle_context = infer_angle(candidate, top_performers, angle_rules)
    src_count, primary_count, urls, source_context_signal, flags = source_summary(observations)

    # v1.8: source failures are diagnostic, not packet-level review flags
    # when enough usable/primary context exists.
    if src_count >= 2 and primary_count >= 1:
        flags = [f for f in flags if f != "source_fetch_failed"]

    context_signal = source_context_signal or angle_context
    headline, dek, brief, cap_hard, cap_voice, story_text, graphics_handoff = make_brief(
        candidate, top_performers, context_signal, angle_tag
    )

    manual_review = "No"
    review_flags = list(flags)

    if clean(candidate.get("manual_review")).lower() == "yes":
        manual_review = "Yes"
        review_flags.append("results_desk_manual_review")

    if not clean(candidate.get("final_score")):
        manual_review = "Yes"
        review_flags.append("final_score_missing")

    # Strong rule: P1 needs either top performers or at least one usable/official source.
    if candidate.get("queue_section") == "MUST POST":
        if not top_performers and primary_count < 1:
            manual_review = "Yes"
            review_flags.append("no_primary_context_for_must_post")
    elif src_count < 1:
        manual_review = "Yes"
        if candidate.get("queue_section") == "DIVERSITY WATCH":
            review_flags.append("no_usable_context_for_diversity_watch")
        else:
            review_flags.append("no_usable_context_for_strong_maybe")

    if "source_fetch_failed" in review_flags and src_count == 0:
        manual_review = "Yes"

    # score lock: news layer never overrides result desk final score
    score_accuracy_check = "locked_to_results_desk"

    packet_context_quality = context_quality(top_performers, src_count, primary_count, clean(candidate.get("final_score")))
    packet_quality_score = quality_score(top_performers, src_count, primary_count, clean(candidate.get("final_score")), candidate.get("queue_section"))
    packet_format_reco = format_recommendation(packet_context_quality, content_family, candidate.get("queue_section"), top_performers)

    if manual_review == "Yes":
        publish_reco = "Hold for editor"
    elif candidate.get("queue_section") == "MUST POST":
        publish_reco = "Publish short brief"
    else:
        publish_reco = "Publish if useful / use for roundup"

    production_ready = "Yes" if manual_review == "No" and packet_context_quality in {"High", "Medium"} else "No"
    urgency = "P1" if candidate.get("queue_section") == "MUST POST" else "P2"
    event_payload = event_date_payload(candidate)
    if event_payload.get("event_date_confidence") == "missing":
        # Event dates are now required downstream for freshness gating.
        manual_review = "Yes"
        if "event_date_missing" not in review_flags:
            review_flags.append("event_date_missing")
        production_ready = "No"
        publish_reco = "Hold for editor"
        packet_format_reco = "Hold until event_date is available from Results Desk"

    # v1.8.3: Results Desk final-score rows are graphics-ready when score + event_date exist.
    # They should not be blocked just because there is not a separate article/context source.
    source_hint = " ".join([
        clean(candidate.get("_result_record_source")),
        clean(candidate.get("result_record_source")),
        clean(candidate.get("status_norm")),
        clean(candidate.get("game_status")),
    ]).lower()
    results_desk_final = bool(clean(candidate.get("final_score"))) and any(
        token in source_hint for token in ["top_womens", "today_final", "reconciled", "result", "final"]
    )
    if results_desk_final and event_payload.get("event_date_confidence") != "missing":
        review_flags = [
            f for f in review_flags
            if f not in {"no_primary_context_for_must_post", "no_usable_context_for_strong_maybe", "source_fetch_failed"}
        ]
        manual_review = "No"
        production_ready = "Yes"
        publish_reco = "Publish graphics-ready result"
        packet_context_quality = "Medium" if packet_context_quality not in {"High", "Medium"} else packet_context_quality
        packet_quality_score = max(int(packet_quality_score or 0), 70)
        if not packet_format_reco or packet_format_reco.startswith("Hold"):
            packet_format_reco = "Graphics-ready result from Results Desk"

    source_confidence = source_confidence_summary(
        candidate,
        observations,
        src_count,
        primary_count,
        clean(candidate.get("final_score")),
        top_performers,
        results_desk_final,
        event_payload.get("event_date_confidence", ""),
        review_flags,
    )
    if source_confidence["publish_grade"] in {"discovery_only", "blocked"}:
        manual_review = "Yes"
        production_ready = "No"
        publish_reco = "Hold for editor"
        if source_confidence["publish_grade"] == "discovery_only":
            review_flags.append("source_confidence_discovery_only")
        else:
            review_flags.append("source_confidence_blocked")
    elif source_confidence["publish_grade"] == "review_before_publish" and production_ready == "Yes":
        manual_review = "Yes"
        production_ready = "No"
        publish_reco = "Hold for editor"
        review_flags.append("source_confidence_review_before_publish")

    return {
        "run_id": run_id,
        "candidate_id": candidate.get("candidate_id"),
        "queue_section": candidate.get("queue_section"),
        "sport": candidate.get("sport"),
        "league": candidate.get("league"),
        "editorial_bucket": candidate.get("editorial_bucket"),
        "content_family": content_family,
        "publish_recommendation": publish_reco,
        "urgency": urgency,
        "headline": headline,
        "dek": dek,
        "brief_120w": brief,
        "caption_hard_fact": cap_hard,
        "caption_voice": cap_voice,
        "story_text": story_text,
        "slide3_context": clean(top_performers or context_signal or candidate.get("slide3_context")),
        "graphics_handoff": graphics_handoff,
        "source_count": src_count,
        "primary_source_count": primary_count,
        "source_confidence_score": source_confidence["score"],
        "source_confidence_tier": source_confidence["tier"],
        "source_publish_grade": source_confidence["publish_grade"],
        "source_confidence_reason": source_confidence["reason"],
        "source_urls_json": json.dumps(urls, ensure_ascii=False),
        "context_signal": context_signal,
        "top_performers": top_performers,
        "review_flags": "; ".join(sorted(set([f for f in review_flags if f]))),
        "context_quality": packet_context_quality,
        "quality_score": packet_quality_score,
        "production_ready": production_ready,
        "content_format_recommendation": packet_format_reco,
        "result_record_source": candidate.get("result_record_source", ""),
        "manual_review": manual_review,
        "score_accuracy_check": score_accuracy_check,
        "rights_safe_note": "Facts and links only. Do not copy article body or source prose.",
        "event_date": event_payload.get("event_date", ""),
        "event_datetime": event_payload.get("event_datetime", ""),
        "result_date": event_payload.get("result_date", ""),
        "freshness_label": event_payload.get("freshness_label", ""),
        "freshness_source": event_payload.get("freshness_source", ""),
        "source_run_timestamp": event_payload.get("source_run_timestamp", ""),
        "event_date_confidence": event_payload.get("event_date_confidence", ""),
        "event_date_required": "Yes",
    }


BREAKING_TERMS = {
    "breaking": 18,
    "announces": 10,
    "announced": 10,
    "trade": 16,
    "traded": 16,
    "signing": 12,
    "signs": 12,
    "waived": 12,
    "transfer": 12,
    "injury": 16,
    "injured": 16,
    "out indefinitely": 18,
    "suspended": 16,
    "retires": 14,
    "retirement": 14,
    "coach": 10,
    "fired": 16,
    "record": 10,
    "upset": 12,
    "comeback": 10,
}


def observation_use(observation: Dict[str, Any]) -> str:
    return clean(observation.get("publish_use")) or publish_use_for_source(observation.get("source_type"))


def public_signal_observations(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        obs for obs in observations
        if observation_use(obs) == "discovery_only"
        or source_trust_band(obs.get("source_type")) == "yellow"
        or any(token in norm(obs.get("source_type")) for token in ["social", "community", "fan", "discovery"])
    ]


def breaking_public_signal_row(
    packet: Dict[str, Any],
    observations: List[Dict[str, Any]],
    run_id: str,
) -> Dict[str, Any]:
    headline_blob = norm(" ".join([
        packet.get("headline", ""),
        packet.get("dek", ""),
        packet.get("context_signal", ""),
        packet.get("review_flags", ""),
    ]))
    reasons: List[str] = []
    score = 0

    queue_section = clean(packet.get("queue_section"))
    if queue_section == "MUST POST":
        score += 30
        reasons.append("Results Desk marked Must Post")
    elif queue_section == "STRONG MAYBE":
        score += 18
        reasons.append("Results Desk marked Strong Maybe")

    try:
        source_score = int(packet.get("source_confidence_score") or 0)
    except Exception:
        source_score = 0
    if source_score:
        score += min(25, max(0, source_score // 4))
        reasons.append(f"source confidence {source_score}/100")

    if clean(packet.get("source_publish_grade")) == "publish_grade":
        score += 12
        reasons.append("publish-grade source confidence available")
    elif clean(packet.get("source_publish_grade")) == "review_before_publish":
        score += 8
        reasons.append("review-grade source confidence available")

    if clean(packet.get("event_date")):
        score += 8
        reasons.append("dated item")
    if clean(packet.get("source_count")) not in {"", "0"}:
        score += 8
        reasons.append(f"{packet.get('source_count')} usable source observation(s)")

    matched_terms = [term for term in BREAKING_TERMS if term in headline_blob]
    if matched_terms:
        term_score = min(24, sum(BREAKING_TERMS[term] for term in matched_terms[:3]))
        score += term_score
        reasons.append("breaking-language match: " + ", ".join(matched_terms[:4]))

    public_obs = public_signal_observations(observations)
    if public_obs:
        score += min(10, 4 + len(public_obs) * 2)
        reasons.append(f"{len(public_obs)} review-only public/community signal observation(s)")

    score = min(100, score)
    if score >= 75:
        band = "P0_breaking_review"
    elif score >= 60:
        band = "P1_urgent_review"
    elif score >= 40:
        band = "P2_monitor_review"
    else:
        band = "P3_watch_review"

    usable_obs = [obs for obs in observations if obs.get("usable_context") in {"Yes", "Partial"}]
    source_urls = [clean(obs.get("url")) for obs in usable_obs if clean(obs.get("url"))]
    source_domains = sorted({clean(obs.get("domain")) for obs in usable_obs if clean(obs.get("domain"))})

    if public_obs:
        public_signal_status = "candidate_public_signal_review_only"
        public_signal_confidence = "medium" if len(public_obs) >= 2 else "low"
        public_signal_summary = "; ".join(
            clean(obs.get("context_signal")) or clean(obs.get("notes")) or clean(obs.get("source_name"))
            for obs in public_obs[:3]
        )
        retrieval_method = "public_metadata_observation"
    else:
        public_signal_status = "not_captured"
        public_signal_confidence = "none"
        public_signal_summary = "No public/community signal captured; use source observations only."
        retrieval_method = "source_metadata_observation" if observations else "not_attempted"

    return {
        "run_id": run_id,
        "candidate_id": clean(packet.get("candidate_id")),
        "headline": clean(packet.get("headline")),
        "sport": clean(packet.get("sport")),
        "league": clean(packet.get("league")),
        "queue_section": queue_section,
        "breaking_score": str(score),
        "urgency_band": band,
        "why_urgent": "; ".join(reasons) if reasons else "No urgent signal beyond normal news packet review",
        "source_confidence_score": clean(packet.get("source_confidence_score")),
        "source_confidence_tier": clean(packet.get("source_confidence_tier")),
        "source_publish_grade": clean(packet.get("source_publish_grade")),
        "source_confidence_reason": clean(packet.get("source_confidence_reason")),
        "public_signal_status": public_signal_status,
        "public_signal_confidence": public_signal_confidence,
        "public_signal_count": str(len(public_obs)),
        "public_signal_summary": public_signal_summary,
        "signal_timestamp_utc": utc_now(),
        "source_urls": json.dumps(source_urls[:12], ensure_ascii=False),
        "source_domains": "; ".join(source_domains[:12]),
        "retrieval_method": retrieval_method,
        "limitations": "Metadata and source-observation scaffold only; no paid API, private data, follower metrics, engagement scraping, login-only content, or auto-confirmation.",
        "human_review_cue": "Operator must verify source provenance, recency, and public-signal meaning before any editorial use.",
        "manual_review_required": "true",
        "review_only": "true",
        "publish_ready": "false",
        "auto_publish": "false",
        "auto_source_enablement": "false",
        "approval_state_change": "false",
    }


def build_breaking_public_signal_rows(
    packets: List[Dict[str, Any]],
    observations_by_candidate: Dict[str, List[Dict[str, Any]]],
    run_id: str,
) -> List[Dict[str, Any]]:
    rows = [
        breaking_public_signal_row(packet, observations_by_candidate.get(packet.get("candidate_id"), []), run_id)
        for packet in packets
    ]
    rows.sort(key=lambda row: (-int(row.get("breaking_score") or 0), row.get("headline", "")))
    return rows


def markdown_breaking_public_signal(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Breaking News + Public Signal Queue",
        "",
        f"Generated: {utc_now()}",
        "",
        "Review-only intelligence scaffold. This file does not approve sources, publish copy, or move anything into a publish-ready lane.",
        "",
    ]
    if not rows:
        lines.extend(["No news packets available for breaking/public-signal review.", ""])
        return "\n".join(lines)

    for row in rows[:20]:
        lines.extend([
            f"## {row.get('urgency_band')} - {row.get('headline')}",
            "",
            f"- Breaking score: `{row.get('breaking_score')}/100`",
            f"- Why urgent: {row.get('why_urgent')}",
            f"- Source confidence: `{row.get('source_confidence_tier')}` / `{row.get('source_publish_grade')}` / `{row.get('source_confidence_score')}`",
            f"- Public signal: `{row.get('public_signal_status')}` / `{row.get('public_signal_confidence')}`",
            f"- Signal timestamp: `{row.get('signal_timestamp_utc')}`",
            f"- Source domains: {row.get('source_domains') or 'none captured'}",
            f"- Retrieval method: `{row.get('retrieval_method')}`",
            f"- Human review: {row.get('human_review_cue')}",
            f"- Limitations: {row.get('limitations')}",
            "",
        ])
    return "\n".join(lines) + "\n"


def required_confirmation_type(row: Dict[str, Any]) -> str:
    if clean(row.get("source_publish_grade")) == "publish_grade":
        return "operator_verify_primary_or_official_source"
    if clean(row.get("public_signal_status")) == "candidate_public_signal_review_only":
        return "official_or_wire_confirmation_required"
    return "second_source_or_operator_confirmation_required"


def confirmation_search_hint(row: Dict[str, Any], source_type: str) -> str:
    parts = [
        clean(row.get("league")),
        clean(row.get("sport")),
        clean(row.get("headline")),
    ]
    suffix = "official news confirmation" if source_type == "official" else "wire report confirmation"
    return clean(" ".join([part for part in parts if part] + [suffix]))


def breaking_confirmation_intake_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    intake: List[Dict[str, Any]] = []
    for row in rows:
        confirmation_id = "confirm_" + stable_id(row.get("run_id"), row.get("candidate_id"), row.get("headline"))
        intake.append(
            {
                "confirmation_id": confirmation_id,
                "run_id": clean(row.get("run_id")),
                "candidate_id": clean(row.get("candidate_id")),
                "headline": clean(row.get("headline")),
                "urgency_band": clean(row.get("urgency_band")),
                "breaking_score": clean(row.get("breaking_score")),
                "required_confirmation_type": required_confirmation_type(row),
                "confirmation_status": "operator_input_required",
                "source_confidence_tier": clean(row.get("source_confidence_tier")),
                "source_publish_grade": clean(row.get("source_publish_grade")),
                "public_signal_status": clean(row.get("public_signal_status")),
                "public_signal_confidence": clean(row.get("public_signal_confidence")),
                "source_domains": clean(row.get("source_domains")),
                "source_urls": clean(row.get("source_urls")),
                "official_source_search_hint": confirmation_search_hint(row, "official"),
                "wire_source_search_hint": confirmation_search_hint(row, "wire"),
                "operator_checked_url": "",
                "operator_checked_domain": "",
                "operator_confirmation_result": "",
                "operator_confirmed_at_utc": "",
                "operator_notes": "",
                "limitations": "Manual intake only; does not update source registry, enable sources, approve copy, publish, or create a publish-ready lane.",
                "manual_review_required": "true",
                "review_only": "true",
                "publish_ready": "false",
                "auto_publish": "false",
                "auto_source_enablement": "false",
                "approval_state_change": "false",
            }
        )
    return intake


def markdown_breaking_confirmation_intake(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Breaking/Public Signal Confirmation Intake",
        "",
        f"Generated: {utc_now()}",
        "",
        "Manual review bridge only. Fill the CSV after checking official, wire, primary, or operator-verified evidence. This file does not approve, publish, or enable sources.",
        "",
    ]
    if not rows:
        lines.extend(["No breaking/public-signal rows need confirmation intake.", ""])
        return "\n".join(lines)

    for row in rows[:20]:
        lines.extend([
            f"## {row.get('urgency_band')} - {row.get('headline')}",
            "",
            f"- Confirmation status: `{row.get('confirmation_status')}`",
            f"- Required confirmation: `{row.get('required_confirmation_type')}`",
            f"- Official search hint: {row.get('official_source_search_hint')}",
            f"- Wire search hint: {row.get('wire_source_search_hint')}",
            f"- Current domains: {row.get('source_domains') or 'none captured'}",
            f"- Operator fill-in fields: `operator_checked_url`, `operator_confirmation_result`, `operator_notes`",
            f"- Guardrails: review_only={row.get('review_only')}, publish_ready={row.get('publish_ready')}, auto_source_enablement={row.get('auto_source_enablement')}, auto_publish={row.get('auto_publish')}",
            "",
        ])
    return "\n".join(lines) + "\n"


def parse_json_list(value: Any) -> List[str]:
    text = clean(value)
    if not text:
        return []
    try:
        data = json.loads(text)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [clean(item) for item in data if clean(item)]


def breaking_cluster_key(row: Dict[str, Any]) -> str:
    headline = norm(row.get("headline"))
    headline = re.sub(r"^(breaking|update|confirmed|report):\s*", "", headline)
    headline = re.sub(r"\b(final|score|result)\b", "", headline)
    headline = re.sub(r"\b\d{1,3}\b", "", headline)
    headline = re.sub(r"[^a-z0-9]+", " ", headline)
    return clean(headline)[:120] or stable_id(row.get("candidate_id"), row.get("headline"))


def strongest_urgency_band(rows: List[Dict[str, Any]]) -> str:
    rank = {"P0_breaking_review": 0, "P1_urgent_review": 1, "P2_monitor_review": 2, "P3_watch_review": 3}
    bands = [clean(row.get("urgency_band")) for row in rows if clean(row.get("urgency_band"))]
    return sorted(bands, key=lambda band: rank.get(band, 99))[0] if bands else "P3_watch_review"


def public_signal_confidence_rollup(rows: List[Dict[str, Any]]) -> str:
    confidences = {clean(row.get("public_signal_confidence")) for row in rows}
    if "medium" in confidences or len(rows) >= 2:
        return "medium"
    if "low" in confidences:
        return "low"
    return "none"


OFFICIAL_RESULT_DOMAINS = (
    "wnba.com",
    "nwsl.com",
    "wta.com",
    "lpga.com",
    "ncaa.com",
    "ussoccer.com",
)

WIRE_RESULT_DOMAINS = (
    "apnews.com",
    "reuters.com",
)


def source_domain_from_url(url: Any) -> str:
    text = clean(url)
    if not text:
        return ""
    try:
        return clean(urlparse(text).netloc).lower()
    except Exception:
        return ""


def is_official_or_wire_domain(domain: Any) -> bool:
    text = clean(domain).lower()
    return any(text == d or text.endswith("." + d) for d in OFFICIAL_RESULT_DOMAINS + WIRE_RESULT_DOMAINS)


def is_free_result_domain(domain: Any) -> bool:
    text = clean(domain).lower()
    return is_official_or_wire_domain(text) or text.endswith("espn.com") or text.endswith("cbssports.com")


def is_official_source_domain(domain: Any) -> bool:
    text = clean(domain).lower()
    return any(text == d or text.endswith("." + d) for d in OFFICIAL_RESULT_DOMAINS)


def is_reputable_public_source_domain(domain: Any) -> bool:
    text = clean(domain).lower()
    return (
        any(text == d or text.endswith("." + d) for d in WIRE_RESULT_DOMAINS)
        or text.endswith("espn.com")
        or text.endswith("cbssports.com")
    )


def urls_for_domains(urls: List[str], domains: List[str], predicate: Any) -> List[str]:
    domain_set = {clean(domain).lower() for domain in domains if predicate(domain)}
    matched: List[str] = []
    for url in urls:
        domain = source_domain_from_url(url)
        if domain in domain_set and url not in matched:
            matched.append(url)
    return matched


def public_signal_ladder_label(public_count: int, public_confidence: str) -> str:
    confidence = clean(public_confidence)
    if public_count <= 0 or confidence in {"", "none"}:
        return "none_captured_public_signal_not_used_for_confirmation"
    if confidence == "medium":
        return f"public_or_community_signal_present_review_only_count={public_count}_confidence=medium"
    return f"public_or_community_signal_present_review_only_count={public_count}_confidence={confidence or 'low'}"


def corroboration_ladder(
    *,
    domains: List[str],
    urls: List[str],
    evidence: List[Dict[str, str]],
    public_count: int,
    public_confidence: str,
    evidence_status: str,
) -> Dict[str, str]:
    official_domains = [domain for domain in domains if is_official_source_domain(domain)]
    reputable_domains = [domain for domain in domains if is_reputable_public_source_domain(domain)]
    official_urls = urls_for_domains(urls, official_domains, is_official_source_domain)
    reputable_urls = urls_for_domains(urls, reputable_domains, is_reputable_public_source_domain)
    evidence_urls = parse_json_list(evidence_urls_json(evidence))
    for url in evidence_urls:
        domain = source_domain_from_url(url)
        if is_official_source_domain(domain) and url not in official_urls:
            official_urls.append(url)
        if is_reputable_public_source_domain(domain) and url not in reputable_urls:
            reputable_urls.append(url)

    official_label = "missing_official_source_operator_add_to_intake"
    if official_domains or official_urls:
        official_label = (
            f"present_operator_verify domains={'; '.join(sorted(set(official_domains))[:6])}"
            if official_domains
            else f"present_operator_verify source_url_count={len(official_urls)}"
        )
    reputable_label = "missing_reputable_free_source_operator_seek_wire_team_league_or_scoreboard"
    if reputable_domains or reputable_urls:
        reputable_label = (
            f"present_operator_verify domains={'; '.join(sorted(set(reputable_domains))[:6])}"
            if reputable_domains
            else f"present_operator_verify source_url_count={len(reputable_urls)}"
        )
    public_label = public_signal_ladder_label(public_count, public_confidence)
    missing_cue = (
        "human_confirmation_still_required_in_breaking_public_signal_confirmation_intake"
        if clean(evidence_status) != "no_matching_current_artifact_evidence_operator_confirmation_required"
        else "missing_confirmation_add_official_wire_primary_or_operator_verified_url_before_story_path"
    )
    if official_domains and reputable_domains and evidence:
        ladder_status = "official_and_reputable_artifact_cues_present_operator_verify"
    elif official_domains or evidence:
        ladder_status = "partial_corroboration_operator_verify"
    else:
        ladder_status = "missing_corroboration_operator_confirmation_required"

    ladder_urls: List[str] = []
    for url in official_urls + reputable_urls + evidence_urls:
        if url not in ladder_urls:
            ladder_urls.append(url)
    summary = (
        f"official={official_label}; reputable_free={reputable_label}; "
        f"public_signal={public_label}; missing_confirmation={missing_cue}"
    )
    return {
        "corroboration_ladder_status": ladder_status,
        "corroboration_ladder_summary": summary,
        "official_source_corroboration": official_label,
        "reputable_source_corroboration": reputable_label,
        "public_signal_corroboration": public_label,
        "missing_confirmation_cue": missing_cue,
        "corroboration_evidence_urls": json.dumps(ladder_urls[:12], ensure_ascii=False),
    }


def official_confirmation_status(rows: List[Dict[str, Any]], domains: List[str]) -> str:
    grades = {clean(row.get("source_publish_grade")) for row in rows}
    tiers = {clean(row.get("source_confidence_tier")) for row in rows}
    if "publish_grade" in grades or "publish_grade" in tiers:
        return "official_or_primary_signal_present_operator_verify"
    if "review_before_publish" in grades or "review_grade" in tiers:
        return "review_grade_signal_present_needs_operator_verification"
    if any(domain.endswith((".wnba.com", ".nwsl.com", ".wta.com", ".lpga.com", ".ncaa.com", ".ussoccer.com")) for domain in domains):
        return "official_domain_seen_operator_verify"
    return "missing_official_confirmation"


def freshness_status_for_timestamps(timestamps: List[datetime]) -> str:
    if not timestamps:
        return "timestamp_missing"
    newest = max(timestamps)
    age_hours = max(0.0, (datetime.now(timezone.utc) - newest).total_seconds() / 3600)
    if age_hours <= 6:
        return "fresh_last_6h"
    if age_hours <= 24:
        return "fresh_last_24h"
    if age_hours <= 72:
        return "monitor_72h"
    return "stale_recheck_required"


def exact_manual_next_action(status: str) -> str:
    if status == "missing_official_confirmation":
        return "Open breaking_public_signal_confirmation_intake.csv, find an official/wire/primary confirmation URL, and record operator_checked_url plus operator_confirmation_result."
    return "Open breaking_public_signal_confirmation_intake.csv, verify the current source URL/domain still confirms the claim, and record operator_checked_url plus operator_notes."


def packet_confirmation_evidence(packet: Dict[str, Any]) -> List[Dict[str, str]]:
    urls = parse_json_list(packet.get("source_urls_json"))
    domains = sorted({source_domain_from_url(url) for url in urls if source_domain_from_url(url)})
    official_urls = [url for url in urls if is_official_or_wire_domain(source_domain_from_url(url))]
    free_urls = [url for url in urls if is_free_result_domain(source_domain_from_url(url))]
    if not official_urls and not free_urls:
        return []
    status = "official_or_wire_news_packet_evidence" if official_urls else "free_news_packet_evidence"
    return [
        {
            "artifact": "news_fact_packets.csv",
            "row_ref": f"candidate_id={clean(packet.get('candidate_id'))}",
            "candidate_id": clean(packet.get("candidate_id")),
            "headline": clean(packet.get("headline")),
            "status": status,
            "source": "; ".join(domains[:8]) or clean(packet.get("source_confidence_tier")),
            "url": json.dumps((official_urls or free_urls or urls)[:6], ensure_ascii=False),
            "review_note": "Operator must open the cited source URL and verify that it still confirms the cluster claim.",
        }
    ]


def game_row_matches_cluster(row: Dict[str, Any], cluster_headline: str, candidate_ids: List[str]) -> bool:
    headline_blob = norm(cluster_headline)
    home = norm(row.get("home_team"))
    away = norm(row.get("away_team"))
    if home and away and home in headline_blob and away in headline_blob:
        return True
    row_text = norm(" ".join([
        row.get("row_id", ""),
        row.get("home_team", ""),
        row.get("away_team", ""),
        row.get("final_score", ""),
    ]))
    return any(cid and cid in row_text for cid in candidate_ids)


def game_confirmation_evidence(row: Dict[str, Any], cluster_headline: str, candidate_ids: List[str]) -> List[Dict[str, str]]:
    if not game_row_matches_cluster(row, cluster_headline, candidate_ids):
        return []
    if clean(row.get("status")).lower() != "final" and clean(row.get("recap_candidate")) != "Yes":
        return []
    url = clean(row.get("source_url"))
    domain = clean(row.get("source_domain")) or source_domain_from_url(url)
    if not url or not is_free_result_domain(domain):
        return []
    return [
        {
            "artifact": "game_intelligence_board_v1.csv",
            "row_ref": f"row_id={clean(row.get('row_id'))}",
            "candidate_id": "",
            "headline": cluster_headline,
            "status": "free_result_game_board_evidence_operator_verify",
            "source": clean(row.get("selected_source")) or domain,
            "url": json.dumps([url], ensure_ascii=False),
            "review_note": "Free/public result evidence only; operator must verify final score, teams, and recency before editorial use.",
        }
    ]


def confirmation_evidence_rows(
    packets: List[Dict[str, Any]],
    game_rows: List[Dict[str, Any]],
    cluster_headline: str,
    candidate_ids: List[str],
) -> List[Dict[str, str]]:
    evidence: List[Dict[str, str]] = []
    candidate_set = {cid for cid in candidate_ids if cid}
    for packet in packets:
        if clean(packet.get("candidate_id")) in candidate_set:
            evidence.extend(packet_confirmation_evidence(packet))
    for row in game_rows:
        evidence.extend(game_confirmation_evidence(row, cluster_headline, candidate_ids))
    return evidence


def event_ids_from_evidence(evidence: List[Dict[str, str]]) -> List[str]:
    event_ids: List[str] = []
    for row in evidence:
        text = " ".join([clean(row.get("row_ref")), clean(row.get("artifact"))])
        for match in re.findall(r"\brow_id=([A-Za-z0-9_-]+)", text):
            if match not in event_ids:
                event_ids.append(match)
    return event_ids


def matchup_teams(matchup: Any) -> List[str]:
    text = clean(matchup)
    if not text:
        return []
    parts = re.split(r"\s+(?:at|vs\.?|versus)\s+", text, flags=re.I)
    return [norm(part) for part in parts if norm(part)]


def proof_row_matches_cluster(row: Dict[str, Any], cluster_headline: str, event_ids: List[str]) -> bool:
    event_uid = clean(row.get("event_uid"))
    if event_uid and event_uid in event_ids:
        return True
    teams = matchup_teams(row.get("matchup"))
    headline = norm(cluster_headline)
    return bool(teams) and all(team in headline for team in teams)


def proof_rows_for_cluster(
    proof_rows: List[Dict[str, Any]],
    cluster_headline: str,
    evidence: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    event_ids = event_ids_from_evidence(evidence)
    matches = [row for row in proof_rows if proof_row_matches_cluster(row, cluster_headline, event_ids)]
    matches.sort(key=lambda row: (clean(row.get("event_uid")), clean(row.get("fact_type")), clean(row.get("fact_label"))))
    return matches


def proof_status_for_rows(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "no_matching_score_stat_proof_operator_confirmation_required"
    has_score = any(clean(row.get("fact_type")) == "final_score" for row in rows)
    named_count = sum(1 for row in rows if clean(row.get("fact_type")) == "named_player_stat_line")
    manual_needed = any(clean(row.get("manual_box_score_confirmation_needed")).lower() == "yes" for row in rows)
    if has_score and named_count and manual_needed:
        return "score_and_named_player_stat_proof_present_manual_confirmation_needed"
    if has_score and named_count:
        return "score_and_named_player_stat_proof_present_operator_verify"
    if has_score:
        return "final_score_proof_present_named_player_stat_proof_missing"
    if named_count:
        return "named_player_stat_proof_present_final_score_proof_missing"
    return "matching_proof_rows_missing_score_and_named_stat_lines"


def proof_source_urls_json(rows: List[Dict[str, Any]]) -> str:
    urls: List[str] = []
    for row in rows:
        url = clean(row.get("source_url"))
        if url and url not in urls:
            urls.append(url)
    return json.dumps(urls[:8], ensure_ascii=False)


def proof_artifact_refs(rows: List[Dict[str, Any]]) -> str:
    refs: List[str] = []
    for row in rows:
        proof_id = clean(row.get("proof_id"))
        if proof_id:
            refs.append(f"final_score_stat_proof_v1.csv proof_id={proof_id}")
        evidence_ref = clean(row.get("evidence_artifact_row"))
        if evidence_ref:
            refs.append(evidence_ref)
    deduped: List[str] = []
    for ref in refs:
        if ref not in deduped:
            deduped.append(ref)
    return "; ".join(deduped[:12])[:700]


def proof_manual_confirmation_cue(status: str, rows: List[Dict[str, Any]]) -> str:
    if status == "no_matching_score_stat_proof_operator_confirmation_required":
        return "No matching final-score/stat proof row found; operator must open final_score_stat_proof_v1.csv and confirm whether score/stat proof exists before using stats in copy or renders."
    if "missing" in status:
        return "Proof is partial; operator must verify the available source URL and add/check the missing score or named-player stat proof before using stats in copy or renders."
    if status == "score_and_named_player_stat_proof_present_manual_confirmation_needed":
        return "Score/stat proof rows exist but at least one row still requires manual box-score confirmation before editorial or render use."
    next_hint = clean(rows[0].get("exact_next_file_or_intake")) if rows else ""
    if next_hint:
        return f"Proof rows are source-backed review cues; operator must still follow the proof cue: {next_hint}"
    return "Proof rows are source-backed review cues; operator must still verify the cited source URL before editorial or render use."


def exact_proof_row_action(rows: List[Dict[str, Any]], cluster_headline: str) -> str:
    if not rows:
        return f"Open final_score_stat_proof_v1.csv and search for the matchup in cluster '{clean(cluster_headline)}'; if no row exists, record missing proof in the confirmation intake before using score/stat claims."
    preferred = next((row for row in rows if clean(row.get("fact_type")) == "named_player_stat_line"), rows[0])
    proof_id = clean(preferred.get("proof_id"))
    source_url = clean(preferred.get("source_url"))
    next_hint = clean(preferred.get("exact_next_file_or_intake"))
    parts = [f"Open final_score_stat_proof_v1.csv proof_id={proof_id}" if proof_id else "Open final_score_stat_proof_v1.csv matching this cluster"]
    if source_url:
        parts.append(f"verify source URL {source_url}")
    if next_hint:
        parts.append(next_hint.rstrip("."))
    else:
        parts.append("record operator confirmation before editorial or render use")
    return "; then ".join(parts).rstrip(".") + "."


def proof_ids_by_type(rows: List[Dict[str, Any]], fact_type: str) -> List[str]:
    ids: List[str] = []
    for row in rows:
        if clean(row.get("fact_type")) == fact_type and clean(row.get("proof_id")):
            proof_id = clean(row.get("proof_id"))
            if proof_id not in ids:
                ids.append(proof_id)
    return ids


def proof_confirmation_targets_for_ids(proof_ids: List[str], confirmation_rows: List[Dict[str, Any]]) -> List[str]:
    targets: List[str] = []
    confirmation_ids = {clean(row.get("proof_id")) for row in confirmation_rows}
    for proof_id in proof_ids:
        suffix = "" if proof_id in confirmation_ids else " (intake row not found; rerun Results Desk or add the row before confirming)"
        targets.append(f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={proof_id}{suffix}")
    return targets


def proof_confirmation_rows_for_ids(proof_ids: List[str], confirmation_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    wanted = set(proof_ids)
    return [row for row in confirmation_rows if clean(row.get("proof_id")) in wanted]


def score_stat_confirmation_status(
    proof_rows: List[Dict[str, Any]],
    confirmation_rows: List[Dict[str, Any]],
) -> str:
    proof_ids = proof_ids_by_type(proof_rows, "final_score") + proof_ids_by_type(proof_rows, "named_player_stat_line")
    if not proof_ids:
        return "no_score_stat_proof_to_confirm"
    matched = proof_confirmation_rows_for_ids(proof_ids, confirmation_rows)
    if len(matched) < len(set(proof_ids)):
        return "score_stat_proof_confirmation_intake_row_missing"
    if any(not clean(row.get("operator_confirmation_status")) for row in matched):
        return "operator_input_required_in_score_stat_proof_confirmation_intake"
    return "operator_confirmation_recorded_review_before_use"


def target_join(targets: List[str], limit: int = 4) -> str:
    if not targets:
        return ""
    visible = targets[:limit]
    suffix = f"; +{len(targets) - limit} more" if len(targets) > limit else ""
    return "; ".join(visible) + suffix


def exact_human_confirmation_action(
    *,
    breaking_target: str,
    score_target: str,
    named_targets: str,
    score_stat_status: str,
) -> str:
    steps = [
        f"Open {breaking_target} and fill operator_checked_url plus operator_confirmation_result for the breaking claim/source URL.",
    ]
    if score_target:
        steps.append(
            f"Open {score_target} and fill operator_checked_source_url plus operator_confirmation_status for the final-score proof."
        )
    else:
        steps.append(
            "No final-score proof confirmation target matched; open final_score_stat_proof_confirmation_intake_v1.csv and search the matchup before using score claims."
        )
    if named_targets:
        steps.append(
            f"Open {named_targets} and fill operator_checked_source_url plus operator_confirmation_status for named-player stat proof."
        )
    else:
        steps.append(
            "No named-player stat proof confirmation target matched; do not use named-player stats until the proof intake has a human-checked row."
        )
    steps.append(f"Current score/stat confirmation status: {score_stat_status}. Review-only; no approval or publish state changes.")
    return " ".join(steps)


def proof_id_from_review_order_row(row: Dict[str, Any]) -> str:
    text = " ".join([
        clean(row.get("proof_row_to_open")),
        clean(row.get("intake_row_to_record")),
        clean(row.get("proof_id")),
    ])
    match = re.search(r"\bproof_id=([A-Za-z0-9_-]+)", text)
    if match:
        return match.group(1)
    return clean(row.get("proof_id"))


def review_order_rows_for_proof_ids(
    proof_ids: List[str],
    review_order_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    wanted = set(proof_ids)
    matches = [row for row in review_order_rows if proof_id_from_review_order_row(row) in wanted]
    def order_value(row: Dict[str, Any]) -> int:
        try:
            return int(clean(row.get("review_order")) or "9999")
        except Exception:
            return 9999

    matches.sort(key=order_value)
    return matches


def review_order_target(row: Dict[str, Any]) -> str:
    review_order = clean(row.get("review_order"))
    phase = clean(row.get("review_phase"))
    intake = clean(row.get("intake_row_to_record"))
    proof = clean(row.get("proof_row_to_open"))
    bits = []
    if review_order:
        bits.append(f"final_score_stat_proof_review_order_v1.csv review_order={review_order}")
    if phase:
        bits.append(f"phase={phase}")
    if proof:
        bits.append(f"proof={proof}")
    if intake:
        bits.append(f"record={intake}")
    return "; ".join(bits)


def review_order_targets_for_rows(rows: List[Dict[str, Any]], limit: int = 4) -> str:
    targets = [review_order_target(row) for row in rows if review_order_target(row)]
    if not targets:
        return ""
    visible = targets[:limit]
    suffix = f"; +{len(targets) - limit} more" if len(targets) > limit else ""
    return "; ".join(visible) + suffix


def review_order_status(proof_rows: List[Dict[str, Any]], order_rows: List[Dict[str, Any]]) -> str:
    proof_ids = proof_ids_by_type(proof_rows, "final_score") + proof_ids_by_type(proof_rows, "named_player_stat_line")
    if not proof_ids:
        return "no_score_stat_proof_to_order"
    if not order_rows:
        return "missing_review_order_rows_for_score_stat_proof"
    if len({proof_id_from_review_order_row(row) for row in order_rows}) < len(set(proof_ids)):
        return "partial_review_order_rows_for_score_stat_proof"
    return "review_order_rows_present_operator_follow_walkthrough"


def first_review_order_target(order_rows: List[Dict[str, Any]]) -> str:
    if not order_rows:
        return ""
    score_first = next((row for row in order_rows if clean(row.get("fact_type")) == "final_score"), order_rows[0])
    return review_order_target(score_first)


def exact_review_walkthrough_action(
    order_status: str,
    first_target: str,
    order_targets: str,
) -> str:
    if order_status == "no_score_stat_proof_to_order":
        return (
            "No score/stat proof row matched this breaking cluster; open final_score_stat_proof_review_walkthrough_v1.md "
            "and confirm whether this item belongs in the proof review order before using score/stat claims."
        )
    if not first_target:
        return (
            "Open final_score_stat_proof_review_walkthrough_v1.md, then search final_score_stat_proof_review_order_v1.csv "
            "for this matchup; if no row exists, record the missing proof path before using score/stat claims."
        )
    return (
        f"Open {FINAL_SCORE_STAT_PROOF_REVIEW_WALKTHROUGH_MD}; start at {first_target}; "
        f"then continue through these cluster proof rows: {order_targets or first_target}. "
        "Record human checks only in the listed final_score_stat_proof_confirmation_intake_v1.csv rows."
    )


def event_ids_from_evidence(evidence: List[Dict[str, str]]) -> List[str]:
    ids: List[str] = []
    for row in evidence:
        text = " ".join([clean(row.get("row_ref")), clean(row.get("artifact"))])
        for match in re.findall(r"\b(?:row_id|event_uid|event_id)=([A-Za-z0-9_-]+)", text):
            if match not in ids:
                ids.append(match)
    return ids


def game_fact_rows_for_events(event_ids: List[str], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    wanted = set(event_ids)
    return [row for row in rows if clean(row.get("event_uid")) in wanted]


def story_proof_rows_for_events(event_ids: List[str], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    wanted = set(event_ids)
    matches = [row for row in rows if clean(row.get("event_id")) in wanted]

    def rank_value(row: Dict[str, Any]) -> int:
        try:
            return int(clean(row.get("candidate_rank")) or "9999")
        except Exception:
            return 9999

    matches.sort(key=rank_value)
    return matches


def game_source_confirmation_tier_cue(game_fact_rows: List[Dict[str, Any]]) -> Dict[str, str]:
    game_fact = game_fact_rows[0] if game_fact_rows else {}
    if not game_fact:
        return {
            "game_source_confirmation_tier": "game_source_tier_missing_from_current_artifacts",
            "game_source_confirmation_limitations": "No matching game_fact_confirmation_status_v1.csv row was found for this breaking cluster.",
            "game_source_confirmation_tier_target": "",
            "game_source_confirmation_tier_cue": "Open the breaking confirmation intake and add official, wire, primary, or operator-checked source evidence before editorial use.",
        }
    event_id = clean(game_fact.get("event_uid"))
    tier = clean(game_fact.get("source_confirmation_tier")) or "source_tier_not_recorded_operator_verify"
    limitations = clean(game_fact.get("source_confirmation_limitations")) or "Operator must verify the source URL before use."
    target = f"game_fact_confirmation_status_v1.csv event_uid={event_id}" if event_id else "game_fact_confirmation_status_v1.csv matching event"
    if tier.startswith("single_free_public_scoreboard"):
        cue = (
            f"{tier}; this is useful free public scoreboard evidence, but it is not official, multi-source, human-approved, "
            "or publish-ready confirmation. Verify the listed source URL and add official/wire/operator-checked confirmation when available."
        )
    elif tier.startswith("single_free_public_schedule"):
        cue = (
            f"{tier}; schedule/source context is review-only and result/stat use remains pending until the game is final and manually checked."
        )
    elif tier.startswith("source_missing"):
        cue = f"{tier}; add official, wire, primary, or operator-checked source evidence before using this as breaking news."
    else:
        cue = f"{tier}; operator must still verify the source URL and limitations before story, render, or editorial use."
    return {
        "game_source_confirmation_tier": tier,
        "game_source_confirmation_limitations": limitations,
        "game_source_confirmation_tier_target": target,
        "game_source_confirmation_tier_cue": cue,
    }


def game_source_freshness_cue(game_fact_rows: List[Dict[str, Any]]) -> Dict[str, str]:
    game_fact = game_fact_rows[0] if game_fact_rows else {}
    if not game_fact:
        return {
            "game_source_freshness_status": "game_source_freshness_missing_current_artifact",
            "game_source_freshness_age_minutes": "",
            "game_source_retrieved_at_utc": "",
            "game_source_freshness_note": "No matching game_fact_confirmation_status_v1.csv freshness row was found for this breaking cluster.",
            "game_source_freshness_target": "",
            "game_source_freshness_cue": "Open the breaking confirmation intake and record a current source URL check before treating this as breaking news.",
        }
    event_id = clean(game_fact.get("event_uid"))
    status = clean(game_fact.get("source_freshness_status")) or "source_freshness_unknown_operator_verify"
    age_minutes = clean(game_fact.get("source_freshness_age_minutes"))
    retrieved_at = clean(game_fact.get("retrieved_at_utc"))
    note = clean(game_fact.get("source_freshness_note")) or "Operator must verify source recency before use."
    target = f"game_fact_confirmation_status_v1.csv event_uid={event_id}" if event_id else "game_fact_confirmation_status_v1.csv matching event"
    if status.startswith("evidence_fresh_under_3h"):
        cue = (
            f"{status}; retrieved_at_utc={retrieved_at or 'missing'}; age_minutes={age_minutes or 'unknown'}. "
            "Fresh enough for review triage, but operator must still open the source URL and confirm facts before any story or render use."
        )
    elif status.startswith("evidence_stale") or "stale" in status:
        cue = (
            f"{status}; retrieved_at_utc={retrieved_at or 'missing'}; age_minutes={age_minutes or 'unknown'}. "
            "Re-open the source URL and record a current check before using this as breaking evidence."
        )
    elif status.startswith("no_matched_source_timestamp") or status.startswith("source_freshness_unknown") or not retrieved_at:
        cue = (
            f"{status}; source timestamp is missing or unclear. Open the source URL manually, record the checked time/result, "
            "and keep this cluster in review-only hold until recency is confirmed."
        )
    else:
        cue = (
            f"{status}; retrieved_at_utc={retrieved_at or 'missing'}; age_minutes={age_minutes or 'unknown'}. "
            "Operator must verify the source timestamp and facts before editorial use."
        )
    return {
        "game_source_freshness_status": status,
        "game_source_freshness_age_minutes": age_minutes,
        "game_source_retrieved_at_utc": retrieved_at,
        "game_source_freshness_note": note,
        "game_source_freshness_target": target,
        "game_source_freshness_cue": cue,
    }


def source_proof_readiness_cue(
    *,
    evidence: List[Dict[str, str]],
    proof_status: str,
    named_proof_rows: List[Dict[str, Any]],
    game_fact_rows: List[Dict[str, Any]],
    story_proof_rows: List[Dict[str, Any]],
) -> Dict[str, str]:
    story = story_proof_rows[0] if story_proof_rows else {}
    game_fact = game_fact_rows[0] if game_fact_rows else {}
    source_tier = game_source_confirmation_tier_cue(game_fact_rows)
    tier = clean(source_tier.get("game_source_confirmation_tier"))
    tier_limitations = clean(source_tier.get("game_source_confirmation_limitations"))
    source_freshness = game_source_freshness_cue(game_fact_rows)
    freshness_status = clean(source_freshness.get("game_source_freshness_status"))
    named_example = clean(named_proof_rows[0].get("fact_value")) if named_proof_rows else ""
    if story:
        event_id = clean(story.get("event_id"))
        candidate_id = clean(story.get("candidate_id"))
        athlete = clean(story.get("athlete_name"))
        renderability = clean(story.get("renderability_state"))
        proof_card_status = clean(story.get("proof_status"))
        copy_unlock = clean(story.get("copy_unlock_level"))
        manual_intake = clean(story.get("manual_intake_path"))
        source_cue = clean(story.get("source_confirmation_cue"))
        target = "; ".join(
            bit for bit in [
                f"story_proof_card_v1.csv event_id={event_id}" if event_id else "story_proof_card_v1.csv",
                f"candidate_id={candidate_id}" if candidate_id else "",
                f"manual_intake={manual_intake}" if manual_intake else "",
            ]
            if bit
        )
        summary = (
            f"{proof_card_status or 'story_proof_card_present_operator_verify'}; "
            f"copy={copy_unlock or 'manual_review_required'}; "
            f"renderability={renderability or 'review'}; "
            f"athlete={athlete or 'none'}; source={source_cue or 'operator_verify_source_url'}; "
            f"game_source_tier={tier or 'missing'}; game_source_freshness={freshness_status or 'missing'}"
        )
        next_action = clean(story.get("smallest_next_action")) or (
            f"Open {target or 'story_proof_card_v1.csv'}, verify the source URL, then record the check in the listed manual intake row."
        )
        return {
            "source_proof_readiness_status": "story_proof_card_ready_operator_verify",
            "source_proof_readiness_summary": summary,
            "story_proof_card_target": target,
            "game_fact_confirmation_target": clean(story.get("game_fact_row")),
            "source_proof_readiness_next_action": next_action,
        }
    if game_fact:
        event_id = clean(game_fact.get("event_uid"))
        story_target = clean(game_fact.get("story_proof_card_row_to_open"))
        summary = (
            f"{clean(game_fact.get('overall_confirmation_status')) or 'game_fact_confirmation_present_operator_verify'}; "
            f"source={clean(game_fact.get('source_domain')) or 'source_domain_missing'}; "
            f"tier={tier or 'missing'}; "
            f"freshness={freshness_status or 'missing'}; "
            f"readiness={clean(game_fact.get('recap_render_readiness')) or 'review'}; "
            f"story_card={story_target or 'missing_story_proof_card_row'}; "
            f"limits={tier_limitations or 'operator_verify_source_url'}"
        )
        next_action = clean(game_fact.get("exact_next_file_or_intake")) or (
            f"Open game_fact_confirmation_status_v1.csv event_uid={event_id}, then follow the listed proof intake rows before editorial use."
        )
        return {
            "source_proof_readiness_status": "game_fact_confirmation_ready_operator_verify",
            "source_proof_readiness_summary": summary,
            "story_proof_card_target": story_target,
            "game_fact_confirmation_target": f"game_fact_confirmation_status_v1.csv event_uid={event_id}" if event_id else "",
            "source_proof_readiness_next_action": next_action,
        }
    if clean(proof_status) != "no_matching_score_stat_proof_operator_confirmation_required":
        summary = (
            f"{proof_status}; named_player_rows={len(named_proof_rows)}; "
            f"example={named_example or 'none'}; story_card=missing_operator_open_game_or_story_proof_artifact"
        )
        return {
            "source_proof_readiness_status": "score_stat_proof_only_operator_verify",
            "source_proof_readiness_summary": summary,
            "story_proof_card_target": "",
            "game_fact_confirmation_target": "",
            "source_proof_readiness_next_action": "Open final_score_stat_proof_v1.csv and final_score_stat_proof_confirmation_intake_v1.csv for the matched proof rows; no story_proof_card_v1.csv row matched this cluster.",
        }
    if evidence:
        return {
            "source_proof_readiness_status": "artifact_evidence_only_operator_verify",
            "source_proof_readiness_summary": "Current news/game artifact evidence matched, but no story proof card or score/stat proof row matched this cluster.",
            "story_proof_card_target": "",
            "game_fact_confirmation_target": "",
            "source_proof_readiness_next_action": "Open the matching evidence artifact, then record breaking-claim confirmation before using this item editorially.",
        }
    return {
        "source_proof_readiness_status": "missing_source_proof_readiness_operator_confirmation_required",
        "source_proof_readiness_summary": "No matching story proof card, game fact confirmation row, or score/stat proof row was found for this breaking cluster.",
        "story_proof_card_target": "",
        "game_fact_confirmation_target": "",
        "source_proof_readiness_next_action": "Add or verify official, wire, primary, or operator-checked source evidence in breaking_public_signal_confirmation_intake.csv before any story path.",
    }


def urgency_review_reason(
    *,
    urgency_band: str,
    freshness_status: str,
    source_freshness_status: str,
    max_score: int,
    ladder_status: str,
    proof_readiness_status: str,
    proof_status: str,
    public_confidence: str,
    named_count: int,
    missing_confirmation_cue: str,
) -> str:
    why_now = (
        f"{urgency_band or 'review'} score={max_score}/100; "
        f"signal_freshness={freshness_status or 'timestamp_missing'}; "
        f"source_freshness={source_freshness_status or 'missing'}"
    )
    hsd_care = (
        f"source/proof readiness={proof_readiness_status or proof_status or 'missing'}; "
        f"named_player_stat_rows={named_count}"
    )
    trust = f"corroboration={ladder_status or 'missing'}; public_signal={public_confidence or 'none'}"
    missing = missing_confirmation_cue or "human_confirmation_required_before_story_use"
    return f"Why now: {why_now}. Why HSD should care: {hsd_care}. Trust cue: {trust}. Missing: {missing}."


def public_signal_limitations_cue(public_count: int, public_confidence: str) -> str:
    confidence = clean(public_confidence) or "none"
    if public_count > 0:
        return (
            f"Public/community signal is review-only discovery context count={public_count} confidence={confidence}; "
            "it cannot confirm the breaking claim, source facts, score, stats, injuries, quotes, or public consensus by itself."
        )
    return "No public/community signal captured; do not infer public reaction or use social context as confirmation."


def verification_priority_cue(
    *,
    freshness_status: str,
    ladder: Dict[str, str],
    proof_readiness: Dict[str, str],
    source_tier: Dict[str, str],
    source_freshness: Dict[str, str],
    public_count: int,
    public_confidence: str,
    breaking_target: str,
    exact_source_action: str,
) -> Dict[str, str]:
    official = clean(ladder.get("official_source_corroboration"))
    reputable = clean(ladder.get("reputable_source_corroboration"))
    public_cue = public_signal_limitations_cue(public_count, public_confidence)
    proof_status = clean(proof_readiness.get("source_proof_readiness_status"))
    proof_target = clean(proof_readiness.get("story_proof_card_target")) or clean(proof_readiness.get("game_fact_confirmation_target"))
    tier = clean(source_tier.get("game_source_confirmation_tier"))
    tier_cue = clean(source_tier.get("game_source_confirmation_tier_cue"))
    source_freshness_status = clean(source_freshness.get("game_source_freshness_status"))
    source_freshness_cue = clean(source_freshness.get("game_source_freshness_cue"))
    source_freshness_target = clean(source_freshness.get("game_source_freshness_target"))
    source_support = (
        f"source_class_support official={official or 'missing'}; reputable_free={reputable or 'missing'}; "
        f"proof_readiness={proof_status or 'missing'}; game_source_tier={tier or 'missing'}; "
        f"game_source_freshness={source_freshness_status or 'missing'}; "
        f"public_signal={public_count}:{clean(public_confidence) or 'none'}"
    )
    if clean(freshness_status) in {"timestamp_missing", "stale_recheck_required"}:
        status = "freshness_recheck_first"
        target = breaking_target
        action = (
            f"Open {breaking_target}; re-check source URL recency and timestamp before using this as breaking news. "
            "Record the stale/missing timestamp result in the confirmation intake."
        )
    elif source_freshness_status in {
        "no_matched_source_timestamp_manual_check",
        "source_freshness_unknown_operator_verify",
    } or "stale" in source_freshness_status:
        status = "source_freshness_recheck_first"
        target = source_freshness_target or breaking_target
        action = (
            f"Open {target}; re-check the source URL timestamp/recency before using this as breaking news. "
            "Record the current check in breaking_public_signal_confirmation_intake.csv or the listed proof intake row."
        )
    elif official.startswith("missing_official_source"):
        status = "official_source_confirmation_first"
        target = breaking_target
        action = (
            f"Open {breaking_target}; add or verify an official team/league, wire, primary, or operator-checked source URL "
            "before any story, render, or editorial use."
        )
    elif proof_status.startswith("missing_") or proof_status == "artifact_evidence_only_operator_verify":
        status = "source_proof_readiness_gap_first"
        target = proof_target or breaking_target
        action = clean(proof_readiness.get("source_proof_readiness_next_action")) or exact_source_action
    elif clean(ladder.get("missing_confirmation_cue")):
        status = "manual_confirmation_intake_first"
        target = breaking_target
        action = (
            f"Open {breaking_target}; record operator_checked_url and operator_confirmation_result before any story path. "
            "Then continue to the listed proof/readiness artifact rows."
        )
    else:
        status = "verification_cues_ready_for_operator_review"
        target = proof_target or breaking_target
        action = clean(proof_readiness.get("source_proof_readiness_next_action")) or exact_source_action
    summary = (
        f"{status}; {source_support}; source_tier_limit={tier_cue or 'operator_verify_source_url'}; "
        f"source_freshness_limit={source_freshness_cue or 'operator_verify_source_timestamp'}; public_limit={public_cue}"
    )
    return {
        "verification_priority_status": status,
        "verification_priority_summary": summary,
        "verification_priority_target": target,
        "verification_priority_next_action": action,
        "public_signal_limitations_cue": public_cue,
    }


def evidence_rollup_status(evidence: List[Dict[str, str]]) -> str:
    statuses = {clean(row.get("status")) for row in evidence}
    has_news = any(clean(row.get("artifact")) == "news_fact_packets.csv" for row in evidence)
    has_game = any(clean(row.get("artifact")) == "game_intelligence_board_v1.csv" for row in evidence)
    if has_news and has_game:
        return "matching_news_and_free_result_evidence_operator_verify"
    if "official_or_wire_news_packet_evidence" in statuses:
        return "matching_official_or_wire_news_evidence_operator_verify"
    if has_game:
        return "matching_free_result_evidence_operator_verify"
    if evidence:
        return "matching_free_public_evidence_operator_verify"
    return "no_matching_current_artifact_evidence_operator_confirmation_required"


def evidence_urls_json(evidence: List[Dict[str, str]]) -> str:
    urls: List[str] = []
    for row in evidence:
        for url in parse_json_list(row.get("url")):
            if url not in urls:
                urls.append(url)
    return json.dumps(urls[:12], ensure_ascii=False)


def cluster_confirmation_gap(status: str) -> str:
    if status == "no_matching_current_artifact_evidence_operator_confirmation_required":
        return "No current news/game artifact match was found; operator must add an official, wire, primary, or operator-verified URL in the confirmation intake before any story path."
    return "Current artifacts provide a review cue only; operator must still verify the cited source URL, final/result facts, and recency in the confirmation intake."


def intake_row_ref_for_cluster(intake_rows: List[Dict[str, Any]], candidate_ids: List[str]) -> str:
    candidate_set = {cid for cid in candidate_ids if cid}
    for row in intake_rows:
        if clean(row.get("candidate_id")) in candidate_set:
            return f"confirmation_id={clean(row.get('confirmation_id'))}"
    if candidate_ids:
        return f"candidate_id={candidate_ids[0]}"
    return "first matching headline row"


def source_or_intake_row_action(evidence: List[Dict[str, str]], intake_rows: List[Dict[str, Any]], candidate_ids: List[str]) -> str:
    intake_ref = intake_row_ref_for_cluster(intake_rows, candidate_ids)
    if evidence:
        first = evidence[0]
        return (
            f"Open {first.get('artifact')} {first.get('row_ref')}, verify the cited URL/facts manually, "
            f"then open breaking_public_signal_confirmation_intake.csv {intake_ref} and record operator_checked_url plus operator_confirmation_result."
        )
    return (
        f"Open breaking_public_signal_confirmation_intake.csv {intake_ref}, add an official/wire/primary confirmation URL, "
        "and record operator_confirmation_result before any editorial use."
    )


def breaking_signal_cluster_rows(
    rows: List[Dict[str, Any]],
    packets: Optional[List[Dict[str, Any]]] = None,
    game_rows: Optional[List[Dict[str, Any]]] = None,
    proof_rows: Optional[List[Dict[str, Any]]] = None,
    proof_confirmation_rows: Optional[List[Dict[str, Any]]] = None,
    proof_review_order_rows: Optional[List[Dict[str, Any]]] = None,
    game_fact_confirmation_rows: Optional[List[Dict[str, Any]]] = None,
    story_proof_card_rows: Optional[List[Dict[str, Any]]] = None,
    intake_rows: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    packets = packets or []
    game_rows = game_rows or []
    proof_rows = proof_rows or []
    proof_confirmation_rows = proof_confirmation_rows or []
    proof_review_order_rows = proof_review_order_rows or []
    game_fact_confirmation_rows = game_fact_confirmation_rows or []
    story_proof_card_rows = story_proof_card_rows or []
    intake_rows = intake_rows or []
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(breaking_cluster_key(row), []).append(row)

    clusters: List[Dict[str, Any]] = []
    for key, group in grouped.items():
        domains = sorted({
            clean(domain)
            for row in group
            for domain in clean(row.get("source_domains")).split(";")
            if clean(domain)
        })
        urls = []
        for row in group:
            for url in parse_json_list(row.get("source_urls")):
                if url not in urls:
                    urls.append(url)
        timestamps = [dt for dt in (parse_event_datetime(row.get("signal_timestamp_utc")) for row in group) if dt]
        max_score = max([int(clean(row.get("breaking_score")) or 0) for row in group] or [0])
        public_count = sum(int(clean(row.get("public_signal_count")) or 0) for row in group)
        status = official_confirmation_status(group, domains)
        candidate_ids = sorted({clean(row.get("candidate_id")) for row in group if clean(row.get("candidate_id"))})
        evidence = confirmation_evidence_rows(packets, game_rows, clean(group[0].get("headline")), candidate_ids)
        evidence_status = evidence_rollup_status(evidence)
        public_confidence = public_signal_confidence_rollup(group)
        ladder = corroboration_ladder(
            domains=domains,
            urls=urls,
            evidence=evidence,
            public_count=public_count,
            public_confidence=public_confidence,
            evidence_status=evidence_status,
        )
        matched_proof_rows = proof_rows_for_cluster(proof_rows, clean(group[0].get("headline")), evidence)
        proof_status = proof_status_for_rows(matched_proof_rows)
        named_proof_rows = [row for row in matched_proof_rows if clean(row.get("fact_type")) == "named_player_stat_line"]
        event_ids = event_ids_from_evidence(evidence)
        matched_game_fact_rows = game_fact_rows_for_events(event_ids, game_fact_confirmation_rows)
        matched_story_proof_rows = story_proof_rows_for_events(event_ids, story_proof_card_rows)
        source_tier = game_source_confirmation_tier_cue(matched_game_fact_rows)
        source_freshness = game_source_freshness_cue(matched_game_fact_rows)
        proof_readiness = source_proof_readiness_cue(
            evidence=evidence,
            proof_status=proof_status,
            named_proof_rows=named_proof_rows,
            game_fact_rows=matched_game_fact_rows,
            story_proof_rows=matched_story_proof_rows,
        )
        proof_ids = proof_ids_by_type(matched_proof_rows, "final_score") + proof_ids_by_type(matched_proof_rows, "named_player_stat_line")
        matched_review_order_rows = review_order_rows_for_proof_ids(proof_ids, proof_review_order_rows)
        review_status = review_order_status(matched_proof_rows, matched_review_order_rows)
        review_targets = review_order_targets_for_rows(matched_review_order_rows)
        first_review_target = first_review_order_target(matched_review_order_rows)
        freshness = freshness_status_for_timestamps(timestamps)
        urgency_reason = urgency_review_reason(
            urgency_band=strongest_urgency_band(group),
            freshness_status=freshness,
            source_freshness_status=source_freshness.get("game_source_freshness_status", ""),
            max_score=max_score,
            ladder_status=ladder.get("corroboration_ladder_status", ""),
            proof_readiness_status=proof_readiness.get("source_proof_readiness_status", ""),
            proof_status=proof_status,
            public_confidence=public_confidence,
            named_count=len(named_proof_rows),
            missing_confirmation_cue=ladder.get("missing_confirmation_cue", ""),
        )
        breaking_target = f"breaking_public_signal_confirmation_intake.csv {intake_row_ref_for_cluster(intake_rows, candidate_ids)}"
        source_action = source_or_intake_row_action(evidence, intake_rows, candidate_ids)
        verification_priority = verification_priority_cue(
            freshness_status=freshness,
            ladder=ladder,
            proof_readiness=proof_readiness,
            source_tier=source_tier,
            source_freshness=source_freshness,
            public_count=public_count,
            public_confidence=public_confidence,
            breaking_target=breaking_target,
            exact_source_action=source_action,
        )
        score_targets = proof_confirmation_targets_for_ids(
            proof_ids_by_type(matched_proof_rows, "final_score"),
            proof_confirmation_rows,
        )
        named_targets = proof_confirmation_targets_for_ids(
            proof_ids_by_type(matched_proof_rows, "named_player_stat_line"),
            proof_confirmation_rows,
        )
        score_target = target_join(score_targets, limit=2)
        named_target = target_join(named_targets, limit=4)
        score_stat_status = score_stat_confirmation_status(matched_proof_rows, proof_confirmation_rows)
        clusters.append(
            {
                "cluster_id": "signal_cluster_" + stable_id(key, "|".join(sorted(clean(row.get("candidate_id")) for row in group))),
                "run_id": clean(group[0].get("run_id")),
                "cluster_headline": clean(group[0].get("headline")),
                "story_count": str(len(group)),
                "candidate_ids": "; ".join(candidate_ids),
                "urgency_band": strongest_urgency_band(group),
                "max_breaking_score": str(max_score),
                "official_confirmation_status": status,
                "matching_official_evidence_status": evidence_status,
                "matching_official_evidence_count": str(len(evidence)),
                "matching_official_evidence_sources": "; ".join(clean(row.get("source")) for row in evidence if clean(row.get("source")))[:500],
                "matching_official_evidence_urls": evidence_urls_json(evidence),
                "matching_official_evidence_artifacts": "; ".join(
                    f"{clean(row.get('artifact'))} {clean(row.get('row_ref'))}".strip()
                    for row in evidence
                    if clean(row.get("artifact")) or clean(row.get("row_ref"))
                )[:500],
                "manual_confirmation_gap": cluster_confirmation_gap(evidence_status),
                "exact_source_or_intake_row_to_open": source_action,
                "score_stat_proof_status": proof_status,
                "named_player_stat_proof_count": str(len(named_proof_rows)),
                "named_player_stat_proof_examples": " | ".join(clean(row.get("fact_value")) for row in named_proof_rows[:3] if clean(row.get("fact_value")))[:700],
                "score_stat_proof_source_urls": proof_source_urls_json(matched_proof_rows),
                "score_stat_proof_artifacts": proof_artifact_refs(matched_proof_rows),
                "score_stat_manual_confirmation_cue": proof_manual_confirmation_cue(proof_status, matched_proof_rows),
                "exact_score_stat_proof_row_or_source_to_open": exact_proof_row_action(matched_proof_rows, clean(group[0].get("headline"))),
                "breaking_claim_confirmation_target": breaking_target,
                "score_proof_confirmation_target": score_target,
                "named_player_stat_proof_confirmation_targets": named_target,
                "score_stat_confirmation_status": score_stat_status,
                "exact_human_confirmation_next_action": exact_human_confirmation_action(
                    breaking_target=breaking_target,
                    score_target=score_target,
                    named_targets=named_target,
                    score_stat_status=score_stat_status,
                ),
                "score_stat_review_order_status": review_status,
                "score_stat_review_order_targets": review_targets,
                "first_score_stat_review_order_target": first_review_target,
                "score_stat_review_walkthrough_target": FINAL_SCORE_STAT_PROOF_REVIEW_WALKTHROUGH_MD,
                "exact_review_walkthrough_next_action": exact_review_walkthrough_action(
                    review_status,
                    first_review_target,
                    review_targets,
                ),
                **ladder,
                "urgency_review_reason": urgency_reason,
                **proof_readiness,
                **verification_priority,
                **source_tier,
                **source_freshness,
                "source_diversity": "multi_domain" if len(domains) >= 2 else "single_domain" if domains else "no_source_domain_captured",
                "source_domain_count": str(len(domains)),
                "source_domains": "; ".join(domains[:12]),
                "source_urls": json.dumps(urls[:12], ensure_ascii=False),
                "public_signal_count": str(public_count),
                "public_signal_confidence": public_confidence,
                "freshness_status": freshness,
                "oldest_signal_timestamp_utc": min(timestamps).isoformat() if timestamps else "",
                "newest_signal_timestamp_utc": max(timestamps).isoformat() if timestamps else "",
                "limitations": "Cluster groups review-only metadata observations only; it does not confirm claims, update sources, approve copy, publish, or create a publish-ready lane.",
                "exact_manual_next_action": exact_manual_next_action(status),
                "manual_review_required": "true",
                "review_only": "true",
                "publish_ready": "false",
                "auto_publish": "false",
                "auto_source_enablement": "false",
                "approval_state_change": "false",
            }
        )
    clusters.sort(key=lambda row: (-int(row.get("max_breaking_score") or 0), row.get("cluster_headline", "")))
    return clusters


def markdown_breaking_signal_clusters(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Breaking/Public Signal Clusters",
        "",
        f"Generated: {utc_now()}",
        "",
        "Review-only cluster summary. Use this to spot repeated story/source observations and decide the next manual confirmation step.",
        "",
    ]
    if not rows:
        lines.extend(["No breaking/public-signal clusters available.", ""])
        return "\n".join(lines)

    for row in rows[:20]:
        lines.extend([
            f"## {row.get('urgency_band')} - {row.get('cluster_headline')}",
            "",
            f"- Cluster size: `{row.get('story_count')}` row(s)",
            f"- Max breaking score: `{row.get('max_breaking_score')}/100`",
            f"- Official confirmation: `{row.get('official_confirmation_status')}`",
            f"- Matching official/free evidence: `{row.get('matching_official_evidence_status')}` / count: `{row.get('matching_official_evidence_count')}`",
            f"- Evidence artifacts: {row.get('matching_official_evidence_artifacts') or 'none matched'}",
            f"- Manual confirmation gap: {row.get('manual_confirmation_gap')}",
            f"- Exact row to open: {row.get('exact_source_or_intake_row_to_open')}",
            f"- Score/stat proof: `{row.get('score_stat_proof_status')}` / named-player rows: `{row.get('named_player_stat_proof_count')}`",
            f"- Score/stat proof rows: {row.get('score_stat_proof_artifacts') or 'none matched'}",
            f"- Named-player proof examples: {row.get('named_player_stat_proof_examples') or 'none matched'}",
            f"- Score/stat manual cue: {row.get('score_stat_manual_confirmation_cue')}",
            f"- Score/stat row to open: {row.get('exact_score_stat_proof_row_or_source_to_open')}",
            f"- Human confirmation targets: breaking claim `{row.get('breaking_claim_confirmation_target') or 'missing'}`; score proof `{row.get('score_proof_confirmation_target') or 'missing'}`; named-player stat proof `{row.get('named_player_stat_proof_confirmation_targets') or 'missing'}`",
            f"- Human confirmation status: `{row.get('score_stat_confirmation_status')}`",
            f"- Exact human confirmation next action: {row.get('exact_human_confirmation_next_action')}",
            f"- Review walkthrough: `{row.get('score_stat_review_walkthrough_target') or 'missing'}` / status: `{row.get('score_stat_review_order_status')}`",
            f"- First review-order row: {row.get('first_score_stat_review_order_target') or 'missing'}",
            f"- Exact walkthrough next action: {row.get('exact_review_walkthrough_next_action')}",
            f"- Corroboration ladder: `{row.get('corroboration_ladder_status')}`",
            f"  - Official: {row.get('official_source_corroboration') or 'missing'}",
            f"  - Reputable/free: {row.get('reputable_source_corroboration') or 'missing'}",
            f"  - Public/community: {row.get('public_signal_corroboration') or 'none captured'}",
            f"  - Missing confirmation cue: {row.get('missing_confirmation_cue') or 'operator confirmation required'}",
            f"- Urgency/trust reason: {row.get('urgency_review_reason') or 'missing'}",
            f"- Verification priority: `{row.get('verification_priority_status')}`",
            f"- Verification priority target: {row.get('verification_priority_target') or 'missing'}",
            f"- Verification priority next action: {row.get('verification_priority_next_action') or 'operator confirmation required'}",
            f"- Public/community limitation: {row.get('public_signal_limitations_cue') or 'public signal is review-only and non-confirming'}",
            f"- Game source tier: `{row.get('game_source_confirmation_tier') or 'missing'}`",
            f"- Game source tier limitation: {row.get('game_source_confirmation_limitations') or 'missing'}",
            f"- Game source tier cue: {row.get('game_source_confirmation_tier_cue') or 'operator verification required'}",
            f"- Game source freshness: `{row.get('game_source_freshness_status') or 'missing'}` / retrieved: `{row.get('game_source_retrieved_at_utc') or 'missing'}` / age minutes: `{row.get('game_source_freshness_age_minutes') or 'unknown'}`",
            f"- Game source freshness target: {row.get('game_source_freshness_target') or 'missing'}",
            f"- Game source freshness cue: {row.get('game_source_freshness_cue') or 'operator freshness check required'}",
            f"- Source/proof readiness: `{row.get('source_proof_readiness_status')}`",
            f"- Source/proof summary: {row.get('source_proof_readiness_summary') or 'missing'}",
            f"- Story proof target: {row.get('story_proof_card_target') or 'missing'}",
            f"- Game fact confirmation target: {row.get('game_fact_confirmation_target') or 'missing'}",
            f"- Source/proof next action: {row.get('source_proof_readiness_next_action') or 'operator confirmation required'}",
            f"- Source diversity: `{row.get('source_diversity')}` / domains: {row.get('source_domains') or 'none captured'}",
            f"- Public signal: `{row.get('public_signal_confidence')}` / count: `{row.get('public_signal_count')}`",
            f"- Freshness: `{row.get('freshness_status')}` / newest: `{row.get('newest_signal_timestamp_utc') or 'missing'}`",
            f"- Manual next action: {row.get('exact_manual_next_action')}",
            f"- Limitations: {row.get('limitations')}",
            "",
        ])
    return "\n".join(lines) + "\n"


def stats_row_for_game(game_row: Dict[str, Any], stats_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    row_id = clean(game_row.get("row_id"))
    if row_id:
        for row in stats_rows:
            if clean(row.get("event_uid")) == row_id:
                return row
    game_matchup = norm(" ".join([game_row.get("away_team", ""), game_row.get("home_team", "")]))
    for row in stats_rows:
        matchup = norm(row.get("matchup"))
        if game_matchup and all(part in matchup for part in [norm(game_row.get("away_team")), norm(game_row.get("home_team"))] if part):
            return row
    return {}


def cluster_for_game_row(game_row: Dict[str, Any], cluster_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    row_id = clean(game_row.get("row_id"))
    if row_id:
        for row in cluster_rows:
            if f"row_id={row_id}" in clean(row.get("matching_official_evidence_artifacts")):
                return row
    home = norm(game_row.get("home_team"))
    away = norm(game_row.get("away_team"))
    for row in cluster_rows:
        headline = norm(row.get("cluster_headline"))
        if home and away and home in headline and away in headline:
            return row
    return {}


def news_packet_for_cluster(cluster_row: Dict[str, Any], packets: List[Dict[str, Any]]) -> Dict[str, Any]:
    candidate_ids = [cid for cid in clean(cluster_row.get("candidate_ids")).split(";") if cid]
    candidate_set = set(candidate_ids)
    for packet in packets:
        if clean(packet.get("candidate_id")) in candidate_set:
            return packet
    return {}


def append_unique_urls(urls: List[str], values: List[str]) -> None:
    for value in values:
        url = clean(value)
        if url and url not in urls:
            urls.append(url)


def first_clean_value(*values: Any) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def breaking_evidence_domain_lead(row: Dict[str, Any]) -> str:
    urls: List[str] = []
    for key in ["corroboration_evidence_urls", "matching_official_evidence_urls", "source_urls"]:
        urls.extend(parse_json_list(row.get(key)))
    domains = [source_domain_from_url(url) for url in urls if source_domain_from_url(url)]
    if domains:
        return domains[0]
    source_domains = [clean(part) for part in clean(row.get("source_domains")).split(";") if clean(part)]
    if source_domains:
        return source_domains[0]
    return clean(row.get("matching_official_evidence_sources"))


def breaking_evidence_cue(row: Dict[str, Any]) -> str:
    official = clean(row.get("official_source_corroboration"))
    reputable = clean(row.get("reputable_source_corroboration"))
    public = clean(row.get("public_signal_corroboration"))
    if official.startswith("present_operator_verify"):
        return f"official_or_primary_evidence_present_operator_verify; {official}"
    if reputable.startswith("present_operator_verify"):
        return f"reputable_or_gray_area_public_evidence_present_operator_verify; {reputable}"
    if public.startswith("public_or_community_signal_present"):
        return f"public_or_community_signal_only_review_not_confirmation; {public}"
    return "missing_official_reputable_or_gray_area_evidence_operator_add_to_intake"


def breaking_next_action_priority(row: Dict[str, Any]) -> str:
    verification = clean(row.get("verification_priority_status"))
    source_freshness = clean(row.get("game_source_freshness_status"))
    official = clean(row.get("official_source_corroboration"))
    reputable = clean(row.get("reputable_source_corroboration"))
    public_count = int(clean(row.get("public_signal_count")) or 0)
    tier = clean(row.get("game_source_confirmation_tier"))
    if verification in {"freshness_recheck_first", "source_freshness_recheck_first"} or "stale" in source_freshness:
        return "P0_freshness_recheck_first"
    if official.startswith("missing_official_source") or verification == "official_source_confirmation_first":
        return "P1_official_confirmation_required"
    if reputable.startswith("present_operator_verify") or tier.startswith("single_free_public"):
        return "P2_reputable_or_gray_area_source_verify"
    if public_count > 0:
        return "P3_public_signal_review_only"
    return "P4_cluster_audit_no_fix"


def breaking_next_action_text(row: Dict[str, Any], priority: str) -> str:
    if priority == "P0_freshness_recheck_first":
        target = clean(row.get("game_source_freshness_target")) or clean(row.get("verification_priority_target")) or clean(row.get("breaking_claim_confirmation_target"))
        return (
            f"Open {target or BREAKING_CONFIRMATION_INTAKE_CSV}; re-check source URL recency, then record the result in "
            "breaking_public_signal_confirmation_intake.csv or the listed proof intake before any story/render use."
        )
    if priority == "P1_official_confirmation_required":
        return clean(row.get("verification_priority_next_action")) or (
            f"Open {clean(row.get('breaking_claim_confirmation_target')) or BREAKING_CONFIRMATION_INTAKE_CSV}; add official, wire, primary, or operator-checked confirmation before editorial use."
        )
    if priority == "P2_reputable_or_gray_area_source_verify":
        target = clean(row.get("verification_priority_target")) or clean(row.get("game_source_confirmation_tier_target")) or clean(row.get("breaking_claim_confirmation_target"))
        return f"Open {target or BREAKING_SIGNAL_CLUSTERS_CSV}; verify the reputable/free public source URL and keep the row review-only until human confirmation is recorded."
    if priority == "P3_public_signal_review_only":
        return (
            f"Open {clean(row.get('breaking_claim_confirmation_target')) or BREAKING_CONFIRMATION_INTAKE_CSV}; public/community signal is context only and cannot confirm the claim."
        )
    return f"Open {BREAKING_SIGNAL_CLUSTERS_CSV} cluster_id={clean(row.get('cluster_id'))}; audit only if this becomes a story candidate."


def breaking_signal_queue_by_candidate(signal_rows: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in signal_rows or []:
        candidate_id = clean(row.get("candidate_id"))
        if candidate_id and candidate_id not in lookup:
            lookup[candidate_id] = row
    return lookup


def first_breaking_signal_for_cluster(
    cluster: Dict[str, Any],
    signal_rows_by_candidate: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    for candidate_id in clean(cluster.get("candidate_ids")).split(";"):
        candidate_id = clean(candidate_id)
        if candidate_id and candidate_id in signal_rows_by_candidate:
            return signal_rows_by_candidate[candidate_id]
    return {}


def split_manual_confirmation_target(target: str) -> Tuple[str, str]:
    target = clean(target)
    if not target:
        return "breaking_public_signal_confirmation_intake.csv", "matching headline or candidate row"
    match = re.match(r"(?P<artifact>[^\s]+\.csv)(?:\s+(?P<row_ref>.*))?$", target)
    if not match:
        return "breaking_public_signal_confirmation_intake.csv", target
    return clean(match.group("artifact")), clean(match.group("row_ref")) or "matching row"


def breaking_signal_next_action_rows(
    cluster_rows: List[Dict[str, Any]],
    signal_rows: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    signal_rows_by_candidate = breaking_signal_queue_by_candidate(signal_rows)
    rows: List[Dict[str, Any]] = []
    for cluster in cluster_rows:
        signal = first_breaking_signal_for_cluster(cluster, signal_rows_by_candidate)
        priority = breaking_next_action_priority(cluster)
        proof_target = first_clean_value(
            cluster.get("game_source_freshness_target"),
            cluster.get("story_proof_card_target"),
            cluster.get("game_fact_confirmation_target"),
            cluster.get("first_score_stat_review_order_target"),
            cluster.get("score_proof_confirmation_target"),
            cluster.get("named_player_stat_proof_confirmation_targets"),
        )
        manual_target = clean(cluster.get("verification_priority_target")) or clean(cluster.get("breaking_claim_confirmation_target"))
        manual_artifact, manual_row_ref = split_manual_confirmation_target(manual_target)
        rows.append(
            {
                "action_rank": "",
                "cluster_id": clean(cluster.get("cluster_id")),
                "cluster_headline": clean(cluster.get("cluster_headline")),
                "urgency_band": clean(cluster.get("urgency_band")),
                "review_priority": priority,
                "verification_priority_status": clean(cluster.get("verification_priority_status")),
                "confirmation_state": clean(cluster.get("corroboration_ladder_status")),
                "official_reputable_gray_area_cue": breaking_evidence_cue(cluster),
                "source_confirmation_tier": clean(cluster.get("game_source_confirmation_tier")),
                "source_freshness_status": clean(cluster.get("game_source_freshness_status")),
                "source_freshness_age_minutes": clean(cluster.get("game_source_freshness_age_minutes")),
                "source_domain_lead": breaking_evidence_domain_lead(cluster),
                "why_story_looks_urgent": clean(cluster.get("urgency_review_reason")) or clean(signal.get("why_urgent")),
                "source_confidence_tier": clean(signal.get("source_confidence_tier")),
                "source_confidence_reason": clean(signal.get("source_confidence_reason")),
                "signal_timestamp_utc": clean(signal.get("signal_timestamp_utc")) or clean(cluster.get("newest_signal_timestamp_utc")),
                "retrieval_method": clean(signal.get("retrieval_method")),
                "public_signal_type": clean(signal.get("public_signal_status")) or clean(cluster.get("public_signal_corroboration")) or "none_captured",
                "public_signal_confidence": clean(cluster.get("public_signal_confidence")),
                "public_signal_count": clean(cluster.get("public_signal_count")) or "0",
                "public_signal_limitations_cue": clean(cluster.get("public_signal_limitations_cue")) or clean(signal.get("limitations")),
                "confirmation_gap": clean(cluster.get("manual_confirmation_gap")),
                "evidence_urls": clean(cluster.get("corroboration_evidence_urls")) or clean(cluster.get("matching_official_evidence_urls")) or clean(cluster.get("source_urls")),
                "source_or_intake_row_to_open": clean(cluster.get("exact_source_or_intake_row_to_open")),
                "freshness_or_proof_row_to_open": proof_target,
                "manual_confirmation_artifact": manual_artifact,
                "manual_confirmation_row_ref": manual_row_ref,
                "manual_confirmation_target": manual_target,
                "manual_return_fields_to_complete": "operator_checked_url; operator_confirmation_result; operator_confirmed_at_utc; operator_notes",
                "manual_return_operator_checked_url": "",
                "manual_return_operator_confirmation_result": "",
                "manual_return_operator_confirmed_at_utc": "",
                "manual_return_operator_notes": "",
                "manual_return_guardrail_cue": "Blank advisory return fields only; human edits belong in breaking_public_signal_confirmation_intake.csv and do not approve, enable, download, render, or publish.",
                "operator_next_action": breaking_next_action_text(cluster, priority),
                "review_limitations": "Review-only triage; public/community signal and free public source evidence do not confirm a breaking claim without human operator verification.",
                "review_only": "true",
                "approval_state_change": "false",
                "source_enablement": "false",
                "publish_action": "none_artifact_only",
            }
        )
    priority_order = {
        "P0_freshness_recheck_first": 0,
        "P1_official_confirmation_required": 1,
        "P2_reputable_or_gray_area_source_verify": 2,
        "P3_public_signal_review_only": 3,
        "P4_cluster_audit_no_fix": 4,
    }
    rows.sort(
        key=lambda row: (
            priority_order.get(row.get("review_priority"), 9),
            -int(clean(row.get("public_signal_count")) or "0"),
            row.get("cluster_headline", ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["action_rank"] = str(index)
    return rows


def breaking_signal_next_action_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        counts[clean(row.get("review_priority"))] += 1
    manual_return_blank_rows = sum(
        1
        for row in rows
        if not clean(row.get("manual_return_operator_checked_url"))
        and not clean(row.get("manual_return_operator_confirmation_result"))
        and not clean(row.get("manual_return_operator_confirmed_at_utc"))
        and not clean(row.get("manual_return_operator_notes"))
    )
    return {
        "version": "v1-review-only-breaking-public-signal-next-action",
        "generated_at_utc": utc_now(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "source_enablement": False,
        "publish_actions": False,
        "rows": len(rows),
        "freshness_recheck_first": counts.get("P0_freshness_recheck_first", 0),
        "official_confirmation_required": counts.get("P1_official_confirmation_required", 0),
        "reputable_gray_area_source_verify": counts.get("P2_reputable_or_gray_area_source_verify", 0),
        "public_signal_review_only": counts.get("P3_public_signal_review_only", 0),
        "cluster_audit_no_fix": counts.get("P4_cluster_audit_no_fix", 0),
        "manual_return_blank_rows": manual_return_blank_rows,
        "manual_return_fields_to_complete": [
            "operator_checked_url",
            "operator_confirmation_result",
            "operator_confirmed_at_utc",
            "operator_notes",
        ],
        "priority_counts": dict(sorted(counts.items())),
    }


def markdown_breaking_signal_next_action(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Breaking/Public Signal Next Actions v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only breaking/public-signal triage.",
        "- No paid APIs, downloads, source enablement, approvals, publishing, or publish-ready movement.",
        "- Rows are advisory only; operator decisions remain in the listed confirmation intake or proof artifact.",
        "",
        "## Counts",
        "",
    ]
    for key in [
        "rows",
        "freshness_recheck_first",
        "official_confirmation_required",
        "reputable_gray_area_source_verify",
        "public_signal_review_only",
        "cluster_audit_no_fix",
        "manual_return_blank_rows",
    ]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Review Order", ""])
    if not rows:
        lines.append("No breaking/public-signal next-action rows were generated in this run.")
    for row in rows[:80]:
        lines.append(f"{row.get('action_rank')}. **{row.get('cluster_headline')}** | {row.get('urgency_band')} | {row.get('review_priority')}")
        lines.append(f"   - status={row.get('verification_priority_status')} | confirmation={row.get('confirmation_state')} | evidence={row.get('official_reputable_gray_area_cue')}")
        lines.append(f"   - why_urgent={row.get('why_story_looks_urgent') or 'missing'}")
        lines.append(f"   - tier={row.get('source_confirmation_tier') or 'missing'} | freshness={row.get('source_freshness_status') or 'missing'} | age_min={row.get('source_freshness_age_minutes') or 'n/a'} | domain={row.get('source_domain_lead') or 'missing'}")
        lines.append(f"   - source_confidence={row.get('source_confidence_tier') or 'missing'} | reason={row.get('source_confidence_reason') or 'missing'} | signal_time={row.get('signal_timestamp_utc') or 'missing'} | retrieval={row.get('retrieval_method') or 'missing'}")
        lines.append(f"   - public_signal_type={row.get('public_signal_type') or 'missing'} confidence={row.get('public_signal_confidence') or 'none'} count={row.get('public_signal_count') or '0'} | limit={row.get('public_signal_limitations_cue') or row.get('review_limitations')}")
        lines.append(f"   - confirmation_gap={row.get('confirmation_gap') or 'missing'}")
        lines.append(f"   - open={row.get('source_or_intake_row_to_open') or 'missing'} | proof_or_freshness={row.get('freshness_or_proof_row_to_open') or 'missing'} | manual_artifact={row.get('manual_confirmation_artifact') or 'missing'} | manual_row={row.get('manual_confirmation_row_ref') or 'missing'}")
        lines.append(f"   - return_fields={row.get('manual_return_fields_to_complete') or 'missing'} | blank_return_fields=operator_checked_url/operator_confirmation_result/operator_confirmed_at_utc/operator_notes | guardrail={row.get('manual_return_guardrail_cue') or 'review-only'}")
        lines.append(f"   - next={row.get('operator_next_action')}")
    if len(rows) > 80:
        lines.append(f"Showing first 80 of {len(rows)} rows. Open `{BREAKING_SIGNAL_NEXT_ACTION_CSV}` for the full board.")
    return "\n".join(lines) + "\n"


def breaking_signal_return_summary_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary_rows: List[Dict[str, Any]] = []
    for item in rows:
        checked_url_present = bool(clean(item.get("manual_return_operator_checked_url")))
        confirmation_result_present = bool(clean(item.get("manual_return_operator_confirmation_result")))
        confirmed_at_present = bool(clean(item.get("manual_return_operator_confirmed_at_utc")))
        notes_present = bool(clean(item.get("manual_return_operator_notes")))
        source_confidence_present = bool(clean(item.get("source_confidence_tier")))
        source_domain_present = bool(clean(item.get("source_domain_lead")))
        missing_fields: List[str] = []
        if not checked_url_present:
            missing_fields.append("manual_return_operator_checked_url")
        if not confirmation_result_present:
            missing_fields.append("manual_return_operator_confirmation_result")
        if not source_confidence_present:
            missing_fields.append("source_confidence_tier")
        if checked_url_present and confirmation_result_present and source_confidence_present:
            manual_return_status = "operator_return_ready_for_review"
            manual_next_step = "Open the listed confirmation intake row and review the human-entered checked URL, confirmation result, and source-confidence cue; do not approve, enable, render, or publish from this summary."
        else:
            manual_return_status = "operator_return_missing_required_fields"
            manual_next_step = "Open breaking_public_signal_next_action_v1.csv and the listed confirmation intake row; fill only human-confirmed checked URL plus confirmation result before any source-trust review."
        summary_rows.append(
            {
                "summary_rank": clean(item.get("action_rank")),
                "cluster_id": clean(item.get("cluster_id")),
                "cluster_headline": clean(item.get("cluster_headline")),
                "review_priority": clean(item.get("review_priority")),
                "verification_priority_status": clean(item.get("verification_priority_status")),
                "manual_confirmation_artifact": clean(item.get("manual_confirmation_artifact")),
                "manual_confirmation_row_ref": clean(item.get("manual_confirmation_row_ref")),
                "operator_checked_url_present": "Yes" if checked_url_present else "No",
                "operator_confirmation_result_present": "Yes" if confirmation_result_present else "No",
                "operator_confirmed_at_utc_present": "Yes" if confirmed_at_present else "No",
                "operator_notes_present": "Yes" if notes_present else "No",
                "source_confidence_tier_present": "Yes" if source_confidence_present else "No",
                "source_domain_lead_present": "Yes" if source_domain_present else "No",
                "manual_return_status": manual_return_status,
                "missing_return_fields": "; ".join(missing_fields) if missing_fields else "none",
                "manual_next_step": manual_next_step,
                "source_or_intake_row_to_open": clean(item.get("source_or_intake_row_to_open")),
                "freshness_or_proof_row_to_open": clean(item.get("freshness_or_proof_row_to_open")),
                "review_only": "Yes",
                "approval_state_change": "none",
                "source_enablement": "none_existing_local_artifacts_only",
                "publish_action": "none_artifact_only",
            }
        )
    summary_rows.sort(
        key=lambda row: (
            row.get("manual_return_status") != "operator_return_missing_required_fields",
            row.get("summary_rank", ""),
            row.get("cluster_headline", ""),
        )
    )
    for index, row in enumerate(summary_rows, start=1):
        row["summary_rank"] = str(index)
    return summary_rows


def breaking_signal_return_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_counts: Dict[str, int] = defaultdict(int)
    priority_counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        status_counts[clean(row.get("manual_return_status"))] += 1
        priority_counts[clean(row.get("review_priority"))] += 1
    return {
        "version": "v1-review-only-breaking-public-signal-return-summary",
        "generated_at_utc": utc_now(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "source_enablement": False,
        "publish_actions": False,
        "rows": len(rows),
        "operator_return_ready_for_review": status_counts.get("operator_return_ready_for_review", 0),
        "operator_return_missing_required_fields": status_counts.get("operator_return_missing_required_fields", 0),
        "missing_operator_checked_url": sum(1 for row in rows if row.get("operator_checked_url_present") != "Yes"),
        "missing_operator_confirmation_result": sum(1 for row in rows if row.get("operator_confirmation_result_present") != "Yes"),
        "missing_source_confidence_tier": sum(1 for row in rows if row.get("source_confidence_tier_present") != "Yes"),
        "missing_source_domain_lead": sum(1 for row in rows if row.get("source_domain_lead_present") != "Yes"),
        "rows_with_operator_notes": sum(1 for row in rows if row.get("operator_notes_present") == "Yes"),
        "status_counts": dict(sorted(status_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
    }


def markdown_breaking_signal_return_summary(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Breaking/Public Signal Return Summary v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only summary of breaking/public-signal manual return fields.",
        "- No fetching, paid APIs, downloads, source enablement, approvals, rendering, publishing, or publish-ready movement.",
        "- A ready-for-review row is not source approval; it only means required manual return fields are present for operator review.",
        "",
        "## Counts",
        "",
    ]
    for key in [
        "rows",
        "operator_return_ready_for_review",
        "operator_return_missing_required_fields",
        "missing_operator_checked_url",
        "missing_operator_confirmation_result",
        "missing_source_confidence_tier",
        "missing_source_domain_lead",
        "rows_with_operator_notes",
    ]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Missing Return Fields", ""])
    missing = [row for row in rows if row.get("manual_return_status") == "operator_return_missing_required_fields"]
    if not missing:
        lines.append("No breaking/public-signal rows are missing the required manual return fields in this snapshot.")
    for row in missing[:80]:
        lines.append(f"- **{row.get('cluster_headline')}** | {row.get('review_priority')} | {row.get('verification_priority_status')}")
        lines.append(f"  - missing={row.get('missing_return_fields')}")
        lines.append(f"  - intake={row.get('manual_confirmation_artifact')} {row.get('manual_confirmation_row_ref')}".rstrip())
        lines.append(f"  - next={row.get('manual_next_step')}")
    if len(missing) > 80:
        lines.append(f"Showing first 80 of {len(missing)} missing rows. Open `{BREAKING_SIGNAL_RETURN_SUMMARY_CSV}` for the full summary.")
    lines.extend(["", "## Ready For Operator Review", ""])
    ready = [row for row in rows if row.get("manual_return_status") == "operator_return_ready_for_review"]
    if not ready:
        lines.append("No rows currently have checked URL, confirmation result, and source confidence present.")
    for row in ready[:80]:
        lines.append(f"- **{row.get('cluster_headline')}** | status={row.get('manual_return_status')} | intake={row.get('manual_confirmation_artifact')} {row.get('manual_confirmation_row_ref')}".rstrip())
    return "\n".join(lines) + "\n"


def game_source_confirmation_bridge_rows(
    *,
    run_id: str,
    game_rows: List[Dict[str, Any]],
    stats_rows: List[Dict[str, Any]],
    cluster_rows: List[Dict[str, Any]],
    packets: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for game in game_rows:
        if clean(game.get("status")).lower() != "final" and clean(game.get("recap_candidate")) != "Yes":
            continue
        row_id = clean(game.get("row_id"))
        stats = stats_row_for_game(game, stats_rows)
        cluster = cluster_for_game_row(game, cluster_rows)
        packet = news_packet_for_cluster(cluster, packets) if cluster else {}
        game_url = clean(game.get("source_url"))
        game_domain = clean(game.get("source_domain")) or source_domain_from_url(game_url)
        game_status = "official_or_free_game_evidence_present_operator_verify" if game_url and is_free_result_domain(game_domain) else "missing_official_or_free_game_evidence"
        stats_status = clean(stats.get("stats_evidence_status")) or "missing_stats_evidence_row"
        cross_status = clean(cluster.get("matching_official_evidence_status")) or "missing_cross_signal_cluster"
        cluster_ref = f"cluster_id={clean(cluster.get('cluster_id'))}" if cluster else ""
        packet_ref = f"candidate_id={clean(packet.get('candidate_id'))}" if packet else ""
        stats_ref = f"event_uid={clean(stats.get('event_uid'))}" if stats else ""
        source_urls = []
        if cluster:
            append_unique_urls(source_urls, parse_json_list(cluster.get("matching_official_evidence_urls")))
        if packet:
            append_unique_urls(source_urls, parse_json_list(packet.get("source_urls_json")))
        append_unique_urls(source_urls, [game_url])
        stats_url = clean(stats.get("confirmation_source_url"))
        append_unique_urls(source_urls, [stats_url])
        next_parts = [
            f"Open game_intelligence_board_v1.csv row_id={row_id}" if row_id else "Open game_intelligence_board_v1.csv matching this game",
        ]
        if stats_ref:
            next_parts.append(f"open stats_evidence_gap_board_v1.csv {stats_ref}")
        else:
            next_parts.append("open stats_confirmation_intake_v1.csv and add/check the missing stat evidence row")
        if cluster_ref:
            next_parts.append(f"open breaking_public_signal_clusters.csv {cluster_ref}")
        else:
            next_parts.append("open breaking_public_signal_clusters.csv and confirm whether a current news cluster exists")
        if packet_ref:
            next_parts.append(f"open news_fact_packets.csv {packet_ref}")
        next_parts.append(
            "record breaking-claim confirmation in breaking_public_signal_confirmation_intake.csv and score/stat proof confirmation in final_score_stat_proof_confirmation_intake_v1.csv before editorial use"
        )
        rows.append(
            {
                "bridge_id": "game_confirm_" + stable_id(run_id, row_id, game.get("final_score")),
                "run_id": run_id,
                "game_row_ref": f"row_id={row_id}" if row_id else "",
                "game_date": clean(game.get("game_date")),
                "league": clean(game.get("league")),
                "matchup": f"{clean(game.get('away_team'))} at {clean(game.get('home_team'))}".strip(),
                "final_score": clean(game.get("final_score")),
                "recap_candidate": clean(game.get("recap_candidate")),
                "official_free_game_evidence_status": game_status,
                "game_source_url": game_url,
                "game_source_domain": game_domain,
                "stats_evidence_status": stats_status,
                "stats_row_ref": stats_ref,
                "stats_source_url": stats_url,
                "top_performers": clean(stats.get("top_performers")),
                "cross_signal_status": cross_status,
                "cluster_row_ref": cluster_ref,
                "news_packet_ref": packet_ref,
                "news_or_cluster_source_urls": json.dumps(source_urls[:12], ensure_ascii=False),
                "manual_confirmation_needed": "true",
                "exact_next_row_or_source_to_open": "; then ".join(next_parts) + ".",
                "operator_confirmation_target": "breaking_public_signal_confirmation_intake.csv for breaking claim/source URL; final_score_stat_proof_confirmation_intake_v1.csv for final score and named-player stat proof; stats_confirmation_intake_v1.csv only if a stat evidence row is missing",
                "limitations": "Review-only bridge across existing artifacts; it does not confirm claims, approve stats/stories/renders/sources, publish, or create a publish-ready lane.",
                "manual_review_required": "true",
                "review_only": "true",
                "publish_ready": "false",
                "auto_publish": "false",
                "auto_source_enablement": "false",
                "approval_state_change": "false",
            }
        )
    rows.sort(key=lambda row: (row.get("cross_signal_status") == "missing_cross_signal_cluster", row.get("game_date", ""), row.get("matchup", "")))
    return rows


def markdown_game_source_confirmation_bridge(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Source Confirmation Bridge v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Review-only bridge across game, stat, and breaking/news artifacts. It tells the operator what to open next; it does not approve anything.",
        "",
    ]
    if not rows:
        lines.extend(["No final/recap game rows are available for confirmation bridging.", ""])
        return "\n".join(lines) + "\n"
    for row in rows[:60]:
        lines.extend(
            [
                f"## {row.get('matchup')} | {row.get('game_date')}",
                "",
                f"- Game evidence: `{row.get('official_free_game_evidence_status')}` / {row.get('game_source_url') or 'missing'}",
                f"- Stat evidence: `{row.get('stats_evidence_status')}` / {row.get('stats_row_ref') or 'missing'}",
                f"- Cross-signal evidence: `{row.get('cross_signal_status')}` / {row.get('cluster_row_ref') or 'missing'}",
                f"- News packet: `{row.get('news_packet_ref') or 'missing'}`",
                f"- Exact next row/source: {row.get('exact_next_row_or_source_to_open')}",
                f"- Guardrail: review_only={row.get('review_only')} publish_ready={row.get('publish_ready')} auto_publish={row.get('auto_publish')} approval_state_change={row.get('approval_state_change')}",
                "",
            ]
        )
    if len(rows) > 60:
        lines.append(f"Showing first 60 of {len(rows)} rows. Open `game_source_confirmation_bridge_v1.csv` for the full bridge.")
    return "\n".join(lines) + "\n"


def markdown_brief_queue(packets: List[Dict[str, Any]], observations_by_candidate: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = [
        "# Her Sports Daily News Brief Queue v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "This is the news layer on top of Results Desk. Results Desk remains the score source of truth.",
        "",
    ]

    for section in ["MUST POST", "STRONG MAYBE", "DIVERSITY WATCH"]:
        group = [p for p in packets if p.get("queue_section") == section]
        lines.extend([f"## {section}", ""])
        if not group:
            lines.extend(["No items.", ""])
            continue

        for idx, p in enumerate(group, 1):
            cid = p.get("candidate_id")
            source_obs = observations_by_candidate.get(cid, [])
            urls = []
            try:
                urls = json.loads(p.get("source_urls_json") or "[]")
            except Exception:
                urls = []

            lines.extend([
                f"### NEWS PACKET {idx}: {p.get('headline')}",
                "",
                f"**Urgency:** {p.get('urgency')}",
                f"**Content family:** {p.get('content_family')}",
                f"**Recommendation:** {p.get('publish_recommendation')}",
                f"**Manual review:** {p.get('manual_review')}",
            f"**Event date:** {p.get('event_date') or 'missing'}",
                f"**Review flags:** {p.get('review_flags') or 'None'}",
                f"**Source depth:** {p.get('source_count')} usable / {p.get('primary_source_count')} primary",
                f"**Event date:** {p.get('event_date') or 'missing'}",
                "",
                "#### Headline",
                p.get("headline", ""),
                "",
                "#### Dek",
                p.get("dek", ""),
                "",
                "#### Short brief",
                p.get("brief_120w", ""),
                "",
                "#### Caption options",
                f"- Hard fact: {p.get('caption_hard_fact')}",
                f"- Voice: {p.get('caption_voice')}",
                "",
                "#### Story text",
                p.get("story_text", ""),
                "",
                "#### Slide 3 / context",
                p.get("slide3_context", ""),
                "",
                "#### Sources",
            ])

            if urls:
                for url in urls[:8]:
                    lines.append(f"- {url}")
            else:
                lines.append("- No usable source URL captured. Hold if this is Must Post.")

            if source_obs:
                lines.extend(["", "#### Source observation notes"])
                for obs in source_obs[:6]:
                    lines.append(
                        f"- {obs.get('source_name')} | {obs.get('fetch_status')} | "
                        f"{obs.get('usable_context')} | {obs.get('context_signal') or obs.get('notes')}"
                    )

            lines.extend(["", "---", ""])

    return "\n".join(lines)


def markdown_social_packets(packets: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Social Packets v1",
        "",
        f"Generated: {utc_now()}",
        "",
    ]
    for p in packets:
        lines.extend([
            f"## {p.get('headline')}",
            "",
            f"**Queue:** {p.get('queue_section')} | **Manual review:** {p.get('manual_review')} | **Event date:** {p.get('event_date') or 'missing'}",
            "",
            "### Instagram caption",
            p.get("caption_voice", ""),
            "",
            "### X / Threads / Bluesky",
            p.get("caption_hard_fact", ""),
            "",
            "### Story text",
            p.get("story_text", ""),
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def markdown_graphics_handoff(packets: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily News-to-Graphics Handoff v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use this to upgrade result graphics with news-safe context.",
        "",
    ]
    for p in packets:
        lines.extend([
            f"## {p.get('headline')}",
            "",
            f"**Content family:** {p.get('content_family')}",
            f"**Manual review:** {p.get('manual_review')}",
            f"**Event date:** {p.get('event_date') or 'missing'}",
            "",
            p.get("graphics_handoff", ""),
            "",
            "**Accuracy lock:** Do not change score, winner, loser, or player stats beyond this packet.",
            "",
            "---",
            "",
        ])
    return "\n".join(lines)



def markdown_daily_plan(packets: List[Dict[str, Any]]) -> str:
    ready = [p for p in packets if p.get("manual_review") != "Yes"]
    p1 = [p for p in ready if p.get("urgency") == "P1"]
    p2 = [p for p in ready if p.get("urgency") == "P2"]
    diversity = [p for p in ready if p.get("queue_section") == "DIVERSITY WATCH"]

    lines = [
        "# Her Sports Daily News Daily Plan v1.8",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Recommended production order",
        "",
    ]

    if p1:
        lines.append("### 1. Main post")
        lead = p1[0]
        lines.extend([
            f"- **{lead.get('headline')}**",
            f"- Format: {lead.get('content_format_recommendation')}",
            f"- Why: {lead.get('context_quality')} context quality, score {lead.get('quality_score')}/100",
            f"- Caption seed: {lead.get('caption_voice')}",
            "",
        ])

        if len(p1) > 1:
            lines.append("### 2. WNBA story/roundup candidates")
            for p in p1[1:5]:
                lines.append(f"- **{p.get('headline')}** | {p.get('content_format_recommendation')} | {p.get('context_quality')}")
            lines.append("")

    if p2:
        lines.append("### 3. Around Women's Sports roundup")
        for p in p2[:5]:
            lines.append(f"- **{p.get('headline')}** | {p.get('sport')} | {p.get('caption_hard_fact')}")
        lines.append("")

    if diversity:
        lines.append("### 4. Diversity watch")
        for p in diversity[:MAX_DIVERSITY_PROMOTIONS]:
            lines.append(f"- **{p.get('headline')}** | {p.get('sport')} | {p.get('caption_hard_fact')}")
        lines.append("")

    lines.extend([
        "## Do not post without review",
        "",
    ])
    held = [p for p in packets if p.get("manual_review") == "Yes"]
    if held:
        for p in held:
            lines.append(f"- **{p.get('headline')}** | flags: {p.get('review_flags')}")
    else:
        lines.append("- No held packets.")

    lines.extend([
        "",
        "## Notes",
        "",
        "- Results Desk remains the score source of truth.",
        "- News Sync adds context and production copy only.",
        "- Player stats must come from the packet or a verified box-score source.",
    ])

    return "\\n".join(lines) + "\\n"


def markdown_hub(run_id: str, candidates: List[Dict[str, Any]], observations: List[Dict[str, Any]], packets: List[Dict[str, Any]]) -> str:
    manual = [p for p in packets if p.get("manual_review") == "Yes"]
    publish = [p for p in packets if p.get("manual_review") != "Yes"]
    p1 = [p for p in packets if p.get("urgency") == "P1"]
    p2 = [p for p in packets if p.get("urgency") == "P2"]
    diversity = [p for p in packets if p.get("queue_section") == "DIVERSITY WATCH"]
    production_ready = [p for p in packets if p.get("production_ready") == "Yes"]

    usable_sources = [o for o in observations if o.get("usable_context") in {"Yes", "Partial"}]
    source_failures = [o for o in observations if o.get("review_flag")]

    lines = [
        "# Her Sports Daily News Sync v1.8 Hub",
        "",
        f"Run ID: `{run_id}`",
        f"Generated: `{utc_now()}`",
        "",
        "## Architecture",
        "",
        "- Results Desk remains the scorer of record.",
        "- News Sync consumes Results Desk outputs and builds source-backed editorial packets.",
        "- The two systems are connected, but not merged into one fragile scraper.",
        "",
        "## Run summary",
        "",
        f"- News candidates read: {len(candidates)}",
        f"- Source observations: {len(observations)}",
        f"- Usable source observations: {len(usable_sources)}",
        f"- Fact packets built: {len(packets)}",
        f"- Publish-ready packets: {len(publish)}",
        f"- Production-ready packets: {len(production_ready)}",
        f"- Manual review packets: {len(manual)}",
        f"- P1 / Must Post packets: {len(p1)}",
        f"- P2 / Strong Maybe plus diversity packets: {len(p2)}",
        f"- Diversity Watch packets: {len(diversity)}",
        f"- Source fetch flags: {len(source_failures)}",
        "",
        "## Manual review rules",
        "",
        "- Hold if Results Desk marked the item for review.",
        "- Hold if Must Post has neither top-performer data nor a primary/official source.",
        "- Hold if no usable source context was captured.",
        "- Never invent player stats, rankings, quotes, injuries, or milestones.",
        "- Final score must be present, or packet is held.",
        "- Store facts, summaries, and links only. Do not copy full article text.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    run_id = stable_id(VERSION, utc_now())

    registry = merge_source_registry(load_json(SOURCE_REGISTRY_FILE, {}))
    angle_rules = load_json(ANGLE_RULES_FILE, angle_rules_defaults())

    queue_path, queue_text = resolve_input(INPUT_RESULTS_QUEUE)
    recs_path, recs_text = resolve_input(INPUT_RESULTS_RECS)
    box_path, box_text = resolve_input(INPUT_WNBA_BOX)
    hub_path, hub_text = resolve_input(INPUT_RESULTS_HUB)

    top_csv_path, top_csv_rows = resolve_csv_input(INPUT_RESULTS_TOP_CSV)
    reconciled_csv_path, reconciled_csv_rows = resolve_csv_input(INPUT_RESULTS_RECONCILED_CSV)
    finals_csv_path, finals_csv_rows = resolve_csv_input(INPUT_RESULTS_FINALS_CSV)
    game_intelligence_path, game_intelligence_rows = resolve_csv_input(INPUT_GAME_INTELLIGENCE_CSV)
    stats_evidence_path, stats_evidence_rows = resolve_csv_input(INPUT_STATS_EVIDENCE_CSV)
    proof_path, proof_rows = resolve_csv_input(INPUT_FINAL_SCORE_STAT_PROOF_CSV)
    proof_confirmation_path, proof_confirmation_rows = resolve_csv_input(INPUT_FINAL_SCORE_STAT_PROOF_CONFIRMATION_CSV)
    proof_review_order_path, proof_review_order_rows = resolve_csv_input(INPUT_FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_CSV)
    game_fact_confirmation_path, game_fact_confirmation_rows = resolve_csv_input(INPUT_GAME_FACT_CONFIRMATION_STATUS_CSV)
    story_proof_card_path, story_proof_card_rows = resolve_csv_input(INPUT_STORY_PROOF_CARD_CSV)

    csv_sources = [
        ("top_womens_results.csv", top_csv_rows),
        ("reconciled_events.csv", reconciled_csv_rows),
        ("today_final_results.csv", finals_csv_rows),
    ]

    input_status = [
        input_status_row("results_graphics_queue", INPUT_RESULTS_QUEUE, queue_text, queue_path),
        input_status_row("daily_results_recommendations", INPUT_RESULTS_RECS, recs_text, recs_path),
        input_status_row("wnba_box_score_summary", INPUT_WNBA_BOX, box_text, box_path),
        input_status_row("results_system_hub", INPUT_RESULTS_HUB, hub_text, hub_path),
        input_status_row_csv("top_womens_results_csv", INPUT_RESULTS_TOP_CSV, top_csv_rows, top_csv_path),
        input_status_row_csv("reconciled_events_csv", INPUT_RESULTS_RECONCILED_CSV, reconciled_csv_rows, reconciled_csv_path),
        input_status_row_csv("today_final_results_csv", INPUT_RESULTS_FINALS_CSV, finals_csv_rows, finals_csv_path),
        input_status_row_csv("game_intelligence_board_csv", INPUT_GAME_INTELLIGENCE_CSV, game_intelligence_rows, game_intelligence_path),
        input_status_row_csv("stats_evidence_gap_board_csv", INPUT_STATS_EVIDENCE_CSV, stats_evidence_rows, stats_evidence_path),
        input_status_row_csv("final_score_stat_proof_csv", INPUT_FINAL_SCORE_STAT_PROOF_CSV, proof_rows, proof_path),
        input_status_row_csv(
            "final_score_stat_proof_confirmation_intake_csv",
            INPUT_FINAL_SCORE_STAT_PROOF_CONFIRMATION_CSV,
            proof_confirmation_rows,
            proof_confirmation_path,
        ),
        input_status_row_csv(
            "final_score_stat_proof_review_order_csv",
            INPUT_FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_CSV,
            proof_review_order_rows,
            proof_review_order_path,
        ),
        input_status_row_csv(
            "game_fact_confirmation_status_csv",
            INPUT_GAME_FACT_CONFIRMATION_STATUS_CSV,
            game_fact_confirmation_rows,
            game_fact_confirmation_path,
        ),
        input_status_row_csv(
            "story_proof_card_csv",
            INPUT_STORY_PROOF_CARD_CSV,
            story_proof_card_rows,
            story_proof_card_path,
        ),
    ]

    csv_candidates = candidates_from_result_csvs(run_id, csv_sources)
    markdown_candidates = parse_graphics_queue(queue_text, run_id)

    if csv_candidates:
        candidates = csv_candidates
        input_status[4]["notes"] = f"Used CSV-primary candidate builder with {len(candidates)} candidates. Markdown remains backup."
        if markdown_candidates:
            input_status[0]["notes"] = f"Markdown parser also found {len(markdown_candidates)} candidates, but CSV-primary mode was used."
        else:
            input_status[0]["notes"] = "Markdown queue did not produce candidates. CSV-primary mode avoided failure."
    else:
        candidates = markdown_candidates
        if candidates:
            input_status[0]["notes"] = f"Parsed {len(candidates)} candidates from graphics queue."
            candidates = enrich_candidates_from_result_csvs(candidates, csv_sources)
        else:
            fallback_candidates = parse_recommendations_fallback(recs_text, run_id)
            if fallback_candidates:
                candidates = enrich_candidates_from_result_csvs(fallback_candidates, csv_sources)
                input_status[1]["notes"] = "Used fallback parser because CSV and graphics queue produced 0 candidates."
            else:
                input_status[0]["notes"] = "No RESULT GRAPHIC blocks parsed. Check that Results Desk has run and committed results_graphics_queue.md."
                input_status[1]["notes"] = "Fallback recommendations parser also produced 0 candidates."
                input_status[4]["notes"] = "CSV candidate builder also produced 0 candidates."

    candidates = dedupe_candidates(candidates)

    box_map = parse_box_score_summary(box_text)

    all_observations: List[Dict[str, Any]] = []
    observations_by_candidate: Dict[str, List[Dict[str, Any]]] = {}

    for candidate in candidates:
        obs = source_observations_for_candidate(candidate, registry, run_id)
        all_observations.extend(obs)
        observations_by_candidate[candidate["candidate_id"]] = obs

    packets = []
    for candidate in candidates:
        obs = observations_by_candidate.get(candidate["candidate_id"], [])
        packet = build_fact_packet(candidate, obs, box_map, angle_rules, run_id)
        packets.append(packet)

    breaking_signal_rows = build_breaking_public_signal_rows(packets, observations_by_candidate, run_id)
    confirmation_intake_rows = breaking_confirmation_intake_rows(breaking_signal_rows)
    cluster_rows = breaking_signal_cluster_rows(
        breaking_signal_rows,
        packets=packets,
        game_rows=game_intelligence_rows,
        proof_rows=proof_rows,
        proof_confirmation_rows=proof_confirmation_rows,
        proof_review_order_rows=proof_review_order_rows,
        game_fact_confirmation_rows=game_fact_confirmation_rows,
        story_proof_card_rows=story_proof_card_rows,
        intake_rows=confirmation_intake_rows,
    )
    breaking_next_action_rows = breaking_signal_next_action_rows(cluster_rows, breaking_signal_rows)
    breaking_next_action_summary = breaking_signal_next_action_summary(breaking_next_action_rows)
    breaking_return_summary_rows = breaking_signal_return_summary_rows(breaking_next_action_rows)
    breaking_return_summary = breaking_signal_return_summary(breaking_return_summary_rows)
    game_source_bridge_rows = game_source_confirmation_bridge_rows(
        run_id=run_id,
        game_rows=game_intelligence_rows,
        stats_rows=stats_evidence_rows,
        cluster_rows=cluster_rows,
        packets=packets,
    )
    manual_packets = [p for p in packets if p.get("manual_review") == "Yes"]

    write_csv(NEWS_INPUT_STATUS_CSV, input_status, INPUT_STATUS_FIELDS)
    write_csv(NEWS_CANDIDATES_CSV, candidates, CANDIDATE_FIELDS)
    write_csv(NEWS_SOURCE_OBS_CSV, all_observations, SOURCE_OBS_FIELDS)
    write_csv(NEWS_FACT_PACKETS_CSV, packets, PACKET_FIELDS)
    write_csv(NEWS_MANUAL_REVIEW_CSV, manual_packets, PACKET_FIELDS)
    write_csv(BREAKING_PUBLIC_SIGNAL_CSV, breaking_signal_rows, BREAKING_PUBLIC_SIGNAL_FIELDS)
    write_csv(BREAKING_CONFIRMATION_INTAKE_CSV, confirmation_intake_rows, BREAKING_CONFIRMATION_INTAKE_FIELDS)
    write_csv(BREAKING_SIGNAL_CLUSTERS_CSV, cluster_rows, BREAKING_SIGNAL_CLUSTER_FIELDS)
    write_csv(BREAKING_SIGNAL_NEXT_ACTION_CSV, breaking_next_action_rows, BREAKING_SIGNAL_NEXT_ACTION_FIELDS)
    write_csv(BREAKING_SIGNAL_RETURN_SUMMARY_CSV, breaking_return_summary_rows, BREAKING_SIGNAL_RETURN_SUMMARY_FIELDS)
    write_csv(GAME_SOURCE_CONFIRMATION_BRIDGE_CSV, game_source_bridge_rows, GAME_SOURCE_CONFIRMATION_BRIDGE_FIELDS)

    write_run_text(NEWS_BRIEF_QUEUE_MD, markdown_brief_queue(packets, observations_by_candidate))
    write_run_text(NEWS_SOCIAL_PACKETS_MD, markdown_social_packets(packets))
    write_run_text(NEWS_GRAPHICS_HANDOFF_MD, markdown_graphics_handoff(packets))
    write_run_text(NEWS_DAILY_PLAN_MD, markdown_daily_plan(packets))
    write_run_text(BREAKING_PUBLIC_SIGNAL_MD, markdown_breaking_public_signal(breaking_signal_rows))
    write_run_text(BREAKING_CONFIRMATION_INTAKE_MD, markdown_breaking_confirmation_intake(confirmation_intake_rows))
    write_run_text(BREAKING_SIGNAL_CLUSTERS_MD, markdown_breaking_signal_clusters(cluster_rows))
    write_run_text(BREAKING_SIGNAL_NEXT_ACTION_MD, markdown_breaking_signal_next_action(breaking_next_action_summary, breaking_next_action_rows))
    write_run_text(BREAKING_SIGNAL_RETURN_SUMMARY_MD, markdown_breaking_signal_return_summary(breaking_return_summary, breaking_return_summary_rows))
    write_run_text(GAME_SOURCE_CONFIRMATION_BRIDGE_MD, markdown_game_source_confirmation_bridge(game_source_bridge_rows))
    write_run_json(
        BREAKING_SIGNAL_NEXT_ACTION_JSON,
        {
            "summary": breaking_next_action_summary,
            "rows": breaking_next_action_rows,
        },
    )
    write_run_json(
        BREAKING_SIGNAL_RETURN_SUMMARY_JSON,
        {
            "summary": breaking_return_summary,
            "rows": breaking_return_summary_rows,
        },
    )
    write_run_text(NEWS_SYNC_HUB_MD, markdown_hub(run_id, candidates, all_observations, packets))
    write_run_json(
        GAME_SOURCE_CONFIRMATION_BRIDGE_JSON,
        {
            "version": "v1-review-only-game-source-confirmation-bridge",
            "run_id": run_id,
            "generated_at_utc": utc_now(),
            "review_only": True,
            "publish_ready": False,
            "auto_publish": False,
            "auto_source_enablement": False,
            "approval_state_change": False,
            "counts": {
                "rows": len(game_source_bridge_rows),
                "with_game_evidence": len([row for row in game_source_bridge_rows if row.get("official_free_game_evidence_status") == "official_or_free_game_evidence_present_operator_verify"]),
                "with_stats_evidence": len([row for row in game_source_bridge_rows if clean(row.get("stats_evidence_status")) not in {"", "missing_stats_evidence_row"}]),
                "with_cross_signal_cluster": len([row for row in game_source_bridge_rows if clean(row.get("cross_signal_status")) != "missing_cross_signal_cluster"]),
            },
            "rows": game_source_bridge_rows,
        },
    )
    write_run_json(
        BREAKING_PUBLIC_SIGNAL_JSON,
        {
            "version": VERSION,
            "run_id": run_id,
            "generated_at_utc": utc_now(),
            "review_only": True,
            "publish_ready": False,
            "auto_publish": False,
            "auto_source_enablement": False,
            "counts": {
                "rows": len(breaking_signal_rows),
                "p0_breaking_review": len([row for row in breaking_signal_rows if row.get("urgency_band") == "P0_breaking_review"]),
                "with_public_signal": len([row for row in breaking_signal_rows if row.get("public_signal_count") not in {"", "0"}]),
                "confirmation_intake_rows": len(confirmation_intake_rows),
                "cluster_rows": len(cluster_rows),
                "breaking_next_action_rows": len(breaking_next_action_rows),
                "breaking_return_summary_rows": len(breaking_return_summary_rows),
                "breaking_return_summary_missing_operator_checked_url": breaking_return_summary.get("missing_operator_checked_url", 0),
                "breaking_return_summary_missing_operator_confirmation_result": breaking_return_summary.get("missing_operator_confirmation_result", 0),
                "breaking_return_summary_missing_source_confidence_tier": breaking_return_summary.get("missing_source_confidence_tier", 0),
                "game_source_confirmation_bridge_rows": len(game_source_bridge_rows),
                "clusters_with_matching_current_artifact_evidence": len([
                    row for row in cluster_rows
                    if clean(row.get("matching_official_evidence_status")) != "no_matching_current_artifact_evidence_operator_confirmation_required"
                ]),
                "clusters_with_score_stat_proof": len([
                    row for row in cluster_rows
                    if clean(row.get("score_stat_proof_status")) not in {"", "no_matching_score_stat_proof_operator_confirmation_required"}
                ]),
                "clusters_with_named_player_stat_proof": len([
                    row for row in cluster_rows
                    if clean(row.get("named_player_stat_proof_count")) not in {"", "0"}
                ]),
                "clusters_with_score_stat_confirmation_targets": len([
                    row for row in cluster_rows
                    if clean(row.get("score_proof_confirmation_target")) or clean(row.get("named_player_stat_proof_confirmation_targets"))
                ]),
                "clusters_with_score_stat_review_order_targets": len([
                    row for row in cluster_rows
                    if clean(row.get("first_score_stat_review_order_target"))
                ]),
                "clusters_with_corroboration_ladder": len([
                    row for row in cluster_rows
                    if clean(row.get("corroboration_ladder_status"))
                ]),
                "clusters_with_story_proof_readiness": len([
                    row for row in cluster_rows
                    if clean(row.get("source_proof_readiness_status")) == "story_proof_card_ready_operator_verify"
                ]),
                "clusters_with_verification_priority": len([
                    row for row in cluster_rows
                    if clean(row.get("verification_priority_status"))
                ]),
                "clusters_requiring_official_source_first": len([
                    row for row in cluster_rows
                    if clean(row.get("verification_priority_status")) == "official_source_confirmation_first"
                ]),
                "clusters_with_game_source_confirmation_tier": len([
                    row for row in cluster_rows
                    if clean(row.get("game_source_confirmation_tier"))
                    and clean(row.get("game_source_confirmation_tier")) != "game_source_tier_missing_from_current_artifacts"
                ]),
                "clusters_with_game_source_freshness": len([
                    row for row in cluster_rows
                    if clean(row.get("game_source_freshness_status"))
                    and clean(row.get("game_source_freshness_status")) != "game_source_freshness_missing_current_artifact"
                ]),
                "clusters_requiring_source_freshness_recheck": len([
                    row for row in cluster_rows
                    if clean(row.get("verification_priority_status")) == "source_freshness_recheck_first"
                ]),
                "breaking_next_actions_official_confirmation_required": breaking_next_action_summary.get("official_confirmation_required", 0),
                "breaking_next_actions_freshness_recheck_first": breaking_next_action_summary.get("freshness_recheck_first", 0),
            },
            "outputs": [
                BREAKING_PUBLIC_SIGNAL_CSV,
                BREAKING_PUBLIC_SIGNAL_MD,
                BREAKING_CONFIRMATION_INTAKE_CSV,
                BREAKING_CONFIRMATION_INTAKE_MD,
                BREAKING_SIGNAL_CLUSTERS_CSV,
                BREAKING_SIGNAL_CLUSTERS_MD,
                BREAKING_SIGNAL_NEXT_ACTION_CSV,
                BREAKING_SIGNAL_NEXT_ACTION_MD,
                BREAKING_SIGNAL_NEXT_ACTION_JSON,
                BREAKING_SIGNAL_RETURN_SUMMARY_CSV,
                BREAKING_SIGNAL_RETURN_SUMMARY_MD,
                BREAKING_SIGNAL_RETURN_SUMMARY_JSON,
                GAME_SOURCE_CONFIRMATION_BRIDGE_CSV,
                GAME_SOURCE_CONFIRMATION_BRIDGE_MD,
                GAME_SOURCE_CONFIRMATION_BRIDGE_JSON,
            ],
        },
    )

    manifest = {
        "version": VERSION,
        "run_id": run_id,
        "generated_at_utc": utc_now(),
        "inputs": {
            "results_graphics_queue": INPUT_RESULTS_QUEUE,
            "daily_results_recommendations": INPUT_RESULTS_RECS,
            "wnba_box_score_summary": INPUT_WNBA_BOX,
            "results_system_hub": INPUT_RESULTS_HUB,
            "top_womens_results_csv": INPUT_RESULTS_TOP_CSV,
            "reconciled_events_csv": INPUT_RESULTS_RECONCILED_CSV,
            "today_final_results_csv": INPUT_RESULTS_FINALS_CSV,
            "game_intelligence_board_csv": INPUT_GAME_INTELLIGENCE_CSV,
            "stats_evidence_gap_board_csv": INPUT_STATS_EVIDENCE_CSV,
            "final_score_stat_proof_csv": INPUT_FINAL_SCORE_STAT_PROOF_CSV,
            "final_score_stat_proof_confirmation_intake_csv": INPUT_FINAL_SCORE_STAT_PROOF_CONFIRMATION_CSV,
            "final_score_stat_proof_review_order_csv": INPUT_FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_CSV,
            "game_fact_confirmation_status_csv": INPUT_GAME_FACT_CONFIRMATION_STATUS_CSV,
            "story_proof_card_csv": INPUT_STORY_PROOF_CARD_CSV,
        },
        "outputs": [
            NEWS_INPUT_STATUS_CSV,
            NEWS_CANDIDATES_CSV,
            NEWS_SOURCE_OBS_CSV,
            NEWS_FACT_PACKETS_CSV,
            NEWS_BRIEF_QUEUE_MD,
            NEWS_SOCIAL_PACKETS_MD,
            NEWS_GRAPHICS_HANDOFF_MD,
            NEWS_DAILY_PLAN_MD,
            NEWS_MANUAL_REVIEW_CSV,
            BREAKING_PUBLIC_SIGNAL_CSV,
            BREAKING_PUBLIC_SIGNAL_MD,
            BREAKING_PUBLIC_SIGNAL_JSON,
            BREAKING_CONFIRMATION_INTAKE_CSV,
            BREAKING_CONFIRMATION_INTAKE_MD,
            BREAKING_SIGNAL_CLUSTERS_CSV,
            BREAKING_SIGNAL_CLUSTERS_MD,
            BREAKING_SIGNAL_NEXT_ACTION_CSV,
            BREAKING_SIGNAL_NEXT_ACTION_MD,
            BREAKING_SIGNAL_NEXT_ACTION_JSON,
            BREAKING_SIGNAL_RETURN_SUMMARY_CSV,
            BREAKING_SIGNAL_RETURN_SUMMARY_MD,
            BREAKING_SIGNAL_RETURN_SUMMARY_JSON,
            GAME_SOURCE_CONFIRMATION_BRIDGE_CSV,
            GAME_SOURCE_CONFIRMATION_BRIDGE_MD,
            GAME_SOURCE_CONFIRMATION_BRIDGE_JSON,
            NEWS_SYNC_HUB_MD,
        ],
        "counts": {
            "candidates": len(candidates),
            "source_observations": len(all_observations),
            "fact_packets": len(packets),
            "manual_review": len(manual_packets),
            "manual_review_not_required_packets": len([p for p in packets if p.get("manual_review") != "Yes"]),
            "production_ready": len([p for p in packets if p.get("production_ready") == "Yes"]),
            "packets_with_event_date": len([p for p in packets if clean(p.get("event_date"))]),
            "packets_missing_event_date": len([p for p in packets if not clean(p.get("event_date"))]),
            "breaking_public_signal_rows": len(breaking_signal_rows),
            "breaking_public_signal_review_only": len([row for row in breaking_signal_rows if row.get("review_only") == "true"]),
            "breaking_confirmation_intake_rows": len(confirmation_intake_rows),
            "breaking_signal_cluster_rows": len(cluster_rows),
            "breaking_signal_next_action_rows": len(breaking_next_action_rows),
            "breaking_signal_return_summary_rows": len(breaking_return_summary_rows),
            "breaking_signal_return_summary_missing_operator_checked_url": breaking_return_summary.get("missing_operator_checked_url", 0),
            "breaking_signal_return_summary_missing_operator_confirmation_result": breaking_return_summary.get("missing_operator_confirmation_result", 0),
            "breaking_signal_return_summary_missing_source_confidence_tier": breaking_return_summary.get("missing_source_confidence_tier", 0),
            "breaking_signal_clusters_with_score_stat_proof": len([
                row for row in cluster_rows
                if clean(row.get("score_stat_proof_status")) not in {"", "no_matching_score_stat_proof_operator_confirmation_required"}
            ]),
            "breaking_signal_clusters_with_named_player_stat_proof": len([
                row for row in cluster_rows
                if clean(row.get("named_player_stat_proof_count")) not in {"", "0"}
            ]),
            "breaking_signal_clusters_with_score_stat_confirmation_targets": len([
                row for row in cluster_rows
                if clean(row.get("score_proof_confirmation_target")) or clean(row.get("named_player_stat_proof_confirmation_targets"))
            ]),
            "breaking_signal_clusters_with_score_stat_review_order_targets": len([
                row for row in cluster_rows
                if clean(row.get("first_score_stat_review_order_target"))
            ]),
            "breaking_signal_clusters_with_corroboration_ladder": len([
                row for row in cluster_rows
                if clean(row.get("corroboration_ladder_status"))
            ]),
            "game_source_confirmation_bridge_rows": len(game_source_bridge_rows),
        },
        "settings": {
            "max_must_post": MAX_MUST_POST,
            "max_strong_maybe": MAX_STRONG_MAYBE,
            "max_diversity_promotions": MAX_DIVERSITY_PROMOTIONS,
            "max_soccer_diversity": MAX_SOCCER_DIVERSITY,
            "enable_fetch": ENABLE_FETCH,
        }
    }
    write_run_json(NEWS_MANIFEST_JSON, manifest)

    if not candidates:
        write_run_text(
            NEWS_SETUP_ERROR_MD,
            "# Her Sports Daily News Sync Setup Error\\n\\n"
            "News Sync ran, but found 0 candidates.\\n\\n"
            "Most likely causes:\\n\\n"
            "1. `results_graphics_queue.md` is missing from the repo root.\\n"
            "2. Results Desk has not committed its latest outputs yet.\\n"
            "3. The file exists only in `results_run_history/latest/`, but the workflow did not include it.\\n"
            "4. The Results Desk queue format changed.\\n\\n"
            "Open `news_input_status_report.csv` first.\\n"
        )

    print(f"Created Her Sports Daily News Sync {VERSION} outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
