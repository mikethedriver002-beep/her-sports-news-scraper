from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "hsd-install-verifier-v3.1"
REQUIRED_FILES = [
    ".github/workflows/hsd-pipeline-control-v1.yml",
    "build_hsd_run_manifest_v1.py",
    "generate_hsd_results_contract_v1.py",
    "normalize_hsd_manual_story_inbox_v1.py",
    "ingest_hsd_discovery_sources_v1.py",
    "build_hsd_daily_slate_v1.py",
    "publish_hsd_guard_v1.py",
    "generate_hsd_operator_status_v1.py",
    "generate_hsd_pipeline_review_lite_v1.py",
    "generate_hsd_graphics_upload_pack_v1.py",
    "validate_hsd_contracts_v1.py",
    "config/pipeline_version.json",
    "config/daily_slate.json",
    "config/source_registry.json",
]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
        return h.hexdigest()
    except Exception:
        return ""

def main() -> None:
    issues = []
    hashes = {}
    for name in REQUIRED_FILES:
        p = Path(name)
        if not p.exists():
            issues.append(f"missing required file: {name}")
        else:
            hashes[name] = sha(p)
    pv = Path("config/pipeline_version.json")
    if pv.exists():
        try:
            version = json.loads(pv.read_text()).get("pipeline_version")
            if version != "v3.1":
                issues.append(f"pipeline_version mismatch: {version}")
        except Exception:
            issues.append("config/pipeline_version.json unreadable")
    wf = Path(".github/workflows/hsd-pipeline-control-v1.yml")
    if wf.exists():
        txt = wf.read_text()
        if "workflow_run" in txt or "\npush:" in txt or "\nschedule:" in txt:
            issues.append("controller workflow has unsafe auto trigger")
    report = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "issues": issues, "hashes": hashes}
    Path("install_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path("install_report.md").write_text("# HSD Install Verification\n\n" + f"- issues: {len(issues)}\n\n" + "\n".join(f"- {x}" for x in issues) + ("\n" if issues else "Install verification passed.\n"), encoding="utf-8")
    print(json.dumps({"issues": len(issues)}, indent=2))
    if issues:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
