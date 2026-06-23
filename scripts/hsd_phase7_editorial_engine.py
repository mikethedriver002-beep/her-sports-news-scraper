from __future__ import annotations

"""Shared sport-aware editorial language engine for HSD Phase 7.

The engine is deliberately fact-light. It converts verified event identity and
optional verified packet language into matchup-specific public copy without
inventing statistics, injuries, form, tactics, or player identity.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

VERSION = "v1.0-phase7-multisport-editorial-engine"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/graphics/v5/phase7/editorial_policy_v1.json"
SUPPORTED_SPORTS = {
    "wnba",
    "nwsl",
    "uswnt",
    "tennis",
    "lpga",
    "ncaa_softball",
    "volleyball",
}
SUPPORTED_KINDS = {"preview", "spotlight", "result", "story"}

CITY_OVERRIDES = {
    "Atlanta Dream": "Atlanta",
    "Chicago Sky": "Chicago",
    "Connecticut Sun": "Connecticut",
    "Dallas Wings": "Dallas",
    "Golden State Valkyries": "Golden State",
    "Indiana Fever": "Indiana",
    "Las Vegas Aces": "Vegas",
    "Los Angeles Sparks": "Los Angeles",
    "Minnesota Lynx": "Minnesota",
    "New York Liberty": "New York",
    "Phoenix Mercury": "Phoenix",
    "Seattle Storm": "Seattle",
    "Toronto Tempo": "Toronto",
    "Washington Mystics": "Washington",
    "United States": "USA",
    "United States Women": "USA",
    "United States Women's National Team": "USA",
    "The Field": "The Field",
}

SPORT_ALIASES = {
    "basketball": "wnba",
    "women's basketball": "wnba",
    "womens basketball": "wnba",
    "wnba": "wnba",
    "nwsl": "nwsl",
    "women's soccer": "nwsl",
    "womens soccer": "nwsl",
    "soccer": "nwsl",
    "uswnt": "uswnt",
    "us women": "uswnt",
    "us women's national team": "uswnt",
    "women's tennis": "tennis",
    "womens tennis": "tennis",
    "wta": "tennis",
    "tennis": "tennis",
    "women's golf": "lpga",
    "womens golf": "lpga",
    "golf": "lpga",
    "lpga": "lpga",
    "softball": "ncaa_softball",
    "ncaa softball": "ncaa_softball",
    "college softball": "ncaa_softball",
    "volleyball": "volleyball",
    "women's volleyball": "volleyball",
    "womens volleyball": "volleyball",
    "ncaa volleyball": "volleyball",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "event"


def as_bool(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def normalize_sport(value: Any, league: Any = "") -> str:
    candidates = [clean(value).lower(), clean(league).lower()]
    for candidate in candidates:
        if candidate in SUPPORTED_SPORTS:
            return candidate
        if candidate in SPORT_ALIASES:
            mapped = SPORT_ALIASES[candidate]
            if mapped == "nwsl" and "uswnt" in " ".join(candidates):
                return "uswnt"
            return mapped
        if "uswnt" in candidate or "united states women" in candidate:
            return "uswnt"
        if "nwsl" in candidate:
            return "nwsl"
        if "wnba" in candidate:
            return "wnba"
        if "tennis" in candidate or candidate == "wta":
            return "tennis"
        if "lpga" in candidate or "women's golf" in candidate or "womens golf" in candidate:
            return "lpga"
        if "softball" in candidate:
            return "ncaa_softball"
        if "volleyball" in candidate:
            return "volleyball"
    return ""


def entity_short(name: Any, sport_id: str = "", preferred: Any = "") -> str:
    preferred_text = clean(preferred)
    if preferred_text:
        return preferred_text
    full = clean(name)
    if not full:
        return ""
    if full in CITY_OVERRIDES:
        return CITY_OVERRIDES[full]
    if sport_id in {"tennis", "lpga"}:
        words = [part for part in re.split(r"\s+", full) if part]
        return words[-1] if words else full
    suffixes = {
        "Dream", "Sky", "Sun", "Wings", "Valkyries", "Fever", "Aces", "Sparks",
        "Lynx", "Liberty", "Mercury", "Storm", "Tempo", "Mystics", "Pride", "Spirit",
        "Courage", "Current", "Wave", "Reign", "Dash", "Thorns", "Royals", "Bay", "Gotham",
        "Sooners", "Longhorns", "Cornhuskers", "Badgers", "Tigers", "Bruins", "Cardinal",
    }
    words = full.split()
    if len(words) >= 2 and words[-1] in suffixes:
        return " ".join(words[:-1])
    return full


def possessive(value: Any) -> str:
    text = clean(value)
    if not text:
        return "TEAM'S"
    return f"{text}'" if text.lower().endswith("s") else f"{text}'S"


def _stable_index(seed: str, count: int) -> int:
    if count <= 1:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % count


def _safe_verified_angle(value: Any, banned: Iterable[str], maximum: int = 92) -> str:
    text = clean(value)
    if not text or len(text) > maximum:
        return ""
    upper = text.upper()
    if any(clean(token).upper() in upper for token in banned if clean(token)):
        return ""
    if any(token in upper for token in ["TBA", "TBD", "UNKNOWN", "PENDING"]):
        return ""
    return text


def normalize_event(raw: Mapping[str, Any]) -> Dict[str, Any]:
    event = dict(raw)
    sport_id = normalize_sport(event.get("sport_id") or event.get("sport"), event.get("league"))
    kind = clean(event.get("kind") or event.get("event_kind") or event.get("story_type")).lower()
    if kind not in SUPPORTED_KINDS:
        hay = " ".join([
            kind,
            clean(event.get("content_family")),
            clean(event.get("source_headline")),
            clean(event.get("scoreline")),
        ]).lower()
        if any(token in hay for token in ["final", "result", "recap", "beat", "wins", "won"]):
            kind = "result"
        elif any(token in hay for token in ["preview", "tonight", "upcoming", "watch"]):
            kind = "preview"
        else:
            kind = "story"

    primary = clean(
        event.get("primary_name")
        or event.get("away_name")
        or event.get("winner_name")
        or event.get("team_name")
        or event.get("athlete_name")
    )
    secondary = clean(
        event.get("secondary_name")
        or event.get("home_name")
        or event.get("loser_name")
        or event.get("opponent_name")
    )
    winner = clean(event.get("winner_name")) or (primary if kind == "result" else "")
    loser = clean(event.get("loser_name")) or (secondary if kind == "result" else "")
    event_id = clean(event.get("event_id") or event.get("packet_id") or event.get("source_id"))
    if not event_id:
        event_id = f"phase7-{slug(sport_id)}-{slug(primary)}-{slug(secondary)}-{slug(kind)}"

    normalized = {
        **event,
        "event_id": event_id,
        "sport_id": sport_id,
        "kind": kind,
        "primary_name": primary,
        "secondary_name": secondary,
        "winner_name": winner,
        "loser_name": loser,
        "primary_short": entity_short(primary, sport_id, event.get("primary_short")),
        "secondary_short": entity_short(secondary, sport_id, event.get("secondary_short")),
        "winner_short": entity_short(winner, sport_id, event.get("winner_short") or event.get("primary_short")),
        "loser_short": entity_short(loser, sport_id, event.get("loser_short") or event.get("secondary_short")),
        "scoreline": clean(event.get("scoreline") or event.get("scores") or event.get("score_display")),
        "source_headline": clean(event.get("source_headline") or event.get("headline") or event.get("title")),
        "verified_angle": clean(event.get("verified_angle") or event.get("angle") or event.get("summary")),
        "fixture_only": as_bool(event.get("fixture_only")),
    }
    return normalized


def _format_pattern(pattern: Mapping[str, Any], event: Mapping[str, Any], banned: Iterable[str]) -> Dict[str, str]:
    primary_short = clean(event.get("primary_short")) or entity_short(event.get("primary_name"), clean(event.get("sport_id")))
    secondary_short = clean(event.get("secondary_short")) or entity_short(event.get("secondary_name"), clean(event.get("sport_id")))
    winner_short = clean(event.get("winner_short")) or primary_short
    loser_short = clean(event.get("loser_short")) or secondary_short
    verified_angle = _safe_verified_angle(event.get("verified_angle"), banned)
    source_headline = clean(event.get("source_headline"))
    scoreline = clean(event.get("scoreline")) or (f"{winner_short} over {loser_short}." if winner_short and loser_short else "FINAL.")

    values = {
        "primary_short": primary_short,
        "secondary_short": secondary_short,
        "away_short": primary_short,
        "home_short": secondary_short,
        "winner_short": winner_short,
        "loser_short": loser_short,
        "primary_possessive": possessive(primary_short),
        "secondary_possessive": possessive(secondary_short),
        "away_possessive": possessive(primary_short),
        "home_possessive": possessive(secondary_short),
        "winner_possessive": possessive(winner_short),
        "scoreline": scoreline,
        "source_headline": source_headline or f"{primary_short} {('VS' if secondary_short else '').strip()} {secondary_short}".strip(),
        "verified_angle": verified_angle or _story_fallback(clean(event.get("sport_id")), primary_short, secondary_short),
    }
    output: Dict[str, str] = {}
    for field in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"]:
        raw = clean(pattern.get(field))
        try:
            output[field] = clean(raw.format_map(values))
        except (KeyError, ValueError):
            output[field] = raw
    return output


def _story_fallback(sport_id: str, primary_short: str, secondary_short: str) -> str:
    subject = primary_short or secondary_short or "THIS STORY"
    fallbacks = {
        "wnba": f"THE NEXT QUESTION FOR {subject}.",
        "nwsl": f"THE TACTICAL QUESTION AROUND {subject}.",
        "uswnt": f"WHAT THIS CHANGES FOR {subject}.",
        "tennis": f"THE PATTERN TO WATCH FOR {subject}.",
        "lpga": f"THE COURSE QUESTION FOR {subject}.",
        "ncaa_softball": f"THE PRESSURE POINT FOR {subject}.",
        "volleyball": f"THE FIRST-CONTACT QUESTION FOR {subject}.",
    }
    return fallbacks.get(sport_id, f"THE NEXT QUESTION FOR {subject}.")


def editorial_quality(copy: Mapping[str, Any], event: Mapping[str, Any], policy: Mapping[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    banned_hits: List[str] = []
    combined = " | ".join(clean(copy.get(field)) for field in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"] if clean(copy.get(field)))
    upper = combined.upper()
    for pattern in policy.get("global_banned_patterns") or []:
        token = clean(pattern).upper()
        if token and token in upper:
            banned_hits.append(token)
    if banned_hits:
        reasons.append("generic_or_banned_editorial_copy")
    if not clean(copy.get("editorial_headline")):
        reasons.append("missing_editorial_headline")
    if not clean(copy.get("debate_question")):
        reasons.append("missing_debate_question")
    if not clean(copy.get("watch_title")):
        reasons.append("missing_watch_title")
    if not clean(copy.get("watch_body")):
        reasons.append("missing_watch_body")
    if "{" in combined or "}" in combined:
        reasons.append("unexpanded_editorial_placeholder")

    limits = policy.get("max_field_characters") or {}
    for field, limit in limits.items():
        value = clean(copy.get(field))
        try:
            maximum = int(limit)
        except Exception:
            maximum = 0
        if maximum and len(value) > maximum:
            reasons.append(f"{field}_too_long:{len(value)}>{maximum}")

    primary = clean(event.get("primary_short")).upper()
    secondary = clean(event.get("secondary_short")).upper()
    source_headline = clean(event.get("source_headline")).upper()
    if clean(event.get("kind")) in {"preview", "spotlight"}:
        entities = [value for value in [primary, secondary] if value and value not in {"THE FIELD", "OPPONENT"}]
        if entities and not any(value in upper for value in entities):
            reasons.append("copy_not_matchup_specific")
    if clean(event.get("kind")) == "story" and source_headline and source_headline not in upper:
        reasons.append("story_headline_not_preserved")

    unique_reasons = sorted(set(reasons))
    score = max(0.0, 1.0 - 0.16 * len(unique_reasons))
    return {
        "phase7_editorial_quality_status": "passed_phase7_editorial_quality" if not unique_reasons else "blocked_phase7_editorial_quality",
        "phase7_editorial_quality_score": f"{score:.3f}",
        "phase7_editorial_quality_reasons": ";".join(unique_reasons),
        "phase7_editorial_banned_count": len(set(banned_hits)),
        "phase7_editorial_banned_tokens": ";".join(sorted(set(banned_hits))),
        "phase7_editorial_public_copy": combined,
    }




def _result_headline_override(event: Mapping[str, Any]) -> str:
    sport_id = clean(event.get("sport_id"))
    winner = clean(event.get("winner_short") or event.get("primary_short"))
    if sport_id != "wnba" or not winner:
        return ""
    numbers = [int(value) for value in re.findall(r"\d+", clean(event.get("scoreline")))[:2]]
    if len(numbers) < 2:
        return ""
    margin = abs(numbers[0] - numbers[1])
    if margin <= 3:
        return f"{winner} SURVIVES"
    if margin <= 9:
        return f"{winner} PULLS AWAY"
    if margin <= 19:
        return f"{winner} HANDLES BUSINESS"
    return f"{winner} ROLLS"

def generate_editorial(raw_event: Mapping[str, Any], policy_path: Optional[Path] = None, variant: str = "") -> Dict[str, Any]:
    policy = read_json(policy_path or DEFAULT_POLICY)
    event = normalize_event(raw_event)
    sport_id = clean(event.get("sport_id"))
    kind = clean(variant or event.get("kind")).lower()
    if kind == "team_spotlight_fallback":
        kind = "spotlight"
    if kind not in SUPPORTED_KINDS:
        kind = "story"
    sport_policy = (policy.get("sports") or {}).get(sport_id, {})
    patterns = sport_policy.get(kind) or sport_policy.get("story") or []
    if not patterns:
        raise ValueError(f"No Phase 7 editorial patterns for sport={sport_id!r}, kind={kind!r}")
    index = _stable_index(f"{event.get('event_id')}|{sport_id}|{kind}", len(patterns))
    copy = _format_pattern(patterns[index], event, policy.get("global_banned_patterns") or [])
    result_override = _result_headline_override(event) if kind == "result" else ""
    if result_override:
        copy["editorial_headline"] = result_override

    # A verified, concise manual angle may replace the fallback body. It cannot
    # replace identity, score, or source truth and still passes the same denylist.
    verified = _safe_verified_angle(event.get("verified_angle"), policy.get("global_banned_patterns") or [], maximum=76)
    if verified and kind in {"preview", "spotlight", "story"}:
        primary = clean(event.get("primary_short")).upper()
        secondary = clean(event.get("secondary_short")).upper()
        verified_upper = verified.upper()
        if kind == "story" or any(value and value in verified_upper for value in [primary, secondary]):
            copy["watch_body"] = verified

    quality = editorial_quality(copy, event, policy)
    return {
        "phase7_editorial_version": VERSION,
        "phase7_editorial_sport_id": sport_id,
        "phase7_editorial_kind": kind,
        **event,
        **copy,
        **quality,
    }


def event_from_renderer_row(row: Mapping[str, Any], variant: str = "watch_point") -> Dict[str, Any]:
    def first(keys: Iterable[str]) -> str:
        for key in keys:
            value = clean(row.get(key))
            if value:
                return value
        return ""

    away = first(["away_team_name", "away_team_display", "away_team", "team_away"])
    home = first(["home_team_name", "home_team_display", "home_team", "team_home"])
    headline = first(["headline", "title"])
    if (not away or not home) and " at " in headline:
        away, home = [clean(part) for part in headline.split(" at ", 1)]
    if (not away or not home) and " vs " in headline.lower():
        parts = re.split(r"\s+vs\.?\s+", headline, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            away, home = clean(parts[0]), clean(parts[1])
    return normalize_event({
        "event_id": first(["event_id", "event_uid", "source_event_id", "canonical_key", "source_id"]) or slug(headline),
        "sport_id": "wnba",
        "kind": "spotlight" if variant in {"spotlight", "team_spotlight_fallback"} else "preview",
        "primary_name": away,
        "secondary_name": home,
        "primary_short": first(["away_team_short", "primary_short"]),
        "secondary_short": first(["home_team_short", "secondary_short"]),
        "source_headline": headline or f"{away} at {home}",
        "verified_angle": first(["verified_angle", "angle", "watch_angle", "editorial_note"]),
        "fixture_only": first(["fixture_only", "fixture_mode"]),
    })


def generate_renderer_editorial(row: Mapping[str, Any], variant: str = "watch_point", policy_path: Optional[Path] = None) -> Dict[str, Any]:
    event = event_from_renderer_row(row, variant=variant)
    return generate_editorial(event, policy_path=policy_path, variant="spotlight" if variant in {"spotlight", "team_spotlight_fallback"} else "preview")


__all__ = [
    "VERSION",
    "SUPPORTED_SPORTS",
    "SUPPORTED_KINDS",
    "clean",
    "slug",
    "normalize_sport",
    "normalize_event",
    "entity_short",
    "possessive",
    "generate_editorial",
    "generate_renderer_editorial",
    "editorial_quality",
]
