from __future__ import annotations
import hashlib, json, os, shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

VERSION = "hsd-run-manifest-v3.0"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def main() -> None:
    now = datetime.now(timezone.utc)
    github_run_id = os.environ.get("GITHUB_RUN_ID", "local")
    run_id = os.environ.get("HSD_RUN_ID") or f"{now.strftime('%Y%m%dT%H%M%SZ')}_{github_run_id}"
    run_dir = Path(os.environ.get("HSD_RUN_DIR", f"runs/{run_id}"))
    for sub in ["manifest", "results", "stories", "slate", "studio", "assets", "graphics", "audit", "review"]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    config = {
        "pipeline_version": read_json("config/pipeline_version.json"),
        "daily_slate": read_json("config/daily_slate.json"),
        "source_registry": read_json("config/source_registry.json"),
        "url_policy": read_json("config/url_policy.json"),
        "env": {
            "HSD_RUN_MODE": os.environ.get("HSD_RUN_MODE", ""),
            "HSD_PUBLISH_MODE": os.environ.get("HSD_PUBLISH_MODE", "artifact_only"),
            "HSD_CONTENT_VOLUME": os.environ.get("HSD_CONTENT_VOLUME", "balanced"),
            "HSD_MAX_RESULT_FRESH_HOURS": os.environ.get("HSD_MAX_RESULT_FRESH_HOURS", "18"),
            "HSD_PREVIEW_LOOKAHEAD_HOURS": os.environ.get("HSD_PREVIEW_LOOKAHEAD_HOURS", "30"),
            "HSD_GREY_SOURCE_MODE": os.environ.get("HSD_GREY_SOURCE_MODE", "review_only"),
        }
    }

    input_candidates = [
        "top_womens_results.csv", "today_final_results.csv", "today_womens_results.csv",
        "reconciled_events.csv", "today_results_board.csv", "today_box_scores.csv",
        "top_performers.csv", "operator/inbox/story_inbox.csv", "operator/inbox/story_inbox.jsonl",
        "config/source_registry.json", "config/daily_slate.json", "config/url_policy.json",
    ]
    input_hashes = {}
    for name in input_candidates:
        p = Path(name)
        if p.exists():
            input_hashes[name] = {"sha256": sha256_file(p), "size": p.stat().st_size}

    manifest = {
        "version": VERSION,
        "run_id": run_id,
        "run_dir": run_dir.as_posix(),
        "run_started_at_utc": now.isoformat(),
        "github_run_id": github_run_id,
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "github_ref": os.environ.get("GITHUB_REF", ""),
        "config": config,
        "input_hashes": input_hashes,
    }
    (run_dir / "manifest/run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (run_dir / "manifest/config_snapshot.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (run_dir / "manifest/input_hashes.json").write_text(json.dumps(input_hashes, indent=2), encoding="utf-8")
    Path("hsd_current_run.json").write_text(json.dumps({"run_id": run_id, "run_dir": run_dir.as_posix()}, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": run_id, "run_dir": run_dir.as_posix()}, indent=2))

if __name__ == "__main__":
    main()
