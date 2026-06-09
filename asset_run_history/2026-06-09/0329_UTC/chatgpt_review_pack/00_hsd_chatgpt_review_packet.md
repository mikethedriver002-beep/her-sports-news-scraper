# HSD ChatGPT Review Packet

Upload this single file for review. The numbered files in `chatgpt_review_pack/` are included only for deeper debugging.

## latest_asset_visual_qa_run_summary.md

# HSD Asset Visual QA v1.5.1 Run Summary

Run timestamp UTC: `2026-06-09 03:29:17 UTC`
Archive folder: `asset_run_history/2026-06-09/0329_UTC`

## Row counts

- `asset_manifest.csv`: 25
- `team_assets.csv`: 25
- `player_assets.csv`: 8
- `asset_rights_review.csv`: 25
- `approved_graphics_assets.csv`: 33
- `launch_integration_points.csv`: 4
- `asset_source_seed_list.csv`: 28
- `fact_warning_queue.csv`: 0
- `player_image_requirements.csv`: 8
- `player_image_candidates.csv`: 48
- `graphics_qa_results.csv`: 4
- `graphics_chat_upload_manifest.csv`: 35
- `graphics_upload_pack_status.csv`: 4

## Player image sourcing

# HSD Player Image Sourcing Report

Generated: 2026-06-09T03:29:14.265754+00:00
Version: hsd-player-image-assets-v1.5-free-sourcing

Player images required: Yes
Required player rows: 8
Found required player images: 8
Missing required player images: 0
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 48

## Required players

- found_downloaded_200 | Jessica Shepard | Dallas Wings | data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg | wikidata_p18
- found_downloaded_200 | Arike Ogunbowale | Dallas Wings | data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg | duckduckgo_images_free
- found_downloaded_200 | Paige Bueckers | Dallas Wings | data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg | wikidata_p18

## Graphics chat upload pack

- bundles: 4
- asset rows: 35
- files created: 35
- png preferred created: 35
- upload packs ready: 4
- upload packs blocked: 0

## Missing optional files



## asset_desk_manifest.json

```json
{
  "version": "hsd-asset-desk-v1.2.2",
  "generated_at_utc": "2026-06-09T03:11:07.610249+00:00",
  "rights_mode": "aggressive",
  "download": true,
  "inputs": {
    "bundle_queue": "studio_bundle_queue.csv",
    "bundle_packets": "studio_bundle_packets.md",
    "launch_graphics_brief": "launch_graphics_chat_brief.md"
  },
  "counts": {
    "bundles": 4,
    "teams_detected": 25,
    "players_detected": 3,
    "asset_candidates": 25,
    "approved_assets": 25,
    "integration_rows": 4,
    "fact_warnings": 0
  },
  "guardrails": [
    "No WNBA fallback player images are approved.",
    "No generic VNL nav logos are approved as team logos.",
    "No random Wikimedia logo search results are approved.",
    "No PDF/app icon/background/logo-nav assets are approved.",
    "Stat abbreviations are filtered out before entity creation.",
    "If exact asset cannot be verified, output remains text-forward.",
    "Player-team mismatches are written to fact_warning_queue.csv."
  ]
}
```

## asset_candidates_review.md

# HSD Asset Desk v1.2 Candidate Review

Generated: 2026-06-09T03:11:07.610111+00:00

v1.2 adds exact entity cleanup, stat-token filtering, expanded WNBA logo registry, safer player-image logic, and mismatch warnings.

Teams detected: 25
Players detected: 3
Approved assets: 25
Fact warnings: 0

## Approved
- approved | Australia W | logo | https://flagcdn.com/w320/au.png
- approved | Belgium W | logo | https://flagcdn.com/w320/be.png
- approved | Brazil U20 W | logo | https://flagcdn.com/w320/br.png
- approved | Brazil W | logo | https://flagcdn.com/w320/br.png
- approved | Bulgaria W | logo | https://flagcdn.com/w320/bg.png
- approved | Canada W | logo | https://flagcdn.com/w320/ca.png
- approved | China W | logo | https://flagcdn.com/w320/cn.png
- approved | Dallas Wings | logo | https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg
- approved | France W | logo | https://flagcdn.com/w320/fr.png
- approved | Golden State Valkyries | logo | https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg
- approved | Italy W | logo | https://flagcdn.com/w320/it.png
- approved | Japan W | logo | https://flagcdn.com/w320/jp.png
- approved | Korea Republic U20 W | logo | https://flagcdn.com/w320/kr.png
- approved | Las Vegas Aces | logo | https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg
- approved | Los Angeles Sparks | logo | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- approved | Mexico W | logo | https://flagcdn.com/w320/mx.png
- approved | Minnesota Lynx | logo | https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg
- approved | Phoenix Mercury | logo | https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg
- approved | Portland Fire | logo | https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg
- approved | Seattle Storm | logo | https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg
- approved | Serbia W | logo | https://flagcdn.com/w320/rs.png
- approved | South Africa W | logo | https://flagcdn.com/w320/za.png
- approved | Thailand W | logo | https://flagcdn.com/w320/th.png
- approved | Turkey W | logo | https://flagcdn.com/w320/tr.png
- approved | USA W | logo | https://flagcdn.com/w320/us.png

## Text-forward / needs verification
- Arike Ogunbowale: no exact approved player image. Use text-forward.
- Jessica Shepard: no exact approved player image. Use text-forward.
- Paige Bueckers: no exact approved player image. Use text-forward.


## approved_graphics_assets.csv

```csv
approved_asset_id,asset_id,approved_variant,entity_type,entity_name,source_url,page_url,master_path,web_path,rights_status,approved_by,approved_utc,usage_scope,notes
appr_a954f58ba7b766,ast_a954f58ba7b766,primary_flag_v1,team,Australia W,https://flagcdn.com/w320/au.png,https://flagcdn.com/w320/au.png,data/assets/approved/appr_a954f58ba7b766.png,data/assets/approved/appr_a954f58ba7b766.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604370+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dbd34b035cd6e1,ast_dbd34b035cd6e1,primary_flag_v1,team,Belgium W,https://flagcdn.com/w320/be.png,https://flagcdn.com/w320/be.png,data/assets/approved/appr_dbd34b035cd6e1.png,data/assets/approved/appr_dbd34b035cd6e1.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604387+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_a79adaf6457f0c,ast_a79adaf6457f0c,primary_flag_v1,team,Brazil U20 W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_a79adaf6457f0c.png,data/assets/approved/appr_a79adaf6457f0c.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604391+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_3b613e56ad6ec8,ast_3b613e56ad6ec8,primary_flag_v1,team,Brazil W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_3b613e56ad6ec8.png,data/assets/approved/appr_3b613e56ad6ec8.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604394+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_6849fd04b54eb4,ast_6849fd04b54eb4,primary_flag_v1,team,Bulgaria W,https://flagcdn.com/w320/bg.png,https://flagcdn.com/w320/bg.png,data/assets/approved/appr_6849fd04b54eb4.png,data/assets/approved/appr_6849fd04b54eb4.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604396+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_14a6cc66f75be0,ast_14a6cc66f75be0,primary_flag_v1,team,Canada W,https://flagcdn.com/w320/ca.png,https://flagcdn.com/w320/ca.png,data/assets/approved/appr_14a6cc66f75be0.png,data/assets/approved/appr_14a6cc66f75be0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604398+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_885836e9869631,ast_885836e9869631,primary_flag_v1,team,China W,https://flagcdn.com/w320/cn.png,https://flagcdn.com/w320/cn.png,data/assets/approved/appr_885836e9869631.png,data/assets/approved/appr_885836e9869631.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604401+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7ca8ac2b2a4ad9,ast_7ca8ac2b2a4ad9,primary_logo_v1,team,Dallas Wings,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604414+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_65747d24fe25ad,ast_65747d24fe25ad,primary_flag_v1,team,France W,https://flagcdn.com/w320/fr.png,https://flagcdn.com/w320/fr.png,data/assets/approved/appr_65747d24fe25ad.png,data/assets/approved/appr_65747d24fe25ad.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604417+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_df24e2082f811d,ast_df24e2082f811d,primary_logo_v1,team,Golden State Valkyries,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,data/assets/approved/appr_df24e2082f811d.svg,data/assets/approved/appr_df24e2082f811d.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604420+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2a96d8d56f4ac2,ast_2a96d8d56f4ac2,primary_flag_v1,team,Italy W,https://flagcdn.com/w320/it.png,https://flagcdn.com/w320/it.png,data/assets/approved/appr_2a96d8d56f4ac2.png,data/assets/approved/appr_2a96d8d56f4ac2.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604422+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2bfc766277e6da,ast_2bfc766277e6da,primary_flag_v1,team,Japan W,https://flagcdn.com/w320/jp.png,https://flagcdn.com/w320/jp.png,data/assets/approved/appr_2bfc766277e6da.png,data/assets/approved/appr_2bfc766277e6da.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604424+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_67a033c94405f7,ast_67a033c94405f7,primary_flag_v1,team,Korea Republic U20 W,https://flagcdn.com/w320/kr.png,https://flagcdn.com/w320/kr.png,data/assets/approved/appr_67a033c94405f7.png,data/assets/approved/appr_67a033c94405f7.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604427+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9c7fc211069805,ast_9c7fc211069805,primary_logo_v1,team,Las Vegas Aces,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,data/assets/approved/appr_9c7fc211069805.svg,data/assets/approved/appr_9c7fc211069805.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604429+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7eea0085424fe3,ast_7eea0085424fe3,primary_logo_v1,team,Los Angeles Sparks,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604432+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_34556a69591b47,ast_34556a69591b47,primary_flag_v1,team,Mexico W,https://flagcdn.com/w320/mx.png,https://flagcdn.com/w320/mx.png,data/assets/approved/appr_34556a69591b47.png,data/assets/approved/appr_34556a69591b47.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604434+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_047086213c7096,ast_047086213c7096,primary_logo_v1,team,Minnesota Lynx,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604436+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9edeb1cdaa6f4c,ast_9edeb1cdaa6f4c,primary_logo_v1,team,Phoenix Mercury,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604440+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_01d68c2809f81f,ast_01d68c2809f81f,primary_logo_v1,team,Portland Fire,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604442+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_52d46724c00ec9,ast_52d46724c00ec9,primary_logo_v1,team,Seattle Storm,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,data/assets/approved/appr_52d46724c00ec9.svg,data/assets/approved/appr_52d46724c00ec9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604444+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9426bf971998ee,ast_9426bf971998ee,primary_flag_v1,team,Serbia W,https://flagcdn.com/w320/rs.png,https://flagcdn.com/w320/rs.png,data/assets/approved/appr_9426bf971998ee.png,data/assets/approved/appr_9426bf971998ee.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604447+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2d1d5b6b4b59b0,ast_2d1d5b6b4b59b0,primary_flag_v1,team,South Africa W,https://flagcdn.com/w320/za.png,https://flagcdn.com/w320/za.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604449+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_526f2acaa1d24e,ast_526f2acaa1d24e,primary_flag_v1,team,Thailand W,https://flagcdn.com/w320/th.png,https://flagcdn.com/w320/th.png,data/assets/approved/appr_526f2acaa1d24e.png,data/assets/approved/appr_526f2acaa1d24e.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604451+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dd35c3cb61c372,ast_dd35c3cb61c372,primary_flag_v1,team,Turkey W,https://flagcdn.com/w320/tr.png,https://flagcdn.com/w320/tr.png,data/assets/approved/appr_dd35c3cb61c372.png,data/assets/approved/appr_dd35c3cb61c372.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604453+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_49824984287991,ast_49824984287991,primary_flag_v1,team,USA W,https://flagcdn.com/w320/us.png,https://flagcdn.com/w320/us.png,data/assets/approved/appr_49824984287991.png,data/assets/approved/appr_49824984287991.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T03:11:07.604455+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_e229246a508b2e,ast_e229246a508b2e,primary_player_photo_v1,player,Jessica Shepard,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg,data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg,auto_approved_by_hsd_aggressive_policy,HSD free player image sourcing pipeline,2026-06-09T03:15:31.463009+00:00,HSD social graphics,Required player image sourced via wikidata_p18. Free/no-paid-API capable pipeline.
appr_90da122ca896f3,ast_90da122ca896f3,primary_player_photo_v1,player,Arike Ogunbowale,https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=,https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=,data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg,data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg,auto_approved_by_hsd_aggressive_policy,HSD free player image sourcing pipeline,2026-06-09T03:18:13.732608+00:00,HSD social graphics,Required player image sourced via duckduckgo_images_free. Free/no-paid-API capable pipeline.
appr_717263c3d3e94e,ast_717263c3d3e94e,primary_player_photo_v1,player,Paige Bueckers,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg,data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg,auto_approved_by_hsd_aggressive_policy,HSD free player image sourcing pipeline,2026-06-09T03:19:38.176830+00:00,HSD social graphics,Required player image sourced via wikidata_p18. Free/no-paid-API capable pipeline.
appr_a6b966fc2efd2d,ast_a6b966fc2efd2d,primary_player_photo_v1,player,Kelsey Plum,https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg,https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg,data/assets/player_images/kelsey-plum_wikipedia_pageimage_1be29b.jpg,data/assets/player_images/kelsey-plum_wikipedia_pageimage_1be29b.jpg,auto_approved_by_hsd_aggressive_policy,HSD free player image sourcing pipeline,2026-06-09T03:21:03.269248+00:00,HSD social graphics,Required player image sourced via wikipedia_pageimage. Free/no-paid-API capable pipeline.
appr_d3440f8552d66f,ast_d3440f8552d66f,primary_player_photo_v1,player,Ariel Atkins,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,data/assets/player_images/ariel-atkins_wikidata_p18_475bc8.jpg,data/assets/player_images/ariel-atkins_wikidata_p18_475bc8.jpg,auto_approved_by_hsd_aggressive_policy,HSD free player image sourcing pipeline,2026-06-09T03:22:28.212782+00:00,HSD social graphics,Required player image sourced via wikidata_p18. Free/no-paid-API capable pipeline.
appr_505914b839a2ec,ast_505914b839a2ec,primary_player_photo_v1,player,Dearica Hamby,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,data/assets/player_images/dearica-hamby_wikidata_p18_19f001.jpg,data/assets/player_images/dearica-hamby_wikidata_p18_19f001.jpg,auto_approved_by_hsd_aggressive_polic
...TRUNCATED...
```

## player_image_requirements.csv

```csv
bundle_slug,player_name,team_name,required,status,approved_asset_id,source_url,local_path,sourcing_method,notes
main-wnba-result,Jessica Shepard,Dallas Wings,Yes,found_downloaded_200,appr_e229246a508b2e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg,wikidata_p18,
main-wnba-result,Arike Ogunbowale,Dallas Wings,Yes,found_downloaded_200,appr_90da122ca896f3,https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=,data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg,duckduckgo_images_free,
main-wnba-result,Paige Bueckers,Dallas Wings,Yes,found_downloaded_200,appr_717263c3d3e94e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg,wikidata_p18,
main-wnba-result,Kelsey Plum,Los Angeles Sparks,Yes,found_downloaded_200,appr_a6b966fc2efd2d,https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg,data/assets/player_images/kelsey-plum_wikipedia_pageimage_1be29b.jpg,wikipedia_pageimage,
main-wnba-result,Ariel Atkins,Los Angeles Sparks,Yes,found_downloaded_200,appr_d3440f8552d66f,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,data/assets/player_images/ariel-atkins_wikidata_p18_475bc8.jpg,wikidata_p18,
main-wnba-result,Dearica Hamby,Los Angeles Sparks,Yes,found_downloaded_200,appr_505914b839a2ec,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,data/assets/player_images/dearica-hamby_wikidata_p18_19f001.jpg,wikidata_p18,
main-wnba-result,Nneka Ogwumike,Los Angeles Sparks,Yes,found_downloaded_200,appr_9a4d6394f0547e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,data/assets/player_images/nneka-ogwumike_wikidata_p18_aea79f.jpg,wikidata_p18,
main-wnba-result,Cameron Brink,Los Angeles Sparks,Yes,found_downloaded_200,appr_5665d39f6486d0,https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Cameron_Brink_Sparks_%28cropped%29.jpg/1280px-Cameron_Brink_Sparks_%28cropped%29.jpg,data/assets/player_images/cameron-brink_wikipedia_pageimage_9343dd.jpg,wikipedia_pageimage,

```

## player_image_sourcing_report.md

# HSD Player Image Sourcing Report

Generated: 2026-06-09T03:29:14.265754+00:00
Version: hsd-player-image-assets-v1.5-free-sourcing

Player images required: Yes
Required player rows: 8
Found required player images: 8
Missing required player images: 0
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 48

## Required players

- found_downloaded_200 | Jessica Shepard | Dallas Wings | data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg | wikidata_p18
- found_downloaded_200 | Arike Ogunbowale | Dallas Wings | data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg | duckduckgo_images_free
- found_downloaded_200 | Paige Bueckers | Dallas Wings | data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg | wikidata_p18
- found_downloaded_200 | Kelsey Plum | Los Angeles Sparks | data/assets/player_images/kelsey-plum_wikipedia_pageimage_1be29b.jpg | wikipedia_pageimage
- found_downloaded_200 | Ariel Atkins | Los Angeles Sparks | data/assets/player_images/ariel-atkins_wikidata_p18_475bc8.jpg | wikidata_p18
- found_downloaded_200 | Dearica Hamby | Los Angeles Sparks | data/assets/player_images/dearica-hamby_wikidata_p18_19f001.jpg | wikidata_p18
- found_downloaded_200 | Nneka Ogwumike | Los Angeles Sparks | data/assets/player_images/nneka-ogwumike_wikidata_p18_aea79f.jpg | wikidata_p18
- found_downloaded_200 | Cameron Brink | Los Angeles Sparks | data/assets/player_images/cameron-brink_wikipedia_pageimage_9343dd.jpg | wikipedia_pageimage


## player_image_candidates.csv

```csv
candidate_id,player_name,team_name,candidate_url,page_url,source_domain,title,method,score,download_status,local_path,width_px,height_px,mime_type,approved,reject_reason
pcand_6fdd96620f1e49,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629574.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_bef2bde953e036,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629491.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_b4f70a0ed3d6be,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1630386.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_49533bf166fb1a,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/201067.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_40409d3b5a58df,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643385.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_7b02d6360b662e,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643605.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_3664cc0dec2901,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/203973.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_d51692384f9fd9,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643604.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_a99f689be5140e,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642906.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_14165ad44ba196,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642897.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_e229246a508b2e,Jessica Shepard,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q63314355,commons.wikimedia.org,Jessica Shepard American basketball player,wikidata_p18,110,downloaded_200,data/assets/player_images/jessica-shepard_wikidata_p18_496bd6.jpg,1684,2902,image/jpeg,Yes,
pcand_f3f1c7d1bc2114,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1641652.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_8250f840619acf,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629481.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_c38557d0556125,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629574.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_84ed3bc41720d3,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643605.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_eeb4a8f89d034d,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/203973.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_3a697d087b3ffb,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642906.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_90da122ca896f3,Arike Ogunbowale,Dallas Wings,https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=,https://www.gettyimages.com/detail/news-photo/arike-ogunbowale-of-the-dallas-wings-poses-for-a-portrait-news-photo/2214193685,media.gettyimages.com,Arike Ogunbowale of the Dallas Wings poses for a portrait during WNBA... News Photo - Getty Images,duckduckgo_images_free,125,downloaded_200,data/assets/player_images/arike-ogunbowale_duckduckgo_images_free_db1bfc.jpg,683,1024,image/jpeg,Yes,
pcand_c6f0b63de9f919,Paige Bueckers,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/203824.png,https://wings.wnba.com/roster/,cdn.wnba.com,Paige Bueckers Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_417d225e678a78,Paige Bueckers,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642784.png,https://wings.wnba.com/roster/,cdn.wnba.com,Paige Bueckers Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_14c6749f390dbd,Paige Bueckers,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643424.png,https://wings.wnba.com/roster/,cdn.wnba.com,Paige Bueckers Dallas Wings roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_717263c3d3e94e,Paige Bueckers,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q67202319,commons.wikimedia.org,Paige Bueckers American basketball player (born 2001),wikidata_p18,125,downloaded_200,data/assets/player_images/paige-bueckers_wikidata_p18_154e0a.jpg,1642,2310,image/jpeg,Yes,
pcand_f14963816ee26d,Kelsey Plum,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628878.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Kelsey Plum Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_ed0946223bf1a8,Kelsey Plum,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628276.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Kelsey Plum Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_ae8f77e4aeec92,Kelsey Plum,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1630996.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Kelsey Plum Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_a6b966fc2efd2d,Kelsey Plum,Los Angeles Sparks,https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg,https://en.wikipedia.org/wiki/Kelsey_Plum,upload.wikimedia.org,Kelsey Plum,wikipedia_pageimage,115,downloaded_200,data/assets/player_images/kelsey-plum_wikipedia_pageimage_1be29b.jpg,1280,1883,image/jpeg,Yes,
pcand_c33cbf129608fb,Ariel Atkins,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1630148.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Ariel Atkins Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_71bfa0590102ca,Ariel Atkins,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628878.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Ariel Atkins Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_f7d4825b69ab76,Ariel Atkins,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628276.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Ariel Atkins Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_d3440f8552d66f,Ariel Atkins,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q56254723,commons.wikimedia.org,Ariel Atkins American basketball player,wikidata_p18,110,downloaded_200,data/assets/player_images/ariel-atkins_wikidata_p18_475bc8.jpg,2102,3434,image/jpeg,Yes,
pcand_aaa186ac4a56d2,Dearica Hamby,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1643461.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Dearica Hamby Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_ff6a6390f96f12,Dearica Hamby,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/204324.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Dearica Hamby Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_45d3baca1d7b06,Dearica Hamby,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1630148.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Dearica Hamby Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_505914b839a2ec,Dearica Hamby,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q20676886,commons.wikimedia.org,Dearica Hamby American basketball player,wikidata_p18,110,downloaded_200,data/assets/player_images/dearica-hamby_wikidata_p18_19f001.jpg,2521,3779,image/jpeg,Yes,
pcand_7ed9d44b619092,Nneka Ogwumike,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642287.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Nneka Ogwumike Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_52fc83d1ba0351,Nneka Ogwumike,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/203014.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Nneka Ogwumike Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)",,0,0,,No,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (read timeout=25)"
pcand_cb79787df01ce6,Nneka Ogwumike,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628242.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Nneka Ogwumike Los Angeles Sparks roster,wnba_roster_html,140,"download_error:HTTPSConnectionPool(host='cdn.wnba.com', port=443): Read timed out. (
...TRUNCATED...
```

## fact_warning_queue.csv

```csv
warning_id,bundle_id,warning_type,severity,subject,details,manual_review_required

```

## graphics_slide_blueprints.md

# HSD Graphics Slide Blueprints

Generated: 2026-06-09T03:29:14.643822+00:00

## Main WNBA Result

Decision: `ready_for_graphics_chat`

### Slide 1: Result hero with people

Layout: Two-player hero, Dallas left/cyan, Los Angeles right/magenta. Headline centered lower third. Logos small near score, not repeated in margins.

Must include:

- Dallas Wings player/person image
- Los Angeles Sparks player/person image
- Dallas Wings logo
- Los Angeles Sparks logo
- Dallas Wings 104
- Los Angeles Sparks 96
- Verified Final

Forbidden:

- fake jerseys
- fake numbers
- logo-only cover if player images are present
- empty right or left side

### Slide 2: Balanced final score board

Layout: Symmetric split scoreboard. Fill both sides equally with score slab, team label, logo, and small context strip. No extra logo floating on the left margin.

Must include:

- Dallas Wings 104
- Los Angeles Sparks 96
- winner label
- loser label
- one Dallas logo
- one Sparks logo

Forbidden:

- duplicate logo in corner or left rail
- empty side
- tiny verified final text strip
- cropped score

### Slide 3: Two-sided top performers

Layout: Two equal columns. Left column Dallas leaders. Right column Sparks leaders. Use small player photos if uploaded. Use logos only as column headers. No giant logo in the margin.

Must include:

- Dallas leaders
- Sparks leaders
- Jessica Shepard 22 PTS 15 REB 5 AST 2 STL
- Arike Ogunbowale 30 PTS 6 REB 6 AST
- Paige Bueckers 18 PTS 3 REB 14 AST 1 STL
- Kelsey Plum 27 PTS 6 AST
- Ariel Atkins 16 PTS
- Dearica Hamby 15 PTS

Forbidden:

- Wings-only performer slide
- Sparks side missing
- duplicate logo on left rail
- players assigned to wrong team

### Slide 4: CTA with filled composition

Layout: Strong CTA, but not empty. Use both logos in footer, basketball texture, score echo, and one comment prompt.

Must include:

- Your take?
- Follow Her Sports Daily
- both team logos
- HSD lockup

Forbidden:

- huge empty dark area
- logo pair only with no context
- same composition as slide 2


## studio_bundle_prompts_v2.md

# HSD Bundle Prompts v2.2

Generated: 2026-06-09T03:29:14.609275+00:00

## Main WNBA Result


### STRICT HSD SLIDE BLUEPRINT OVERRIDE

Player images required: YES
Production decision: ready_for_graphics_chat

PLAYER IMAGE STATUS: required player/person images are present in the upload pack. Use the uploaded player image files only. Do not generate or invent people.

Slide-by-slide requirements:

SLIDE 1 - Result hero with people
Layout: Two-player hero, Dallas left/cyan, Los Angeles right/magenta. Headline centered lower third. Logos small near score, not repeated in margins.
Must include: Dallas Wings player/person image; Los Angeles Sparks player/person image; Dallas Wings logo; Los Angeles Sparks logo; Dallas Wings 104; Los Angeles Sparks 96; Verified Final
Forbidden: fake jerseys; fake numbers; logo-only cover if player images are present; empty right or left side

SLIDE 2 - Balanced final score board
Layout: Symmetric split scoreboard. Fill both sides equally with score slab, team label, logo, and small context strip. No extra logo floating on the left margin.
Must include: Dallas Wings 104; Los Angeles Sparks 96; winner label; loser label; one Dallas logo; one Sparks logo
Forbidden: duplicate logo in corner or left rail; empty side; tiny verified final text strip; cropped score

SLIDE 3 - Two-sided top performers
Layout: Two equal columns. Left column Dallas leaders. Right column Sparks leaders. Use small player photos if uploaded. Use logos only as column headers. No giant logo in the margin.
Must include: Dallas leaders; Sparks leaders; Jessica Shepard 22 PTS 15 REB 5 AST 2 STL; Arike Ogunbowale 30 PTS 6 REB 6 AST; Paige Bueckers 18 PTS 3 REB 14 AST 1 STL; Kelsey Plum 27 PTS 6 AST; Ariel Atkins 16 PTS; Dearica Hamby 15 PTS
Forbidden: Wings-only performer slide; Sparks side missing; duplicate logo on left rail; players assigned to wrong team

SLIDE 4 - CTA with filled composition
Layout: Strong CTA, but not empty. Use both logos in footer, basketball texture, score echo, and one comment prompt.
Must include: Your take?; Follow Her Sports Daily; both team logos; HSD lockup
Forbidden: huge empty dark area; logo pair only with no context; same composition as slide 2

Global correction from previous output:
- Do not put a duplicate Dallas Wings logo on the left margin of the top performers slide.
- Do not create a Wings-only top performers slide. Sparks performers are required too.
- Keep slide 2 balanced so neither side feels empty.
- Use uploaded player/person images when present. No fake player bodies or fake jersey numbers.

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Main WNBA Result
Template: result_slide_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Dallas Wings beat Los Angeles Sparks. Top performers: Jessica Shepard (Dallas Wings): PTS 22, REB 15, AST 5, STL 2; Arike Ogunbowale (Dallas Wings): PTS 30, REB 6, AST 6; Paige Bueckers (Dallas Wings): PTS 18, REB 3, AST 14, STL 1.
Accuracy lock: BUNDLE LOCKED FACTS: Dallas Wings beat Los Angeles Sparks: Dallas Wings 104, Los Angeles Sparks 96. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: player_images_allowed
Critical instruction: Player photos are allowed only for approved exact player assets listed below. Never invent or substitute.

Approved exact assets:
- Dallas Wings | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg
- Los Angeles Sparks | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- Jessica Shepard | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg
- Arike Ogunbowale | primary_player_photo_v1 | https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=
- Paige Bueckers | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg
- Kelsey Plum | primary_player_photo_v1 | https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg
- Ariel Atkins | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg
- Dearica Hamby | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg
- Nneka Ogwumike | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg
- Cameron Brink | primary_player_photo_v1 | https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Cameron_Brink_Sparks_%28cropped%29.jpg/1280px-Cameron_Brink_Sparks_%28cropped%29.jpg

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

## Tonight in the W Mini-Roundup

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Tonight in the W Mini-Roundup
Template: roundup_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Tonight in the W roundup: Las Vegas Aces beat Golden State Valkyries: Las Vegas Aces 84, Golden State Valkyries 79 | Minnesota Lynx beat Seattle Storm: Minnesota Lynx 88, Seattle Storm 68 | Phoenix Mercury beat Portland Fire: Phoenix Mercury 78, Portland Fire 72
Accuracy lock: BUNDLE LOCKED FACTS: Las Vegas Aces beat Golden State Valkyries: Las Vegas Aces 84, Golden State Valkyries 79 | Minnesota Lynx beat Seattle Storm: Minnesota Lynx 88, Seattle Storm 68 | Phoenix Mercury beat Portland Fire: Phoenix Mercury 78, Portland Fire 72. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Golden State Valkyries | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg
- Las Vegas Aces | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg
- Minnesota Lynx | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg
- Phoenix Mercury | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg
- Portland Fire | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg
- Seattle Storm | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

## Volleyball Results Roundup

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Volleyball Results Roundup
Template: roundup_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Around Women’s Sports volleyball radar: USA W beat France W: USA W 3 - France W 2 | Belgium W beat Thailand W: Belgium W 3 - Thailand W 2 | Brazil W beat Bulgaria W: Brazil W 3 - Bulgaria W 0 | Canada W beat France W: Canada W 3 - France W 1 | China W beat Serbia W: China W 3 - Serbia W 0 | Italy W beat Turkey W: Italy W 3 - Turkey W 1
Accuracy lock: BUNDLE LOCKED FACTS: USA W beat France W: USA W 3 - France W 2 | Belgium W beat Thailand W: Belgium W 3 - Thailand W 2 | Brazil W beat Bulgaria W: Brazil W 3 - Bulgaria W 0 | Canada W beat France W: Canada W 3 - France W 1 | China W beat Serbia W: China W 3 - Serbia W 0 | Italy W beat Turkey W: Italy W 3 - Turkey W 1. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Belgium W | primary_flag_v1 | https://flagcdn.com/w320/be.png
- Brazil W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Bulgaria W | primary_flag_v1 | https://flagcdn.com/w320/bg.png
- Canada W | primary_flag_v1 | https://flagcdn.com/w320/ca.png
- China W | primary_flag_v1 | https://flagcdn.com/w320/cn.png
- France W | primary_flag_v1 | https://flagcdn.com/w320/fr.png
- Italy W | primary_flag_v1 | https://flagcdn.com/w320/it.png
- Serbia W | primary_flag_v1 | https://flagcdn.com/w320/rs.png
- Thailand W | primary_flag_v1 | https://flagcdn.com/w320/th.png
- Turkey W | primary_flag_v1 | https://flagcdn.com/w320/tr.png
- USA W | primary_flag_v1 | https://flagcdn.com/w320/us.png

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```

## Women's Soccer Radar

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Women's Soccer Radar
Template: radar_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Women’s soccer radar: Brazil U20 W beat Korea Republic U20 W: Brazil U20 W 3 - Korea Republic U20 W 0 | Brazil W beat USA W: Brazil W 2 - USA W 1 | Japan W beat South Africa W: Japan W 5 - South Africa W 0 | Mexico W beat Australia W: Mexico W 1 - Australia W 0
Accuracy lock: BUNDLE LOCKED FACTS: Brazil U20 W beat Korea Republic U20 W: Brazil U20 W 3 - Korea Republic U20 W 0 | Brazil W beat USA W: Brazil W 2 - USA W 1 | Japan W beat South Africa W: Japan W 5 - South Africa W 0 | Mexico W beat Australia W: Mexico W 1 - Australia W 0. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Australia W | primary_flag_v1 | https://flagcdn.com/w320/au.png
- Brazil U20 W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Brazil W | primary_flag_v1 | https://flagcdn.com/w320/br.png
- Japan W | primary_flag_v1 | https://flagcdn.com/w320/jp.png
- Korea Republic U20 W | primary_flag_v1 | https://flagcdn.com/w320/kr.png
- Mexico W | primary_flag_v1 | https://flagcdn.com/w320/mx.png
- South Africa W | primary_flag_v1 | https://flagcdn.com/w320/za.png
- USA W | primary_flag_v1 | https://flagcdn.com/w320/us.png

Fact warnings:
No fact warnings.

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
```


## graphics_chat_upload_instructions.md

# HSD Graphics Chat Upload Instructions

The graphics chat cannot reliably fetch external logo or player image URLs. Use this upload pack instead.

For the post you are making:

1. Open `graphics_chat_upload_pack/<post_slug>/`.
2. Upload `00_PROMPT_TO_PASTE.md`.
3. Upload every file in `assets_png_preferred/`, including player/person images if present.
4. If a PNG is missing, upload the matching file in `assets_original/`.
5. Tell the graphics chat: use only the attached assets, do not fetch or invent logos or player images.

Quick ZIPs are in `graphics_chat_upload_pack_zips/`.

Upload pack status is in `graphics_upload_pack_status.csv`.


## graphics_chat_upload_manifest.csv

```csv
bundle_id,post_slug,bundle_name,entity_name,entity_type,approved_asset_id,approved_variant,source_url,source_domain,local_asset_path,local_png_path,asset_filename,png_filename,download_status,conversion_status,asset_ready,required_for_bundle,upload_instruction
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Dallas Wings,team,appr_7ca8ac2b2a4ad9,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/main-wnba-result/assets_original/dallas-wings_primary-logo-v1_2a4ad9.svg,graphics_chat_upload_pack/main-wnba-result/assets_png_preferred/dallas-wings_primary-logo-v1_2a4ad9.png,dallas-wings_primary-logo-v1_2a4ad9.svg,dallas-wings_primary-logo-v1_2a4ad9.png,copied_local,converted_svg_to_png,Yes,Yes,Upload dallas-wings_primary-logo-v1_2a4ad9.png
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Los Angeles Sparks,team,appr_7eea0085424fe3,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/los-angeles-sparks_primary-logo-v1_424fe3.svg,graphics_chat_upload_pack/main-wnba-result/assets_png_preferred/los-angeles-sparks_primary-logo-v1_424fe3.png,los-angeles-sparks_primary-logo-v1_424fe3.svg,los-angeles-sparks_primary-logo-v1_424fe3.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload los-angeles-sparks_primary-logo-v1_424fe3.png
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Jessica Shepard,player,appr_e229246a508b2e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_508b2e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_508b2e.jpg,jessica-shepard_primary-player-photo-v1_508b2e.jpg,jessica-shepard_primary-player-photo-v1_508b2e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload jessica-shepard_primary-player-photo-v1_508b2e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Arike Ogunbowale,player,appr_90da122ca896f3,primary_player_photo_v1,https://media.gettyimages.com/id/2214193685/photo/2025-dallas-wings-media-day.jpg?s=1024x1024&w=gi&k=20&c=FNhvng7pUboPcxv0142yFuYDaLmjCQwH_JV7qOIRV8U=,media.gettyimages.com,graphics_chat_upload_pack/main-wnba-result/assets_original/arike-ogunbowale_primary-player-photo-v1_a896f3.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/arike-ogunbowale_primary-player-photo-v1_a896f3.jpg,arike-ogunbowale_primary-player-photo-v1_a896f3.jpg,arike-ogunbowale_primary-player-photo-v1_a896f3.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload arike-ogunbowale_primary-player-photo-v1_a896f3.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Paige Bueckers,player,appr_717263c3d3e94e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/paige-bueckers_primary-player-photo-v1_d3e94e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/paige-bueckers_primary-player-photo-v1_d3e94e.jpg,paige-bueckers_primary-player-photo-v1_d3e94e.jpg,paige-bueckers_primary-player-photo-v1_d3e94e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload paige-bueckers_primary-player-photo-v1_d3e94e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Kelsey Plum,player,appr_a6b966fc2efd2d,primary_player_photo_v1,https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Kelsey_Plum_2025_Sparks_%28cropped%29.jpg/1280px-Kelsey_Plum_2025_Sparks_%28cropped%29.jpg,upload.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/kelsey-plum_primary-player-photo-v1_2efd2d.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/kelsey-plum_primary-player-photo-v1_2efd2d.jpg,kelsey-plum_primary-player-photo-v1_2efd2d.jpg,kelsey-plum_primary-player-photo-v1_2efd2d.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload kelsey-plum_primary-player-photo-v1_2efd2d.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Ariel Atkins,player,appr_d3440f8552d66f,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/ariel-atkins_primary-player-photo-v1_52d66f.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/ariel-atkins_primary-player-photo-v1_52d66f.jpg,ariel-atkins_primary-player-photo-v1_52d66f.jpg,ariel-atkins_primary-player-photo-v1_52d66f.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload ariel-atkins_primary-player-photo-v1_52d66f.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Dearica Hamby,player,appr_505914b839a2ec,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/dearica-hamby_primary-player-photo-v1_39a2ec.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/dearica-hamby_primary-player-photo-v1_39a2ec.jpg,dearica-hamby_primary-player-photo-v1_39a2ec.jpg,dearica-hamby_primary-player-photo-v1_39a2ec.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload dearica-hamby_primary-player-photo-v1_39a2ec.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Nneka Ogwumike,player,appr_9a4d6394f0547e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload nneka-ogwumike_primary-player-photo-v1_f0547e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Cameron Brink,player,appr_5665d39f6486d0,primary_player_photo_v1,https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Cameron_Brink_Sparks_%28cropped%29.jpg/1280px-Cameron_Brink_Sparks_%28cropped%29.jpg,upload.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/cameron-brink_primary-player-photo-v1_6486d0.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/cameron-brink_primary-player-photo-v1_6486d0.jpg,cameron-brink_primary-player-photo-v1_6486d0.jpg,cameron-brink_primary-player-photo-v1_6486d0.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload cameron-brink_primary-player-photo-v1_6486d0.jpg
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Golden State Valkyries,team,appr_df24e2082f811d,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/golden-state-valkyries_primary-logo-v1_2f811d.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/golden-state-valkyries_primary-logo-v1_2f811d.png,golden-state-valkyries_primary-logo-v1_2f811d.svg,golden-state-valkyries_primary-logo-v1_2f811d.png,copied_local,converted_svg_to_png,Yes,Yes,Upload golden-state-valkyries_primary-logo-v1_2f811d.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Las Vegas Aces,team,appr_9c7fc211069805,primary_logo_v1,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/las-vegas-aces_primary-logo-v1_069805.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/las-vegas-aces_primary-logo-v1_069805.png,las-vegas-aces_primary-logo-v1_069805.svg,las-vegas-aces_primary-logo-v1_069805.png,copied_local,converted_svg_to_png,Yes,Yes,Upload las-vegas-aces_primary-logo-v1_069805.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Minnesota Lynx,team,appr_047086213c7096,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/minnesota-lynx_primary-logo-v1_3c7096.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/minnesota-lynx_primary-logo-v1_3c7096.png,minnesota-lynx_primary-logo-v1_3c7096.svg,minnesota-lynx_primary-logo-v1_3c7096.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload minnesota-lynx_primary-logo-v1_3c7096.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Phoenix Mercury,team,appr_9edeb1cdaa6f4c,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/phoenix-mercury_primary-logo-v1_aa6f4c.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/phoenix-mercury_primary-logo-v1_aa6f4c.png,phoenix-mercury_primary-logo-v1_aa6f4c.svg,phoenix-mercury_primary-logo-v1_aa6f4c.png,copied_local,converted_svg_to_png,Yes,Yes,Upload phoenix-mercury_primary-logo-v1_aa6f4c.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Portland Fire,team,appr_01d68c2809f81f,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/portland-fire_primary-logo-v1_09f81f.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/portland-fire_primary-logo-v1_09f81f.png,portland-fire_primary-logo-v1_09f81f.svg,portland-fire_primary-logo-v1_09f81f.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload portland-fire_primary-logo-v1_09f81f.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Seattle Storm,team,appr_52d46724c00ec9,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/seattle-storm_primary-logo-v1_c00ec9.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/seattle-storm_primary-logo-v1_c00ec9.png,seattle-storm_primary-logo-v1_c00ec9.svg,seattle-storm_primary-logo-v1_c00ec9.png,copied_local,converted_svg_to_png,Yes,Yes,Upload seattle-storm_primary-logo-v1_c00ec9.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Belgium W,team,appr_dbd34b035cd6e1,primary_flag_v1,https://flagcdn.com/w320/be.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/belgium-w_primary-flag-v1_5cd6e1.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/belgium-w_primary-flag-v1_5cd6e1.png,belgium-w_primary-flag-v1_5cd6e1.png,belgium-w_primary-flag-v1_5cd6e1.png,copied_local,already_png,Yes,Yes,Upload belgium-w_primary-flag-v1_5cd6e1.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Brazil W,team,appr_3b613e56ad6ec8,primary_flag_v1,https://flagcdn.com/w320/br.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/brazil-w_primary-flag-v1_ad6ec8.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/brazil-w_primary-flag-v1_ad6ec8.png,brazil-w_primary-flag-v1_ad6ec8.png,brazil-w_primary-flag-v1_ad6ec8.png,copied_local,already_png,Yes,Yes,Upload brazil-w_primary-flag-v1_ad6ec8.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Bulgaria W,team,appr_6849fd04b54eb4,primary_flag_v1,https://flagcdn.com/w320/bg.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/bulgaria-w_primary-flag-v1_b54eb4.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/bulgaria-w_primary-flag-v1_b54eb4.png,bulgaria-w_primary-flag-v1_b54eb4.png,bulgaria-w_primary-flag-v1_b54eb4.png,copied_local,already_png,Yes,Yes,Upload bulgaria-w_primary-flag-v1_b54eb4.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Canada W,team,appr_14a6cc66f75be0,primary_flag_v1,https://flagcdn.com/w320/ca.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/canada-w_primary-flag-v1_f75be0.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/canada-w_primary-flag-v1_f75be0.png,canada-w_primary-flag-v1_f75be0.png,canada-w_primary-flag-v1_f75be0.png,copied_local,already_png,Yes,Yes,Upload canada-w_primary-flag-v1_f75be0.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,China W,team,appr_885836e9869631,primary_flag_v1,https://flagcdn.com/w320/cn.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/china-w_primary-flag-v1_869631.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/china-w_primary-flag-v1_869631.png,china-w_primary-flag-v1_869631.png,china-w_primary-flag-v1_869631.png,copied_local,already_png,Yes,Yes,Upload china-w_primary-flag-v1_869631.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,France W,team,appr_65747d24fe25ad,primary_flag_v1,https://flagcdn.com/w320/fr.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/france-w_primary-flag-v1_fe25ad.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/france-w_primary-flag-v1_fe25ad.png,france-w_primary-flag-v1_fe25ad.png,france-w_primary-flag-v1_fe25ad.png,copied_local,already_png,Yes,Yes,Upload france-w_primary-flag-v1_fe25ad.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Italy W,team,appr_2a96d8d56f4ac2,primary_flag_v1,https://flagcdn.com/w320/it.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/italy-w_primary-flag-v1_6f4ac2.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/italy-w_primary-flag-v1_6f4ac2.png,italy-w_primary-flag-v1_6f4ac2.png,italy-w_primary-flag-v1_6f4ac2.png,copied_local,already_png,Yes,Yes,Upload italy-w_primary-flag-v1_6f4ac2.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Serbia W,team,appr_9426bf971998ee,primary_flag_v1,https://flagcdn.com/w320/rs.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/serbia-w_primary-flag-v1_1998ee.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/serbia-w_primary-flag-v1_1998ee.png,serbia-w_primary-flag-v1_1998ee.png,serbia-w_primary-flag-v1_1998ee.png,copied_local,already_png,Yes,Yes,Upload serbia-w_primary-flag-v1_1998ee.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Thailand W,team,appr_526f2acaa1d24e,primary_flag_v1,https://flagcdn.com/w320/th.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/thailand-w_primary-flag-v1_a1d24e.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/thailand-w_primary-flag-v1_a1d24e.png,thailand-w_primary-flag-v1_a1d24e.png,thailand-w_primary-flag-v1_a1d24e.png,copied_local,already_png,Yes,Yes,Upload thailand-w_primary-flag-v1_a1d24e.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Turkey W,team,appr_dd35c3cb61c372,primary_flag_v1,https://flagcdn.com/w320/tr.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/turkey-w_primary-flag-v1_61c372.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/turkey-w_primary-flag-v1_61c372.png,turkey-w_primary-flag-v1_61c372.png,turkey-w_primary-flag-v1_61c372.png,copied_local,already_png,Yes,Yes,U
...TRUNCATED...
```

## graphics_chat_direct_handoff.md

# HSD Graphics Chat Direct Handoff

Use the ZIP below for the graphics chat. Upload the ZIP contents if the chat cannot unzip.

## Main WNBA Result

Recommended ZIP: `graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip`

Status: READY

Instructions to paste into the graphics chat:

```text
Use the uploaded prompt, uploaded logo files, and uploaded player/person image files only. Do not fetch logo URLs. Do not fetch player image URLs. Do not substitute logos or players. Do not invent player bodies, jerseys, or numbers. Output separate slide files.
```


## graphics_upload_pack_status.csv

```csv
bundle_id,post_slug,bundle_name,upload_pack_status,assets_expected,assets_ready,assets_missing,missing_asset_names,zip_path,notes
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,ready,10,10,0,,graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip,Upload pack is complete.
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,ready,6,6,0,,graphics_chat_upload_pack_zips/tonight-in-the-w-mini-roundup_graphics_chat_upload_pack.zip,Upload pack is complete.
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,ready,11,11,0,,graphics_chat_upload_pack_zips/volleyball-results-roundup_graphics_chat_upload_pack.zip,Upload pack is complete.
bundle_33580e1adf9d95,women-s-soccer-radar,Women's Soccer Radar,ready,8,8,0,,graphics_chat_upload_pack_zips/women-s-soccer-radar_graphics_chat_upload_pack.zip,Upload pack is complete.

```

## graphics_upload_pack_status.json

```json
{
  "version": "hsd-graphics-upload-pack-v1.5.1",
  "generated_at_utc": "2026-06-09T03:29:17.851630+00:00",
  "counts": {
    "bundles": 4,
    "asset_rows": 35,
    "files_created": 35,
    "png_preferred_created": 35,
    "upload_packs_ready": 4,
    "upload_packs_blocked": 0
  },
  "bundles": [
    {
      "bundle_id": "bundle_34740d18e445ce",
      "post_slug": "main-wnba-result",
      "bundle_name": "Main WNBA Result",
      "upload_pack_status": "ready",
      "assets_expected": 10,
      "assets_ready": 10,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip",
      "notes": "Upload pack is complete."
    },
    {
      "bundle_id": "bundle_ab66100c39c23e",
      "post_slug": "tonight-in-the-w-mini-roundup",
      "bundle_name": "Tonight in the W Mini-Roundup",
      "upload_pack_status": "ready",
      "assets_expected": 6,
      "assets_ready": 6,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/tonight-in-the-w-mini-roundup_graphics_chat_upload_pack.zip",
      "notes": "Upload pack is complete."
    },
    {
      "bundle_id": "bundle_99dc10394fd30c",
      "post_slug": "volleyball-results-roundup",
      "bundle_name": "Volleyball Results Roundup",
      "upload_pack_status": "ready",
      "assets_expected": 11,
      "assets_ready": 11,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/volleyball-results-roundup_graphics_chat_upload_pack.zip",
      "notes": "Upload pack is complete."
    },
    {
      "bundle_id": "bundle_33580e1adf9d95",
      "post_slug": "women-s-soccer-radar",
      "bundle_name": "Women's Soccer Radar",
      "upload_pack_status": "ready",
      "assets_expected": 8,
      "assets_ready": 8,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/women-s-soccer-radar_graphics_chat_upload_pack.zip",
      "notes": "Upload pack is complete."
    }
  ]
}
```

## graphics_qa_report.md

# HSD Graphics QA Scorer v1.5.1 Report

Generated: 2026-06-09T03:29:17.906725+00:00

Bundles scored: 4

## main-wnba-result

- Decision: **pass_with_review**
- Score: 95
- Issues: `[{"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`

## tonight-in-the-w-mini-roundup

- Decision: **pass_with_review**
- Score: 95
- Issues: `[{"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`

## volleyball-results-roundup

- Decision: **pass_with_review**
- Score: 95
- Issues: `[{"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`

## women-s-soccer-radar

- Decision: **pass_with_review**
- Score: 95
- Issues: `[{"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`


## visual_upgrade_manifest.json

```json
{
  "version": "hsd-studio-visual-upgrade-v2.5",
  "generated_at_utc": "2026-06-09T03:29:14.610767+00:00",
  "counts": {
    "bundles": 4,
    "approved_assets": 33,
    "fact_warnings": 0,
    "warnings_propagated_to_prompts": 0
  }
}
```

## graphics_qa_manifest.json

```json
{
  "version": "hsd-graphics-qa-scorer-v1.5.1",
  "generated_at_utc": "2026-06-09T03:29:17.906833+00:00",
  "counts": {
    "bundles_scored": 4,
    "upload_status_rows": 4
  }
}
```
