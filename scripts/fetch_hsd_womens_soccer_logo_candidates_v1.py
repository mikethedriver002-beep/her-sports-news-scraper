from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from bs4 import BeautifulSoup
from PIL import Image


ROOT = Path("data/asset_registry/womens_soccer")
CONTACT_SHEET = ROOT / "womens_soccer_logo_contact_sheet.csv"
REPORT_JSON = ROOT / "womens_soccer_logo_candidate_fetch_report.json"
REPORT_MD = ROOT / "womens_soccer_logo_candidate_fetch_report.md"

USER_AGENT = "HerSportsDailyAssetReview/1.0 review-only local candidate fetch"
MIN_IMAGE_BYTES = 300

EXACT_SEARCH_TITLES = {
    "arsenal_women": "Arsenal W.F.C.",
    "aston_villa_women": "Aston Villa W.F.C.",
    "brighton_hove_albion_women": "Brighton & Hove Albion W.F.C.",
    "chelsea_women": "Chelsea F.C. Women",
    "everton_women": "Everton F.C. (women)",
    "leicester_city_women": "Leicester City W.F.C.",
    "liverpool_women": "Liverpool F.C. Women",
    "london_city_lionesses": "London City Lionesses",
    "manchester_city_women": "Manchester City W.F.C.",
    "manchester_united_women": "Manchester United W.F.C.",
    "tottenham_hotspur_women": "Tottenham Hotspur F.C. Women",
    "west_ham_united_women": "West Ham United F.C. Women",
    "alhama_cf_elpozo": "Alhama CF",
    "athletic_club": "Athletic Club (women)",
    "atletico_de_madrid": "Atlético Madrid Femenino",
    "costa_adeje_tenerife": "UD Tenerife",
    "deportivo_abanca": "Deportivo de La Coruña (women)",
    "dux_logrono": "Dux Logroño",
    "fc_badalona_women": "FC Levante Badalona",
    "fc_barcelona": "FC Barcelona Femení",
    "granada_cf": "Granada CF (women)",
    "levante_ud": "Levante UD Femenino",
    "madrid_cff": "Madrid CFF",
    "rcd_espanyol_de_barcelona": "RCD Espanyol Femení",
    "real_madrid_cf": "Real Madrid Femenino",
    "real_sociedad": "Real Sociedad Femenino",
    "sd_eibar": "SD Eibar (women)",
    "sevilla_fc": "Sevilla FC (women)",
    "as_roma_women": "AS Roma (women)",
    "ac_milan_women": "AC Milan Women",
    "como_women": "Como 1907 (women)",
    "fc_internazionale_women": "Inter Milan (women)",
    "fiorentina_women": "ACF Fiorentina (women)",
    "genoa_women": "Genoa CFC Women",
    "juventus_women": "Juventus FC (women)",
    "lazio_women": "SS Lazio Women 2015",
    "napoli_femminile": "Napoli Femminile",
    "parma_women": "Parma Calcio 2022",
    "sassuolo_women": "US Sassuolo Calcio (women)",
    "ternana_women": "Ternana Women",
    "ol_lyonnes": "OL Lyonnes",
    "paris_saint_germain_women": "Paris Saint-Germain FC (women)",
    "paris_fc_women": "Paris FC (women)",
    "as_saint_etienne_women": "AS Saint-Étienne (women)",
    "dijon_fco_women": "Dijon FCO (women)",
    "fc_fleury_91_women": "FC Fleury 91 (women)",
    "fc_nantes_women": "FC Nantes (women)",
    "le_havre_ac_women": "Le Havre AC (women)",
    "mhsc_feminines": "Montpellier HSC (women)",
    "olympique_marseille_women": "Olympique de Marseille (women)",
    "rc_lens_women": "RC Lens (women)",
    "rc_strasbourg_alsace_women": "RC Strasbourg Alsace (women)",
    "premiere_ligue_france": "Première Ligue",
}

EXACT_CANDIDATE_URLS = {
    "everton_women": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Everton_FC_logo.svg/330px-Everton_FC_logo.svg.png",
    "chelsea_women": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/330px-Chelsea_FC.svg.png",
    "manchester_united_women": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/330px-Manchester_United_FC_crest.svg.png",
    "west_ham_united_women": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c2/West_Ham_United_FC_logo.svg/330px-West_Ham_United_FC_logo.svg.png",
    "alhama_cf_elpozo": "https://upload.wikimedia.org/wikipedia/en/2/21/Alhama_CF_logo.png",
    "athletic_club": "https://upload.wikimedia.org/wikipedia/en/thumb/9/98/Club_Athletic_Bilbao_logo.svg/330px-Club_Athletic_Bilbao_logo.svg.png",
    "atletico_de_madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Atletico_Madrid_logo.svg/330px-Atletico_Madrid_logo.svg.png",
    "fc_badalona_women": "https://upload.wikimedia.org/wikipedia/en/0/0d/FC_Levante_Badalona.png",
    "granada_cf": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d5/Logo_of_Granada_Club_de_F%C3%BAtbol.svg/330px-Logo_of_Granada_Club_de_F%C3%BAtbol.svg.png",
    "madrid_cff": "https://upload.wikimedia.org/wikipedia/en/2/26/Madrid_CFF_Logo.PNG",
    "sevilla_fc": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Sevilla_FC_logo.svg/330px-Sevilla_FC_logo.svg.png",
    "as_roma_women": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f7/AS_Roma_logo_%282017%29.svg/330px-AS_Roma_logo_%282017%29.svg.png",
    "como_women": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Calcio_Como_-_logo_%28Italy%2C_2019-%29.svg/330px-Calcio_Como_-_logo_%28Italy%2C_2019-%29.svg.png",
    "genoa_women": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/Genoa_CFC_crest.svg/330px-Genoa_CFC_crest.svg.png",
    "juventus_women": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Juventus_FC_-_logo_black_%28Italy%2C_2020%29.svg/330px-Juventus_FC_-_logo_black_%28Italy%2C_2020%29.svg.png",
    "lazio_women": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/SS_Lazio.svg/330px-SS_Lazio.svg.png",
    "napoli_femminile": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/SSC_Napoli_2024_%28deep_blue_navy%29.svg/330px-SSC_Napoli_2024_%28deep_blue_navy%29.svg.png",
    "parma_women": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Logo_Parma_Calcio_1913_%28adozione_2016%29.svg/330px-Logo_Parma_Calcio_1913_%28adozione_2016%29.svg.png",
    "sassuolo_women": "https://upload.wikimedia.org/wikipedia/en/thumb/1/1c/US_Sassuolo_Calcio_logo.svg/330px-US_Sassuolo_Calcio_logo.svg.png",
    "ternana_women": "https://upload.wikimedia.org/wikipedia/it/thumb/8/88/Ternana_Calcio_Stemma.svg/330px-Ternana_Calcio_Stemma.svg.png",
    "as_saint_etienne_women": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Logo_AS_Saint-%C3%89tienne.svg/500px-Logo_AS_Saint-%C3%89tienne.svg.png",
    "fc_fleury_91_women": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b9/FC_Fleury_91_%28women%29_logo.svg/330px-FC_Fleury_91_%28women%29_logo.svg.png",
    "le_havre_ac_women": "https://upload.wikimedia.org/wikipedia/en/thumb/f/fc/Le_Havre_AC_logo.svg/330px-Le_Havre_AC_logo.svg.png",
    "paris_saint_germain_women": "https://upload.wikimedia.org/wikipedia/en/4/4a/PSG_women_team.png",
    "rc_lens_women": "https://upload.wikimedia.org/wikipedia/en/9/9e/RC_Lens_Feminin_logo.jpg",
    "rc_strasbourg_alsace_women": "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Racing_Club_de_Strasbourg_logo.svg/330px-Racing_Club_de_Strasbourg_logo.svg.png",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def request_bytes(url: str, *, limit: int | None = None) -> Tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=24) as response:
        data = response.read(limit or 8_000_000)
        return data, response.headers.get("content-type", "")


def normalize_candidate_url(base_url: str, value: str) -> str:
    url = urllib.parse.urljoin(base_url, clean(value))
    parsed = urllib.parse.urlparse(url)
    if parsed.path.lower().endswith(".svg"):
        url = urllib.parse.urlunparse(parsed._replace(path=parsed.path[:-4] + ".png"))
    return url


def words(value: str) -> set[str]:
    stop = {"fc", "cf", "women", "womens", "femenino", "feminine", "femminile", "club", "de", "the", "ac"}
    return {part for part in re.findall(r"[a-z0-9]+", value.lower()) if part not in stop and len(part) > 1}


def name_score(row: Mapping[str, str], text: str) -> int:
    wanted = words(clean(row.get("display_name")) + " " + clean(row.get("entity_id")).replace("_", " "))
    haystack = words(text)
    return len(wanted & haystack)


def html_candidates(row: Mapping[str, str]) -> List[Dict[str, str]]:
    source_url = clean(row.get("official_source_candidate")) or clean(row.get("current_source_url"))
    if not source_url:
        return []
    try:
        data, content_type = request_bytes(source_url, limit=1_200_000)
    except Exception:
        return []
    if "html" not in content_type.lower() and b"<html" not in data[:1000].lower():
        return [{"url": source_url, "method": "direct_source_image", "score": "1"}]
    soup = BeautifulSoup(data, "html.parser")
    candidates: List[Dict[str, str]] = []
    for tag in soup.find_all("img"):
        src = tag.get("src") or tag.get("data-src") or tag.get("data-lazy-src") or ""
        if not src:
            continue
        label = " ".join([tag.get("alt") or "", tag.get("title") or "", " ".join(tag.get("class") or []), src])
        score = name_score(row, label)
        if score or re.search(r"logo|crest|badge|emblem|team|club|escudo", label, re.I):
            candidates.append({"url": normalize_candidate_url(source_url, src), "method": "official_page_img", "score": str(score)})
    for tag in soup.find_all("meta"):
        key = clean(tag.get("property") or tag.get("name")).lower()
        content = clean(tag.get("content"))
        if content and "image" in key:
            candidates.append({"url": normalize_candidate_url(source_url, content), "method": f"official_page_meta:{key}", "score": "0"})
    for tag in soup.find_all("link"):
        rel = " ".join(tag.get("rel") or []).lower()
        href = clean(tag.get("href"))
        if href and any(part in rel for part in ["apple-touch-icon", "icon"]):
            candidates.append({"url": normalize_candidate_url(source_url, href), "method": f"official_page_link:{rel}", "score": "0"})
    return sorted(candidates, key=lambda item: int(item.get("score") or 0), reverse=True)


def wikipedia_titles(row: Mapping[str, str]) -> List[str]:
    entity_id = clean(row.get("entity_id"))
    display = clean(row.get("display_name"))
    titles = []
    if entity_id in EXACT_SEARCH_TITLES:
        titles.append(EXACT_SEARCH_TITLES[entity_id])
    titles.extend(
        [
            display,
            f"{display} women's football",
            f"{display} women football",
            f"{display} football club",
        ]
    )
    deduped: List[str] = []
    seen: set[str] = set()
    for title in titles:
        key = title.lower()
        if key not in seen:
            deduped.append(title)
            seen.add(key)
    return deduped


def wikipedia_summary(title: str) -> Optional[Dict[str, Any]]:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    try:
        data, _ = request_bytes(url, limit=400_000)
        return json.loads(data.decode("utf-8", errors="replace"))
    except Exception:
        return None


def wikipedia_search(query: str) -> List[str]:
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": "3"})
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    try:
        data, _ = request_bytes(url, limit=400_000)
        payload = json.loads(data.decode("utf-8", errors="replace"))
        return [item["title"] for item in payload.get("query", {}).get("search", []) if item.get("title")]
    except Exception:
        return []


def wikimedia_candidates(row: Mapping[str, str]) -> List[Dict[str, str]]:
    if clean(row.get("entity_type")) == "league":
        return []
    candidates: List[Dict[str, str]] = []
    titles = wikipedia_titles(row)
    for title in titles:
        summary = wikipedia_summary(title)
        time.sleep(0.35)
        if summary and summary.get("thumbnail", {}).get("source"):
            candidates.append({"url": clean(summary["thumbnail"]["source"]), "method": f"wikimedia_summary:{summary.get('title', title)}", "score": str(name_score(row, title))})
            return candidates
    for title in wikipedia_search(clean(row.get("display_name")) + " women's football crest"):
        summary = wikipedia_summary(title)
        time.sleep(0.35)
        if summary and summary.get("thumbnail", {}).get("source"):
            candidates.append({"url": clean(summary["thumbnail"]["source"]), "method": f"wikimedia_search:{summary.get('title', title)}", "score": str(name_score(row, title))})
            return candidates
    return candidates


def exact_alias_candidates(row: Mapping[str, str]) -> List[Dict[str, str]]:
    entity_id = clean(row.get("entity_id"))
    direct = EXACT_CANDIDATE_URLS.get(entity_id)
    if direct:
        return [{"url": direct, "method": "wikimedia_exact_candidate_url", "score": "100"}]
    title = EXACT_SEARCH_TITLES.get(entity_id)
    if not title:
        return []
    summary = wikipedia_summary(title)
    time.sleep(0.35)
    if summary and summary.get("thumbnail", {}).get("source"):
        return [{"url": clean(summary["thumbnail"]["source"]), "method": f"wikimedia_exact:{summary.get('title', title)}", "score": "99"}]
    return []


def save_as_png(data: bytes, target_path: Path) -> Tuple[bool, str]:
    if len(data) < MIN_IMAGE_BYTES:
        return False, "image_too_small"
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            if image.width < 24 or image.height < 24:
                return False, f"image_dimensions_too_small:{image.width}x{image.height}"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            image.convert("RGBA").save(target_path, "PNG")
            return True, f"saved_png:{image.width}x{image.height}"
    except Exception as exc:
        return False, f"pillow_unreadable:{type(exc).__name__}:{exc}"


def fetch_row(row: Mapping[str, str], *, overwrite: bool = False) -> Dict[str, Any]:
    target_path = Path(clean(row.get("local_logo_path")))
    result: Dict[str, Any] = {
        "scope_id": clean(row.get("scope_id")),
        "league_id": clean(row.get("league_id")),
        "entity_type": clean(row.get("entity_type")),
        "entity_id": clean(row.get("entity_id")),
        "display_name": clean(row.get("display_name")),
        "target_path": target_path.as_posix(),
        "source_url": clean(row.get("official_source_candidate")),
        "status": "not_started",
        "candidate_url": "",
        "candidate_method": "",
        "reason": "",
    }
    if not target_path.as_posix():
        result.update({"status": "skipped", "reason": "missing_target_path"})
        return result
    if target_path.exists() and target_path.stat().st_size > MIN_IMAGE_BYTES and not overwrite:
        result.update({"status": "exists", "reason": "local_candidate_already_exists", "bytes": target_path.stat().st_size})
        return result

    official_candidates = html_candidates(row)
    high_confidence_official = [candidate for candidate in official_candidates if int(candidate.get("score") or 0) > 0]
    generic_official = [candidate for candidate in official_candidates if int(candidate.get("score") or 0) <= 0]
    candidates = exact_alias_candidates(row)
    candidates.extend(high_confidence_official)
    candidates.extend(wikimedia_candidates(row))
    if clean(row.get("entity_type")) == "league":
        candidates.extend(generic_official)
    seen: set[str] = set()
    for candidate in candidates:
        url = clean(candidate.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            data, content_type = request_bytes(url)
        except Exception as exc:
            result["reason"] = f"candidate_fetch_failed:{type(exc).__name__}:{exc}"
            continue
        ok, reason = save_as_png(data, target_path)
        if ok:
            result.update(
                {
                    "status": "downloaded_candidate",
                    "candidate_url": url,
                    "candidate_method": clean(candidate.get("method")),
                    "candidate_content_type": content_type,
                    "bytes": target_path.stat().st_size,
                    "reason": reason,
                    "approval_status": "not_approved",
                    "review_only": True,
                }
            )
            return result
        result["reason"] = reason

    target_path.parent.mkdir(parents=True, exist_ok=True)
    result.update({"status": "failed", "reason": result.get("reason") or "no_usable_image_candidate"})
    return result


def write_report(report: Mapping[str, Any]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Women's Soccer Logo Candidate Fetch Report",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        "",
        "Review-only candidate fetch. This report does not approve assets, render-enable rows, publish, or create a publish-ready lane.",
        "",
        "## Counts",
        "",
        f"- rows: `{report['rows']}`",
        f"- downloaded candidates: `{report['downloaded_candidate']}`",
        f"- already existed: `{report['exists']}`",
        f"- failed: `{report['failed']}`",
        "",
        "## Results",
        "",
    ]
    for item in report["results"]:
        lines.append(
            f"- {item['display_name']} | {item['status']} | target=`{item['target_path']}` | source={item.get('candidate_url') or item.get('source_url') or 'missing'} | method={item.get('candidate_method') or 'none'} | {item.get('reason') or ''}"
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch review-only women soccer logo candidates into sanctioned local paths.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--league", action="append", default=[])
    args = parser.parse_args()
    scopes = {clean(value) for value in args.scope if clean(value)}
    leagues = {clean(value) for value in args.league if clean(value)}
    rows = [
        row
        for row in read_csv(CONTACT_SHEET)
        if (not scopes or clean(row.get("scope_id")) in scopes)
        and (not leagues or clean(row.get("league_id")) in leagues)
    ]
    if args.limit:
        rows = rows[: args.limit]
    results = [fetch_row(row, overwrite=args.overwrite) for row in rows]
    counts: Dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    report = {
        "version": "hsd-womens-soccer-logo-candidate-fetch-v1-review-only",
        "generated_at_utc": now_iso(),
        "rows": len(results),
        "downloaded_candidate": counts.get("downloaded_candidate", 0),
        "exists": counts.get("exists", 0),
        "failed": counts.get("failed", 0),
        "approval_state_changed": False,
        "asset_downloads_are_review_only_candidates": True,
        "results": results,
    }
    write_report(report)
    print(json.dumps({key: report[key] for key in ["rows", "downloaded_candidate", "exists", "failed", "approval_state_changed"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
