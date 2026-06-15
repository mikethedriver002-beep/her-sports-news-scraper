from __future__ import annotations

import csv
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path("data/asset_registry/wnba")
SOURCES = ROOT / "athlete_sources.csv"
ATHLETES = ROOT / "athletes.csv"
ALIASES = ROOT / "athlete_aliases.csv"
IMAGES = ROOT / "athlete_images.csv"
CANDIDATES = ROOT / "athlete_image_candidates.csv"
MATCH_REVIEW = ROOT / "athlete_image_match_review.csv"
MISSING_IMAGES = ROOT / "missing_athlete_images.csv"
REPORT_JSON = ROOT / "athlete_registry_report.json"
REPORT_MD = ROOT / "athlete_registry_report.md"
ROSTER_ENTITIES = ROOT / "roster_entities.csv"
ROSTER_NAMES = ROOT / "roster_names.csv"

ATHLETE_FIELDS = ["athlete_id", "league", "display_name", "team_id", "provider_player_id", "status", "source_url", "last_verified_utc", "notes"]
ALIAS_FIELDS = ["name_variant", "athlete_id", "type"]
IMAGE_FIELDS = ["athlete_id", "display_name", "team_id", "provider_player_id", "image_type", "file_path", "file_exists", "approved", "source_note", "last_verified_utc"]
CANDIDATE_FIELDS = ["candidate_id", "athlete_id", "display_name", "team_id", "provider_player_id", "source_url", "image_url", "image_type", "status", "notes"]
MATCH_FIELDS = ["team_id", "athlete_id", "display_name", "provider_player_id", "image_url", "match_method", "confidence", "status", "approval_target_path", "notes"]
MISSING_FIELDS = ["athlete_id", "display_name", "team_id", "required_image_type", "reason", "recommended_path"]
ROSTER_ENTITY_FIELDS = ["id", "league", "name", "display_name", "team_id", "status", "source_url", "last_verified_utc", "notes"]
ROSTER_NAME_FIELDS = ["name_variant", "entity_id", "type"]

STOP_PHRASES = [
    "download on the apple app store", "get it on google play", "privacy policy", "terms of use", "cookie policy",
    "league pass", "ticket central", "single game tickets", "season membership", "fan code", "atlanta dream",
    "chicago sky", "connecticut sun", "indiana fever", "new york liberty", "toronto tempo", "washington mystics",
    "dallas wings", "golden state valkyries", "las vegas aces", "los angeles sparks", "minnesota lynx",
    "phoenix mercury", "portland fire", "seattle storm",
]
POSITIONS = ["Guard-Forward", "Forward-Center", "Center-Forward", "Guard", "Forward", "Center"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def clean_name(value: str) -> str:
    name = clean(value)
    name = re.sub(r"\b(headshot|photo|image|portrait)\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip(" -–—|•\t\n\r")
    return name


def slug(value: str, sep: str = "_") -> str:
    return re.sub(r"[^a-z0-9]+", sep, clean_name(value).lower()).strip(sep)


def title_from_slug(value: str) -> str:
    parts = [p for p in re.split(r"[-_]+", value) if p]
    special = {"aja": "A'ja", "nalyssa": "NaLyssa", "diijonai": "DiJonai", "te": "Te", "hina": "Hina"}
    out = [special.get(p.lower(), p.capitalize()) for p in parts]
    return clean_name(" ".join(out).replace("Te Hina", "Te-Hina"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fetch_url(url: str) -> Tuple[str, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HerSportsDailyAthleteRegistry/1.4"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace"), "ok"
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def strip_tags(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return clean(text)


def valid_name(name: str) -> bool:
    name = clean_name(name)
    low = name.lower()
    if not name or len(name) < 4 or len(name) > 38:
        return False
    if any(phrase == low or phrase in low for phrase in STOP_PHRASES):
        return False
    if not re.search(r"[A-Za-z]", name) or re.search(r"\d", name):
        return False
    if len(name.split()) < 2:
        return False
    bad_words = ["http", "cookie", "privacy", "tickets", "schedule", "standings", "stats", "roster", "league", "app store", "google play", "coach", "trainer"]
    if any(b in low for b in bad_words):
        return False
    return True


def extract_player_links(text: str) -> Dict[str, Dict[str, str]]:
    players: Dict[str, Dict[str, str]] = {}
    for m in re.finditer(r'/player/(\d+)/([a-z0-9-]+)', text, flags=re.I):
        player_id, name_slug = m.group(1), m.group(2)
        name = title_from_slug(name_slug)
        if valid_name(name):
            players[player_id] = {"provider_player_id": player_id, "display_name": name, "source": "player_link"}
    return players


def extract_roster_names_ordered(text: str) -> List[str]:
    plain = strip_tags(text)
    names: List[str] = []
    seen: Set[str] = set()
    pos_pattern = "|".join(re.escape(p) for p in POSITIONS)
    pattern = re.compile(rf"#\s*\d{{1,2}}\s+([A-Z][A-Za-z' .-]{{2,42}}?)\s+(?:{pos_pattern})\s+PPG", flags=re.I)
    for m in pattern.finditer(plain):
        name = clean_name(m.group(1))
        key = name.lower()
        if valid_name(name) and key not in seen:
            names.append(name)
            seen.add(key)
    return names


def extract_roster_names_from_plain(text: str) -> Dict[str, Dict[str, str]]:
    return {slug(name): {"provider_player_id": "", "display_name": name, "source": "roster_text"} for name in extract_roster_names_ordered(text)}


def extract_headshot_pairs_ordered(text: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    seen: Set[str] = set()
    patterns = [
        r'https?:\\/\\/cdn\.wnba\.com\\/headshots\\/wnba\\/latest\\/260x190\\/(\d+)\.png',
        r'https?://cdn\.wnba\.com/headshots/wnba/latest/260x190/(\d+)\.png',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            player_id = m.group(1)
            if player_id in seen:
                continue
            raw = m.group(0).replace("\\/", "/")
            pairs.append((player_id, raw))
            seen.add(player_id)
    return pairs


def extract_headshot_urls(text: str) -> Dict[str, str]:
    return {pid: url for pid, url in extract_headshot_pairs_ordered(text)}


def row_for_athlete(name: str, team_id: str, player_id: str, source_url: str, note: str) -> Dict[str, Any]:
    base = slug(name)
    athlete_id = f"{team_id}_{base}"
    return {
        "athlete_id": athlete_id,
        "league": "WNBA",
        "display_name": clean_name(name),
        "team_id": team_id,
        "provider_player_id": player_id,
        "status": "active_candidate",
        "source_url": source_url,
        "last_verified_utc": now_iso(),
        "notes": note,
    }


def build_aliases(athlete_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for athlete in athlete_rows:
        name = clean_name(athlete["display_name"])
        variants = {name, name.lower(), re.sub(r"[^A-Za-z0-9]+", " ", name).strip()}
        parts = name.split()
        if len(parts) >= 2:
            variants.add(parts[-1])
            variants.add(f"{parts[0][0]}. {parts[-1]}")
        for variant in variants:
            variant = clean(variant)
            if not variant:
                continue
            key = (variant.lower(), athlete["athlete_id"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({"name_variant": variant, "athlete_id": athlete["athlete_id"], "type": "canonical" if variant == name else "auto_alias"})
    return rows


def build_image_rows(athlete_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    images: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    for athlete in athlete_rows:
        for image_type in ["headshot", "cutout"]:
            recommended = f"assets/leagues/wnba/athletes/{athlete['athlete_id']}/{image_type}.png"
            exists = Path(recommended).exists()
            approved = exists and Path(recommended + ".approved").exists()
            images.append({
                "athlete_id": athlete["athlete_id"],
                "display_name": athlete["display_name"],
                "team_id": athlete["team_id"],
                "provider_player_id": athlete.get("provider_player_id", ""),
                "image_type": image_type,
                "file_path": recommended,
                "file_exists": "true" if exists else "false",
                "approved": "true" if approved else "false",
                "source_note": "approved_marker_required" if exists else "missing_review_required",
                "last_verified_utc": now_iso(),
            })
            if not approved:
                missing.append({
                    "athlete_id": athlete["athlete_id"],
                    "display_name": athlete["display_name"],
                    "team_id": athlete["team_id"],
                    "required_image_type": image_type,
                    "reason": "approved athlete image missing",
                    "recommended_path": recommended,
                })
    return images, missing


def order_match_candidates(team_id: str, url: str, names_ordered: List[str], headshots_ordered: List[Tuple[str, str]], athletes_by_key: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    candidates: List[Dict[str, Any]] = []
    review_rows: List[Dict[str, Any]] = []
    usable_count = min(len(names_ordered), len(headshots_ordered))
    confidence = "0.72" if len(headshots_ordered) >= len(names_ordered) and len(names_ordered) >= 10 else "0.55"
    for index, (player_id, img_url) in enumerate(headshots_ordered):
        if index < usable_count:
            name = names_ordered[index]
            athlete_id = f"{team_id}_{slug(name)}"
            if athlete_id not in athletes_by_key:
                athletes_by_key[athlete_id] = row_for_athlete(name, team_id, "", url, "official_roster_order_text_review_required")
            status = "order_match_review_required"
            display_name = name
            match_method = "roster_order_name_to_headshot_order"
            target_path = f"assets/leagues/wnba/athletes/{athlete_id}/headshot.png"
            notes = "review_before_approval; do_not_use_until_approved_marker_present"
        else:
            athlete_id = "unmatched_review_required"
            display_name = ""
            status = "unmatched_extra_headshot_review_required"
            match_method = "extra_headshot_no_roster_name"
            target_path = ""
            notes = "extra headshot beyond roster-name count"
        candidates.append({
            "candidate_id": f"{team_id}_{player_id}",
            "athlete_id": athlete_id,
            "display_name": display_name,
            "team_id": team_id,
            "provider_player_id": player_id,
            "source_url": url,
            "image_url": img_url,
            "image_type": "headshot_candidate",
            "status": status,
            "notes": notes,
        })
        if status == "order_match_review_required":
            review_rows.append({
                "team_id": team_id,
                "athlete_id": athlete_id,
                "display_name": display_name,
                "provider_player_id": player_id,
                "image_url": img_url,
                "match_method": match_method,
                "confidence": confidence,
                "status": "needs_human_approval",
                "approval_target_path": target_path,
                "notes": notes,
            })
    return candidates, review_rows


def main() -> None:
    source_rows = read_csv(SOURCES)
    athletes_by_key: Dict[str, Dict[str, Any]] = {}
    candidate_rows: List[Dict[str, Any]] = []
    match_review_rows: List[Dict[str, Any]] = []
    source_status: List[Dict[str, Any]] = []
    dirty_name_drops = 0
    for source in source_rows:
        team_id = source.get("team_id", "")
        url = source.get("roster_url", "")
        text, status = fetch_url(url)
        player_links = extract_player_links(text) if text else {}
        names_ordered = extract_roster_names_ordered(text) if text else []
        roster_names = {slug(name): {"provider_player_id": "", "display_name": name, "source": "roster_text"} for name in names_ordered}
        headshot_pairs = extract_headshot_pairs_ordered(text) if text else []

        for player_id, info in player_links.items():
            row = row_for_athlete(info["display_name"], team_id, player_id, url, "official_roster_player_link_review_required")
            athletes_by_key[row["athlete_id"]] = row
        for info in roster_names.values():
            name = info["display_name"]
            if not any(row["display_name"].lower() == name.lower() and row["team_id"] == team_id for row in athletes_by_key.values()):
                row = row_for_athlete(name, team_id, "", url, "official_roster_text_review_required")
                athletes_by_key[row["athlete_id"]] = row
        for name in re.findall(r'alt="([^"]+)"', text or ""):
            if not valid_name(clean_name(name)):
                dirty_name_drops += 1

        team_candidates, team_review_rows = order_match_candidates(team_id, url, names_ordered, headshot_pairs, athletes_by_key)
        candidate_rows.extend(team_candidates)
        match_review_rows.extend(team_review_rows)
        source_status.append({"team_id": team_id, "team_name": source.get("team_name", ""), "source_url": url, "status": status, "player_links": len(player_links), "roster_names": len(names_ordered), "headshot_urls": len(headshot_pairs), "order_matches": len(team_review_rows)})

    athlete_rows = sorted(athletes_by_key.values(), key=lambda r: (r["team_id"], r["display_name"]))
    alias_rows = build_aliases(athlete_rows)
    image_rows, missing_rows = build_image_rows(athlete_rows)
    write_csv(ATHLETES, athlete_rows, ATHLETE_FIELDS)
    write_csv(ALIASES, alias_rows, ALIAS_FIELDS)
    write_csv(IMAGES, image_rows, IMAGE_FIELDS)
    write_csv(CANDIDATES, candidate_rows, CANDIDATE_FIELDS)
    write_csv(MATCH_REVIEW, match_review_rows, MATCH_FIELDS)
    write_csv(MISSING_IMAGES, missing_rows, MISSING_FIELDS)
    write_csv(ROSTER_ENTITIES, [{"id": r["athlete_id"], "league": r["league"], "name": r["display_name"], "display_name": r["display_name"], "team_id": r["team_id"], "status": r["status"], "source_url": r["source_url"], "last_verified_utc": r["last_verified_utc"], "notes": r["notes"]} for r in athlete_rows], ROSTER_ENTITY_FIELDS)
    write_csv(ROSTER_NAMES, [{"name_variant": r["name_variant"], "entity_id": r["athlete_id"], "type": r["type"]} for r in alias_rows], ROSTER_NAME_FIELDS)

    matched_candidates = len([r for r in candidate_rows if r.get("status") == "order_match_review_required"])
    unmatched_candidates = len([r for r in candidate_rows if "unmatched" in r.get("status", "")])
    report = {
        "version": "hsd-wnba-athlete-registry-v1.4-order-based-review-sheet",
        "generated_at_utc": now_iso(),
        "source_count": len(source_rows),
        "sources_ok": len([s for s in source_status if s["status"] == "ok"]),
        "sources_failed": len([s for s in source_status if s["status"] != "ok"]),
        "athletes": len(athlete_rows),
        "aliases": len(alias_rows),
        "image_candidates": len(candidate_rows),
        "matched_image_candidates": matched_candidates,
        "unmatched_image_candidates": unmatched_candidates,
        "match_review_rows": len(match_review_rows),
        "approved_images": len([r for r in image_rows if r.get("approved") == "true"]),
        "missing_approved_images": len(missing_rows),
        "dirty_name_drops": dirty_name_drops,
        "usage_policy": "review_only_until_approved_marker_present",
        "source_status": source_status,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Athlete Registry v1.4",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- roster sources: {report['source_count']}",
        f"- sources ok: {report['sources_ok']}",
        f"- sources failed: {report['sources_failed']}",
        f"- athletes discovered: {report['athletes']}",
        f"- aliases: {report['aliases']}",
        f"- image candidates: {report['image_candidates']}",
        f"- matched image candidates: {matched_candidates}",
        f"- unmatched image candidates: {unmatched_candidates}",
        f"- match review rows: {len(match_review_rows)}",
        f"- approved images: {report['approved_images']}",
        f"- missing approved images: {report['missing_approved_images']}",
        f"- dirty name drops: {dirty_name_drops}",
        "",
        "## Usage policy",
        "",
        "- Order matches are review-only, not auto-approved.",
        "- Athlete images are public-use only when a matching approved file exists and an `.approved` marker is present.",
        "- Do not use athlete candidates in public graphics automatically.",
        "- Current team context comes from official WNBA roster source pages.",
        "",
        "## Source status",
        "",
    ]
    for item in source_status:
        lines.append(f"- {item['team_name']}: {item['status']} | player_links={item['player_links']} | roster_names={item['roster_names']} | headshot_urls={item['headshot_urls']} | order_matches={item['order_matches']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"athletes": len(athlete_rows), "image_candidates": len(candidate_rows), "matched_image_candidates": matched_candidates, "match_review_rows": len(match_review_rows), "sources_ok": report["sources_ok"], "sources_failed": report["sources_failed"]}, indent=2))


if __name__ == "__main__":
    main()
