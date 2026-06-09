# HSD Asset Visual QA v1.3.1

This is the next upgrade after v1.1.

## What v1.2 adds

- exact entity cleanup
- stat-token filtering so PTS, REB, AST, STL do not become fake teams
- expanded WNBA team logo registry
- safer player image pipeline
- safe graphics mode flag
- fact warning queue for suspicious player-team mismatches
- improved visual prompts that explicitly ban player photos unless exact player assets exist
- QA fail logic when fact warnings exist
- always writes latest_asset_visual_qa_run_summary.md

## Main outputs

- approved_graphics_assets.csv
- team_assets.csv
- player_assets.csv
- launch_integration_points.csv
- fact_warning_queue.csv
- studio_bundle_prompts_v2.md
- graphics_qa_report.md
- latest_asset_visual_qa_run_summary.md

## Operational note

If no exact player image is verified, the system will intentionally force a logo-and-text-forward graphic instead of making up a player visual.


## v1.2.2 QoL + warning propagation patch

Adds:

- `chatgpt_review_pack/`
- `hsd_chatgpt_review_packet.md`

Upload `hsd_chatgpt_review_packet.md` for the fastest review, or upload the 9 numbered files in `chatgpt_review_pack/` for deeper debugging.

Also fixes warning propagation so `fact_warning_queue.csv` warnings reach `studio_bundle_prompts_v2.md` and QA even when bundle IDs differ between source files.


## v1.2.2

This patch updates the `PLAYER_TEAM_HINTS` mapping for Jessica Shepard from Minnesota Lynx to Dallas Wings so the WNBA result bundle stops failing on a stale team hint while keeping all v1.2.1 warning propagation and review-pack improvements.


## v1.3 Graphics Chat Upload Pack

This patch fixes the logo URL problem.

The graphics chat should not be expected to fetch logo URLs. v1.3 creates local upload-ready asset packs:

```text
graphics_chat_upload_pack/
graphics_chat_upload_pack_zips/
graphics_chat_upload_manifest.csv
graphics_chat_upload_instructions.md
```

For a post, upload the matching ZIP or the folder contents to the graphics chat. The graphics chat should use only attached asset files and never fetch or invent logos.


## v1.3.1

Adds a direct graphics handoff file and forces the review packet + run summary to include the graphics upload pack outputs so you can verify the ZIPs actually exist after each run.
