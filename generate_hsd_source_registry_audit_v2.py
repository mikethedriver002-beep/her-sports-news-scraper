from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from hsd_run_io import input_path, run_output_dir, write_csv as write_run_csv, write_json, write_text

VERSION = "hsd-source-registry-audit-bebe-v2.5-coverage-map"
REGISTRY = "config/source_registry.json"
OUT_CSV = "source_registry_audit.csv"
OUT_COVERAGE_CSV = "source_coverage_map.csv"
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


def main() -> None:
    raw = read_json(REGISTRY)
    sources = raw.get("sources", []) if isinstance(raw.get("sources", []), list) else []
    seen: set[str] = set()
    rows = [audit_source(src, seen) for src in sources if isinstance(src, dict)]
    coverage_rows = build_coverage_map(sources)
    write_csv(OUT_CSV, rows)
    write_coverage_csv(OUT_COVERAGE_CSV, coverage_rows)

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
    lines += ["", "## Full registry audit", "", "See `source_registry_audit.csv` for every source.", ""]
    write_text(OUT_MD, "\n".join(lines), encoding="utf-8")
    print(json.dumps({"output_scope": manifest["output_scope"], **counts}, indent=2))


if __name__ == "__main__":
    main()
