from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v3.5.1-render-studio-v3-integrity-check"
OUT_REPORT = Path("assignment_handoff_publisher_report.md")
OUT_MANIFEST = Path("assignment_handoff_publisher_manifest.json")


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


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


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


def run_script(path: str) -> Dict[str, Any]:
    script = Path(path)
    if not script.exists():
        return {"status": "missing", "returncode": 127}
    proc = subprocess.run([sys.executable, script.as_posix()], text=True, capture_output=True, timeout=320)
    return {"status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-1200:], "stderr": proc.stderr[-1200:]}


def run_cmd(args: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(args, text=True, capture_output=True, timeout=120)
    return {"cmd": " ".join(args), "returncode": proc.returncode, "stdout": proc.stdout[-1200:], "stderr": proc.stderr[-1200:]}


def maybe_commit_latest_outputs() -> Dict[str, Any]:
    if os.environ.get("HSD_COMMIT_HEAVY_OUTPUTS", "false").lower() != "true":
        return {"status": "skipped", "reason": "HSD_COMMIT_HEAVY_OUTPUTS is not true"}
    if not Path("outputs/latest").exists():
        return {"status": "skipped", "reason": "outputs/latest does not exist"}
    steps = []
    steps.append(run_cmd(["git", "config", "user.name", "github-actions"]))
    steps.append(run_cmd(["git", "config", "user.email", "github-actions@github.com"]))
    steps.append(run_cmd(["git", "add", "-A", "outputs/latest"]))
    diff = run_cmd(["git", "diff", "--cached", "--quiet"])
    steps.append(diff)
    if diff["returncode"] == 0:
        return {"status": "no_changes", "steps": steps}
    commit = run_cmd(["git", "commit", "-m", "Update latest HSD render review outputs"])
    steps.append(commit)
    push = run_cmd(["git", "push", "origin", "HEAD:main"])
    steps.append(push)
    return {"status": "pushed" if push["returncode"] == 0 else "push_failed", "steps": steps}


def main() -> None:
    registry_build = run_script("scripts/build_hsd_wnba_asset_registry_v1.py")
    registry_validate = run_script("scripts/validate_hsd_wnba_asset_registry_v1.py")
    registry_gaps = run_script("scripts/report_hsd_wnba_asset_gaps_v1.py")
    handoff_run = run_script("generate_hsd_mermaid_assignment_handoff_v2_6.py")
    actions: List[str] = []
    copy_file("assignment_handoff_report.md", "manual_workflow_handoff.md", actions)
    copy_file("assignment_handoff_index.csv", "manual_workflow_content_packets.csv", actions)
    copy_file("assignment_handoff_status.csv", "manual_workflow_pack_status.csv", actions)
    copy_dir("assignment_handoff_packets", "manual_workflow_packets", actions)
    copy_dir("assignment_handoff_zips", "manual_workflow_handoff_packs", actions)
    render_run = run_script("scripts/generate_hsd_mermaid_render_studio_v3_0.py")
    if Path("rendered_handoff_zips").exists():
        target = Path("manual_workflow_handoff_packs")
        target.mkdir(exist_ok=True)
        for zp in Path("rendered_handoff_zips").glob("*.zip"):
            shutil.copy2(zp, target / ("rendered_" + zp.name))
            actions.append(f"{zp.as_posix()} -> {(target / ('rendered_' + zp.name)).as_posix()}")
    publish_run = run_script("scripts/generate_hsd_mermaid_render_publish_bridge_v2_8.py")
    integrity_run = run_script("scripts/check_hsd_render_integrity_v1.py")
    render_meta = read_json("rendered_handoff_metadata.json")
    latest_summary = read_json("outputs/latest/summary.json")
    commit_run = maybe_commit_latest_outputs()
    counts = {
        "handoff_packets": len(read_csv("assignment_handoff_index.csv")),
        "manual_packets": len(read_csv("manual_workflow_content_packets.csv")),
        "handoff_status_rows": len(read_csv("assignment_handoff_status.csv")),
        "manual_status_rows": len(read_csv("manual_workflow_pack_status.csv")),
        "manual_zip_count": len(list(Path("manual_workflow_handoff_packs").glob("*.zip"))) if Path("manual_workflow_handoff_packs").exists() else 0,
        "rendered_rows": len(read_csv("rendered_handoff_manifest.csv")),
        "render_blocked_rows": len([r for r in read_csv("rendered_handoff_status.csv") if r.get("status") == "blocked"]),
        "render_zip_count": len(list(Path("rendered_handoff_zips").glob("*.zip"))) if Path("rendered_handoff_zips").exists() else 0,
        "latest_outputs_files": len(list(Path("outputs/latest").rglob("*"))) if Path("outputs/latest").exists() else 0,
        "verified_team_logos": len([r for r in read_csv("data/asset_registry/wnba/team_logos.csv") if r.get("file_exists") == "true"]),
        "missing_team_logos": len(read_csv("data/asset_registry/wnba/missing_team_logos.csv")),
        "render_integrity": render_meta.get("integrity_status", "unknown"),
        "publish_integrity": latest_summary.get("integrity_status", "unknown"),
    }
    manifest = {"version": VERSION, "generated_at": now_iso(), "registry_build": registry_build, "registry_validate": registry_validate, "registry_gaps": registry_gaps, "handoff_run": handoff_run, "render_run": render_run, "render_meta": render_meta, "publish_run": publish_run, "integrity_run": integrity_run, "latest_summary": latest_summary, "commit_run": commit_run, "actions": actions, "counts": counts}
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = ["# Mermaid Handoff Publisher v3.0 Registry Resolver", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Counts", ""]
    lines += [f"- {k}: {v}" for k, v in counts.items()]
    lines += ["", "## Commit latest outputs", "", f"- status: {commit_run.get('status')}"]
    if commit_run.get("reason"):
        lines.append(f"- reason: {commit_run.get('reason')}")
    lines += ["", "## Actions", ""]
    lines += [f"- {a}" for a in actions] if actions else ["- No actions completed."]
    for extra in ["data/asset_registry/wnba/asset_registry_report.md", "data/asset_registry/wnba/asset_registry_validation_report.md", "data/asset_registry/wnba/asset_gap_report.md", "rendered_handoff_qa_report.md", "render_integrity_report.md", "outputs/latest/README.md"]:
        p = Path(extra)
        if p.exists():
            lines += ["", "---", "", p.read_text(encoding="utf-8", errors="replace")]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"counts": counts, "actions": len(actions), "commit_status": commit_run.get("status")}, indent=2))


if __name__ == "__main__":
    main()
