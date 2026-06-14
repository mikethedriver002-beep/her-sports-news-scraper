from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v3.3.6.1-mermaid-handoff-publisher"
OUT_REPORT = Path("assignment_handoff_publisher_report.md")
OUT_MANIFEST = Path("assignment_handoff_publisher_manifest.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return str(v or "").strip()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def copy_file(src: str, dst: str, actions: List[str]) -> None:
    s = Path(src)
    if not s.exists() or not s.is_file():
        return
    shutil.copy2(s, dst)
    actions.append(f"{src} -> {dst}")


def copy_dir(src: str, dst: str, actions: List[str]) -> None:
    s = Path(src)
    d = Path(dst)
    if not s.exists() or not s.is_dir():
        return
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(s, d)
    actions.append(f"{src} -> {dst}")


def run_handoff() -> Dict[str, Any]:
    script = Path("generate_hsd_mermaid_assignment_handoff_v2_6.py")
    if not script.exists():
        return {"status": "missing", "returncode": 127}
    proc = subprocess.run([sys.executable, script.as_posix()], text=True, capture_output=True, timeout=240)
    return {"status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-1200:], "stderr": proc.stderr[-1200:]}


def main() -> None:
    result = run_handoff()
    actions: List[str] = []
    copy_file("assignment_handoff_report.md", "manual_workflow_handoff.md", actions)
    copy_file("assignment_handoff_index.csv", "manual_workflow_content_packets.csv", actions)
    copy_file("assignment_handoff_status.csv", "manual_workflow_pack_status.csv", actions)
    copy_dir("assignment_handoff_packets", "manual_workflow_packets", actions)
    copy_dir("assignment_handoff_zips", "manual_workflow_handoff_packs", actions)
    counts = {
        "handoff_packets": len(read_csv("assignment_handoff_index.csv")),
        "manual_packets": len(read_csv("manual_workflow_content_packets.csv")),
        "handoff_status_rows": len(read_csv("assignment_handoff_status.csv")),
        "manual_status_rows": len(read_csv("manual_workflow_pack_status.csv")),
        "manual_zip_count": len(list(Path("manual_workflow_handoff_packs").glob("*.zip"))) if Path("manual_workflow_handoff_packs").exists() else 0,
    }
    manifest = {"version": VERSION, "generated_at": now_iso(), "handoff_run": result, "actions": actions, "counts": counts}
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = ["# Mermaid Handoff Publisher v2.6.1", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Counts", ""]
    lines += [f"- {k}: {v}" for k, v in counts.items()]
    lines += ["", "## Actions", ""]
    lines += [f"- {a}" for a in actions] if actions else ["- No actions completed."]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"counts": counts, "actions": len(actions)}, indent=2))


if __name__ == "__main__":
    main()
