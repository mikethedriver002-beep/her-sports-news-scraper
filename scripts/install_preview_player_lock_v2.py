from __future__ import annotations
import json
from pathlib import Path

WORKFLOW = Path(".github/workflows/hsd-pipeline-control-v1.yml")
STEP = "            python generate_hsd_preview_player_lock_v2.py || true\n"
ARTIFACT_LINES = [
    "            tonight_preview_player_lock_v2_report.md",
    "            tonight_preview_player_lock_v2.csv",
    "            tonight_preview_player_lock_v2_status.json",
    "            tonight_preview_safe_prompt_v2.md",
    "            tonight_preview_copy_family_guard.csv",
    "            tonight_preview_matchup_plan_v2.md",
    "            tonight_preview_asset_actions_v2.csv",
]

def patch_workflow() -> None:
    if not WORKFLOW.exists():
        raise SystemExit(f"Missing {WORKFLOW}")
    text = WORKFLOW.read_text(encoding="utf-8", errors="replace")
    text = text.replace('HSD_RELEASE_VERSION: "v3.2.16-mermaid-preview-intelligence-v1.0"', 'HSD_RELEASE_VERSION: "v3.2.17-mermaid-preview-player-lock-v2"')
    if "generate_hsd_preview_player_lock_v2.py" not in text:
        marker = "            python generate_hsd_preview_intelligence_v1.py || true\n"
        if marker in text:
            text = text.replace(marker, marker + STEP, 1)
        else:
            marker = "            python generate_hsd_graphics_upload_pack_v1.py\n"
            text = text.replace(marker, marker + STEP, 1)
    if "tonight_preview_player_lock_v2_report.md" not in text:
        marker = "            tonight_preview_graphics_chat_override.txt\n"
        if marker in text:
            text = text.replace(marker, marker + "\n".join(ARTIFACT_LINES) + "\n", 1)
        else:
            marker = "            tonight_preview_pack_status.json\n"
            text = text.replace(marker, marker + "\n" + "\n".join(ARTIFACT_LINES), 1)
    WORKFLOW.write_text(text, encoding="utf-8")

def patch_versions() -> None:
    pv = Path("config/pipeline_version.json")
    data = json.loads(pv.read_text(encoding="utf-8")) if pv.exists() else {}
    data.update({
        "pipeline_name": "Her Sports Daily Mermaid Ops",
        "pipeline_version": "v3.2.17-mermaid-preview-player-lock-v2",
        "operator_codename": "BB",
        "system_codename": "Mermaid",
        "github_visible_version": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "notes": "Preview Player Lock v2: strict player gate, no generated player slides unless one exact player per slate team is attached."
    })
    pv.write_text(json.dumps(data, indent=2), encoding="utf-8")
    rv = Path("config/hsd_release_version.json")
    release = {
        "release": "HSD Mermaid Preview Player Lock v2",
        "pipeline_version": "v3.2.17-mermaid-preview-player-lock-v2",
        "github_visible_name": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "assistant_operator": "BB",
        "system_codename": "Mermaid",
        "summary": "Strict preview-player asset gate and safe prompt rewriting."
    }
    rv.write_text(json.dumps(release, indent=2), encoding="utf-8")

def main() -> None:
    patch_workflow()
    patch_versions()
    print("Installed Preview Player Lock v2 wiring. Commit and push changes.")

if __name__ == "__main__":
    main()
