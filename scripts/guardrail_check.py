from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "hsd_guardrails.json"


@dataclass
class Violation:
    code: str
    message: str
    path: str | None = None
    line: int | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path is not None:
            payload["path"] = self.path
        if self.line is not None:
            payload["line"] = self.line
        return payload


def load_guardrails(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing guardrail config: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def git_diff_text(base: str, head: str) -> str:
    committed = run_git(["diff", f"{base}...{head}"])
    unstaged = run_git(["diff"])
    staged = run_git(["diff", "--cached"])
    return "\n".join(part for part in (committed, unstaged, staged) if part)


def git_changed_paths(base: str, head: str) -> list[str]:
    outputs = [
        run_git(["diff", "--name-only", f"{base}...{head}"]),
        run_git(["diff", "--name-only"]),
        run_git(["diff", "--cached", "--name-only"]),
    ]
    paths = {
        line.strip().replace("\\", "/")
        for output in outputs
        for line in output.splitlines()
        if line.strip()
    }
    return sorted(paths)


def git_untracked_paths() -> list[str]:
    output = run_git(["ls-files", "--others", "--exclude-standard"])
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def display_path(path: Path) -> str:
    try:
        return normalize_path(path.relative_to(ROOT))
    except ValueError:
        return normalize_path(path)


def has_fragment(path: str, fragments: list[str]) -> bool:
    path_lower = path.lower()
    return any(fragment.lower().replace("\\", "/") in path_lower for fragment in fragments)


def has_path_exception(path: str, exceptions: list[str]) -> bool:
    normalized = normalize_path(path).lower().lstrip("./")
    padded = f"/{normalized}"
    for exception in exceptions:
        cleaned = str(exception).lower().replace("\\", "/").lstrip("./").lstrip("/")
        if not cleaned:
            continue
        if normalized.startswith(cleaned) or f"/{cleaned}" in padded:
            return True
    return False


def is_truthy(value: Any, truthy_values: set[str]) -> bool:
    return str(value).strip().lower() in truthy_values


def allowed_human_download_approval_intake_row(path: Path, field: str, row: dict[str, str], config: dict[str, Any]) -> bool:
    if field != "download_approved":
        return False
    display = display_path(path).lower()
    allowed_paths = [str(path).lower().replace("\\", "/").lstrip("./") for path in config.get("human_download_approval_intake_csv_exceptions", [])]
    if not any(display == allowed or display.endswith(f"/{allowed}") for allowed in allowed_paths):
        return False
    required_fields = [
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
        "quarantine_target_hint",
    ]
    if any(not str(row.get(required, "")).strip() for required in required_fields):
        return False
    quarantine_hint = normalize_path(str(row.get("quarantine_target_hint", "")).strip()).lower()
    if not quarantine_hint.startswith("data/assets/quarantine/review_only_candidates/"):
        return False
    if str(row.get("review_only", "")).strip().lower() != "true":
        return False
    if str(row.get("publish_ready", "")).strip().lower() != "false":
        return False
    return True


def truthy_text_pattern(field: str, truthy_values: set[str]) -> re.Pattern[str]:
    values = "|".join(re.escape(value) for value in sorted(truthy_values, key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9_]){re.escape(field.lower())}\b\s*(?:=|:|\||\s)\s*(?:{values})(?![a-z0-9_])")


def safe_text_exception(field: str, raw_line: str, path: str | None, config: dict[str, Any]) -> bool:
    if path:
        normalized_path = normalize_path(path).lower()
        for exception_path in config.get("diff_truthy_path_exceptions", []):
            if normalized_path.startswith(str(exception_path).lower().replace("\\", "/")):
                return True
    exceptions = config.get("diff_truthy_exceptions", {}).get(field, [])
    haystack = f"{path or ''}\n{raw_line}".lower()
    return any(str(exception).lower() in haystack for exception in exceptions)


def safe_artifact_text_line(raw_line: str, config: dict[str, Any]) -> bool:
    normalized = " ".join(raw_line.lower().split())
    cleaned = normalized.replace("`", "").replace('"', "").replace("'", "")
    for phrase in config.get("text_guardrail_safe_phrases", []):
        if str(phrase).lower() in normalized or str(phrase).lower() in cleaned:
            return True
    return False


def false_guardrail_text(field: str, raw_line: str) -> bool:
    cleaned = raw_line.lower().replace("`", "").replace('"', "").replace("'", "")
    return bool(re.search(rf"(?<![a-z0-9_]){re.escape(field)}\b\s*(?:=|:|\||\s)\s*(?:false|no|0)(?![a-z0-9_])", cleaned))


def protected_asset_write_intent(raw_line: str) -> bool:
    line = raw_line.lower()
    intent_words = [
        "write_target",
        "write",
        "writes",
        "writeback",
        "create",
        "created",
        "copy",
        "move",
        "save",
        "download",
        "destination",
        "output",
        "land in",
        "place in",
    ]
    safe_hold_words = ["hold", "disabled", "missing", "review-only", "review only", "fallback"]
    return any(word in line for word in intent_words) and not any(word in line for word in safe_hold_words)


def blocked_path_text_intent(raw_line: str, config: dict[str, Any]) -> bool:
    line = raw_line.lower()
    if false_guardrail_text("publish_ready", raw_line):
        return False
    if re.search(r"\b(?:no|not|without|disabled|manual-review-only|manual review only)\b.{0,80}(?:publish-ready|publish_ready)", line):
        return False
    if re.search(r"(?:publish-ready|publish_ready).{0,80}\b(?:false|disabled|blocked)\b", line):
        return False
    for fragment in config.get("blocked_path_fragments", []):
        cleaned = str(fragment).lower().replace("\\", "/")
        if cleaned in {"publish_ready", "publish-ready"}:
            if re.search(r"(?:^|[\\/\s])publish[-_]ready(?:[\\/]|$)", line):
                return True
            continue
        if cleaned in line:
            return True
    return False


def marker_text_present(raw_line: str, marker_suffixes: list[str]) -> bool:
    line = raw_line.lower()
    for suffix in marker_suffixes:
        escaped = re.escape(str(suffix).lower())
        if re.search(rf"{escaped}(?![a-z0-9_])", line):
            return True
    return False


def safe_marker_prohibition_text(raw_line: str) -> bool:
    cleaned = raw_line.lower().replace("`", "").replace('"', "").replace("'", "")
    if ".approved" not in cleaned:
        return False
    return bool(re.search(r"\b(?:no|not|without|do not|does not)\b.{0,120}\.approved", cleaned))


def added_diff_lines(diff_text: str) -> list[tuple[str | None, int | None, str]]:
    current_path: str | None = None
    new_line: int | None = None
    rows: list[tuple[str | None, int | None, str]] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:].strip()
            continue
        if line.startswith("@@"):
            marker = line.split("+", 1)[1].split(" ", 1)[0]
            start = marker.split(",", 1)[0]
            try:
                new_line = int(start)
            except ValueError:
                new_line = None
            continue
        if line.startswith("+") and not line.startswith("+++"):
            rows.append((current_path, new_line, line[1:]))
            if new_line is not None:
                new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        elif new_line is not None:
            new_line += 1
    return rows


def scan_changed_paths(paths: list[str], config: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []
    blocked_fragments = config.get("blocked_path_fragments", [])
    marker_suffixes = config.get("blocked_marker_suffixes", [])
    protected_fragments = config.get("protected_asset_write_fragments", [])
    protected_exceptions = config.get("protected_asset_write_exceptions", [])
    changed_path_exceptions = config.get("changed_path_exceptions", [])
    for path in paths:
        normalized = normalize_path(path)
        if has_path_exception(normalized, changed_path_exceptions):
            continue
        if has_fragment(normalized, blocked_fragments):
            violations.append(Violation("blocked_path", "Changed path is inside a blocked publish/publish-ready boundary.", normalized))
        if any(normalized.lower().endswith(suffix.lower()) for suffix in marker_suffixes):
            violations.append(Violation("blocked_marker", "Changed path writes a blocked approval marker.", normalized))
        if has_fragment(normalized, protected_fragments) and not has_path_exception(normalized, protected_exceptions):
            violations.append(Violation("protected_asset_write", "Changed path touches a protected asset write boundary.", normalized))
    return violations


def scan_diff_content(diff_text: str, config: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []
    truthy_values = {str(v).lower() for v in config.get("truthy_values", [])}
    fields = config.get("truthy_guardrail_fields", [])
    for path, line_number, raw_line in added_diff_lines(diff_text):
        compact = raw_line.strip().replace(" ", "").replace('"', "'").lower()
        for field in fields:
            candidates = (
                f"{field}=true",
                f"{field}='true'",
                f"{field}:true",
                f"{field}:'true'",
                f"{field}=yes",
                f"{field}='yes'",
                f"{field}:yes",
                f"{field}:'yes'",
            )
            if any(candidate in compact for candidate in candidates):
                if safe_text_exception(field, raw_line, path, config):
                    continue
                violations.append(
                    Violation(
                        "truthy_guardrail_diff",
                        f"Added line appears to set guardrail field `{field}` truthy.",
                        path,
                        line_number,
                    )
                )
    return violations


def scan_structured_file(path: Path, config: dict[str, Any]) -> list[Violation]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return scan_csv_file(path, config)
    if suffix in {".json", ".jsonl"}:
        return scan_json_file(path, config)
    return []


def scan_text_file(path: Path, config: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []
    display = display_path(path)
    text_path_exceptions = [*config.get("changed_path_exceptions", []), *config.get("text_scan_path_exceptions", [])]
    if has_path_exception(display, text_path_exceptions):
        return violations

    truthy_values = {str(v).lower() for v in config.get("truthy_values", [])}
    fields = config.get("truthy_guardrail_fields", [])
    truthy_patterns = {field: truthy_text_pattern(field, truthy_values) for field in fields}
    marker_suffixes = config.get("blocked_marker_suffixes", [])
    protected_fragments = config.get("protected_asset_write_fragments", [])
    protected_exceptions = config.get("protected_asset_write_exceptions", [])

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw_line.lower()
        if safe_artifact_text_line(raw_line, config):
            continue
        for field, pattern in truthy_patterns.items():
            if pattern.search(line) and not safe_text_exception(field, raw_line, display, config):
                violations.append(
                    Violation(
                        "truthy_guardrail_text",
                        f"Generated text artifact appears to set guardrail field `{field}` truthy.",
                        display,
                        line_number,
                    )
                )
        pathlike_line = "/" in line or "\\" in line or "path" in line or marker_text_present(raw_line, marker_suffixes)
        if not pathlike_line:
            continue
        if blocked_path_text_intent(raw_line, config):
            violations.append(
                Violation(
                    "blocked_path_text",
                    "Generated text artifact references a blocked publish/publish-ready path.",
                    display,
                    line_number,
                )
            )
        if marker_text_present(raw_line, marker_suffixes) and not safe_marker_prohibition_text(raw_line):
            violations.append(
                Violation(
                    "blocked_marker_text",
                    "Generated text artifact references a blocked approval marker.",
                    display,
                    line_number,
                )
            )
        if has_fragment(line, protected_fragments) and protected_asset_write_intent(raw_line) and not has_path_exception(line, protected_exceptions):
            violations.append(
                Violation(
                    "protected_asset_text",
                    "Generated text artifact references a protected asset/headshot write boundary.",
                    display,
                    line_number,
                )
            )
    return violations


def scan_csv_file(path: Path, config: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []
    truthy_values = {str(v).lower() for v in config.get("truthy_values", [])}
    fields = set(config.get("truthy_guardrail_fields", []))
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            for field in fields.intersection(row.keys()):
                if is_truthy(row.get(field, ""), truthy_values):
                    if allowed_human_download_approval_intake_row(path, field, row, config):
                        continue
                    violations.append(
                        Violation(
                            "truthy_guardrail_csv",
                            f"CSV field `{field}` is truthy in generated artifact.",
                            normalize_path(path),
                            row_number,
                        )
                    )
    return violations


def scan_json_file(path: Path, config: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []
    truthy_values = {str(v).lower() for v in config.get("truthy_values", [])}
    fields = set(config.get("truthy_guardrail_fields", []))

    def visit(value: Any, trail: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_trail = f"{trail}.{key}" if trail else str(key)
                if key in fields and is_truthy(child, truthy_values):
                    violations.append(
                        Violation(
                            "truthy_guardrail_json",
                            f"JSON field `{child_trail}` is truthy in generated artifact.",
                            normalize_path(path),
                        )
                    )
                visit(child, child_trail)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{trail}[{index}]")

    if path.suffix.lower() == ".jsonl":
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                visit(json.loads(line), "")
            except json.JSONDecodeError:
                violations.append(Violation("invalid_jsonl", "Could not parse JSONL line.", normalize_path(path), line_number))
        return violations

    try:
        visit(json.loads(path.read_text(encoding="utf-8", errors="replace")), "")
    except json.JSONDecodeError as exc:
        violations.append(Violation("invalid_json", f"Could not parse JSON: {exc}", normalize_path(path), exc.lineno))
    return violations


def scan_directory(scan_dir: Path, config: dict[str, Any]) -> list[Violation]:
    if not scan_dir.exists():
        return []
    violations = scan_changed_paths([display_path(p) for p in scan_dir.rglob("*") if p.is_file()], config)
    extensions = set(config.get("scan_file_extensions", []))
    text_extensions = set(config.get("scan_text_extensions", []))
    for path in scan_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            violations.extend(scan_structured_file(path, config))
        if path.is_file() and path.suffix.lower() in text_extensions:
            violations.extend(scan_text_file(path, config))
    return violations


def render_markdown(status: str, violations: list[Violation], summary: dict[str, Any]) -> str:
    lines = [f"## HSD Guardrail Check {status}"]
    lines.append("")
    lines.append(f"- Changed paths checked: `{summary.get('changed_paths_checked', 0)}`")
    lines.append(f"- Scan files checked: `{summary.get('scan_files_checked', 0)}`")
    lines.append(f"- Violations: `{len(violations)}`")
    if violations:
        lines.append("")
        for violation in violations:
            location = f" ({violation.path}" if violation.path else ""
            if location and violation.line is not None:
                location += f":{violation.line}"
            if location:
                location += ")"
            lines.append(f"- [ ] `{violation.code}`{location}: {violation.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="HSD deterministic guardrail checker")
    parser.add_argument("--base", help="Base ref for branch diff scanning, such as origin/main")
    parser.add_argument("--head", default="HEAD", help="Head ref for branch diff scanning")
    parser.add_argument("--scan-dir", help="Directory to scan for generated artifact guardrail state")
    parser.add_argument("--skip-untracked", action="store_true", help="Skip untracked paths in changed-path scans")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Guardrail config path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    config = load_guardrails(Path(args.config))
    violations: list[Violation] = []
    changed_paths: list[str] = []
    scan_files_checked = 0

    if args.base:
        diff_text = git_diff_text(args.base, args.head)
        changed_paths = git_changed_paths(args.base, args.head)
        if not args.skip_untracked:
            changed_paths.extend(git_untracked_paths())
            changed_paths = sorted(set(changed_paths))
        violations.extend(scan_changed_paths(changed_paths, config))
        violations.extend(scan_diff_content(diff_text, config))

    if args.scan_dir:
        scan_dir = (ROOT / args.scan_dir).resolve()
        if scan_dir.exists():
            scan_files_checked = sum(1 for path in scan_dir.rglob("*") if path.is_file())
        violations.extend(scan_directory(scan_dir, config))

    summary = {
        "changed_paths_checked": len(changed_paths),
        "scan_files_checked": scan_files_checked,
        "violation_count": len(violations),
    }
    payload = {
        "status": "FAILED" if violations else "PASSED",
        "summary": summary,
        "violations": [violation.as_dict() for violation in violations],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_markdown(payload["status"], violations, summary))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
