from __future__ import annotations
import json
from pathlib import Path

WORKFLOW = Path(".github/workflows/hsd-pipeline-control-v1.yml")

QUALITY_STEP = """\n      - name: Mermaid Quality Brain v2.1\n        if: always()\n        shell: bash\n        run: python generate_hsd_mermaid_quality_brain_v2_1.py || true\n"""

ARTIFACT_LINES = [
    "            mermaid_quality_brain_report.md",
    "            mermaid_quality_brain_manifest.json",
    "            mermaid_master_content_board_v2_1.md",
    "            multisport_scout_candidates_filtered.csv",
    "            multisport_rejected_candidates.csv",
    "            mermaid_quality_story_graph.csv",
    "            mermaid_quality_content_slots.csv",
    "            ig_feed_queue_v2_1.csv",
    "            ig_story_queue_v2_1.csv",
    "            threads_queue_v2_1.csv",
    "            breaking_news_queue_v2_1.csv",
    "            rumor_watch_queue_v2_1.csv",
    "            player_asset_debt_v2_1.csv",
    "            mermaid_quality_prompt_index.csv",
    "            mermaid_quality_compiled_packets/**",
    "            operator_next_actions_v2_1.md",
]

def patch_workflow() -> None:
    if not WORKFLOW.exists():
        raise SystemExit(f"Missing workflow file: {WORKFLOW}")
    text = WORKFLOW.read_text(encoding="utf-8", errors="replace")
    text = text.replace('HSD_RELEASE_VERSION: "v3.3.0-mermaid-upper-echelon-v2"', 'HSD_RELEASE_VERSION: "v3.3.1-mermaid-quality-brain-v2.1"')

    if "generate_hsd_mermaid_quality_brain_v2_1.py" not in text:
        marker = "      - name: Final status and review artifact"
        pos = text.find(marker)
        if pos == -1:
            raise SystemExit("Could not find Final status insertion point.")
        text = text[:pos] + QUALITY_STEP + "\n" + text[pos:]

    if "mermaid_quality_brain_report.md" not in text:
        marker = "            mermaid_upper_echelon_report.md"
        if marker in text:
            text = text.replace(marker, marker + "\n" + "\n".join(ARTIFACT_LINES), 1)
        else:
            marker = "            first_comment_hooks.md"
            text = text.replace(marker, marker + "\n" + "\n".join(ARTIFACT_LINES), 1)

    WORKFLOW.write_text(text, encoding="utf-8")

def patch_versions() -> None:
    pv = Path("config/pipeline_version.json")
    data = json.loads(pv.read_text(encoding="utf-8")) if pv.exists() else {}
    data.update({
        "pipeline_name": "Her Sports Daily Mermaid Ops",
        "pipeline_version": "v3.3.1-mermaid-quality-brain-v2.1",
        "operator_codename": "BB",
        "system_codename": "Mermaid",
        "github_visible_version": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "notes": "Quality Brain v2.1: scout filtering, sport balancing, player asset debt bridge, upgraded ranking, HSD voice prompt packets."
    })
    pv.write_text(json.dumps(data, indent=2), encoding="utf-8")

    rv = Path("config/hsd_release_version.json")
    rv.write_text(json.dumps({
        "release": "HSD Mermaid Quality Brain v2.1",
        "pipeline_version": "v3.3.1-mermaid-quality-brain-v2.1",
        "github_visible_name": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "assistant_operator": "BB",
        "system_codename": "Mermaid",
        "summary": "Quality Brain: removes scout junk, balances sports, bridges asset debt, improves content ranking, and compiles HSD-style quality packets."
    }, indent=2), encoding="utf-8")

def main() -> None:
    patch_workflow()
    patch_versions()
    print("Installed HSD Mermaid Quality Brain v2.1 wiring. Commit and push changes.")

if __name__ == "__main__":
    main()
