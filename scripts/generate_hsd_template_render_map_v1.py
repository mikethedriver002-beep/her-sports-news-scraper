from __future__ import annotations

import csv
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v1.2-hsd-template-render-map-safe-renderer-v2-handoff"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping")
OUT_CSV = OUT_DIR / "hsd_template_render_map.csv"
OUT_JSON = OUT_DIR / "hsd_template_render_map.json"
OUT_MD = OUT_DIR / "hsd_template_render_map.md"
CONFIG = Path("config/graphics/template_render_mapping_v1.json")
REGISTRY = Path("config/graphics/template_registry_v1.json")
CONTRACT = Path("results_contract_v2.csv")
FINALS = Path("today_final_results.csv")
RENDERER_V2_SCRIPT = Path("scripts/generate_hsd_template_renderer_v2.py")
FIELDS = ["item_id", "source", "source_id", "row_kind", "sport", "league", "platform", "template_id", "template_family", "template_variant", "mode", "headline", "status", "review_only", "reason", "spec_path"]


def clean(v: Any) -> str:
    return str(v or "").strip()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in FIELDS})


def registry_index(registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row.get("template_id", ""): row for row in registry.get("families", []) if row.get("template_id")}


def template_row(template_id: str, index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return index.get(template_id, {})


def add_event_rows(rows: List[Dict[str, Any]], config: Dict[str, Any], index: Dict[str, Dict[str, Any]]) -> None:
    contract_rows = read_csv(CONTRACT)
    for src in contract_rows:
        if clean(src.get("content_eligibility")).lower() not in {"eligible", ""}:
            continue
        row_kind = clean(src.get("row_kind")).lower()
        sport = clean(src.get("sport")).lower()
        league = clean(src.get("league")).upper()
        for mapping in config.get("event_mappings", []):
            if row_kind != clean(mapping.get("row_kind")).lower():
                continue
            if clean(mapping.get("sport")).lower() and sport != clean(mapping.get("sport")).lower():
                continue
            if clean(mapping.get("league")).upper() and league != clean(mapping.get("league")).upper():
                continue
            template_id = mapping.get("template_id", "")
            t = template_row(template_id, index)
            for platform in mapping.get("platforms", []):
                if platform == "stories" and "1080x1920" not in t.get("supported_formats", []):
                    status = "blocked"
                    reason = "template does not support story canvas"
                else:
                    status = "mapped"
                    reason = "review-only event mapping"
                rows.append({
                    "item_id": f"{src.get('event_id') or src.get('dedupe_key')}::{platform}::{template_id}",
                    "source": CONTRACT.as_posix(),
                    "source_id": src.get("event_id") or src.get("dedupe_key"),
                    "row_kind": row_kind,
                    "sport": src.get("sport"),
                    "league": src.get("league"),
                    "platform": platform,
                    "template_id": template_id,
                    "template_family": t.get("family", ""),
                    "template_variant": t.get("variant", ""),
                    "mode": mapping.get("mode", ""),
                    "headline": src.get("headline") or src.get("summary") or src.get("dedupe_key"),
                    "status": status,
                    "review_only": "true",
                    "reason": reason,
                    "spec_path": t.get("spec_path", ""),
                })


def add_batch_rows(rows: List[Dict[str, Any]], config: Dict[str, Any], index: Dict[str, Dict[str, Any]]) -> None:
    finals = [r for r in read_csv(FINALS) if clean(r.get("status_norm")).lower() == "final" or clean(r.get("game_state")).lower() == "final"]
    final_count = len(finals)
    if final_count < 2:
        return
    headline = f"Last Night in the W: {final_count} finals"
    for mapping in config.get("batch_mappings", []):
        min_rows = int(mapping.get("min_final_rows", 1))
        if final_count < min_rows:
            continue
        template_id = mapping.get("template_id", "")
        t = template_row(template_id, index)
        for platform in mapping.get("platforms", []):
            rows.append({
                "item_id": f"batch::{mapping.get('name')}::{platform}::{template_id}",
                "source": mapping.get("source", FINALS.as_posix()),
                "source_id": f"today_final_results::{final_count}",
                "row_kind": "batch_result_recap",
                "sport": "basketball",
                "league": "WNBA",
                "platform": platform,
                "template_id": template_id,
                "template_family": t.get("family", ""),
                "template_variant": t.get("variant", ""),
                "mode": mapping.get("mode", ""),
                "headline": headline,
                "status": "mapped",
                "review_only": "true",
                "reason": "review-only batch mapping from final results",
                "spec_path": t.get("spec_path", ""),
            })


def build_payload(rows: List[Dict[str, Any]], registry: Dict[str, Any], config: Dict[str, Any], renderer_v2_ran: bool) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_only": True,
        "renderer_v2_ran": renderer_v2_ran,
        "registry_version": registry.get("version"),
        "mapping_config_version": config.get("version"),
        "mapped_count": len([r for r in rows if r.get("status") == "mapped"]),
        "blocked_count": len([r for r in rows if r.get("status") == "blocked"]),
        "rows": rows,
        "future_mappings": config.get("future_mappings", []),
    }


def write_md(payload: Dict[str, Any]) -> None:
    md = [
        "# HSD Template Render Map v1",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{VERSION}`",
        f"Registry: `{payload['registry_version']}`",
        "",
        "## Policy",
        "",
        "- Review-only render mapping.",
        "- Renderer remains a compiler, not a designer.",
        "- Human review is required before publishing.",
        "",
        "## Summary",
        "",
        f"- Mapped rows: `{payload['mapped_count']}`",
        f"- Blocked rows: `{payload['blocked_count']}`",
        f"- Template Renderer v2 ran: `{payload['renderer_v2_ran']}`",
        "",
        "## Mapped items",
        "",
    ]
    for row in payload.get("rows", []):
        md.append(f"- {row.get('status')} | {row.get('platform')} | `{row.get('template_id')}` | {row.get('headline')}")
    md += ["", "## Future mappings", ""]
    for fm in payload.get("future_mappings", []):
        md.append(f"- {fm.get('family')}: {fm.get('status')}")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


def run_template_renderer_v2() -> bool:
    if not RENDERER_V2_SCRIPT.exists():
        return False
    runpy.run_path(RENDERER_V2_SCRIPT.as_posix(), run_name="__main__")
    return True


def main() -> None:
    config = load_json(CONFIG)
    registry = load_json(REGISTRY)
    index = registry_index(registry)
    rows: List[Dict[str, Any]] = []
    add_event_rows(rows, config, index)
    add_batch_rows(rows, config, index)
    write_csv(OUT_CSV, rows)
    payload = build_payload(rows, registry, config, renderer_v2_ran=False)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    renderer_v2_ran = run_template_renderer_v2()
    payload = build_payload(rows, registry, config, renderer_v2_ran=renderer_v2_ran)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_md(payload)
    print(json.dumps({"version": VERSION, "mapped": payload["mapped_count"], "blocked": payload["blocked_count"], "renderer_v2_ran": renderer_v2_ran, "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
