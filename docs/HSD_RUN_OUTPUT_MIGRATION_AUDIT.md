# HSD Run-Scoped Output Migration Audit

## Decision

Batch 1 asset and graphics generator migration is complete.

The asset-stage generators now read run-folder review copies first and write generated review/upload artifacts into `HSD_RUN_OUTPUT_DIR` during local runs. Legacy root compatibility remains when `HSD_RUN_OUTPUT_DIR` is unset.

Move Batch 2 next: the remaining Results/News support scripts that still write root files.

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

Recommended after Batch 1:

- `scripts/generate_hsd_expected_games_v5.py`
- `scripts/verify_hsd_wnba_schedule_independent_v5.py`
- `generate_news_dashboard_v1.py`

Why second:

- These still write root support reports during the Results and News path.
- They have fewer output surfaces than the asset/graphics stage.
- They should be easier to route through `hsd_run_io`.

## Batch 3: Legacy Scraper

Recommended after the normal runner path is clean:

- `womens_sports_scraper.py`

Why third:

- It is still callable through `-Mode scraper`.
- It is legacy and lower priority than the active daily operator path.

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
