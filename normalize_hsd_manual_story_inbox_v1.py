from __future__ import annotations
import csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from typing import Any, Dict, List

VERSION = "hsd-manual-story-inbox-v3.0"

CSV_PATH = Path("operator/inbox/story_inbox.csv")
JSONL_PATH = Path("operator/inbox/story_inbox.jsonl")
OUT_JSONL = Path("story_candidates_manual.jsonl")
OUT_CSV = Path("story_candidates_manual.csv")
OUT_REPORT = Path("manual_story_inbox_report.md")

FIELDS = [
    "story_id","input_type","source_url","canonical_url","title","summary","sport","league","story_kind",
    "priority","verification_status","status","idempotency_key","requires_second_source","evidence_urls_json",
    "fact_lock_json","publish_not_after_utc","risk_tier","publish_eligible","reason"
]

STRIP_PARAMS = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","fbclid","gclid"}

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
    base = canonicalize(url) or clean(title)
    return "story_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:14]

def risk_tier_for(url: str, input_type: str) -> str:
    host = urlsplit(url).netloc.lower() if url else ""
    if input_type in {"x_url_manual", "instagram_url_manual", "threads_url_manual", "tiktok_url_manual"}:
        return "yellow_social_manual"
    if any(x in host for x in ["wnba.com","nwsl","espn","apnews","reuters","fifa","volleyballworld"]):
        return "green_official_or_primary"
    if any(x in host for x in ["reddit.com","mastodon"]):
        return "yellow_discovery_only"
    return "yellow_unclassified"

def eligible(row: Dict[str, Any]) -> tuple[str, str]:
    status = clean(row.get("status")) or "queued"
    verification = clean(row.get("verification_status")) or "pending"
    risk = clean(row.get("risk_tier"))
    if status not in {"approved", "queued"}:
        return "No", f"status={status}"
    if verification not in {"verified_official", "verified_multi_source", "operator_verified"}:
        return "No", f"verification_status={verification}"
    if risk.startswith("yellow") and clean(row.get("requires_second_source")).lower() in {"true","yes","1"}:
        evidence = clean(row.get("evidence_urls_json"))
        if evidence in {"", "[]"}:
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
    rows = []
    for line in JSONL_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            j = json.loads(line)
        except Exception:
            continue
        if j.get("story_id") == "example_manual_story":
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
    out["story_id"] = clean(row.get("story_id")) or story_id_for(out["canonical_url"], out.get("title",""))
    out["input_type"] = clean(row.get("input_type")) or "url"
    out["status"] = clean(row.get("status")) or "queued"
    out["verification_status"] = clean(row.get("verification_status")) or "pending"
    out["story_kind"] = clean(row.get("story_kind")) or "breaking"
    out["priority"] = clean(row.get("priority")) or "P2"
    out["idempotency_key"] = clean(row.get("idempotency_key")) or story_id_for(out["canonical_url"], out.get("title",""))
    out["risk_tier"] = risk_tier_for(out["canonical_url"], out["input_type"])
    out["publish_eligible"], out["reason"] = eligible(out)
    return out

def main() -> None:
    rows = [normalize(r) for r in read_csv_rows() + read_jsonl_rows()]
    # dedupe by idempotency key
    by_key = {}
    for r in rows:
        if not r["source_url"] and not r["title"]:
            continue
        by_key[r["idempotency_key"]] = r
    rows = list(by_key.values())

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")
    eligible_count = sum(1 for r in rows if r["publish_eligible"] == "Yes")
    lines = [
        "# HSD Manual Story Inbox Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- candidates: {len(rows)}",
        f"- publish eligible: {eligible_count}",
        "",
    ]
    for r in rows[:25]:
        lines.append(f"- {r['publish_eligible']} | {r['story_kind']} | {r['title'] or r['source_url']} | {r['reason']}")
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"manual_candidates": len(rows), "publish_eligible": eligible_count}, indent=2))

if __name__ == "__main__":
    main()
