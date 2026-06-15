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
MISSING_IMAGES = ROOT / "missing_athlete_images.csv"
REPORT_JSON = ROOT / "athlete_registry_report.json"
REPORT_MD = ROOT / "athlete_registry_report.md"
ROSTER_ENTITIES = ROOT / "roster_entities.csv"
ROSTER_NAMES = ROOT / "roster_names.csv"

ATHLETE_FIELDS = ["athlete_id", "league", "display_name", "team_id", "status", "source_url", "last_verified_utc", "notes"]
ALIAS_FIELDS = ["name_variant", "athlete_id", "type"]
IMAGE_FIELDS = ["athlete_id", "display_name", "team_id", "image_type", "file_path", "file_exists", "approved", "source_note", "last_verified_utc"]
CANDIDATE_FIELDS = ["candidate_id", "athlete_id", "display_name", "team_id", "source_url", "image_url", "image_type", "status", "notes"]
MISSING_FIELDS = ["athlete_id", "display_name", "team_id", "required_image_type", "reason", "recommended_path"]
ROSTER_ENTITY_FIELDS = ["id", "league", "name", "display_name", "team_id", "status", "source_url", "last_verified_utc", "notes"]
ROSTER_NAME_FIELDS = ["name_variant", "entity_id", "type"]

STOP_NAMES = {
    "Roster", "Stats", "Schedule", "Tickets", "Shop", "News", "Videos", "Photos", "Standings", "Teams", "League Pass",
    "Privacy Policy", "Terms Of Use", "Cookie Policy", "WNBA", "NBA", "Home", "Games", "Scores", "More", "Menu",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def slug(value: str, sep: str = "_") -> str:
    return re.sub(r"[^a-z0-9]+", sep, clean(value).lower()).strip(sep)


def title_from_slug(value: str) -> str:
    parts = [p for p in re.split(r"[-_]+", value) if p]
    tiny = {"aja": "A'ja", "nalyssa": "NaLyssa", "nneka": "Nneka", "chiney": "Chiney", "arike": "Arike", "diijonai": "DiJonai"}
    out = []
    for p in parts:
        out.append(tiny.get(p.lower(), p.capitalize()))
    return " ".join(out)


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
        req = urllib.request.Request(url, headers={"User-Agent": "HerSportsDailyAthleteRegistry/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace"), "ok"
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def valid_name(name: str) -> bool:
    name = clean(name)
    if not name or name in STOP_NAMES:
        return False
    if len(name) < 4 or len(name) > 42:
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    if len(name.split()) < 2:
        return False
    if re.search(r"\d", name):
        return False
    bad = ["http", "cookie", "privacy", "tickets", "schedule", "standings", "stats", "roster", "league"]
    if any(b in name.lower() for b in bad):
        return False
    return True


def extract_names(text: str) -> List[str]:
    names: Set[str] = set()
    for pattern in [
        r'"displayName"\s*:\s*"([^"]{3,60})"',
        r'"fullName"\s*:\s*"([^"]{3,60})"',
        r'"firstName"\s*:\s*"([^"]{2,30})"\s*,\s*"lastName"\s*:\s*"([^"]{2,35})"',
        r'/player/\d+/([a-z0-9-]+)',
        r'/players?/([a-z0-9-]{4,60})',
        r'alt="([A-Z][A-Za-z\' .-]+ [A-Z][A-Za-z\' .-]+)"',
        r'aria-label="([A-Z][A-Za-z\' .-]+ [A-Z][A-Za-z\' .-]+)"',
    ]:
        for m in re.finditer(pattern, text):
            if len(m.groups()) == 2:
                raw = clean(m.group(1) + " " + m.group(2))
            else:
                raw = clean(m.group(1))
                if "/" not in pattern and "-" in raw and raw.lower() == raw:
                    raw = title_from_slug(raw)
                elif "player" in pattern or "players" in pattern:
                    raw = title_from_slug(raw)
            if valid_name(raw):
                names.add(raw)
    return sorted(names)


def extract_images(text: str) -> List[str]:
    urls: Set[str] = set()
    for m in re.finditer(r'https?:\\/\\/[^"\\]+?\.(?:png|jpg|jpeg|webp)', text):
        urls.add(m.group(0).replace("\\/", "/"))
    for m in re.finditer(r'https?://[^"\'<> ]+?\.(?:png|jpg|jpeg|webp)', text):
        urls.add(m.group(0))
    return sorted(u for u in urls if any(word in u.lower() for word in ["headshot", "player", "wnba", "nba", "image", "person"]))[:80]


def row_for_athlete(name: str, team_id: str, source_url: str, note: str) -> Dict[str, Any]:
    athlete_id = f"{team_id}_{slug(name)}"
    return {
        "athlete_id": athlete_id,
        "league": "WNBA",
        "display_name": name,
        "team_id": team_id,
        "status": "active_candidate",
        "source_url": source_url,
        "last_verified_utc": now_iso(),
        "notes": note,
    }


def build_aliases(athlete_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    for athlete in athlete_rows:
        name = clean(athlete["display_name"])
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
            rows.append({"name_variant": variant, "athlete_id": athlete["athlete_id"], "type": "auto_alias" if variant != name else "canonical"})
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


def main() -> None:
    source_rows = read_csv(SOURCES)
    athletes_by_id: Dict[str, Dict[str, Any]] = {}
    candidate_rows: List[Dict[str, Any]] = []
    source_status: List[Dict[str, Any]] = []
    for source in source_rows:
        team_id = source.get("team_id", "")
        url = source.get("roster_url", "")
        text, status = fetch_url(url)
        names = extract_names(text) if text else []
        image_urls = extract_images(text) if text else []
        source_status.append({"team_id": team_id, "team_name": source.get("team_name", ""), "source_url": url, "status": status, "names_found": len(names), "image_urls_found": len(image_urls)})
        for name in names:
            row = row_for_athlete(name, team_id, url, "official_roster_candidate_review_required")
            athletes_by_id[row["athlete_id"]] = row
        # Images are candidates only. No auto-approval and no public render usage.
        for index, img_url in enumerate(image_urls[:20]):
            candidate_rows.append({
                "candidate_id": f"{team_id}_{index+1:03d}",
                "athlete_id": "unmatched_review_required",
                "display_name": "",
                "team_id": team_id,
                "source_url": url,
                "image_url": img_url,
                "image_type": "headshot_candidate",
                "status": "candidate_review_required",
                "notes": "do_not_use_until_matched_and_approved",
            })
    athlete_rows = sorted(athletes_by_id.values(), key=lambda r: (r["team_id"], r["display_name"]))
    alias_rows = build_aliases(athlete_rows)
    image_rows, missing_rows = build_image_rows(athlete_rows)
    write_csv(ATHLETES, athlete_rows, ATHLETE_FIELDS)
    write_csv(ALIASES, alias_rows, ALIAS_FIELDS)
    write_csv(IMAGES, image_rows, IMAGE_FIELDS)
    write_csv(CANDIDATES, candidate_rows, CANDIDATE_FIELDS)
    write_csv(MISSING_IMAGES, missing_rows, MISSING_FIELDS)
    # Backward-compatible roster files for older pipeline readers.
    write_csv(ROSTER_ENTITIES, [{"id": r["athlete_id"], "league": r["league"], "name": r["display_name"], "display_name": r["display_name"], "team_id": r["team_id"], "status": r["status"], "source_url": r["source_url"], "last_verified_utc": r["last_verified_utc"], "notes": r["notes"]} for r in athlete_rows], ROSTER_ENTITY_FIELDS)
    write_csv(ROSTER_NAMES, [{"name_variant": r["name_variant"], "entity_id": r["athlete_id"], "type": r["type"]} for r in alias_rows], ROSTER_NAME_FIELDS)
    report = {
        "version": "hsd-wnba-athlete-registry-v1",
        "generated_at_utc": now_iso(),
        "source_count": len(source_rows),
        "sources_ok": len([s for s in source_status if s["status"] == "ok"]),
        "sources_failed": len([s for s in source_status if s["status"] != "ok"]),
        "athletes": len(athlete_rows),
        "aliases": len(alias_rows),
        "image_candidates": len(candidate_rows),
        "approved_images": len([r for r in image_rows if r.get("approved") == "true"]),
        "missing_approved_images": len(missing_rows),
        "usage_policy": "review_only_until_approved_marker_present",
        "source_status": source_status,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Athlete Registry v1",
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
        f"- approved images: {report['approved_images']}",
        f"- missing approved images: {report['missing_approved_images']}",
        "",
        "## Usage policy",
        "",
        "- Athlete images are review-only until a matching approved file exists and an `.approved` marker is present.",
        "- Do not use athlete candidates in public graphics automatically.",
        "- Current team context comes from official WNBA roster source pages.",
        "",
        "## Source status",
        "",
    ]
    for item in source_status:
        lines.append(f"- {item['team_name']}: {item['status']} | names={item['names_found']} | image_urls={item['image_urls_found']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"athletes": len(athlete_rows), "image_candidates": len(candidate_rows), "sources_ok": report["sources_ok"], "sources_failed": report["sources_failed"]}, indent=2))


if __name__ == "__main__":
    main()
