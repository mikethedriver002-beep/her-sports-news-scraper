from __future__ import annotations
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

WORKFLOW = Path(".github/workflows/hsd-pipeline-control-v1.yml")
DISABLED_DIR = Path(".github/workflows_disabled")
MPD_STEP = """      - name: Generate Multi-Post Desk v1
        if: always()
        shell: bash
        run: python generate_hsd_multi_post_desk_v1.py || true
"""

MPD_ARTIFACT_LINES = [
    "            multi_post_daily_board.md",
    "            multi_post_daily_board.json",
    "            post_slot_status.csv",
    "            ig_feed_queue.csv",
    "            ig_story_queue.csv",
    "            threads_queue.csv",
    "            caption_bank.md",
    "            first_comment_hooks.md",
]

def patch_workflow() -> None:
    if not WORKFLOW.exists():
        raise SystemExit(f"Missing workflow: {WORKFLOW}")
    text = WORKFLOW.read_text(encoding="utf-8", errors="replace")

    text = re.sub(r"^name: .*$", "name: HSD Mermaid Ops v1", text, count=1, flags=re.M)
    if re.search(r"^run-name:", text, flags=re.M):
        text = re.sub(
            r"^run-name: .*$",
            "run-name: HSD Mermaid Ops v1 • ${{ github.event.inputs.run_mode || 'full_pipeline' }} • run ${{ github.run_number }}",
            text,
            count=1,
            flags=re.M,
        )
    else:
        text = text.replace("name: HSD Mermaid Ops v1\n", "name: HSD Mermaid Ops v1\nrun-name: HSD Mermaid Ops v1 • ${{ github.event.inputs.run_mode || 'full_pipeline' }} • run ${{ github.run_number }}\n", 1)

    text = re.sub(r'HSD_RELEASE_VERSION: ".*?"', 'HSD_RELEASE_VERSION: "v3.2.14-mermaid-ops-v1.0"', text)
    text = re.sub(r'HSD_ARTIFACT_NAME_PREFIX: ".*?"', 'HSD_ARTIFACT_NAME_PREFIX: "hsd-mermaid-ops-v1"', text)
    text = text.replace("BeBe daily ops", "Mermaid daily ops").replace("BeBe Ops", "Mermaid Ops")

    if "generate_hsd_multi_post_desk_v1.py" not in text:
        marker = "      - name: Build preliminary"
        pos = text.find(marker)
        if pos == -1:
            marker = "      - name: Run News Sync stage"
            pos = text.find(marker)
        if pos == -1:
            raise SystemExit("Could not find insertion point for Multi-Post Desk step.")
        text = text[:pos] + MPD_STEP + "\n" + text[pos:]

    final_status = "python generate_hsd_manual_workflow_merge_v1.py || true"
    if final_status in text and "python generate_hsd_multi_post_desk_v1.py || true" not in text.split("      - name: Build lite review artifact")[0]:
        text = text.replace(final_status, final_status + "\n          python generate_hsd_multi_post_desk_v1.py || true", 1)

    text = re.sub(
        r"name: hsd-production-control-[^\\n]+",
        "name: hsd-mermaid-ops-v1-lite-review-${{ github.run_number }}",
        text,
        count=1,
    )

    if "multi_post_daily_board.md" not in text:
        insert_after = "            manual_workflow_handoff_packs/*.zip"
        if insert_after in text:
            text = text.replace(insert_after, insert_after + "\n" + "\n".join(MPD_ARTIFACT_LINES), 1)
        else:
            insert_after = "            operator_command_center.json"
            text = text.replace(insert_after, insert_after + "\n" + "\n".join(MPD_ARTIFACT_LINES), 1)

    if '"manual_workflow_handoff.md"' in text and '"multi_post_daily_board.md"' not in text:
        text = text.replace(
            '"manual_workflow_handoff.md"',
            '"manual_workflow_handoff.md"\n            "multi_post_daily_board.md" "multi_post_daily_board.json" "post_slot_status.csv" "ig_feed_queue.csv" "ig_story_queue.csv" "threads_queue.csv" "caption_bank.md" "first_comment_hooks.md"',
            1,
        )

    WORKFLOW.write_text(text, encoding="utf-8")

def update_versions() -> None:
    pipeline = {
        "pipeline_name": "Her Sports Daily Mermaid Ops",
        "pipeline_version": "v3.2.14-mermaid-ops-v1.0",
        "contract_version": "v2",
        "operator_codename": "BB",
        "system_codename": "Mermaid",
        "default_publish_mode": "artifact_only",
        "default_review_artifact_size": "lite",
        "platforms": ["Instagram", "Threads"],
        "github_visible_version": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "release_date_local": "2026-06-12",
        "notes": "Mermaid workflow consolidation plus Multi-Post Desk v1.",
    }
    Path("config/pipeline_version.json").write_text(json.dumps(pipeline, indent=2), encoding="utf-8")
    release = {
        "release": "Mermaid Ops v1",
        "pipeline_version": "v3.2.14-mermaid-ops-v1.0",
        "github_visible_name": "HSD Mermaid Ops v1",
        "artifact_name_prefix": "hsd-mermaid-ops-v1",
        "assistant_operator": "BB",
        "system_codename": "Mermaid",
        "release_date_local": "2026-06-12",
        "summary": "Workflow consolidation, Actions declutter, and Multi-Post Desk v1 wiring.",
    }
    Path("config/hsd_release_version.json").write_text(json.dumps(release, indent=2), encoding="utf-8")

def move_old_workflows() -> None:
    active = WORKFLOW.resolve()
    DISABLED_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in Path(".github/workflows").glob("*"):
        if not p.is_file() or p.resolve() == active:
            continue
        if p.suffix.lower() not in {".yml", ".yaml"}:
            continue
        dest = DISABLED_DIR / f"{p.name}.disabled"
        if dest.exists():
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest = DISABLED_DIR / f"{p.name}.{stamp}.disabled"
        shutil.move(str(p), str(dest))
        moved.append((p.as_posix(), dest.as_posix()))
    if moved:
        print("Moved old workflows out of .github/workflows:")
        for src, dest in moved:
            print(f"- {src} -> {dest}")
    else:
        print("No extra workflow files found to move.")

def main() -> None:
    patch_workflow()
    update_versions()
    move_old_workflows()
    print("Mermaid workflow consolidation complete.")
    print("Next: git add . && git commit -m 'Install HSD Mermaid Ops v1 workflow consolidation' && git push origin main")

if __name__ == "__main__":
    main()
