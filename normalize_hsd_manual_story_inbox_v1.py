from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

VERSION = "hsd-manual-story-inbox-v3.2.5-bebe-ops-v2.4"

CSV_PATH = Path("operator/inbox/story_inbox.csv")
JSONL_PATH = Path("operator/inbox/story_inbox.jsonl")
OUT_JSONL = Path("story_candidates_manual.jsonl")
OUT_CSV = Path("story_candidates_manual.csv")
OUT_REPORT = Path("manual_story_inbox_report.md")
REGISTRY_PATH = Path("config/source_registry.json")

FIELDS = [
    "story_id", "input_type", "source_url", "canonical_url", "title", "summary", "sport", "league", "story_kind",
    "priority", "verification_status", "status", "idempotency_key", "requires_second_source", "evidence_urls_json",
    "fact_lock_json", "publish_not_after_utc", "risk_tier", "source_trust_band", "publish_eligible", "reason",
]

STRIP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}

BUILTIN_GREEN_DOMAINS = [
    "wnba.com", "nba.com", "nwslsoccer.com", "wtatennis.com", "lpga.com", "volleyballworld.com",
    "ncaa.com", "ussoccer.com", "fifa.com", "concacaf.com", "apnews.com", "reuters.com",
    "espn.com", "cbssports.com", "sports-reference.com",
]
BUILTIN_YELLOW_DOMAINS = ["instagram.com", "threads.net", "x.com", "twitter.com", "tiktok.com", "reddit.com", "mastodon"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def canonicalize(url: str) -> str:
    url = clean(url)
    if not url:
        return ""
    try:
        s = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if k not in STRIP_PARAMS]
        return urlunsplit((s.scheme.lower(), s.netloc.lower(), s.path.rstrip("/") or "/", urlencode(query), ""))
    except Exception:
        return url


def story_id_for(url: str, title: str) -> str:
    base = canonicalize(url) or clean(title) or datetime.now(timezone.utc).isoformat()
    return "story_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:14]


def host_for(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def load_registry_domains() -> Tuple[List[str], List[str], List[str]]:
    green: List[str] = []
    yellow: List[str] = []
    red: List[str] = []
    if REGISTRY_PATH.exists():
        try:
            raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            for src in raw.get("sources", []):
                domains = [clean(d).lower().removeprefix("www.") for d in src.get("domains", []) if clean(d)]
                band = clean(src.get("trust_band") or src.get("tier")).lower()
                tier = clean(src.get("tier")).lower()
                if not domains:
                    continue
                if "red" in band or tier in {"red", "prohibited"}:
                    red.extend(domains)
                elif "green" in band or tier in {"official", "operator", "wire", "primary_media", "stats_provider"}:
                    green.extend(domains)
                else:
                    yellow.extend(domains)
        except Exception:
            pass
    return sorted(set(green)), sorted(set(yellow)), sorted(set(red))


def domain_matches(host: str, domains: List[str]) -> bool:
    return any(host == d or host.endswith("." + d) or d in host for d in domains if d)


def risk_tier_for(url: str, input_type: str) -> Tuple[str, str]:
    host = host_for(url)
    green_domains, yellow_domains, red_domains = load_registry_domains()
    green_domains = sorted(set(BUILTIN_GREEN_DOMAINS + green_domains))
    yellow_domains = sorted(set(BUILTIN_YELLOW_DOMAINS + yellow_domains))

    if domain_matches(host, red_domains):
        return "red_prohibited", "red"
    if input_type in {"x_url_manual", "instagram_url_manual", "threads_url_manual", "tiktok_url_manual"}:
        return "yellow_social_manual", "yellow"
    if domain_matches(host, green_domains):
        return "green_official_or_primary", "green"
    if domain_matches(host, yellow_domains):
        return "yellow_discovery_only", "yellow"
    return "yellow_unclassified", "yellow"


def parse_jsonish(value: str, default: Any) -> Any:
    value = clean(value)
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        if ";" in value:
            return [x.strip() for x in value.split(";") if x.strip()]
        return default


def eligible(row: Dict[str, Any]) -> Tuple[str, str]:
    status = clean(row.get("status")) or "queued"
    verification = clean(row.get("verification_status")) or "pending"
    risk = clean(row.get("risk_tier"))
    trust = clean(row.get("source_trust_band"))
    evidence = parse_jsonish(clean(row.get("evidence_urls_json")), [])
    facts = parse_jsonish(clean(row.get("fact_lock_json")), [])

    if status not in {"approved", "queued"}:
        return "No", f"status={status}"
    if risk.startswith("red") or trust == "red":
        return "No", "red/prohibited source policy"
    if verification not in {"verified_official", "verified_multi_source", "operator_verified"}:
        return "No", f"verification_status={verification}"
    if not facts:
        return "No", "missing fact_lock_json"
    if risk.startswith("yellow") and clean(row.get("requires_second_source")).lower() in {"true", "yes", "1"} and not evidence:
        return "No", "yellow-risk source requires supporting evidence"
    return "Yes", "manual story eligible"


def read_csv_rows() -> List[Dict[str, Any]]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def read_jsonl_rows() -> List[Dict[str, Any]]:
    if not JSONL_PATH.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in JSONL_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            j = json.loads(line)
        except Exception:
            continue
        if j.get("story_id") in {"example_manual_story", "example_delete_me"}:
            continue
        verification = j.get("verification", {}) or {}
        publish_window = j.get("publish_window", {}) or {}
        rows.append({
            "story_id": j.get("story_id", ""),
            "input_type": j.get("input_type", "url"),
            "source_url": j.get("source_url", ""),
            "canonical_url": j.get("canonical_url", ""),
            "title": j.get("title", ""),
            "summary": j.get("summary", ""),
            "sport": j.get("sport", ""),
            "league": j.get("league", ""),
            "story_kind": j.get("story_kind", "breaking"),
            "priority": j.get("priority", "P2"),
            "verification_status": verification.get("status", "pending"),
            "status": j.get("status", "queued"),
            "idempotency_key": j.get("idempotency_key", ""),
            "requires_second_source": str(verification.get("requires_second_source", True)),
            "evidence_urls_json": json.dumps(verification.get("evidence_urls", []), ensure_ascii=False),
            "fact_lock_json": json.dumps(verification.get("fact_lock", []), ensure_ascii=False),
            "publish_not_after_utc": publish_window.get("not_after_utc", ""),
        })
    return rows


def normalize(row: Dict[str, Any]) -> Dict[str, str]:
    out = {k: clean(row.get(k, "")) for k in FIELDS}
    out["source_url"] = clean(row.get("source_url") or row.get("url") or row.get("link"))
    out["canonical_url"] = clean(row.get("canonical_url")) or canonicalize(out["source_url"])
    out["story_id"] = clean(row.get("story_id")) or story_id_for(out["canonical_url"], out.get("title", ""))
    out["input_type"] = clean(row.get("input_type")) or "url"
    out["status"] = clean(row.get("status")) or "queued"
    out["verification_status"] = clean(row.get("verification_status")) or "pending"
    out["story_kind"] = clean(row.get("story_kind")) or "breaking"
    out["priority"] = clean(row.get("priority")) or "P2"
    out["idempotency_key"] = clean(row.get("idempotency_key")) or story_id_for(out["canonical_url"], out.get("title", ""))
    out["requires_second_source"] = clean(row.get("requires_second_source")) or "true"
    out["evidence_urls_json"] = clean(row.get("evidence_urls_json")) or "[]"
    out["fact_lock_json"] = clean(row.get("fact_lock_json")) or "[]"
    out["risk_tier"], out["source_trust_band"] = risk_tier_for(out["canonical_url"], out["input_type"])
    out["publish_eligible"], out["reason"] = eligible(out)
    return out


def main() -> None:
    rows = [normalize(r) for r in read_csv_rows() + read_jsonl_rows()]
    by_key: Dict[str, Dict[str, str]] = {}
    for r in rows:
        if r.get("story_id") == "example_delete_me":
            continue
        if not r["source_url"] and not r["title"]:
            continue
        by_key[r["idempotency_key"]] = r
    rows = list(by_key.values())

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")

    eligible_count = sum(1 for r in rows if r["publish_eligible"] == "Yes")
    lines = [
        "# HSD Manual Story Inbox Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Version: {VERSION}",
        f"- candidates: {len(rows)}",
        f"- publish eligible: {eligible_count}",
        f"- yellow/unverified blocked: {sum(1 for r in rows if r['publish_eligible'] != 'Yes')}",
        "",
        "## Candidates",
        "",
    ]
    for r in rows[:50]:
        lines.append(f"- {r['publish_eligible']} | {r['priority']} | {r['story_kind']} | {r['source_trust_band']} | {r['title'] or r['source_url']} | {r['reason']}")
    if not rows:
        lines += [
            "No manual stories found.",
            "",
            "Use `operator/inbox/story_inbox_template_v2.csv` as the template. Copy it to `operator/inbox/story_inbox.csv` and delete the example row.",
        ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"manual_candidates": len(rows), "publish_eligible": eligible_count}, indent=2))


if __name__ == "__main__":
    main()
