# HSD Run-Scoped Output Migration Audit

## Decision

Batch 1 asset/graphics and Batch 2 Results/News support migrations are complete.

The asset-stage generators now read run-folder review copies first and write generated review/upload artifacts into `HSD_RUN_OUTPUT_DIR` during local runs. Legacy root compatibility remains when `HSD_RUN_OUTPUT_DIR` is unset.

The remaining Results/News support scripts now write generated reports, dashboards, and expected-games review copies into `HSD_RUN_OUTPUT_DIR` during local runs.

Batch 3 is retired from the active local workflow instead of migrated. The old `womens_sports_scraper.py` path duplicated the current News Sync lane, wrote legacy root files, and did not add enough daily operator value to justify modernizing it right now.

Guardrails stay unchanged:

- Local/manual operation remains the default.
- Free-source behavior remains the default.
- Paid APIs are not part of this migration.
- No auto-publishing or workflow automation should be added.
- Legacy root compatibility should remain when `HSD_RUN_OUTPUT_DIR` is unset.

## Batch 1: Asset And Graphics Generators

Completed run-aware migration:

- `generate_hsd_asset_desk_v1.py`
- `generate_hsd_player_image_assets_v1.py`
- `generate_hsd_graphics_upload_pack_v1.py`
- `generate_hsd_graphics_qa_v1.py`

What changed:

- `generate_hsd_asset_desk_v1.py` writes asset manifests, team/player asset files, and review reports into the active run folder.
- `generate_hsd_player_image_assets_v1.py` stages player image files and approved/player asset table updates as run-folder review copies.
- `generate_hsd_graphics_upload_pack_v1.py` creates upload-pack directories, zip files, status reports, and direct handoff files in the run folder.
- `generate_hsd_graphics_qa_v1.py` reads run-scoped upload packs first and writes QA reports/dashboard output into the run folder.

Important caution:

Separate generated review/upload artifacts from canonical asset registry or approved-asset data. Generated packs now move into the run folder first; source-like asset registry updates remain explicit review decisions.

## Batch 2: Results And News Support Outputs

Completed run-aware migration:

- `scripts/generate_hsd_expected_games_v5.py`
- `scripts/verify_hsd_wnba_schedule_independent_v5.py`
- `generate_news_dashboard_v1.py`

What changed:

- `scripts/generate_hsd_expected_games_v5.py` writes `config/hsd_expected_games_v5.csv`, its manifest, and its report into the active run folder as review copies.
- `scripts/verify_hsd_wnba_schedule_independent_v5.py` reads the run-folder expected-games copy first and writes verifier CSV/JSON/MD reports into the run folder.
- `generate_news_dashboard_v1.py` reads run-folder news inputs first and writes `news_dashboard/index.html` into the run folder.

## Batch 3: Legacy Scraper

Retired from the active local workflow:

- `womens_sports_scraper.py`

Decision:

- It is no longer callable through a local runner mode.
- Keep it as a standalone legacy reference for now.
- Only reintroduce it if it is rebuilt as run-aware through `HSD_RUN_OUTPUT_DIR` and adds value beyond the current News Sync path.

## Non-Runner Cleanup Pass

First selected cleanup:

- `generate_hsd_manual_workflow_merge_v1.py`

Why this was first:

- It is operator-facing: it turns manual editorial inbox rows into copy, render, and handoff packs.
- The local review bundle and command center already know about `manual_workflow_handoff.md` and `manual_workflow_pack_status.csv`.
- It improves the daily operator workflow without adding a source, paid API, workflow trigger, or publishing action.

What changed:

- Manual workflow packets, handoff ZIPs, copy desk files, status files, and handoff markdown now write into `HSD_RUN_OUTPUT_DIR` when set.
- Legacy root output remains available when `HSD_RUN_OUTPUT_DIR` is unset.
- The local runner now exposes an explicit `handoff` mode for this path, then refreshes the review command center.
- This does not add the generator to `full`; the operator still chooses when to run this manual handoff layer.

Second selected cleanup:

- `generate_hsd_final_score_stories_v1.py`

Why this was next:

- It is operator-facing: it turns recent verified final scores into IG Story graphics upload packs.
- The lite review pack, manual workflow merge, multi-post desk, and command center already know about `ig_story_results_*` artifacts.
- It improves the daily operator workflow without adding a paid source, workflow trigger, or publishing action.

What changed:

- Final-score story queue files, guard reports, upload-pack folders, and ZIPs now write into `HSD_RUN_OUTPUT_DIR` when set.
- Legacy root output remains available when `HSD_RUN_OUTPUT_DIR` is unset.
- The local runner now exposes an explicit `stories` mode for this path, then refreshes the review command center.
- This does not add the generator to `full`; the operator still chooses when to build result-story packs.

Third selected cleanup:

- `generate_hsd_multi_post_desk_v1.py`

Why this was next:

- It is operator-facing: it turns handoff, story, and slate artifacts into a platform-by-platform daily posting board.
- The outputs answer a practical daily question: what should go to IG Feed, IG Stories, and Threads today.
- It improves the daily operator workflow without adding a paid source, workflow trigger, or publishing action.

What changed:

- Multi-post board files, post-slot status, platform queues, caption bank, and first-comment hooks now write into `HSD_RUN_OUTPUT_DIR` when set.
- Legacy root output remains available when `HSD_RUN_OUTPUT_DIR` is unset.
- The local runner now exposes an explicit `posts` mode for this path, then refreshes the review command center.
- This does not add the generator to `full`; the operator still chooses when to build the multi-post board.

## Already Run-Scoped Or Run-Aware

Current local runner scripts already moved or made run-aware:

- `generate_hsd_results_desk_v5.py`
- `generate_hsd_news_sync_v1.py`
- `generate_hsd_studio_bridge_v1.py`
- `generate_hsd_tonight_preview_bridge_v1.py`
- `generate_hsd_preview_quality_gate_v1.py`
- `generate_hsd_asset_desk_v1.py`
- `generate_hsd_player_image_assets_v1.py`
- `generate_hsd_graphics_upload_pack_v1.py`
- `generate_hsd_graphics_qa_v1.py`
- `generate_hsd_manual_workflow_merge_v1.py`
- `generate_hsd_final_score_stories_v1.py`
- `generate_hsd_multi_post_desk_v1.py`
- `scripts/generate_hsd_expected_games_v5.py`
- `scripts/verify_hsd_wnba_schedule_independent_v5.py`
- `generate_news_dashboard_v1.py`
- `publish_hsd_guard_v1.py`
- `generate_hsd_operator_status_v1.py`
- `generate_hsd_bebe_daily_ops_plan_v2.py`
- `generate_hsd_operator_command_center_v2.py`
- `generate_hsd_pipeline_review_lite_v1.py`

## Repeatable Audit

Run this manually when planning another migration pass:

```powershell
.\.venv\Scripts\python.exe scripts\report_hsd_run_output_migration_v1.py --print-md
```

When `HSD_RUN_OUTPUT_DIR` is set, the audit report writes into that run folder. Without it, the script preserves legacy behavior and writes the report to the current working folder.
