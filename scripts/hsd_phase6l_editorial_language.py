from __future__ import annotations

"""Phase 6L editorial language helper for Her Sports Daily graphics.

The helper is intentionally score-safe: it never invents stats, quotes, injuries,
or tactical details. It converts already-verified winner/loser/score facts into
short HSD-style public language and provides copy-quality validation helpers.
"""

import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "v1.0-phase6l-editorial-language"
PUBLIC_COPY_PASS = "passed_public_copy_quality"
PUBLIC_COPY_NEEDS_FIX = "needs_public_copy_quality"

BANNED_PUBLIC_PHRASES = [
    r"\bclosed with a\b",
    r"\bfinished\b.*\bpoints? clear\b",
    r"\bpoints? clear\b",
    r"\bpoints? victory\b",
    r"\bfinal margin\b",
    r"\bmargin\b",
    r"\bwhat fueled\b",
    r"\bseparation\b",
    r"\bwhat changed the game\b",
    r"\bfull box score review pending\b",
    r"\bfinal score confirmed\b",
    r"\bsurvived the finish\b",
]

TEAM_CITY_OVERRIDES = {
    "atlanta dream": "Atlanta",
    "chicago sky": "Chicago",
    "connecticut sun": "Connecticut",
    "dallas wings": "Dallas",
    "golden state valkyries": "Golden State",
    "indiana fever": "Indiana",
    "las vegas aces": "Las Vegas",
    "los angeles sparks": "Los Angeles",
    "minnesota lynx": "Minnesota",
    "new york liberty": "New York",
    "phoenix mercury": "Phoenix",
    "seattle storm": "Seattle",
    "toronto tempo": "Toronto",
    "washington mystics": "Washington",
}

TEAM_NICKNAME_OVERRIDES = {
    "atlanta dream": "Dream",
    "chicago sky": "Sky",
    "connecticut sun": "Sun",
    "dallas wings": "Wings",
    "golden state valkyries": "Valkyries",
    "indiana fever": "Fever",
    "las vegas aces": "Aces",
    "los angeles sparks": "Sparks",
    "minnesota lynx": "Lynx",
    "new york liberty": "Liberty",
    "phoenix mercury": "Mercury",
    "seattle storm": "Storm",
    "toronto tempo": "Tempo",
    "washington mystics": "Mystics",
}

# Verbs are deliberately short. User-approved target style: "Dallas Survives",
# not "Dallas survived the finish."
MARGIN_BANDS = [
    (3, "Survives", "survival"),
    (9, "Pulls Away", "control"),
    (19, "Handles Business", "control"),
    (999, "Rolls", "statement"),
]

MONTHS = {
    1: "JANUARY", 2: "FEBRUARY", 3: "MARCH", 4: "APRIL", 5: "MAY", 6: "JUNE",
    7: "JULY", 8: "AUGUST", 9: "SEPTEMBER", 10: "OCTOBER", 11: "NOVEMBER", 12: "DECEMBER",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def titleish(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    # Title case is good enough for team/city copy while preserving apostrophes.
    return " ".join(part[:1].upper() + part[1:].lower() for part in text.split())


def team_city(team: Any) -> str:
    key = norm(team)
    if key in TEAM_CITY_OVERRIDES:
        return TEAM_CITY_OVERRIDES[key]
    text = titleish(team)
    parts = text.split()
    return " ".join(parts[:-1]) if len(parts) > 1 else text


def team_nickname(team: Any) -> str:
    key = norm(team)
    if key in TEAM_NICKNAME_OVERRIDES:
        return TEAM_NICKNAME_OVERRIDES[key]
    text = titleish(team)
    parts = text.split()
    return parts[-1] if parts else text


def possessive(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    return f"{text}'" if text.upper().endswith("S") else f"{text}'S"


def parse_int(value: Any) -> Optional[int]:
    match = re.search(r"-?\d+", clean(value))
    return int(match.group(0)) if match else None


def score_margin(score_winner: Any, score_loser: Any) -> Optional[int]:
    winner = parse_int(score_winner)
    loser = parse_int(score_loser)
    if winner is None or loser is None:
        return None
    return max(0, winner - loser)


def margin_band(score_winner: Any, score_loser: Any) -> Tuple[str, str, Optional[int]]:
    margin = score_margin(score_winner, score_loser)
    if margin is None:
        return "final", "Gets It Done", None
    for ceiling, phrase, band in MARGIN_BANDS:
        if margin <= ceiling:
            return band, phrase, margin
    return "statement", "Rolls", margin


def scoreline(winner: Any, loser: Any, score_winner: Any, score_loser: Any) -> str:
    left = team_nickname(winner)
    right = team_nickname(loser)
    sw = clean(score_winner)
    sl = clean(score_loser)
    if left and right and sw and sl:
        return f"{left} {sw}, {right} {sl}."
    return ""


def hsd_result_language(winner: Any, loser: Any, score_winner: Any, score_loser: Any) -> Dict[str, Any]:
    city = team_city(winner) or titleish(winner) or "Winner"
    band, phrase, margin = margin_band(score_winner, score_loser)
    headline = f"{city} {phrase}"
    line = scoreline(winner, loser, score_winner, score_loser)
    if line:
        body = line
    elif margin is not None:
        body = f"{city} gets the result."
    else:
        body = f"{city} gets it done."
    if margin is None:
        cta = f"{headline}. Biggest takeaway?"
    elif margin <= 3:
        cta = f"{headline}. What swung it?"
    elif margin >= 20:
        cta = f"{headline}. Biggest reason?"
    else:
        cta = f"{headline}. What stood out?"
    public_copy = " | ".join(part for part in [headline, body, cta] if part)
    hits = banned_public_hits(public_copy)
    return {
        "editorial_headline": headline,
        "editorial_body": body,
        "editorial_scoreline": line,
        "editorial_cta_prompt": cta.upper(),
        "editorial_margin_band": band,
        "editorial_margin": "" if margin is None else str(margin),
        "public_copy": public_copy,
        "public_copy_banned_count": len(hits),
        "public_copy_banned_tokens": ";".join(hits),
        "public_copy_quality_status": PUBLIC_COPY_PASS if not hits else PUBLIC_COPY_NEEDS_FIX,
        "public_copy_quality_score": f"{max(0.0, 1.0 - 0.25 * len(hits)):.3f}",
    }


def banned_public_hits(text: Any, extra_patterns: Optional[Iterable[str]] = None) -> List[str]:
    value = clean(text).lower()
    patterns = list(BANNED_PUBLIC_PHRASES)
    if extra_patterns:
        patterns.extend(extra_patterns)
    hits: List[str] = []
    for pattern in patterns:
        if re.search(pattern, value):
            hits.append(pattern)
    return sorted(set(hits))


def public_date(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            parsed = datetime.strptime(text.title(), fmt)
            return f"{MONTHS[parsed.month]} {parsed.day}, {parsed.year}"
        except ValueError:
            pass
    # Already-public copy like JUNE 20, 2026 is acceptable.
    return text.upper()


def validate_public_copy_fields(item: Dict[str, Any], extra_patterns: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    copy = " | ".join(
        clean(item.get(key))
        for key in [
            "editorial_headline",
            "editorial_body",
            "editorial_scoreline",
            "editorial_cta_prompt",
            "content_module_title",
            "content_module_body",
            "content_module_prompt",
            "story_prompt",
            "story_cta_label",
            "story_cta_body",
            "rendered_copy",
        ]
        if clean(item.get(key))
    )
    hits = banned_public_hits(copy, extra_patterns=extra_patterns)
    return {
        "public_copy_quality_status": PUBLIC_COPY_PASS if not hits else PUBLIC_COPY_NEEDS_FIX,
        "public_copy_quality_score": f"{max(0.0, 1.0 - 0.25 * len(hits)):.3f}",
        "public_copy_banned_count": len(hits),
        "public_copy_banned_tokens": ";".join(hits),
        "public_copy": copy,
    }
