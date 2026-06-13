
from __future__ import annotations
import csv, json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Iterable

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def write_csv(path: str | Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def read_json(path: str | Path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default

def story_id(*parts: Any) -> str:
    h = hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]
    return "story_" + h

def score_priority(league: str, kind: str, source_state: str = "") -> str:
    l = clean(league).upper()
    if kind in {"breaking", "rumor_confirmed"}:
        return "P0"
    if l == "WNBA":
        return "P1"
    if l in {"WTA", "NWSL"}:
        return "P2"
    if l in {"LPGA", "VNL", "VOLLEYBALL"}:
        return "P3"
    return "P4"

VERSION = "v3.3.0-mermaid-social-rumor-desk-v1"
INBOX = Path("operator/inbox/social_rumor_inbox.csv")
OUT_CSV = "social_rumor_candidates.csv"
OUT_MD = "social_rumor_desk_report.md"
OUT_JSON = "social_rumor_desk_manifest.json"
FIELDS = ["claim_id","platform","source_url","source_handle","claim_text","sport","league","teams_people","claim_type","verification_state","publish_lane","priority","required_next_step","notes"]

def classify(row: Dict[str,str]) -> Dict[str,str]:
    hint = clean(row.get("verification_hint")).lower()
    text = (clean(row.get("claim_text")) + " " + clean(row.get("operator_notes"))).lower()
    if "official" in hint or "confirmed" in hint or "team announced" in text or "league announced" in text:
        state = "confirmed_official"; lane = "breaking_ready_with_review"; priority = "P0"; step = "verify source URL is official, then write attributed copy"
    elif "two" in hint or "corroborated" in hint:
        state = "corroborated_report"; lane = "review_with_attribution"; priority = "P1"; step = "add second source/evidence before IG; Threads review ok"
    elif "debunk" in hint or "false" in text:
        state = "debunked"; lane = "do_not_publish"; priority = "P9"; step = "archive as debunked so it is not re-amplified"
    elif "buzz" in hint or "social" in hint:
        state = "social_buzz"; lane = "hold_social_buzz"; priority = "P4"; step = "wait for official/reputable confirmation"
    else:
        state = "single_source_report"; lane = "manual_review_only"; priority = "P3"; step = "verify provenance, date, original source, and official response"
    return {"verification_state": state, "publish_lane": lane, "priority": priority, "required_next_step": step}

def main() -> None:
    rows = []
    for r in read_csv(INBOX):
        c = classify(r)
        rows.append({
            "claim_id": clean(r.get("claim_id")) or story_id(r.get("source_url"), r.get("claim_text")),
            "platform": clean(r.get("platform")),
            "source_url": clean(r.get("source_url")),
            "source_handle": clean(r.get("source_handle")),
            "claim_text": clean(r.get("claim_text")),
            "sport": clean(r.get("sport")),
            "league": clean(r.get("league")),
            "teams_people": clean(r.get("teams_people")),
            "claim_type": clean(r.get("claim_type")),
            "verification_state": c["verification_state"],
            "publish_lane": c["publish_lane"],
            "priority": c["priority"],
            "required_next_step": c["required_next_step"],
            "notes": clean(r.get("operator_notes")),
        })
    write_csv(OUT_CSV, rows, FIELDS)
    lines = ["# HSD Social Rumor Desk", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- claims: {len(rows)}", ""]
    if not rows:
        lines += ["No social rumor claims submitted. Copy `operator/inbox/social_rumor_inbox_template_v1.csv` to `social_rumor_inbox.csv` to use this lane.", ""]
    else:
        for r in rows:
            lines.append(f"- **{r['verification_state']}** / {r['publish_lane']}: {r['claim_text']} — {r['required_next_step']}")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "claims": len(rows)}, indent=2), encoding="utf-8")
    print(json.dumps({"rumor_claims": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
