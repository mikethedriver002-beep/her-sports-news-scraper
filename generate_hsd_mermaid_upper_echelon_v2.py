
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

import subprocess, sys

VERSION = "v3.3.0-mermaid-upper-echelon-control-plane"
OUT_MD = "mermaid_upper_echelon_report.md"
OUT_JSON = "mermaid_upper_echelon_manifest.json"

STEPS = [
    ("Social Rumor Desk", "generate_hsd_social_rumor_desk_v1.py"),
    ("Multi-Sport Scout", "generate_hsd_multisport_scout_v2.py"),
    ("Official Player Backfill", "generate_hsd_official_player_backfill_v1.py"),
    ("Player Registry v2", "generate_hsd_player_registry_v2.py"),
    ("Story Graph", "generate_hsd_mermaid_story_graph_v1.py"),
    ("Prompt Compiler v2", "generate_hsd_mermaid_prompt_compiler_v2.py"),
    ("Content Engine v2", "generate_hsd_mermaid_content_engine_v2.py"),
]

def run_step(name: str, script: str) -> Dict[str, Any]:
    p = Path(script)
    if not p.exists():
        return {"name": name, "script": script, "status": "missing", "returncode": 127}
    try:
        proc = subprocess.run([sys.executable, script], text=True, capture_output=True, timeout=120)
        return {"name": name, "script": script, "status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-3000:]}
    except Exception as exc:
        return {"name": name, "script": script, "status": "exception", "returncode": 999, "stderr": type(exc).__name__ + ": " + str(exc)}

def main() -> None:
    results = [run_step(name, script) for name, script in STEPS]
    counts = {
        "story_graph_rows": len(read_csv("mermaid_story_graph.csv")),
        "compiled_packets": len(read_csv("mermaid_compiled_packet_index.csv")),
        "content_slots": len(read_csv("mermaid_content_slots_v2.csv")),
        "multisport_candidates": len(read_csv("multisport_scout_candidates.csv")),
        "rumor_claims": len(read_csv("social_rumor_candidates.csv")),
        "player_asset_debt": len(read_csv("player_asset_debt.csv")),
    }
    Path(OUT_JSON).write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "steps": results, "counts": counts}, indent=2), encoding="utf-8")
    lines = ["# HSD Mermaid Upper Echelon Report", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Counts", ""]
    lines += [f"- {k}: {v}" for k,v in counts.items()]
    lines += ["", "## Step status", ""]
    for r in results:
        lines.append(f"- {r['name']}: {r['status']} ({r['returncode']})")
    lines += ["", "## Next operator focus", ""]
    if counts["player_asset_debt"]:
        lines.append("- Fill player asset debt before relying on player-led preview graphics.")
    if counts["multisport_candidates"]:
        lines.append("- Review multi-sport scout candidates for non-WNBA posts.")
    if counts["rumor_claims"]:
        lines.append("- Review rumor desk claims; confirmed/corroborated only should move to publish lanes.")
    lines.append("- Keep publish mode artifact-only until rendered QA passes.")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2))

if __name__ == "__main__":
    main()
