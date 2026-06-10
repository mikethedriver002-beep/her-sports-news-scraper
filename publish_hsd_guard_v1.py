from __future__ import annotations
import csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-publish-guard-v3.0"
OUT_JSON = Path("publish_guard_report.json")
OUT_MD = Path("publish_guard_report.md")
LEDGER = Path("audit/publish_ledger.jsonl")

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def fingerprint(row: Dict[str, str]) -> str:
    blob = "|".join([clean(row.get("content_type")), clean(row.get("headline")), clean(row.get("event_date")), clean(row.get("source_id"))])
    return hashlib.sha256(blob.encode()).hexdigest()

def load_ledger() -> set[str]:
    if not LEDGER.exists():
        return set()
    vals = set()
    for line in LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            j = json.loads(line)
            vals.add(j.get("publish_fingerprint",""))
        except Exception:
            pass
    return vals

def main() -> None:
    slate = read_csv("daily_slate_plan.csv")
    upload_rows = read_csv("graphics_upload_pack_status.csv")
    ready_packs = [r for r in upload_rows if r.get("upload_pack_status") in {"ready","ready_with_review"}]
    ledger = load_ledger()
    issues = []
    decisions = []
    for r in slate:
        fp = fingerprint(r)
        if fp in ledger:
            issues.append({"severity":"critical","code":"duplicate_publish_fingerprint","headline":r.get("headline")})
        decisions.append({"headline":r.get("headline"),"content_type":r.get("content_type"),"fingerprint":fp,"status":"candidate"})
    if not slate and not ready_packs:
        issues.append({"severity":"critical","code":"no_content_ready","detail":"No slate items and no ready graphics upload pack."})
    if upload_rows and not ready_packs:
        issues.append({"severity":"critical","code":"no_ready_upload_pack","detail":"Graphics packs exist but none are ready."})
    publish_allowed = not any(i["severity"] == "critical" for i in issues)
    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "publish_allowed": publish_allowed,
        "ready_upload_packs": len(ready_packs),
        "slate_items": len(slate),
        "issues": issues,
        "decisions": decisions,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# HSD Publish Guard", "", f"Generated: {report['generated_at_utc']}", "", f"- publish_allowed: {publish_allowed}", f"- ready_upload_packs: {len(ready_packs)}", f"- slate_items: {len(slate)}", ""]
    if issues:
        lines += ["## Issues", ""] + [f"- {i['severity']} | {i['code']} | {i.get('detail') or i.get('headline','')}" for i in issues] + [""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"publish_allowed": publish_allowed, "issues": len(issues)}, indent=2))

if __name__ == "__main__":
    main()
