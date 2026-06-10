
from __future__ import annotations
import csv, json, sys
from pathlib import Path
from typing import Dict, List

VERSION = "hsd-contract-validator-v3.1-soft-block-aware"
BASE_REQUIRED = {
    "results_contract_v2.csv": ["run_id","event_id","row_kind","content_eligibility","dedupe_key"],
    "story_candidates_manual.csv": ["story_id","source_url","story_kind","verification_status","status","idempotency_key"],
    "story_candidates_discovery.csv": ["story_id","source_url","source_type","risk_tier","publish_eligible"],
}
NON_BLOCKED_REQUIRED = {"results_contract_v2.csv": ["event_date_local"]}

def read_csv(path: str) -> tuple[List[str], List[Dict[str, str]]]:
    p = Path(path)
    if not p.exists():
        return [], []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)

def validate_file(path: str, required: List[str]) -> List[str]:
    fields, rows = read_csv(path)
    issues = []
    if not fields and not Path(path).exists():
        issues.append(f"{path}: missing")
        return issues
    for col in required:
        if col not in fields:
            issues.append(f"{path}: missing column {col}")
    for i, row in enumerate(rows[:1000], start=2):
        eligibility = str(row.get("content_eligibility","")).strip().lower()
        for col in required:
            if col in fields and not str(row.get(col,"")).strip():
                issues.append(f"{path}: row {i} missing {col}")
                break
        if path in NON_BLOCKED_REQUIRED and eligibility not in {"blocked", "review"}:
            for col in NON_BLOCKED_REQUIRED[path]:
                if col in fields and not str(row.get(col,"")).strip():
                    issues.append(f"{path}: row {i} eligible row missing {col}")
                    break
    return issues

def main() -> None:
    issues = []
    for path, required in BASE_REQUIRED.items():
        issues.extend(validate_file(path, required))
    report = ["# HSD Contract Validation Report", "", f"Version: {VERSION}", "", f"- issues: {len(issues)}", ""]
    report += (["## Issues", ""] + [f"- {x}" for x in issues]) if issues else ["All checked contracts passed."]
    Path("contract_validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    Path("contract_validation_manifest.json").write_text(json.dumps({"version": VERSION, "issues": len(issues), "issue_list": issues}, indent=2), encoding="utf-8")
    print(json.dumps({"issues": len(issues)}, indent=2))
    if issues and "--hard" in sys.argv:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
