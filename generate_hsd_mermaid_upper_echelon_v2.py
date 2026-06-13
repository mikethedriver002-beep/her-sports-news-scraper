from __future__ import annotations

import csv
import json
import re
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


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


VERSION = "v3.3.1-mermaid-upper-echelon-quality-brain-bridge"
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
]


def run_step(name: str, script: str) -> Dict[str, Any]:
    p = Path(script)
    if not p.exists():
        return {"name": name, "script": script, "status": "missing", "returncode": 127}
    try:
        proc = subprocess.run([sys.executable, script], text=True, capture_output=True, timeout=180)
        return {
            "name": name,
            "script": script,
            "status": "ok" if proc.returncode == 0 else "error",
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
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
    """Make Quality Brain outputs visible through the existing artifact list.

    The workflow already uploads the classic Upper Echelon paths. This bridge lets us
    upgrade output quality without requiring the operator to patch PowerShell or YAML.
    """
    actions: List[str] = []
    aliases = [
        ("mermaid_master_content_board_v2_1.md", "mermaid_master_content_board.md"),
        ("mermaid_quality_story_graph.csv", "mermaid_story_graph.csv"),
        ("mermaid_quality_content_slots.csv", "mermaid_content_slots_v2.csv"),
        ("ig_feed_queue_v2_1.csv", "ig_feed_queue_v2.csv"),
        ("ig_story_queue_v2_1.csv", "ig_story_queue_v2.csv"),
        ("threads_queue_v2_1.csv", "threads_queue_v2.csv"),
        ("breaking_news_queue_v2_1.csv", "breaking_news_queue.csv"),
        ("rumor_watch_queue_v2_1.csv", "rumor_watch_queue.csv"),
        ("player_asset_debt_v2_1.csv", "player_asset_debt.csv"),
        ("mermaid_quality_prompt_index.csv", "mermaid_compiled_packet_index.csv"),
    ]
    for src, dst in aliases:
        if copy_if_exists(src, dst):
            actions.append(f"aliased {src} -> {dst}")

    if Path("mermaid_quality_compiled_packets").exists():
        copy_if_exists("mermaid_quality_compiled_packets", "mermaid_compiled_packets")
        actions.append("aliased mermaid_quality_compiled_packets -> mermaid_compiled_packets")

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
        "quality_slots": len(read_csv("mermaid_quality_content_slots.csv")),
        "quality_packets": len(read_csv("mermaid_quality_prompt_index.csv")),
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
        "quality_brain_present": Path("mermaid_quality_brain_report.md").exists(),
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
        "Upper Echelon ran with the Quality Brain bridge. The quality outputs are aliased into the existing artifact paths so the operator does not need local PowerShell/Git/Python wiring.",
        "",
        "## Counts",
        "",
    ]
    lines += [f"- {k}: {v}" for k, v in c.items()]
    lines += ["", "## Step status", ""]
    for r in results:
        lines.append(f"- {r['name']}: {r['status']} ({r['returncode']})")
        if r.get("status") not in {"ok"} and r.get("stderr"):
            lines.append(f"  - stderr: {clean(r.get('stderr'))[:500]}")

    lines += ["", "## Quality bridge actions", ""]
    if bridge_actions:
        lines += [f"- {a}" for a in bridge_actions]
    else:
        lines.append("- No quality aliases were created. Check whether Quality Brain generated outputs.")

    qb_report = read_text("mermaid_quality_brain_report.md")
    if qb_report:
        lines += ["", "---", "", "## Quality Brain v2.1 Report", ""]
        lines += qb_report.splitlines()

    lines += ["", "## Next operator focus", ""]
    if c["player_asset_debt"]:
        lines.append("- Fill player asset debt before relying on player-led preview graphics.")
    if c["multisport_candidates_filtered"]:
        lines.append("- Review the quality-filtered multi-sport scout candidates, not the raw scout dump.")
    if c["quality_slots"]:
        lines.append("- Use the quality-routed v2 queues and compiled packets for handoff.")
    if c["rumor_claims"]:
        lines.append("- Review rumor desk claims. Confirmed/corroborated only should move to publish lanes.")
    lines.append("- Keep publish mode artifact-only until rendered QA passes.")

    write_text(OUT_MD, "\n".join(lines) + "\n")
    print(json.dumps(c, indent=2))


if __name__ == "__main__":
    main()
