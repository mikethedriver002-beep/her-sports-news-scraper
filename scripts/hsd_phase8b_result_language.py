from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

VERSION = "v1.0-phase8b-final-score-result-language-engine"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/graphics/v5/phase8b/final_score_language_v1.json"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "event"


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


def short_name(name: Any) -> str:
    text = clean(name)
    if not text:
        return ""
    replacements = {
        "Connecticut Sun": "Sun",
        "Chicago Sky": "Sky",
        "Atlanta Dream": "Dream",
        "Toronto Tempo": "Tempo",
        "Indiana Fever": "Fever",
        "Phoenix Mercury": "Mercury",
        "Dallas Wings": "Wings",
        "Seattle Storm": "Storm",
        "Los Angeles Sparks": "Sparks",
        "New York Liberty": "Liberty",
        "Las Vegas Aces": "Aces",
        "Golden State Valkyries": "Valkyries",
        "Minnesota Lynx": "Lynx",
        "Washington Mystics": "Mystics",
        "Portland Fire": "Fire",
    }
    return replacements.get(text, text.split()[-1] if len(text.split()) > 1 else text)


def parse_headline(headline: str) -> Tuple[str, str]:
    text = clean(headline)
    for sep in [" beat ", " beats ", " defeated ", " def. ", " over "]:
        if sep in text:
            left, right = text.split(sep, 1)
            return clean(left), clean(right)
    return clean(text), ""


def as_int(value: Any) -> Optional[int]:
    text = clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def margin(row: Mapping[str, Any]) -> Optional[int]:
    direct = as_int(row.get("editorial_margin"))
    if direct is not None:
        return abs(direct)
    ws = as_int(row.get("winner_score") or row.get("primary_score"))
    ls = as_int(row.get("loser_score") or row.get("secondary_score"))
    if ws is not None and ls is not None:
        return abs(ws - ls)
    scoreline = clean(row.get("scoreline") or row.get("editorial_scoreline"))
    nums = [int(n) for n in re.findall(r"\b\d+\b", scoreline)]
    if len(nums) >= 2:
        return abs(nums[0] - nums[1])
    return None


def normalize_result_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    headline = clean(row.get("headline") or row.get("event_title") or row.get("source_headline"))
    winner = clean(row.get("winner_name") or row.get("winner") or row.get("primary_name"))
    loser = clean(row.get("loser_name") or row.get("loser") or row.get("secondary_name"))
    if (not winner or not loser) and headline:
        parsed_winner, parsed_loser = parse_headline(headline)
        winner = winner or parsed_winner
        loser = loser or parsed_loser
    winner_short = clean(row.get("winner_short") or row.get("winner_short_name") or short_name(winner))
    loser_short = clean(row.get("loser_short") or short_name(loser))
    scoreline = clean(row.get("scoreline") or row.get("score_display") or row.get("editorial_scoreline") or row.get("content_module_body"))
    if not scoreline:
        ws = clean(row.get("winner_score") or row.get("primary_score"))
        ls = clean(row.get("loser_score") or row.get("secondary_score"))
        if ws and ls and winner_short and loser_short:
            scoreline = f"{winner_short} {ws}, {loser_short} {ls}."
    sport_id = clean(row.get("sport_id") or row.get("phase8a_editorial_sport_id") or row.get("league") or "wnba").lower()
    if sport_id in {"wta", "women's tennis", "womens_tennis"}:
        sport_id = "tennis"
    if sport_id in {"softball", "college_softball"}:
        sport_id = "ncaa_softball"
    return {
        **dict(row),
        "sport_id": sport_id,
        "winner_name": winner,
        "loser_name": loser,
        "winner_short": winner_short,
        "loser_short": loser_short,
        "scoreline": scoreline,
        "margin": margin(row),
        "headline": headline or (f"{winner} beat {loser}" if winner and loser else clean(row.get("source_headline"))),
    }


def band_for(row: Mapping[str, Any]) -> str:
    m = row.get("margin")
    sport = clean(row.get("sport_id"))
    if sport != "wnba":
        return "standard"
    if isinstance(m, int):
        if m <= 5:
            return "close"
        if m >= 16:
            return "blowout"
    return "standard"


def fmt(template: str, row: Mapping[str, Any]) -> str:
    values = {
        "winner_short": clean(row.get("winner_short")).upper(),
        "loser_short": clean(row.get("loser_short")).upper(),
        "winner_name": clean(row.get("winner_name")),
        "loser_name": clean(row.get("loser_name")),
        "scoreline": clean(row.get("scoreline")),
        "headline": clean(row.get("headline")),
    }
    try:
        return clean(template.format_map(values))
    except Exception:
        return clean(template)


def no_mid_word_trim(value: str, limit: int) -> str:
    value = clean(value)
    if len(value) <= limit:
        return value
    trimmed = value[:limit].rstrip(" ,.;:!?-")
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip(" ,.;:!?-")
    if value.endswith("?") and not trimmed.endswith("?") and len(trimmed) + 1 <= limit:
        trimmed += "?"
    return trimmed


def choose(values: Sequence[str], row: Mapping[str, Any], limit: int, seed: str) -> str:
    formatted = [fmt(v, row) for v in values if clean(v)]
    if not formatted:
        return "RESULT LEVER"
    start = stable_index(seed, len(formatted))
    ordered = formatted[start:] + formatted[:start]
    for value in ordered:
        if len(value) <= limit:
            return value
    return no_mid_word_trim(ordered[0], limit)


def generate_result_editorial(raw_row: Mapping[str, Any], config_path: Optional[Path] = None) -> Dict[str, Any]:
    config = read_json(config_path or DEFAULT_CONFIG)
    row = normalize_result_row(raw_row)
    sport = clean(row.get("sport_id")) or "wnba"
    sport_cfg = ((config.get("sports") or {}).get(sport) or (config.get("sports") or {}).get("wnba") or {})
    band = band_for(row)
    patterns = sport_cfg.get(band) or sport_cfg.get("standard") or {}
    limits = config.get("fit_limits") or {}
    seed = clean(row.get("item_id") or row.get("event_id") or row.get("headline") or row.get("scoreline"))
    result_label = choose(patterns.get("label_variants") or ["RESULT LEVER"], row, int(limits.get("result_label") or 28), seed + "label")
    body = choose(patterns.get("body_variants") or ["{winner_short} found the result-shaping stretch."], row, int(limits.get("body") or 72), seed + "body")
    cta = choose(patterns.get("cta_variants") or ["Which stretch decided it?"], row, int(limits.get("cta") or 50), seed + "cta")
    headline = choose(["{winner_short} OVER {loser_short}", "{winner_short} TAKES IT", "{winner_short} CLOSES"], row, int(limits.get("headline") or 42), seed + "headline")
    scoreline = no_mid_word_trim(clean(row.get("scoreline")), int(limits.get("scoreline") or 46))
    public_copy = " | ".join(v for v in [clean(row.get("headline")), headline, scoreline, result_label, body, cta] if v)
    banned = [b for b in config.get("global_banned_patterns") or [] if clean(b).upper() in public_copy.upper()]
    return {
        "phase8b_result_language_version": VERSION,
        "phase8b_result_language_status": "passed_phase8b_result_language" if not banned else "blocked_phase8b_result_language",
        "phase8b_result_language_reasons": "" if not banned else "banned_result_language:" + ";".join(banned),
        "phase8b_result_sport_id": sport,
        "phase8b_result_band": band,
        "phase8b_result_headline": headline,
        "phase8b_result_label": result_label,
        "phase8b_result_body": body,
        "phase8b_result_cta": cta,
        "phase8b_result_scoreline": scoreline,
        "phase8b_result_public_copy": public_copy,
        "phase8b_result_banned_count": len(banned),
        "phase8b_result_banned_tokens": ";".join(banned),
    }


def validate_result_editorial(ed: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    public_copy = clean(ed.get("phase8b_result_public_copy"))
    if clean(ed.get("phase8b_result_banned_count")) and int(ed.get("phase8b_result_banned_count") or 0) > 0:
        reasons.append("banned_result_language")
    if public_copy.upper().count("FINAL READ") > 0:
        reasons.append("final_read_present")
    if "CLEANEST STRETCH" in public_copy.upper():
        reasons.append("cleanest_stretch_present")
    label = clean(ed.get("phase8b_result_label")).upper()
    body = clean(ed.get("phase8b_result_body")).upper()
    if label and body and label in body:
        reasons.append("label_repeated_in_body")
    return reasons
