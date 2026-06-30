from __future__ import annotations

import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence


DEFAULT_VOLATILE_JSON_KEYS = frozenset(
    {
        "compiled_at",
        "compiled_at_local",
        "compiled_at_utc",
        "generated_at",
        "generated_at_local",
        "generated_at_utc",
        "reviewed_at",
        "reviewed_at_local",
        "reviewed_at_utc",
    }
)
DEFAULT_VOLATILE_JSON_SUFFIXES = (
    "_compiled_at",
    "_compiled_at_local",
    "_compiled_at_utc",
    "_generated_at",
    "_generated_at_local",
    "_generated_at_utc",
    "_reviewed_at",
    "_reviewed_at_local",
    "_reviewed_at_utc",
)
DEFAULT_VOLATILE_MARKDOWN_PREFIXES = (
    "Generated:",
    "Draft-copy generated at UTC:",
)


def run_output_dir() -> Path | None:
    raw = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if not raw:
        return None
    return Path(raw).resolve()


def output_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    root = run_output_dir()
    return root / p if root else p


def input_candidates(path: str | Path) -> List[Path]:
    p = Path(path)
    if p.is_absolute():
        return [p]
    root = run_output_dir()
    candidates: List[Path] = []
    if root:
        candidates.append(root / p)
    candidates.append(p)
    return candidates


def input_path(path: str | Path) -> Path:
    candidates = input_candidates(path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def exists(path: str | Path) -> bool:
    return input_path(path).exists()


def is_file(path: str | Path) -> bool:
    return input_path(path).is_file()


def is_dir(path: str | Path) -> bool:
    return input_path(path).is_dir()


def _read_existing_text(path: Path, encoding: str) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding=encoding)
    except Exception:
        return None


def _write_text_if_changed(path: Path, text: str, *, encoding: str, normalize: Callable[[str], str] | None = None) -> None:
    existing = _read_existing_text(path, encoding)
    if existing is not None:
        left = normalize(existing) if normalize else existing
        right = normalize(text) if normalize else text
        if left == right:
            return
    path.write_text(text, encoding=encoding)


def _is_volatile_json_key(key: str, volatile_keys: set[str]) -> bool:
    return key in volatile_keys or key.endswith(DEFAULT_VOLATILE_JSON_SUFFIXES)


def _normalize_json_payload(payload: Any, volatile_keys: set[str]) -> Any:
    if isinstance(payload, dict):
        normalized: Dict[str, Any] = {}
        for key, value in payload.items():
            if _is_volatile_json_key(str(key), volatile_keys):
                continue
            normalized[str(key)] = _normalize_json_payload(value, volatile_keys)
        return normalized
    if isinstance(payload, list):
        return [_normalize_json_payload(value, volatile_keys) for value in payload]
    return payload


def _existing_json_matches(path: Path, payload: Any, volatile_keys: set[str]) -> bool:
    if not path.exists():
        return False
    try:
        existing = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return False
    return _normalize_json_payload(existing, volatile_keys) == _normalize_json_payload(payload, volatile_keys)


def _normalize_csv_rows(rows: Iterable[Dict[str, Any]], volatile_fields: set[str]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for row in rows:
        normalized.append({str(key): str(value) for key, value in row.items() if key not in volatile_fields})
    return normalized


def _existing_csv_matches(path: Path, rendered_csv: str, volatile_fields: set[str]) -> bool:
    existing = _read_existing_text(path, "utf-8")
    if existing is None:
        return False
    if not volatile_fields:
        return existing == rendered_csv
    try:
        current_reader = csv.DictReader(io.StringIO(existing))
        new_reader = csv.DictReader(io.StringIO(rendered_csv))
        if list(current_reader.fieldnames or []) != list(new_reader.fieldnames or []):
            return False
        current_rows = _normalize_csv_rows(list(current_reader), volatile_fields)
        new_rows = _normalize_csv_rows(list(new_reader), volatile_fields)
        return current_rows == new_rows
    except Exception:
        return False


def strip_volatile_markdown_lines(text: str, prefixes: Sequence[str] = DEFAULT_VOLATILE_MARKDOWN_PREFIXES) -> str:
    if not prefixes:
        return text
    normalized_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in prefixes):
            continue
        normalized_lines.append(line)
    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip() + "\n"


def write_text(
    path: str | Path,
    text: str,
    encoding: str = "utf-8",
    *,
    if_changed: bool = True,
    normalize: Callable[[str], str] | None = None,
) -> Path:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if if_changed:
        _write_text_if_changed(out, text, encoding=encoding, normalize=normalize)
    else:
        out.write_text(text, encoding=encoding)
    return out


def write_json(
    path: str | Path,
    payload: Any,
    *,
    volatile_keys: Iterable[str] | None = DEFAULT_VOLATILE_JSON_KEYS,
    if_changed: bool = True,
    **kwargs: Any,
) -> Path:
    if "indent" not in kwargs:
        kwargs["indent"] = 2
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if if_changed and _existing_json_matches(out, payload, set(volatile_keys or ())):
        return out
    out.write_text(json.dumps(payload, **kwargs), encoding="utf-8")
    return out


def read_text(path: str | Path, default: str = "", encoding: str = "utf-8") -> str:
    p = input_path(path)
    if not p.exists():
        return default
    return p.read_text(encoding=encoding, errors="replace")


def read_json(path: str | Path, default: Any) -> Any:
    p = input_path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return default


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = input_path(path)
    if not p.exists() or not p.is_file():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def write_csv(
    path: str | Path,
    rows: Iterable[Dict[str, Any]],
    fieldnames: Sequence[str],
    *,
    extrasaction: str = "ignore",
    volatile_fields: Sequence[str] | None = None,
    if_changed: bool = True,
) -> Path:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    materialized_rows = list(rows)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction=extrasaction)
    writer.writeheader()
    writer.writerows(materialized_rows)
    rendered_csv = buffer.getvalue()
    if if_changed and _existing_csv_matches(out, rendered_csv, set(volatile_fields or ())):
        return out
    with out.open("w", newline="", encoding="utf-8") as handle:
        handle.write(rendered_csv)
    return out
