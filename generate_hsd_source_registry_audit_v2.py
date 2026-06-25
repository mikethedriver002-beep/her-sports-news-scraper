from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from hsd_run_io import input_path, read_csv as read_run_csv, run_output_dir, write_csv as write_run_csv, write_json, write_text

VERSION = "hsd-source-registry-audit-bebe-v2.9-league-proposal-pack-framework"
REGISTRY = "config/source_registry.json"
PROPOSALS = "operator/inbox/source_registry_proposals.csv"
OUT_CSV = "source_registry_audit.csv"
OUT_COVERAGE_CSV = "source_coverage_map.csv"
OUT_INTAKE_CSV = "source_registry_intake_template.csv"
OUT_INTAKE_MD = "source_registry_intake_template.md"
OUT_PROPOSAL_CSV = "source_registry_proposal_review.csv"
OUT_PROPOSAL_MD = "source_registry_proposal_review.md"
OUT_PROPOSAL_PACKS_CSV = "source_proposal_packs.csv"
OUT_PROPOSAL_PACKS_MD = "source_proposal_packs.md"
OUT_PWHL_PACK_CSV = "pwhl_source_proposal_pack.csv"
OUT_PWHL_PACK_MD = "pwhl_source_proposal_pack.md"
OUT_MD = "source_registry_audit.md"
OUT_JSON = "source_registry_audit.json"

FIELDS = [
    "source_id", "source_type", "tier", "trust_band", "enabled", "sport_league", "automation_status",
    "publish_policy", "status", "issues", "urls_count", "domains_count",
]

GREEN_TIERS = {"official", "operator", "wire", "primary_media", "stats_provider"}
YELLOW_TIERS = {"social", "social_manual", "community", "discovery", "media_review"}
RED_TIERS = {"red", "prohibited"}

COVERAGE_FIELDS = [
    "coverage_key",
    "display_name",
    "official_sources",
    "team_sources",
    "wire_sources",
    "cross_check_sources",
    "coverage_status",
    "coverage_gap",
    "operator_next_step",
]

INTAKE_FIELDS = [
    "coverage_key",
    "display_name",
    "needed_source_type",
    "coverage_gap",
    "candidate_source_id",
    "candidate_source_name",
    "candidate_url",
    "candidate_domain",
    "source_type",
    "tier",
    "trust_band",
    "sport_league",
    "proposed_enabled",
    "automation_status",
    "publish_policy",
    "allowed_use",
    "operator_verification_status",
    "registry_action",
    "review_notes",
]

PROPOSAL_REVIEW_FIELDS = [
    "candidate_source_id",
    "candidate_source_name",
    "candidate_url",
    "candidate_domain",
    "sport_league",
    "source_type",
    "tier",
    "proposed_enabled",
    "review_status",
    "issue_count",
    "issues",
    "safety_flags",
    "recommendation",
    "registry_action",
]

SOURCE_PROPOSAL_PACK_FIELDS = [
    "pack_key",
    "pack_name",
    "candidate_group",
    "suggested_priority",
    *INTAKE_FIELDS,
    "source_basis",
    "registry_presence",
    "manual_review_note",
]

PWHL_SOURCE_CANDIDATES = [
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "missing official league/team source",
        "candidate_source_id": "pwhl_official_home",
        "candidate_source_name": "PWHL official site",
        "candidate_url": "https://www.thepwhl.com/en/",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; league_context; source_confirmation",
        "source_basis": "Free public league official site with team, schedule, standings, stats, and news navigation.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "missing official league/team source",
        "candidate_source_id": "pwhl_official_news",
        "candidate_source_name": "PWHL official news",
        "candidate_url": "https://www.thepwhl.com/en/news",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; source_confirmation; transaction_confirmation",
        "source_basis": "Free public official league news page for announcements and source confirmation.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_scores",
        "candidate_source_name": "PWHL official scores",
        "candidate_url": "https://www.thepwhl.com/en/scores",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; scores; schedules; game_summaries",
        "source_basis": "Free public official scores page for manual final-score and schedule checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_standings",
        "candidate_source_name": "PWHL official standings",
        "candidate_url": "https://www.thepwhl.com/en/stats/standings",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; standings; league_context",
        "source_basis": "Free public official standings page for table and context checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_player_stats",
        "candidate_source_name": "PWHL official player stats",
        "candidate_url": "https://www.thepwhl.com/en/stats/player-stats",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; player_stats; league_context",
        "source_basis": "Free public official player stats page for context and stat checks.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_boston_fleet_team",
        "candidate_source_name": "Boston Fleet official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/boston-fleet",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_detroit_team",
        "candidate_source_name": "PWHL Detroit official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/detroit",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Detroit team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_hamilton_team",
        "candidate_source_name": "PWHL Hamilton official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/hamilton",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Hamilton team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_las_vegas_team",
        "candidate_source_name": "PWHL Las Vegas official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/las-vegas",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Las Vegas team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_minnesota_frost_team",
        "candidate_source_name": "Minnesota Frost official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/minnesota-frost",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_montreal_victoire_team",
        "candidate_source_name": "Montreal Victoire official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/montreal-victoire",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_new_york_sirens_team",
        "candidate_source_name": "New York Sirens official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/new-york-sirens",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_ottawa_charge_team",
        "candidate_source_name": "Ottawa Charge official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/ottawa-charge",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_san_jose_team",
        "candidate_source_name": "PWHL San Jose official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/san-jose",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for San Jose team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_seattle_torrent_team",
        "candidate_source_name": "Seattle Torrent official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/seattle-torrent",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Seattle team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_toronto_sceptres_team",
        "candidate_source_name": "Toronto Sceptres official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/toronto-sceptres",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_vancouver_goldeneyes_team",
        "candidate_source_name": "Vancouver Goldeneyes official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/vancouver-goldeneyes",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Vancouver team news and launch context.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "eliteprospects_pwhl_cross_check",
        "candidate_source_name": "Elite Prospects PWHL page",
        "candidate_url": "https://www.eliteprospects.com/league/pwhl-w",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; roster_context; standings_context",
        "source_basis": "Free public hockey database page for manual roster/stat cross-checking; not an official source.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "hockeydb_pwhl_cross_check",
        "candidate_source_name": "HockeyDB PWHL season page",
        "candidate_url": "https://www.hockeydb.com/ihdb/stats/leagues/seasons/pwhl20242026.html",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; historical_scores; standings_context",
        "source_basis": "Free public hockey database season page for manual historical/stat cross-checking; not an official source.",
    },
]

SOURCE_PROPOSAL_PACKS = [
    {
        "pack_key": "pwhl",
        "pack_name": "PWHL Source Proposal Pack",
        "display_name": "PWHL",
        "fallback_coverage_gap": "missing official league/team source; missing scoreboard/stat/cross-check source",
        "fallback_operator_next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
        "description": "Guided free-source candidates for manual review of PWHL coverage gaps.",
        "output_csv": OUT_PWHL_PACK_CSV,
        "output_md": OUT_PWHL_PACK_MD,
        "candidates": PWHL_SOURCE_CANDIDATES,
        "group_order": ["league_official", "team_official", "league_cross_check", "reputable_cross_check"],
    },
]

COVERAGE_TARGETS = [
    {
        "key": "wnba",
        "name": "WNBA",
        "aliases": ["wnba"],
        "needs_team_source": True,
        "next_step": "Monitor WNBA league/team official pages plus AP/Reuters or scoreboard cross-checks.",
    },
    {
        "key": "wta",
        "name": "WTA / tennis",
        "aliases": ["wta", "tennis", "wimbledon"],
        "needs_team_source": False,
        "next_step": "Monitor WTA official news/tournament pages and add a second free wire or tournament source when needed.",
    },
    {
        "key": "nwsl",
        "name": "NWSL",
        "aliases": ["nwsl"],
        "needs_team_source": True,
        "next_step": "Monitor NWSL official news/schedule and add club-specific free sources when they become useful.",
    },
    {
        "key": "lpga",
        "name": "LPGA / golf",
        "aliases": ["lpga", "golf"],
        "needs_team_source": False,
        "next_step": "Monitor LPGA official tournament pages and wire context for result confirmation.",
    },
    {
        "key": "ncaa_softball",
        "name": "NCAA softball",
        "aliases": ["ncaa softball", "softball"],
        "needs_team_source": False,
        "next_step": "Monitor NCAA softball official pages and add event-specific public sources for championship weeks.",
    },
    {
        "key": "uswnt",
        "name": "USWNT",
        "aliases": ["uswnt", "us soccer"],
        "needs_team_source": False,
        "next_step": "Monitor US Soccer official pages plus FIFA/CONCACAF sources for international context.",
    },
    {
        "key": "volleyball",
        "name": "Volleyball / VNL",
        "aliases": ["volleyball", "vnl"],
        "needs_team_source": False,
        "next_step": "Monitor Volleyball World/VNL official pages and add event-specific public sources when useful.",
    },
    {
        "key": "pwhl",
        "name": "PWHL",
        "aliases": ["pwhl", "phwl"],
        "needs_team_source": True,
        "next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
    },
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def lower(v: Any) -> str:
    return clean(v).lower()


def read_json(path: str | Path) -> Dict[str, Any]:
    p = input_path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, FIELDS, extrasaction="ignore")


def write_coverage_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, COVERAGE_FIELDS, extrasaction="ignore")


def write_intake_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, INTAKE_FIELDS, extrasaction="ignore")


def write_proposal_review_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, PROPOSAL_REVIEW_FIELDS, extrasaction="ignore")


def write_source_proposal_pack_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_PROPOSAL_PACK_FIELDS, extrasaction="ignore")


def canonical_band(src: Dict[str, Any]) -> str:
    raw = clean(src.get("trust_band")).lower()
    tier = clean(src.get("tier")).lower()
    if "red" in raw or tier in RED_TIERS:
        return "red"
    if "green" in raw or tier in GREEN_TIERS:
        return "green"
    if "yellow" in raw or tier in YELLOW_TIERS:
        return "yellow"
    return "yellow"


def url_ok(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def split_tokens(value: Any) -> List[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [clean(item) for item in re.split(r"[;,]", clean(value)) if clean(item)]


def audit_source(src: Dict[str, Any], seen: set[str]) -> Dict[str, Any]:
    issues: List[str] = []
    sid = clean(src.get("source_id"))
    stype = clean(src.get("source_type"))
    tier = clean(src.get("tier"))
    band = canonical_band(src)
    urls = src.get("urls") or []
    domains = src.get("domains") or []
    enabled = bool(src.get("enabled"))

    if not sid:
        issues.append("missing source_id")
    elif sid in seen:
        issues.append("duplicate source_id")
    seen.add(sid)

    if not stype:
        issues.append("missing source_type")
    if not tier:
        issues.append("missing tier")
    if band == "red" and enabled:
        issues.append("red/prohibited source cannot be enabled")
    if stype in {"official_site", "scoreboard_site", "wire"} and not urls:
        issues.append("official/cross-check source should include urls")
    for url in urls:
        if not url_ok(clean(url)):
            issues.append(f"bad url: {url}")
            break
    if stype in {"official_site", "scoreboard_site", "wire", "official_site_collection"} and band != "green":
        issues.append("official/primary source should resolve to green trust band")
    if stype in {"reddit_public_json", "mastodon_public"} and enabled:
        issues.append("community/social discovery is enabled; keep disabled until weekly review")
    if not clean(src.get("publish_policy")):
        issues.append("missing publish_policy")
    if not clean(src.get("automation_status")):
        issues.append("missing automation_status")

    status = "PASS" if not issues else "REVIEW" if all("disabled" in x or "should include" in x or "missing automation" in x for x in issues) else "FAIL"
    return {
        "source_id": sid,
        "source_type": stype,
        "tier": tier,
        "trust_band": band,
        "enabled": "Yes" if enabled else "No",
        "sport_league": clean(src.get("sport_league")),
        "automation_status": clean(src.get("automation_status")),
        "publish_policy": clean(src.get("publish_policy")),
        "status": status,
        "issues": "; ".join(issues),
        "urls_count": len(urls),
        "domains_count": len(domains),
    }


def source_matches_target(src: Dict[str, Any], target: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            clean(src.get("source_id")),
            clean(src.get("source_type")),
            clean(src.get("sport_league")),
            " ".join(clean(item) for item in src.get("allowed_use", [])),
            clean(src.get("publish_policy")),
        ]
    ).lower()
    return any(alias in text for alias in target["aliases"])


def source_kind(src: Dict[str, Any]) -> str:
    stype = clean(src.get("source_type")).lower()
    tier = clean(src.get("tier")).lower()
    trust = clean(src.get("trust_band")).lower()
    allowed = " ".join(clean(item) for item in src.get("allowed_use", [])).lower()
    sid = clean(src.get("source_id")).lower()
    if "wire" in stype or tier == "wire":
        return "wire"
    if "team" in sid or "club" in allowed or "team_news" in allowed or "official_site_collection" in stype:
        return "team"
    if "official" in stype or tier == "official":
        return "official"
    if "scoreboard" in stype or "cross_check" in trust or "cross_check" in allowed:
        return "cross_check"
    return "other"


def build_coverage_map(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    enabled_green = [
        src
        for src in sources
        if isinstance(src, dict) and src.get("enabled") and canonical_band(src) == "green"
    ]
    all_wires = [src for src in enabled_green if source_kind(src) == "wire" and clean(src.get("sport_league")).lower() == "all"]
    rows: List[Dict[str, str]] = []
    for target in COVERAGE_TARGETS:
        matched = [src for src in enabled_green if source_matches_target(src, target)]
        official = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "official")
        team = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "team")
        wire = sorted({clean(src.get("source_id")) for src in matched if source_kind(src) == "wire"} | {clean(src.get("source_id")) for src in all_wires})
        cross = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "cross_check")

        gaps: List[str] = []
        if not official and not team:
            gaps.append("missing official league/team source")
        elif target.get("needs_team_source") and not team:
            gaps.append("missing team/club source")
        if not wire:
            gaps.append("missing wire source")
        if not cross:
            gaps.append("missing scoreboard/stat/cross-check source")

        if not official and not team:
            status = "gap"
        elif target.get("needs_team_source") and not team:
            status = "watch"
        elif not wire or not cross:
            status = "watch"
        else:
            status = "covered"

        if gaps:
            next_step = target["next_step"]
        else:
            next_step = "Coverage is strong enough for normal manual review; keep monitoring existing free sources."

        rows.append(
            {
                "coverage_key": target["key"],
                "display_name": target["name"],
                "official_sources": "; ".join(official),
                "team_sources": "; ".join(team),
                "wire_sources": "; ".join(wire),
                "cross_check_sources": "; ".join(cross),
                "coverage_status": status,
                "coverage_gap": "; ".join(gaps) if gaps else "none",
                "operator_next_step": next_step,
            }
        )
    return rows


def intake_need_for_gap(gap: str) -> Dict[str, str] | None:
    if gap == "missing official league/team source":
        return {
            "needed_source_type": "official_or_team",
            "source_type": "official_site",
            "tier": "official",
            "allowed_use": "official_news; team_news; source_confirmation",
        }
    if gap == "missing team/club source":
        return {
            "needed_source_type": "team_or_club",
            "source_type": "official_site_collection",
            "tier": "official",
            "allowed_use": "team_news; roster_confirmation; source_confirmation",
        }
    if gap == "missing scoreboard/stat/cross-check source":
        return {
            "needed_source_type": "scoreboard_or_stats_cross_check",
            "source_type": "scoreboard_site",
            "tier": "stats_provider",
            "allowed_use": "cross_check; scores; schedules; standings",
        }
    if gap == "missing wire source":
        return {
            "needed_source_type": "free_wire_or_reputable_media",
            "source_type": "wire",
            "tier": "wire",
            "allowed_use": "second_source; context; source_confirmation",
        }
    return None


def build_intake_template(coverage_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for coverage in coverage_rows:
        if coverage.get("coverage_status") == "covered":
            continue
        gaps = [clean(gap) for gap in coverage.get("coverage_gap", "").split(";") if clean(gap) and clean(gap) != "none"]
        for gap in gaps:
            need = intake_need_for_gap(gap)
            if not need:
                continue
            rows.append(
                {
                    "coverage_key": coverage["coverage_key"],
                    "display_name": coverage["display_name"],
                    "needed_source_type": need["needed_source_type"],
                    "coverage_gap": gap,
                    "candidate_source_id": "",
                    "candidate_source_name": "",
                    "candidate_url": "",
                    "candidate_domain": "",
                    "source_type": need["source_type"],
                    "tier": need["tier"],
                    "trust_band": "green_candidate_after_operator_review",
                    "sport_league": coverage["display_name"],
                    "proposed_enabled": "No",
                    "automation_status": "disabled_manual_review_only",
                    "publish_policy": "proposal_only_not_publish_ready",
                    "allowed_use": need["allowed_use"],
                    "operator_verification_status": "unverified",
                    "registry_action": "proposal_only_do_not_import",
                    "review_notes": "Fill candidate fields only after checking the free public source manually.",
                }
            )
    return rows


def write_intake_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Intake Template",
        "",
        "Use this worksheet to propose free official, team, wire, or cross-check sources from coverage gaps.",
        "Rows are proposal-only and disabled by default. They do not update `config/source_registry.json`.",
        "",
        "## Guardrails",
        "",
        "- Free public sources only.",
        "- Keep `proposed_enabled` as `No` until a human review deliberately updates the source registry.",
        "- Social or gray-area sources remain discovery-only unless separately verified.",
        "- Do not add paywalled, login-only, private, or paid API sources.",
        "",
        "## Suggested rows",
        "",
    ]
    if not rows:
        lines.append("No open coverage gaps found.")
    else:
        for row in rows:
            lines.append(
                f"- {row['display_name']} | {row['needed_source_type']} | {row['coverage_gap']} | "
                f"{row['source_type']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']}"
            )
    lines += ["", "See `source_registry_intake_template.csv` for the fillable worksheet.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposal_has_candidate(row: Dict[str, str]) -> bool:
    candidate_fields = [
        "candidate_source_id",
        "candidate_source_name",
        "candidate_url",
        "candidate_domain",
        "review_notes",
    ]
    return any(clean(row.get(field)) for field in candidate_fields)


def existing_registry_indexes(sources: List[Dict[str, Any]]) -> Dict[str, set[str]]:
    source_ids: set[str] = set()
    urls: set[str] = set()
    domains: set[str] = set()
    for src in sources:
        if not isinstance(src, dict):
            continue
        sid = lower(src.get("source_id"))
        if sid:
            source_ids.add(sid)
        for url in src.get("urls") or []:
            url_text = clean(url)
            if url_text:
                urls.add(url_text.lower().rstrip("/"))
                domain = domain_from_url(url_text)
                if domain:
                    domains.add(domain)
        for domain in src.get("domains") or []:
            domain_text = lower(domain).removeprefix("www.")
            if domain_text:
                domains.add(domain_text)
    return {"source_ids": source_ids, "urls": urls, "domains": domains}


def registry_presence_for_candidate(candidate: Dict[str, str], registry_indexes: Dict[str, set[str]]) -> str:
    sid = lower(candidate.get("candidate_source_id"))
    url = clean(candidate.get("candidate_url"))
    normalized_url = url.lower().rstrip("/")
    domain = domain_from_url(url)
    if sid and sid in registry_indexes["source_ids"]:
        return "source_id_already_exists"
    if normalized_url and normalized_url in registry_indexes["urls"]:
        return "url_already_exists"
    if domain and domain in registry_indexes["domains"]:
        return "domain_already_exists_check_duplicate"
    return "not_in_registry"


def proposal_pack_coverage_context(pack: Dict[str, Any], coverage_rows: List[Dict[str, str]]) -> Dict[str, str]:
    pack_key = clean(pack.get("pack_key"))
    for row in coverage_rows:
        if row.get("coverage_key") == pack_key:
            return row
    return {
        "coverage_key": pack_key,
        "display_name": clean(pack.get("display_name") or pack.get("pack_name")),
        "coverage_status": "gap",
        "coverage_gap": clean(pack.get("fallback_coverage_gap")) or "review current source coverage",
        "operator_next_step": clean(pack.get("fallback_operator_next_step")) or "Review free official/team/cross-check coverage manually.",
    }


def build_source_proposal_pack(sources: List[Dict[str, Any]], coverage_rows: List[Dict[str, str]], pack: Dict[str, Any]) -> List[Dict[str, str]]:
    registry_indexes = existing_registry_indexes(sources)
    coverage = proposal_pack_coverage_context(pack, coverage_rows)
    pack_key = clean(pack.get("pack_key"))
    pack_name = clean(pack.get("pack_name"))
    display_name = clean(pack.get("display_name") or coverage.get("display_name") or pack_name)
    current_gap = clean(coverage.get("coverage_gap")) or f"review current {display_name} coverage"
    current_status = clean(coverage.get("coverage_status")) or "review"
    rows: List[Dict[str, str]] = []
    for candidate in pack.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        url = clean(candidate.get("candidate_url"))
        presence = registry_presence_for_candidate(candidate, registry_indexes)
        note = (
            "Open and verify this free public page manually before copying it into "
            "`operator/inbox/source_registry_proposals.csv`. Keep proposed_enabled=No; "
            "this pack never updates config/source_registry.json."
        )
        if presence != "not_in_registry":
            note += f" Registry check: {presence}."
        rows.append(
            {
                "pack_key": pack_key,
                "pack_name": pack_name,
                "candidate_group": clean(candidate.get("candidate_group")),
                "suggested_priority": clean(candidate.get("suggested_priority")),
                "coverage_key": pack_key,
                "display_name": display_name,
                "needed_source_type": clean(candidate.get("needed_source_type")),
                "coverage_gap": clean(candidate.get("coverage_gap")) or current_gap,
                "candidate_source_id": clean(candidate.get("candidate_source_id")),
                "candidate_source_name": clean(candidate.get("candidate_source_name")),
                "candidate_url": url,
                "candidate_domain": domain_from_url(url),
                "source_type": clean(candidate.get("source_type")),
                "tier": clean(candidate.get("tier")),
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": display_name,
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": clean(candidate.get("allowed_use")),
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": f"Guided {display_name} pack candidate. Current coverage status: {current_status}; current gap: {current_gap}.",
                "source_basis": clean(candidate.get("source_basis")),
                "registry_presence": presence,
                "manual_review_note": note,
            }
        )
    return rows


def build_source_proposal_packs(sources: List[Dict[str, Any]], coverage_rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    return {
        clean(pack.get("pack_key")): build_source_proposal_pack(sources, coverage_rows, pack)
        for pack in SOURCE_PROPOSAL_PACKS
        if clean(pack.get("pack_key"))
    }


def source_proposal_pack_rows(pack_rows_by_key: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for pack in SOURCE_PROPOSAL_PACKS:
        rows.extend(pack_rows_by_key.get(clean(pack.get("pack_key")), []))
    return rows


def write_source_proposal_pack_markdown(path: str | Path, rows: List[Dict[str, str]], coverage_rows: List[Dict[str, str]], pack: Dict[str, Any]) -> None:
    coverage = proposal_pack_coverage_context(pack, coverage_rows)
    pack_name = clean(pack.get("pack_name")) or "Source Proposal Pack"
    description = clean(pack.get("description")) or "Guided free-source candidates for manual review of source coverage gaps."
    lines = [
        f"# {pack_name}",
        "",
        description,
        "No rows are imported automatically, no sources are auto-enabled, and this pack does not publish anything.",
        "",
        "## Current Coverage",
        "",
        f"- status: {coverage.get('coverage_status') or 'review'}",
        f"- gap: {coverage.get('coverage_gap') or 'review current PWHL coverage'}",
        f"- operator next step: {coverage.get('operator_next_step') or 'Review free official/team/cross-check coverage manually.'}",
        "",
        "## Guardrails",
        "",
        "- Free public pages only.",
        "- Open each candidate manually before proposing it.",
        "- Keep `proposed_enabled` as `No`.",
        "- Keep `registry_action` as `proposal_only_do_not_import`.",
        "- Do not use paid APIs, paywalled pages, login-only pages, private pages, auto-runs, or auto-publishing.",
        "",
        "## Candidate Rows",
        "",
    ]
    if not rows:
        lines.append("No proposal candidates were generated.")
    else:
        configured_groups = pack.get("group_order") if isinstance(pack.get("group_order"), list) else []
        row_groups = sorted({row.get("candidate_group") for row in rows if row.get("candidate_group")})
        for group in [*configured_groups, *[item for item in row_groups if item not in configured_groups]]:
            grouped = [row for row in rows if row.get("candidate_group") == group]
            if not grouped:
                continue
            lines += [f"### {group.replace('_', ' ').title()}", ""]
            for row in grouped:
                lines.append(
                    f"- {row['suggested_priority']} | {row['candidate_source_id']} | {row['candidate_source_name']} | "
                    f"{row['candidate_url']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']} | "
                    f"registry: {row['registry_presence']}"
                )
            lines.append("")
    lines += [f"See `{pack.get('output_csv') or OUT_PROPOSAL_PACKS_CSV}` for copy-ready proposal rows.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def write_source_proposal_packs_markdown(path: str | Path, pack_rows_by_key: Dict[str, List[Dict[str, str]]], coverage_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Guided Source Proposal Packs",
        "",
        "Reusable free-source proposal packs for leagues with known coverage gaps.",
        "These packs are review guides only: no rows are imported automatically, no sources are auto-enabled, and nothing is published.",
        "",
        "## Guardrails",
        "",
        "- Free public pages only.",
        "- Keep `proposed_enabled` as `No`.",
        "- Keep `registry_action` as `proposal_only_do_not_import`.",
        "- Do not use paid APIs, paywalled pages, login-only pages, private pages, auto-runs, or auto-publishing.",
        "",
        "## Packs",
        "",
    ]
    if not pack_rows_by_key:
        lines.append("No guided source proposal packs are configured.")
    for pack in SOURCE_PROPOSAL_PACKS:
        key = clean(pack.get("pack_key"))
        rows = pack_rows_by_key.get(key, [])
        coverage = proposal_pack_coverage_context(pack, coverage_rows)
        official = sum(1 for row in rows if row.get("candidate_group") in {"league_official", "team_official"})
        cross_check = sum(1 for row in rows if "cross_check" in row.get("candidate_group", ""))
        lines += [
            f"### {clean(pack.get('pack_name')) or key}",
            "",
            f"- coverage status: {coverage.get('coverage_status') or 'review'}",
            f"- coverage gap: {coverage.get('coverage_gap') or 'review'}",
            f"- candidates: {len(rows)} total; {official} official/team; {cross_check} cross-check",
            f"- detailed report: `{pack.get('output_md') or ''}`",
            f"- detailed data: `{pack.get('output_csv') or ''}`",
            "",
        ]
        for row in rows[:6]:
            lines.append(
                f"- {row['suggested_priority']} | {row['candidate_group']} | {row['candidate_source_id']} | "
                f"{row['candidate_url']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']}"
            )
        if len(rows) > 6:
            lines.append(f"- ... {len(rows) - 6} more candidates in the CSV.")
        lines.append("")
    lines += ["See `source_proposal_packs.csv` for every configured pack row.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposal_issue_flags(row: Dict[str, str], registry_indexes: Dict[str, set[str]], seen: set[str]) -> Dict[str, List[str]]:
    issues: List[str] = []
    flags: List[str] = []
    sid = lower(row.get("candidate_source_id"))
    url = clean(row.get("candidate_url"))
    normalized_url = url.lower().rstrip("/")
    domain = lower(row.get("candidate_domain")).removeprefix("www.") or domain_from_url(url)
    source_type = lower(row.get("source_type"))
    tier = lower(row.get("tier"))
    trust = lower(row.get("trust_band"))
    enabled = lower(row.get("proposed_enabled"))
    action = lower(row.get("registry_action"))
    text = " ".join(
        [
            lower(row.get("candidate_source_name")),
            lower(row.get("candidate_url")),
            lower(row.get("candidate_domain")),
            lower(row.get("publish_policy")),
            lower(row.get("allowed_use")),
            lower(row.get("review_notes")),
        ]
    )

    if not sid:
        issues.append("missing candidate_source_id")
        flags.append("incomplete")
    elif sid in registry_indexes["source_ids"]:
        issues.append("duplicate source_id already exists in trusted registry")
        flags.append("duplicate")
    elif sid in seen:
        issues.append("duplicate source_id inside proposal inbox")
        flags.append("duplicate")
    seen.add(sid)

    if not url:
        issues.append("missing candidate_url")
        flags.append("incomplete")
    elif not url_ok(url):
        issues.append("unsafe or invalid URL; only http/https public sources are allowed")
        flags.append("unsafe_url")
    elif normalized_url in registry_indexes["urls"]:
        issues.append("duplicate URL already exists in trusted registry")
        flags.append("duplicate")

    if domain and domain in registry_indexes["domains"]:
        issues.append("candidate domain already exists in trusted registry; confirm this is not duplicate coverage")
        flags.append("duplicate_domain")

    social_domains = {
        "instagram.com", "threads.net", "x.com", "twitter.com", "tiktok.com", "facebook.com",
        "reddit.com", "mastodon.social", "bsky.app", "youtube.com", "youtu.be",
    }
    if any(domain == item or domain.endswith(f".{item}") for item in social_domains) or "social" in source_type or tier.startswith("social"):
        issues.append("social-only source cannot be added as official/wire/cross-check registry coverage")
        flags.append("social_only")

    paid_tokens = ["paid api", "paid_api", "api key", "apikey", "subscription", "subscribe", "paywall", "pricing", "premium"]
    paid_domains = ["sportradar.com", "sportsdata.io", "statsperform.com", "rapidapi.com", "serpapi.com"]
    if any(token in text for token in paid_tokens) or any(domain == item or domain.endswith(f".{item}") for item in paid_domains):
        issues.append("paid, paywalled, or API-key source is not allowed for free-first intake")
        flags.append("paid_or_api")

    login_tokens = ["login", "log-in", "signin", "sign-in", "account", "auth", "members-only", "private"]
    if any(token in text for token in login_tokens):
        issues.append("login-only or private/account source is not allowed")
        flags.append("login_only")

    unsafe_domains = ["bet365.com", "draftkings.com", "fanduel.com", "prizepicks.com", "onlyfans.com", "patreon.com"]
    if any(domain == item or domain.endswith(f".{item}") for item in unsafe_domains):
        issues.append("unsafe or off-policy source domain")
        flags.append("unsafe_domain")

    if enabled in {"yes", "true", "1"}:
        issues.append("proposal attempts to enable source; keep proposed_enabled=No until registry review")
        flags.append("auto_enable_attempt")
    if action and action != "proposal_only_do_not_import":
        issues.append("registry_action must stay proposal_only_do_not_import before human registry update")
        flags.append("unsafe_registry_action")
    if "green" not in trust:
        issues.append("trust_band should remain green_candidate_after_operator_review for source proposals")
        flags.append("needs_trust_review")

    return {"issues": issues, "flags": flags}


def build_proposal_review(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    proposal_rows = [row for row in read_run_csv(PROPOSALS) if proposal_has_candidate(row)]
    registry_indexes = existing_registry_indexes(sources)
    seen: set[str] = set()
    review_rows: List[Dict[str, str]] = []
    for row in proposal_rows:
        result = proposal_issue_flags(row, registry_indexes, seen)
        issues = result["issues"]
        flags = sorted(set(result["flags"]))
        blocking = {"duplicate", "social_only", "paid_or_api", "login_only", "unsafe_url", "unsafe_domain", "auto_enable_attempt", "unsafe_registry_action"}
        if any(flag in blocking for flag in flags):
            status = "hold"
            recommendation = "Do not add to trusted source registry until the blocking issue is resolved."
        elif issues:
            status = "review"
            recommendation = "Manually review the proposal before any registry update."
        else:
            status = "ready_for_registry_review"
            recommendation = "Candidate may be considered for a deliberate manual registry update."
        review_rows.append(
            {
                "candidate_source_id": clean(row.get("candidate_source_id")),
                "candidate_source_name": clean(row.get("candidate_source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")) or domain_from_url(clean(row.get("candidate_url"))),
                "sport_league": clean(row.get("sport_league") or row.get("display_name")),
                "source_type": clean(row.get("source_type")),
                "tier": clean(row.get("tier")),
                "proposed_enabled": clean(row.get("proposed_enabled")) or "No",
                "review_status": status,
                "issue_count": str(len(issues)),
                "issues": "; ".join(issues) if issues else "none",
                "safety_flags": "; ".join(flags) if flags else "none",
                "recommendation": recommendation,
                "registry_action": clean(row.get("registry_action")) or "proposal_only_do_not_import",
            }
        )
    return review_rows


def write_proposal_review_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Proposal Review",
        "",
        "Reviews `operator/inbox/source_registry_proposals.csv` before any manual update to `config/source_registry.json`.",
        "The report flags duplicates, paid/API sources, login-only sources, social-only sources, and unsafe proposals.",
        "",
        "## Summary",
        "",
        f"- proposals reviewed: {len(rows)}",
        f"- hold: {sum(1 for row in rows if row['review_status'] == 'hold')}",
        f"- review: {sum(1 for row in rows if row['review_status'] == 'review')}",
        f"- ready for registry review: {sum(1 for row in rows if row['review_status'] == 'ready_for_registry_review')}",
        "",
        "## Proposal rows",
        "",
    ]
    if not rows:
        lines.append("No manual source proposals found. Add rows to `operator/inbox/source_registry_proposals.csv` when ready.")
    else:
        for row in rows:
            lines.append(
                f"- **{row['review_status']}** | {row['candidate_source_id'] or 'missing_id'} | "
                f"{row['candidate_url'] or 'missing_url'} | flags: {row['safety_flags']} | {row['issues']}"
            )
    lines += ["", "No rows are imported automatically. Update the trusted registry only after deliberate human review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def main() -> None:
    raw = read_json(REGISTRY)
    sources = raw.get("sources", []) if isinstance(raw.get("sources", []), list) else []
    seen: set[str] = set()
    rows = [audit_source(src, seen) for src in sources if isinstance(src, dict)]
    coverage_rows = build_coverage_map(sources)
    intake_rows = build_intake_template(coverage_rows)
    proposal_review_rows = build_proposal_review(sources)
    proposal_pack_rows_by_key = build_source_proposal_packs(sources, coverage_rows)
    proposal_pack_rows = source_proposal_pack_rows(proposal_pack_rows_by_key)
    pwhl_proposal_pack_rows = proposal_pack_rows_by_key.get("pwhl", [])
    write_csv(OUT_CSV, rows)
    write_coverage_csv(OUT_COVERAGE_CSV, coverage_rows)
    write_intake_csv(OUT_INTAKE_CSV, intake_rows)
    write_intake_markdown(OUT_INTAKE_MD, intake_rows)
    write_proposal_review_csv(OUT_PROPOSAL_CSV, proposal_review_rows)
    write_proposal_review_markdown(OUT_PROPOSAL_MD, proposal_review_rows)
    write_source_proposal_pack_csv(OUT_PROPOSAL_PACKS_CSV, proposal_pack_rows)
    write_source_proposal_packs_markdown(OUT_PROPOSAL_PACKS_MD, proposal_pack_rows_by_key, coverage_rows)
    for pack in SOURCE_PROPOSAL_PACKS:
        pack_key = clean(pack.get("pack_key"))
        pack_rows = proposal_pack_rows_by_key.get(pack_key, [])
        if pack.get("output_csv"):
            write_source_proposal_pack_csv(pack["output_csv"], pack_rows)
        if pack.get("output_md"):
            write_source_proposal_pack_markdown(pack["output_md"], pack_rows, coverage_rows, pack)

    counts = {
        "sources": len(rows),
        "green": sum(1 for r in rows if r["trust_band"] == "green"),
        "yellow": sum(1 for r in rows if r["trust_band"] == "yellow"),
        "red": sum(1 for r in rows if r["trust_band"] == "red"),
        "pass": sum(1 for r in rows if r["status"] == "PASS"),
        "review": sum(1 for r in rows if r["status"] == "REVIEW"),
        "fail": sum(1 for r in rows if r["status"] == "FAIL"),
        "coverage_total": len(coverage_rows),
        "coverage_gap": sum(1 for r in coverage_rows if r["coverage_status"] == "gap"),
        "coverage_watch": sum(1 for r in coverage_rows if r["coverage_status"] == "watch"),
        "coverage_covered": sum(1 for r in coverage_rows if r["coverage_status"] == "covered"),
        "intake_template_rows": len(intake_rows),
        "proposal_review_rows": len(proposal_review_rows),
        "proposal_hold": sum(1 for r in proposal_review_rows if r["review_status"] == "hold"),
        "proposal_review": sum(1 for r in proposal_review_rows if r["review_status"] == "review"),
        "proposal_ready": sum(1 for r in proposal_review_rows if r["review_status"] == "ready_for_registry_review"),
        "proposal_pack_leagues": len(proposal_pack_rows_by_key),
        "proposal_pack_rows": len(proposal_pack_rows),
        "proposal_pack_official": sum(1 for r in proposal_pack_rows if r["candidate_group"] in {"league_official", "team_official"}),
        "proposal_pack_cross_check": sum(1 for r in proposal_pack_rows if "cross_check" in r["candidate_group"]),
        "pwhl_proposal_pack_rows": len(pwhl_proposal_pack_rows),
        "pwhl_proposal_pack_official": sum(1 for r in pwhl_proposal_pack_rows if r["candidate_group"] in {"league_official", "team_official"}),
        "pwhl_proposal_pack_cross_check": sum(1 for r in pwhl_proposal_pack_rows if "cross_check" in r["candidate_group"]),
    }
    run_dir = run_output_dir()
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_scope": "run_scoped" if run_dir else "legacy_root",
        "output_dir": run_dir.as_posix() if run_dir else ".",
        "counts": counts,
        "registry_version": raw.get("registry_version", ""),
        "coverage_map": coverage_rows,
        "source_registry_intake_template": intake_rows,
        "source_registry_proposal_review": proposal_review_rows,
        "source_proposal_packs": proposal_pack_rows,
        "source_proposal_pack_index": [
            {
                "pack_key": clean(pack.get("pack_key")),
                "pack_name": clean(pack.get("pack_name")),
                "rows": len(proposal_pack_rows_by_key.get(clean(pack.get("pack_key")), [])),
                "output_csv": clean(pack.get("output_csv")),
                "output_md": clean(pack.get("output_md")),
            }
            for pack in SOURCE_PROPOSAL_PACKS
        ],
        "pwhl_source_proposal_pack": pwhl_proposal_pack_rows,
    }
    write_json(OUT_JSON, manifest, indent=2)

    lines = [
        "# HSD Source Registry Audit",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Version: {VERSION}",
        f"Registry version: {raw.get('registry_version', '')}",
        "",
        f"- total sources: {counts['sources']}",
        f"- green: {counts['green']}",
        f"- yellow: {counts['yellow']}",
        f"- red: {counts['red']}",
        f"- pass: {counts['pass']}",
        f"- review: {counts['review']}",
        f"- fail: {counts['fail']}",
        f"- coverage gaps: {counts['coverage_gap']}",
        f"- coverage watch: {counts['coverage_watch']}",
        f"- coverage covered: {counts['coverage_covered']}",
        f"- source intake template rows: {counts['intake_template_rows']}",
        f"- source proposals reviewed: {counts['proposal_review_rows']}",
        f"- source proposals on hold: {counts['proposal_hold']}",
        f"- guided proposal pack leagues: {counts['proposal_pack_leagues']}",
        f"- guided proposal pack rows: {counts['proposal_pack_rows']}",
        f"- PWHL proposal pack rows: {counts['pwhl_proposal_pack_rows']}",
        "",
        "## Green source decision",
        "",
    ]
    for item in raw.get("green_approved_decision", []):
        lines.append(f"- {item}")
    lines += ["", "## Source rows needing attention", ""]
    attention = [r for r in rows if r["status"] != "PASS"]
    if attention:
        for r in attention:
            lines.append(f"- **{r['status']}** | {r['source_id']} | {r['issues']}")
    else:
        lines.append("No source registry issues detected.")
    lines += ["", "## Coverage map", ""]
    for row in coverage_rows:
        lines.append(
            f"- **{row['coverage_status'].upper()}** | {row['display_name']} | "
            f"{row['coverage_gap']} | {row['operator_next_step']}"
        )
    lines += ["", "## Manual source intake template", ""]
    if intake_rows:
        lines.append("Proposal rows were created in `source_registry_intake_template.csv`.")
        for row in intake_rows:
            lines.append(
                f"- {row['display_name']} | {row['needed_source_type']} | {row['coverage_gap']} | "
                f"{row['registry_action']}"
            )
    else:
        lines.append("No source intake proposal rows were needed.")
    lines += ["", "## Manual source proposal review", ""]
    if proposal_review_rows:
        lines.append("Manual proposal rows were reviewed in `source_registry_proposal_review.csv`.")
        for row in proposal_review_rows:
            lines.append(
                f"- **{row['review_status']}** | {row['candidate_source_id'] or 'missing_id'} | "
                f"{row['safety_flags']} | {row['issues']}"
            )
    else:
        lines.append("No manual source proposals found in `operator/inbox/source_registry_proposals.csv`.")
    lines += ["", "## Guided source proposal packs", ""]
    lines.append("Guided free-source proposal candidates were created in `source_proposal_packs.csv` and `.md`.")
    for pack in SOURCE_PROPOSAL_PACKS:
        pack_key = clean(pack.get("pack_key"))
        pack_rows = proposal_pack_rows_by_key.get(pack_key, [])
        lines.append(
            f"- {clean(pack.get('pack_name'))} | rows: {len(pack_rows)} | "
            f"data: `{clean(pack.get('output_csv'))}` | report: `{clean(pack.get('output_md'))}`"
        )
        for row in pack_rows[:5]:
            lines.append(
                f"  - {row['suggested_priority']} | {row['candidate_group']} | {row['candidate_source_id']} | "
                f"{row['registry_action']} | enabled: {row['proposed_enabled']}"
            )
        if len(pack_rows) > 5:
            lines.append(f"  - ... {len(pack_rows) - 5} more candidates in the CSV.")
    lines += ["", "## Full registry audit", "", "See `source_registry_audit.csv` for every source.", ""]
    write_text(OUT_MD, "\n".join(lines), encoding="utf-8")
    print(json.dumps({"output_scope": manifest["output_scope"], **counts}, indent=2))


if __name__ == "__main__":
    main()
