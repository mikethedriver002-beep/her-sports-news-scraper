from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


VERSION = "news-sync-v1.7"

INPUT_RESULTS_QUEUE = os.environ.get("HSD_RESULTS_GRAPHICS_QUEUE", "results_graphics_queue.md")
INPUT_RESULTS_RECS = os.environ.get("HSD_RESULTS_RECOMMENDATIONS", "daily_results_recommendations.md")
INPUT_WNBA_BOX = os.environ.get("HSD_WNBA_BOX_SUMMARY", "wnba_box_score_summary.md")
INPUT_RESULTS_HUB = os.environ.get("HSD_RESULTS_HUB", "results_system_hub.md")
INPUT_RESULTS_TOP_CSV = os.environ.get("HSD_RESULTS_TOP_CSV", "top_womens_results.csv")
INPUT_RESULTS_RECONCILED_CSV = os.environ.get("HSD_RESULTS_RECONCILED_CSV", "reconciled_events.csv")
INPUT_RESULTS_FINALS_CSV = os.environ.get("HSD_RESULTS_FINALS_CSV", "today_final_results.csv")

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
]

SOURCE_OBS_FIELDS = [
    "run_id", "candidate_id", "source_id", "source_name", "source_priority",
    "source_type", "url", "domain", "fetch_status", "http_status", "title",
    "description", "matched_terms", "published_hint", "usable_context",
    "context_signal", "fetched_at_utc", "review_flag", "notes",
]

PACKET_FIELDS = [
    "run_id", "candidate_id", "queue_section", "sport", "league", "editorial_bucket",
    "content_family", "publish_recommendation", "urgency", "headline", "dek",
    "brief_120w", "caption_hard_fact", "caption_voice", "story_text",
    "slide3_context", "graphics_handoff", "source_count", "primary_source_count",
    "source_urls_json", "context_signal", "top_performers", "review_flags",
    "context_quality", "quality_score", "production_ready",
    "content_format_recommendation", "result_record_source",
    "manual_review", "score_accuracy_check", "rights_safe_note",
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


def load_json(path: str, default: Any) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def candidate_input_paths(path: str) -> List[Path]:
    """
    News Sync v1.1 searches both root outputs and archived latest outputs.

    This fixes the first-run failure mode where News Sync ran successfully
    but found 0 candidates because it did not locate Results Desk files.
    """
    p = Path(path)
    names = [p]
    if not p.is_absolute():
        names.extend([
            Path("results_run_history") / "latest" / path,
            Path("results_run_history") / "latest" / p.name,
            Path("results_run_history") / p.name,
        ])
    return names


def resolve_input(path: str) -> Tuple[Path, str]:
    for p in candidate_input_paths(path):
        if p.exists() and p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                text = p.read_text(encoding="utf-8", errors="replace")
            return p, text
    return Path(path), ""


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
    with open(path, "w", newline="", encoding="utf-8") as f:
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
    return Path(path), []


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
    if clean(record.get("gender_scope")).lower() != "women":
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
            if not row_is_news_safe(r):
                continue
            rr = dict(r)
            rr["_result_record_source"] = source_name
            rows.append(rr)

    rows = dedupe_result_records(rows)

    must_rows = [r for r in rows if row_is_must(r)]
    strong_rows = [r for r in rows if row_is_strong(r) and not row_is_must(r)]

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

    # The file varies across versions, so parse broadly.
    chunks = re.split(r"\n(?=##|\d+\.|\- \*\*)", text)
    for chunk in chunks:
        ch = clean(chunk)
        if not ch:
            continue

        # look for known player-stat-rich lines
        if any(name in ch for name in ["A'ja", "Arike", "Paige", "Natasha", "DeWanna", "Jackie", "Jessica", "Olivia"]):
            # key by teams if present, otherwise by first sentence
            key = ""
            team_hits = []
            for team in [
                "Dallas", "Los Angeles", "Phoenix", "Portland", "Minnesota", "Seattle",
                "Las Vegas", "Golden State", "Chicago", "Connecticut"
            ]:
                if team.lower() in ch.lower():
                    team_hits.append(team)
            if len(team_hits) >= 2:
                key = " ".join(team_hits[:2]).lower()
            else:
                key = clean(ch[:80]).lower()
            out[key] = ch

    return out


def find_top_performers(candidate: Dict[str, Any], box_map: Dict[str, str]) -> str:
    blob = " ".join([
        candidate.get("graphics_headline", ""),
        candidate.get("matchup", ""),
        candidate.get("final_score", ""),
        candidate.get("slide3_context", ""),
    ]).lower()

    best = ""
    best_score = 0
    for key, val in box_map.items():
        score = 0
        for token in key.split():
            if len(token) >= 4 and token in blob:
                score += 1
        if score > best_score:
            best_score = score
            best = val

    if best_score >= 1:
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
                "urls": ["https://www.theguardian.com/football/women"],
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
            "dallas wings": ["https://wings.wnba.com/"],
            "los angeles sparks": ["https://sparks.wnba.com/"],
            "phoenix mercury": ["https://mercury.wnba.com/"],
            "minnesota lynx": ["https://lynx.wnba.com/"],
            "seattle storm": ["https://storm.wnba.com/"],
            "las vegas aces": ["https://aces.wnba.com/"],
            "golden state valkyries": ["https://valkyries.wnba.com/"],
            "chicago sky": ["https://sky.wnba.com/"],
            "connecticut sun": ["https://sun.wnba.com/"]
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
                "fetched_at_utc": utc_now(),
                "review_flag": review_flag,
                "notes": meta.get("notes", "") or source.get("notes", ""),
            })
            time.sleep(REQUEST_SLEEP_SECONDS)

    return observations


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
    }


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
                f"**Review flags:** {p.get('review_flags') or 'None'}",
                f"**Source depth:** {p.get('source_count')} usable / {p.get('primary_source_count')} primary",
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
            f"**Queue:** {p.get('queue_section')} | **Manual review:** {p.get('manual_review')}",
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
        "# Her Sports Daily News Daily Plan v1.3",
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
        "# Her Sports Daily News Sync v1.7 Hub",
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

    manual_packets = [p for p in packets if p.get("manual_review") == "Yes"]

    write_csv(NEWS_INPUT_STATUS_CSV, input_status, INPUT_STATUS_FIELDS)
    write_csv(NEWS_CANDIDATES_CSV, candidates, CANDIDATE_FIELDS)
    write_csv(NEWS_SOURCE_OBS_CSV, all_observations, SOURCE_OBS_FIELDS)
    write_csv(NEWS_FACT_PACKETS_CSV, packets, PACKET_FIELDS)
    write_csv(NEWS_MANUAL_REVIEW_CSV, manual_packets, PACKET_FIELDS)

    Path(NEWS_BRIEF_QUEUE_MD).write_text(markdown_brief_queue(packets, observations_by_candidate), encoding="utf-8")
    Path(NEWS_SOCIAL_PACKETS_MD).write_text(markdown_social_packets(packets), encoding="utf-8")
    Path(NEWS_GRAPHICS_HANDOFF_MD).write_text(markdown_graphics_handoff(packets), encoding="utf-8")
    Path(NEWS_DAILY_PLAN_MD).write_text(markdown_daily_plan(packets), encoding="utf-8")
    Path(NEWS_SYNC_HUB_MD).write_text(markdown_hub(run_id, candidates, all_observations, packets), encoding="utf-8")

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
            NEWS_SYNC_HUB_MD,
        ],
        "counts": {
            "candidates": len(candidates),
            "source_observations": len(all_observations),
            "fact_packets": len(packets),
            "manual_review": len(manual_packets),
            "publish_ready": len([p for p in packets if p.get("manual_review") != "Yes"]),
            "production_ready": len([p for p in packets if p.get("production_ready") == "Yes"]),
        },
        "settings": {
            "max_must_post": MAX_MUST_POST,
            "max_strong_maybe": MAX_STRONG_MAYBE,
            "max_diversity_promotions": MAX_DIVERSITY_PROMOTIONS,
            "max_soccer_diversity": MAX_SOCCER_DIVERSITY,
            "enable_fetch": ENABLE_FETCH,
        }
    }
    Path(NEWS_MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if not candidates:
        Path(NEWS_SETUP_ERROR_MD).write_text(
            "# Her Sports Daily News Sync Setup Error\\n\\n"
            "News Sync ran, but found 0 candidates.\\n\\n"
            "Most likely causes:\\n\\n"
            "1. `results_graphics_queue.md` is missing from the repo root.\\n"
            "2. Results Desk has not committed its latest outputs yet.\\n"
            "3. The file exists only in `results_run_history/latest/`, but the workflow did not include it.\\n"
            "4. The Results Desk queue format changed.\\n\\n"
            "Open `news_input_status_report.csv` first.\\n",
            encoding="utf-8"
        )

    print("Created Her Sports Daily News Sync v1.1 outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
