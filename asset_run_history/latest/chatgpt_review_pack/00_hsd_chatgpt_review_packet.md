# HSD ChatGPT Review Packet

Upload this single file for review. The numbered files in `chatgpt_review_pack/` are included only for deeper debugging.

## latest_asset_visual_qa_run_summary.md

# HSD Asset Visual QA v1.8.1 Run Summary

Run timestamp UTC: `2026-06-09 23:11:32 UTC`
Archive folder: `asset_run_history/2026-06-09/2311_UTC`

## Row counts

- `asset_manifest.csv`: 25
- `team_assets.csv`: 25
- `player_assets.csv`: 23
- `asset_rights_review.csv`: 25
- `approved_graphics_assets.csv`: 49
- `launch_integration_points.csv`: 4
- `asset_source_seed_list.csv`: 28
- `fact_warning_queue.csv`: 0
- `player_image_requirements.csv`: 36
- `player_image_candidates.csv`: 47
- `graphics_qa_results.csv`: 4
- `graphics_display_copy.csv`: 7
- `graphics_banned_language.csv`: 10
- `studio_freshness_gate.csv`: 4
- `studio_stale_packet_queue.csv`: 4
- `player_image_fit_gate.csv`: 36
- `rendered_slide_qa.csv`: 0
- `graphics_chat_upload_manifest.csv`: 38
- `graphics_upload_pack_status.csv`: 4

## Player image sourcing

# HSD People and Player Image Sourcing Report

Generated: 2026-06-09T23:11:20.226649+00:00
Version: hsd-player-image-assets-v1.6-all-sports-people

People/player images required: Yes
Required people rows: 36
Found required people/player images: 31
Missing required people/player images: 5
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 47

## Required people and players

- found_downloaded | main-wnba-result | Jessica Shepard | Dallas Wings | data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg | duckduckgo_images_free
- found_downloaded | main-wnba-result | Arike Ogunbowale | Dallas Wings | data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Paige Bueckers | Dallas Wings | data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg | wikidata_p18

## Graphics chat upload pack

- bundles: 4
- asset rows: 38
- files created: 37
- png preferred created: 37
- upload packs ready: 0
- upload packs blocked: 4

## Missing optional files



## asset_desk_manifest.json

```json
{
  "version": "hsd-asset-desk-v1.2.2",
  "generated_at_utc": "2026-06-09T22:58:35.922155+00:00",
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

Generated: 2026-06-09T22:58:35.922031+00:00

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
appr_a954f58ba7b766,ast_a954f58ba7b766,primary_flag_v1,team,Australia W,https://flagcdn.com/w320/au.png,https://flagcdn.com/w320/au.png,data/assets/approved/appr_a954f58ba7b766.png,data/assets/approved/appr_a954f58ba7b766.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916348+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dbd34b035cd6e1,ast_dbd34b035cd6e1,primary_flag_v1,team,Belgium W,https://flagcdn.com/w320/be.png,https://flagcdn.com/w320/be.png,data/assets/approved/appr_dbd34b035cd6e1.png,data/assets/approved/appr_dbd34b035cd6e1.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916365+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_a79adaf6457f0c,ast_a79adaf6457f0c,primary_flag_v1,team,Brazil U20 W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_a79adaf6457f0c.png,data/assets/approved/appr_a79adaf6457f0c.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916368+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_3b613e56ad6ec8,ast_3b613e56ad6ec8,primary_flag_v1,team,Brazil W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_3b613e56ad6ec8.png,data/assets/approved/appr_3b613e56ad6ec8.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916371+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_6849fd04b54eb4,ast_6849fd04b54eb4,primary_flag_v1,team,Bulgaria W,https://flagcdn.com/w320/bg.png,https://flagcdn.com/w320/bg.png,data/assets/approved/appr_6849fd04b54eb4.png,data/assets/approved/appr_6849fd04b54eb4.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916373+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_14a6cc66f75be0,ast_14a6cc66f75be0,primary_flag_v1,team,Canada W,https://flagcdn.com/w320/ca.png,https://flagcdn.com/w320/ca.png,data/assets/approved/appr_14a6cc66f75be0.png,data/assets/approved/appr_14a6cc66f75be0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916376+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_885836e9869631,ast_885836e9869631,primary_flag_v1,team,China W,https://flagcdn.com/w320/cn.png,https://flagcdn.com/w320/cn.png,data/assets/approved/appr_885836e9869631.png,data/assets/approved/appr_885836e9869631.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916378+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7ca8ac2b2a4ad9,ast_7ca8ac2b2a4ad9,primary_logo_v1,team,Dallas Wings,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916388+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_65747d24fe25ad,ast_65747d24fe25ad,primary_flag_v1,team,France W,https://flagcdn.com/w320/fr.png,https://flagcdn.com/w320/fr.png,data/assets/approved/appr_65747d24fe25ad.png,data/assets/approved/appr_65747d24fe25ad.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916391+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_df24e2082f811d,ast_df24e2082f811d,primary_logo_v1,team,Golden State Valkyries,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,data/assets/approved/appr_df24e2082f811d.svg,data/assets/approved/appr_df24e2082f811d.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916393+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2a96d8d56f4ac2,ast_2a96d8d56f4ac2,primary_flag_v1,team,Italy W,https://flagcdn.com/w320/it.png,https://flagcdn.com/w320/it.png,data/assets/approved/appr_2a96d8d56f4ac2.png,data/assets/approved/appr_2a96d8d56f4ac2.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916395+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2bfc766277e6da,ast_2bfc766277e6da,primary_flag_v1,team,Japan W,https://flagcdn.com/w320/jp.png,https://flagcdn.com/w320/jp.png,data/assets/approved/appr_2bfc766277e6da.png,data/assets/approved/appr_2bfc766277e6da.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916398+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_67a033c94405f7,ast_67a033c94405f7,primary_flag_v1,team,Korea Republic U20 W,https://flagcdn.com/w320/kr.png,https://flagcdn.com/w320/kr.png,data/assets/approved/appr_67a033c94405f7.png,data/assets/approved/appr_67a033c94405f7.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916400+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9c7fc211069805,ast_9c7fc211069805,primary_logo_v1,team,Las Vegas Aces,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,data/assets/approved/appr_9c7fc211069805.svg,data/assets/approved/appr_9c7fc211069805.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916402+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7eea0085424fe3,ast_7eea0085424fe3,primary_logo_v1,team,Los Angeles Sparks,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916404+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_34556a69591b47,ast_34556a69591b47,primary_flag_v1,team,Mexico W,https://flagcdn.com/w320/mx.png,https://flagcdn.com/w320/mx.png,data/assets/approved/appr_34556a69591b47.png,data/assets/approved/appr_34556a69591b47.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916406+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_047086213c7096,ast_047086213c7096,primary_logo_v1,team,Minnesota Lynx,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916408+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9edeb1cdaa6f4c,ast_9edeb1cdaa6f4c,primary_logo_v1,team,Phoenix Mercury,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916412+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_01d68c2809f81f,ast_01d68c2809f81f,primary_logo_v1,team,Portland Fire,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916416+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_52d46724c00ec9,ast_52d46724c00ec9,primary_logo_v1,team,Seattle Storm,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,data/assets/approved/appr_52d46724c00ec9.svg,data/assets/approved/appr_52d46724c00ec9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916418+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9426bf971998ee,ast_9426bf971998ee,primary_flag_v1,team,Serbia W,https://flagcdn.com/w320/rs.png,https://flagcdn.com/w320/rs.png,data/assets/approved/appr_9426bf971998ee.png,data/assets/approved/appr_9426bf971998ee.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916419+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2d1d5b6b4b59b0,ast_2d1d5b6b4b59b0,primary_flag_v1,team,South Africa W,https://flagcdn.com/w320/za.png,https://flagcdn.com/w320/za.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916421+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_526f2acaa1d24e,ast_526f2acaa1d24e,primary_flag_v1,team,Thailand W,https://flagcdn.com/w320/th.png,https://flagcdn.com/w320/th.png,data/assets/approved/appr_526f2acaa1d24e.png,data/assets/approved/appr_526f2acaa1d24e.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916423+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dd35c3cb61c372,ast_dd35c3cb61c372,primary_flag_v1,team,Turkey W,https://flagcdn.com/w320/tr.png,https://flagcdn.com/w320/tr.png,data/assets/approved/appr_dd35c3cb61c372.png,data/assets/approved/appr_dd35c3cb61c372.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916425+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_49824984287991,ast_49824984287991,primary_flag_v1,team,USA W,https://flagcdn.com/w320/us.png,https://flagcdn.com/w320/us.png,data/assets/approved/appr_49824984287991.png,data/assets/approved/appr_49824984287991.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T22:58:35.916427+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_02cebc205c27d1,ast_02cebc205c27d1,primary_player_photo_v1,player,Jessica Shepard,https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg,https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg,data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg,data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-09T22:59:15.438755+00:00,HSD social graphics,Required people/player image sourced via duckduckgo_images_free.
appr_2646dc354c1762,ast_2646dc354c1762,primary_player_photo_v1,player,Arike Ogunbowale,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-09T23:05:56.692836+00:00,HSD social graphics,Required people/player image sourced via wikidata_p18.
appr_717263c3d3e94e,ast_717263c3d3e94e,primary_player_photo_v1,player,Paige Bueckers,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-09T23:06:36.165002+00:00,HSD social graphics,Required people/player image sourced via wikidata_p18.
appr_d8c206f8d07cbd,ast_d8c206f8d07cbd,primary_player_photo_v1,player,Kelsey Plum,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-09T23:07:15.796703+00:00,HSD social graphics,Required people/player image sourced via wikidata_p18.
appr_d3440f8552d66f,ast_d3440f8552d66f,primary_player_photo_v1,player,Ariel Atkins,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-09T23:07:54.765967+00:00,HSD social graphics,Required people/player image sourced via wikidata_p18.
appr_505914b839a2ec,ast_505914b839a2ec,primary_player_photo_v1,player,Dearica Hamby,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28c
...TRUNCATED...
```

## player_image_requirements.csv

```csv
bundle_slug,bundle_name,sport,league,player_name,team_name,required,status,approved_asset_id,source_url,local_path,sourcing_method,notes
main-wnba-result,Main WNBA Result,basketball,WNBA,Jessica Shepard,Dallas Wings,Yes,found_downloaded,appr_02cebc205c27d1,https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg,data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg,duckduckgo_images_free,
main-wnba-result,Main WNBA Result,basketball,WNBA,Arike Ogunbowale,Dallas Wings,Yes,found_downloaded,appr_2646dc354c1762,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Paige Bueckers,Dallas Wings,Yes,found_downloaded,appr_717263c3d3e94e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Kelsey Plum,Los Angeles Sparks,Yes,found_downloaded,appr_d8c206f8d07cbd,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Ariel Atkins,Los Angeles Sparks,Yes,found_downloaded,appr_d3440f8552d66f,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Dearica Hamby,Los Angeles Sparks,Yes,found_downloaded,appr_505914b839a2ec,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,data/assets/player_images/dearica-hamby_img_380e300619f001.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Nneka Ogwumike,Los Angeles Sparks,Yes,found_downloaded,appr_9a4d6394f0547e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg,wikidata_p18,
main-wnba-result,Main WNBA Result,basketball,WNBA,Cameron Brink,Los Angeles Sparks,Yes,found_downloaded,appr_26395171db11b9,https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg,data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,HSD Bundle Prompts,,Yes,missing,,,,,"Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."
general-bundle,General Bundle,basketball,WNBA,PLAYER IMAGE STATUS,,Yes,found_downloaded,appr_97c6c2747ba7de,https://upload.wikimedia.org/wikipedia/commons/8/80/1923-24_UNC_Tar_Heels_Basketball_Player_E.jpg,data/assets/player_images/player-image-status_img_1b6be7736a707e.jpg,commons_api,
general-bundle,General Bundle,basketball,WNBA,One Dallas,,Yes,found_downloaded,appr_31c010fb6e1321,https://commons.wikimedia.org/wiki/Special:Redirect/file/PatriotTower01.jpg,data/assets/player_images/one-dallas_img_e99c44e20bacb2.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,One Sparks,,Yes,found_downloaded,appr_c53adf657a1ff5,https://upload.wikimedia.org/wikipedia/commons/b/ba/Sparks_Basketball_Team%2C_1921%2C_Saint_Louis_College%2C_sec9_no1641_0001%2C_from_Brother_Bertram_Photograph_Collection.jpg,data/assets/player_images/one-sparks_img_e88690d731f255.jpg,commons_api,
general-bundle,General Bundle,basketball,WNBA,Los Angeles,,Yes,found_downloaded,appr_315287c0f37435,https://commons.wikimedia.org/wiki/Special:Redirect/file/Los%20Angeles%20with%20Mount%20Baldy.jpg,data/assets/player_images/los-angeles_img_06725f01a7c25f.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Verified Final,,Yes,missing,,,,,"Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."
general-bundle,General Bundle,basketball,WNBA,Use Dallas,,Yes,found_downloaded,appr_46c4bc5989b05f,https://upload.wikimedia.org/wikipedia/commons/f/f6/Dallas_vs._UT_Arlington_men%27s_wheelchair_basketball_2020_01_%28Dallas_warming_up%29.jpg,data/assets/player_images/use-dallas_img_e1ae9fad28f664.jpg,commons_api,
general-bundle,General Bundle,basketball,WNBA,Jessica Shepard,Dallas Wings,Yes,found_downloaded,appr_e229246a508b2e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,data/assets/player_images/jessica-shepard_img_1720d64e496bd6.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Arike Ogunbowale,Dallas Wings,Yes,found_downloaded,appr_2646dc354c1762,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Paige Bueckers,Dallas Wings,Yes,found_downloaded,appr_717263c3d3e94e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Kelsey Plum,Los Angeles Sparks,Yes,found_downloaded,appr_d8c206f8d07cbd,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Ariel Atkins,Los Angeles Sparks,Yes,found_downloaded,appr_d3440f8552d66f,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Dearica Hamby,Los Angeles Sparks,Yes,found_downloaded,appr_505914b839a2ec,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,data/assets/player_images/dearica-hamby_img_380e300619f001.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Los Angeles Sparks.,,Yes,found_downloaded,appr_14945fd31a3a9d,https://upload.wikimedia.org/wikipedia/commons/c/c2/The_Minnesota_Lynx_huddle_during_the_second_half_of_the_game_against_the_Los_Angeles_Sparks.jpg,data/assets/player_images/los-angeles-sparks_img_1eefc8b53a66d0.jpg,commons_api,
general-bundle,General Bundle,basketball,WNBA,Nneka Ogwumike,Los Angeles Sparks,Yes,found_downloaded,appr_9a4d6394f0547e,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Cameron Brink,Los Angeles Sparks,Yes,found_downloaded,appr_26395171db11b9,https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg,data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,BUNDLE LOCKED FACTS,,Yes,missing,,,,,"Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."
general-bundle,General Bundle,basketball,WNBA,Graphics Chat Starter,,Yes,missing,,,,,"Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."
general-bundle,General Bundle,basketball,WNBA,HER SPORTS DAILY,,Yes,missing,,,,,"Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."
general-bundle,General Bundle,basketball,WNBA,A'ja Wilson,,Yes,found_downloaded,appr_2d9a5cdffd79d7,https://commons.wikimedia.org/wiki/Special:Redirect/file/A%27ja%20Wilson.jpg,data/assets/player_images/a-ja-wilson_img_bc9d5ea0730f15.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Gabby Williams,,Yes,found_downloaded,appr_f99707780fd466,https://commons.wikimedia.org/wiki/Special:Redirect/file/Gabby%20Williams%205%20Fenerbah%C3%A7e%20WB%20EuroLeague%20Women%2020250108%20%281%29.jpg,data/assets/player_images/gabby-williams_img_76997e5fc820a2.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Jackie Young,,Yes,found_downloaded,appr_08c59b4ecde0c1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jackie%20Young.jpg,data/assets/player_images/jackie-young_img_6028f5e4a8042a.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Natasha Howard,,Yes,found_downloaded,appr_f9ebd695d5736c,https://commons.wikimedia.org/wiki/Special:Redirect/file/Natasha%20Howard%20%28basketball%29%2000%20%C3%87BK%20Mersin%20TKBSL%2020250104%20%287%29.jpg,data/assets/player_images/natasha-howard_img_7c5aaef665f58a.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Olivia Miles,,Yes,found_downloaded,appr_37bca07ca08aa4,https://commons.wikimedia.org/wiki/Special:Redirect/file/UNC%20vs%20ND%20%28Jan%202025%29%2023%20%28cropped%29.jpg,data/assets/player_images/olivia-miles_img_a898e15f5c26b7.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Natisha Hiedeman,,Yes,found_downloaded,appr_8bd0af15e97991,https://commons.wikimedia.org/wiki/Special:Redirect/file/Natisha%20Hiedeman%20%28cropped%29.jpg,data/assets/player_images/natisha-hiedeman_img_e6ea9532b77671.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,DeWanna Bonner,,Yes,found_downloaded,appr_920597fdff68d4,https://commons.wikimedia.org/wiki/Special:Redirect/file/Bonner9-20180601.jpg,data/assets/player_images/dewanna-bonner_img_bb07e37b03eda0.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Natasha Mack,,Yes,found_downloaded,appr_00637795ef7ab5,https://commons.wikimedia.org/wiki/Special:Redirect/file/Natasha%20Mack%202024%20%28cropped%29.jpg,data/assets/player_images/natasha-mack_img_ca1cdd91efc73c.jpg,wikidata_p18,
general-bundle,General Bundle,basketball,WNBA,Monique Akoa Makani,,Yes,found_downloaded,appr_8618f797bbf877,https://commons.wikimedia.org/wiki/Special:Redirect/file/Monique%20Akoa%20Makani%20%28cropped%29.jpg,data/assets/player_images/monique-akoa-makani_img_f9995fbce7fc7a.jpg,wikidata_p18,

```

## player_image_sourcing_report.md

# HSD People and Player Image Sourcing Report

Generated: 2026-06-09T23:11:20.226649+00:00
Version: hsd-player-image-assets-v1.6-all-sports-people

People/player images required: Yes
Required people rows: 36
Found required people/player images: 31
Missing required people/player images: 5
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 47

## Required people and players

- found_downloaded | main-wnba-result | Jessica Shepard | Dallas Wings | data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg | duckduckgo_images_free
- found_downloaded | main-wnba-result | Arike Ogunbowale | Dallas Wings | data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Paige Bueckers | Dallas Wings | data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Kelsey Plum | Los Angeles Sparks | data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Ariel Atkins | Los Angeles Sparks | data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Dearica Hamby | Los Angeles Sparks | data/assets/player_images/dearica-hamby_img_380e300619f001.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Nneka Ogwumike | Los Angeles Sparks | data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg | wikidata_p18
- found_downloaded | main-wnba-result | Cameron Brink | Los Angeles Sparks | data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg | wikidata_p18
- missing | general-bundle | HSD Bundle Prompts |  | missing | 
- found_downloaded | general-bundle | PLAYER IMAGE STATUS |  | data/assets/player_images/player-image-status_img_1b6be7736a707e.jpg | commons_api
- found_downloaded | general-bundle | One Dallas |  | data/assets/player_images/one-dallas_img_e99c44e20bacb2.jpg | wikidata_p18
- found_downloaded | general-bundle | One Sparks |  | data/assets/player_images/one-sparks_img_e88690d731f255.jpg | commons_api
- found_downloaded | general-bundle | Los Angeles |  | data/assets/player_images/los-angeles_img_06725f01a7c25f.jpg | wikidata_p18
- missing | general-bundle | Verified Final |  | missing | 
- found_downloaded | general-bundle | Use Dallas |  | data/assets/player_images/use-dallas_img_e1ae9fad28f664.jpg | commons_api
- found_downloaded | general-bundle | Jessica Shepard | Dallas Wings | data/assets/player_images/jessica-shepard_img_1720d64e496bd6.jpg | wikidata_p18
- found_downloaded | general-bundle | Arike Ogunbowale | Dallas Wings | data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg | wikidata_p18
- found_downloaded | general-bundle | Paige Bueckers | Dallas Wings | data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg | wikidata_p18
- found_downloaded | general-bundle | Kelsey Plum | Los Angeles Sparks | data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg | wikidata_p18
- found_downloaded | general-bundle | Ariel Atkins | Los Angeles Sparks | data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg | wikidata_p18
- found_downloaded | general-bundle | Dearica Hamby | Los Angeles Sparks | data/assets/player_images/dearica-hamby_img_380e300619f001.jpg | wikidata_p18
- found_downloaded | general-bundle | Los Angeles Sparks. |  | data/assets/player_images/los-angeles-sparks_img_1eefc8b53a66d0.jpg | commons_api
- found_downloaded | general-bundle | Nneka Ogwumike | Los Angeles Sparks | data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg | wikidata_p18
- found_downloaded | general-bundle | Cameron Brink | Los Angeles Sparks | data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg | wikidata_p18
- missing | general-bundle | BUNDLE LOCKED FACTS |  | missing | 
- missing | general-bundle | Graphics Chat Starter |  | missing | 
- missing | general-bundle | HER SPORTS DAILY |  | missing | 
- found_downloaded | general-bundle | A'ja Wilson |  | data/assets/player_images/a-ja-wilson_img_bc9d5ea0730f15.jpg | wikidata_p18
- found_downloaded | general-bundle | Gabby Williams |  | data/assets/player_images/gabby-williams_img_76997e5fc820a2.jpg | wikidata_p18
- found_downloaded | general-bundle | Jackie Young |  | data/assets/player_images/jackie-young_img_6028f5e4a8042a.jpg | wikidata_p18
- found_downloaded | general-bundle | Natasha Howard |  | data/assets/player_images/natasha-howard_img_7c5aaef665f58a.jpg | wikidata_p18
- found_downloaded | general-bundle | Olivia Miles |  | data/assets/player_images/olivia-miles_img_a898e15f5c26b7.jpg | wikidata_p18
- found_downloaded | general-bundle | Natisha Hiedeman |  | data/assets/player_images/natisha-hiedeman_img_e6ea9532b77671.jpg | wikidata_p18
- found_downloaded | general-bundle | DeWanna Bonner |  | data/assets/player_images/dewanna-bonner_img_bb07e37b03eda0.jpg | wikidata_p18
- found_downloaded | general-bundle | Natasha Mack |  | data/assets/player_images/natasha-mack_img_ca1cdd91efc73c.jpg | wikidata_p18
- found_downloaded | general-bundle | Monique Akoa Makani |  | data/assets/player_images/monique-akoa-makani_img_f9995fbce7fc7a.jpg | wikidata_p18

## Missing image action

The no-paid-API lane tried local files, manual CSV, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images.
For any remaining misses, add a file such as `player_image_assets/paige-bueckers.png` or add `manual_player_assets.csv` with `player_name,source_url`. This works for non-WNBA athletes too.



## player_image_candidates.csv

```csv
candidate_id,player_name,team_name,candidate_url,page_url,source_domain,title,method,score,download_status,local_path,width_px,height_px,mime_type,approved,reject_reason
pcand_bef2bde953e036,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629491.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_02cebc205c27d1,Jessica Shepard,Dallas Wings,https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg,https://www.alamy.com/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-image679199325.html,c8.alamy.com,Minnesota Lynx forward Jessica Shepard (15) looks to shoot as Dallas ...,duckduckgo_images_free,120,downloaded,data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg,1300,956,image/jpeg,Yes,
pcand_8250f840619acf,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629481.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_2646dc354c1762,Arike Ogunbowale,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q51858305,commons.wikimedia.org,Arike Ogunbowale American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,1653,2361,image/jpeg,Yes,
pcand_417d225e678a78,Paige Bueckers,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642784.png,https://wings.wnba.com/roster/,cdn.wnba.com,Paige Bueckers headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_717263c3d3e94e,Paige Bueckers,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q67202319,commons.wikimedia.org,Paige Bueckers American basketball player (born 2001),wikidata_p18,130,downloaded,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,1642,2310,image/jpeg,Yes,
pcand_ed0946223bf1a8,Kelsey Plum,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628276.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Kelsey Plum headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_d8c206f8d07cbd,Kelsey Plum,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q20657581,commons.wikimedia.org,Kelsey Plum American basketball player (born 1994),wikidata_p18,115,downloaded,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,2999,2405,image/jpeg,Yes,
pcand_71bfa0590102ca,Ariel Atkins,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628878.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Ariel Atkins headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_d3440f8552d66f,Ariel Atkins,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q56254723,commons.wikimedia.org,Ariel Atkins American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,2102,3434,image/jpeg,Yes,
pcand_ff6a6390f96f12,Dearica Hamby,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/204324.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Dearica Hamby headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_505914b839a2ec,Dearica Hamby,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q20676886,commons.wikimedia.org,Dearica Hamby American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/dearica-hamby_img_380e300619f001.jpg,2521,3779,image/jpeg,Yes,
pcand_52fc83d1ba0351,Nneka Ogwumike,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/203014.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Nneka Ogwumike headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_9a4d6394f0547e,Nneka Ogwumike,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,https://www.wikidata.org/wiki/Q3342371,commons.wikimedia.org,Nneka Ogwumike American basketball player (born 1990),wikidata_p18,115,downloaded,data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg,1924,3430,image/jpeg,Yes,
pcand_81f4e7d274b33a,Cameron Brink,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642287.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Cameron Brink headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_26395171db11b9,Cameron Brink,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q108175240,commons.wikimedia.org,Cameron Brink American basketball player (born 2001),wikidata_p18,115,downloaded,data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg,970,1371,image/jpeg,Yes,
pcand_97c6c2747ba7de,PLAYER IMAGE STATUS,,https://upload.wikimedia.org/wikipedia/commons/8/80/1923-24_UNC_Tar_Heels_Basketball_Player_E.jpg,https://commons.wikimedia.org/wiki/File%3A1923-24_UNC_Tar_Heels_Basketball_Player_E.jpg,upload.wikimedia.org,File:1923-24 UNC Tar Heels Basketball Player E.jpg,commons_api,60,downloaded,data/assets/player_images/player-image-status_img_1b6be7736a707e.jpg,291,808,image/jpeg,Yes,
pcand_31c010fb6e1321,One Dallas,,https://commons.wikimedia.org/wiki/Special:Redirect/file/PatriotTower01.jpg,https://www.wikidata.org/wiki/Q14711218,commons.wikimedia.org,"One Dallas Center Skyscraper in Dallas, Texas",wikidata_p18,97,downloaded,data/assets/player_images/one-dallas_img_e99c44e20bacb2.jpg,800,600,image/jpeg,Yes,
pcand_c53adf657a1ff5,One Sparks,,https://upload.wikimedia.org/wikipedia/commons/b/ba/Sparks_Basketball_Team%2C_1921%2C_Saint_Louis_College%2C_sec9_no1641_0001%2C_from_Brother_Bertram_Photograph_Collection.jpg,https://commons.wikimedia.org/wiki/File%3ASparks_Basketball_Team%2C_1921%2C_Saint_Louis_College%2C_sec9_no1641_0001%2C_from_Brother_Bertram_Photograph_Collection.jpg,upload.wikimedia.org,"File:Sparks Basketball Team, 1921, Saint Louis College, sec9 no1641 0001, from Brother Bertram Photograph Collection.jpg",commons_api,60,downloaded,data/assets/player_images/one-sparks_img_e88690d731f255.jpg,724,576,image/jpeg,Yes,
pcand_315287c0f37435,Los Angeles,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Los%20Angeles%20with%20Mount%20Baldy.jpg,https://www.wikidata.org/wiki/Q65,commons.wikimedia.org,"Los Angeles seat of Los Angeles County, and largest city in California, United States",wikidata_p18,97,downloaded,data/assets/player_images/los-angeles_img_06725f01a7c25f.jpg,8267,3873,image/jpeg,Yes,
pcand_46c4bc5989b05f,Use Dallas,,https://upload.wikimedia.org/wikipedia/commons/f/f6/Dallas_vs._UT_Arlington_men%27s_wheelchair_basketball_2020_01_%28Dallas_warming_up%29.jpg,https://commons.wikimedia.org/wiki/File%3ADallas_vs._UT_Arlington_men%27s_wheelchair_basketball_2020_01_%28Dallas_warming_up%29.jpg,upload.wikimedia.org,File:Dallas vs. UT Arlington men's wheelchair basketball 2020 01 (Dallas warming up).jpg,commons_api,60,downloaded,data/assets/player_images/use-dallas_img_e1ae9fad28f664.jpg,6000,4000,image/jpeg,Yes,
pcand_bef2bde953e036,Jessica Shepard,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629491.png,https://wings.wnba.com/roster/,cdn.wnba.com,Jessica Shepard headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_e229246a508b2e,Jessica Shepard,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q63314355,commons.wikimedia.org,Jessica Shepard American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/jessica-shepard_img_1720d64e496bd6.jpg,1684,2902,image/jpeg,Yes,
pcand_8250f840619acf,Arike Ogunbowale,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1629481.png,https://wings.wnba.com/roster/,cdn.wnba.com,Arike Ogunbowale headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_2646dc354c1762,Arike Ogunbowale,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q51858305,commons.wikimedia.org,Arike Ogunbowale American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,1653,2361,image/jpeg,Yes,
pcand_417d225e678a78,Paige Bueckers,Dallas Wings,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642784.png,https://wings.wnba.com/roster/,cdn.wnba.com,Paige Bueckers headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_717263c3d3e94e,Paige Bueckers,Dallas Wings,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q67202319,commons.wikimedia.org,Paige Bueckers American basketball player (born 2001),wikidata_p18,130,downloaded,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,1642,2310,image/jpeg,Yes,
pcand_ed0946223bf1a8,Kelsey Plum,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628276.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Kelsey Plum headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_d8c206f8d07cbd,Kelsey Plum,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q20657581,commons.wikimedia.org,Kelsey Plum American basketball player (born 1994),wikidata_p18,115,downloaded,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,2999,2405,image/jpeg,Yes,
pcand_71bfa0590102ca,Ariel Atkins,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1628878.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Ariel Atkins headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_d3440f8552d66f,Ariel Atkins,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q56254723,commons.wikimedia.org,Ariel Atkins American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,2102,3434,image/jpeg,Yes,
pcand_ff6a6390f96f12,Dearica Hamby,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/204324.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Dearica Hamby headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_505914b839a2ec,Dearica Hamby,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q20676886,commons.wikimedia.org,Dearica Hamby American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/dearica-hamby_img_380e300619f001.jpg,2521,3779,image/jpeg,Yes,
pcand_14945fd31a3a9d,Los Angeles Sparks.,,https://upload.wikimedia.org/wikipedia/commons/c/c2/The_Minnesota_Lynx_huddle_during_the_second_half_of_the_game_against_the_Los_Angeles_Sparks.jpg,https://commons.wikimedia.org/wiki/File%3AThe_Minnesota_Lynx_huddle_during_the_second_half_of_the_game_against_the_Los_Angeles_Sparks.jpg,upload.wikimedia.org,File:The Minnesota Lynx huddle during the second half of the game against the Los Angeles Sparks.jpg,commons_api,97,downloaded,data/assets/player_images/los-angeles-sparks_img_1eefc8b53a66d0.jpg,3955,2637,image/jpeg,Yes,
pcand_52fc83d1ba0351,Nneka Ogwumike,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/203014.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Nneka Ogwumike headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_9a4d6394f0547e,Nneka Ogwumike,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,https://www.wikidata.org/wiki/Q3342371,commons.wikimedia.org,Nneka Ogwumike American basketball player (born 1990),wikidata_p18,115,downloaded,data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg,1924,3430,image/jpeg,Yes,
pcand_81f4e7d274b33a,Cameron Brink,Los Angeles Sparks,https://cdn.wnba.com/headshots/wnba/latest/260x190/1642287.png,https://sparks.wnba.com/roster/,cdn.wnba.com,Cameron Brink headshot,wnba_roster_html,134,download_error,,0,0,,No,download_error
pcand_26395171db11b9,Cameron Brink,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q108175240,commons.wikimedia.org,Cameron Brink American basketball player (born 2001),wikidata_p18,115,downloaded,data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg,970,1371,image/jpeg,Yes,
pcand_2d9a5cdffd79d7,A'ja Wilson,,https://commons.wikimedia.org/wiki/Special:Redirect/file/A%27ja%20Wilson.jpg,https://www.wikidata.org/wiki/Q21623331,commons.wikimedia.org,A'ja Wilson American basketball player (born 1996),wikidata_p18,100,downloaded,data/assets/player_images/a-ja-wilson_img_bc9d5ea0730f15.jpg,2587,2973,image/jpeg,Yes,
pcand_f99707780fd466,Gabby Williams,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Gabby%20Williams%205%20Fenerbah%C3%A7e%20WB%20EuroLeague%20Women%2020250108%20%281%29.jpg,https://www.wikidata.org/wiki/Q19867079,commons.wikimedia.org,Gabby Williams French-American basketball player (1996-),wikidata_p18,115,downloaded,data/assets/player_images/gabby-williams_img_76997e5fc820a2.jpg,7728,5152,image/jpeg,Yes,
pcand_08c59b4ecde0c1,Jackie Young,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jackie%20Young.jpg,https://www.wikidata.org/wiki/Q63101251,commons.wikimedia.org,Jackie Young American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/jackie-young_img_6028f5e4a8042a.jpg,1902,2778,image/jpeg,Yes,
pcand_f9ebd695d5736c,Natasha Howard,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Natasha%20Howard%20%28basketball%29%2000%20%C3%87BK%20Mersin%20TKBSL%2020250104%20%287%29.jpg,https://www.wikidata.org/wiki/Q16729933,commons.wikimedia.org,Natasha Howard American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/natasha-howard_img_7c5aaef665f58a.jpg,5811,5152,image/jpeg,Yes,
pcand_37bca07ca08aa4,Olivia Miles,,https://commons.wikimedia.org/wiki/Special:Redirect/file/UNC%20vs%20ND%20%28Jan%202025%29%2023%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q113641976,commons.wikimedia.org,Olivia Miles American basketball player (born 2003),wikidata_p18,115,downloaded,data/assets/player_images/olivia-miles_img_a898e15f5c26b7.jpg,2781,3315,image/jpeg,Yes,
pcand_8bd0af15e97991,Natisha Hiedeman,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Natisha%20Hiedeman%20%28cropped%29.jpg,https://www.wikidata.org/wiki/Q64875538,commons.wikimedia.org,Natisha Hiedeman American basketball player,wikidata_p18,115,downloaded,data/assets/player_images/natisha-hiedeman_img_e6ea9532b77671.jpg,1980,2601,image/jpeg,Yes,
pcand_920597fdff68d4,DeWanna Bonner,,https://commons.wikimedia.org/wiki/Special:Redirect/file/Bon
...TRUNCATED...
```

## fact_warning_queue.csv

```csv
warning_id,bundle_id,warning_type,severity,subject,details,manual_review_required

```

## graphics_slide_blueprints.md

# HSD Graphics Slide Blueprints

Generated: 2026-06-09T23:11:20.704843+00:00

## Main WNBA Result

Decision: `ready_for_graphics_chat`

### Slide 1: Result hero with both teams represented

Layout: Two-player hero, Dallas left/cyan, Sparks right/magenta. Both sides should feel visually full.

Must include:

- One Dallas player image
- One Sparks player image
- Dallas Wings logo
- Los Angeles Sparks logo
- Dallas 104
- Los Angeles 96

Forbidden:

- Verified Final
- empty side
- logos-only cover when player images are available
- fake players or fake jerseys

### Slide 2: Balanced final score board

Layout: Symmetric split scoreboard. Fill both sides equally with team name, score, and logo.

Must include:

- Final Score
- Dallas Wings 104
- Los Angeles Sparks 96
- one Dallas logo
- one Sparks logo

Forbidden:

- Winner label
- Loser label
- Verified Final strip
- empty side
- duplicate logo floating in margin

### Slide 3: Two-sided top performers

Layout: Two equal columns or stacked two-team comparison. Use Dallas players only on the Dallas side and Sparks players only on the Sparks side.

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
- duplicate giant team logo in the margin
- mixed-up player identities

### Slide 4: CTA with filled composition

Layout: Strong CTA with score echo, both logos, HSD branding, and one community prompt.

Must include:

- What stood out?
- Follow Her Sports Daily
- Dallas 104
- Los Angeles 96
- both logos

Forbidden:

- dead space
- Verified Final
- generic robotic CTA
- same composition as slide 2


## studio_bundle_prompts_v2.md

# HSD Bundle Prompts v2.2

Generated: 2026-06-09T23:11:20.670872+00:00

## Main WNBA Result


### STRICT HSD SLIDE BLUEPRINT OVERRIDE v1.7

Player images required: YES
Production decision: ready_for_graphics_chat

PROMPT SANITIZER RULES:
- Strip internal QA language before writing the final prompt.
- Never render: Verified Final, Winner, Loser, BUNDLE LOCKED FACTS, source-safe context, graphics-safe context, or Do not alter.
- Prefer display language from graphics_display_copy.csv.
- If both team performer data exists, slide 3 must include both teams.
- If approved player images exist, use them. Do not replace with invented people.

PLAYER IMAGE STATUS: required player images are present in the upload pack. Use the uploaded player image files only.

Slide-by-slide requirements:

SLIDE 1 - Result hero with both teams represented
Layout: Two-player hero, Dallas left/cyan, Sparks right/magenta. Both sides should feel visually full.
Must include: One Dallas player image; One Sparks player image; Dallas Wings logo; Los Angeles Sparks logo; Dallas 104; Los Angeles 96
Forbidden: Verified Final; empty side; logos-only cover when player images are available; fake players or fake jerseys

SLIDE 2 - Balanced final score board
Layout: Symmetric split scoreboard. Fill both sides equally with team name, score, and logo.
Must include: Final Score; Dallas Wings 104; Los Angeles Sparks 96; one Dallas logo; one Sparks logo
Forbidden: Winner label; Loser label; Verified Final strip; empty side; duplicate logo floating in margin

SLIDE 3 - Two-sided top performers
Layout: Two equal columns or stacked two-team comparison. Use Dallas players only on the Dallas side and Sparks players only on the Sparks side.
Must include: Dallas leaders; Sparks leaders; Jessica Shepard 22 PTS 15 REB 5 AST 2 STL; Arike Ogunbowale 30 PTS 6 REB 6 AST; Paige Bueckers 18 PTS 3 REB 14 AST 1 STL; Kelsey Plum 27 PTS 6 AST; Ariel Atkins 16 PTS; Dearica Hamby 15 PTS
Forbidden: Wings-only performer slide; Sparks side missing; duplicate giant team logo in the margin; mixed-up player identities

SLIDE 4 - CTA with filled composition
Layout: Strong CTA with score echo, both logos, HSD branding, and one community prompt.
Must include: What stood out?; Follow Her Sports Daily; Dallas 104; Los Angeles 96; both logos
Forbidden: dead space; Verified Final; generic robotic CTA; same composition as slide 2

Global correction rules from prior runs:
- Never render the phrase Verified Final.
- Never label teams as Winner or Loser.
- Slide 2 must feel balanced on both sides.
- Slide 3 must include Sparks performers as well as Dallas performers.
- Do not place a duplicate team logo in an unused margin just to fill space.

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Main WNBA Result
Template: result_slide_v2
Canvas: 1080x1350 carousel
Source facts: 
Event date: missing
Freshness: unknown / unknown
Caption/context: Dallas Wings beat Los Angeles Sparks. Top performers: Jessica Shepard (Dallas Wings): PTS 22, REB 15, AST 5, STL 2; Arike Ogunbowale (Dallas Wings): PTS 30, REB 6, AST 6; Paige Bueckers (Dallas Wings): PTS 18, REB 3, AST 14, STL 1.
Accuracy lock: BUNDLE LOCKED FACTS: Dallas Wings beat Los Angeles Sparks: Dallas Wings 104, Los Angeles Sparks 96. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: player_images_allowed
Critical instruction: Player photos are allowed only for approved exact player assets listed below. Never invent or substitute.

Approved exact assets:
- Dallas Wings | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg
- Los Angeles Sparks | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- Jessica Shepard | primary_player_photo_v1 | https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg
- Arike Ogunbowale | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg
- Paige Bueckers | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg
- Kelsey Plum | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg
- Ariel Atkins | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg
- Dearica Hamby | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg
- Nneka Ogwumike | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg
- Cameron Brink | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg
- Los Angeles | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Los%20Angeles%20with%20Mount%20Baldy.jpg
- Jessica Shepard | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg
- Los Angeles Sparks. | primary_player_photo_v1 | https://upload.wikimedia.org/wikipedia/commons/c/c2/The_Minnesota_Lynx_huddle_during_the_second_half_of_the_game_against_the_Los_Angeles_Sparks.jpg

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
Event date: missing
Freshness: unknown / unknown
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
Event date: missing
Freshness: unknown / unknown
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
Event date: missing
Freshness: unknown / unknown
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
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Jessica Shepard,player,appr_02cebc205c27d1,primary_player_photo_v1,https://c8.alamy.com/comp/3BD05JN/minnesota-lynx-forward-jessica-shepard-15-looks-to-shoot-as-dallas-wings-forward-myisha-hines-allen-2-back-defends-during-the-second-half-of-a-wnba-basketball-game-wednesday-may-21-2025-in-minneapolis-ap-photoabbie-parr-3BD05JN.jpg,c8.alamy.com,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_5c27d1.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_5c27d1.jpg,jessica-shepard_primary-player-photo-v1_5c27d1.jpg,jessica-shepard_primary-player-photo-v1_5c27d1.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload jessica-shepard_primary-player-photo-v1_5c27d1.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Arike Ogunbowale,player,appr_2646dc354c1762,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Arike%20Ogunbowale%2001%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/arike-ogunbowale_primary-player-photo-v1_4c1762.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/arike-ogunbowale_primary-player-photo-v1_4c1762.jpg,arike-ogunbowale_primary-player-photo-v1_4c1762.jpg,arike-ogunbowale_primary-player-photo-v1_4c1762.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload arike-ogunbowale_primary-player-photo-v1_4c1762.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Paige Bueckers,player,appr_717263c3d3e94e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Paige%20Bueckers%20Dallas%20Wings%202%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/paige-bueckers_primary-player-photo-v1_d3e94e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/paige-bueckers_primary-player-photo-v1_d3e94e.jpg,paige-bueckers_primary-player-photo-v1_d3e94e.jpg,paige-bueckers_primary-player-photo-v1_d3e94e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload paige-bueckers_primary-player-photo-v1_d3e94e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Kelsey Plum,player,appr_d8c206f8d07cbd,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Kelsey%20Plum%20Fenerbah%C3%A7e%20Women%27s%20Basketball%20vs%20BC%20Nadezhda%20Orenburg%20EuroLeague%20Women%2020171011%20%282%29%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/kelsey-plum_primary-player-photo-v1_d07cbd.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/kelsey-plum_primary-player-photo-v1_d07cbd.jpg,kelsey-plum_primary-player-photo-v1_d07cbd.jpg,kelsey-plum_primary-player-photo-v1_d07cbd.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload kelsey-plum_primary-player-photo-v1_d07cbd.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Ariel Atkins,player,appr_d3440f8552d66f,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ariel%20Atkins%203%20Fenerbah%C3%A7e%20WB%2020241002%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/ariel-atkins_primary-player-photo-v1_52d66f.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/ariel-atkins_primary-player-photo-v1_52d66f.jpg,ariel-atkins_primary-player-photo-v1_52d66f.jpg,ariel-atkins_primary-player-photo-v1_52d66f.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload ariel-atkins_primary-player-photo-v1_52d66f.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Dearica Hamby,player,appr_505914b839a2ec,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Dearica%20Hamby%202024%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/dearica-hamby_primary-player-photo-v1_39a2ec.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/dearica-hamby_primary-player-photo-v1_39a2ec.jpg,dearica-hamby_primary-player-photo-v1_39a2ec.jpg,dearica-hamby_primary-player-photo-v1_39a2ec.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload dearica-hamby_primary-player-photo-v1_39a2ec.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Nneka Ogwumike,player,appr_9a4d6394f0547e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ogwumike%2020161011.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,nneka-ogwumike_primary-player-photo-v1_f0547e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload nneka-ogwumike_primary-player-photo-v1_f0547e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Cameron Brink,player,appr_26395171db11b9,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Cameron%20Brink%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/cameron-brink_primary-player-photo-v1_db11b9.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/cameron-brink_primary-player-photo-v1_db11b9.jpg,cameron-brink_primary-player-photo-v1_db11b9.jpg,cameron-brink_primary-player-photo-v1_db11b9.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload cameron-brink_primary-player-photo-v1_db11b9.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Los Angeles,player,appr_315287c0f37435,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Los%20Angeles%20with%20Mount%20Baldy.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/los-angeles_primary-player-photo-v1_f37435.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/los-angeles_primary-player-photo-v1_f37435.jpg,los-angeles_primary-player-photo-v1_f37435.jpg,los-angeles_primary-player-photo-v1_f37435.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload los-angeles_primary-player-photo-v1_f37435.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Jessica Shepard,player,appr_e229246a508b2e,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Jessica%20Shepard%20%28cropped%29.jpg,commons.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_508b2e.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/jessica-shepard_primary-player-photo-v1_508b2e.jpg,jessica-shepard_primary-player-photo-v1_508b2e.jpg,jessica-shepard_primary-player-photo-v1_508b2e.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload jessica-shepard_primary-player-photo-v1_508b2e.jpg
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,Los Angeles Sparks.,player,appr_14945fd31a3a9d,primary_player_photo_v1,https://upload.wikimedia.org/wikipedia/commons/c/c2/The_Minnesota_Lynx_huddle_during_the_second_half_of_the_game_against_the_Los_Angeles_Sparks.jpg,upload.wikimedia.org,graphics_chat_upload_pack/main-wnba-result/assets_original/los-angeles-sparks_primary-player-photo-v1_1a3a9d.jpg,graphics_chat_upload_pack/main-wnba-result/assets_original/los-angeles-sparks_primary-player-photo-v1_1a3a9d.jpg,los-angeles-sparks_primary-player-photo-v1_1a3a9d.jpg,los-angeles-sparks_primary-player-photo-v1_1a3a9d.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload los-angeles-sparks_primary-player-photo-v1_1a3a9d.jpg
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Golden State Valkyries,team,appr_df24e2082f811d,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/golden-state-valkyries_primary-logo-v1_2f811d.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/golden-state-valkyries_primary-logo-v1_2f811d.png,golden-state-valkyries_primary-logo-v1_2f811d.svg,golden-state-valkyries_primary-logo-v1_2f811d.png,copied_local,converted_svg_to_png,Yes,Yes,Upload golden-state-valkyries_primary-logo-v1_2f811d.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Las Vegas Aces,team,appr_9c7fc211069805,primary_logo_v1,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/las-vegas-aces_primary-logo-v1_069805.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/las-vegas-aces_primary-logo-v1_069805.png,las-vegas-aces_primary-logo-v1_069805.svg,las-vegas-aces_primary-logo-v1_069805.png,copied_local,converted_svg_to_png,Yes,Yes,Upload las-vegas-aces_primary-logo-v1_069805.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Minnesota Lynx,team,appr_047086213c7096,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/minnesota-lynx_primary-logo-v1_3c7096.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/minnesota-lynx_primary-logo-v1_3c7096.png,minnesota-lynx_primary-logo-v1_3c7096.svg,minnesota-lynx_primary-logo-v1_3c7096.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload minnesota-lynx_primary-logo-v1_3c7096.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Phoenix Mercury,team,appr_9edeb1cdaa6f4c,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/phoenix-mercury_primary-logo-v1_aa6f4c.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/phoenix-mercury_primary-logo-v1_aa6f4c.png,phoenix-mercury_primary-logo-v1_aa6f4c.svg,phoenix-mercury_primary-logo-v1_aa6f4c.png,copied_local,converted_svg_to_png,Yes,Yes,Upload phoenix-mercury_primary-logo-v1_aa6f4c.png
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Portland Fire,team,appr_01d68c2809f81f,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,upload.wikimedia.org,,,,,download_failed:https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg -> status_429; https://upload.wikimedia.org/wikipedia/en/c/cf/Portland_Fire_logo.svg -> status_429; https://en.wikipedia.org/wiki/Special:Redirect/file/Portland_Fire_logo.svg -> status_429; https://en.wikipedia.org/wiki/Special:FilePath/Portland_Fire_logo.svg -> status_429,no_local_asset,No,Yes,MISSING REQUIRED FILE: rerun upload pack or add this asset manually
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,Seattle Storm,team,appr_52d46724c00ec9,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_original/seattle-storm_primary-logo-v1_c00ec9.svg,graphics_chat_upload_pack/tonight-in-the-w-mini-roundup/assets_png_preferred/seattle-storm_primary-logo-v1_c00ec9.png,seattle-storm_primary-logo-v1_c00ec9.svg,seattle-storm_primary-logo-v1_c00ec9.png,copied_local,converted_svg_to_png,Yes,Yes,Upload seattle-storm_primary-logo-v1_c00ec9.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Belgium W,team,appr_dbd34b035cd6e1,primary_flag_v1,https://flagcdn.com/w320/be.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/belgium-w_primary-flag-v1_5cd6e1.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/belgium-w_primary-flag-v1_5cd6e1.png,belgium-w_primary-flag-v1_5cd6e1.png,belgium-w_primary-flag-v1_5cd6e1.png,copied_local,already_png,Yes,Yes,Upload belgium-w_primary-flag-v1_5cd6e1.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Brazil W,team,appr_3b613e56ad6ec8,primary_flag_v1,https://flagcdn.com/w320/br.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/brazil-w_primary-flag-v1_ad6ec8.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/brazil-w_primary-flag-v1_ad6ec8.png,brazil-w_primary-flag-v1_ad6ec8.png,brazil-w_primary-flag-v1_ad6ec8.png,copied_local,already_png,Yes,Yes,Upload brazil-w_primary-flag-v1_ad6ec8.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Bulgaria W,team,appr_6849fd04b54eb4,primary_flag_v1,https://flagcdn.com/w320/bg.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/bulgaria-w_primary-flag-v1_b54eb4.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/bulgaria-w_primary-flag-v1_b54eb4.png,bulgaria-w_primary-flag-v1_b54eb4.png,bulgaria-w_primary-flag-v1_b54eb4.png,copied_local,already_png,Yes,Yes,Upload bulgaria-w_primary-flag-v1_b54eb4.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,Canada W,team,appr_14a6cc66f75be0,primary_flag_v1,https://flagcdn.com/w320/ca.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/canada-w_primary-flag-v1_f75be0.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/canada-w_primary-flag-v1_f75be0.png,canada-w_primary-flag-v1_f75be0.png,canada-w_primary-flag-v1_f75be0.png,copied_local,already_png,Yes,Yes,Upload canada-w_primary-flag-v1_f75be0.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,China W,team,appr_885836e9869631,primary_flag_v1,https://flagcdn.com/w320/cn.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/china-w_primary-flag-v1_869631.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/china-w_primary-flag-v1_869631.png,china-w_primary-flag-v1_869631.png,china-w_primary-flag-v1_869631.png,copied_local,already_png,Yes,Yes,Upload china-w_primary-flag-v1_869631.png
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,France W,team,appr_65747d24fe25ad,primary_flag_v1,https://flagcdn.com/w320/fr.png,flagcdn.com,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/france-w_primary-flag-v1_fe25ad.png,graphics_chat_upload_pack/volleyball-results-roundup/assets_original/france-w_primary-flag-v1_fe25ad.png,france-w_primary-flag-v1_fe25ad.png
...TRUNCATED...
```

## graphics_chat_direct_handoff.md

# HSD Graphics Chat Direct Handoff

Use the ZIP below for the graphics chat. Upload the ZIP contents if the chat cannot unzip.

## Main WNBA Result

Status: BLOCKED

Missing assets: 

Do not send this pack to the graphics chat yet.


## graphics_upload_pack_status.csv

```csv
bundle_id,post_slug,bundle_name,upload_pack_status,assets_expected,assets_ready,assets_missing,missing_asset_names,zip_path,notes
bundle_34740d18e445ce,main-wnba-result,Main WNBA Result,blocked_freshness_gate,13,13,0,,graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip,Review freshness/player-image-fit gate before using this pack.
bundle_ab66100c39c23e,tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,blocked_missing_required_assets,6,5,1,Portland Fire,graphics_chat_upload_pack_zips/tonight-in-the-w-mini-roundup_graphics_chat_upload_pack.zip,Review freshness/player-image-fit gate before using this pack.
bundle_99dc10394fd30c,volleyball-results-roundup,Volleyball Results Roundup,blocked_freshness_gate,11,11,0,,graphics_chat_upload_pack_zips/volleyball-results-roundup_graphics_chat_upload_pack.zip,Review freshness/player-image-fit gate before using this pack.
bundle_33580e1adf9d95,women-s-soccer-radar,Women's Soccer Radar,blocked_freshness_gate,8,8,0,,graphics_chat_upload_pack_zips/women-s-soccer-radar_graphics_chat_upload_pack.zip,Review freshness/player-image-fit gate before using this pack.

```

## graphics_upload_pack_status.json

```json
{
  "version": "hsd-graphics-upload-pack-v1.8",
  "generated_at_utc": "2026-06-09T23:11:32.658971+00:00",
  "counts": {
    "bundles": 4,
    "asset_rows": 38,
    "files_created": 37,
    "png_preferred_created": 37,
    "upload_packs_ready": 0,
    "upload_packs_blocked": 4
  },
  "bundles": [
    {
      "bundle_id": "bundle_34740d18e445ce",
      "post_slug": "main-wnba-result",
      "bundle_name": "Main WNBA Result",
      "upload_pack_status": "blocked_freshness_gate",
      "assets_expected": 13,
      "assets_ready": 13,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/main-wnba-result_graphics_chat_upload_pack.zip",
      "notes": "Review freshness/player-image-fit gate before using this pack."
    },
    {
      "bundle_id": "bundle_ab66100c39c23e",
      "post_slug": "tonight-in-the-w-mini-roundup",
      "bundle_name": "Tonight in the W Mini-Roundup",
      "upload_pack_status": "blocked_missing_required_assets",
      "assets_expected": 6,
      "assets_ready": 5,
      "assets_missing": 1,
      "missing_asset_names": "Portland Fire",
      "zip_path": "graphics_chat_upload_pack_zips/tonight-in-the-w-mini-roundup_graphics_chat_upload_pack.zip",
      "notes": "Review freshness/player-image-fit gate before using this pack."
    },
    {
      "bundle_id": "bundle_99dc10394fd30c",
      "post_slug": "volleyball-results-roundup",
      "bundle_name": "Volleyball Results Roundup",
      "upload_pack_status": "blocked_freshness_gate",
      "assets_expected": 11,
      "assets_ready": 11,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/volleyball-results-roundup_graphics_chat_upload_pack.zip",
      "notes": "Review freshness/player-image-fit gate before using this pack."
    },
    {
      "bundle_id": "bundle_33580e1adf9d95",
      "post_slug": "women-s-soccer-radar",
      "bundle_name": "Women's Soccer Radar",
      "upload_pack_status": "blocked_freshness_gate",
      "assets_expected": 8,
      "assets_ready": 8,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/women-s-soccer-radar_graphics_chat_upload_pack.zip",
      "notes": "Review freshness/player-image-fit gate before using this pack."
    }
  ]
}
```

## graphics_qa_report.md

# HSD Graphics QA Scorer v1.8.1 Report

Generated: 2026-06-09T23:11:32.755316+00:00

Bundles scored: 4

## main-wnba-result

- Decision: **fail**
- Score: 0
- Render path: `generated_graphics/main-wnba-result.png`
- Issues: `[{"code": "MISSING_REQUIRED_PLAYER_IMAGES", "severity": "critical", "message": "HSD Bundle Prompts, Verified Final, BUNDLE LOCKED FACTS, Graphics Chat Starter, HER SPORTS DAILY"}, {"code": "UPLOAD_PACK_BLOCKED_BY_FRESHNESS", "severity": "critical", "message": "blocked_freshness_gate"}, {"code": "FRESHNESS_GATE_BLOCKED", "severity": "critical", "message": "no event date found and strict freshness gate is enabled"}, {"code": "PLAYER_IMAGE_FIT_REVIEW", "severity": "review", "message": "Use tight crop rules for: Arike Ogunbowale, Paige Bueckers, Kelsey Plum, Ariel Atkins, Dearica Hamby, Nneka Ogwumike, Cameron Brink"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`
- Remediation: Resolve flagged issues and rerun QA.

## tonight-in-the-w-mini-roundup

- Decision: **fail**
- Score: 5
- Render path: `generated_graphics/tonight-in-the-w-mini-roundup.png`
- Issues: `[{"code": "UPLOAD_PACK_INCOMPLETE", "severity": "critical", "message": "Portland Fire"}, {"code": "FRESHNESS_GATE_BLOCKED", "severity": "critical", "message": "no event date found and strict freshness gate is enabled"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`
- Remediation: Resolve flagged issues and rerun QA.

## volleyball-results-roundup

- Decision: **fail**
- Score: 5
- Render path: `generated_graphics/volleyball-results-roundup.png`
- Issues: `[{"code": "UPLOAD_PACK_BLOCKED_BY_FRESHNESS", "severity": "critical", "message": "blocked_freshness_gate"}, {"code": "FRESHNESS_GATE_BLOCKED", "severity": "critical", "message": "no event date found and strict freshness gate is enabled"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`
- Remediation: Resolve flagged issues and rerun QA.

## women-s-soccer-radar

- Decision: **fail**
- Score: 5
- Render path: `generated_graphics/women-s-soccer-radar.png`
- Issues: `[{"code": "UPLOAD_PACK_BLOCKED_BY_FRESHNESS", "severity": "critical", "message": "blocked_freshness_gate"}, {"code": "FRESHNESS_GATE_BLOCKED", "severity": "critical", "message": "no event date found and strict freshness gate is enabled"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`
- Remediation: Resolve flagged issues and rerun QA.


## graphics_copy_style_guide.md

# HSD Graphics Copy Style Guide v1.7

Generated: 2026-06-09T23:11:20.738054+00:00

## Core rule

Keep verification and accuracy-lock language **internal**. Do not render it on the graphic.

The graphic can say:

- Final
- Final Score
- Dallas gets the win
- Dallas Wings Beat Los Angeles Sparks
- What stood out?

The graphic must not say:

- Verified Final
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- do not alter

## Voice

HSD should sound like a sharp women’s sports desk, not a database export.

Use short active headlines, human sports language, clean score echoes, and confident CTAs.

Avoid robotic verification language, harsh winner/loser tags, and internal QA terms.

## Separation of concerns

- `graphics_display_copy.csv` is the **display layer**. Only this language is meant to appear on graphics.
- `graphics_banned_language.csv` is the **guardrail layer**. These terms should be stripped from prompts and final graphics.
- `graphics_asset_usage_map.csv` is the **identity layer**. Every player image has a strict one-to-one mapping.
- `graphics_layout_blueprint.csv` is the **composition layer**. It tells the graphics chat what each slide must contain.

## Main WNBA display copy

- Slide 1: Dallas Wings Beat Los Angeles Sparks | Dallas handles L.A., 104-96 | 104-96
- Slide 2: Final Score | Dallas Wings 104, Los Angeles Sparks 96 | Dallas 104 · Sparks 96
- Slide 3: Top Performers | Dallas leaders and Sparks leaders from the same game | 
- Slide 4: What stood out? | Dallas 104, Los Angeles 96 | Final: 104-96

## Asset identity rule

Every player/person image has a one-to-one mapping. The graphics chat must use each image only for the named player in `graphics_asset_usage_map.csv`.


## graphics_display_copy.csv

```csv
bundle_slug,slide_number,slide_role,display_headline,display_subhead,display_kicker,score_copy,cta_copy,do_not_render_terms,notes
main-wnba-result,1,cover_result_hero,Dallas Wings Beat Los Angeles Sparks,"Dallas handles L.A., 104-96",Final in Los Angeles,104-96,,Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,"Use one hero player from each team when available. Headline should feel editorial, not robotic."
main-wnba-result,2,balanced_scoreboard,Final Score,"Dallas Wings 104, Los Angeles Sparks 96",Dallas gets the win,Dallas 104 · Sparks 96,,Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Do not render Winner/Loser or Verified Final. Use a balanced two-sided scoreboard with both teams equally present.
main-wnba-result,3,two_team_performers,Top Performers,Dallas leaders and Sparks leaders from the same game,The box score story,,,Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,"Two equal sides. Dallas performers on one side, Sparks performers on the other. No one-team-only layout."
main-wnba-result,4,cta_wrap,What stood out?,"Dallas 104, Los Angeles 96",Join the conversation,Final: 104-96,Follow Her Sports Daily for more women’s sports coverage.,Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Use a filled CTA slide with one prompt and both logos. Avoid empty dead space.
tonight-in-the-w-mini-roundup,1,bundle_cover,Tonight in the W Mini-Roundup,Results worth knowing.,Around women’s sports,,Follow Her Sports Daily for more women’s sports coverage.,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Avoid robotic verification language. Use natural sports-editor phrasing.
volleyball-results-roundup,1,bundle_cover,Volleyball Results Roundup,Results worth knowing.,Around women’s sports,,Follow Her Sports Daily for more women’s sports coverage.,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Avoid robotic verification language. Use natural sports-editor phrasing.
women-s-soccer-radar,1,bundle_cover,Women's Soccer Radar,Results worth knowing.,Around women’s sports,,Follow Her Sports Daily for more women’s sports coverage.,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Avoid robotic verification language. Use natural sports-editor phrasing.

```

## graphics_banned_language.csv

```csv
term,severity,replacement,reason
Verified Final,hard_ban,Final / Final Score,Keep verification internal only. Display language must sound editorial.
VERIFIED FINAL,hard_ban,Final / Final Score,Keep verification internal only. Display language must sound editorial.
Winner,soft_ban,Dallas gets the win / Dallas beats L.A.,Too generic for HSD graphics.
Loser,hard_ban,Los Angeles Sparks / Sparks fall,Harsh and uneditorial.
Your Take?,soft_ban,What stood out?,More natural CTA language.
Biggest takeaway,soft_ban,What stood out in this one?,Avoid repetitive robotic CTA copy.
BUNDLE LOCKED FACTS,hard_ban,,Internal instruction only.
source-safe context,hard_ban,,Internal instruction only.
graphics-safe context,hard_ban,,Internal instruction only.
Do not alter,hard_ban,,Internal instruction only.

```

## graphics_asset_usage_map.csv

```csv
bundle_slug,asset_role,entity_name,team_name,approved_asset_id,local_or_source_path,allowed_usage,forbidden_usage,notes
main-wnba-result,team_logo,Dallas Wings,Dallas Wings,appr_7ca8ac2b2a4ad9,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,Use only as the Dallas Wings logo.,Do not use as a player image. Do not place duplicate floating logos in unused corners or margins.,One intentional logo placement per zone only.
main-wnba-result,team_logo,Los Angeles Sparks,Los Angeles Sparks,appr_7eea0085424fe3,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,Use only as the Los Angeles Sparks logo.,Do not use as a player image. Do not place duplicate floating logos in unused corners or margins.,One intentional logo placement per zone only.
main-wnba-result,player_photo,Jessica Shepard,Dallas Wings,appr_02cebc205c27d1,data/assets/player_images/jessica-shepard_img_d10dd596201a9c.jpg,Use this image only for Jessica Shepard (Dallas Wings).,"Never use this image for any player other than Jessica Shepard. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Arike Ogunbowale,Dallas Wings,appr_2646dc354c1762,data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg,Use this image only for Arike Ogunbowale (Dallas Wings).,"Never use this image for any player other than Arike Ogunbowale. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Paige Bueckers,Dallas Wings,appr_717263c3d3e94e,data/assets/player_images/paige-bueckers_img_83ab92fe154e0a.jpg,Use this image only for Paige Bueckers (Dallas Wings).,"Never use this image for any player other than Paige Bueckers. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Kelsey Plum,Los Angeles Sparks,appr_d8c206f8d07cbd,data/assets/player_images/kelsey-plum_img_4a7054cd62f785.jpg,Use this image only for Kelsey Plum (Los Angeles Sparks).,"Never use this image for any player other than Kelsey Plum. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Ariel Atkins,Los Angeles Sparks,appr_d3440f8552d66f,data/assets/player_images/ariel-atkins_img_d142138a475bc8.jpg,Use this image only for Ariel Atkins (Los Angeles Sparks).,"Never use this image for any player other than Ariel Atkins. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Dearica Hamby,Los Angeles Sparks,appr_505914b839a2ec,data/assets/player_images/dearica-hamby_img_380e300619f001.jpg,Use this image only for Dearica Hamby (Los Angeles Sparks).,"Never use this image for any player other than Dearica Hamby. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Nneka Ogwumike,Los Angeles Sparks,appr_9a4d6394f0547e,data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg,Use this image only for Nneka Ogwumike (Los Angeles Sparks).,"Never use this image for any player other than Nneka Ogwumike. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.
main-wnba-result,player_photo,Cameron Brink,Los Angeles Sparks,appr_26395171db11b9,data/assets/player_images/cameron-brink_img_1eebb8b3461051.jpg,Use this image only for Cameron Brink (Los Angeles Sparks).,"Never use this image for any player other than Cameron Brink. Never swap with another player. If unsure, omit the photo rather than substituting.",Player-to-file mapping is strict.

```

## graphics_language_manifest.json

```json
{
  "version": "hsd-graphics-language-pack-v1.7.2",
  "generated_at_utc": "2026-06-09T23:11:20.738175+00:00",
  "outputs": [
    "graphics_copy_style_guide.md",
    "graphics_display_copy.csv",
    "graphics_banned_language.csv",
    "graphics_asset_usage_map.csv",
    "graphics_layout_blueprint.csv"
  ],
  "counts": {
    "display_copy_rows": 7,
    "banned_language_rows": 10,
    "asset_usage_rows": 10,
    "layout_blueprint_rows": 4
  }
}
```

## graphics_layout_blueprint.csv

```csv
bundle_slug,slide_number,slide_role,required_left_entity,required_right_entity,required_left_people,required_right_people,must_include_terms,must_not_include_terms,composition_rule,notes
main-wnba-result,1,cover_result_hero,Dallas Wings,Los Angeles Sparks,1,1,Dallas Wings; Los Angeles Sparks; 104; 96,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,"Balanced split cover. If player images exist, use one Dallas player and one Sparks player.",No empty side. Do not make this a logos-only cover when approved player photos are present.
main-wnba-result,2,balanced_scoreboard,Dallas Wings,Los Angeles Sparks,0,0,Final Score; Dallas Wings; Los Angeles Sparks; 104; 96,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Scores and team identity should be visually balanced left and right. Do not label teams as Winner or Loser.,Both sides must feel equally full.
main-wnba-result,3,two_team_performers,Dallas Wings,Los Angeles Sparks,2,2,Jessica Shepard; Arike Ogunbowale; Paige Bueckers; Kelsey Plum; Ariel Atkins; Dearica Hamby,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Two-column performer comparison. Left column Dallas. Right column Sparks.,No one-team-only layout. No giant duplicate margin logo.
main-wnba-result,4,cta_wrap,Dallas Wings,Los Angeles Sparks,0,0,Follow Her Sports Daily; What stood out?; 104; 96,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,CTA should feel filled and purposeful. Include both logos and a conversation prompt.,Avoid dead space and generic filler copy.

```

## graphics_prompt_sanitizer_rules.md

# HSD Graphics Prompt Sanitizer Rules v1.7

Generated: 2026-06-09T23:11:20.704977+00:00

## Purpose

This file defines the last-pass cleanup rules before a graphics-chat prompt is handed off.

## Hard-strip phrases

- Verified Final
- VERIFIED FINAL
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- Do not alter

## Replace with human display copy

- Verified Final -> Final / Final Score
- Winner -> team name or natural result line
- Loser -> opposing team name or natural result line
- Your Take? -> What stood out?
- Biggest takeaway -> What stood out in this one?

## Display copy rule

The graphics chat should render only display language, not internal QA language.


## graphics_prompt_clean_report.md

# HSD Graphics Prompt Sanitizer v1.7.2

Generated: 2026-06-09T23:11:20.843244+00:00

## Main WNBA Result

- Prompt path: `graphics_clean_prompts/main-wnba-result/00_PROMPT_TO_PASTE.md`
- Raw prompt chars: 6367
- Clean prompt chars: 14564
- Removed internal lines: 4
- Term replacements/removals: 8

## Tonight in the W Mini-Roundup

- Prompt path: `graphics_clean_prompts/tonight-in-the-w-mini-roundup/00_PROMPT_TO_PASTE.md`
- Raw prompt chars: 2459
- Clean prompt chars: 3252
- Removed internal lines: 3
- Term replacements/removals: 0

## Volleyball Results Roundup

- Prompt path: `graphics_clean_prompts/volleyball-results-roundup/00_PROMPT_TO_PASTE.md`
- Raw prompt chars: 2650
- Clean prompt chars: 3376
- Removed internal lines: 3
- Term replacements/removals: 0

## Women's Soccer Radar

- Prompt path: `graphics_clean_prompts/women-s-soccer-radar/00_PROMPT_TO_PASTE.md`
- Raw prompt chars: 2334
- Clean prompt chars: 3106
- Removed internal lines: 3
- Term replacements/removals: 0


## graphics_prompt_clean_manifest.json

```json
{
  "version": "hsd-graphics-prompt-sanitizer-v1.7.2",
  "generated_at_utc": "2026-06-09T23:11:20.851790+00:00",
  "bundle_count": 4,
  "outputs": [
    "graphics_clean_prompts",
    "graphics_prompt_clean_report.md",
    "graphics_prompt_clean_manifest.json"
  ],
  "bundles": [
    {
      "bundle_slug": "main-wnba-result",
      "bundle_name": "Main WNBA Result",
      "prompt_path": "graphics_clean_prompts/main-wnba-result/00_PROMPT_TO_PASTE.md",
      "raw_prompt_chars": 6367,
      "clean_prompt_chars": 14564,
      "removed_lines": 4,
      "replacements": 8
    },
    {
      "bundle_slug": "tonight-in-the-w-mini-roundup",
      "bundle_name": "Tonight in the W Mini-Roundup",
      "prompt_path": "graphics_clean_prompts/tonight-in-the-w-mini-roundup/00_PROMPT_TO_PASTE.md",
      "raw_prompt_chars": 2459,
      "clean_prompt_chars": 3252,
      "removed_lines": 3,
      "replacements": 0
    },
    {
      "bundle_slug": "volleyball-results-roundup",
      "bundle_name": "Volleyball Results Roundup",
      "prompt_path": "graphics_clean_prompts/volleyball-results-roundup/00_PROMPT_TO_PASTE.md",
      "raw_prompt_chars": 2650,
      "clean_prompt_chars": 3376,
      "removed_lines": 3,
      "replacements": 0
    },
    {
      "bundle_slug": "women-s-soccer-radar",
      "bundle_name": "Women's Soccer Radar",
      "prompt_path": "graphics_clean_prompts/women-s-soccer-radar/00_PROMPT_TO_PASTE.md",
      "raw_prompt_chars": 2334,
      "clean_prompt_chars": 3106,
      "removed_lines": 3,
      "replacements": 0
    }
  ]
}
```

## studio_freshness_report.md

# HSD Studio Freshness Gate v1.8

Generated: 2026-06-09T23:11:20.776564+00:00

- bundles checked: 4
- allowed: 0
- review: 0
- blocked: 4
- max fresh hours: 18.0
- strict missing event date: Yes

## Main WNBA Result

- Decision: **block**
- Status: `blocked_missing_event_date`
- Event date: `missing`
- Recommended label: Add event_date upstream or mark carryover
- Reason: no event date found and strict freshness gate is enabled

## Tonight in the W Mini-Roundup

- Decision: **block**
- Status: `blocked_missing_event_date`
- Event date: `missing`
- Recommended label: Add event_date upstream or mark carryover
- Reason: no event date found and strict freshness gate is enabled

## Volleyball Results Roundup

- Decision: **block**
- Status: `blocked_missing_event_date`
- Event date: `missing`
- Recommended label: Add event_date upstream or mark carryover
- Reason: no event date found and strict freshness gate is enabled

## Women's Soccer Radar

- Decision: **block**
- Status: `blocked_missing_event_date`
- Event date: `missing`
- Recommended label: Add event_date upstream or mark carryover
- Reason: no event date found and strict freshness gate is enabled


## studio_freshness_gate.csv

```csv
bundle_slug,bundle_name,freshness_status,freshness_decision,event_date,event_age_hours,bundle_created_at,source_run_timestamp,is_carryover,requires_relabel,recommended_label,reason,source_evidence
main-wnba-result,Main WNBA Result,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
volleyball-results-roundup,Volleyball Results Roundup,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
women-s-soccer-radar,Women's Soccer Radar,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc

```

## studio_stale_packet_queue.csv

```csv
bundle_slug,bundle_name,freshness_status,freshness_decision,event_date,event_age_hours,bundle_created_at,source_run_timestamp,is_carryover,requires_relabel,recommended_label,reason,source_evidence
main-wnba-result,Main WNBA Result,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
tonight-in-the-w-mini-roundup,Tonight in the W Mini-Roundup,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
volleyball-results-roundup,Volleyball Results Roundup,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc
women-s-soccer-radar,Women's Soccer Radar,blocked_missing_event_date,block,,,,2026-06-09T22:57:01.246669+00:00,No,No,Add event_date upstream or mark carryover,no event date found and strict freshness gate is enabled,news_sync_manifest.json:generated_at_utc

```

## player_image_fit_report.md

# HSD Player Image Fit Gate v1.8

Generated: 2026-06-09T23:11:20.810507+00:00

- checked: 36
- approved: 4
- review: 27
- blocked: 5

This gate does not prove identity by face recognition. It catches sourcing/team-context risks and gives the graphics chat crop rules to avoid wrong-team jersey exposure.

## Jessica Shepard

- Team: Dallas Wings
- Status: **approved**
- Usage mode: `normal_player_photo`
- Risk: low | none
- Crop rule: Normal crop is allowed if the image clearly matches the player and team context.

## Arike Ogunbowale

- Team: Dallas Wings
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Paige Bueckers

- Team: Dallas Wings
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Kelsey Plum

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Ariel Atkins

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Dearica Hamby

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Nneka Ogwumike

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Cameron Brink

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## HSD Bundle Prompts

- Team: 
- Status: **blocked_missing_image**
- Usage mode: `normal_player_photo`
- Risk: critical | missing required player image
- Crop rule: Do not use.

## PLAYER IMAGE STATUS

- Team: 
- Status: **approved**
- Usage mode: `normal_player_photo`
- Risk: low | none
- Crop rule: Normal crop is allowed if the image clearly matches the player and team context.

## One Dallas

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## One Sparks

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | possible non-current-team/alternate jersey source: college
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Los Angeles

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Verified Final

- Team: 
- Status: **blocked_missing_image**
- Usage mode: `normal_player_photo`
- Risk: critical | missing required player image
- Crop rule: Do not use.

## Use Dallas

- Team: 
- Status: **approved**
- Usage mode: `normal_player_photo`
- Risk: low | none
- Crop rule: Normal crop is allowed if the image clearly matches the player and team context.

## Jessica Shepard

- Team: Dallas Wings
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Arike Ogunbowale

- Team: Dallas Wings
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Paige Bueckers

- Team: Dallas Wings
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Kelsey Plum

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Ariel Atkins

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Dearica Hamby

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Los Angeles Sparks.

- Team: 
- Status: **approved**
- Usage mode: `normal_player_photo`
- Risk: low | none
- Crop rule: Normal crop is allowed if the image clearly matches the player and team context.

## Nneka Ogwumike

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Cameron Brink

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## BUNDLE LOCKED FACTS

- Team: 
- Status: **blocked_missing_image**
- Usage mode: `normal_player_photo`
- Risk: critical | missing required player image
- Crop rule: Do not use.

## Graphics Chat Starter

- Team: 
- Status: **blocked_missing_image**
- Usage mode: `normal_player_photo`
- Risk: critical | missing required player image
- Crop rule: Do not use.

## HER SPORTS DAILY

- Team: 
- Status: **blocked_missing_image**
- Usage mode: `normal_player_photo`
- Risk: critical | missing required player image
- Crop rule: Do not use.

## A'ja Wilson

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Gabby Williams

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Jackie Young

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Natasha Howard

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Olivia Miles

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Natisha Hiedeman

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## DeWanna Bonner

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Natasha Mack

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.

## Monique Akoa Makani

- Team: 
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.


## player_image_fit_gate.csv

```csv
bundle_slug,player_name,team_name,approved_asset_id,fit_status,usage_mode,risk_level,risk_reasons,recommended_crop,prompt_instruction
main-wnba-result,Jessica Shepard,Dallas Wings,appr_02cebc205c27d1,approved,normal_player_photo,low,,Normal crop is allowed if the image clearly matches the player and team context.,Use Jessica Shepard's image only for Jessica Shepard.
main-wnba-result,Arike Ogunbowale,Dallas Wings,appr_2646dc354c1762,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Arike Ogunbowale's image only for Arike Ogunbowale. Crop tightly if the jersey is not clearly Dallas Wings.
main-wnba-result,Paige Bueckers,Dallas Wings,appr_717263c3d3e94e,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Paige Bueckers's image only for Paige Bueckers. Crop tightly if the jersey is not clearly Dallas Wings.
main-wnba-result,Kelsey Plum,Los Angeles Sparks,appr_d8c206f8d07cbd,review,tight_face_crop_only,medium,possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Kelsey Plum's image only for Kelsey Plum. Crop tightly if the jersey is not clearly Los Angeles Sparks.
main-wnba-result,Ariel Atkins,Los Angeles Sparks,appr_d3440f8552d66f,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Ariel Atkins's image only for Ariel Atkins. Crop tightly if the jersey is not clearly Los Angeles Sparks.
main-wnba-result,Dearica Hamby,Los Angeles Sparks,appr_505914b839a2ec,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Dearica Hamby's image only for Dearica Hamby. Crop tightly if the jersey is not clearly Los Angeles Sparks.
main-wnba-result,Nneka Ogwumike,Los Angeles Sparks,appr_9a4d6394f0547e,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Nneka Ogwumike's image only for Nneka Ogwumike. Crop tightly if the jersey is not clearly Los Angeles Sparks.
main-wnba-result,Cameron Brink,Los Angeles Sparks,appr_26395171db11b9,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Cameron Brink's image only for Cameron Brink. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,HSD Bundle Prompts,,,blocked_missing_image,normal_player_photo,critical,missing required player image,Do not use.,Missing approved image for HSD Bundle Prompts. Do not substitute another player.
general-bundle,PLAYER IMAGE STATUS,,appr_97c6c2747ba7de,approved,normal_player_photo,low,,Normal crop is allowed if the image clearly matches the player and team context.,Use PLAYER IMAGE STATUS's image only for PLAYER IMAGE STATUS.
general-bundle,One Dallas,,appr_31c010fb6e1321,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use One Dallas's image only for One Dallas. Crop tightly if the jersey is not clearly .
general-bundle,One Sparks,,appr_c53adf657a1ff5,review,tight_face_crop_only,medium,possible non-current-team/alternate jersey source: college,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use One Sparks's image only for One Sparks. Crop tightly if the jersey is not clearly .
general-bundle,Los Angeles,,appr_315287c0f37435,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Los Angeles's image only for Los Angeles. Crop tightly if the jersey is not clearly .
general-bundle,Verified Final,,,blocked_missing_image,normal_player_photo,critical,missing required player image,Do not use.,Missing approved image for Verified Final. Do not substitute another player.
general-bundle,Use Dallas,,appr_46c4bc5989b05f,approved,normal_player_photo,low,,Normal crop is allowed if the image clearly matches the player and team context.,Use Use Dallas's image only for Use Dallas.
general-bundle,Jessica Shepard,Dallas Wings,appr_e229246a508b2e,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Jessica Shepard's image only for Jessica Shepard. Crop tightly if the jersey is not clearly Dallas Wings.
general-bundle,Arike Ogunbowale,Dallas Wings,appr_2646dc354c1762,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Arike Ogunbowale's image only for Arike Ogunbowale. Crop tightly if the jersey is not clearly Dallas Wings.
general-bundle,Paige Bueckers,Dallas Wings,appr_717263c3d3e94e,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Paige Bueckers's image only for Paige Bueckers. Crop tightly if the jersey is not clearly Dallas Wings.
general-bundle,Kelsey Plum,Los Angeles Sparks,appr_d8c206f8d07cbd,review,tight_face_crop_only,medium,possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Kelsey Plum's image only for Kelsey Plum. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,Ariel Atkins,Los Angeles Sparks,appr_d3440f8552d66f,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Ariel Atkins's image only for Ariel Atkins. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,Dearica Hamby,Los Angeles Sparks,appr_505914b839a2ec,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Dearica Hamby's image only for Dearica Hamby. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,Los Angeles Sparks.,,appr_14945fd31a3a9d,approved,normal_player_photo,low,,Normal crop is allowed if the image clearly matches the player and team context.,Use Los Angeles Sparks.'s image only for Los Angeles Sparks..
general-bundle,Nneka Ogwumike,Los Angeles Sparks,appr_9a4d6394f0547e,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Nneka Ogwumike's image only for Nneka Ogwumike. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,Cameron Brink,Los Angeles Sparks,appr_26395171db11b9,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Cameron Brink's image only for Cameron Brink. Crop tightly if the jersey is not clearly Los Angeles Sparks.
general-bundle,BUNDLE LOCKED FACTS,,,blocked_missing_image,normal_player_photo,critical,missing required player image,Do not use.,Missing approved image for BUNDLE LOCKED FACTS. Do not substitute another player.
general-bundle,Graphics Chat Starter,,,blocked_missing_image,normal_player_photo,critical,missing required player image,Do not use.,Missing approved image for Graphics Chat Starter. Do not substitute another player.
general-bundle,HER SPORTS DAILY,,,blocked_missing_image,normal_player_photo,critical,missing required player image,Do not use.,Missing approved image for HER SPORTS DAILY. Do not substitute another player.
general-bundle,A'ja Wilson,,appr_2d9a5cdffd79d7,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use A'ja Wilson's image only for A'ja Wilson. Crop tightly if the jersey is not clearly .
general-bundle,Gabby Williams,,appr_f99707780fd466,review,tight_face_crop_only,medium,possible non-current-team/alternate jersey source: euroleague; public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Gabby Williams's image only for Gabby Williams. Crop tightly if the jersey is not clearly .
general-bundle,Jackie Young,,appr_08c59b4ecde0c1,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Jackie Young's image only for Jackie Young. Crop tightly if the jersey is not clearly .
general-bundle,Natasha Howard,,appr_f9ebd695d5736c,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Natasha Howard's image only for Natasha Howard. Crop tightly if the jersey is not clearly .
general-bundle,Olivia Miles,,appr_37bca07ca08aa4,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Olivia Miles's image only for Olivia Miles. Crop tightly if the jersey is not clearly .
general-bundle,Natisha Hiedeman,,appr_8bd0af15e97991,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Natisha Hiedeman's image only for Natisha Hiedeman. Crop tightly if the jersey is not clearly .
general-bundle,DeWanna Bonner,,appr_920597fdff68d4,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use DeWanna Bonner's image only for DeWanna Bonner. Crop tightly if the jersey is not clearly .
general-bundle,Natasha Mack,,appr_00637795ef7ab5,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Natasha Mack's image only for Natasha Mack. Crop tightly if the jersey is not clearly .
general-bundle,Monique Akoa Makani,,appr_8618f797bbf877,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Monique Akoa Makani's image only for Monique Akoa Makani. Crop tightly if the jersey is not clearly .

```

## rendered_slide_qa_report.md

# HSD Rendered Slide QA v1.8

Generated: 2026-06-09T23:11:32.818359+00:00

- rendered image files found: 0
- pass: 0
- review: 0
- fail: 0

No rendered slide files were found.

To use this gate, upload finished images into `rendered_graphics_input/` in the repo and rerun Asset Visual QA.


## rendered_slide_qa.csv

```csv
file_path,slide_number,width,height,dimension_status,ocr_status,banned_language_hits,expected_copy_status,score_status,qa_decision,issues

```

## visual_upgrade_manifest.json

```json
{
  "version": "hsd-studio-visual-upgrade-v2.6-event-dates",
  "generated_at_utc": "2026-06-09T23:11:20.672549+00:00",
  "counts": {
    "bundles": 4,
    "approved_assets": 49,
    "fact_warnings": 0,
    "warnings_propagated_to_prompts": 0
  }
}
```

## graphics_qa_manifest.json

```json
{
  "version": "hsd-graphics-qa-scorer-v1.8.1-event-date-bridge",
  "generated_at_utc": "2026-06-09T23:11:32.755415+00:00",
  "counts": {
    "bundles_scored": 4,
    "upload_status_rows": 4,
    "freshness_rows": 4,
    "player_fit_rows": 36
  }
}
```
