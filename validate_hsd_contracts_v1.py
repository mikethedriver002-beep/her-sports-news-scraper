from __future__ import annotations
import csv, json, sys
from pathlib import Path
from typing import Dict, List

VERSION = "hsd-contract-validator-v3.0"

REQUIRED = {
    "results_contract_v2.csv": ["run_id","event_id","row_kind","event_date_local","content_eligibility"],
    "story_candidates_manual.csv": ["story_id","source_url","story_kind","verification_status","status","idempotency_key"],
    "story_candidates_discovery.csv": ["story_id","source_url","source_type","risk_tier","publish_eligible"],
}

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def validate_file(path: str, required: List[str]) -> List[str]:
    p = Path(path)
    issues = []
    if not p.exists():
        issues.append(f"{path}: missing")
        return issues
    rows = read_csv(path)
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
    for col in required:
        if col not in fields:
            issues.append(f"{path}: missing column {col}")
    for i, row in enumerate(rows[:1000], start=2):
        for col in required:
            if col in fields and not str(row.get(col,"")).strip():
                issues.append(f"{path}: row {i} missing {col}")
                break
    return issues

def main() -> None:
    issues = []
    for path, required in REQUIRED.items():
        issues.extend(validate_file(path, required))
    report = ["# HSD Contract Validation Report", "", f"Version: {VERSION}", "", f"- issues: {len(issues)}", ""]
    if issues:
        report += ["## Issues", ""] + [f"- {x}" for x in issues]
    else:
        report += ["All checked contracts passed."]
    Path("contract_validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    Path("contract_validation_manifest.json").write_text(json.dumps({"version": VERSION, "issues": len(issues), "issue_list": issues}, indent=2), encoding="utf-8")
    print(json.dumps({"issues": len(issues)}, indent=2))
    if issues and "--soft" not in sys.argv:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
