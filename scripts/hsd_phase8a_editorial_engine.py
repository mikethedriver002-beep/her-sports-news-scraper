from __future__ import annotations

"""Phase 8A sport-specific, fit-safe editorial language engine for HSD.

Phase 8A replaces generic fallback language with sport-mechanic copy, ranked
fit variants, duplicate-clause checks, and hard generic-language blocking.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

try:
    from hsd_phase7_editorial_engine import (
        clean,
        slug,
        normalize_event as phase7_normalize_event,
        entity_short,
        possessive,
        normalize_sport,
    )
except Exception:  # pragma: no cover
    def clean(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()
    def slug(value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "event"
    def normalize_sport(value: Any, league: Any = "") -> str:
        return clean(value or league).lower()
    def entity_short(name: Any, sport_id: str = "", preferred: Any = "") -> str:
        return clean(preferred) or clean(name).split()[-1] if sport_id in {"tennis", "lpga"} else (clean(preferred) or clean(name))
    def possessive(value: Any) -> str:
        text = clean(value)
        return f"{text}'" if text.lower().endswith("s") else f"{text}'S"
    def phase7_normalize_event(raw: Mapping[str, Any]) -> Dict[str, Any]:
        event = dict(raw)
        event.setdefault("sport_id", normalize_sport(event.get("sport_id") or event.get("sport"), event.get("league")))
        event.setdefault("kind", clean(event.get("kind") or event.get("event_kind") or "preview").lower())
        event.setdefault("primary_name", clean(event.get("primary_name") or event.get("away_name") or event.get("winner_name")))
        event.setdefault("secondary_name", clean(event.get("secondary_name") or event.get("home_name") or event.get("loser_name")))
        event.setdefault("primary_short", entity_short(event.get("primary_name"), event.get("sport_id")))
        event.setdefault("secondary_short", entity_short(event.get("secondary_name"), event.get("sport_id")))
        event.setdefault("winner_short", entity_short(event.get("winner_name") or event.get("primary_name"), event.get("sport_id")))
        event.setdefault("scoreline", clean(event.get("scoreline")))
        event.setdefault("event_id", slug("-".join([event.get("sport_id", ""), event.get("primary_name", ""), event.get("secondary_name", ""), event.get("kind", "preview")])) )
        return event

VERSION = "v1.0-phase8a-sport-specific-fit-safe-editorial-engine"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = ROOT / "config/graphics/v5/phase8a/phrase_library_v1.json"
SUPPORTED_SPORTS = {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"}
SUPPORTED_KINDS = {"preview", "spotlight", "result", "story", "watch_point", "team_spotlight_fallback", "match_spotlight", "round_spotlight"}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "at", "with", "can", "who", "what", "where", "does", "do", "is", "are", "will", "this", "that", "their", "game", "match", "round",
}


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def stable_index(seed: str, count: int) -> int:
    if count <= 1:
        return 0
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12], 16) % count


def normalize_kind(kind: Any, variant: str = "") -> str:
    raw = clean(variant or kind).lower()
    if raw in {"watch_point", "player", "preview_card"}:
        return "preview"
    if raw in {"team_spotlight_fallback", "team_spotlight", "match_spotlight", "round_spotlight", "spotlight"}:
        return "spotlight"
    if raw in {"final", "recap", "result"}:
        return "result"
    if raw in SUPPORTED_KINDS:
        return raw
    return "story"


def normalize_event(raw: Mapping[str, Any]) -> Dict[str, Any]:
    event = phase7_normalize_event(raw)
    sport_id = clean(event.get("sport_id"))
    if sport_id not in SUPPORTED_SPORTS:
        sport_id = normalize_sport(raw.get("sport_id") or raw.get("sport"), raw.get("league"))
    if sport_id not in SUPPORTED_SPORTS:
        sport_id = "wnba"
    event["sport_id"] = sport_id
    event["kind"] = normalize_kind(event.get("kind") or raw.get("event_kind"), clean(raw.get("variant")))
    if not clean(event.get("primary_short")):
        event["primary_short"] = entity_short(event.get("primary_name"), sport_id, raw.get("primary_short"))
    if not clean(event.get("secondary_short")):
        event["secondary_short"] = entity_short(event.get("secondary_name"), sport_id, raw.get("secondary_short"))
    if not clean(event.get("winner_short")):
        event["winner_short"] = entity_short(event.get("winner_name") or event.get("primary_name"), sport_id, raw.get("winner_short"))
    if not clean(event.get("loser_short")):
        event["loser_short"] = entity_short(event.get("loser_name") or event.get("secondary_name"), sport_id, raw.get("loser_short"))
    return event


def format_value(raw: str, event: Mapping[str, Any]) -> str:
    primary = clean(event.get("primary_short") or entity_short(event.get("primary_name"), clean(event.get("sport_id"))))
    secondary = clean(event.get("secondary_short") or entity_short(event.get("secondary_name"), clean(event.get("sport_id"))))
    winner = clean(event.get("winner_short") or primary)
    loser = clean(event.get("loser_short") or secondary)
    scoreline = clean(event.get("scoreline") or event.get("score_display")) or (f"{winner} over {loser}." if winner and loser else "FINAL.")
    values = {
        "primary_short": primary,
        "secondary_short": secondary,
        "away_short": primary,
        "home_short": secondary,
        "winner_short": winner,
        "loser_short": loser,
        "primary_possessive": possessive(primary),
        "secondary_possessive": possessive(secondary),
        "winner_possessive": possessive(winner),
        "scoreline": scoreline,
        "source_headline": clean(event.get("source_headline") or event.get("headline") or event.get("title")),
        "verified_angle": clean(event.get("verified_angle") or event.get("angle")) or "THE SPORT-SPECIFIC QUESTION COMES FIRST.",
    }
    try:
        return clean(raw.format_map(values))
    except Exception:
        return clean(raw)


def text_tokens(value: Any) -> Set[str]:
    return {token for token in re.findall(r"[A-Z0-9]+", clean(value).upper()) if token.lower() not in STOP_WORDS and len(token) > 2}


def similarity(a: Any, b: Any) -> float:
    ta, tb = text_tokens(a), text_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


def phrase_hits(copy: Mapping[str, Any], banned: Sequence[str]) -> List[str]:
    combined = " | ".join(clean(copy.get(field)) for field in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"])
    upper = combined.upper()
    return sorted({clean(token).upper() for token in banned if clean(token) and clean(token).upper() in upper})


def has_mechanic(copy: Mapping[str, Any], sport_id: str, library: Mapping[str, Any]) -> bool:
    terms = [clean(term).upper() for term in ((library.get("mechanic_terms_by_sport") or {}).get(sport_id) or [])]
    combined = " | ".join(clean(copy.get(field)).upper() for field in ["debate_question", "watch_title", "watch_body", "cta"])
    return any(term and term in combined for term in terms)


def fit_select(values: Sequence[str], event: Mapping[str, Any], limit: int, banned: Sequence[str], fallback: str = "") -> str:
    formatted = [format_value(value, event) for value in values if clean(value)]
    if fallback and fallback not in formatted:
        formatted.append(fallback)
    for value in formatted:
        if len(value) <= limit and not phrase_hits({"debate_question": value, "watch_title": value, "watch_body": value, "cta": value}, banned):
            return value
    for value in sorted(formatted, key=len):
        if not phrase_hits({"debate_question": value, "watch_title": value, "watch_body": value, "cta": value}, banned):
            return value[:limit].rstrip(" ,.;:!?-")
    return (fallback or "WATCH THE SPORT-SPECIFIC EDGE.")[:limit]


def choose_pattern(event: Mapping[str, Any], library: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
    sport_id = clean(event.get("sport_id"))
    sport = (library.get("sports") or {}).get(sport_id) or {}
    patterns = sport.get(kind) or sport.get("story") or []
    if not patterns:
        raise ValueError(f"No Phase 8A phrase patterns for {sport_id}/{kind}")
    return patterns[stable_index(f"{event.get('event_id')}|{sport_id}|{kind}|phase8a", len(patterns))]


def generate_editorial(raw_event: Mapping[str, Any], policy_path: Optional[Path] = None, variant: str = "", context: str = "review_card") -> Dict[str, Any]:
    library = read_json(policy_path or DEFAULT_LIBRARY)
    event = normalize_event({**raw_event, "variant": variant})
    sport_id = clean(event.get("sport_id"))
    kind = normalize_kind(variant or event.get("kind"))
    if kind not in {"preview", "spotlight", "result", "story"}:
        kind = "story"
    pattern = choose_pattern(event, library, kind)
    banned = library.get("global_banned_patterns") or []
    limits = ((library.get("fit_limits") or {}).get(context) or (library.get("fit_limits") or {}).get("review_card") or {})
    copy = {
        "editorial_headline": fit_select([clean(pattern.get("editorial_headline"))], event, int(limits.get("editorial_headline") or 52), banned),
        "debate_question": fit_select(pattern.get("debate_question_variants") or [clean(pattern.get("debate_question"))], event, int(limits.get("debate_question") or 58), banned),
        "watch_title": fit_select(pattern.get("watch_title_variants") or [clean(pattern.get("watch_title"))], event, int(limits.get("watch_title") or 32), banned),
        "watch_body": fit_select(pattern.get("watch_body_variants") or [clean(pattern.get("watch_body"))], event, int(limits.get("watch_body") or 88), banned),
        "cta": fit_select(pattern.get("cta_variants") or [clean(pattern.get("cta"))], event, int(limits.get("cta") or 52), banned),
    }
    quality = editorial_quality(copy, event, library)
    public_copy = " | ".join(copy[field] for field in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"] if clean(copy.get(field)))
    return {
        "phase8a_editorial_version": VERSION,
        "phase8a_editorial_sport_id": sport_id,
        "phase8a_editorial_kind": kind,
        **event,
        **copy,
        **quality,
        "phase8a_editorial_public_copy": public_copy,
        # Phase 7 compatibility fields so existing Phase 7 review-card code can reuse Phase 8A safely.
        "phase7_editorial_version": VERSION,
        "phase7_editorial_sport_id": sport_id,
        "phase7_editorial_kind": kind,
        "phase7_editorial_quality_status": "passed_phase7_editorial_quality" if quality["phase8a_editorial_quality_status"] == "passed_phase8a_editorial_quality" else "blocked_phase7_editorial_quality",
        "phase7_editorial_quality_score": quality["phase8a_editorial_quality_score"],
        "phase7_editorial_quality_reasons": quality["phase8a_editorial_quality_reasons"],
        "phase7_editorial_banned_count": quality["phase8a_editorial_banned_count"],
        "phase7_editorial_banned_tokens": quality["phase8a_editorial_banned_tokens"],
        "phase7_editorial_public_copy": public_copy,
    }


def editorial_quality(copy: Mapping[str, Any], event: Mapping[str, Any], library: Mapping[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    banned = phrase_hits(copy, library.get("global_banned_patterns") or [])
    if banned:
        reasons.append("generic_or_banned_editorial_copy")
    if not has_mechanic(copy, clean(event.get("sport_id")), library) and clean(event.get("kind")) in {"preview", "spotlight"}:
        reasons.append("missing_sport_mechanic")
    fields = [clean(copy.get(field)) for field in ["debate_question", "watch_title", "watch_body", "cta"] if clean(copy.get(field))]
    duplicates: List[str] = []
    for i, left in enumerate(fields):
        for right in fields[i + 1:]:
            sim = similarity(left, right)
            if min(len(text_tokens(left)), len(text_tokens(right))) >= 4 and sim >= float(library.get("duplicate_similarity_threshold") or 0.62):
                duplicates.append(f"{sim:.2f}:{left[:28]}~{right[:28]}")
    if duplicates:
        reasons.append("duplicate_editorial_clause")
    combined = " | ".join(clean(copy.get(field)) for field in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"])
    if "{" in combined or "}" in combined:
        reasons.append("unexpanded_editorial_placeholder")
    limits = (library.get("fit_limits") or {}).get("review_card") or {}
    for field, limit in limits.items():
        value = clean(copy.get(field))
        if value and int(limit) and len(value) > int(limit):
            reasons.append(f"{field}_fit_limit_exceeded:{len(value)}>{limit}")
    unique = sorted(set(reasons))
    score = max(0.0, 1.0 - 0.18 * len(unique))
    return {
        "phase8a_editorial_quality_status": "passed_phase8a_editorial_quality" if not unique else "blocked_phase8a_editorial_quality",
        "phase8a_editorial_quality_score": f"{score:.3f}",
        "phase8a_editorial_quality_reasons": ";".join(unique),
        "phase8a_editorial_banned_count": len(banned),
        "phase8a_editorial_banned_tokens": ";".join(banned),
        "phase8a_duplicate_clause_count": len(duplicates),
        "phase8a_duplicate_clause_details": ";".join(duplicates[:5]),
    }


def event_from_renderer_row(row: Mapping[str, Any], variant: str = "watch_point") -> Dict[str, Any]:
    def first(keys: Iterable[str]) -> str:
        for key in keys:
            value = clean(row.get(key))
            if value:
                return value
        return ""
    away = first(["away_team_name", "away_team_display", "away_team", "team_away", "primary_name"])
    home = first(["home_team_name", "home_team_display", "home_team", "team_home", "secondary_name"])
    headline = first(["headline", "title", "source_headline"])
    if (not away or not home) and " at " in headline:
        away, home = [clean(part) for part in headline.split(" at ", 1)]
    return normalize_event({
        "event_id": first(["event_id", "event_uid", "source_event_id", "canonical_key", "source_id"]) or slug(headline or f"{away}-{home}"),
        "sport_id": "wnba",
        "kind": "spotlight" if variant in {"spotlight", "team_spotlight_fallback"} else "preview",
        "primary_name": away,
        "secondary_name": home,
        "primary_short": first(["away_team_short", "primary_short"]),
        "secondary_short": first(["home_team_short", "secondary_short"]),
        "source_headline": headline or f"{away} at {home}",
        "verified_angle": first(["verified_angle", "angle", "watch_angle", "editorial_note"]),
    })


def generate_renderer_editorial(row: Mapping[str, Any], variant: str = "watch_point", policy_path: Optional[Path] = None) -> Dict[str, Any]:
    event = event_from_renderer_row(row, variant=variant)
    normalized_variant = "spotlight" if variant in {"spotlight", "team_spotlight_fallback"} else "preview"
    return generate_editorial(event, policy_path=policy_path, variant=normalized_variant, context="renderer_tonight")

__all__ = [
    "VERSION", "SUPPORTED_SPORTS", "clean", "slug", "normalize_event", "generate_editorial", "generate_renderer_editorial", "editorial_quality", "similarity", "text_tokens",
]
