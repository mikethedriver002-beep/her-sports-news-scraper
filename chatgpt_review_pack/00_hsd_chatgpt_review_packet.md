# HSD ChatGPT Review Packet\n\nUpload this single file if you want the fastest possible review. Upload the individual files in `chatgpt_review_pack/` only if deeper debugging is needed.\n\n## latest_asset_visual_qa_run_summary.md\n\n# HSD Asset Visual QA v1.3 Run Summary

Run timestamp UTC: `2026-06-09 01:08:19 UTC`
Archive folder: `asset_run_history/2026-06-09/0108_UTC`

## Row counts

- `asset_manifest.csv`: 25
- `team_assets.csv`: 25
- `player_assets.csv`: 3
- `asset_rights_review.csv`: 25
- `approved_graphics_assets.csv`: 25
- `launch_integration_points.csv`: 4
- `asset_source_seed_list.csv`: 28
- `fact_warning_queue.csv`: 0
- `graphics_qa_results.csv`: 4
- `graphics_chat_upload_manifest.csv`: 27

## Missing optional files

\n\n## asset_desk_manifest.json\n\n```json\n{
  "version": "hsd-asset-desk-v1.2.2",
  "generated_at_utc": "2026-06-09T01:09:50.325574+00:00",
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
}\n```\n\n## asset_candidates_review.md\n\n# HSD Asset Desk v1.2 Candidate Review

Generated: 2026-06-09T01:09:50.325482+00:00

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
\n\n## approved_graphics_assets.csv\n\n```csv\napproved_asset_id,asset_id,approved_variant,entity_type,entity_name,source_url,page_url,master_path,web_path,rights_status,approved_by,approved_utc,usage_scope,notes
appr_a954f58ba7b766,ast_a954f58ba7b766,primary_flag_v1,team,Australia W,https://flagcdn.com/w320/au.png,https://flagcdn.com/w320/au.png,data/assets/approved/appr_a954f58ba7b766.png,data/assets/approved/appr_a954f58ba7b766.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319913+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dbd34b035cd6e1,ast_dbd34b035cd6e1,primary_flag_v1,team,Belgium W,https://flagcdn.com/w320/be.png,https://flagcdn.com/w320/be.png,data/assets/approved/appr_dbd34b035cd6e1.png,data/assets/approved/appr_dbd34b035cd6e1.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319933+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_a79adaf6457f0c,ast_a79adaf6457f0c,primary_flag_v1,team,Brazil U20 W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_a79adaf6457f0c.png,data/assets/approved/appr_a79adaf6457f0c.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319937+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_3b613e56ad6ec8,ast_3b613e56ad6ec8,primary_flag_v1,team,Brazil W,https://flagcdn.com/w320/br.png,https://flagcdn.com/w320/br.png,data/assets/approved/appr_3b613e56ad6ec8.png,data/assets/approved/appr_3b613e56ad6ec8.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319940+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_6849fd04b54eb4,ast_6849fd04b54eb4,primary_flag_v1,team,Bulgaria W,https://flagcdn.com/w320/bg.png,https://flagcdn.com/w320/bg.png,data/assets/approved/appr_6849fd04b54eb4.png,data/assets/approved/appr_6849fd04b54eb4.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319943+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_14a6cc66f75be0,ast_14a6cc66f75be0,primary_flag_v1,team,Canada W,https://flagcdn.com/w320/ca.png,https://flagcdn.com/w320/ca.png,data/assets/approved/appr_14a6cc66f75be0.png,data/assets/approved/appr_14a6cc66f75be0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319946+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_885836e9869631,ast_885836e9869631,primary_flag_v1,team,China W,https://flagcdn.com/w320/cn.png,https://flagcdn.com/w320/cn.png,data/assets/approved/appr_885836e9869631.png,data/assets/approved/appr_885836e9869631.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319949+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7ca8ac2b2a4ad9,ast_7ca8ac2b2a4ad9,primary_logo_v1,team,Dallas Wings,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,data/assets/approved/appr_7ca8ac2b2a4ad9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319958+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_65747d24fe25ad,ast_65747d24fe25ad,primary_flag_v1,team,France W,https://flagcdn.com/w320/fr.png,https://flagcdn.com/w320/fr.png,data/assets/approved/appr_65747d24fe25ad.png,data/assets/approved/appr_65747d24fe25ad.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319962+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_df24e2082f811d,ast_df24e2082f811d,primary_logo_v1,team,Golden State Valkyries,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg,data/assets/approved/appr_df24e2082f811d.svg,data/assets/approved/appr_df24e2082f811d.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319965+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2a96d8d56f4ac2,ast_2a96d8d56f4ac2,primary_flag_v1,team,Italy W,https://flagcdn.com/w320/it.png,https://flagcdn.com/w320/it.png,data/assets/approved/appr_2a96d8d56f4ac2.png,data/assets/approved/appr_2a96d8d56f4ac2.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319967+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2bfc766277e6da,ast_2bfc766277e6da,primary_flag_v1,team,Japan W,https://flagcdn.com/w320/jp.png,https://flagcdn.com/w320/jp.png,data/assets/approved/appr_2bfc766277e6da.png,data/assets/approved/appr_2bfc766277e6da.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319970+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_67a033c94405f7,ast_67a033c94405f7,primary_flag_v1,team,Korea Republic U20 W,https://flagcdn.com/w320/kr.png,https://flagcdn.com/w320/kr.png,data/assets/approved/appr_67a033c94405f7.png,data/assets/approved/appr_67a033c94405f7.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.319998+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9c7fc211069805,ast_9c7fc211069805,primary_logo_v1,team,Las Vegas Aces,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg,data/assets/approved/appr_9c7fc211069805.svg,data/assets/approved/appr_9c7fc211069805.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320001+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7eea0085424fe3,ast_7eea0085424fe3,primary_logo_v1,team,Los Angeles Sparks,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320005+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_34556a69591b47,ast_34556a69591b47,primary_flag_v1,team,Mexico W,https://flagcdn.com/w320/mx.png,https://flagcdn.com/w320/mx.png,data/assets/approved/appr_34556a69591b47.png,data/assets/approved/appr_34556a69591b47.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320009+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_047086213c7096,ast_047086213c7096,primary_logo_v1,team,Minnesota Lynx,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,https://upload.wikimedia.org/wikipedia/en/7/70/Minnesota_Lynx_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320013+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9edeb1cdaa6f4c,ast_9edeb1cdaa6f4c,primary_logo_v1,team,Phoenix Mercury,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,data/assets/approved/appr_9edeb1cdaa6f4c.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320020+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_01d68c2809f81f,ast_01d68c2809f81f,primary_logo_v1,team,Portland Fire,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,https://upload.wikimedia.org/wikipedia/en/0/09/Portland_Fire_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320024+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_52d46724c00ec9,ast_52d46724c00ec9,primary_logo_v1,team,Seattle Storm,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,data/assets/approved/appr_52d46724c00ec9.svg,data/assets/approved/appr_52d46724c00ec9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320028+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_9426bf971998ee,ast_9426bf971998ee,primary_flag_v1,team,Serbia W,https://flagcdn.com/w320/rs.png,https://flagcdn.com/w320/rs.png,data/assets/approved/appr_9426bf971998ee.png,data/assets/approved/appr_9426bf971998ee.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320030+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_2d1d5b6b4b59b0,ast_2d1d5b6b4b59b0,primary_flag_v1,team,South Africa W,https://flagcdn.com/w320/za.png,https://flagcdn.com/w320/za.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,data/assets/approved/appr_2d1d5b6b4b59b0.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320032+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_526f2acaa1d24e,ast_526f2acaa1d24e,primary_flag_v1,team,Thailand W,https://flagcdn.com/w320/th.png,https://flagcdn.com/w320/th.png,data/assets/approved/appr_526f2acaa1d24e.png,data/assets/approved/appr_526f2acaa1d24e.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320033+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_dd35c3cb61c372,ast_dd35c3cb61c372,primary_flag_v1,team,Turkey W,https://flagcdn.com/w320/tr.png,https://flagcdn.com/w320/tr.png,data/assets/approved/appr_dd35c3cb61c372.png,data/assets/approved/appr_dd35c3cb61c372.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320035+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_49824984287991,ast_49824984287991,primary_flag_v1,team,USA W,https://flagcdn.com/w320/us.png,https://flagcdn.com/w320/us.png,data/assets/approved/appr_49824984287991.png,data/assets/approved/appr_49824984287991.png,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-09T01:09:50.320037+00:00,HSD social graphics,\n...TRUNCATED...\n```\n\n## fact_warning_queue.csv\n\n```csv\nwarning_id,bundle_id,warning_type,severity,subject,details,manual_review_required
\n```\n\n## studio_bundle_prompts_v2.md\n\n# HSD Bundle Prompts v2.2

Generated: 2026-06-09T01:09:50.670084+00:00

## Main WNBA Result

```text
HSD VISUAL UPGRADE v2.2 PROMPT
Bundle: Main WNBA Result
Template: result_slide_v2
Canvas: 1080x1350 carousel
Source facts: 
Caption/context: Dallas Wings beat Los Angeles Sparks. Top performers: Jessica Shepard (Dallas Wings): PTS 22, REB 15, AST 5, STL 2; Arike Ogunbowale (Dallas Wings): PTS 30, REB 6, AST 6; Paige Bueckers (Dallas Wings): PTS 18, REB 3, AST 14, STL 1.
Accuracy lock: BUNDLE LOCKED FACTS: Dallas Wings beat Los Angeles Sparks: Dallas Wings 104, Los Angeles Sparks 96. Do not alter winners, losers, scores, stat lines, team order, or source-safe context. Check every result row before posting.

Safe graphics mode: logos_and_text_only
Critical instruction: Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only.

Approved exact assets:
- Dallas Wings | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg
- Los Angeles Sparks | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg

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
HSD VISUAL UPGRADE v2.2 PROMPT
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
HSD VISUAL UPGRADE v2.2 PROMPT
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
HSD VISUAL UPGRADE v2.2 PROMPT
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
\n\n## graphics_qa_report.md\n\n# HSD Graphics QA Scorer v1.2.2 Report

Generated: 2026-06-09T01:09:52.360394+00:00

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
\n\n## visual_upgrade_manifest.json\n\n```json\n{
  "version": "hsd-studio-visual-upgrade-v2.2.2",
  "generated_at_utc": "2026-06-09T01:09:50.671572+00:00",
  "counts": {
    "bundles": 4,
    "approved_assets": 25,
    "fact_warnings": 0,
    "warnings_propagated_to_prompts": 0
  }
}\n```\n\n## graphics_qa_manifest.json\n\n```json\n{
  "version": "hsd-graphics-qa-scorer-v1.2.2",
  "generated_at_utc": "2026-06-09T01:09:52.360503+00:00",
  "counts": {
    "bundles_scored": 4
  }
}\n```\n