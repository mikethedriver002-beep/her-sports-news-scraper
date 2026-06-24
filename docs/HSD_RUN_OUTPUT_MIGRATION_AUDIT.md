# HSD Run-Scoped Output Migration Audit

## Decision

Move the asset and graphics generators next.

They are the remaining normal local-run stage with the highest root-output risk after the daily Results, News, Studio, Preview, and Operator scripts were moved to `HSD_RUN_OUTPUT_DIR`.

Guardrails stay unchanged:

- Local/manual operation remains the default.
- Free-source behavior remains the default.
- Paid APIs are not part of this migration.
- No auto-publishing or workflow automation should be added.
- Legacy root compatibility should remain when `HSD_RUN_OUTPUT_DIR` is unset.

## Batch 1: Asset And Graphics Generators

Recommended next implementation batch:

- `generate_hsd_asset_desk_v1.py`
- `generate_hsd_player_image_assets_v1.py`
- `generate_hsd_graphics_upload_pack_v1.py`
- `generate_hsd_graphics_qa_v1.py`

Why this batch is first:

- These scripts are called by local `-Mode asset`.
- They create the most remaining root files and generated folders in the normal local runner path.
- `generate_hsd_graphics_upload_pack_v1.py` creates upload-pack directories, zip files, status reports, and direct handoff files.
- `generate_hsd_player_image_assets_v1.py` copies image assets and writes player/approved-asset outputs.
- `generate_hsd_asset_desk_v1.py` writes asset manifests, team/player asset files, and review reports.
- `generate_hsd_graphics_qa_v1.py` writes QA reports and dashboard output.

Important caution:

Separate generated review/upload artifacts from canonical asset registry or approved-asset data. Generated packs should move into the run folder first; source-like asset registry updates should remain explicit review decisions.

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
