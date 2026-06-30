from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import requests

from hsd_run_io import input_path, output_path, write_json, write_text

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

VERSION = "v5.0-free-public-source-accuracy"
RESULTS_TIMEZONE = os.environ.get("HSD_TIMEZONE", "America/New_York")
LOOKBACK_DAYS = int(os.environ.get("HSD_LOOKBACK_DAYS", "1"))
LOOKAHEAD_DAYS = int(os.environ.get("HSD_LOOKAHEAD_DAYS", "1"))
REQUEST_SLEEP_SECONDS = 0.15

OBSERVATIONS_FILE = "source_observations.csv"
RECONCILED_FILE = "reconciled_events.csv"
RESULTS_BOARD_FILE = "today_results_board.csv"
WOMENS_RESULTS_FILE = "today_womens_results.csv"
FINAL_RESULTS_FILE = "today_final_results.csv"
TOP_RESULTS_FILE = "top_womens_results.csv"
MANUAL_REVIEW_FILE = "manual_review_queue.csv"
SOURCE_HEALTH_FILE = "source_health_report.csv"
BOX_SCORE_AUDIT_FILE = "wnba_box_score_audit.csv"
BOX_SCORE_SUMMARY_FILE = "wnba_box_score_summary.md"
GAME_INTELLIGENCE_BOARD_FILE = "game_intelligence_board_v1.csv"
GAME_INTELLIGENCE_REPORT_FILE = "game_intelligence_board_v1.md"
GAME_INTELLIGENCE_MANIFEST_FILE = "game_intelligence_board_v1.json"
STATS_EVIDENCE_GAP_BOARD_FILE = "stats_evidence_gap_board_v1.csv"
STATS_EVIDENCE_GAP_REPORT_FILE = "stats_evidence_gap_board_v1.md"
STATS_EVIDENCE_GAP_MANIFEST_FILE = "stats_evidence_gap_board_v1.json"
STATS_CONFIRMATION_INTAKE_FILE = "stats_confirmation_intake_v1.csv"
GAME_FACT_CONFIRMATION_STATUS_FILE = "game_fact_confirmation_status_v1.csv"
GAME_FACT_CONFIRMATION_STATUS_REPORT_FILE = "game_fact_confirmation_status_v1.md"
GAME_FACT_CONFIRMATION_STATUS_MANIFEST_FILE = "game_fact_confirmation_status_v1.json"
GAME_SOURCE_CONFIRMATION_NEXT_ACTION_FILE = "game_source_confirmation_next_action_v1.csv"
GAME_SOURCE_CONFIRMATION_NEXT_ACTION_REPORT_FILE = "game_source_confirmation_next_action_v1.md"
GAME_SOURCE_CONFIRMATION_NEXT_ACTION_MANIFEST_FILE = "game_source_confirmation_next_action_v1.json"
GAME_SOURCE_RESEARCH_WORKSHEET_FILE = "game_source_research_worksheet_v1.csv"
GAME_SOURCE_RESEARCH_WORKSHEET_REPORT_FILE = "game_source_research_worksheet_v1.md"
GAME_SOURCE_RESEARCH_WORKSHEET_MANIFEST_FILE = "game_source_research_worksheet_v1.json"
GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_FILE = "game_source_confirmation_return_summary_v1.csv"
GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_REPORT_FILE = "game_source_confirmation_return_summary_v1.md"
GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_MANIFEST_FILE = "game_source_confirmation_return_summary_v1.json"
FINAL_SCORE_STAT_PROOF_FILE = "final_score_stat_proof_v1.csv"
FINAL_SCORE_STAT_PROOF_REPORT_FILE = "final_score_stat_proof_v1.md"
FINAL_SCORE_STAT_PROOF_MANIFEST_FILE = "final_score_stat_proof_v1.json"
FINAL_SCORE_STAT_PROOF_CONFIRMATION_INTAKE_FILE = "final_score_stat_proof_confirmation_intake_v1.csv"
FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_FILE = "final_score_stat_proof_review_order_v1.csv"
FINAL_SCORE_STAT_PROOF_WALKTHROUGH_FILE = "final_score_stat_proof_review_walkthrough_v1.md"
ATHLETE_RENDER_CANDIDATE_BOARD_FILE = "athlete_render_candidate_board_v1.csv"
ATHLETE_RENDER_CANDIDATE_REPORT_FILE = "athlete_render_candidate_board_v1.md"
ATHLETE_RENDER_CANDIDATE_MANIFEST_FILE = "athlete_render_candidate_board_v1.json"
STORY_PROOF_CARD_FILE = "story_proof_card_v1.csv"
STORY_PROOF_CARD_REPORT_FILE = "story_proof_card_v1.md"
STORY_PROOF_CARD_MANIFEST_FILE = "story_proof_card_v1.json"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
RECOMMENDATIONS_FILE = "daily_results_recommendations.md"
HUB_FILE = "results_system_hub.md"
MANIFEST_FILE = "run_manifest.json"

V5_MANIFEST = output_path("results_desk_v5_manifest.json")
V5_REPORT = output_path("results_desk_v5_report.md")
SOURCE_ACCURACY_JSON = output_path("source_accuracy_v5.json")
SOURCE_ACCURACY_MD = output_path("source_accuracy_v5.md")
DUPLICATE_AUDIT = output_path("duplicate_game_audit_v5.csv")
STALE_AUDIT = output_path("stale_source_audit_v5.csv")
MISSING_ALERT_JSON = output_path("missing_games_alert_v5.json")
MISSING_ALERT_MD = output_path("missing_games_alert_v5.md")
EXPECTED_GAMES = [Path("config/hsd_expected_games_v5.csv"), Path("data/expected_games/wnba_expected_games.csv"), Path("expected_games.csv")]

WNBA_TEAM_ROOTS = {
    "atlanta dream", "chicago sky", "connecticut sun", "dallas wings", "golden state valkyries",
    "indiana fever", "las vegas aces", "los angeles sparks", "minnesota lynx", "new york liberty",
    "phoenix mercury", "portland fire", "seattle storm", "toronto tempo", "washington mystics",
}

OBS_FIELDS = [
    "run_id", "source_name", "source_priority", "source_event_id", "canonical_key",
    "sport_norm", "league_norm", "competition_id", "gender_scope", "scheduled_start_utc",
    "scheduled_date_local", "home_team_raw", "away_team_raw", "home_team_norm",
    "away_team_norm", "status_raw", "status_norm", "home_score", "away_score",
    "score_by_period_json", "team_stats_json", "player_stats_json", "top_performers_json",
    "source_url", "fetched_at_utc", "http_status", "parse_ok", "stale_rejected",
    "women_match_method", "raw_archive_path", "notes",
]

EVENT_FIELDS = [
    "run_id", "event_uid", "canonical_key", "selected_source", "source_count",
    "all_sources_json", "sport_norm", "league_norm", "gender_scope", "scheduled_start_utc",
    "scheduled_date_local", "home_team_norm", "away_team_norm", "home_team_display",
    "away_team_display", "final_score_display", "game_state", "status_norm",
    "home_score", "away_score", "winner", "loser", "outcome_type",
    "editorial_tier", "editorial_bucket", "content_action", "content_family",
    "posting_priority", "caption_seed", "score_by_period_json",
    "team_stats_json", "player_stats_json", "top_performers_json", "confidence",
    "confidence_reason_json", "score_conflict", "manual_review", "include_in_dashboard",
    "include_in_graphics", "editorial_rank", "graphics_headline", "graphics_subhead",
    "source_url", "source_priority",
]

DUP_FIELDS = ["canonical_key", "source_count", "source_names", "score_variants", "date", "teams", "decision"]
STALE_FIELDS = ["source_name", "source_event_id", "canonical_key", "scheduled_date_local", "status_norm", "source_url", "reason"]
EXPECTED_FIELDS = ["date", "league", "sport", "home_team", "away_team", "expected_key", "source_name", "source_url", "matched", "matched_event_uid", "reason"]
GAME_INTELLIGENCE_FIELDS = [
    "row_id",
    "row_type",
    "attention_bucket",
    "game_date",
    "league",
    "sport",
    "home_team",
    "away_team",
    "status",
    "final_score",
    "recap_candidate",
    "stats_context_status",
    "stats_context",
    "missing_evidence",
    "selected_source",
    "source_count",
    "source_confidence",
    "source_confidence_reason",
    "source_confirmation_tier",
    "source_confirmation_limitations",
    "source_url",
    "source_domain",
    "retrieved_at_utc",
    "source_freshness_status",
    "source_freshness_age_minutes",
    "source_freshness_note",
    "manual_review_status",
    "game_fact_status_row_to_open",
    "story_proof_card_row_to_open",
    "proof_review_order_row_to_open",
    "proof_manual_intake_path",
    "source_confirmation_cue",
    "recap_render_readiness",
    "operator_next_review_step",
    "review_only",
    "approval_state_change",
    "publish_action",
]
STATS_EVIDENCE_FIELDS = [
    "event_uid",
    "game_date",
    "league",
    "sport",
    "matchup",
    "status",
    "recap_candidate",
    "final_score",
    "stats_evidence_status",
    "box_score_audit_status",
    "top_performers",
    "missing_stat_evidence",
    "manual_confirmation_needed",
    "operator_next_step",
    "confirmation_source_url",
    "confirmation_source_domain",
    "selected_score_source",
    "score_source_url",
    "source_confidence",
    "retrieved_at_utc",
    "review_only",
    "approval_state_change",
    "publish_action",
]
STATS_CONFIRMATION_FIELDS = [
    "event_uid",
    "game_date",
    "league",
    "matchup",
    "status",
    "final_score",
    "manual_confirmation_needed",
    "operator_next_step",
    "confirmation_source_url",
    "operator_checked_url",
    "operator_confirmation_status",
    "operator_confirmed_stats",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "publish_action",
]
GAME_FACT_CONFIRMATION_STATUS_FIELDS = [
    "event_uid",
    "game_date",
    "league",
    "sport",
    "matchup",
    "game_status",
    "attention_bucket",
    "recap_candidate",
    "schedule_fact_status",
    "result_fact_status",
    "stats_fact_status",
    "overall_confirmation_status",
    "source_confidence",
    "source_confirmation_tier",
    "source_confirmation_limitations",
    "source_url",
    "source_domain",
    "stats_source_url",
    "missing_confirmation",
    "exact_next_file_or_intake",
    "story_proof_card_row_to_open",
    "final_score_review_order_row",
    "named_stat_review_order_row",
    "proof_manual_intake_path",
    "source_confirmation_cue",
    "recap_render_readiness",
    "manual_review_required",
    "retrieved_at_utc",
    "source_freshness_status",
    "source_freshness_age_minutes",
    "source_freshness_note",
    "review_only",
    "approval_state_change",
    "publish_action",
]
GAME_SOURCE_CONFIRMATION_NEXT_ACTION_FIELDS = [
    "action_rank",
    "operator_review_order_cue",
    "event_uid",
    "game_date",
    "league",
    "matchup",
    "game_status",
    "recap_candidate",
    "review_priority",
    "confirmation_state",
    "source_confidence",
    "schedule_fact_status",
    "result_fact_status",
    "stats_fact_status",
    "source_confirmation_tier",
    "source_freshness_status",
    "source_freshness_age_minutes",
    "missing_confirmation",
    "missing_expected_game_flag",
    "conflict_or_lag_note",
    "official_or_public_source_cue",
    "second_source_check_cue",
    "recap_render_readiness",
    "recap_render_human_review_gate",
    "source_url",
    "source_domain",
    "source_row_to_open",
    "proof_row_to_open",
    "manual_intake_path",
    "source_confirmation_next_action",
    "manual_confirmation_return_fields",
    "operator_checked_source_url",
    "operator_source_confirmation_status",
    "operator_source_confirmation_notes",
    "review_only",
    "approval_state_change",
    "source_enablement",
    "publish_action",
]
GAME_SOURCE_RESEARCH_WORKSHEET_FIELDS = [
    "worksheet_rank",
    "worksheet_import_cue",
    "event_uid",
    "game_date",
    "league",
    "matchup",
    "game_status",
    "recap_candidate",
    "research_need",
    "current_source_tier",
    "official_or_public_source_cue",
    "second_source_check_cue",
    "source_confidence",
    "source_freshness_status",
    "schedule_fact_status",
    "result_fact_status",
    "stats_fact_status",
    "missing_confirmation",
    "scoreboard_source_url",
    "scoreboard_source_domain",
    "box_score_or_stat_source_url",
    "operator_official_box_score_url",
    "source_type_to_verify",
    "operator_stat_line_confirmation",
    "operator_manual_verification_status",
    "operator_evidence_note",
    "source_proof_next_action",
    "proof_row_to_open",
    "source_row_to_open",
    "manual_intake_path",
    "operator_research_prompt",
    "operator_found_official_url",
    "operator_found_public_scoreboard_url",
    "operator_found_box_score_url",
    "operator_source_tier_decision",
    "operator_confirmation_status",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "source_enablement",
    "publish_action",
]
GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_FIELDS = [
    "summary_rank",
    "event_uid",
    "game_date",
    "league",
    "matchup",
    "research_need",
    "current_source_tier",
    "scoreboard_source_url",
    "operator_found_official_url_present",
    "operator_found_public_scoreboard_url_present",
    "operator_found_box_score_url_present",
    "operator_confirmation_status_present",
    "operator_notes_present",
    "manual_return_status",
    "missing_return_fields",
    "manual_next_step",
    "source_row_to_open",
    "proof_row_to_open",
    "manual_intake_path",
    "review_only",
    "approval_state_change",
    "source_enablement",
    "publish_action",
]
FINAL_SCORE_STAT_PROOF_FIELDS = [
    "proof_id",
    "event_uid",
    "game_date",
    "league",
    "matchup",
    "recap_candidate",
    "fact_type",
    "fact_label",
    "fact_value",
    "named_player",
    "player_team",
    "stat_line",
    "proof_status",
    "manual_box_score_confirmation_needed",
    "source_confidence",
    "source_url",
    "source_domain",
    "evidence_artifact_row",
    "exact_next_file_or_intake",
    "operator_note_path",
    "limitations",
    "review_only",
    "approval_state_change",
    "publish_action",
]
FINAL_SCORE_STAT_PROOF_CONFIRMATION_FIELDS = [
    "proof_id",
    "event_uid",
    "game_date",
    "matchup",
    "fact_type",
    "fact_value",
    "proof_status",
    "source_url",
    "evidence_artifact_row",
    "operator_review_task",
    "operator_checked_source_url",
    "operator_confirmation_status",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "publish_action",
]
FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_FIELDS = [
    "review_order",
    "review_phase",
    "score_stat_review_sequence_cue",
    "event_uid",
    "game_date",
    "matchup",
    "fact_type",
    "fact_label",
    "fact_value",
    "named_player",
    "player_team",
    "stat_line",
    "proof_status",
    "source_check_status",
    "source_confirmation_cue",
    "manual_box_score_confirmation_needed",
    "source_url",
    "source_domain",
    "proof_row_to_open",
    "evidence_artifact_row",
    "intake_row_to_record",
    "story_proof_card_row_to_open",
    "operator_next_step",
    "operator_decision_fields",
    "render_review_cue",
    "review_only",
    "approval_state_change",
    "publish_action",
]
ATHLETE_RENDER_CANDIDATE_FIELDS = [
    "candidate_id",
    "candidate_rank",
    "candidate_status",
    "rank_score",
    "event_uid",
    "game_date",
    "matchup",
    "athlete_name",
    "player_team",
    "stat_line",
    "fact_value",
    "proof_status",
    "source_url",
    "source_domain",
    "proof_row_to_open",
    "review_order_row_to_open",
    "intake_row_to_record",
    "asset_status",
    "athlete_id",
    "asset_kind",
    "local_athlete_image_path",
    "approved_marker_path",
    "image_file_exists",
    "approved_marker_exists",
    "asset_source_url",
    "asset_catalog_row",
    "render_candidate_title",
    "render_candidate_dek",
    "exact_renderer_handoff_fields",
    "story_proof_card_row_to_open",
    "handoff_action",
    "missing_blockers",
    "operator_next_step",
    "operator_checked_source_url",
    "operator_asset_review_notes",
    "review_only",
    "approval_state_change",
    "publish_action",
    "auto_approval",
    "auto_publish",
    "asset_downloads",
    "move_files",
    "publish_ready",
]
STORY_PROOF_CARD_FIELDS = [
    "candidate_id",
    "candidate_rank",
    "claim",
    "event_id",
    "game_date",
    "matchup",
    "official_source_url",
    "cross_check_source_url",
    "wire_source_url_if_present",
    "source_domain",
    "proof_status",
    "schedule_result_status",
    "named_stat_proof_status",
    "named_stat_proof",
    "named_stat_proof_row",
    "athlete_name",
    "athlete_team",
    "athlete_photo_path",
    "athlete_photo_marker_path",
    "copy_unlock_level",
    "asset_unlock_state",
    "renderability_state",
    "athlete_render_candidate_id",
    "athlete_render_handoff_fields",
    "game_fact_row",
    "final_score_proof_row",
    "final_score_review_order_row",
    "proof_review_order_row",
    "named_stat_review_order_row",
    "manual_intake_path",
    "source_confirmation_cue",
    "smallest_next_action",
    "human_confirmation_needed",
    "missing_blockers",
    "operator_checked_source_url",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "auto_approval",
    "publish_action",
    "publish_ready",
    "asset_downloads",
    "asset_download_policy",
    "asset_approval_state_change",
    "source_enablement",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def source_domain(url: Any) -> str:
    raw = clean(url)
    if not raw:
        return ""
    try:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        return parsed.netloc.lower()
    except Exception:
        return ""


def low(value: Any) -> str:
    return clean(value).lower()


def slug(value: Any) -> str:
    s = low(value).replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def date_window() -> Tuple[List[str], List[str]]:
    if ZoneInfo is not None:
        today = datetime.now(ZoneInfo(RESULTS_TIMEZONE)).date()
    else:
        today = datetime.now(timezone.utc).date()
    iso_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    compact_dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    return iso_dates, compact_dates


def local_date_from_iso(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if ZoneInfo is not None:
            dt = dt.astimezone(ZoneInfo(RESULTS_TIMEZONE))
        return dt.date().isoformat()
    except Exception:
        return value[:10]


def normalize_status(value: Any) -> str:
    s = low(value)
    if any(x in s for x in ["finished", "match finished", "after fulltime", "after overtime", "final", "ft", "ended"]):
        return "final"
    if any(x in s for x in ["live", "in progress", "quarter", "half", "period"]):
        return "live"
    if any(x in s for x in ["not started", "scheduled", "pre match", "pre-match", "time to be defined"]):
        return "scheduled"
    if any(x in s for x in ["postponed", "cancelled", "canceled", "suspended", "abandoned"]):
        return "not_played"
    if re.search(r"\b(mon|tue|wed|thu|fri|sat|sun)(day)?\b.*\b\d{1,2}:\d{2}\s*[ap]\.?m", s):
        return "scheduled"
    if re.search(r"\b\d{1,2}:\d{2}\s*[ap]\.?m\b", s) and any(tz in s for tz in [" et", " edt", " est", " ct", " cdt", " cst", " mt", " mdt", " mst", " pt", " pdt", " pst"]):
        return "scheduled"
    return s or "unknown"


def normalize_team(value: Any) -> str:
    s = slug(value)
    replacements = {"united states": "usa", "u s a": "usa", "women": "w", "womens": "w", "women s": "w"}
    for src, dst in replacements.items():
        s = re.sub(rf"\b{re.escape(src)}\b", dst, s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_team_for_context(team: Any, league: Any = "", sport: Any = "") -> str:
    s = normalize_team(team)
    if clean(league).upper() == "WNBA" or s in WNBA_TEAM_ROOTS:
        s = re.sub(r"\bw$", "", s).strip()
    return s


def canonical_key(sport: str, date_local: str, home: str, away: str, league: str = "") -> str:
    pair = sorted([normalize_team_for_context(home, league, sport), normalize_team_for_context(away, league, sport)])
    return "|".join([clean(sport), clean(date_local), pair[0], pair[1]])


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if clean(value) == "":
            return default
        return int(float(str(value)))
    except Exception:
        return default


def score_present(home_score: Any, away_score: Any) -> bool:
    return clean(home_score) != "" and clean(away_score) != ""


def score_values_valid(home_score: Any, away_score: Any) -> bool:
    return safe_int(home_score) is not None and safe_int(away_score) is not None


def score_winner(home: str, away: str, home_score: Any, away_score: Any) -> Tuple[str, str]:
    h = safe_int(home_score)
    a = safe_int(away_score)
    if h is None or a is None:
        return "", ""
    if h > a:
        return clean(home), clean(away)
    if a > h:
        return clean(away), clean(home)
    return "", ""


def score_signature(obs: Dict[str, str]) -> str:
    if not score_present(obs.get("home_score"), obs.get("away_score")):
        return "no_score"
    pairs = sorted([(clean(obs.get("home_team_norm")), clean(obs.get("home_score"))), (clean(obs.get("away_team_norm")), clean(obs.get("away_score")))])
    return json.dumps(pairs, sort_keys=True)


def allowed_sources() -> List[str]:
    raw = os.environ.get("HSD_RESULTS_V5_SOURCES", "espn_wnba_public,manual_seed")
    allowed = {"espn_wnba_public", "manual_seed"}
    return [s for s in [x.strip().lower() for x in raw.split(",") if x.strip()] if s in allowed]


def fetch_espn_wnba(run_id: str, compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    for date_compact in compact_dates:
        try:
            r = requests.get(endpoint, params={"dates": date_compact}, headers={"User-Agent": "HerSportsDailyResultsDesk/5.0"}, timeout=30)
            status = r.status_code
            r.raise_for_status()
            data = r.json()
            error = ""
        except Exception as exc:
            data = {}
            try:
                status = r.status_code
            except Exception:
                status = 0
            error = str(exc)
        events = data.get("events") if isinstance(data, dict) else []
        events = events or []
        emitted = 0
        for event in events:
            try:
                event_id = clean(event.get("id"))
                status_raw = clean((((event.get("status") or {}).get("type") or {}).get("detail")))
                start_utc = clean(event.get("date"))
                date_local = local_date_from_iso(start_utc)
                home = away = home_score = away_score = ""
                score_periods: Dict[str, Any] = {}
                comps = event.get("competitions") or []
                if comps:
                    for comp in comps[0].get("competitors") or []:
                        team = clean(((comp.get("team") or {}).get("displayName")))
                        score = clean(comp.get("score"))
                        if clean(comp.get("homeAway")).lower() == "home":
                            home, home_score = team, score
                        elif clean(comp.get("homeAway")).lower() == "away":
                            away, away_score = team, score
                        score_periods[team] = comp.get("linescores") or []
                observations.append({
                    "run_id": run_id,
                    "source_name": "espn_wnba_public",
                    "source_priority": "95",
                    "source_event_id": event_id,
                    "canonical_key": canonical_key("basketball", date_local, home, away, "WNBA"),
                    "sport_norm": "basketball",
                    "league_norm": "WNBA",
                    "competition_id": "USA",
                    "gender_scope": "women",
                    "scheduled_start_utc": start_utc,
                    "scheduled_date_local": date_local,
                    "home_team_raw": home,
                    "away_team_raw": away,
                    "home_team_norm": normalize_team_for_context(home, "WNBA", "basketball"),
                    "away_team_norm": normalize_team_for_context(away, "WNBA", "basketball"),
                    "status_raw": status_raw,
                    "status_norm": normalize_status(status_raw),
                    "home_score": home_score,
                    "away_score": away_score,
                    "score_by_period_json": json.dumps(score_periods, ensure_ascii=False),
                    "team_stats_json": "",
                    "player_stats_json": "",
                    "top_performers_json": "",
                    "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}",
                    "fetched_at_utc": now_iso(),
                    "http_status": str(status),
                    "parse_ok": "Yes",
                    "stale_rejected": "No",
                    "women_match_method": "explicit_league",
                    "raw_archive_path": "",
                    "notes": f"requested_date={date_compact}; free public ESPN scoreboard endpoint",
                })
                emitted += 1
            except Exception:
                pass
        health.append({"source_name": "espn_wnba_public", "sport_or_league": "WNBA", "date": date_compact, "http_status": status, "ok": "Yes" if status == 200 and not error else "No", "events_found": len(events), "observations_emitted": emitted, "stale_rejected": 0, "notes": error or "free public ESPN scoreboard endpoint ok"})
        time.sleep(REQUEST_SLEEP_SECONDS)
    return observations, health


def read_csv(path: Path) -> List[Dict[str, str]]:
    path = input_path(path)
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def normalize_manual_seed_row(run_id: str, row: Dict[str, str], source_file: str) -> Dict[str, str] | None:
    league = clean(row.get("league") or "WNBA")
    sport = clean(row.get("sport") or "basketball")
    date = clean(row.get("scheduled_date_local") or row.get("event_date_local") or row.get("date"))
    home = clean(row.get("home_team") or row.get("home_team_name"))
    away = clean(row.get("away_team") or row.get("away_team_name"))
    if not date or not home or not away:
        return None
    status = normalize_status(row.get("status") or row.get("status_norm") or "scheduled")
    return {
        "run_id": run_id, "source_name": "manual_seed", "source_priority": "100", "source_event_id": clean(row.get("source_event_id") or row.get("event_id")),
        "canonical_key": canonical_key(sport, date, home, away, league), "sport_norm": sport, "league_norm": league, "competition_id": clean(row.get("competition_id") or "manual"),
        "gender_scope": clean(row.get("gender_scope") or "women"), "scheduled_start_utc": clean(row.get("scheduled_start_utc")), "scheduled_date_local": date,
        "home_team_raw": home, "away_team_raw": away, "home_team_norm": normalize_team_for_context(home, league, sport), "away_team_norm": normalize_team_for_context(away, league, sport),
        "status_raw": status, "status_norm": status, "home_score": clean(row.get("home_score") or row.get("score_home")), "away_score": clean(row.get("away_score") or row.get("score_away")),
        "score_by_period_json": clean(row.get("score_by_period_json")), "team_stats_json": clean(row.get("team_stats_json")), "player_stats_json": clean(row.get("player_stats_json")), "top_performers_json": clean(row.get("top_performers_json")),
        "source_url": clean(row.get("source_url") or source_file), "fetched_at_utc": now_iso(), "http_status": "0", "parse_ok": "Yes", "stale_rejected": "No", "women_match_method": "manual_seed", "raw_archive_path": source_file, "notes": "manual seed fallback; user/source reviewed",
    }


def load_manual_seed_observations(run_id: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in [Path("manual_results_seed.csv"), Path("data/manual_results_seed.csv"), Path("config/manual_results_seed.csv")]:
        for row in read_csv(path):
            obs = normalize_manual_seed_row(run_id, row, path.as_posix())
            if obs:
                rows.append(obs)
    return rows


def free_source_observations(run_id: str, compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    sources = allowed_sources()
    if "espn_wnba_public" in sources:
        obs, h = fetch_espn_wnba(run_id, compact_dates)
        observations.extend(obs)
        health.extend(h)
    manual_rows = load_manual_seed_observations(run_id)
    if manual_rows:
        observations.extend(manual_rows)
        health.append({"source_name": "manual_seed", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "Yes", "events_found": len(manual_rows), "observations_emitted": len(manual_rows), "stale_rejected": 0, "notes": "manual seed rows loaded from free local files"})
    elif "manual_seed" in sources:
        health.append({"source_name": "manual_seed", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "Yes", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": "optional fallback; no manual seed file found"})
    return observations, health


def score_display(obs: Dict[str, str]) -> str:
    away, home, a, h = clean(obs.get("away_team_raw")), clean(obs.get("home_team_raw")), clean(obs.get("away_score")), clean(obs.get("home_score"))
    if away and home and a != "" and h != "":
        return f"{away} {a} · {home} {h}"
    return f"{away} at {home}".strip()


def headline_for(obs: Dict[str, str], winner: str, loser: str) -> str:
    if winner and loser:
        return f"{winner} beat {loser}"
    away, home = clean(obs.get("away_team_raw")), clean(obs.get("home_team_raw"))
    return f"{away} at {home}" if away and home else "WNBA result"


def confidence_for(chosen: Dict[str, str], group: List[Dict[str, str]], conflict: bool) -> Tuple[float, Dict[str, Any]]:
    score = 0.78 if chosen.get("source_name") == "espn_wnba_public" else 0.86 if chosen.get("source_name") == "manual_seed" else 0.50
    reasons: Dict[str, Any] = {"base_source": chosen.get("source_name"), "base": score, "adjustments": []}
    if chosen.get("status_norm") == "final":
        score += 0.08; reasons["adjustments"].append(["final_state", 0.08])
    if score_present(chosen.get("home_score"), chosen.get("away_score")):
        score += 0.06; reasons["adjustments"].append(["score_complete", 0.06])
    if len(group) >= 2 and not conflict:
        score += 0.08; reasons["adjustments"].append(["multi_source_same_key", 0.08])
    if conflict:
        score -= 0.30; reasons["adjustments"].append(["score_conflict", -0.30])
    score = max(0.0, min(1.0, score)); reasons["final_confidence"] = round(score, 3)
    return score, reasons


def apply_event_gates(event: Dict[str, Any]) -> None:
    rank = float(event.get("confidence") or 0) * 100
    if event.get("league_norm") == "WNBA":
        rank += 70
    if event.get("status_norm") == "final":
        rank += 15
    event["editorial_rank"] = round(rank, 1)
    if event.get("gender_scope") == "women" and event.get("status_norm") == "final" and not event.get("manual_review") and float(event.get("confidence") or 0) >= 0.82:
        event["include_in_graphics"] = True
        event["editorial_bucket"] = "Must Post" if event["editorial_rank"] >= 145 else "Strong Maybe" if event["editorial_rank"] >= 120 else "Watchlist"
        event["content_action"] = "Make First" if event["editorial_bucket"] == "Must Post" else event["editorial_bucket"]
        event["posting_priority"] = "P1" if event["editorial_bucket"] == "Must Post" else "P2" if event["editorial_bucket"] == "Strong Maybe" else "P3"
    elif event.get("gender_scope") == "women":
        event["editorial_bucket"] = "Watchlist"; event["content_action"] = "Watch"; event["posting_priority"] = "Review"


def reconcile(run_id: str, observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for obs in observations:
        if clean(obs.get("canonical_key")):
            grouped[obs["canonical_key"]].append(obs)
    events: List[Dict[str, Any]] = []
    for key, group in grouped.items():
        group.sort(key=lambda r: int(r.get("source_priority") or 0), reverse=True)
        chosen = group[0]
        sigs = {score_signature(obs) for obs in group if score_signature(obs) != "no_score"}
        conflict = len(sigs) > 1
        winner, loser = score_winner(chosen.get("home_team_raw", ""), chosen.get("away_team_raw", ""), chosen.get("home_score"), chosen.get("away_score"))
        status = chosen.get("status_norm", "unknown")
        final_score_display = score_display(chosen)
        confidence, reasons = confidence_for(chosen, group, conflict)
        manual_review = conflict or chosen.get("gender_scope") != "women" or (status == "final" and not score_present(chosen.get("home_score"), chosen.get("away_score")))
        event = {"run_id": run_id, "event_uid": "event_" + stable_id(key), "canonical_key": key, "selected_source": chosen.get("source_name", ""), "source_count": len(group), "all_sources_json": json.dumps(sorted({obs.get("source_name", "") for obs in group}), ensure_ascii=False), "sport_norm": chosen.get("sport_norm", ""), "league_norm": chosen.get("league_norm", ""), "gender_scope": chosen.get("gender_scope", ""), "scheduled_start_utc": chosen.get("scheduled_start_utc", ""), "scheduled_date_local": chosen.get("scheduled_date_local", ""), "home_team_norm": chosen.get("home_team_norm", ""), "away_team_norm": chosen.get("away_team_norm", ""), "home_team_display": chosen.get("home_team_raw", ""), "away_team_display": chosen.get("away_team_raw", ""), "final_score_display": final_score_display, "game_state": status, "status_norm": status, "home_score": chosen.get("home_score", ""), "away_score": chosen.get("away_score", ""), "winner": winner, "loser": loser, "outcome_type": "win" if status == "final" and winner and loser else status, "editorial_tier": "Tier 1" if chosen.get("league_norm") == "WNBA" else "Tier 3", "editorial_bucket": "Archive Only", "content_action": "Archive", "content_family": "Tonight in the W" if chosen.get("league_norm") == "WNBA" else "Results Desk", "posting_priority": "Archive Only", "caption_seed": f"{winner} defeated {loser}, {final_score_display}." if winner and loser else final_score_display, "score_by_period_json": chosen.get("score_by_period_json", ""), "team_stats_json": chosen.get("team_stats_json", ""), "player_stats_json": chosen.get("player_stats_json", ""), "top_performers_json": chosen.get("top_performers_json", ""), "confidence": confidence, "confidence_reason_json": json.dumps(reasons, ensure_ascii=False), "score_conflict": conflict, "manual_review": manual_review, "include_in_dashboard": chosen.get("gender_scope") == "women", "include_in_graphics": False, "editorial_rank": 0.0, "graphics_headline": headline_for(chosen, winner, loser), "graphics_subhead": final_score_display, "source_url": chosen.get("source_url", ""), "source_priority": int(chosen.get("source_priority") or 0), "espn_event_id": chosen.get("source_event_id", "") if chosen.get("source_name") == "espn_wnba_public" else "", "slide_3_context": "This result is sourced from free public scoreboard data and remains human-review first."}
        apply_event_gates(event); events.append(event)
    events.sort(key=lambda e: (e.get("gender_scope") != "women", e.get("status_norm") != "final", -float(e.get("editorial_rank", 0)), e.get("scheduled_date_local", "")))
    return events


def apply_strict_date_window_gate(events: List[Dict[str, Any]], iso_dates: List[str]) -> List[Dict[str, Any]]:
    dates = set(iso_dates)
    for event in events:
        date = clean(event.get("scheduled_date_local"))
        status = "in_window" if date in dates else "missing_date" if not date else "outside_window"
        event["date_window_status"] = status; event["is_carryover"] = "No" if status == "in_window" else "Yes"
        if status != "in_window":
            event["include_in_graphics"] = False; event["content_action"] = "Archive"; event["editorial_bucket"] = "Archive Only"; event["posting_priority"] = "Archive Only"
    return events


def duplicate_audit(observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for obs in observations:
        grouped[clean(obs.get("canonical_key")) or f"missing|{len(grouped)}"].append(obs)
    rows: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        scores = sorted(set(score_signature(obs) for obs in group)); sources = sorted(set(clean(obs.get("source_name")) for obs in group if clean(obs.get("source_name")))); first = group[0]
        rows.append({"canonical_key": key, "source_count": len(group), "source_names": ";".join(sources), "score_variants": " || ".join(scores), "date": first.get("scheduled_date_local", ""), "teams": f"{first.get('away_team_raw')} at {first.get('home_team_raw')}", "decision": "merge_same_score" if len(scores) == 1 else "manual_review_score_conflict"})
    return rows


def stale_audit(observations: List[Dict[str, str]], iso_dates: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []; dates = set(iso_dates)
    for obs in observations:
        date = clean(obs.get("scheduled_date_local"))
        if not date or date not in dates:
            obs["stale_rejected"] = "Yes"
            rows.append({"source_name": obs.get("source_name"), "source_event_id": obs.get("source_event_id"), "canonical_key": obs.get("canonical_key"), "scheduled_date_local": date, "status_norm": obs.get("status_norm"), "source_url": obs.get("source_url"), "reason": "missing_scheduled_date" if not date else f"outside_window:{date}"})
    return rows


def write_csv(path: str | Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore"); writer.writeheader()
        for row in rows:
            out: Dict[str, Any] = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, bool): value = "Yes" if value else "No"
                elif isinstance(value, float) and field in {"confidence", "editorial_rank"}: value = f"{value:.2f}" if field == "confidence" else f"{value:.1f}"
                out[field] = value
            writer.writerow(out)


def expected_game_rows() -> List[Dict[str, str]]:
    for path in EXPECTED_GAMES:
        rows = read_csv(path)
        if rows: return rows
    return []


def expected_key(row: Dict[str, str]) -> str:
    date = clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local")); league = clean(row.get("league") or "WNBA"); sport = clean(row.get("sport") or "basketball"); home = clean(row.get("home_team") or row.get("home_team_name")); away = clean(row.get("away_team") or row.get("away_team_name"))
    return canonical_key(sport, date, home, away, league) if date and home and away else ""


def missing_games_alert(expected_rows: List[Dict[str, str]], events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    event_by_key = {clean(e.get("canonical_key")): e for e in events if clean(e.get("canonical_key"))}; rows: List[Dict[str, str]] = []
    for row in expected_rows:
        key = expected_key(row); matched = key in event_by_key; event = event_by_key.get(key, {})
        rows.append({"date": clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local")), "league": clean(row.get("league") or "WNBA"), "sport": clean(row.get("sport") or "basketball"), "home_team": clean(row.get("home_team") or row.get("home_team_name")), "away_team": clean(row.get("away_team") or row.get("away_team_name")), "expected_key": key, "source_name": clean(row.get("source_name")), "source_url": clean(row.get("source_url")), "matched": "Yes" if matched else "No", "matched_event_uid": clean(event.get("event_uid")), "reason": "matched" if matched else "missing_from_free_sources_or_outside_window"})
    summary = {"expected_fixture_file_present": bool(expected_rows), "expected_games": len(expected_rows), "matched": sum(1 for row in rows if row.get("matched") == "Yes"), "missing": sum(1 for row in rows if row.get("matched") == "No")}
    return rows, summary


def extract_espn_top_performers(summary: Dict[str, Any]) -> List[str]:
    candidates: List[Tuple[int, str]] = []
    for team_block in ((summary.get("boxscore") or {}).get("players") or []):
        team = clean(((team_block.get("team") or {}).get("displayName")))
        for stat_group in team_block.get("statistics") or []:
            labels = [clean(x) for x in (stat_group.get("labels") or [])]
            for athlete in stat_group.get("athletes") or []:
                name = clean(((athlete.get("athlete") or {}).get("displayName"))); values = athlete.get("stats") or []
                if not name: continue
                stat_map = {labels[i]: clean(values[i]) for i in range(min(len(labels), len(values)))}; score = 0; parts = []
                for key, mult in {"PTS": 1, "REB": 1, "AST": 1, "STL": 2, "BLK": 2}.items():
                    value = stat_map.get(key)
                    if value and value not in {"0", "0.0"}:
                        parts.append(f"{key} {value}")
                        try: score += int(float(value.split("-")[0])) * mult
                        except Exception: pass
                if parts: candidates.append((score, f"{name} ({team}): {', '.join(parts[:4])}"))
    candidates.sort(reverse=True, key=lambda x: x[0]); out: List[str] = []; seen: set[str] = set()
    for _, line in candidates:
        name = line.split(" (")[0]
        if name not in seen: seen.add(name); out.append(line)
        if len(out) >= 3: break
    return out


def audit_wnba_box_scores(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    eligible = [e for e in events if e.get("league_norm") == "WNBA" and e.get("espn_event_id")]
    for event in eligible:
        event["box_score_audit_status"] = "not_audited_sample_cap"
    if low(os.environ.get("HSD_WNBA_BOX_AUDIT", "true")) in {"0", "false", "no"}:
        for event in eligible:
            event["box_score_audit_status"] = "disabled"
        return []
    rows: List[Dict[str, Any]] = []
    for event in eligible[:10]:
        event_id = event.get("espn_event_id"); url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary"
        try:
            r = requests.get(url, params={"event": event_id}, headers={"User-Agent": "HerSportsDailyResultsDesk/5.0"}, timeout=30); status = r.status_code; r.raise_for_status(); performers = extract_espn_top_performers(r.json()); audit_status = "found" if performers else "summary_found_no_performers"
            event["box_score_audit_status"] = audit_status
            if performers: event["box_score_top_performers"] = " | ".join(performers); event["slide_3_context"] = f"Box-score context available: {event['box_score_top_performers']}"
            rows.append({"event_uid": event.get("event_uid"), "espn_event_id": event_id, "graphics_headline": event.get("graphics_headline"), "league_norm": event.get("league_norm"), "http_status": status, "audit_status": audit_status, "top_performers": event.get("box_score_top_performers", ""), "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}", "notes": ""})
        except Exception as exc:
            event["box_score_audit_status"] = "error"
            rows.append({"event_uid": event.get("event_uid"), "espn_event_id": event_id, "graphics_headline": event.get("graphics_headline"), "league_norm": event.get("league_norm"), "http_status": 0, "audit_status": "error", "top_performers": "", "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}", "notes": str(exc)})
        time.sleep(REQUEST_SLEEP_SECONDS)
    return rows


def box_score_summary_md(rows: List[Dict[str, Any]]) -> str:
    lines = ["# WNBA Box-Score Enrichment Audit v5", "", f"Generated: {now_iso()}", ""]
    if not rows: lines.append("No WNBA box-score audit rows were produced."); return "\n".join(lines) + "\n"
    for idx, row in enumerate(rows, 1):
        lines.append(f"{idx}. **{row.get('graphics_headline')}**"); lines.append(f"   - ESPN event: {row.get('espn_event_id')}"); lines.append(f"   - Status: {row.get('audit_status')}")
        if row.get("top_performers"): lines.append(f"   - Top performers: {row.get('top_performers')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def graphics_queue(events: List[Dict[str, Any]]) -> str:
    ready = [e for e in events if e.get("include_in_graphics")]; ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("scheduled_date_local", "")))
    lines = ["# Her Sports Daily Results Graphics Queue v5", "", f"Generated: {now_iso()}", "", "## Queue rules", "", "- Free/public sources only.", "- Do not invent player stats.", "- Auto-rendered graphics remain human-review only.", ""]
    if not ready: lines.append("No high-confidence final women's result graphics are ready right now."); return "\n".join(lines) + "\n"
    for idx, e in enumerate(ready[:20], 1):
        lines.extend([f"## RESULT GRAPHIC {idx}: {e.get('graphics_headline')}", "", f"**League:** {e.get('league_norm')}", f"**Selected source:** {e.get('selected_source')}", f"**Confidence:** {float(e.get('confidence') or 0):.2f}", f"**Final score:** {e.get('final_score_display')}", f"**Source:** {e.get('source_url')}", "", "### Accuracy rules", "- Do not change the final score.", "- Do not invent top performer stats.", "- Use official/approved assets only.", "", "---", ""])
    return "\n".join(lines) + "\n"


def recommendations_md(events: List[Dict[str, Any]]) -> str:
    ready = [e for e in events if e.get("include_in_dashboard")]; ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("scheduled_date_local", "")))
    lines = ["# Her Sports Daily Daily Results Recommendations v5", "", "Free/public source accuracy layer. Human review before posting.", "", "## Top rows", ""]
    if not ready: lines.append("No women's result rows surfaced.")
    for idx, e in enumerate(ready[:30], 1):
        lines.append(f"{idx}. **{e.get('graphics_headline')}**"); lines.append(f"   - {e.get('league_norm')} | {e.get('status_norm')} | confidence {float(e.get('confidence') or 0):.2f} | {e.get('editorial_bucket')}"); lines.append(f"   - {e.get('graphics_subhead')}"); lines.append(f"   - Source: {e.get('source_url')}"); lines.append("")
    return "\n".join(lines) + "\n"


def source_accuracy(events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], duplicates: List[Dict[str, Any]], stale: List[Dict[str, Any]], expected_summary: Dict[str, Any]) -> Dict[str, Any]:
    women = [e for e in events if e.get("gender_scope") == "women"]; finals = [e for e in women if e.get("status_norm") == "final"]
    return {"version": VERSION, "generated_at_utc": now_iso(), "free_only": True, "paid_sources_required": False, "source_policy": "free public ESPN WNBA scoreboard plus optional local manual seed; no paid APIs required", "counts": {"observations": len(observations), "reconciled_events": len(events), "women_events": len(women), "women_finals": len(finals), "duplicate_groups": len(duplicates), "stale_observations": len(stale), "source_health_rows": len(health), **{f"expected_{k}": v for k, v in expected_summary.items()}}, "health": health, "risk_flags": {"stale_observations_present": bool(stale), "missing_expected_games_present": expected_summary.get("missing", 0) > 0, "expected_games_fixture_missing": not expected_summary.get("expected_fixture_file_present")}}


def write_source_accuracy_md(data: Dict[str, Any]) -> str:
    lines = ["# HSD Source Accuracy v5", "", f"Generated: `{data.get('generated_at_utc')}`", f"Version: `{VERSION}`", "", "## Source policy", "", "- Free/public sources only.", "- No paid sports data, paid search, paid scraping proxy, or LLM dependency is required.", "- Current source: public ESPN WNBA scoreboard endpoint plus optional local manual seed fallback.", "", "## Counts", ""]
    for key, value in data.get("counts", {}).items(): lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Risk flags", ""])
    for key, value in data.get("risk_flags", {}).items(): lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def missing_games_md(summary: Dict[str, Any], rows: List[Dict[str, str]]) -> str:
    lines = ["# Missing Games Alert v5", "", f"Generated: `{now_iso()}`", "", "## Summary", ""]
    for key, value in summary.items(): lines.append(f"- {key}: `{value}`")
    lines.append("")
    if not summary.get("expected_fixture_file_present"):
        lines.extend(["## Status", "", "No expected-games fixture file was found. V5 can audit source coverage and duplicates, but cannot prove complete slate coverage without an expected-games fixture.", "Add `config/hsd_expected_games_v5.csv` with columns `date,league,home_team,away_team` when testing a known slate."])
    elif summary.get("missing", 0):
        lines.extend(["## Missing", ""])
        for row in rows:
            if row.get("matched") == "No": lines.append(f"- {row.get('date')} | {row.get('league')} | {row.get('away_team')} at {row.get('home_team')} | {row.get('reason')}")
    else: lines.extend(["## Status", "", "All expected games matched current free-source observations."])
    return "\n".join(lines) + "\n"


def game_attention_bucket(event: Dict[str, Any]) -> str:
    status = clean(event.get("status_norm"))
    if event.get("include_in_graphics"):
        return "recap_candidate"
    if status == "final":
        return "final_result"
    if status == "live":
        return "live_watch"
    if status == "scheduled":
        return "upcoming_game"
    return status or "review"


def stats_context_for(event: Dict[str, Any]) -> Tuple[str, str]:
    performers = clean(event.get("box_score_top_performers"))
    if performers:
        return "free_box_score_context_found", performers
    for key in ["top_performers_json", "team_stats_json", "player_stats_json"]:
        value = clean(event.get(key))
        if value:
            return "source_stats_present", value
    status = clean(event.get("status_norm"))
    audit_status = clean(event.get("box_score_audit_status"))
    if audit_status == "not_audited_sample_cap":
        return "box_score_not_checked_sample_cap", ""
    if audit_status == "disabled":
        return "box_score_audit_disabled", ""
    if audit_status == "error":
        return "box_score_audit_error", ""
    if status == "final":
        return "missing_free_box_score_context", ""
    if status == "scheduled":
        return "not_expected_pre_game", ""
    return "not_available_yet", ""


def confidence_reason_summary(event: Dict[str, Any]) -> str:
    raw = clean(event.get("confidence_reason_json"))
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except Exception:
        return raw[:240]
    adjustments = data.get("adjustments") or []
    parts = [f"base_source={data.get('base_source', '')}", f"final={data.get('final_confidence', '')}"]
    if adjustments:
        parts.append("adjustments=" + ",".join(clean(item[0]) for item in adjustments if item))
    return "; ".join(part for part in parts if part)


def missing_evidence_for(event: Dict[str, Any], stats_status: str) -> str:
    missing: List[str] = []
    if not clean(event.get("source_url")):
        missing.append("source_url")
    if clean(event.get("status_norm")) == "final" and not score_values_valid(event.get("home_score"), event.get("away_score")):
        missing.append("final_score")
    if stats_status == "missing_free_box_score_context":
        missing.append("box_score_or_top_performer_context")
    if stats_status == "box_score_not_checked_sample_cap":
        missing.append("box_score_audit_limit")
    if stats_status == "box_score_audit_error":
        missing.append("box_score_audit_error")
    if event.get("score_conflict"):
        missing.append("score_conflict_resolution")
    if event.get("manual_review"):
        missing.append("manual_review_clearance")
    try:
        if float(event.get("confidence") or 0) < 0.82:
            missing.append("higher_confidence_source_or_cross_check")
    except Exception:
        missing.append("confidence_parse")
    return "; ".join(missing) if missing else "none"


def selected_observation_by_key(observations: List[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
    selected: Dict[Tuple[str, str], Dict[str, str]] = {}
    for obs in observations:
        key = (clean(obs.get("canonical_key")), clean(obs.get("source_name")))
        if not key[0]:
            continue
        current = selected.get(key)
        if current is None or int(obs.get("source_priority") or 0) > int(current.get("source_priority") or 0):
            selected[key] = obs
    return selected


def source_confirmation_tier(source_url: Any, source_count: Any, selected_source: Any, status: Any, missing_evidence: Any = "") -> Tuple[str, str]:
    url = clean(source_url)
    count = int(clean(source_count) or "0") if clean(source_count).isdigit() else 0
    source = clean(selected_source)
    missing = clean(missing_evidence)
    if not url or "free_source_observation_match" in missing:
        return (
            "source_missing_manual_confirmation_required",
            "No matched free/public game observation is present for this row; operator must confirm manually before use.",
        )
    if not url.lower().startswith(("http://", "https://")):
        return (
            "manual_or_local_source_operator_verify",
            "Source points to a local/manual artifact rather than a live free/public URL; operator must verify the row before use.",
        )
    if count > 1:
        return (
            "multi_source_free_public_cross_check_operator_verify",
            "Multiple free/public observations contributed to this row; operator still verifies the listed source and any conflict notes before use.",
        )
    if source == "espn_wnba_public" or "espn.com" in source_domain(url):
        if clean(status) == "scheduled":
            return (
                "single_free_public_schedule_source_result_pending",
                "Single ESPN public scoreboard schedule row; result, box score, and recap use remain pending until the game is final.",
            )
        return (
            "single_free_public_scoreboard_operator_verify",
            "Single ESPN public scoreboard row; not a paid API, but not a human approval or publish-ready confirmation.",
        )
    return (
        "single_free_public_or_manual_source_operator_verify",
        "Single source row is present; operator must confirm the source class and facts before use.",
    )


def parse_utc_timestamp(value: Any) -> datetime | None:
    raw = clean(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def source_freshness_fields(retrieved_at_utc: Any, *, now: datetime | None = None, no_matched_source: bool = False) -> Dict[str, str]:
    if no_matched_source:
        return {
            "source_freshness_status": "no_matched_source_timestamp_manual_check",
            "source_freshness_age_minutes": "",
            "source_freshness_note": "No matched free/public source timestamp is available for this row.",
        }
    parsed = parse_utc_timestamp(retrieved_at_utc)
    if parsed is None:
        return {
            "source_freshness_status": "evidence_timestamp_missing_manual_check",
            "source_freshness_age_minutes": "",
            "source_freshness_note": "Retrieved timestamp is missing or invalid; operator should confirm source freshness before use.",
        }
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age_minutes = int((now_utc - parsed).total_seconds() // 60)
    if age_minutes < 0:
        return {
            "source_freshness_status": "evidence_timestamp_future_manual_check",
            "source_freshness_age_minutes": str(age_minutes),
            "source_freshness_note": "Retrieved timestamp is in the future relative to this run; operator should confirm source freshness.",
        }
    if age_minutes <= 180:
        return {
            "source_freshness_status": "evidence_fresh_under_3h_operator_verify",
            "source_freshness_age_minutes": str(age_minutes),
            "source_freshness_note": "Evidence was retrieved within 3 hours; operator still verifies source facts before use.",
        }
    if age_minutes <= 1440:
        return {
            "source_freshness_status": "evidence_same_day_under_24h_operator_verify",
            "source_freshness_age_minutes": str(age_minutes),
            "source_freshness_note": "Evidence is under 24 hours old; operator should check for final-score/stat changes before use.",
        }
    return {
        "source_freshness_status": "evidence_stale_over_24h_manual_check",
        "source_freshness_age_minutes": str(age_minutes),
        "source_freshness_note": "Evidence is over 24 hours old; operator should reopen the source or rerun Results before use.",
    }


def game_intelligence_rows(events: List[Dict[str, Any]], observations: List[Dict[str, str]], expected_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    obs_by_key = selected_observation_by_key(observations)
    rows: List[Dict[str, Any]] = []
    for event in events:
        stats_status, stats_context = stats_context_for(event)
        obs = obs_by_key.get((clean(event.get("canonical_key")), clean(event.get("selected_source"))), {})
        source_url = clean(event.get("source_url"))
        bucket = game_attention_bucket(event)
        tier, limitations = source_confirmation_tier(source_url, event.get("source_count"), event.get("selected_source"), event.get("status_norm"), missing_evidence_for(event, stats_status))
        retrieved_at = clean(obs.get("fetched_at_utc")) or now_iso()
        freshness = source_freshness_fields(retrieved_at)
        row_type = "game_event"
        if bucket == "upcoming_game":
            row_type = "upcoming_game"
        elif bucket == "final_result":
            row_type = "final_result"
        elif bucket == "recap_candidate":
            row_type = "recap_candidate"
        elif bucket == "live_watch":
            row_type = "live_game"
        rows.append(
            {
                "row_id": clean(event.get("event_uid")),
                "row_type": row_type,
                "attention_bucket": bucket,
                "game_date": clean(event.get("scheduled_date_local")),
                "league": clean(event.get("league_norm")),
                "sport": clean(event.get("sport_norm")),
                "home_team": clean(event.get("home_team_display")),
                "away_team": clean(event.get("away_team_display")),
                "status": clean(event.get("status_norm")),
                "final_score": clean(event.get("final_score_display")),
                "recap_candidate": "Yes" if event.get("include_in_graphics") else "No",
                "stats_context_status": stats_status,
                "stats_context": stats_context,
                "missing_evidence": missing_evidence_for(event, stats_status),
                "selected_source": clean(event.get("selected_source")),
                "source_count": clean(event.get("source_count")),
                "source_confidence": f"{float(event.get('confidence') or 0):.2f}",
                "source_confidence_reason": confidence_reason_summary(event),
                "source_confirmation_tier": tier,
                "source_confirmation_limitations": limitations,
                "source_url": source_url,
                "source_domain": source_domain(source_url),
                "retrieved_at_utc": retrieved_at,
                **freshness,
                "manual_review_status": "review_only_recap_candidate" if event.get("include_in_graphics") else "manual_review_required" if event.get("manual_review") else "review_only_monitor",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
    for expected in expected_rows:
        if clean(expected.get("matched")) != "No":
            continue
        source_url = clean(expected.get("source_url"))
        missing_bits = ["free_source_observation_match"]
        if clean(expected.get("date")) <= datetime.now(timezone.utc).date().isoformat():
            missing_bits.extend(["final_score", "stats_context"])
        else:
            missing_bits.append("scheduled_game_observation")
        rows.append(
            {
                "row_id": clean(expected.get("expected_key")),
                "row_type": "missing_expected_game",
                "attention_bucket": "missing_source_evidence",
                "game_date": clean(expected.get("date")),
                "league": clean(expected.get("league")),
                "sport": clean(expected.get("sport") or "basketball"),
                "home_team": clean(expected.get("home_team")),
                "away_team": clean(expected.get("away_team")),
                "status": clean(expected.get("reason")) or "missing_from_free_sources_or_outside_window",
                "final_score": "",
                "recap_candidate": "No",
                "stats_context_status": "missing_game_observation",
                "stats_context": "",
                "missing_evidence": "; ".join(missing_bits),
                "selected_source": clean(expected.get("source_name")),
                "source_count": "0",
                "source_confidence": "0.00",
                "source_confidence_reason": "expected game was not matched by current free-source observations",
                "source_confirmation_tier": "source_missing_manual_confirmation_required",
                "source_confirmation_limitations": "Expected game seed has no matched free/public observation in this run; operator must confirm schedule/result manually.",
                "source_url": source_url,
                "source_domain": source_domain(source_url),
                "retrieved_at_utc": now_iso(),
                **source_freshness_fields("", no_matched_source=True),
                "manual_review_status": "manual_review_required_missing_source_evidence",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
    rows.sort(key=lambda row: (row.get("game_date", ""), row.get("attention_bucket", ""), row.get("away_team", "")))
    return rows


def game_intelligence_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def count_where(field: str, value: str) -> int:
        return sum(1 for row in rows if clean(row.get(field)) == value)

    return {
        "version": "v1-review-only-game-intelligence-board",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "upcoming_games": count_where("row_type", "upcoming_game"),
        "live_games": count_where("row_type", "live_game"),
        "final_results": count_where("status", "final"),
        "recap_candidates": count_where("row_type", "recap_candidate"),
        "missing_expected_games": count_where("row_type", "missing_expected_game"),
        "missing_stats_context": count_where("stats_context_status", "missing_free_box_score_context"),
    }


def game_intelligence_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Intelligence Board v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only output.",
        "- No paid APIs, credentials, source enablement, approvals, publishing, or publish-ready movement.",
        "- Every row keeps source confidence, source URL/domain, retrieval timestamp, and manual-review status visible.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "upcoming_games", "live_games", "final_results", "recap_candidates", "missing_expected_games", "missing_stats_context"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Operator Rows", ""])
    if not rows:
        lines.append("No game rows are available from the current free/public or manual sources.")
    if len(rows) > 80:
        lines.append(f"Showing first 80 of {len(rows)} rows. Open `game_intelligence_board_v1.csv` for the full board.")
    for row in rows[:80]:
        matchup = f"{row.get('away_team')} at {row.get('home_team')}".strip()
        lines.append(f"- **{row.get('attention_bucket')}** | {row.get('game_date')} | {row.get('league')} | {matchup}")
        lines.append(f"  - status={row.get('status')} | confidence={row.get('source_confidence')} | review={row.get('manual_review_status')}")
        lines.append(f"  - source_tier={row.get('source_confirmation_tier')} | limits={row.get('source_confirmation_limitations')}")
        lines.append(f"  - freshness={row.get('source_freshness_status')} | age_min={row.get('source_freshness_age_minutes') or 'n/a'} | note={row.get('source_freshness_note')}")
        lines.append(f"  - stats={row.get('stats_context_status')} | missing={row.get('missing_evidence')}")
        lines.append(f"  - source_cue={row.get('source_confirmation_cue')} | render={row.get('recap_render_readiness')}")
        lines.append(f"  - fact_status={row.get('game_fact_status_row_to_open') or 'missing'} | proof={row.get('proof_review_order_row_to_open') or 'missing'}")
        lines.append(f"  - next={row.get('operator_next_review_step') or 'missing'}")
        if row.get("source_url"):
            lines.append(f"  - source={row.get('source_url')}")
    return "\n".join(lines) + "\n"


def stats_evidence_status(event: Dict[str, Any], stats_status: str) -> Tuple[str, str, str]:
    audit_status = clean(event.get("box_score_audit_status"))
    if stats_status == "free_box_score_context_found":
        return "confirmed_free_public_box_score", "No", "Review stats text against source before writing copy."
    if stats_status == "source_stats_present":
        return "source_stats_present_manual_review", "Yes", "Confirm manually supplied stats and source URL before using in copy."
    if stats_status == "box_score_not_checked_sample_cap":
        return "box_score_audit_capped", "Yes", "Open the confirmation source and record whether box-score/top-performer evidence is present."
    if stats_status == "box_score_audit_disabled":
        return "box_score_audit_disabled", "Yes", "Run the box-score audit or manually confirm stats from the source URL."
    if stats_status == "box_score_audit_error":
        return "box_score_audit_error", "Yes", "Retry the public source or manually confirm stats from the source URL."
    if stats_status == "missing_free_box_score_context":
        if audit_status == "summary_found_no_performers":
            return "box_score_summary_no_performers", "Yes", "Open the source box score and confirm whether usable stat context exists."
        return "missing_box_score_or_top_performer_context", "Yes", "Find a free/public box score or leave stats out of copy."
    if clean(event.get("status_norm")) != "final":
        return "not_final_stats_optional", "No", "No final-stat confirmation expected yet."
    return "stats_evidence_unknown", "Yes", "Manually confirm whether stat context is available."


def stats_missing_evidence(status: str, stats_status: str) -> str:
    if status == "confirmed_free_public_box_score":
        return "none"
    if status == "source_stats_present_manual_review":
        return "operator_confirmation_of_manual_stats"
    if status == "box_score_summary_no_performers":
        return "top_performer_context"
    if status == "box_score_audit_capped":
        return "box_score_audit_not_run_for_this_row"
    if status == "box_score_audit_disabled":
        return "box_score_audit_disabled"
    if status == "box_score_audit_error":
        return "box_score_audit_retry_or_manual_source_check"
    if status == "missing_box_score_or_top_performer_context":
        return "box_score_or_top_performer_context"
    if status == "not_final_stats_optional":
        return "none"
    return clean(stats_status) or "stats_evidence"


def stats_evidence_gap_rows(events: List[Dict[str, Any]], observations: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    obs_by_key = selected_observation_by_key(observations)
    rows: List[Dict[str, Any]] = []
    intake: List[Dict[str, Any]] = []
    focus_events = [
        event
        for event in events
        if clean(event.get("status_norm")) == "final" or bool(event.get("include_in_graphics"))
    ]
    for event in focus_events:
        stats_status, stats_context = stats_context_for(event)
        status, manual_needed, next_step = stats_evidence_status(event, stats_status)
        source_url = clean(event.get("source_url"))
        obs = obs_by_key.get((clean(event.get("canonical_key")), clean(event.get("selected_source"))), {})
        matchup = f"{clean(event.get('away_team_display'))} at {clean(event.get('home_team_display'))}".strip()
        row = {
            "event_uid": clean(event.get("event_uid")),
            "game_date": clean(event.get("scheduled_date_local")),
            "league": clean(event.get("league_norm")),
            "sport": clean(event.get("sport_norm")),
            "matchup": matchup,
            "status": clean(event.get("status_norm")),
            "recap_candidate": "Yes" if event.get("include_in_graphics") else "No",
            "final_score": clean(event.get("final_score_display")),
            "stats_evidence_status": status,
            "box_score_audit_status": clean(event.get("box_score_audit_status")),
            "top_performers": stats_context if stats_status in {"free_box_score_context_found", "source_stats_present"} else "",
            "missing_stat_evidence": stats_missing_evidence(status, stats_status),
            "manual_confirmation_needed": manual_needed,
            "operator_next_step": next_step,
            "confirmation_source_url": source_url,
            "confirmation_source_domain": source_domain(source_url),
            "selected_score_source": clean(event.get("selected_source")),
            "score_source_url": source_url,
            "source_confidence": f"{float(event.get('confidence') or 0):.2f}",
            "retrieved_at_utc": clean(obs.get("fetched_at_utc")) or now_iso(),
            "review_only": "Yes",
            "approval_state_change": "none",
            "publish_action": "none_artifact_only",
        }
        rows.append(row)
        if manual_needed == "Yes":
            intake.append(
                {
                    "event_uid": row["event_uid"],
                    "game_date": row["game_date"],
                    "league": row["league"],
                    "matchup": row["matchup"],
                    "status": row["status"],
                    "final_score": row["final_score"],
                    "manual_confirmation_needed": "Yes",
                    "operator_next_step": next_step,
                    "confirmation_source_url": source_url,
                    "operator_checked_url": "",
                    "operator_confirmation_status": "",
                    "operator_confirmed_stats": "",
                    "operator_notes": "",
                    "review_only": "Yes",
                    "approval_state_change": "none",
                    "publish_action": "none_artifact_only",
                }
            )
    rows.sort(key=lambda row: (row.get("manual_confirmation_needed") != "Yes", row.get("game_date", ""), row.get("matchup", "")))
    intake.sort(key=lambda row: (row.get("game_date", ""), row.get("matchup", "")))
    return rows, intake


def stats_evidence_gap_summary(rows: List[Dict[str, Any]], intake: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        counts[clean(row.get("stats_evidence_status"))] += 1
    return {
        "version": "v1-review-only-stats-evidence-gap-board",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "manual_confirmation_rows": len(intake),
        "confirmed_free_public_box_score": counts.get("confirmed_free_public_box_score", 0),
        "missing_or_manual_confirmation": len(intake),
        "status_counts": dict(sorted(counts.items())),
    }


def stats_evidence_gap_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]], intake: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Stats Evidence Gap Board v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only stats evidence board.",
        "- No paid APIs, credentials, source enablement, story/render approval changes, publishing, or publish-ready movement.",
        "- Operator confirmation rows are manual intake only; blank fields are for human review notes.",
        "",
        "## Counts",
        "",
        f"- final_or_recap_rows: `{summary['rows']}`",
        f"- confirmed_free_public_box_score: `{summary['confirmed_free_public_box_score']}`",
        f"- manual_confirmation_rows: `{summary['manual_confirmation_rows']}`",
        "",
        "## Manual Confirmation Needed",
        "",
    ]
    if not intake:
        lines.append("No final/recap stat evidence gaps require manual confirmation in this run.")
    else:
        by_id = {row.get("event_uid"): row for row in rows}
        for item in intake[:80]:
            row = by_id.get(item.get("event_uid"), {})
            lines.append(f"- **{item.get('matchup')}** | {item.get('game_date')} | {row.get('stats_evidence_status')}")
            lines.append(f"  - missing={row.get('missing_stat_evidence')} | score={item.get('final_score')}")
            lines.append(f"  - next={item.get('operator_next_step')}")
            if item.get("confirmation_source_url"):
                lines.append(f"  - source={item.get('confirmation_source_url')}")
    if len(intake) > 80:
        lines.append(f"Showing first 80 of {len(intake)} intake rows. Open `stats_confirmation_intake_v1.csv` for the full intake.")
    lines.extend(["", "## Confirmed Evidence Rows", ""])
    confirmed = [row for row in rows if row.get("stats_evidence_status") == "confirmed_free_public_box_score"]
    if not confirmed:
        lines.append("No final/recap rows have confirmed free/public box-score context yet.")
    for row in confirmed[:40]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('game_date')} | confidence={row.get('source_confidence')}")
        lines.append(f"  - performers={row.get('top_performers') or 'none'}")
        lines.append(f"  - source={row.get('confirmation_source_url')}")
    if len(confirmed) > 40:
        lines.append(f"Showing first 40 of {len(confirmed)} confirmed rows. Open `stats_evidence_gap_board_v1.csv` for the full board.")
    return "\n".join(lines) + "\n"


def fact_status_stats_by_event(stats_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {clean(row.get("event_uid")): row for row in stats_rows if clean(row.get("event_uid"))}


def game_schedule_fact_status(row: Dict[str, Any]) -> str:
    if clean(row.get("row_type")) == "missing_expected_game":
        return "schedule_source_missing_manual_verification_required"
    if not clean(row.get("source_url")):
        return "schedule_source_url_missing_manual_verification_required"
    try:
        confidence = float(clean(row.get("source_confidence")) or 0)
    except Exception:
        confidence = 0.0
    if confidence < 0.82:
        return "schedule_source_present_low_confidence_manual_verify"
    return "schedule_source_confirmed_free_public_operator_verify"


def game_result_fact_status(row: Dict[str, Any]) -> str:
    status = clean(row.get("status"))
    missing = clean(row.get("missing_evidence"))
    if clean(row.get("row_type")) == "missing_expected_game":
        if "final_score" in missing:
            return "final_score_missing_manual_verification_required"
        return "result_not_expected_yet_missing_schedule_observation"
    if status == "final":
        if "final_score" in missing or not clean(row.get("final_score")):
            return "final_score_missing_manual_verification_required"
        return "final_score_source_confirmed_free_public_operator_verify"
    if status == "live":
        return "live_result_not_final_manual_monitor"
    return "not_final_result_pending"


def game_stats_fact_status(row: Dict[str, Any], stats_row: Dict[str, Any]) -> str:
    status = clean(row.get("status"))
    if status != "final" and clean(row.get("recap_candidate")) != "Yes":
        return "not_final_stats_optional"
    if not stats_row:
        return "stats_evidence_row_missing_manual_review_required"
    stats_status = clean(stats_row.get("stats_evidence_status"))
    if stats_status == "confirmed_free_public_box_score":
        return "stats_source_confirmed_free_public_operator_verify"
    if clean(stats_row.get("manual_confirmation_needed")) == "Yes":
        return "stats_manual_confirmation_required"
    return stats_status or "stats_evidence_unknown_manual_review_required"


def game_fact_missing_confirmation(schedule_status: str, result_status: str, stats_status: str) -> str:
    missing: List[str] = []
    if "missing" in schedule_status or "low_confidence" in schedule_status:
        missing.append("schedule_source")
    if "missing" in result_status or "live_result" in result_status:
        missing.append("result_or_final_score")
    if "missing" in stats_status or "manual" in stats_status or "unknown" in stats_status:
        missing.append("stats_or_box_score")
    return "; ".join(missing) if missing else "none"


def game_fact_overall_status(schedule_status: str, result_status: str, stats_status: str, missing: str) -> str:
    if missing != "none":
        return "manual_verification_required"
    if result_status == "not_final_result_pending":
        return "schedule_confirmed_result_pending"
    if result_status == "live_result_not_final_manual_monitor":
        return "live_monitor_manual_review"
    return "source_confirmed_operator_verify_before_use"


def game_fact_next_step(row: Dict[str, Any], stats_row: Dict[str, Any], missing: str) -> str:
    row_id = clean(row.get("row_id"))
    parts = [f"Open game_intelligence_board_v1.csv row_id={row_id}" if row_id else "Open game_intelligence_board_v1.csv for this row"]
    if clean(row.get("row_type")) == "missing_expected_game":
        parts.append("open missing_games_alert_v5.csv for the unmatched expected-game row")
    if clean(row.get("status")) == "final" or clean(row.get("recap_candidate")) == "Yes":
        if stats_row:
            parts.append(f"open stats_evidence_gap_board_v1.csv event_uid={clean(stats_row.get('event_uid'))}")
        else:
            parts.append("open stats_confirmation_intake_v1.csv and add/check the missing stats evidence row")
    if missing != "none":
        parts.append("record manual confirmation before editorial use")
    else:
        parts.append("operator should still verify the listed source before using facts in copy")
    return "; then ".join(parts) + "."


def game_fact_confirmation_status_rows(intelligence_rows: List[Dict[str, Any]], stats_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stats_by_event = fact_status_stats_by_event(stats_rows)
    rows: List[Dict[str, Any]] = []
    for item in intelligence_rows:
        event_uid = clean(item.get("row_id"))
        stats_row = stats_by_event.get(event_uid, {})
        schedule_status = game_schedule_fact_status(item)
        result_status = game_result_fact_status(item)
        stats_status = game_stats_fact_status(item, stats_row)
        missing = game_fact_missing_confirmation(schedule_status, result_status, stats_status)
        overall = game_fact_overall_status(schedule_status, result_status, stats_status, missing)
        matchup = f"{clean(item.get('away_team'))} at {clean(item.get('home_team'))}".strip()
        tier, limitations = source_confirmation_tier(
            item.get("source_url"),
            clean(item.get("source_count")) or ("0" if "free_source_observation_match" in clean(item.get("missing_evidence")) else "1"),
            item.get("selected_source"),
            item.get("status"),
            item.get("missing_evidence"),
        )
        retrieved_at = clean(item.get("retrieved_at_utc")) or now_iso()
        freshness = {
            "source_freshness_status": clean(item.get("source_freshness_status")),
            "source_freshness_age_minutes": clean(item.get("source_freshness_age_minutes")),
            "source_freshness_note": clean(item.get("source_freshness_note")),
        }
        if not freshness["source_freshness_status"]:
            freshness = source_freshness_fields(retrieved_at, no_matched_source="free_source_observation_match" in clean(item.get("missing_evidence")))
        rows.append(
            {
                "event_uid": event_uid,
                "game_date": clean(item.get("game_date")),
                "league": clean(item.get("league")),
                "sport": clean(item.get("sport")),
                "matchup": matchup,
                "game_status": clean(item.get("status")),
                "attention_bucket": clean(item.get("attention_bucket")),
                "recap_candidate": clean(item.get("recap_candidate")),
                "schedule_fact_status": schedule_status,
                "result_fact_status": result_status,
                "stats_fact_status": stats_status,
                "overall_confirmation_status": overall,
                "source_confidence": clean(item.get("source_confidence")),
                "source_confirmation_tier": clean(item.get("source_confirmation_tier")) or tier,
                "source_confirmation_limitations": clean(item.get("source_confirmation_limitations")) or limitations,
                "source_url": clean(item.get("source_url")),
                "source_domain": clean(item.get("source_domain")),
                "stats_source_url": clean(stats_row.get("confirmation_source_url")),
                "missing_confirmation": missing,
                "exact_next_file_or_intake": game_fact_next_step(item, stats_row, missing),
                "manual_review_required": "Yes" if missing != "none" or clean(item.get("recap_candidate")) == "Yes" else "No",
                "retrieved_at_utc": retrieved_at,
                **freshness,
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
    rows.sort(key=lambda row: (row.get("overall_confirmation_status") != "manual_verification_required", row.get("game_date", ""), row.get("matchup", "")))
    return rows


def game_fact_confirmation_status_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        counts[clean(row.get("overall_confirmation_status"))] += 1
    return {
        "version": "v1-review-only-game-fact-confirmation-status",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "manual_verification_required": counts.get("manual_verification_required", 0),
        "source_confirmed_operator_verify_before_use": counts.get("source_confirmed_operator_verify_before_use", 0),
        "schedule_confirmed_result_pending": counts.get("schedule_confirmed_result_pending", 0),
        "status_counts": dict(sorted(counts.items())),
    }


def game_fact_confirmation_status_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Fact Confirmation Status v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only confirmation status board.",
        "- No paid APIs, credentials, source enablement, approvals, publishing, or publish-ready movement.",
        "- Open the exact file or intake listed on each row before using schedule, score, or stat facts in copy.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "manual_verification_required", "source_confirmed_operator_verify_before_use", "schedule_confirmed_result_pending"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Rows Needing Manual Verification", ""])
    needs = [row for row in rows if row.get("overall_confirmation_status") == "manual_verification_required"]
    if not needs:
        lines.append("No game fact rows require manual confirmation beyond operator source review in this run.")
    for row in needs[:80]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('game_date')} | {row.get('game_status')} | missing={row.get('missing_confirmation')}")
        lines.append(f"  - schedule={row.get('schedule_fact_status')} | result={row.get('result_fact_status')} | stats={row.get('stats_fact_status')}")
        lines.append(f"  - source_tier={row.get('source_confirmation_tier')} | limits={row.get('source_confirmation_limitations')}")
        lines.append(f"  - freshness={row.get('source_freshness_status')} | age_min={row.get('source_freshness_age_minutes') or 'n/a'} | note={row.get('source_freshness_note')}")
        lines.append(f"  - source_cue={row.get('source_confirmation_cue')} | render={row.get('recap_render_readiness')}")
        lines.append(f"  - proof_card={row.get('story_proof_card_row_to_open') or 'missing'}")
        lines.append(f"  - review_order_score={row.get('final_score_review_order_row') or 'missing'} | review_order_named={row.get('named_stat_review_order_row') or 'missing'}")
        lines.append(f"  - next={row.get('exact_next_file_or_intake')}")
    if len(needs) > 80:
        lines.append(f"Showing first 80 of {len(needs)} rows. Open `game_fact_confirmation_status_v1.csv` for the full board.")
    lines.extend(["", "## Source-Confirmed / Pending Rows", ""])
    for row in [item for item in rows if item.get("overall_confirmation_status") != "manual_verification_required"][:40]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('game_date')} | {row.get('overall_confirmation_status')}")
        lines.append(f"  - schedule={row.get('schedule_fact_status')} | result={row.get('result_fact_status')} | stats={row.get('stats_fact_status')}")
        lines.append(f"  - source_tier={row.get('source_confirmation_tier')} | limits={row.get('source_confirmation_limitations')}")
        lines.append(f"  - freshness={row.get('source_freshness_status')} | age_min={row.get('source_freshness_age_minutes') or 'n/a'} | note={row.get('source_freshness_note')}")
        lines.append(f"  - source_cue={row.get('source_confirmation_cue')} | render={row.get('recap_render_readiness')}")
        lines.append(f"  - proof_card={row.get('story_proof_card_row_to_open') or 'missing'}")
        lines.append(f"  - review_order_score={row.get('final_score_review_order_row') or 'missing'} | review_order_named={row.get('named_stat_review_order_row') or 'missing'}")
        lines.append(f"  - next={row.get('exact_next_file_or_intake')}")
    return "\n".join(lines) + "\n"


def source_confirmation_public_cue(row: Dict[str, Any]) -> str:
    tier = clean(row.get("source_confirmation_tier"))
    url = clean(row.get("source_url"))
    domain = clean(row.get("source_domain")) or source_domain(url)
    if tier == "source_missing_manual_confirmation_required":
        return "no_matched_free_public_source_manual_confirmation_required"
    if tier == "manual_or_local_source_operator_verify":
        return "manual_or_local_source_operator_verify"
    if tier == "multi_source_free_public_cross_check_operator_verify":
        return "multiple_free_public_sources_cross_check_operator_verify"
    if "espn.com" in domain or "free_public" in tier:
        return "public_scoreboard_source_operator_verify"
    if url.lower().startswith(("http://", "https://")):
        return "free_public_or_reputable_web_source_operator_verify"
    return "source_class_unknown_manual_confirmation_required"


def source_second_check_cue(row: Dict[str, Any]) -> str:
    tier = clean(row.get("source_confirmation_tier"))
    stats_status = clean(row.get("stats_fact_status"))
    game_status = clean(row.get("game_status"))
    source_url = clean(row.get("source_url"))
    stats_source_url = clean(row.get("stats_source_url")) or clean(row.get("box_score_or_stat_source_url"))
    missing = clean(row.get("missing_confirmation"))
    if not source_url or "source_missing" in tier or missing not in ("", "none"):
        return "find_primary_free_public_source_before_second_source_check"
    if "multi_source" in tier:
        return "multiple_free_public_sources_present_operator_cross_check"
    if game_status in {"scheduled", "live"}:
        return "recheck_same_public_scoreboard_after_game_window_before_final_use"
    if "stats_source_confirmed" in stats_status and stats_source_url and stats_source_url != source_url:
        return "score_and_stats_sources_present_operator_cross_check"
    if "stats_source_confirmed" in stats_status or "box_score" in stats_status:
        return "single_box_score_source_present_second_free_public_source_recommended_before_copy_or_render"
    if clean(row.get("recap_candidate")) == "Yes" or game_status == "final":
        return "find_second_free_public_box_score_or_recap_before_named_stat_use"
    return "free_public_source_currentness_recheck_operator_verify"


def source_confirmation_review_priority(row: Dict[str, Any]) -> str:
    missing = clean(row.get("missing_confirmation"))
    freshness = clean(row.get("source_freshness_status"))
    overall = clean(row.get("overall_confirmation_status") or row.get("confirmation_state"))
    result_status = clean(row.get("result_fact_status"))
    game_status = clean(row.get("game_status"))
    recap = clean(row.get("recap_candidate")) == "Yes"
    if overall == "manual_verification_required" or missing not in ("", "none"):
        return "P0_manual_confirmation_required"
    if freshness in {
        "no_matched_source_timestamp_manual_check",
        "evidence_timestamp_missing_manual_check",
        "evidence_timestamp_future_manual_check",
        "evidence_stale_over_24h_manual_check",
    }:
        return "P1_source_freshness_or_lag_check"
    if recap or game_status == "final":
        return "P2_final_recap_source_review"
    if result_status in {"not_final_result_pending", "live_result_not_final_manual_monitor"} or game_status in {"scheduled", "live"}:
        return "P3_result_pending_monitor"
    return "P4_source_audit_no_fix"


def source_confirmation_lag_note(row: Dict[str, Any]) -> str:
    missing = clean(row.get("missing_confirmation"))
    freshness = clean(row.get("source_freshness_status"))
    if missing and missing != "none":
        return f"Manual confirmation still needed for: {missing}."
    if freshness in {
        "no_matched_source_timestamp_manual_check",
        "evidence_timestamp_missing_manual_check",
        "evidence_timestamp_future_manual_check",
        "evidence_stale_over_24h_manual_check",
    }:
        return clean(row.get("source_freshness_note")) or "Source timestamp needs operator freshness confirmation."
    if clean(row.get("result_fact_status")) == "not_final_result_pending":
        return "Schedule row is present, but result, final score, and stats remain pending."
    if clean(row.get("result_fact_status")) == "live_result_not_final_manual_monitor":
        return "Game is live or not final; monitor the same source before recap or render use."
    if clean(row.get("recap_candidate")) == "Yes" or clean(row.get("game_status")) == "final":
        return "Final/recap row has source evidence; operator still opens proof rows before copy or render use."
    return "No fix is required in this run beyond normal operator source review."


def recap_render_human_review_gate(row: Dict[str, Any], priority: str) -> str:
    missing = clean(row.get("missing_confirmation"))
    readiness = clean(row.get("recap_render_readiness"))
    if priority == "P0_manual_confirmation_required" or missing not in ("", "none"):
        return "blocked_manual_source_confirmation_required"
    if priority == "P1_source_freshness_or_lag_check":
        return "blocked_source_freshness_check_required"
    if priority == "P3_result_pending_monitor":
        return "blocked_result_pending_not_recap_or_render_ready"
    if clean(row.get("recap_candidate")) == "Yes" or clean(row.get("game_status")) == "final":
        if readiness:
            return f"{readiness}_human_review_required"
        return "recap_or_render_candidate_human_review_required"
    return "not_recap_or_render_candidate"


def source_confirmation_next_action_text(row: Dict[str, Any], priority: str) -> str:
    event_uid = clean(row.get("event_uid"))
    source_row = f"game_fact_confirmation_status_v1.csv event_uid={event_uid}" if event_uid else "game_fact_confirmation_status_v1.csv"
    proof_row = clean(row.get("story_proof_card_row_to_open")) or clean(row.get("final_score_review_order_row")) or clean(row.get("named_stat_review_order_row"))
    intake = clean(row.get("proof_manual_intake_path"))
    source_url = clean(row.get("source_url"))
    if priority == "P0_manual_confirmation_required":
        return clean(row.get("exact_next_file_or_intake")) or f"Open {source_row}; record the manual source check before using this game fact."
    if priority == "P1_source_freshness_or_lag_check":
        target = source_url or source_row
        return f"Open {target}; confirm the source is current, then record any source/stat check in {intake or source_row}."
    if priority == "P2_final_recap_source_review":
        if proof_row:
            return f"Open {source_row}; then open {proof_row}; verify source facts before copy/render use."
        return f"Open {source_row}; verify final score/stat source facts before copy/render use."
    if priority == "P3_result_pending_monitor":
        return f"Open {source_url or source_row} after the game window; rerun Results before treating the row as final or recap-ready."
    return f"Open {source_row} only if this game becomes a story/render candidate; no approval or publishing action is implied."


def game_source_confirmation_next_action_rows(fact_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in fact_rows:
        priority = source_confirmation_review_priority(item)
        event_uid = clean(item.get("event_uid"))
        proof_row = clean(item.get("story_proof_card_row_to_open")) or clean(item.get("final_score_review_order_row")) or clean(item.get("named_stat_review_order_row"))
        missing_expected = "Yes" if clean(item.get("source_confirmation_tier")) == "source_missing_manual_confirmation_required" or "schedule_source" in clean(item.get("missing_confirmation")) else "No"
        rows.append(
            {
                "action_rank": "",
                "operator_review_order_cue": "",
                "event_uid": event_uid,
                "game_date": clean(item.get("game_date")),
                "league": clean(item.get("league")),
                "matchup": clean(item.get("matchup")),
                "game_status": clean(item.get("game_status")),
                "recap_candidate": clean(item.get("recap_candidate")),
                "review_priority": priority,
                "confirmation_state": clean(item.get("overall_confirmation_status")),
                "source_confidence": clean(item.get("source_confidence")),
                "schedule_fact_status": clean(item.get("schedule_fact_status")),
                "result_fact_status": clean(item.get("result_fact_status")),
                "stats_fact_status": clean(item.get("stats_fact_status")),
                "source_confirmation_tier": clean(item.get("source_confirmation_tier")),
                "source_freshness_status": clean(item.get("source_freshness_status")),
                "source_freshness_age_minutes": clean(item.get("source_freshness_age_minutes")),
                "missing_confirmation": clean(item.get("missing_confirmation")) or "none",
                "missing_expected_game_flag": missing_expected,
                "conflict_or_lag_note": source_confirmation_lag_note(item),
                "official_or_public_source_cue": source_confirmation_public_cue(item),
                "second_source_check_cue": source_second_check_cue(item),
                "recap_render_readiness": clean(item.get("recap_render_readiness")),
                "recap_render_human_review_gate": recap_render_human_review_gate(item, priority),
                "source_url": clean(item.get("source_url")),
                "source_domain": clean(item.get("source_domain")),
                "source_row_to_open": f"game_fact_confirmation_status_v1.csv event_uid={event_uid}" if event_uid else "game_fact_confirmation_status_v1.csv",
                "proof_row_to_open": proof_row,
                "manual_intake_path": clean(item.get("proof_manual_intake_path")),
                "source_confirmation_next_action": source_confirmation_next_action_text(item, priority),
                "manual_confirmation_return_fields": "operator_checked_source_url, operator_source_confirmation_status, operator_source_confirmation_notes",
                "operator_checked_source_url": "",
                "operator_source_confirmation_status": "",
                "operator_source_confirmation_notes": "",
                "review_only": "Yes",
                "approval_state_change": "none",
                "source_enablement": "none_existing_local_artifacts_only",
                "publish_action": "none_artifact_only",
            }
        )
    priority_order = {
        "P0_manual_confirmation_required": 0,
        "P1_source_freshness_or_lag_check": 1,
        "P2_final_recap_source_review": 2,
        "P3_result_pending_monitor": 3,
        "P4_source_audit_no_fix": 4,
    }
    rows.sort(key=lambda row: (priority_order.get(row.get("review_priority"), 9), row.get("game_date", ""), row.get("matchup", "")))
    for index, row in enumerate(rows, start=1):
        row["action_rank"] = str(index)
        row["operator_review_order_cue"] = "START_HERE_first_incomplete_game_source_confirmation_row" if index == 1 else "continue_in_action_rank_order"
    return rows


def game_source_confirmation_next_action_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    gate_counts: Dict[str, int] = defaultdict(int)
    blank_manual_return_fields = True
    for row in rows:
        counts[clean(row.get("review_priority"))] += 1
        gate_counts[clean(row.get("recap_render_human_review_gate"))] += 1
        for field in [
            "operator_checked_source_url",
            "operator_source_confirmation_status",
            "operator_source_confirmation_notes",
        ]:
            if clean(row.get(field)):
                blank_manual_return_fields = False
    return {
        "version": "v1-review-only-game-source-confirmation-next-action",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "source_enablement": False,
        "manual_return_fields_prefilled": not blank_manual_return_fields,
        "rows": len(rows),
        "manual_confirmation_required": counts.get("P0_manual_confirmation_required", 0),
        "freshness_or_lag_check": counts.get("P1_source_freshness_or_lag_check", 0),
        "final_recap_source_review": counts.get("P2_final_recap_source_review", 0),
        "result_pending_monitor": counts.get("P3_result_pending_monitor", 0),
        "source_audit_no_fix": counts.get("P4_source_audit_no_fix", 0),
        "recap_render_human_review_required": sum(value for key, value in gate_counts.items() if key.endswith("_human_review_required")),
        "blocked_before_recap_render": sum(value for key, value in gate_counts.items() if key.startswith("blocked_")),
        "priority_counts": dict(sorted(counts.items())),
        "gate_counts": dict(sorted(gate_counts.items())),
    }


def game_source_confirmation_next_action_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Source Confirmation Next Actions v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only source confirmation triage.",
        "- No paid APIs, downloads, source enablement, approvals, publishing, or publish-ready movement.",
        "- Rows are advisory only; operator decisions remain in the listed manual intake or proof artifact.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "manual_confirmation_required", "freshness_or_lag_check", "final_recap_source_review", "result_pending_monitor", "source_audit_no_fix", "recap_render_human_review_required", "blocked_before_recap_render"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.append(f"- manual_return_fields_prefilled: `{summary.get('manual_return_fields_prefilled')}`")
    lines.extend(["", "## Review Order", ""])
    if not rows:
        lines.append("No game source confirmation rows were generated in this run.")
    for row in rows[:80]:
        lines.append(f"{row.get('action_rank')}. **{row.get('matchup')}** | {row.get('game_date')} | {row.get('review_priority')}")
        lines.append(f"   - state={row.get('confirmation_state')} | confidence={row.get('source_confidence') or 'n/a'} | tier={row.get('source_confirmation_tier')} | freshness={row.get('source_freshness_status')} | age_min={row.get('source_freshness_age_minutes') or 'n/a'}")
        lines.append(f"   - schedule={row.get('schedule_fact_status')} | result={row.get('result_fact_status')} | stats={row.get('stats_fact_status')}")
        lines.append(f"   - start={row.get('operator_review_order_cue')} | missing={row.get('missing_confirmation')} | source_cue={row.get('official_or_public_source_cue')} | second_check={row.get('second_source_check_cue')} | lag={row.get('conflict_or_lag_note')}")
        lines.append(f"   - recap_render={row.get('recap_render_readiness') or 'n/a'} | gate={row.get('recap_render_human_review_gate')}")
        lines.append(f"   - open={row.get('source_row_to_open')} | proof={row.get('proof_row_to_open') or 'not required'} | intake={row.get('manual_intake_path') or 'not required'}")
        lines.append(f"   - next={row.get('source_confirmation_next_action')}")
        lines.append(f"   - return_fields={row.get('manual_confirmation_return_fields')}")
    if len(rows) > 80:
        lines.append(f"Showing first 80 of {len(rows)} rows. Open `game_source_confirmation_next_action_v1.csv` for the full board.")
    return "\n".join(lines) + "\n"


def game_source_research_need(row: Dict[str, Any]) -> str:
    priority = clean(row.get("review_priority"))
    stats_status = clean(row.get("stats_fact_status"))
    missing = clean(row.get("missing_confirmation"))
    if priority == "P0_manual_confirmation_required" or missing not in ("", "none"):
        return "find_official_or_public_schedule_result_stat_source"
    if priority == "P1_source_freshness_or_lag_check":
        return "refresh_existing_source_and_confirm_current_facts"
    if clean(row.get("recap_candidate")) == "Yes" or clean(row.get("game_status")) == "final":
        if "manual" in stats_status or "missing" in stats_status or not clean(row.get("proof_row_to_open")):
            return "find_box_score_or_named_stat_source"
        return "confirm_final_score_and_named_stat_source_before_recap"
    if priority == "P3_result_pending_monitor":
        return "monitor_public_scoreboard_until_final"
    return "optional_source_audit_no_fix"


def game_source_research_prompt(row: Dict[str, Any], need: str) -> str:
    matchup = clean(row.get("matchup")) or "this game"
    league = clean(row.get("league")) or "league"
    source_url = clean(row.get("source_url"))
    if need == "find_official_or_public_schedule_result_stat_source":
        return f"Find a free official or reputable public source confirming schedule/result/stat facts for {league} {matchup}; record URLs only in the blank operator fields."
    if need == "refresh_existing_source_and_confirm_current_facts":
        return f"Open the current source URL for {league} {matchup}, confirm it is current, and record any fresher official/public source in the blank operator fields."
    if need == "find_box_score_or_named_stat_source":
        return f"Find a free official/public box score or recap source for named player stat lines in {league} {matchup}; do not infer stats from unsourced copy."
    if need == "confirm_final_score_and_named_stat_source_before_recap":
        return f"Open the listed free/public scoreboard or box-score source for {league} {matchup}; verify the final score and named player stat line, check a second free/public source when available, and record only human-confirmed URLs/status in blank operator fields before recap or render use."
    if need == "monitor_public_scoreboard_until_final":
        return f"After the game window, open {source_url or 'the public scoreboard'} for {league} {matchup}, rerun Results, and record final-score/box-score confirmation only if visible; do not treat the row as recap-ready or render-ready until final source proof is recorded in the blank operator fields."
    return f"Optional audit: open the listed source row for {league} {matchup} only if it becomes a recap/render candidate."


def source_type_to_verify_for_research(row: Dict[str, Any], need: str) -> str:
    tier = clean(row.get("source_confirmation_tier"))
    stats_status = clean(row.get("stats_fact_status"))
    source_url = clean(row.get("source_url"))
    source_domain_value = clean(row.get("source_domain")) or source_domain(source_url)
    if need == "find_official_or_public_schedule_result_stat_source":
        return "official_or_reputable_public_schedule_result_stat_source_needed"
    if need == "find_box_score_or_named_stat_source":
        return "official_or_reputable_public_box_score_needed"
    if "stats_source_confirmed" in stats_status or "box_score" in stats_status:
        if "espn.com" in source_domain_value:
            return "public_scoreboard_box_score_operator_verify"
        return "public_box_score_or_stat_source_operator_verify"
    if "schedule_source_result_pending" in tier:
        return "public_schedule_source_result_pending_operator_monitor"
    return "public_scoreboard_or_official_source_operator_verify"


def source_proof_next_action_for_research(row: Dict[str, Any], need: str) -> str:
    prompt = game_source_research_prompt(row, need)
    proof_row = clean(row.get("proof_row_to_open"))
    intake = clean(row.get("manual_intake_path"))
    source_row = clean(row.get("source_row_to_open"))
    parts = [prompt]
    if proof_row:
        parts.append(f"Open proof row: {proof_row}.")
    if intake:
        parts.append(f"Record human confirmation only in: {intake}.")
    elif source_row:
        parts.append(f"Use source row for review context only: {source_row}.")
    parts.append("Leave operator fields blank until a human verifies the official/public evidence.")
    return " ".join(parts)


def game_source_research_worksheet_rows(next_action_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in next_action_rows:
        need = game_source_research_need(item)
        source_url = clean(item.get("source_url"))
        stats_status = clean(item.get("stats_fact_status"))
        box_source_url = source_url if ("stats_source_confirmed" in stats_status or "box_score" in stats_status) else ""
        prompt = game_source_research_prompt(item, need)
        rows.append(
            {
                "worksheet_rank": clean(item.get("action_rank")),
                "worksheet_import_cue": "import_or_edit_this_csv_row_only; keep_operator_fields_blank_until_human_verification",
                "event_uid": clean(item.get("event_uid")),
                "game_date": clean(item.get("game_date")),
                "league": clean(item.get("league")),
                "matchup": clean(item.get("matchup")),
                "game_status": clean(item.get("game_status")),
                "recap_candidate": clean(item.get("recap_candidate")),
                "research_need": need,
                "current_source_tier": clean(item.get("source_confirmation_tier")),
                "official_or_public_source_cue": clean(item.get("official_or_public_source_cue")),
                "second_source_check_cue": clean(item.get("second_source_check_cue")) or source_second_check_cue(item),
                "source_confidence": clean(item.get("source_confidence")),
                "source_freshness_status": clean(item.get("source_freshness_status")),
                "schedule_fact_status": clean(item.get("schedule_fact_status")),
                "result_fact_status": clean(item.get("result_fact_status")),
                "stats_fact_status": stats_status,
                "missing_confirmation": clean(item.get("missing_confirmation")) or "none",
                "scoreboard_source_url": source_url,
                "scoreboard_source_domain": clean(item.get("source_domain")),
                "box_score_or_stat_source_url": box_source_url,
                "operator_official_box_score_url": "",
                "source_type_to_verify": source_type_to_verify_for_research(item, need),
                "operator_stat_line_confirmation": "",
                "operator_manual_verification_status": "",
                "operator_evidence_note": "",
                "source_proof_next_action": source_proof_next_action_for_research(item, need),
                "proof_row_to_open": clean(item.get("proof_row_to_open")),
                "source_row_to_open": clean(item.get("source_row_to_open")),
                "manual_intake_path": clean(item.get("manual_intake_path")),
                "operator_research_prompt": prompt,
                "operator_found_official_url": "",
                "operator_found_public_scoreboard_url": "",
                "operator_found_box_score_url": "",
                "operator_source_tier_decision": "",
                "operator_confirmation_status": "",
                "operator_notes": "",
                "review_only": "Yes",
                "approval_state_change": "none",
                "source_enablement": "none_existing_local_artifacts_only",
                "publish_action": "none_artifact_only",
            }
        )
    return rows


def game_source_research_worksheet_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    blank_operator_fields = True
    for row in rows:
        counts[clean(row.get("research_need"))] += 1
        for field in [
            "operator_official_box_score_url",
            "operator_stat_line_confirmation",
            "operator_manual_verification_status",
            "operator_evidence_note",
            "operator_found_official_url",
            "operator_found_public_scoreboard_url",
            "operator_found_box_score_url",
            "operator_source_tier_decision",
            "operator_confirmation_status",
            "operator_notes",
        ]:
            if clean(row.get(field)):
                blank_operator_fields = False
    return {
        "version": "v1-review-only-game-source-research-worksheet",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "source_enablement": False,
        "operator_fields_prefilled": not blank_operator_fields,
        "rows": len(rows),
        "research_need_counts": dict(sorted(counts.items())),
    }


def game_source_research_worksheet_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Source Research Worksheet v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only worksheet for manual/ChatGPT Pro/Gemini source research.",
        "- No fetching, paid APIs, downloads, source enablement, approvals, publishing, or publish-ready movement.",
        "- Operator fields are intentionally blank; record human findings in the CSV before any downstream use.",
        "",
        "## Counts",
        "",
        f"- rows: `{summary.get('rows')}`",
        f"- operator_fields_prefilled: `{summary.get('operator_fields_prefilled')}`",
    ]
    for key, value in summary.get("research_need_counts", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Worksheet Rows", ""])
    if not rows:
        lines.append("No game source research worksheet rows were generated in this run.")
    for row in rows[:80]:
        lines.append(f"{row.get('worksheet_rank')}. **{row.get('matchup')}** | {row.get('game_date')} | {row.get('research_need')}")
        lines.append(f"   - import={row.get('worksheet_import_cue')} | tier={row.get('current_source_tier')} | cue={row.get('official_or_public_source_cue')} | second_check={row.get('second_source_check_cue')} | confidence={row.get('source_confidence') or 'n/a'}")
        lines.append(f"   - schedule={row.get('schedule_fact_status')} | result={row.get('result_fact_status')} | stats={row.get('stats_fact_status')}")
        lines.append(f"   - source={row.get('scoreboard_source_url') or 'missing'} | box_score={row.get('box_score_or_stat_source_url') or 'manual check'} | source_type={row.get('source_type_to_verify')}")
        lines.append(f"   - open={row.get('source_row_to_open')} | proof={row.get('proof_row_to_open') or 'not required'} | intake={row.get('manual_intake_path') or 'not required'}")
        lines.append(f"   - proof_next={row.get('source_proof_next_action')}")
        lines.append(f"   - prompt={row.get('operator_research_prompt')}")
    if len(rows) > 80:
        lines.append(f"Showing first 80 of {len(rows)} rows. Open `game_source_research_worksheet_v1.csv` for the full worksheet.")
    return "\n".join(lines) + "\n"


def game_source_confirmation_return_summary_rows(worksheet_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in worksheet_rows:
        official_url_present = bool(clean(item.get("operator_found_official_url")))
        public_scoreboard_present = bool(clean(item.get("operator_found_public_scoreboard_url")))
        box_score_present = bool(clean(item.get("operator_found_box_score_url")))
        confirmation_status_present = bool(clean(item.get("operator_confirmation_status")))
        notes_present = bool(clean(item.get("operator_notes")))
        missing_fields: List[str] = []
        if not official_url_present:
            missing_fields.append("operator_found_official_url")
        if not confirmation_status_present:
            missing_fields.append("operator_confirmation_status")
        if official_url_present and confirmation_status_present:
            manual_return_status = "operator_return_ready_for_review"
            manual_next_step = "Open the worksheet row and review the human-entered official/public URL plus confirmation status; do not approve, enable, render, or publish from this summary."
        else:
            manual_return_status = "operator_return_missing_required_fields"
            manual_next_step = "Open game_source_research_worksheet_v1.csv and fill only human-confirmed official/public URL plus confirmation status before any downstream source trust review."
        rows.append(
            {
                "summary_rank": clean(item.get("worksheet_rank")),
                "event_uid": clean(item.get("event_uid")),
                "game_date": clean(item.get("game_date")),
                "league": clean(item.get("league")),
                "matchup": clean(item.get("matchup")),
                "research_need": clean(item.get("research_need")),
                "current_source_tier": clean(item.get("current_source_tier")),
                "scoreboard_source_url": clean(item.get("scoreboard_source_url")),
                "operator_found_official_url_present": "Yes" if official_url_present else "No",
                "operator_found_public_scoreboard_url_present": "Yes" if public_scoreboard_present else "No",
                "operator_found_box_score_url_present": "Yes" if box_score_present else "No",
                "operator_confirmation_status_present": "Yes" if confirmation_status_present else "No",
                "operator_notes_present": "Yes" if notes_present else "No",
                "manual_return_status": manual_return_status,
                "missing_return_fields": "; ".join(missing_fields) if missing_fields else "none",
                "manual_next_step": manual_next_step,
                "source_row_to_open": clean(item.get("source_row_to_open")),
                "proof_row_to_open": clean(item.get("proof_row_to_open")),
                "manual_intake_path": clean(item.get("manual_intake_path")),
                "review_only": "Yes",
                "approval_state_change": "none",
                "source_enablement": "none_existing_local_artifacts_only",
                "publish_action": "none_artifact_only",
            }
        )
    rows.sort(key=lambda row: (row.get("manual_return_status") != "operator_return_missing_required_fields", row.get("summary_rank", ""), row.get("game_date", ""), row.get("matchup", "")))
    for index, row in enumerate(rows, start=1):
        row["summary_rank"] = str(index)
    return rows


def game_source_confirmation_return_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_counts: Dict[str, int] = defaultdict(int)
    need_counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        status_counts[clean(row.get("manual_return_status"))] += 1
        need_counts[clean(row.get("research_need"))] += 1
    return {
        "version": "v1-review-only-game-source-confirmation-return-summary",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "source_enablement": False,
        "rows": len(rows),
        "operator_return_ready_for_review": status_counts.get("operator_return_ready_for_review", 0),
        "operator_return_missing_required_fields": status_counts.get("operator_return_missing_required_fields", 0),
        "missing_official_url": sum(1 for row in rows if row.get("operator_found_official_url_present") != "Yes"),
        "missing_confirmation_status": sum(1 for row in rows if row.get("operator_confirmation_status_present") != "Yes"),
        "rows_with_operator_notes": sum(1 for row in rows if row.get("operator_notes_present") == "Yes"),
        "status_counts": dict(sorted(status_counts.items())),
        "research_need_counts": dict(sorted(need_counts.items())),
    }


def game_source_confirmation_return_summary_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Game Source Confirmation Return Summary v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only summary of manual worksheet return fields.",
        "- No fetching, paid APIs, downloads, source enablement, approvals, publishing, or publish-ready movement.",
        "- A ready-for-review row is not source approval; it only means required manual return fields are present.",
        "",
        "## Counts",
        "",
    ]
    for key in [
        "rows",
        "operator_return_ready_for_review",
        "operator_return_missing_required_fields",
        "missing_official_url",
        "missing_confirmation_status",
        "rows_with_operator_notes",
    ]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Missing Return Fields", ""])
    missing = [row for row in rows if row.get("manual_return_status") == "operator_return_missing_required_fields"]
    if not missing:
        lines.append("No rows are missing the required manual return fields in this worksheet snapshot.")
    for row in missing[:80]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('game_date')} | {row.get('research_need')}")
        lines.append(f"  - missing={row.get('missing_return_fields')}")
        lines.append(f"  - open={row.get('source_row_to_open') or 'game_source_research_worksheet_v1.csv'}")
        lines.append(f"  - next={row.get('manual_next_step')}")
    if len(missing) > 80:
        lines.append(f"Showing first 80 of {len(missing)} missing rows. Open `game_source_confirmation_return_summary_v1.csv` for the full summary.")
    lines.extend(["", "## Ready For Operator Review", ""])
    ready = [row for row in rows if row.get("manual_return_status") == "operator_return_ready_for_review"]
    if not ready:
        lines.append("No rows currently have both required manual return fields present.")
    for row in ready[:80]:
        lines.append(f"- **{row.get('matchup')}** | status={row.get('manual_return_status')} | source_row={row.get('source_row_to_open')}")
    return "\n".join(lines) + "\n"


def parse_top_performer_line(line: str) -> Dict[str, str]:
    text = clean(line)
    match = re.match(r"^(?P<player>.+?)\s+\((?P<team>.+?)\):\s+(?P<stats>.+)$", text)
    if not match:
        return {"named_player": "", "player_team": "", "stat_line": text}
    return {
        "named_player": clean(match.group("player")),
        "player_team": clean(match.group("team")),
        "stat_line": clean(match.group("stats")),
    }


def final_score_stat_proof_rows(stats_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in stats_rows:
        if clean(item.get("status")) != "final" and clean(item.get("recap_candidate")) != "Yes":
            continue
        event_uid = clean(item.get("event_uid"))
        matchup = clean(item.get("matchup"))
        source_url = clean(item.get("confirmation_source_url")) or clean(item.get("score_source_url"))
        source_dom = clean(item.get("confirmation_source_domain")) or source_domain(source_url)
        stats_status = clean(item.get("stats_evidence_status"))
        score_source_status = "score_source_backed_operator_verify" if source_url else "score_source_missing_manual_verify"
        base_next = f"Open stats_evidence_gap_board_v1.csv event_uid={event_uid}; then open game_fact_confirmation_status_v1.csv event_uid={event_uid}"
        rows.append(
            {
                "proof_id": stable_id(event_uid, "score", clean(item.get("final_score"))),
                "event_uid": event_uid,
                "game_date": clean(item.get("game_date")),
                "league": clean(item.get("league")),
                "matchup": matchup,
                "recap_candidate": clean(item.get("recap_candidate")),
                "fact_type": "final_score",
                "fact_label": "Final score",
                "fact_value": clean(item.get("final_score")),
                "named_player": "",
                "player_team": "",
                "stat_line": "",
                "proof_status": score_source_status,
                "manual_box_score_confirmation_needed": "No" if source_url else "Yes",
                "source_confidence": clean(item.get("source_confidence")),
                "source_url": source_url,
                "source_domain": source_dom,
                "evidence_artifact_row": f"stats_evidence_gap_board_v1.csv event_uid={event_uid}",
                "exact_next_file_or_intake": base_next + "; then verify the final score source URL before writing copy.",
                "operator_note_path": f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={stable_id(event_uid, 'score', clean(item.get('final_score')))}",
                "limitations": "Review-only score proof derived from current Results Desk artifacts; it does not approve stories, stats, renders, sources, or publishing.",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
        performers = [clean(part) for part in clean(item.get("top_performers")).split("|") if clean(part)]
        if not performers:
            rows.append(
                {
                    "proof_id": stable_id(event_uid, "missing_stat_line"),
                    "event_uid": event_uid,
                    "game_date": clean(item.get("game_date")),
                    "league": clean(item.get("league")),
                    "matchup": matchup,
                    "recap_candidate": clean(item.get("recap_candidate")),
                    "fact_type": "named_player_stat_line",
                    "fact_label": "Missing named player stat line",
                    "fact_value": "",
                    "named_player": "",
                    "player_team": "",
                    "stat_line": "",
                    "proof_status": "named_stat_line_missing_manual_box_score_confirmation_required",
                    "manual_box_score_confirmation_needed": "Yes",
                    "source_confidence": clean(item.get("source_confidence")),
                    "source_url": source_url,
                    "source_domain": source_dom,
                    "evidence_artifact_row": f"stats_confirmation_intake_v1.csv event_uid={event_uid}",
                    "exact_next_file_or_intake": f"{base_next}; then open stats_confirmation_intake_v1.csv and record whether a named player stat line is available.",
                    "operator_note_path": f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={stable_id(event_uid, 'missing_stat_line')}",
                    "limitations": "Review-only stat proof gap; do not invent or publish named player stats without operator confirmation.",
                    "review_only": "Yes",
                    "approval_state_change": "none",
                    "publish_action": "none_artifact_only",
                }
            )
            continue
        for index, performer in enumerate(performers, start=1):
            parsed = parse_top_performer_line(performer)
            parsed_ok = bool(parsed.get("named_player") and parsed.get("player_team") and parsed.get("stat_line"))
            confirmed = stats_status == "confirmed_free_public_box_score" and parsed_ok
            proof_status = "named_stat_line_source_backed_operator_verify" if confirmed else "named_stat_line_manual_box_score_confirmation_required"
            manual_needed = "No" if confirmed else "Yes"
            rows.append(
                {
                    "proof_id": stable_id(event_uid, "stat", str(index), performer),
                    "event_uid": event_uid,
                    "game_date": clean(item.get("game_date")),
                    "league": clean(item.get("league")),
                    "matchup": matchup,
                    "recap_candidate": clean(item.get("recap_candidate")),
                    "fact_type": "named_player_stat_line",
                    "fact_label": f"Named player stat line {index}",
                    "fact_value": performer,
                    "named_player": parsed.get("named_player", ""),
                    "player_team": parsed.get("player_team", ""),
                    "stat_line": parsed.get("stat_line", performer),
                    "proof_status": proof_status,
                    "manual_box_score_confirmation_needed": manual_needed,
                    "source_confidence": clean(item.get("source_confidence")),
                    "source_url": source_url,
                    "source_domain": source_dom,
                    "evidence_artifact_row": f"stats_evidence_gap_board_v1.csv event_uid={event_uid}; top_performers item {index}",
                    "exact_next_file_or_intake": base_next + "; then verify this named player stat line against the source URL before rendering or writing copy.",
                    "operator_note_path": f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={stable_id(event_uid, 'stat', str(index), performer)}",
                    "limitations": "Review-only stat proof derived from current box-score context; operator must verify the source before editorial or render use.",
                    "review_only": "Yes",
                    "approval_state_change": "none",
                    "publish_action": "none_artifact_only",
                }
            )
    rows.sort(key=lambda row: (row.get("manual_box_score_confirmation_needed") != "Yes", row.get("game_date", ""), row.get("matchup", ""), row.get("fact_type", ""), row.get("fact_label", "")))
    return rows


def final_score_stat_proof_confirmation_rows(proof_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for proof in proof_rows:
        fact_type = clean(proof.get("fact_type"))
        task = "Verify final score against the source URL and note any discrepancy."
        if fact_type == "named_player_stat_line":
            task = "Verify named player, team, and stat line against the box-score source URL."
        if clean(proof.get("manual_box_score_confirmation_needed")) == "Yes":
            task += " Manual confirmation is required before the stat can be used."
        rows.append(
            {
                "proof_id": clean(proof.get("proof_id")),
                "event_uid": clean(proof.get("event_uid")),
                "game_date": clean(proof.get("game_date")),
                "matchup": clean(proof.get("matchup")),
                "fact_type": fact_type,
                "fact_value": clean(proof.get("fact_value")),
                "proof_status": clean(proof.get("proof_status")),
                "source_url": clean(proof.get("source_url")),
                "evidence_artifact_row": clean(proof.get("evidence_artifact_row")),
                "operator_review_task": task,
                "operator_checked_source_url": "",
                "operator_confirmation_status": "",
                "operator_notes": "",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
    return rows


def final_score_stat_proof_review_order_rows(proof_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def phase(proof: Dict[str, Any]) -> str:
        if clean(proof.get("manual_box_score_confirmation_needed")) == "Yes":
            return "1_manual_box_score_gap"
        if clean(proof.get("fact_type")) == "final_score":
            return "2_final_score_source_check"
        return "3_named_player_stat_source_check"

    ordered = sorted(
        proof_rows,
        key=lambda proof: (
            clean(proof.get("manual_box_score_confirmation_needed")) != "Yes",
            proof.get("game_date", ""),
            proof.get("matchup", ""),
            clean(proof.get("fact_type")) != "final_score",
            proof.get("fact_label", ""),
        ),
    )
    rows: List[Dict[str, Any]] = []
    for index, proof in enumerate(ordered, start=1):
        manual_needed = clean(proof.get("manual_box_score_confirmation_needed"))
        fact_type = clean(proof.get("fact_type"))
        source_url = clean(proof.get("source_url"))
        source_check_status = "source_url_present_operator_verify" if source_url else "source_url_missing_human_source_required"
        source_confirmation_cue = "free_public_source_url_present_operator_verify" if source_url else "free_public_source_needed_manual_check"
        if fact_type == "named_player_stat_line" and source_url:
            source_confirmation_cue = "free_public_box_score_stat_source_present_operator_verify"
        if fact_type == "final_score" and source_url:
            source_confirmation_cue = "free_public_final_score_source_present_operator_verify"
        if manual_needed == "Yes" and fact_type == "named_player_stat_line":
            source_confirmation_cue = "free_public_box_score_stat_source_needed_manual_check"
        next_step = "Open the source URL, compare the final score or stat text to the proof row, then record the check in the intake row."
        if manual_needed == "Yes":
            next_step = "Open the evidence row and intake row, find a free/public box-score source manually, then record the check without approving or publishing."
        render_cue = "Score check first, then named player stat checks before render/copy use."
        if fact_type == "named_player_stat_line":
            render_cue = "Confirm named player, team, and stat line before any render/copy use."
        sequence_cue = "confirm_final_score_source_before_named_stat_rows_for_this_event" if fact_type == "final_score" else "confirm_matching_final_score_row_first_then_this_named_stat_row"
        rows.append(
            {
                "review_order": str(index),
                "review_phase": phase(proof),
                "score_stat_review_sequence_cue": sequence_cue,
                "event_uid": clean(proof.get("event_uid")),
                "game_date": clean(proof.get("game_date")),
                "matchup": clean(proof.get("matchup")),
                "fact_type": fact_type,
                "fact_label": clean(proof.get("fact_label")),
                "fact_value": clean(proof.get("fact_value")),
                "named_player": clean(proof.get("named_player")),
                "player_team": clean(proof.get("player_team")),
                "stat_line": clean(proof.get("stat_line")),
                "proof_status": clean(proof.get("proof_status")),
                "source_check_status": source_check_status,
                "source_confirmation_cue": source_confirmation_cue,
                "manual_box_score_confirmation_needed": manual_needed,
                "source_url": source_url,
                "source_domain": clean(proof.get("source_domain")),
                "proof_row_to_open": f"final_score_stat_proof_v1.csv proof_id={clean(proof.get('proof_id'))}",
                "evidence_artifact_row": clean(proof.get("evidence_artifact_row")),
                "intake_row_to_record": f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={clean(proof.get('proof_id'))}",
                "story_proof_card_row_to_open": f"story_proof_card_v1.csv event_id={clean(proof.get('event_uid'))}; proof_id={clean(proof.get('proof_id'))}",
                "operator_next_step": next_step,
                "operator_decision_fields": "operator_checked_source_url, operator_confirmation_status, operator_notes",
                "render_review_cue": render_cue,
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )
    return rows


def final_score_stat_proof_review_walkthrough_md(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Final Score Stat Proof Review Walkthrough v1",
        "",
        f"Generated: `{now_iso()}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only operator walkthrough.",
        "- No paid APIs, credentials, source enablement, approval-state changes, publishing, or publish-ready movement.",
        "- Human confirmation must be recorded in `final_score_stat_proof_confirmation_intake_v1.csv`; this file does not approve anything.",
        "",
        "## How To Use",
        "",
        "1. Open the first row in `final_score_stat_proof_review_order_v1.csv`.",
        "2. Open the `proof_row_to_open` and `evidence_artifact_row` values.",
        "3. Open the source URL when present, or find a free/public manual source when missing.",
        "4. Record only the human check fields in `intake_row_to_record`.",
        "",
        "## Review Order",
        "",
    ]
    if not rows:
        lines.append("No final-score/stat proof rows were available in this run.")
    for row in rows[:80]:
        lines.append(f"{row.get('review_order')}. **{row.get('matchup')}** | {row.get('fact_label')} | {row.get('proof_status')}")
        lines.append(f"   - fact={row.get('fact_value') or 'missing'}")
        lines.append(f"   - source={row.get('source_url') or 'missing'}")
        lines.append(f"   - sequence={row.get('score_stat_review_sequence_cue')}")
        lines.append(f"   - proof={row.get('proof_row_to_open')}")
        lines.append(f"   - evidence={row.get('evidence_artifact_row')}")
        lines.append(f"   - record={row.get('intake_row_to_record')}")
        lines.append(f"   - next={row.get('operator_next_step')}")
    if len(rows) > 80:
        lines.append(f"Showing first 80 of {len(rows)} rows. Open `final_score_stat_proof_review_order_v1.csv` for the full review order.")
    return "\n".join(lines) + "\n"


def slug_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")


def points_from_stat_line(value: Any) -> int:
    match = re.search(r"\bPTS\s+(\d+)\b", clean(value), flags=re.IGNORECASE)
    return int(match.group(1)) if match else 0


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"true", "yes", "1", "approved", "present"}


def athlete_render_candidate_rows(
    proof_rows: List[Dict[str, Any]],
    review_order_rows: List[Dict[str, Any]],
    photo_catalog_rows: List[Dict[str, str]],
    check_paths: bool = True,
) -> List[Dict[str, Any]]:
    order_by_proof: Dict[str, Dict[str, Any]] = {}
    for row in review_order_rows:
        match = re.search(r"proof_id=([A-Za-z0-9_-]+)", clean(row.get("proof_row_to_open")))
        if match:
            order_by_proof[match.group(1)] = row
    catalog_by_name_team: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in photo_catalog_rows:
        if clean(row.get("asset_kind")) != "headshot":
            continue
        catalog_by_name_team[(slug_text(row.get("athlete_name")), slug_text(row.get("team_id")))] = row
    rows: List[Dict[str, Any]] = []
    for proof in proof_rows:
        if clean(proof.get("fact_type")) != "named_player_stat_line":
            continue
        proof_id = clean(proof.get("proof_id"))
        player = clean(proof.get("named_player"))
        if not player:
            continue
        player_team = clean(proof.get("player_team"))
        catalog = catalog_by_name_team.get((slug_text(player), slug_text(player_team))) or {}
        local_path = clean(catalog.get("local_asset_path"))
        marker_path = clean(catalog.get("approved_marker_path"))
        catalog_file_exists = truthy(catalog.get("file_exists"))
        catalog_marker_exists = truthy(catalog.get("approved_marker_exists"))
        actual_file_exists = Path(local_path).exists() if check_paths and local_path else catalog_file_exists
        actual_marker_exists = Path(marker_path).exists() if check_paths and marker_path else catalog_marker_exists
        proof_ready = clean(proof.get("proof_status")) == "named_stat_line_source_backed_operator_verify"
        asset_ready = bool(local_path and marker_path and catalog_file_exists and catalog_marker_exists and actual_file_exists and actual_marker_exists)
        blockers: List[str] = []
        if not proof_ready:
            blockers.append("verified_named_player_stat_proof_missing")
        if not local_path:
            blockers.append("approved_local_athlete_image_path_missing")
        if local_path and not actual_file_exists:
            blockers.append("local_athlete_image_file_missing")
        if marker_path and not actual_marker_exists:
            blockers.append("approved_marker_missing")
        if not marker_path:
            blockers.append("approved_marker_path_missing")
        candidate_status = (
            "athlete_render_candidate_ready_for_manual_review"
            if proof_ready and asset_ready
            else "athlete_render_candidate_blocked_manual_review_required"
        )
        order = order_by_proof.get(proof_id, {})
        stat_line = clean(proof.get("stat_line"))
        title = f"{player} leads {player_team}" if player and player_team else clean(proof.get("matchup"))
        event_uid = clean(proof.get("event_uid"))
        candidate_id = stable_id(proof_id, player, local_path)
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_rank": "",
                "candidate_status": candidate_status,
                "rank_score": points_from_stat_line(stat_line),
                "event_uid": event_uid,
                "game_date": clean(proof.get("game_date")),
                "matchup": clean(proof.get("matchup")),
                "athlete_name": player,
                "player_team": player_team,
                "stat_line": stat_line,
                "fact_value": clean(proof.get("fact_value")),
                "proof_status": clean(proof.get("proof_status")),
                "source_url": clean(proof.get("source_url")),
                "source_domain": clean(proof.get("source_domain")),
                "proof_row_to_open": f"final_score_stat_proof_v1.csv proof_id={proof_id}",
                "review_order_row_to_open": clean(order.get("review_order")) and f"final_score_stat_proof_review_order_v1.csv review_order={clean(order.get('review_order'))}; proof_id={proof_id}",
                "intake_row_to_record": f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={proof_id}",
                "asset_status": "approved_local_headshot_found" if asset_ready else "athlete_asset_manual_review_required",
                "athlete_id": clean(catalog.get("athlete_id")),
                "asset_kind": clean(catalog.get("asset_kind")),
                "local_athlete_image_path": local_path,
                "approved_marker_path": marker_path,
                "image_file_exists": "Yes" if actual_file_exists else "No",
                "approved_marker_exists": "Yes" if actual_marker_exists else "No",
                "asset_source_url": clean(catalog.get("source_url")),
                "asset_catalog_row": clean(catalog.get("athlete_id")) and f"data/asset_registry/wnba/athlete_photo_catalog.csv athlete_id={clean(catalog.get('athlete_id'))}; asset_kind=headshot",
                "render_candidate_title": title,
                "render_candidate_dek": f"{stat_line} in {clean(proof.get('matchup'))}" if stat_line else clean(proof.get("matchup")),
                "exact_renderer_handoff_fields": f"title={title}; dek={stat_line}; athlete_image={local_path}; source_url={clean(proof.get('source_url'))}; proof_id={proof_id}",
                "story_proof_card_row_to_open": f"story_proof_card_v1.csv event_id={event_uid}; athlete_render_candidate_id={candidate_id}",
                "handoff_action": "Manual athlete-led render candidate only; verify proof source and local asset row before using this image path.",
                "missing_blockers": ";".join(blockers) if blockers else "none_manual_source_check_still_required",
                "operator_next_step": "Open proof row, source URL, review-order row, and asset catalog row; then record the source check in the intake row before any manual render use.",
                "operator_checked_source_url": "",
                "operator_asset_review_notes": "",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
                "auto_approval": "No",
                "auto_publish": "No",
                "asset_downloads": "No",
                "move_files": "No",
                "publish_ready": "No",
            }
        )
    rows.sort(key=lambda row: (row.get("candidate_status") != "athlete_render_candidate_ready_for_manual_review", -int(row.get("rank_score") or 0), row.get("game_date", ""), row.get("matchup", ""), row.get("athlete_name", "")))
    for index, row in enumerate(rows, 1):
        row["candidate_rank"] = str(index)
    return rows


def athlete_render_candidate_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    ready = [row for row in rows if row.get("candidate_status") == "athlete_render_candidate_ready_for_manual_review"]
    return {
        "version": "v1-review-only-athlete-render-candidates",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "ready_for_manual_review": len(ready),
        "blocked": len(rows) - len(ready),
        "top_candidate_id": ready[0].get("candidate_id") if ready else "",
        "top_candidate_athlete": ready[0].get("athlete_name") if ready else "",
        "top_candidate_asset_path": ready[0].get("local_athlete_image_path") if ready else "",
    }


def athlete_render_candidate_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Athlete Render Candidate Board v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only athlete render candidate packet.",
        "- No paid APIs, downloads, source enablement, asset approvals, marker writes, publishing, or publish-ready movement.",
        "- Candidate rows do not approve stats, sources, stories, renders, or athlete assets.",
        "- Human source checks stay blank until an operator records them in `final_score_stat_proof_confirmation_intake_v1.csv`.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "ready_for_manual_review", "blocked", "top_candidate_athlete", "top_candidate_asset_path"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Ready Athlete-Led Candidates", ""])
    ready = [row for row in rows if row.get("candidate_status") == "athlete_render_candidate_ready_for_manual_review"]
    if not ready:
        lines.append("No athlete-led render candidates have both named stat proof and an approved local athlete image in this run.")
    for row in ready[:40]:
        lines.append(f"- **{row.get('candidate_rank')}. {row.get('athlete_name')}** | {row.get('player_team')} | {row.get('stat_line')}")
        lines.append(f"  - game={row.get('matchup')}")
        lines.append(f"  - image=`{row.get('local_athlete_image_path')}`")
        lines.append(f"  - review_marker_present={row.get('approved_marker_exists')}")
        lines.append(f"  - proof={row.get('proof_row_to_open')}")
        lines.append(f"  - review={row.get('review_order_row_to_open')}")
        lines.append(f"  - record={row.get('intake_row_to_record')}")
    lines.extend(["", "## Blocked Rows", ""])
    blocked = [row for row in rows if row.get("candidate_status") != "athlete_render_candidate_ready_for_manual_review"]
    if not blocked:
        lines.append("No blocker rows in this run; all named-player stat proof rows matched approved local headshots.")
    for row in blocked[:40]:
        lines.append(f"- **{row.get('athlete_name') or row.get('matchup')}** | blockers={row.get('missing_blockers')}")
        lines.append(f"  - proof={row.get('proof_row_to_open')}")
        lines.append(f"  - asset_catalog={row.get('asset_catalog_row') or 'missing'}")
    return "\n".join(lines) + "\n"


def proof_id_from_reference(value: Any) -> str:
    match = re.search(r"proof_id=([A-Za-z0-9_-]+)", clean(value))
    return match.group(1) if match else ""


def review_order_ref(row: Dict[str, Any]) -> str:
    order = clean(row.get("review_order"))
    proof_id = proof_id_from_reference(row.get("proof_row_to_open"))
    if not order or not proof_id:
        return ""
    return f"final_score_stat_proof_review_order_v1.csv review_order={order}; proof_id={proof_id}"


def enrich_game_fact_confirmation_status_rows(
    rows: List[Dict[str, Any]],
    review_order_rows: List[Dict[str, Any]],
    story_proof_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    score_review_by_event: Dict[str, Dict[str, Any]] = {}
    named_review_by_event: Dict[str, Dict[str, Any]] = {}
    for row in review_order_rows:
        event_uid = clean(row.get("event_uid"))
        if not event_uid:
            continue
        if clean(row.get("fact_type")) == "final_score" and event_uid not in score_review_by_event:
            score_review_by_event[event_uid] = row
        if clean(row.get("fact_type")) == "named_player_stat_line" and event_uid not in named_review_by_event:
            named_review_by_event[event_uid] = row

    story_by_event: Dict[str, Dict[str, Any]] = {}
    for row in story_proof_rows:
        event_uid = clean(row.get("event_id"))
        if event_uid and event_uid not in story_by_event:
            story_by_event[event_uid] = row

    enriched: List[Dict[str, Any]] = []
    for row in rows:
        event_uid = clean(row.get("event_uid"))
        story = story_by_event.get(event_uid, {})
        score_review = score_review_by_event.get(event_uid, {})
        named_review = named_review_by_event.get(event_uid, {})
        story_ref = ""
        if story:
            story_ref = f"story_proof_card_v1.csv event_id={event_uid}; candidate_id={clean(story.get('candidate_id'))}"
        score_review_ref = clean(story.get("final_score_review_order_row")) or review_order_ref(score_review)
        named_review_ref = clean(story.get("named_stat_review_order_row")) or review_order_ref(named_review)
        source_cue = clean(story.get("source_confirmation_cue")) or clean(named_review.get("source_confirmation_cue")) or clean(score_review.get("source_confirmation_cue"))
        if not source_cue:
            if clean(row.get("game_status")) == "scheduled":
                source_cue = "free_public_schedule_source_present_result_pending"
            elif clean(row.get("missing_confirmation")) != "none":
                source_cue = "manual_source_confirmation_required"
            else:
                source_cue = "free_public_source_present_operator_verify"
        readiness = clean(story.get("renderability_state"))
        if not readiness:
            if clean(row.get("recap_candidate")) == "Yes":
                readiness = "recap_candidate_needs_story_proof_card"
            elif clean(row.get("game_status")) == "scheduled":
                readiness = "result_pending_not_render_ready"
            else:
                readiness = "not_recap_or_render_candidate"
        intake = clean(story.get("manual_intake_path")) or clean(named_review.get("intake_row_to_record")) or clean(score_review.get("intake_row_to_record"))
        next_step = clean(row.get("exact_next_file_or_intake"))
        proof_steps = [value for value in [story_ref, score_review_ref, named_review_ref, intake] if value]
        if proof_steps:
            next_step = next_step.rstrip(".") + "; then open " + "; then open ".join(proof_steps) + "."
        enriched.append(
            {
                **row,
                "story_proof_card_row_to_open": story_ref,
                "final_score_review_order_row": score_review_ref,
                "named_stat_review_order_row": named_review_ref,
                "proof_manual_intake_path": intake,
                "source_confirmation_cue": source_cue,
                "recap_render_readiness": readiness,
                "exact_next_file_or_intake": next_step,
            }
        )
    return enriched


def enrich_game_intelligence_rows_with_proof_cues(
    rows: List[Dict[str, Any]],
    fact_status_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    fact_by_event = {clean(row.get("event_uid")): row for row in fact_status_rows if clean(row.get("event_uid"))}
    enriched: List[Dict[str, Any]] = []
    for row in rows:
        row_id = clean(row.get("row_id"))
        fact = fact_by_event.get(row_id, {})
        proof_order = clean(fact.get("named_stat_review_order_row")) or clean(fact.get("final_score_review_order_row"))
        next_step = clean(fact.get("exact_next_file_or_intake"))
        if not next_step:
            next_step = f"Open game_fact_confirmation_status_v1.csv event_uid={row_id}" if row_id else "Open game_fact_confirmation_status_v1.csv for this row"
        enriched.append(
            {
                **row,
                "game_fact_status_row_to_open": f"game_fact_confirmation_status_v1.csv event_uid={row_id}" if row_id else "",
                "story_proof_card_row_to_open": clean(fact.get("story_proof_card_row_to_open")),
                "proof_review_order_row_to_open": proof_order,
                "proof_manual_intake_path": clean(fact.get("proof_manual_intake_path")),
                "source_confirmation_cue": clean(fact.get("source_confirmation_cue")) or ("manual_source_confirmation_required" if clean(row.get("missing_evidence")) != "none" else "free_public_source_present_operator_verify"),
                "recap_render_readiness": clean(fact.get("recap_render_readiness")) or ("result_pending_not_render_ready" if clean(row.get("status")) == "scheduled" else "not_recap_or_render_candidate"),
                "operator_next_review_step": next_step,
            }
        )
    return enriched


def story_proof_card_rows(
    fact_rows: List[Dict[str, Any]],
    stat_proof_rows: List[Dict[str, Any]],
    review_order_rows: List[Dict[str, Any]],
    athlete_candidate_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    score_by_event: Dict[str, Dict[str, Any]] = {}
    named_proofs_by_event: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in stat_proof_rows:
        event_uid = clean(row.get("event_uid"))
        if clean(row.get("fact_type")) == "final_score":
            score_by_event[event_uid] = row
        elif clean(row.get("fact_type")) == "named_player_stat_line" and clean(row.get("named_player")):
            named_proofs_by_event[event_uid].append(row)
    order_by_proof: Dict[str, Dict[str, Any]] = {}
    for row in review_order_rows:
        proof_id = proof_id_from_reference(row.get("proof_row_to_open"))
        if proof_id:
            order_by_proof[proof_id] = row
    athlete_by_event: Dict[str, Dict[str, Any]] = {}
    for row in athlete_candidate_rows:
        event_uid = clean(row.get("event_uid"))
        if event_uid and event_uid not in athlete_by_event:
            athlete_by_event[event_uid] = row
    cards: List[Dict[str, Any]] = []
    for fact in fact_rows:
        event_uid = clean(fact.get("event_uid"))
        result_status = clean(fact.get("result_fact_status"))
        stats_status = clean(fact.get("stats_fact_status"))
        if "final_score" not in result_status and "stats_source_confirmed" not in stats_status:
            continue
        score = score_by_event.get(event_uid, {})
        athlete = athlete_by_event.get(event_uid, {})
        athlete_status = clean(athlete.get("candidate_status"))
        named_proofs = named_proofs_by_event.get(event_uid, [])
        selected_named = {}
        if clean(athlete.get("proof_row_to_open")):
            athlete_proof_id = proof_id_from_reference(athlete.get("proof_row_to_open"))
            selected_named = next((row for row in named_proofs if clean(row.get("proof_id")) == athlete_proof_id), {})
        if not selected_named and named_proofs:
            selected_named = named_proofs[0]
        selected_proof_id = clean(selected_named.get("proof_id")) or proof_id_from_reference(athlete.get("proof_row_to_open"))
        review_order = order_by_proof.get(selected_proof_id, {})
        score_proof_id = clean(score.get("proof_id"))
        score_review_order = order_by_proof.get(score_proof_id, {})
        source_url = clean(fact.get("source_url")) or clean(score.get("source_url")) or clean(athlete.get("source_url"))
        cross_check = clean(fact.get("stats_source_url"))
        named_stat = clean(athlete.get("stat_line")) or clean(selected_named.get("stat_line")) or clean(selected_named.get("fact_value"))
        athlete_ready = athlete_status == "athlete_render_candidate_ready_for_manual_review"
        score_ready = clean(score.get("proof_status")) == "score_source_backed_operator_verify"
        named_ready = clean(selected_named.get("proof_status")) == "named_stat_line_source_backed_operator_verify" or athlete_ready
        proof_status = "proof_card_ready_for_manual_review" if score_ready and named_ready else "proof_card_needs_human_confirmation"
        copy_unlock = "score_and_named_stat_copy_review_ready" if score_ready and named_ready else "score_only_or_manual_copy_review_required"
        asset_unlock = "approved_local_athlete_photo_available" if athlete_ready else "athlete_asset_missing_or_manual_review_required"
        renderability = "athlete_led_manual_render_candidate" if athlete_ready and named_ready else "not_athlete_renderable_until_blockers_clear"
        blockers: List[str] = []
        if not score_ready:
            blockers.append("final_score_proof_missing_or_unverified")
        if not named_ready:
            blockers.append("named_stat_proof_missing_or_unverified")
        if not athlete_ready:
            blockers.append(clean(athlete.get("missing_blockers")) or "athlete_render_candidate_missing")
        score_review_order_ref = clean(score_review_order.get("review_order")) and f"final_score_stat_proof_review_order_v1.csv review_order={clean(score_review_order.get('review_order'))}; proof_id={score_proof_id}"
        named_review_order_ref = clean(athlete.get("review_order_row_to_open")) or (clean(review_order.get("review_order")) and f"final_score_stat_proof_review_order_v1.csv review_order={clean(review_order.get('review_order'))}; proof_id={selected_proof_id}")
        source_confirmation_cue = clean(review_order.get("source_confirmation_cue")) or clean(score_review_order.get("source_confirmation_cue"))
        if not source_confirmation_cue:
            source_confirmation_cue = "free_public_source_url_present_operator_verify" if source_url else "free_public_source_needed_manual_check"
        action = "Open story_proof_card_v1.md, verify the official source URL, record the check in the manual intake row, then hand the athlete fields to the renderer lane."
        if blockers:
            action = "Clear blocker(s): {blockers}; then record source confirmation in the manual intake row.".format(blockers="; ".join(blockers))
        manual_intake = clean(athlete.get("intake_row_to_record")) or (score_proof_id and f"final_score_stat_proof_confirmation_intake_v1.csv proof_id={score_proof_id}") or "final_score_stat_proof_confirmation_intake_v1.csv"
        claim_parts = [clean(fact.get("matchup")), clean(score.get("fact_value"))]
        if named_stat:
            claim_parts.append(named_stat)
        claim = " | ".join(part for part in claim_parts if part)
        cards.append(
            {
                "candidate_id": stable_id(event_uid, selected_proof_id or score_proof_id, athlete.get("candidate_id")),
                "candidate_rank": "",
                "claim": claim,
                "event_id": event_uid,
                "game_date": clean(fact.get("game_date")),
                "matchup": clean(fact.get("matchup")),
                "official_source_url": source_url,
                "cross_check_source_url": cross_check if cross_check != source_url else "",
                "wire_source_url_if_present": "",
                "source_domain": clean(fact.get("source_domain")) or source_domain(source_url),
                "proof_status": proof_status,
                "schedule_result_status": f"{clean(fact.get('schedule_fact_status'))}; {clean(fact.get('result_fact_status'))}",
                "named_stat_proof_status": clean(selected_named.get("proof_status")) or ("athlete_candidate_stat_proof_available" if athlete_ready else "named_stat_proof_missing"),
                "named_stat_proof": named_stat,
                "named_stat_proof_row": clean(athlete.get("proof_row_to_open")) or (selected_proof_id and f"final_score_stat_proof_v1.csv proof_id={selected_proof_id}"),
                "athlete_name": clean(athlete.get("athlete_name")) or clean(selected_named.get("named_player")),
                "athlete_team": clean(athlete.get("player_team")) or clean(selected_named.get("player_team")),
                "athlete_photo_path": clean(athlete.get("local_athlete_image_path")),
                "athlete_photo_marker_path": clean(athlete.get("approved_marker_path")),
                "copy_unlock_level": copy_unlock,
                "asset_unlock_state": asset_unlock,
                "renderability_state": renderability,
                "athlete_render_candidate_id": clean(athlete.get("candidate_id")),
                "athlete_render_handoff_fields": clean(athlete.get("exact_renderer_handoff_fields")),
                "game_fact_row": f"game_fact_confirmation_status_v1.csv event_uid={event_uid}",
                "final_score_proof_row": score_proof_id and f"final_score_stat_proof_v1.csv proof_id={score_proof_id}",
                "final_score_review_order_row": score_review_order_ref,
                "proof_review_order_row": named_review_order_ref,
                "named_stat_review_order_row": named_review_order_ref,
                "manual_intake_path": manual_intake,
                "source_confirmation_cue": source_confirmation_cue,
                "smallest_next_action": action,
                "human_confirmation_needed": "Yes",
                "missing_blockers": ";".join(blockers) if blockers else "none_manual_source_check_still_required",
                "operator_checked_source_url": "",
                "operator_notes": "",
                "review_only": "Yes",
                "approval_state_change": "none",
                "auto_approval": "No",
                "publish_action": "none_artifact_only",
                "publish_ready": "No",
                "asset_downloads": "No",
                "asset_download_policy": "no_automatic_downloads; review_only_asset_download_intake_required_for_candidate_downloads; download_approval_is_not_asset_approval",
                "asset_approval_state_change": "none",
                "source_enablement": "none_existing_local_artifacts_only",
            }
        )
    cards.sort(key=lambda row: (row.get("renderability_state") != "athlete_led_manual_render_candidate", row.get("game_date", ""), row.get("matchup", "")))
    for index, row in enumerate(cards, 1):
        row["candidate_rank"] = str(index)
    return cards


def story_proof_card_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    athlete_ready = [row for row in rows if row.get("renderability_state") == "athlete_led_manual_render_candidate"]
    return {
        "version": "v1-review-only-story-proof-card",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "asset_downloads": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "athlete_led_manual_render_candidates": len(athlete_ready),
        "blocked_or_score_only": len(rows) - len(athlete_ready),
        "top_candidate_id": athlete_ready[0].get("candidate_id") if athlete_ready else "",
        "top_candidate_claim": athlete_ready[0].get("claim") if athlete_ready else "",
        "top_candidate_next_action": athlete_ready[0].get("smallest_next_action") if athlete_ready else "",
    }


def story_proof_card_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Story Proof Card v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only proof cards.",
        "- No paid APIs, source enablement, automatic downloads, asset approvals, story approvals, render approvals, publishing, or publish-ready movement.",
        "- Asset download approval, if ever needed, must come from human-edited `operator/inbox/review_only_asset_download_intake.csv`; download approval is not asset approval.",
        "- Human confirmation fields stay blank in generated rows.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "athlete_led_manual_render_candidates", "blocked_or_score_only", "top_candidate_claim"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Proof Cards", ""])
    if not rows:
        lines.append("No story proof cards were available in this run.")
    for row in rows[:40]:
        lines.append(f"- **{row.get('candidate_rank')}. {row.get('matchup')}** | {row.get('proof_status')} | {row.get('renderability_state')}")
        lines.append(f"  - claim={row.get('claim')}")
        lines.append(f"  - source={row.get('official_source_url')}")
        lines.append(f"  - source_cue={row.get('source_confirmation_cue')}")
        lines.append(f"  - named_stat={row.get('named_stat_proof') or 'missing'}")
        lines.append(f"  - athlete_image={row.get('athlete_photo_path') or 'missing'}")
        lines.append(f"  - proof={row.get('final_score_proof_row')} | named={row.get('named_stat_proof_row')}")
        lines.append(f"  - review_order_score={row.get('final_score_review_order_row') or 'missing'}")
        lines.append(f"  - review_order_named={row.get('named_stat_review_order_row') or 'missing'}")
        lines.append(f"  - record={row.get('manual_intake_path')}")
        lines.append(f"  - next={row.get('smallest_next_action')}")
    return "\n".join(lines) + "\n"


def final_score_stat_proof_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        counts[clean(row.get("proof_status"))] += 1
    return {
        "version": "v1-review-only-final-score-stat-proof",
        "generated_at_utc": now_iso(),
        "review_only": True,
        "paid_sources_required": False,
        "approval_state_changes": False,
        "publish_actions": False,
        "rows": len(rows),
        "final_score_rows": sum(1 for row in rows if row.get("fact_type") == "final_score"),
        "named_player_stat_rows": sum(1 for row in rows if row.get("fact_type") == "named_player_stat_line"),
        "manual_box_score_confirmation_needed": sum(1 for row in rows if row.get("manual_box_score_confirmation_needed") == "Yes"),
        "status_counts": dict(sorted(counts.items())),
    }


def final_score_stat_proof_report_md(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# HSD Final Score Stat Proof v1",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Policy",
        "",
        "- Review-only, artifact-only score/stat proof ledger.",
        "- No paid APIs, credentials, source enablement, approvals, publishing, or publish-ready movement.",
        "- Each named stat line must be checked against its source URL before copy or render use.",
        "- Record the human check in `final_score_stat_proof_confirmation_intake_v1.csv`; this intake does not approve or publish anything.",
        "",
        "## Counts",
        "",
    ]
    for key in ["rows", "final_score_rows", "named_player_stat_rows", "manual_box_score_confirmation_needed"]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Manual Box-Score Confirmation Needed", ""])
    manual = [row for row in rows if row.get("manual_box_score_confirmation_needed") == "Yes"]
    if not manual:
        lines.append("No named stat lines require manual box-score confirmation beyond operator source review in this run.")
    for row in manual[:80]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('fact_label')} | {row.get('proof_status')}")
        lines.append(f"  - fact={row.get('fact_value') or 'missing'}")
        lines.append(f"  - next={row.get('exact_next_file_or_intake')}")
        lines.append(f"  - note={row.get('operator_note_path')}")
    if len(manual) > 80:
        lines.append(f"Showing first 80 of {len(manual)} manual rows. Open `final_score_stat_proof_v1.csv` for the full ledger.")
    lines.extend(["", "## Source-Backed Score/Stat Rows", ""])
    for row in [item for item in rows if item.get("manual_box_score_confirmation_needed") != "Yes"][:80]:
        lines.append(f"- **{row.get('matchup')}** | {row.get('fact_label')} | {row.get('proof_status')}")
        lines.append(f"  - fact={row.get('fact_value')}")
        lines.append(f"  - source={row.get('source_url')}")
        lines.append(f"  - next={row.get('exact_next_file_or_intake')}")
        lines.append(f"  - note={row.get('operator_note_path')}")
    return "\n".join(lines) + "\n"


def v5_hub_md(run_id: str, events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], iso_dates: List[str]) -> str:
    women = [e for e in events if e.get("gender_scope") == "women"]; finals = [e for e in women if e.get("status_norm") == "final"]; graphics = [e for e in events if e.get("include_in_graphics")]; review = [e for e in events if e.get("manual_review") and e.get("gender_scope") == "women"]
    return "\n".join(["# Her Sports Daily Results Desk v5 Hub", "", f"Run ID: `{run_id}`", f"Generated: `{now_iso()}`", f"Date window: `{', '.join(iso_dates)}`", "", "## Source strategy", "", "- Free/public sources only.", "- Active source: ESPN public WNBA scoreboard endpoint.", "- Optional fallback: local/manual seed CSVs.", "- Paid API keys are not required and are not read by v5.", "", "## Run summary", "", f"- Raw source observations: {len(observations)}", f"- Reconciled events: {len(events)}", f"- Women's events surfaced: {len(women)}", f"- Women's finals: {len(finals)}", f"- Graphics-ready results: {len(graphics)}", f"- Manual review items: {len(review)}", "", "## Accuracy gates", "", "- Duplicate groups are written to `duplicate_game_audit_v5.csv`.", "- Stale/out-of-window observations are written to `stale_source_audit_v5.csv`.", "- Expected-game fixtures, when provided, are checked in `missing_games_alert_v5.*`.", "- No player stats are invented."]) + "\n"


def report_md(run_id: str, manifest: Dict[str, Any]) -> str:
    lines = ["# Her Sports Daily Results Desk v5", "", f"Run ID: `{run_id}`", f"Generated: `{manifest.get('generated_at_utc')}`", f"Version: `{VERSION}`", "", "## What v5 changes", "", "- Removes paid source reliance from the active Results Desk path.", "- Uses free/public WNBA scoreboard data plus manual seed fallback.", "- Keeps v4-compatible output filenames so existing contracts, story results, and graphics packs keep working.", "- Adds duplicate, stale-source, expected-game, and source-health audits.", "", "## Counts", ""]
    for key, value in manifest.get("counts", {}).items(): lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    iso_dates, compact_dates = date_window(); run_id = stable_id(now_iso(), VERSION, ",".join(allowed_sources()))
    observations, health = free_source_observations(run_id, compact_dates); stale_rows = stale_audit(observations, iso_dates); duplicate_rows = duplicate_audit(observations)
    events = apply_strict_date_window_gate(reconcile(run_id, observations), iso_dates); box_audit_rows = audit_wnba_box_scores(events)
    all_events = events; womens = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")]; finals = [e for e in events if e.get("gender_scope") == "women" and e.get("status_norm") == "final" and float(e.get("confidence") or 0) >= 0.70]; top = womens[:50]; review = [e for e in events if e.get("gender_scope") == "women" and e.get("manual_review")]
    expected_rows, expected_summary = missing_games_alert(expected_game_rows(), events); accuracy = source_accuracy(events, observations, health, duplicate_rows, stale_rows, expected_summary); intelligence_rows = game_intelligence_rows(events, observations, expected_rows); stats_gap_rows, stats_confirmation_rows = stats_evidence_gap_rows(events, observations); stats_gap_summary = stats_evidence_gap_summary(stats_gap_rows, stats_confirmation_rows); fact_status_rows = game_fact_confirmation_status_rows(intelligence_rows, stats_gap_rows); stat_proof_rows = final_score_stat_proof_rows(stats_gap_rows); stat_proof_summary = final_score_stat_proof_summary(stat_proof_rows); stat_proof_confirmation_rows = final_score_stat_proof_confirmation_rows(stat_proof_rows); stat_proof_review_order_rows = final_score_stat_proof_review_order_rows(stat_proof_rows); athlete_render_candidate_rows_data = athlete_render_candidate_rows(stat_proof_rows, stat_proof_review_order_rows, read_csv(Path("data/asset_registry/wnba/athlete_photo_catalog.csv"))); athlete_render_candidate_summary_data = athlete_render_candidate_summary(athlete_render_candidate_rows_data); story_proof_card_rows_data = story_proof_card_rows(fact_status_rows, stat_proof_rows, stat_proof_review_order_rows, athlete_render_candidate_rows_data); story_proof_card_summary_data = story_proof_card_summary(story_proof_card_rows_data); fact_status_rows = enrich_game_fact_confirmation_status_rows(fact_status_rows, stat_proof_review_order_rows, story_proof_card_rows_data); fact_status_summary = game_fact_confirmation_status_summary(fact_status_rows); source_next_action_rows_data = game_source_confirmation_next_action_rows(fact_status_rows); source_next_action_summary_data = game_source_confirmation_next_action_summary(source_next_action_rows_data); source_research_worksheet_rows_data = game_source_research_worksheet_rows(source_next_action_rows_data); source_research_worksheet_summary_data = game_source_research_worksheet_summary(source_research_worksheet_rows_data); source_return_summary_rows_data = game_source_confirmation_return_summary_rows(source_research_worksheet_rows_data); source_return_summary_data = game_source_confirmation_return_summary(source_return_summary_rows_data); intelligence_rows = enrich_game_intelligence_rows_with_proof_cues(intelligence_rows, fact_status_rows); intelligence_summary = game_intelligence_summary(intelligence_rows)
    write_csv(OBSERVATIONS_FILE, observations, OBS_FIELDS); write_csv(RECONCILED_FILE, events, EVENT_FIELDS); write_csv(RESULTS_BOARD_FILE, all_events, EVENT_FIELDS); write_csv(WOMENS_RESULTS_FILE, womens, EVENT_FIELDS); write_csv(FINAL_RESULTS_FILE, finals, EVENT_FIELDS); write_csv(TOP_RESULTS_FILE, top, EVENT_FIELDS); write_csv(MANUAL_REVIEW_FILE, review, EVENT_FIELDS)
    write_csv(SOURCE_HEALTH_FILE, health, ["source_name", "sport_or_league", "date", "http_status", "ok", "events_found", "observations_emitted", "stale_rejected", "notes"]); write_csv(BOX_SCORE_AUDIT_FILE, box_audit_rows, ["event_uid", "espn_event_id", "graphics_headline", "league_norm", "http_status", "audit_status", "top_performers", "source_url", "notes"]); write_csv(DUPLICATE_AUDIT, duplicate_rows, DUP_FIELDS); write_csv(STALE_AUDIT, stale_rows, STALE_FIELDS); write_csv("missing_games_alert_v5.csv", expected_rows, EXPECTED_FIELDS); write_csv(GAME_INTELLIGENCE_BOARD_FILE, intelligence_rows, GAME_INTELLIGENCE_FIELDS); write_csv(STATS_EVIDENCE_GAP_BOARD_FILE, stats_gap_rows, STATS_EVIDENCE_FIELDS); write_csv(STATS_CONFIRMATION_INTAKE_FILE, stats_confirmation_rows, STATS_CONFIRMATION_FIELDS); write_csv(GAME_FACT_CONFIRMATION_STATUS_FILE, fact_status_rows, GAME_FACT_CONFIRMATION_STATUS_FIELDS); write_csv(GAME_SOURCE_CONFIRMATION_NEXT_ACTION_FILE, source_next_action_rows_data, GAME_SOURCE_CONFIRMATION_NEXT_ACTION_FIELDS); write_csv(GAME_SOURCE_RESEARCH_WORKSHEET_FILE, source_research_worksheet_rows_data, GAME_SOURCE_RESEARCH_WORKSHEET_FIELDS); write_csv(GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_FILE, source_return_summary_rows_data, GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_FIELDS); write_csv(FINAL_SCORE_STAT_PROOF_FILE, stat_proof_rows, FINAL_SCORE_STAT_PROOF_FIELDS); write_csv(FINAL_SCORE_STAT_PROOF_CONFIRMATION_INTAKE_FILE, stat_proof_confirmation_rows, FINAL_SCORE_STAT_PROOF_CONFIRMATION_FIELDS); write_csv(FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_FILE, stat_proof_review_order_rows, FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_FIELDS); write_csv(ATHLETE_RENDER_CANDIDATE_BOARD_FILE, athlete_render_candidate_rows_data, ATHLETE_RENDER_CANDIDATE_FIELDS); write_csv(STORY_PROOF_CARD_FILE, story_proof_card_rows_data, STORY_PROOF_CARD_FIELDS)
    write_text(BOX_SCORE_SUMMARY_FILE, box_score_summary_md(box_audit_rows)); write_text(GRAPHICS_QUEUE_FILE, graphics_queue(events)); write_text(RECOMMENDATIONS_FILE, recommendations_md(events)); write_text(HUB_FILE, v5_hub_md(run_id, events, observations, health, iso_dates)); write_text(GAME_INTELLIGENCE_REPORT_FILE, game_intelligence_report_md(intelligence_summary, intelligence_rows)); write_text(STATS_EVIDENCE_GAP_REPORT_FILE, stats_evidence_gap_report_md(stats_gap_summary, stats_gap_rows, stats_confirmation_rows)); write_text(GAME_FACT_CONFIRMATION_STATUS_REPORT_FILE, game_fact_confirmation_status_report_md(fact_status_summary, fact_status_rows)); write_text(GAME_SOURCE_CONFIRMATION_NEXT_ACTION_REPORT_FILE, game_source_confirmation_next_action_report_md(source_next_action_summary_data, source_next_action_rows_data)); write_text(GAME_SOURCE_RESEARCH_WORKSHEET_REPORT_FILE, game_source_research_worksheet_report_md(source_research_worksheet_summary_data, source_research_worksheet_rows_data)); write_text(GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_REPORT_FILE, game_source_confirmation_return_summary_report_md(source_return_summary_data, source_return_summary_rows_data)); write_text(FINAL_SCORE_STAT_PROOF_REPORT_FILE, final_score_stat_proof_report_md(stat_proof_summary, stat_proof_rows)); write_text(FINAL_SCORE_STAT_PROOF_WALKTHROUGH_FILE, final_score_stat_proof_review_walkthrough_md(stat_proof_review_order_rows)); write_text(ATHLETE_RENDER_CANDIDATE_REPORT_FILE, athlete_render_candidate_report_md(athlete_render_candidate_summary_data, athlete_render_candidate_rows_data)); write_text(STORY_PROOF_CARD_REPORT_FILE, story_proof_card_report_md(story_proof_card_summary_data, story_proof_card_rows_data))
    write_json(SOURCE_ACCURACY_JSON, accuracy); write_text(SOURCE_ACCURACY_MD, write_source_accuracy_md(accuracy)); write_json(MISSING_ALERT_JSON, {"summary": expected_summary, "rows": expected_rows}); write_text(MISSING_ALERT_MD, missing_games_md(expected_summary, expected_rows)); write_json(GAME_INTELLIGENCE_MANIFEST_FILE, {"summary": intelligence_summary, "rows": intelligence_rows}); write_json(STATS_EVIDENCE_GAP_MANIFEST_FILE, {"summary": stats_gap_summary, "rows": stats_gap_rows, "confirmation_intake": stats_confirmation_rows}); write_json(GAME_FACT_CONFIRMATION_STATUS_MANIFEST_FILE, {"summary": fact_status_summary, "rows": fact_status_rows}); write_json(GAME_SOURCE_CONFIRMATION_NEXT_ACTION_MANIFEST_FILE, {"summary": source_next_action_summary_data, "rows": source_next_action_rows_data}); write_json(GAME_SOURCE_RESEARCH_WORKSHEET_MANIFEST_FILE, {"summary": source_research_worksheet_summary_data, "rows": source_research_worksheet_rows_data}); write_json(GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_MANIFEST_FILE, {"summary": source_return_summary_data, "rows": source_return_summary_rows_data}); write_json(FINAL_SCORE_STAT_PROOF_MANIFEST_FILE, {"summary": stat_proof_summary, "rows": stat_proof_rows, "confirmation_intake": stat_proof_confirmation_rows, "review_order": stat_proof_review_order_rows}); write_json(ATHLETE_RENDER_CANDIDATE_MANIFEST_FILE, {"summary": athlete_render_candidate_summary_data, "rows": athlete_render_candidate_rows_data}); write_json(STORY_PROOF_CARD_MANIFEST_FILE, {"summary": story_proof_card_summary_data, "rows": story_proof_card_rows_data})
    manifest = {"version": VERSION, "run_id": run_id, "generated_at_utc": now_iso(), "sources": allowed_sources(), "date_window": iso_dates, "free_only": True, "paid_sources_required": False, "counts": {"observations": len(observations), "reconciled_events": len(events), "women_events": len(womens), "final_women_events": len(finals), "manual_review": len(review), "graphics_ready": sum(1 for e in events if e.get("include_in_graphics")), "must_post": sum(1 for e in events if e.get("editorial_bucket") == "Must Post"), "strong_maybe": sum(1 for e in events if e.get("editorial_bucket") == "Strong Maybe"), "watchlist": sum(1 for e in events if e.get("editorial_bucket") == "Watchlist"), "carryover_archived": sum(1 for e in events if e.get("is_carryover") == "Yes"), "wnba_box_audit_rows": len(box_audit_rows), "game_intelligence_rows": len(intelligence_rows), "game_intelligence_recap_candidates": intelligence_summary.get("recap_candidates", 0), "game_intelligence_missing_stats_context": intelligence_summary.get("missing_stats_context", 0), "stats_evidence_gap_rows": len(stats_gap_rows), "stats_confirmation_intake_rows": len(stats_confirmation_rows), "game_fact_confirmation_status_rows": len(fact_status_rows), "game_fact_manual_verification_required": fact_status_summary.get("manual_verification_required", 0), "game_source_confirmation_return_summary_rows": len(source_return_summary_rows_data), "game_source_confirmation_return_summary_missing_official_url": source_return_summary_data.get("missing_official_url", 0), "game_source_confirmation_return_summary_missing_status": source_return_summary_data.get("missing_confirmation_status", 0), "final_score_stat_proof_rows": len(stat_proof_rows), "final_score_stat_proof_manual_confirmation_needed": stat_proof_summary.get("manual_box_score_confirmation_needed", 0), "final_score_stat_proof_confirmation_intake_rows": len(stat_proof_confirmation_rows), "final_score_stat_proof_review_order_rows": len(stat_proof_review_order_rows), "athlete_render_candidate_rows": len(athlete_render_candidate_rows_data), "athlete_render_candidate_ready": athlete_render_candidate_summary_data.get("ready_for_manual_review", 0), "story_proof_card_rows": len(story_proof_card_rows_data), "story_proof_card_athlete_led_candidates": story_proof_card_summary_data.get("athlete_led_manual_render_candidates", 0), "duplicate_groups": len(duplicate_rows), "stale_observations": len(stale_rows), "expected_games": expected_summary.get("expected_games", 0), "missing_expected_games": expected_summary.get("missing", 0)}, "source_health": health, "v5_audit_files": {"source_accuracy": SOURCE_ACCURACY_JSON.as_posix(), "duplicates": DUPLICATE_AUDIT.as_posix(), "stale": STALE_AUDIT.as_posix(), "missing_games": MISSING_ALERT_JSON.as_posix(), "game_intelligence": GAME_INTELLIGENCE_MANIFEST_FILE, "stats_evidence_gap": STATS_EVIDENCE_GAP_MANIFEST_FILE, "game_fact_confirmation_status": GAME_FACT_CONFIRMATION_STATUS_MANIFEST_FILE, "game_source_confirmation_return_summary": GAME_SOURCE_CONFIRMATION_RETURN_SUMMARY_MANIFEST_FILE, "final_score_stat_proof": FINAL_SCORE_STAT_PROOF_MANIFEST_FILE, "final_score_stat_proof_confirmation_intake": FINAL_SCORE_STAT_PROOF_CONFIRMATION_INTAKE_FILE, "final_score_stat_proof_review_order": FINAL_SCORE_STAT_PROOF_REVIEW_ORDER_FILE, "final_score_stat_proof_review_walkthrough": FINAL_SCORE_STAT_PROOF_WALKTHROUGH_FILE, "athlete_render_candidate_board": ATHLETE_RENDER_CANDIDATE_BOARD_FILE, "athlete_render_candidate_report": ATHLETE_RENDER_CANDIDATE_REPORT_FILE, "athlete_render_candidate_manifest": ATHLETE_RENDER_CANDIDATE_MANIFEST_FILE, "story_proof_card": STORY_PROOF_CARD_FILE, "story_proof_card_report": STORY_PROOF_CARD_REPORT_FILE, "story_proof_card_manifest": STORY_PROOF_CARD_MANIFEST_FILE}}
    write_json(MANIFEST_FILE, manifest); write_json(V5_MANIFEST, manifest); write_text(V5_REPORT, report_md(run_id, manifest))
    print("Created Results Desk v5 outputs"); print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
