from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v3.3.6-mermaid-assignment-handoff-v2.6-bridge"
OUT_MD = Path("mermaid_upper_echelon_report.md")
OUT_JSON = Path("mermaid_upper_echelon_manifest.json")

STEPS = [
    ("Social Rumor Desk", "generate_hsd_social_rumor_desk_v1.py"),
    ("Multi-Sport Scout", "generate_hsd_multisport_scout_v2.py"),
    ("Official Player Backfill", "generate_hsd_official_player_backfill_v1.py"),
    ("Player Registry v2", "generate_hsd_player_registry_v2.py"),
    ("Story Graph", "generate_hsd_mermaid_story_graph_v1.py"),
    ("Prompt Compiler v2", "generate_hsd_mermaid_prompt_compiler_v2.py"),
    ("Content Engine v2", "generate_hsd_mermaid_content_engine_v2.py"),
    ("Quality Brain v2.1", "generate_hsd_mermaid_quality_brain_v2_1.py"),
    ("Quality Brain v2.2", "generate_hsd_mermaid_quality_brain_v2_2.py"),
    ("Content Director v2.3", "generate_hsd_mermaid_content_director_v2_3.py"),
    ("Assignment Desk v2.4", "generate_hsd_mermaid_assignment_desk_v2_4.py"),
    ("Assignment Freshness Gate v2.5", "generate_hsd_mermaid_assignment_freshness_gate_v2_5.py"),
    ("Assignment Handoff v2.6", "generate_hsd_mermaid_assignment_handoff_v2_6.py"),
]

ALIASES = [
    ("mermaid_assignment_freshness_gate_report.md", "mermaid_master_content_board.md"),
    ("mermaid_assignment_final_slots.csv", "mermaid_content_slots_v2.csv"),
    ("ig_feed_queue_v2_5.csv", "ig_feed_queue_v2.csv"),
    ("ig_story_queue_v2_5.csv", "ig_story_queue_v2.csv"),
    ("threads_queue_v2_5.csv", "threads_queue_v2.csv"),
    ("mermaid_assignment_final_prompt_index.csv", "mermaid_compiled_packet_index.csv"),
    ("assignment_handoff_report.md", "manual_workflow_handoff.md"),
    ("assignment_handoff_index.csv", "manual_workflow_content_packets.csv"),
]


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


def run_step(name: str, script: str) -> Dict[str, Any]:
    if not Path(script).exists():
        return {"name": name, "script": script, "status": "missing", "returncode": 127}
    try:
        proc = subprocess.run([sys.executable, script], text=True, capture_output=True, timeout=240)
        return {"name": name, "script": script, "status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-2500:], "stderr": proc.stderr[-2500:]}
    except Exception as exc:
        return {"name": name, "script": script, "status": "exception", "returncode": 999, "stderr": type(exc).__name__ + ": " + str(exc)}


def copy_alias(src: str, dst: str) -> bool:
    s = Path(src)
    d = Path(dst)
    if not s.exists():
        return False
    if s.is_dir():
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)
    return True


def bridge_outputs() -> List[str]:
    actions: List[str] = []
    for src, dst in ALIASES:
        if copy_alias(src, dst):
            actions.append(f"{src} -> {dst}")
    if Path("mermaid_assignment_final_packets").exists():
        copy_alias("mermaid_assignment_final_packets", "mermaid_compiled_packets")
        actions.append("mermaid_assignment_final_packets -> mermaid_compiled_packets")
    if Path("assignment_handoff_packets").exists():
        copy_alias("assignment_handoff_packets", "manual_workflow_packets")
        actions.append("assignment_handoff_packets -> manual_workflow_packets")
    if Path("assignment_handoff_zips").exists():
        copy_alias("assignment_handoff_zips", "manual_workflow_handoff_packs")
        actions.append("assignment_handoff_zips -> manual_workflow_handoff_packs")
    return actions


def counts() -> Dict[str, int]:
    return {
        "final_slots": len(read_csv("mermaid_assignment_final_slots.csv")),
        "held_slots": len(read_csv("assignment_freshness_held_slots.csv")),
        "feed_rows": len(read_csv("ig_feed_queue_v2.csv")),
        "story_rows": len(read_csv("ig_story_queue_v2.csv")),
        "thread_rows": len(read_csv("threads_queue_v2.csv")),
        "compiled_packets": len(read_csv("mermaid_compiled_packet_index.csv")),
        "handoff_packets": len(read_csv("assignment_handoff_index.csv")),
        "handoff_held": len([r for r in read_csv("assignment_handoff_status.csv") if r.get("status") == "held"]),
        "player_asset_debt": len(read_csv("player_asset_debt.csv")),
    }


def main() -> None:
    results = [run_step(name, script) for name, script in STEPS]
    bridge = bridge_outputs()
    c = counts()
    manifest = {"version": VERSION, "generated_at": now_iso(), "steps": results, "bridge_actions": bridge, "counts": c}
    OUT_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = ["# HSD Mermaid Upper Echelon Report", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Counts", ""]
    lines += [f"- {k}: {v}" for k, v in c.items()]
    lines += ["", "## Step status", ""]
    for r in results:
        lines.append(f"- {r['name']}: {r['status']} ({r['returncode']})")
    lines += ["", "## Output bridge", ""]
    lines += [f"- {b}" for b in bridge] if bridge else ["- No aliases created."]
    for report in ["mermaid_assignment_freshness_gate_report.md", "assignment_handoff_report.md"]:
        p = Path(report)
        if p.exists():
            lines += ["", "---", "", p.read_text(encoding="utf-8", errors="replace")]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(c, indent=2))


if __name__ == "__main__":
    main()
