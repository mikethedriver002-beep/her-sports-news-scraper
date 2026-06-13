
from __future__ import annotations
import json
from pathlib import Path

WORKFLOW = Path(".github/workflows/hsd-pipeline-control-v1.yml")

UPPER_STEP = """      - name: Mermaid Upper Echelon Control Plane
        if: always()
        shell: bash
        run: |
          python generate_hsd_mermaid_upper_echelon_v2.py || true
"""

ARTIFACT_LINES = [
    "            mermaid_upper_echelon_report.md",
    "            mermaid_upper_echelon_manifest.json",
    "            mermaid_story_graph.csv",
    "            mermaid_story_graph.jsonl",
    "            mermaid_story_graph_report.md",
    "            mermaid_master_content_board.md",
    "            mermaid_content_slots_v2.csv",
    "            mermaid_content_engine_manifest.json",
    "            multisport_scout_candidates.csv",
    "            multisport_scout_report.md",
    "            multisport_scout_manifest.json",
    "            social_rumor_candidates.csv",
    "            social_rumor_desk_report.md",
    "            social_rumor_desk_manifest.json",
    "            player_asset_registry.csv",
    "            player_asset_debt.csv",
    "            player_registry_status.md",
    "            player_registry_manifest.json",
    "            official_player_headshot_candidates.csv",
    "            official_player_headshot_report.md",
    "            mermaid_compiled_packet_index.csv",
    "            mermaid_prompt_compiler_report.md",
    "            mermaid_compiled_packets/**",
    "            ig_feed_queue_v2.csv",
    "            ig_story_queue_v2.csv",
    "            threads_queue_v2.csv",
    "            breaking_news_queue.csv",
    "            rumor_watch_queue.csv",
]

def patch_workflow() -> None:
    if not WORKFLOW.exists():
        raise SystemExit(f"Missing workflow file: {WORKFLOW}")
    text = WORKFLOW.read_text(encoding="utf-8", errors="replace")
    text = text.replace('HSD_RELEASE_VERSION: "v3.2.17-mermaid-preview-player-lock-v2"', 'HSD_RELEASE_VERSION: "v3.3.0-mermaid-upper-echelon-v2"')
    if "generate_hsd_mermaid_upper_echelon_v2.py" not in text:
        marker = "      - name: Upload lite production review artifact"
        pos = text.find(marker)
        if pos == -1:
            raise SystemExit("Could not find artifact upload step insertion point.")
        text = text[:pos] + UPPER_STEP + "\n" + text[pos:]
    if "mermaid_upper_echelon_report.md" not in text:
        marker = "            first_comment_hooks.md"
        if marker in text:
            text = text.replace(marker, marker + "\n" + "\n".join(ARTIFACT_LINES), 1)
        else:
            marker = "            source_registry_audit.json"
            text = text.replace(marker, marker + "\n" + "\n".join(ARTIFACT_LINES), 1)
    WORKFLOW.write_text(text, encoding="utf-8")

def patch_versions() -> None:
    pv = Path("config/pipeline_version.json")
    data = json.loads(pv.read_text(encoding="utf-8")) if pv.exists() else {}
    data.update({
        "pipeline_name": "Her Sports Daily Mermaid Ops",
        "pipeline_version": "v3.3.0-mermaid-upper-echelon-v2",
        "operator_codename": "BB",
        "system_codename": "Mermaid",
        "github_visible_version": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "notes": "Upper Echelon v2: story graph, multi-sport scout, rumor desk, player registry v2, deterministic prompt compiler, and multi-slot content engine."
    })
    pv.write_text(json.dumps(data, indent=2), encoding="utf-8")
    rv = Path("config/hsd_release_version.json")
    rv.write_text(json.dumps({
        "release": "HSD Mermaid Upper Echelon v2",
        "pipeline_version": "v3.3.0-mermaid-upper-echelon-v2",
        "github_visible_name": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "assistant_operator": "BB",
        "system_codename": "Mermaid",
        "summary": "Story graph control plane, multi-sport scout, rumor desk, player registry v2, deterministic prompt compiler, and expanded daily content engine."
    }, indent=2), encoding="utf-8")

def main() -> None:
    patch_workflow()
    patch_versions()
    print("Installed HSD Mermaid Upper Echelon v2 wiring. Commit and push changes.")

if __name__ == "__main__":
    main()
