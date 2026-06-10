from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-operator-status-v3.0"
FIELDS = ["run_id","bundle_id","bundle_name","readiness","publish_eligible","reason_code","reason_detail","manual_action"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {}

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def main() -> None:
    current = read_json("hsd_current_run.json")
    run_id = current.get("run_id","")
    guard = read_json("publish_guard_report.json")
    packs = read_csv("graphics_upload_pack_status.csv")
    ready = [p for p in packs if p.get("upload_pack_status") in {"ready","ready_with_review"}]
    blocked = [p for p in packs if p.get("upload_pack_status") not in {"ready","ready_with_review"}]
    issues = guard.get("issues", [])
    if ready and not any(i.get("severity") == "critical" for i in issues):
        overall = "GO"
    elif ready:
        overall = "REVIEW"
    else:
        overall = "NO-GO"
    rows = []
    for p in ready:
        rows.append({"run_id":run_id,"bundle_id":p.get("bundle_id"),"bundle_name":p.get("bundle_name"),"readiness":p.get("upload_pack_status"),"publish_eligible":"Yes" if overall=="GO" else "Review","reason_code":"ready_upload_pack","reason_detail":p.get("zip_path"),"manual_action":"Send ready pack to graphics chat or publish path."})
    for p in blocked:
        rows.append({"run_id":run_id,"bundle_id":p.get("bundle_id"),"bundle_name":p.get("bundle_name"),"readiness":p.get("upload_pack_status"),"publish_eligible":"No","reason_code":"blocked_upload_pack","reason_detail":p.get("missing_asset_names"),"manual_action":"Resolve blocked pack reason."})
    if not rows:
        rows.append({"run_id":run_id,"bundle_id":"","bundle_name":"","readiness":overall,"publish_eligible":"No","reason_code":"no_ready_pack","reason_detail":"No ready upload packs found.","manual_action":"Check results_contract_report.md, studio_bundle_queue.csv, and graphics_upload_pack_status.csv."})
    with Path("operator_status.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    status = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "overall": overall,
        "publish_allowed": bool(guard.get("publish_allowed")) and overall == "GO",
        "ready_upload_packs": len(ready),
        "blocked_upload_packs": len(blocked),
        "issues": issues,
        "manual_actions": [r["manual_action"] for r in rows],
    }
    Path("operator_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    Path("operator_status.md").write_text(
        "# HSD Operator Status\n\n"
        f"Generated: {status['generated_at_utc']}\n\n"
        f"## {overall}\n\n"
        f"- Ready upload packs: {len(ready)}\n"
        f"- Blocked upload packs: {len(blocked)}\n"
        f"- Publish allowed: {status['publish_allowed']}\n\n"
        + "\n".join(f"- {r['bundle_name'] or 'Pipeline'}: {r['readiness']} — {r['manual_action']}" for r in rows) + "\n",
        encoding="utf-8"
    )
    print(json.dumps({"overall": overall, "ready": len(ready)}, indent=2))

if __name__ == "__main__":
    main()
