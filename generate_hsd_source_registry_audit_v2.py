from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

VERSION = "hsd-source-registry-audit-bebe-v2.4"
REGISTRY = Path("config/source_registry.json")
OUT_CSV = Path("source_registry_audit.csv")
OUT_MD = Path("source_registry_audit.md")
OUT_JSON = Path("source_registry_audit.json")

FIELDS = [
    "source_id", "source_type", "tier", "trust_band", "enabled", "sport_league", "automation_status",
    "publish_policy", "status", "issues", "urls_count", "domains_count",
]

GREEN_TIERS = {"official", "operator", "wire", "primary_media", "stats_provider"}
YELLOW_TIERS = {"social", "social_manual", "community", "discovery", "media_review"}
RED_TIERS = {"red", "prohibited"}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


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


def main() -> None:
    raw = read_json(REGISTRY)
    sources = raw.get("sources", []) if isinstance(raw.get("sources", []), list) else []
    seen: set[str] = set()
    rows = [audit_source(src, seen) for src in sources if isinstance(src, dict)]
    write_csv(OUT_CSV, rows)

    counts = {
        "sources": len(rows),
        "green": sum(1 for r in rows if r["trust_band"] == "green"),
        "yellow": sum(1 for r in rows if r["trust_band"] == "yellow"),
        "red": sum(1 for r in rows if r["trust_band"] == "red"),
        "pass": sum(1 for r in rows if r["status"] == "PASS"),
        "review": sum(1 for r in rows if r["status"] == "REVIEW"),
        "fail": sum(1 for r in rows if r["status"] == "FAIL"),
    }
    OUT_JSON.write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "registry_version": raw.get("registry_version", ""),
    }, indent=2), encoding="utf-8")

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
    lines += ["", "## Full registry audit", "", "See `source_registry_audit.csv` for every source.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
