from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


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


def write_text(path: str | Path, text: str, encoding: str = "utf-8") -> Path:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding=encoding)
    return out


def write_json(path: str | Path, payload: Any, **kwargs: Any) -> Path:
    if "indent" not in kwargs:
        kwargs["indent"] = 2
    return write_text(path, json.dumps(payload, **kwargs), encoding="utf-8")


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
) -> Path:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction=extrasaction)
        writer.writeheader()
        writer.writerows(rows)
    return out
