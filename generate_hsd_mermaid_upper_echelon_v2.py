from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


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


def read_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def write_text(path: str | Path, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def copy_if_exists(src: str | Path, dst: str | Path) -> bool:
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


VERSION = "v3.3.3-mermaid-upper-echelon-content-director-v2.3-bridge"
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
    ("Quality Brain v2.1", "generate_hsd_mermaid_quality_brain_v2_1.py"),
    ("Quality Brain v2.2", "generate_hsd_mermaid_quality_brain_v2_2.py"),
    ("Content Director v2.3", "generate_hsd_mermaid_content_director_v2_3.py"),
]


def run_step(name: str, script: str) -> Dict[str, Any]:
    p = Path(script)
    if not p.exists():
        return {"name": name, "script": script, "status": "missing", "returncode": 127}
    try:
        proc = subprocess.run([sys.executable, script], text=True, capture_output=True, timeout=240)
        return {
            "name": name,
            "script": script,
            "status": "ok" if proc.returncode == 0 else "error",
            "returncode": proc.returncode,
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-5000:],
        }
    except Exception as exc:
        return {
            "name": name,
            "script": script,
            "status": "exception",
            "returncode": 999,
            "stderr": type(exc).__name__ + ": " + str(exc),
        }


def bridge_quality_outputs() -> List[str]:
    actions: List[str] = []
    aliases = [
        ("mermaid_content_director_report.md", "mermaid_master_content_board.md"),
        ("mermaid_director_story_graph.csv", "mermaid_story_graph.csv"),
        ("mermaid_director_content_slots.csv", "mermaid_content_slots_v2.csv"),
        ("ig_feed_queue_v2_3.csv", "ig_feed_queue_v2.csv"),
        ("ig_story_queue_v2_3.csv", "ig_story_queue_v2.csv"),
        ("threads_queue_v2_3.csv", "threads_queue_v2.csv"),
        ("mermaid_director_prompt_index.csv", "mermaid_compiled_packet_index.csv"),
        ("content_director_sport_floor_status.csv", "multisport_sport_floor_status.csv"),
        ("content_director_rejected_wrong_sport.csv", "multisport_wrong_sport_rejections.csv"),
    ]
    for src, dst in aliases:
        if copy_if_exists(src, dst):
            actions.append(f"aliased {src} -> {dst}")
    if Path("mermaid_director_compiled_packets").exists():
        copy_if_exists("mermaid_director_compiled_packets", "mermaid_compiled_packets")
        actions.append("aliased mermaid_director_compiled_packets -> mermaid_compiled_packets")
    return actions


def counts() -> Dict[str, int]:
    return {
        "story_graph_rows": len(read_csv("mermaid_story_graph.csv")),
        "compiled_packets": len(read_csv("mermaid_compiled_packet_index.csv")),
        "content_slots": len(read_csv("mermaid_content_slots_v2.csv")),
        "multisport_candidates_raw": len(read_csv("multisport_scout_candidates.csv")),
        "multisport_candidates_filtered": len(read_csv("multisport_scout_candidates_filtered.csv")),
        "multisport_candidates_rejected": len(read_csv("multisport_rejected_candidates.csv")),
        "rumor_claims": len(read_csv("social_rumor_candidates.csv")),
        "player_asset_debt": len(read_csv("player_asset_debt.csv")),
        "director_story_graph_rows": len(read_csv("mermaid_director_story_graph.csv")),
        "director_slots": len(read_csv("mermaid_director_content_slots.csv")),
        "director_packets": len(read_csv("mermaid_director_prompt_index.csv")),
        "director_wrong_sport_rejections": len(read_csv("content_director_rejected_wrong_sport.csv")),
        "director_crossposts": len(read_csv("content_director_crosspost_plan.csv")),
    }


def main() -> None:
    results = [run_step(name, script) for name, script in STEPS]
    bridge_actions = bridge_quality_outputs()
    c = counts()
    manifest = {
        "version": VERSION,
        "generated_at": now_iso(),
        "steps": results,
        "bridge_actions": bridge_actions,
        "counts": c,
        "content_director_present": Path("mermaid_content_director_report.md").exists(),
    }
    write_text(OUT_JSON, json.dumps(manifest, indent=2))
    lines = [
        "# HSD Mermaid Upper Echelon Report",
        "",
        f"Generated: {now_iso()}",
        f"Version: {VERSION}",
        "",
        "## Status",
        "",
        "Upper Echelon ran with Content Director v2.3. Director outputs are aliased into the normal artifact paths so the operator can stay on GitHub Actions.",
        "",
        "## Counts",
        "",
    ]
    lines += [f"- {k}: {v}" for k, v in c.items()]
    lines += ["", "## Step status", ""]
    for r in results:
        lines.append(f"- {r['name']}: {r['status']} ({r['returncode']})")
        if r.get("status") not in {"ok"} and r.get("stderr"):
            lines.append(f"  - stderr: {clean(r.get('stderr'))[:700]}")
    lines += ["", "## Director bridge actions", ""]
    lines += [f"- {a}" for a in bridge_actions] if bridge_actions else ["- No director aliases were created."]
    director = read_text("mermaid_content_director_report.md")
    if director:
        lines += ["", "---", "", "## Content Director v2.3 Report", ""]
        lines += director.splitlines()
    lines += ["", "## Next operator focus", ""]
    if c["player_asset_debt"]:
        lines.append("- Fill player asset debt before relying on player-led preview graphics.")
    if c["director_wrong_sport_rejections"]:
        lines.append("- Review wrong-sport rejections, especially NCAA Softball filters.")
    if c["director_slots"]:
        lines.append("- Use Content Director queues and compiled packets for handoff.")
    if c["rumor_claims"]:
        lines.append("- Review rumor desk claims. Confirmed/corroborated only should move to publish lanes.")
    lines.append("- Keep publish mode artifact-only until rendered QA passes.")
    write_text(OUT_MD, "\n".join(lines) + "\n")
    print(json.dumps(c, indent=2))


if __name__ == "__main__":
    main()
