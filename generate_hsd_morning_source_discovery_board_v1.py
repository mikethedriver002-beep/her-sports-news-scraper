from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from hsd_run_io import input_path, output_path, read_csv, read_json, write_csv, write_json, write_text

VERSION = "hsd-morning-source-discovery-board-v1.5-story-opportunities"

OUT_CSV = output_path("morning_source_discovery_board.csv")
OUT_JSON = output_path("morning_source_discovery_board.json")
OUT_MD = output_path("morning_source_discovery_board.md")
PROMOTION_CSV = output_path("morning_lead_promotion_recommendations.csv")
PROMOTION_JSON = output_path("morning_lead_promotion_recommendations.json")
PROMOTION_MD = output_path("morning_lead_promotion_recommendations.md")

FIELDS = [
    "rank",
    "lane",
    "review_status",
    "source_band",
    "publish_posture",
    "source_name",
    "source_type",
    "sport_league",
    "title",
    "summary",
    "source_url",
    "evidence_title",
    "evidence_published_at",
    "evidence_description",
    "evidence_preview",
    "evidence_source",
    "story_opportunity_id",
    "story_opportunity_title",
    "story_opportunity_size",
    "story_opportunity_sources",
    "story_opportunity_urls",
    "story_opportunity_reason",
    "source_artifact",
    "next_action",
    "reason",
    "candidate_id",
    "evidence_count",
    "lead_score",
    "freshness_date",
    "freshness_label",
    "freshness_source",
    "freshness_score",
    "urgency_score",
    "quality_score",
    "quality_reason",
    "promotion_hint",
    "promotion_recommendation",
    "promotion_priority",
    "promotion_target",
    "promotion_reason",
    "promotion_next_step",
]

PROMOTION_FIELDS = ["promotion_rank"] + FIELDS

STRIP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value: Any) -> str:
    return clean(value).lower()


def yes(value: Any) -> bool:
    return norm(value) in {"1", "true", "yes", "y", "pass", "ready", "approved"}


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(clean(value)))
    except Exception:
        return default


def canonicalize(url: str) -> str:
    url = clean(url)
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in STRIP_PARAMS]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/", urlencode(query), ""))
    except Exception:
        return url


def lead_id(parts: Iterable[Any]) -> str:
    raw = "|".join(clean(part) for part in parts if clean(part))
    if not raw:
        raw = datetime.now(timezone.utc).isoformat()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]


CLUSTER_STOPWORDS = {
    "about",
    "after",
    "again",
    "ahead",
    "also",
    "amid",
    "announce",
    "announced",
    "announces",
    "article",
    "before",
    "during",
    "final",
    "first",
    "from",
    "game",
    "games",
    "league",
    "match",
    "matchup",
    "news",
    "official",
    "over",
    "preview",
    "result",
    "results",
    "says",
    "score",
    "season",
    "sports",
    "story",
    "that",
    "their",
    "this",
    "today",
    "with",
    "wnba",
    "women",
    "womens",
    "wire",
}


def cluster_tokens(row: Dict[str, Any]) -> set[str]:
    text = " ".join(
        clean(row.get(key))
        for key in ["title", "evidence_title", "summary", "evidence_description"]
        if clean(row.get(key))
    )
    tokens = set()
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        if len(token) < 3 or token in CLUSTER_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


def clusterable_story_row(row: Dict[str, str]) -> bool:
    return (
        row.get("source_artifact") == "story_candidates_discovery.csv"
        and row.get("lane") in {"official_free", "wire"}
        and row.get("promotion_recommendation") in {"news_packet", "studio_brief"}
    )


def related_story_rows(left: Dict[str, str], right: Dict[str, str]) -> bool:
    if canonicalize(left.get("source_url", "")) and canonicalize(left.get("source_url", "")) == canonicalize(right.get("source_url", "")):
        return True
    left_tokens = cluster_tokens(left)
    right_tokens = cluster_tokens(right)
    shared = left_tokens & right_tokens
    if len(shared) < 2:
        return False
    return token_overlap(left_tokens, right_tokens) >= 0.5


def trust_band_from_values(*values: Any) -> str:
    text = " ".join(norm(value) for value in values)
    if any(token in text for token in ["red", "prohibited", "paid", "private", "paywall", "restricted"]):
        return "red"
    if "green_cross_check" in text or "cross_check" in text:
        return "green_cross_check"
    if "green" in text or any(token in text for token in ["official", "operator", "wire", "primary"]):
        return "green"
    if any(token in text for token in ["yellow", "social", "community", "discovery", "gray", "grey"]):
        return "yellow"
    return "yellow"


def lane_for(source_type: Any, band: Any, artifact: str = "") -> str:
    text = " ".join([norm(source_type), norm(band), norm(artifact)])
    if "story_candidates_manual" in text or "operator/inbox" in text or norm(source_type) == "manual":
        return "manual_lead"
    if "social" in text or "reddit" in text or "mastodon" in text:
        return "social_discovery"
    if "wire" in text:
        return "wire"
    if "scoreboard" in text or "cross_check" in text or "mainstream" in text or "primary_media" in text:
        return "free_cross_check"
    if "official" in text or "green" in text:
        return "official_free"
    return "gray_area_review"


def publish_posture_for(band: str, lane: str, eligible: Any = "", publish_use: str = "") -> str:
    use = norm(publish_use)
    if band == "red" or use == "blocked":
        return "blocked"
    if use == "publish_grade":
        return "publish_grade_review"
    if use == "cross_check" or lane == "free_cross_check":
        return "cross_check"
    if yes(eligible):
        return "operator_verified_review"
    if band == "green" and lane in {"official_free", "wire"}:
        return "source_scan"
    return "discovery_only"


def review_status_for(band: str, posture: str, eligible: Any = "") -> str:
    if posture == "blocked":
        return "blocked"
    if yes(eligible) or posture in {"publish_grade_review", "operator_verified_review"}:
        return "editor_review"
    if posture == "source_scan":
        return "source_scan"
    if band == "green_cross_check":
        return "verify_with_primary"
    return "needs_green_confirmation"


def next_action_for(lane: str, posture: str, reason: str = "") -> str:
    if posture == "blocked":
        return "Do not use this source path."
    if lane == "manual_lead" and posture == "operator_verified_review":
        return "Confirm locked facts and decide whether to promote into News or Studio."
    if lane == "manual_lead":
        return "Finish verification and add evidence before this becomes a publish-grade fact."
    if lane in {"social_discovery", "gray_area_review"}:
        return "Use as a lead only; find official, wire, or primary confirmation before publishing."
    if lane == "wire":
        return "Review facts against the wire/source link, then pair with official context when possible."
    if lane == "free_cross_check":
        return "Use as a cross-check; official or wire source wins on conflict."
    if posture == "source_scan":
        return "Morning scan source; add a lead only when a relevant fact appears."
    return reason or "Review source evidence before any manual post."


def has_any(text: str, terms: Iterable[str]) -> bool:
    low = norm(text)
    return any(term in low for term in terms)


def visual_story_signal(row: Dict[str, Any]) -> bool:
    text = " ".join([clean(row.get("title")), clean(row.get("summary")), clean(row.get("reason")), clean(row.get("promotion_hint"))])
    return has_any(
        text,
        [
            "beat",
            "beats",
            "defeat",
            "defeats",
            "final",
            "score",
            "winner",
            "wins",
            "preview",
            " vs ",
            " at ",
            "leaderboard",
            "top performer",
            "graphic",
            "highlight",
            "studio_brief",
        ],
    )


def news_story_signal(row: Dict[str, Any]) -> bool:
    text = " ".join([clean(row.get("title")), clean(row.get("summary")), clean(row.get("reason")), clean(row.get("promotion_hint"))])
    return has_any(
        text,
        [
            "announce",
            "announces",
            "sign",
            "signs",
            "trade",
            "trades",
            "waive",
            "waives",
            "injury",
            "roster",
            "award",
            "record",
            "expansion",
            "coach",
            "press release",
            "partnership",
            "launch",
            "hires",
            "hired",
            "named",
            "fined",
            "fines",
            "retires",
            "returns",
            "commits",
            "news",
        ],
    )


def promotion_for(row: Dict[str, Any]) -> Dict[str, str]:
    lane = clean(row.get("lane"))
    posture = clean(row.get("publish_posture"))
    status = clean(row.get("review_status"))
    artifact = clean(row.get("source_artifact"))
    band = clean(row.get("source_band"))
    hint = clean(row.get("promotion_hint"))

    if posture == "blocked" or band == "red":
        return {
            "promotion_recommendation": "no_promotion",
            "promotion_priority": "P0",
            "promotion_target": "",
            "promotion_reason": "Blocked or prohibited source posture.",
            "promotion_next_step": "Do not promote this lead.",
        }

    if artifact == "config/source_registry.json" or status == "source_scan" or posture == "source_scan":
        return {
            "promotion_recommendation": "monitor_only",
            "promotion_priority": "P4",
            "promotion_target": "morning_source_discovery_board.md",
            "promotion_reason": "Source scan row; no concrete story lead has been captured yet.",
            "promotion_next_step": "Open the source manually and add a concrete lead only when a relevant fact appears.",
        }

    if lane in {"social_discovery", "gray_area_review"} or posture == "discovery_only":
        return {
            "promotion_recommendation": "manual_story_candidate",
            "promotion_priority": "P3",
            "promotion_target": "story_candidates_manual.csv",
            "promotion_reason": "Discovery-only lead needs official, wire, primary, or operator-verified evidence before it can become a fact.",
            "promotion_next_step": "Add or verify the lead in the manual story inbox with evidence URLs and locked facts.",
        }

    if lane == "free_cross_check" or posture == "cross_check":
        return {
            "promotion_recommendation": "cross_check_existing",
            "promotion_priority": "P3",
            "promotion_target": "news_source_observations.csv",
            "promotion_reason": "Free cross-check source should support another lead, not carry the story alone.",
            "promotion_next_step": "Pair this with an official, wire, or operator-verified source before promotion.",
        }

    if hint == "manual_story_candidate":
        priority = "P2" if band == "green" else "P3"
        return {
            "promotion_recommendation": "manual_story_candidate",
            "promotion_priority": priority,
            "promotion_target": "story_candidates_manual.csv",
            "promotion_reason": "The lead is concrete but needs operator fact-locking before it becomes a News packet or Studio brief.",
            "promotion_next_step": "Add the lead to the manual story inbox with evidence URLs, locked facts, and the intended angle.",
        }

    if visual_story_signal(row):
        return {
            "promotion_recommendation": "studio_brief",
            "promotion_priority": "P1",
            "promotion_target": "studio_bundle_queue.csv",
            "promotion_reason": "The lead has a visual/result/preview signal and enough source posture for editor review.",
            "promotion_next_step": "Draft a Studio brief manually after confirming facts and asset readiness.",
        }

    if news_story_signal(row) or lane in {"official_free", "wire", "manual_lead"}:
        priority = "P1" if posture in {"publish_grade_review", "operator_verified_review"} else "P2"
        return {
            "promotion_recommendation": "news_packet",
            "promotion_priority": priority,
            "promotion_target": "news_fact_packets.csv",
            "promotion_reason": "The lead has official, wire, or operator-verified posture and reads like a factual news item.",
            "promotion_next_step": "Draft or refresh a News packet manually; keep quotes, claims, and stats source-backed.",
        }

    return {
        "promotion_recommendation": "monitor_only",
        "promotion_priority": "P4",
        "promotion_target": "morning_source_discovery_board.md",
        "promotion_reason": "No clear News, manual-story, or Studio promotion signal yet.",
        "promotion_next_step": "Keep in the morning board until a stronger story angle appears.",
    }


def evidence_count(value: Any) -> str:
    text = clean(value)
    if not text:
        return "0"
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return str(len(parsed))
    except Exception:
        pass
    return str(len([part for part in re.split(r"[;,]", text) if clean(part)]))


def source_url_from_registry(source: Dict[str, Any]) -> str:
    urls = source.get("urls") or []
    if urls:
        return clean(urls[0])
    for key in ["path_csv", "path_jsonl"]:
        if clean(source.get(key)):
            return clean(source.get(key))
    domains = source.get("domains") or []
    if domains:
        return clean(domains[0])
    return ""


def make_row(
    *,
    lane: str,
    source_band: str,
    source_name: str,
    source_type: str,
    sport_league: str,
    title: str,
    summary: str,
    source_url: str,
    source_artifact: str,
    reason: str,
    evidence_title: str = "",
    evidence_published_at: str = "",
    evidence_description: str = "",
    evidence_preview: str = "",
    evidence_source: str = "",
    candidate_id: str = "",
    evidence: str = "0",
    eligible: Any = "",
    publish_use: str = "",
    promotion_hint: str = "",
    lead_score: str = "",
    freshness_date: str = "",
    freshness_label: str = "",
    freshness_source: str = "",
    freshness_score: str = "",
    urgency_score: str = "",
    quality_score: str = "",
    quality_reason: str = "",
    priority_score: int = 99,
) -> Dict[str, Any]:
    posture = publish_posture_for(source_band, lane, eligible, publish_use)
    status = review_status_for(source_band, posture, eligible)
    return {
        "_priority_score": priority_score,
        "_dedupe": lead_id([lane, canonicalize(source_url), title, source_artifact, candidate_id]),
        "rank": "",
        "lane": lane,
        "review_status": status,
        "source_band": source_band,
        "publish_posture": posture,
        "source_name": source_name,
        "source_type": source_type,
        "sport_league": sport_league,
        "title": title or source_name or source_url,
        "summary": summary,
        "source_url": source_url,
        "evidence_title": clean(evidence_title),
        "evidence_published_at": clean(evidence_published_at),
        "evidence_description": clean(evidence_description),
        "evidence_preview": clean(evidence_preview),
        "evidence_source": clean(evidence_source),
        "story_opportunity_id": "",
        "story_opportunity_title": "",
        "story_opportunity_size": "",
        "story_opportunity_sources": "",
        "story_opportunity_urls": "",
        "story_opportunity_reason": "",
        "source_artifact": source_artifact,
        "next_action": next_action_for(lane, posture, reason),
        "reason": reason,
        "candidate_id": candidate_id,
        "evidence_count": evidence,
        "lead_score": clean(lead_score),
        "freshness_date": clean(freshness_date),
        "freshness_label": clean(freshness_label),
        "freshness_source": clean(freshness_source),
        "freshness_score": clean(freshness_score),
        "urgency_score": clean(urgency_score),
        "quality_score": clean(quality_score),
        "quality_reason": clean(quality_reason),
        "promotion_hint": clean(promotion_hint),
    }


def rows_from_manual_candidates() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in read_csv("story_candidates_manual.csv"):
        band = trust_band_from_values(row.get("source_trust_band"), row.get("risk_tier"))
        lane = lane_for(row.get("input_type"), band, "story_candidates_manual.csv")
        eligible = row.get("publish_eligible")
        rows.append(
            make_row(
                lane=lane,
                source_band=band,
                source_name="Manual story inbox",
                source_type=clean(row.get("input_type")) or "manual",
                sport_league=clean(row.get("league") or row.get("sport") or "all"),
                title=clean(row.get("title") or row.get("source_url")),
                summary=clean(row.get("summary")),
                source_url=clean(row.get("source_url") or row.get("canonical_url")),
                source_artifact="story_candidates_manual.csv",
                reason=clean(row.get("reason")) or clean(row.get("verification_status")),
                evidence=evidence_count(row.get("evidence_urls_json")),
                eligible=eligible,
                promotion_hint=clean(row.get("promotion_hint")),
                priority_score=10 if yes(eligible) else 28,
            )
        )
    return rows


def rows_from_raw_manual_inbox() -> List[Dict[str, Any]]:
    raw_rows = read_csv("operator/inbox/story_inbox.csv")
    rows: List[Dict[str, Any]] = []
    for row in raw_rows:
        title = clean(row.get("title") or row.get("headline") or row.get("source_url") or row.get("url"))
        source_url = clean(row.get("source_url") or row.get("url") or row.get("link"))
        if not title and not source_url:
            continue
        band = trust_band_from_values(row.get("source_trust_band"), row.get("risk_tier"), row.get("input_type"))
        rows.append(
            make_row(
                lane="manual_lead",
                source_band=band,
                source_name="Manual story inbox",
                source_type=clean(row.get("input_type")) or "manual",
                sport_league=clean(row.get("league") or row.get("sport") or "all"),
                title=title,
                summary=clean(row.get("summary")),
                source_url=source_url,
                source_artifact="operator/inbox/story_inbox.csv",
                reason="raw manual inbox item; normalize or verify before publish",
                evidence=evidence_count(row.get("evidence_urls_json")),
                eligible=row.get("publish_eligible"),
                promotion_hint=clean(row.get("promotion_hint")),
                priority_score=32,
            )
        )
    return rows


def rows_from_discovery_candidates() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in read_csv("story_candidates_discovery.csv"):
        band = trust_band_from_values(row.get("source_trust_band"), row.get("risk_tier"), row.get("source_tier"))
        lane = lane_for(row.get("source_type"), band, "story_candidates_discovery.csv")
        eligible = row.get("publish_eligible")
        quality = as_int(row.get("quality_score"), 0)
        rows.append(
            make_row(
                lane=lane,
                source_band=band,
                source_name=clean(row.get("source_id")) or "Discovery source",
                source_type=clean(row.get("source_type")),
                sport_league=clean(row.get("sport") or row.get("league") or "all"),
                title=clean(row.get("title") or row.get("source_url")),
                summary=clean(row.get("summary")),
                source_url=clean(row.get("source_url") or row.get("canonical_url")),
                evidence_title=clean(row.get("evidence_title")),
                evidence_published_at=clean(row.get("evidence_published_at")),
                evidence_description=clean(row.get("evidence_description")),
                evidence_preview=clean(row.get("evidence_preview")),
                evidence_source=clean(row.get("evidence_source")),
                source_artifact="story_candidates_discovery.csv",
                reason=clean(row.get("review_next_step") or row.get("reason")),
                eligible=eligible,
                promotion_hint=clean(row.get("promotion_hint")),
                lead_score=clean(row.get("lead_score")),
                freshness_date=clean(row.get("freshness_date")),
                freshness_label=clean(row.get("freshness_label")),
                freshness_source=clean(row.get("freshness_source")),
                freshness_score=clean(row.get("freshness_score")),
                urgency_score=clean(row.get("urgency_score")),
                quality_score=clean(row.get("quality_score")),
                quality_reason=clean(row.get("quality_reason")),
                priority_score=(12 if yes(eligible) else 36) + max(0, 100 - quality) // 8,
            )
        )
    return rows


def rows_from_news_observations() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in read_csv("news_source_observations.csv"):
        if norm(row.get("usable_context")) not in {"yes", "partial"}:
            continue
        band = trust_band_from_values(row.get("source_trust_band"), row.get("source_type"))
        lane = lane_for(row.get("source_type"), band, "news_source_observations.csv")
        publish_use = clean(row.get("publish_use"))
        priority = 12 if publish_use == "publish_grade" else 24 if publish_use == "cross_check" else 46
        rows.append(
            make_row(
                lane=lane,
                source_band=band,
                source_name=clean(row.get("source_name") or row.get("source_id")),
                source_type=clean(row.get("source_type")),
                sport_league="news",
                title=clean(row.get("context_signal") or row.get("title") or row.get("source_name")),
                summary=clean(row.get("description") or row.get("notes")),
                source_url=clean(row.get("url")),
                source_artifact="news_source_observations.csv",
                reason=clean(row.get("review_flag") or row.get("usable_context")),
                candidate_id=clean(row.get("candidate_id")),
                publish_use=publish_use,
                priority_score=priority,
            )
        )
    return rows


def rows_from_registry_scans(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for source in registry.get("sources", []):
        if not source.get("enabled"):
            continue
        band = trust_band_from_values(source.get("trust_band"), source.get("tier"), source.get("source_type"))
        if band == "red":
            continue
        lane = lane_for(source.get("source_type"), band, "config/source_registry.json")
        source_type = clean(source.get("source_type"))
        priority = 62 if lane == "manual_lead" else 68 if lane in {"official_free", "wire"} else 78
        rows.append(
            make_row(
                lane=lane,
                source_band=band,
                source_name=clean(source.get("source_id")),
                source_type=source_type,
                sport_league=clean(source.get("sport_league") or "all"),
                title=f"Scan {clean(source.get('source_id'))}",
                summary=clean(source.get("publish_policy")),
                source_url=source_url_from_registry(source),
                source_artifact="config/source_registry.json",
                reason=clean(source.get("automation_status") or source.get("publish_policy")),
                priority_score=priority,
            )
        )
    return rows


def dedupe_and_rank(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = clean(row.get("_dedupe"))
        if not key:
            continue
        current = by_key.get(key)
        if current is None or int(row.get("_priority_score", 99)) < int(current.get("_priority_score", 99)):
            by_key[key] = row
    ranked = sorted(by_key.values(), key=lambda item: (int(item.get("_priority_score", 99)), clean(item.get("lane")), clean(item.get("title"))))
    out: List[Dict[str, str]] = []
    for index, row in enumerate(ranked, 1):
        row.update(promotion_for(row))
        cleaned = {field: clean(row.get(field)) for field in FIELDS}
        cleaned["rank"] = str(index)
        out.append(cleaned)
    return out


def opportunity_sort_key(row: Dict[str, str]) -> tuple[int, int, int, int, str]:
    priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    return (
        priority_order.get(row.get("promotion_priority"), 9),
        -as_int(row.get("quality_score"), 0),
        -as_int(row.get("freshness_score"), 0),
        int(row.get("rank") or 9999),
        row.get("title", ""),
    )


def assign_story_opportunities(rows: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    clusters: List[List[Dict[str, str]]] = []
    for row in rows:
        if not clusterable_story_row(row):
            continue
        matched: List[Dict[str, str]] | None = None
        for cluster in clusters:
            if any(related_story_rows(row, existing) for existing in cluster):
                matched = cluster
                break
        if matched is None:
            clusters.append([row])
        else:
            matched.append(row)

    for cluster in clusters:
        ranked = sorted(cluster, key=opportunity_sort_key)
        representative = ranked[0]
        sources = sorted({clean(row.get("source_name")) for row in cluster if clean(row.get("source_name"))})
        urls = []
        seen_urls = set()
        for row in ranked:
            url = canonicalize(row.get("source_url", ""))
            if url and url not in seen_urls:
                urls.append(url)
                seen_urls.add(url)
        opportunity_id = "opp_" + lead_id([representative.get("title"), *sources, *urls])[:12]
        opportunity_title = representative.get("title", "")
        opportunity_reason = (
            f"Grouped {len(cluster)} related official/wire discovery leads from {', '.join(sources)}."
            if len(cluster) > 1
            else f"Single official/wire discovery lead from {sources[0] if sources else representative.get('source_name', 'source')}."
        )
        for row in cluster:
            row["story_opportunity_id"] = opportunity_id
            row["story_opportunity_title"] = opportunity_title
            row["story_opportunity_size"] = str(len(cluster))
            row["story_opportunity_sources"] = "; ".join(sources)
            row["story_opportunity_urls"] = "; ".join(urls[:6])
            row["story_opportunity_reason"] = opportunity_reason
    return clusters


def promotion_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    promotable = [
        row
        for row in rows
        if row.get("promotion_recommendation") in {"news_packet", "manual_story_candidate", "studio_brief"}
    ]
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in promotable:
        opportunity_id = clean(row.get("story_opportunity_id"))
        key = f"opportunity:{opportunity_id}" if opportunity_id and clusterable_story_row(row) else f"row:{row.get('rank') or row.get('title')}"
        grouped.setdefault(key, []).append(row)
    ranked = [sorted(group, key=opportunity_sort_key)[0] for group in grouped.values()]
    ranked = sorted(ranked, key=opportunity_sort_key)
    out: List[Dict[str, str]] = []
    for index, row in enumerate(ranked, 1):
        promoted = {field: clean(row.get(field)) for field in PROMOTION_FIELDS}
        promoted["promotion_rank"] = str(index)
        size = as_int(promoted.get("story_opportunity_size"), 0)
        if size > 1:
            promoted["promotion_reason"] = (
                f"{promoted['story_opportunity_reason']} Review the grouped evidence before choosing the final angle."
            )
            promoted["promotion_next_step"] = (
                "Review the grouped official/wire links, pick the strongest source-backed angle, then draft or refresh the target artifact manually."
            )
        out.append(promoted)
    return out


def build_payload() -> Dict[str, Any]:
    registry = read_json("config/source_registry.json", {"sources": []})
    rows = dedupe_and_rank(
        rows_from_manual_candidates()
        + rows_from_raw_manual_inbox()
        + rows_from_discovery_candidates()
        + rows_from_news_observations()
        + rows_from_registry_scans(registry)
    )
    story_opportunities = assign_story_opportunities(rows)
    counts = {
        "total": len(rows),
        "manual_leads": sum(1 for row in rows if row["lane"] == "manual_lead"),
        "official_free": sum(1 for row in rows if row["lane"] == "official_free"),
        "wire": sum(1 for row in rows if row["lane"] == "wire"),
        "gray_area_review": sum(1 for row in rows if row["lane"] == "gray_area_review"),
        "social_discovery": sum(1 for row in rows if row["lane"] == "social_discovery"),
        "discovery_only": sum(1 for row in rows if row["publish_posture"] == "discovery_only"),
        "publish_grade_review": sum(1 for row in rows if row["publish_posture"] == "publish_grade_review"),
        "blocked": sum(1 for row in rows if row["publish_posture"] == "blocked"),
        "promote_to_news_packets": sum(1 for row in rows if row["promotion_recommendation"] == "news_packet"),
        "promote_to_manual_story_candidates": sum(1 for row in rows if row["promotion_recommendation"] == "manual_story_candidate"),
        "promote_to_studio_briefs": sum(1 for row in rows if row["promotion_recommendation"] == "studio_brief"),
        "fresh_today_or_48h": sum(1 for row in rows if row["freshness_label"] in {"today", "last_48_hours"}),
        "stale_or_evergreen": sum(1 for row in rows if "stale" in row["freshness_label"] or "evergreen" in row["freshness_label"]),
        "quality_70_plus": sum(1 for row in rows if as_int(row["quality_score"]) >= 70),
        "story_opportunities": len(story_opportunities),
        "grouped_story_opportunities": sum(1 for cluster in story_opportunities if len(cluster) > 1),
    }
    promotions = promotion_rows(rows)
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "free_sources_only": True,
            "manual_only": True,
            "auto_publish_allowed": False,
            "paid_apis_required": False,
            "promotion_mode": "manual_recommendation_only",
        },
        "counts": counts,
        "rows": rows,
        "promotion_recommendations": promotions,
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    counts = payload["counts"]
    lines = [
        "# HSD Morning Source Discovery Board",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {payload['version']}",
        "",
        "## Counts",
        "",
        f"- Total queue rows: `{counts['total']}`",
        f"- Manual leads: `{counts['manual_leads']}`",
        f"- Official/free scan rows: `{counts['official_free']}`",
        f"- Wire rows: `{counts['wire']}`",
        f"- Gray-area review rows: `{counts['gray_area_review']}`",
        f"- Social discovery rows: `{counts['social_discovery']}`",
        f"- Discovery-only rows: `{counts['discovery_only']}`",
        f"- Promote to News packets: `{counts['promote_to_news_packets']}`",
        f"- Promote to manual story candidates: `{counts['promote_to_manual_story_candidates']}`",
        f"- Promote to Studio briefs: `{counts['promote_to_studio_briefs']}`",
        f"- Fresh today / last 48 hours: `{counts['fresh_today_or_48h']}`",
        f"- Stale or evergreen: `{counts['stale_or_evergreen']}`",
        f"- Quality 70+: `{counts['quality_70_plus']}`",
        f"- Story opportunities: `{counts['story_opportunities']}`",
        f"- Grouped story opportunities: `{counts['grouped_story_opportunities']}`",
        "",
        "## Promotion Recommendations",
        "",
    ]
    for row in payload["promotion_recommendations"][:25]:
        lines.append(
            f"{row['promotion_rank']}. `{row['promotion_priority']}` | `{row['promotion_recommendation']}` | "
            f"quality `{row.get('quality_score') or 'n/a'}` | `{row.get('freshness_label') or 'undated'}` | "
            f"{row['title']} | opportunity `{row.get('story_opportunity_size') or '1'}` source(s) | {row['promotion_next_step']}"
        )
    if not payload["promotion_recommendations"]:
        lines.append("No lead promotion recommendations found.")
    lines += [
        "",
        "## Queue",
        "",
    ]
    for row in payload["rows"][:40]:
        lines.append(
            f"{row['rank']}. `{row['lane']}` | `{row['review_status']}` | `{row['publish_posture']}` | "
            f"quality `{row.get('quality_score') or 'n/a'}` | `{row.get('freshness_label') or 'undated'}` | "
            f"{row['title']} | opportunity `{row.get('story_opportunity_size') or 'n/a'}` | {row['next_action']}"
        )
    if not payload["rows"]:
        lines.append("No source discovery rows found.")
    lines += [
        "",
        "## Policy",
        "",
        "- Free sources only.",
        "- Gray-area and social rows are discovery or review inputs until confirmed.",
        "- Official/wire story opportunities group related leads for review; original source rows remain visible.",
        "- Lead promotion is advisory only; the board does not write into News packets, manual story candidates, or Studio briefs.",
        "- Nothing in this board auto-publishes or auto-runs outside the local manual runner.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(payload: Dict[str, Any]) -> None:
    write_csv(OUT_CSV, payload["rows"], FIELDS)
    write_json(OUT_JSON, payload)
    write_text(OUT_MD, render_markdown(payload))
    write_csv(PROMOTION_CSV, payload["promotion_recommendations"], PROMOTION_FIELDS)
    write_json(PROMOTION_JSON, {
        "version": payload["version"],
        "generated_at_utc": payload["generated_at_utc"],
        "policy": payload["policy"],
        "counts": payload["counts"],
        "promotion_recommendations": payload["promotion_recommendations"],
    })
    write_text(PROMOTION_MD, render_promotion_markdown(payload))


def render_promotion_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# HSD Morning Lead Promotion Recommendations",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {payload['version']}",
        "",
        "## Recommendations",
        "",
    ]
    for row in payload["promotion_recommendations"]:
        lines.append(
            f"{row['promotion_rank']}. `{row['promotion_priority']}` | `{row['promotion_recommendation']}` | "
            f"quality `{row.get('quality_score') or 'n/a'}` | `{row.get('freshness_label') or 'undated'}` | "
            f"{row['title']} | opportunity `{row.get('story_opportunity_size') or '1'}` source(s) | "
            f"target: `{row['promotion_target']}` | {row['promotion_reason']}"
        )
    if not payload["promotion_recommendations"]:
        lines.append("No lead promotion recommendations found.")
    lines += [
        "",
        "## Policy",
        "",
        "- Manual recommendation only.",
        "- Related official/wire leads are grouped into one story opportunity before promotion ranking.",
        "- No automatic writes to News, manual story, or Studio artifacts.",
        "- No paid APIs, auto-runs, or auto-publishing.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps({
        "version": VERSION,
        "rows": payload["counts"]["total"],
        "promotion_recommendations": len(payload["promotion_recommendations"]),
        "output": OUT_CSV.as_posix(),
    }, indent=2))


if __name__ == "__main__":
    main()
