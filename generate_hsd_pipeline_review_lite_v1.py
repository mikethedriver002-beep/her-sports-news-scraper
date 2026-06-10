from __future__ import annotations

import csv, json, os, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-pipeline-review-lite-v1.7"
OUT_DIR = Path("hsd_pipeline_lite_review")
OUT_ZIP = Path("hsd_pipeline_lite_review.zip")

KEY_FILES = [
    "pipeline_outcome.md",
    "pipeline_stop_reason.md",
    "studio_preview_fallback_report.md",
    "results_freshness_report.md",
    "results_freshness_gate.csv",
    "results_freshness_manifest.json",
    "latest_results_run_summary.md",
    "latest_news_sync_run_summary.md",
    "latest_studio_run_summary.md",
    "latest_asset_visual_qa_run_summary.md",
    "news_setup_error.md",
    "news_input_status_report.csv",
    "news_fact_packets.csv",
    "studio_fresh_packet_report.md",
    "studio_fresh_packet_gate.csv",
    "studio_bundle_queue.csv",
    "studio_bundle_packets.md",
    "studio_bundle_prompts.md",
    "studio_graphics_queue.csv",
    "graphics_upload_pack_status.csv",
    "graphics_chat_direct_handoff.md",
    "graphics_qa_report.md",
    "player_image_sourcing_report.md",
    "player_image_requirements.csv",
    "player_image_fit_report.md",
    "player_image_fit_gate.csv",
    "studio_freshness_report.md",
    "studio_freshness_gate.csv",
    "asset_candidates_review.md",
    "asset_manifest.csv",
    "team_assets.csv",
    "approved_graphics_assets.csv",
    "graphics_chat_upload_manifest.csv",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def count_csv(path: str) -> int:
    p=Path(path)
    if not p.exists(): return 0
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in csv.DictReader(f)))
    except Exception:
        return 0


def read_csv_rows(path: str, limit: int = 50) -> List[Dict[str, str]]:
    p=Path(path)
    if not p.exists(): return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return [r for _, r in zip(range(limit), csv.DictReader(f))]
    except Exception:
        return []


def head_text(path: str, chars: int = 12000) -> str:
    p=Path(path)
    if not p.exists(): return ""
    txt=p.read_text(encoding="utf-8", errors="replace")
    if len(txt) > chars:
        return txt[:chars] + "\n\n...[truncated by lite review]...\n"
    return txt


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def summarize_results() -> Dict[str, Any]:
    out={"fresh":0,"stale":0,"missing":0,"examples":[]}
    for r in read_csv_rows("results_freshness_gate.csv", 200):
        st=clean(r.get("status"))
        if st == "fresh": out["fresh"] += 1
        elif st == "stale": out["stale"] += 1
        elif st: out["missing"] += 1
        if len(out["examples"]) < 8:
            out["examples"].append({k:r.get(k,"") for k in ["headline","event_date","event_age_hours","status","source_file"]})
    return out


def summarize_studio() -> Dict[str, Any]:
    rows=read_csv_rows("studio_fresh_packet_gate.csv", 200)
    counts={}
    examples=[]
    for r in rows:
        st=clean(r.get("freshness_status") or r.get("freshness_decision"))
        counts[st]=counts.get(st,0)+1
        if len(examples)<8:
            examples.append({k:r.get(k,"") for k in ["headline","event_date","event_age_hours","freshness_status","freshness_decision"]})
    return {"rows":len(rows),"counts":counts,"examples":examples}


def summarize_upload() -> Dict[str, Any]:
    rows=read_csv_rows("graphics_upload_pack_status.csv", 50)
    return {"rows":len(rows),"bundles":[{k:r.get(k,"") for k in ["bundle_name","upload_pack_status","assets_expected","assets_ready","assets_missing","missing_asset_names","zip_path"]} for r in rows]}



def ready_upload_pack_zips(max_mb: float = 25.0) -> List[Dict[str, Any]]:
    """Copy ready/ready_with_review pack ZIPs into the lite review when small enough."""
    out: List[Dict[str, Any]] = []
    dest_dir = OUT_DIR / "ready_upload_packs"
    for row in read_csv_rows("graphics_upload_pack_status.csv", 100):
        status = clean(row.get("upload_pack_status")).lower()
        zip_path = clean(row.get("zip_path"))
        if status not in {"ready", "ready_with_review"} or not zip_path:
            continue
        p = Path(zip_path)
        if not p.exists():
            out.append({"bundle_name": row.get("bundle_name",""), "status": status, "zip_path": zip_path, "included": "no", "reason": "zip_missing"})
            continue
        size_mb = p.stat().st_size / (1024 * 1024)
        if size_mb > max_mb:
            out.append({"bundle_name": row.get("bundle_name",""), "status": status, "zip_path": zip_path, "included": "no", "reason": f"too_large_{size_mb:.1f}mb"})
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / p.name
        dest.write_bytes(p.read_bytes())
        out.append({"bundle_name": row.get("bundle_name",""), "status": status, "zip_path": str(dest.relative_to(OUT_DIR)), "included": "yes", "reason": f"{size_mb:.2f}mb"})
    return out

def main() -> None:
    if OUT_DIR.exists():
        import shutil; shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ready_packs = ready_upload_pack_zips()
    status={
        "version":VERSION,
        "generated_at_utc":now(),
        "counts":{
            "results_freshness_rows":count_csv("results_freshness_gate.csv"),
            "news_fact_packets":count_csv("news_fact_packets.csv"),
            "studio_bundle_rows":count_csv("studio_bundle_queue.csv"),
            "upload_pack_rows":count_csv("graphics_upload_pack_status.csv"),
            "player_image_requirements":count_csv("player_image_requirements.csv"),
        },
        "results":summarize_results(),
        "studio":summarize_studio(),
        "upload_packs":summarize_upload(),
        "ready_upload_packs_included": ready_packs,
        "stop_reason_file_exists":Path("pipeline_stop_reason.md").exists(),
        "outcome_file_exists":Path("pipeline_outcome.md").exists(),
    }
    (OUT_DIR/"pipeline_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    lines=["# HSD Pipeline Lite Review", "", f"Generated: {status['generated_at_utc']}", "", "## Counts", ""]
    for k,v in status["counts"].items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Results freshness", "", f"- fresh: {status['results']['fresh']}", f"- stale: {status['results']['stale']}", f"- missing/other: {status['results']['missing']}", ""]
    if status["results"]["examples"]:
        lines += ["### Examples", ""] + [f"- {x.get('headline')} | {x.get('event_date')} | {x.get('event_age_hours')}h | {x.get('status')} | {x.get('source_file')}" for x in status['results']['examples']] + [""]
    lines += ["## Studio", "", f"- fresh packet rows: {status['studio']['rows']}", f"- status counts: `{json.dumps(status['studio']['counts'])}`", ""]
    if status['studio']['examples']:
        lines += ["### Examples", ""] + [f"- {x.get('headline')} | {x.get('event_date')} | {x.get('event_age_hours')}h | {x.get('freshness_status')} | {x.get('freshness_decision')}" for x in status['studio']['examples']] + [""]
    lines += ["## Upload packs", ""]
    for b in status["upload_packs"]["bundles"]:
        lines.append(f"- {b.get('bundle_name')}: {b.get('upload_pack_status')} | ready {b.get('assets_ready')}/{b.get('assets_expected')} | missing {b.get('missing_asset_names')}")
    if status.get("ready_upload_packs_included"):
        lines += ["", "## Ready upload packs included", ""]
        for pack in status["ready_upload_packs_included"]:
            lines.append(f"- {pack.get('bundle_name')}: included={pack.get('included')} | {pack.get('zip_path')} | {pack.get('reason')}")
    if Path("pipeline_outcome.md").exists():
        lines += ["", "## Outcome", "", "```", head_text("pipeline_outcome.md", 3000), "```"]
    if Path("pipeline_stop_reason.md").exists():
        lines += ["", "## Stop reason", "", "```", head_text("pipeline_stop_reason.md", 3000), "```"]
    (OUT_DIR/"README.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

    # Copy small key files only, trimming very large markdown when needed.
    files_dir=OUT_DIR/"files"
    files_dir.mkdir(exist_ok=True)
    manifest=[]
    for name in KEY_FILES:
        p=Path(name)
        if not p.exists():
            continue
        dest=files_dir/name.replace("/","__")
        if p.suffix.lower() in {".md", ".txt", ".json", ".csv"} and p.stat().st_size > 250_000:
            dest.write_text(head_text(name, 50000), encoding="utf-8")
            copied_size=dest.stat().st_size; note="truncated"
        else:
            dest.write_bytes(p.read_bytes())
            copied_size=dest.stat().st_size; note="full"
        manifest.append({"source":name,"lite_path":str(dest.relative_to(OUT_DIR)),"bytes":copied_size,"mode":note})
    write_csv(OUT_DIR/"lite_manifest.csv", manifest, ["source","lite_path","bytes","mode"])
    if OUT_ZIP.exists(): OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in OUT_DIR.rglob("*"):
            if p.is_file(): z.write(p, p.relative_to(OUT_DIR.parent))
    print(json.dumps({"lite_review_dir":str(OUT_DIR),"lite_review_zip":str(OUT_ZIP),"zip_bytes":OUT_ZIP.stat().st_size,"files":len(manifest)}, indent=2))

if __name__ == "__main__":
    main()
