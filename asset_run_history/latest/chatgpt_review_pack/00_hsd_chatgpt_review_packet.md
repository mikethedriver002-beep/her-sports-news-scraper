# HSD ChatGPT Review Packet

Upload this single file for review. The numbered files in `chatgpt_review_pack/` are included only for deeper debugging.

## latest_asset_visual_qa_run_summary.md

# HSD Asset Visual QA v1.8.1 Run Summary

Run timestamp UTC: `2026-06-10 02:43:22 UTC`
Archive folder: `asset_run_history/2026-06-10/0243_UTC`

## Row counts

- `asset_manifest.csv`: 3
- `team_assets.csv`: 3
- `player_assets.csv`: 1
- `asset_rights_review.csv`: 3
- `approved_graphics_assets.csv`: 4
- `launch_integration_points.csv`: 1
- `asset_source_seed_list.csv`: 3
- `fact_warning_queue.csv`: 0
- `player_image_requirements.csv`: 1
- `player_image_candidates.csv`: 1
- `graphics_qa_results.csv`: 1
- `graphics_display_copy.csv`: 5
- `graphics_banned_language.csv`: 10
- `studio_freshness_gate.csv`: 1
- `studio_stale_packet_queue.csv`: 0
- `player_image_fit_gate.csv`: 1
- `rendered_slide_qa.csv`: 0
- `graphics_chat_upload_manifest.csv`: 4
- `graphics_upload_pack_status.csv`: 1

## Player image sourcing

# HSD People and Player Image Sourcing Report

Generated: 2026-06-10T02:43:20.266677+00:00
Version: hsd-player-image-assets-v1.6.1-people-filter-fix

People/player images required: Yes
Required people rows: 1
Found required people/player images: 1
Missing required people/player images: 0
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 1

## Required people and players

- found_downloaded | tonight-in-the-w-preview | Toronto Tempo | Los Angeles Sparks | data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg | wikidata_p18

## Graphics chat upload pack

- bundles: 1
- asset rows: 4
- files created: 4
- png preferred created: 4
- upload packs ready: 0
- upload packs blocked: 1

## Missing optional files



## asset_desk_manifest.json

```json
{
  "version": "hsd-asset-desk-v1.2.2",
  "generated_at_utc": "2026-06-10T02:43:10.229872+00:00",
  "rights_mode": "aggressive",
  "download": true,
  "inputs": {
    "bundle_queue": "studio_bundle_queue.csv",
    "bundle_packets": "studio_bundle_packets.md",
    "launch_graphics_brief": "launch_graphics_chat_brief.md"
  },
  "counts": {
    "bundles": 1,
    "teams_detected": 3,
    "players_detected": 0,
    "asset_candidates": 3,
    "approved_assets": 3,
    "integration_rows": 1,
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

Generated: 2026-06-10T02:43:10.229764+00:00

v1.2 adds exact entity cleanup, stat-token filtering, expanded WNBA logo registry, safer player-image logic, and mismatch warnings.

Teams detected: 3
Players detected: 0
Approved assets: 3
Fact warnings: 0

## Approved
- approved | Connecticut Sun | logo | https://upload.wikimedia.org/wikipedia/en/7/79/Connecticut_Sun_logo.svg
- approved | Los Angeles Sparks | logo | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- approved | Seattle Storm | logo | https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg

## Text-forward / needs verification


## approved_graphics_assets.csv

```csv
approved_asset_id,asset_id,approved_variant,entity_type,entity_name,source_url,page_url,master_path,web_path,rights_status,approved_by,approved_utc,usage_scope,notes
appr_41e4beca67bf4e,ast_41e4beca67bf4e,primary_logo_v1,team,Connecticut Sun,https://upload.wikimedia.org/wikipedia/en/7/79/Connecticut_Sun_logo.svg,https://upload.wikimedia.org/wikipedia/en/7/79/Connecticut_Sun_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-10T02:43:10.227931+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_7eea0085424fe3,ast_7eea0085424fe3,primary_logo_v1,team,Los Angeles Sparks,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,,,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-10T02:43:10.227951+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_52d46724c00ec9,ast_52d46724c00ec9,primary_logo_v1,team,Seattle Storm,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,data/assets/approved/appr_52d46724c00ec9.svg,data/assets/approved/appr_52d46724c00ec9.svg,auto_approved_by_hsd_aggressive_policy,HSD aggressive asset policy with v1.2 exact-entity and fallback guard,2026-06-10T02:43:10.227955+00:00,HSD social graphics,"Auto-approved only after exact-match, fallback, and entity-cleanup guard."
appr_d1b2ad2066c091,ast_d1b2ad2066c091,primary_player_photo_v1,player,Toronto Tempo,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg,data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg,data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg,auto_approved_by_hsd_aggressive_policy,HSD people/player image sourcing pipeline,2026-06-10T02:43:20.265862+00:00,HSD social graphics,Required people/player image sourced via wikidata_p18.

```

## player_image_requirements.csv

```csv
bundle_slug,bundle_name,sport,league,player_name,team_name,required,status,approved_asset_id,source_url,local_path,sourcing_method,notes
tonight-in-the-w-preview,Tonight in the W Preview,basketball,WNBA,Toronto Tempo,Los Angeles Sparks,Yes,found_downloaded,appr_d1b2ad2066c091,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg,data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg,wikidata_p18,

```

## player_image_sourcing_report.md

# HSD People and Player Image Sourcing Report

Generated: 2026-06-10T02:43:20.266677+00:00
Version: hsd-player-image-assets-v1.6.1-people-filter-fix

People/player images required: Yes
Required people rows: 1
Found required people/player images: 1
Missing required people/player images: 0
Free search enabled: Yes
DuckDuckGo package available: Yes
Candidate rows inspected: 1

## Required people and players

- found_downloaded | tonight-in-the-w-preview | Toronto Tempo | Los Angeles Sparks | data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg | wikidata_p18


## player_image_candidates.csv

```csv
candidate_id,player_name,team_name,candidate_url,page_url,source_domain,title,method,score,download_status,local_path,width_px,height_px,mime_type,approved,reject_reason
pcand_d1b2ad2066c091,Toronto Tempo,Los Angeles Sparks,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg,https://www.wikidata.org/wiki/Q125879905,commons.wikimedia.org,"Toronto Tempo women's National Basketball Association team in Toronto, Ontario",wikidata_p18,105,downloaded,data/assets/player_images/toronto-tempo_img_3dd9b150b4ef7a.jpg,1024,768,image/jpeg,Yes,

```

## fact_warning_queue.csv

```csv
warning_id,bundle_id,warning_type,severity,subject,details,manual_review_required

```

## graphics_slide_blueprints.md

# HSD Graphics Slide Blueprints

Generated: 2026-06-10T02:43:20.600450+00:00

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

Generated: 2026-06-10T02:43:20.566016+00:00

## Tonight in the W Preview

```text
HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: Tonight in the W Preview
Template: roundup_v2
Canvas: 1080x1350 carousel
Source facts: Connecticut Sun at Toronto Tempo | Los Angeles Sparks at Seattle Storm
Event date: 2026-06-10
Freshness: fresh_upcoming_schedule / allow
Caption/context: Tonight in the W: Connecticut Sun at Toronto Tempo - wed, june 10th at 7:00 pm edt | Los Angeles Sparks at Seattle Storm - wed, june 10th at 10:00 pm edt
Accuracy lock: Preview schedule only. Do not invent final scores, player stats, injuries, records, or quotes.

Safe graphics mode: player_images_allowed
Critical instruction: Player photos are allowed only for approved exact player assets listed below. Never invent or substitute.

Approved exact assets:
- Connecticut Sun | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/7/79/Connecticut_Sun_logo.svg
- Los Angeles Sparks | primary_logo_v1 | https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg
- Seattle Storm | primary_logo_v1 | https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg
- Toronto Tempo | primary_player_photo_v1 | https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg

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
bundle_4ce84aeaf997c0,tonight-in-the-w-preview,Tonight in the W Preview,Connecticut Sun,team,appr_41e4beca67bf4e,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/7/79/Connecticut_Sun_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_original/connecticut-sun_primary-logo-v1_67bf4e.svg,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_png_preferred/connecticut-sun_primary-logo-v1_67bf4e.png,connecticut-sun_primary-logo-v1_67bf4e.svg,connecticut-sun_primary-logo-v1_67bf4e.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload connecticut-sun_primary-logo-v1_67bf4e.png
bundle_4ce84aeaf997c0,tonight-in-the-w-preview,Tonight in the W Preview,Los Angeles Sparks,team,appr_7eea0085424fe3,primary_logo_v1,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,upload.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_original/los-angeles-sparks_primary-logo-v1_424fe3.svg,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_png_preferred/los-angeles-sparks_primary-logo-v1_424fe3.png,los-angeles-sparks_primary-logo-v1_424fe3.svg,los-angeles-sparks_primary-logo-v1_424fe3.png,downloaded:200:content_type_image,converted_svg_to_png,Yes,Yes,Upload los-angeles-sparks_primary-logo-v1_424fe3.png
bundle_4ce84aeaf997c0,tonight-in-the-w-preview,Tonight in the W Preview,Seattle Storm,team,appr_52d46724c00ec9,primary_logo_v1,https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg,cdn.wnba.com,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_original/seattle-storm_primary-logo-v1_c00ec9.svg,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_png_preferred/seattle-storm_primary-logo-v1_c00ec9.png,seattle-storm_primary-logo-v1_c00ec9.svg,seattle-storm_primary-logo-v1_c00ec9.png,copied_local,converted_svg_to_png,Yes,Yes,Upload seattle-storm_primary-logo-v1_c00ec9.png
bundle_4ce84aeaf997c0,tonight-in-the-w-preview,Tonight in the W Preview,Toronto Tempo,player,appr_d1b2ad2066c091,primary_player_photo_v1,https://commons.wikimedia.org/wiki/Special:Redirect/file/Ricohcoliseum.jpg,commons.wikimedia.org,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_original/toronto-tempo_primary-player-photo-v1_66c091.jpg,graphics_chat_upload_pack/tonight-in-the-w-preview/assets_original/toronto-tempo_primary-player-photo-v1_66c091.jpg,toronto-tempo_primary-player-photo-v1_66c091.jpg,toronto-tempo_primary-player-photo-v1_66c091.jpg,copied_local,raster_no_conversion,Yes,Yes,Upload toronto-tempo_primary-player-photo-v1_66c091.jpg

```

## graphics_chat_direct_handoff.md

# HSD Graphics Chat Direct Handoff

Use the ZIP below for the graphics chat. Upload the ZIP contents if the chat cannot unzip.

## Tonight in the W Preview

Recommended ZIP: `graphics_chat_upload_pack_zips/tonight-in-the-w-preview_graphics_chat_upload_pack.zip`

Status: READY_WITH_REVIEW

```text
Use the sanitized uploaded prompt and uploaded asset files only. Use uploaded logo files and uploaded player/person image files if present for this specific bundle. Do not fetch logo URLs. Do not fetch player image URLs. Do not substitute logos or players. Do not invent player bodies, jerseys, jersey numbers, fake player images, or fake logos. If no approved player/person image is present for this bundle, stay text-forward. Output separate slide files.
```


## graphics_upload_pack_status.csv

```csv
bundle_id,post_slug,bundle_name,upload_pack_status,assets_expected,assets_ready,assets_missing,missing_asset_names,zip_path,notes
bundle_4ce84aeaf997c0,tonight-in-the-w-preview,Tonight in the W Preview,ready_with_review,4,4,0,,graphics_chat_upload_pack_zips/tonight-in-the-w-preview_graphics_chat_upload_pack.zip,Review freshness/player-image-fit gate before using this pack.

```

## graphics_upload_pack_status.json

```json
{
  "version": "hsd-graphics-upload-pack-v1.8.3",
  "generated_at_utc": "2026-06-10T02:43:22.278003+00:00",
  "counts": {
    "bundles": 1,
    "asset_rows": 4,
    "files_created": 4,
    "png_preferred_created": 4,
    "upload_packs_ready": 0,
    "upload_packs_blocked": 1
  },
  "bundles": [
    {
      "bundle_id": "bundle_4ce84aeaf997c0",
      "post_slug": "tonight-in-the-w-preview",
      "bundle_name": "Tonight in the W Preview",
      "upload_pack_status": "ready_with_review",
      "assets_expected": 4,
      "assets_ready": 4,
      "assets_missing": 0,
      "missing_asset_names": "",
      "zip_path": "graphics_chat_upload_pack_zips/tonight-in-the-w-preview_graphics_chat_upload_pack.zip",
      "notes": "Review freshness/player-image-fit gate before using this pack."
    }
  ]
}
```

## graphics_qa_report.md

# HSD Graphics QA Scorer v1.8.1 Report

Generated: 2026-06-10T02:43:22.367488+00:00

Bundles scored: 1

## tonight-in-the-w-preview

- Decision: **pass_with_review**
- Score: 92
- Render path: `generated_graphics/tonight-in-the-w-preview.png`
- Issues: `[{"code": "PLAYER_IMAGE_FIT_REVIEW", "severity": "review", "message": "Use tight crop rules for: Toronto Tempo"}, {"code": "RENDER_NOT_FOUND", "severity": "review", "message": "Graphic file not exported yet. Manifest QA only."}]`
- Remediation: Resolve flagged issues and rerun QA.


## graphics_copy_style_guide.md

# HSD Graphics Copy Style Guide v1.7

Generated: 2026-06-10T02:43:20.634923+00:00

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
tonight-in-the-w-preview,1,bundle_cover,Tonight in the W Preview,Results worth knowing.,Around women’s sports,,Follow Her Sports Daily for more women’s sports coverage.,Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context,Avoid robotic verification language. Use natural sports-editor phrasing.

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
main-wnba-result,team_logo,Los Angeles Sparks,Los Angeles Sparks,appr_7eea0085424fe3,https://upload.wikimedia.org/wikipedia/en/9/98/Los_Angeles_Sparks_logo.svg,Use only as the Los Angeles Sparks logo.,Do not use as a player image. Do not place duplicate floating logos in unused corners or margins.,One intentional logo placement per zone only.

```

## graphics_language_manifest.json

```json
{
  "version": "hsd-graphics-language-pack-v1.7.2",
  "generated_at_utc": "2026-06-10T02:43:20.635028+00:00",
  "outputs": [
    "graphics_copy_style_guide.md",
    "graphics_display_copy.csv",
    "graphics_banned_language.csv",
    "graphics_asset_usage_map.csv",
    "graphics_layout_blueprint.csv"
  ],
  "counts": {
    "display_copy_rows": 5,
    "banned_language_rows": 10,
    "asset_usage_rows": 1,
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

Generated: 2026-06-10T02:43:20.600554+00:00

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

Generated: 2026-06-10T02:43:20.739007+00:00

## Tonight in the W Preview

- Prompt path: `graphics_clean_prompts/tonight-in-the-w-preview/00_PROMPT_TO_PASTE.md`
- Raw prompt chars: 1945
- Clean prompt chars: 3358
- Removed internal lines: 3
- Term replacements/removals: 0


## graphics_prompt_clean_manifest.json

```json
{
  "version": "hsd-graphics-prompt-sanitizer-v1.7.2",
  "generated_at_utc": "2026-06-10T02:43:20.740707+00:00",
  "bundle_count": 1,
  "outputs": [
    "graphics_clean_prompts",
    "graphics_prompt_clean_report.md",
    "graphics_prompt_clean_manifest.json"
  ],
  "bundles": [
    {
      "bundle_slug": "tonight-in-the-w-preview",
      "bundle_name": "Tonight in the W Preview",
      "prompt_path": "graphics_clean_prompts/tonight-in-the-w-preview/00_PROMPT_TO_PASTE.md",
      "raw_prompt_chars": 1945,
      "clean_prompt_chars": 3358,
      "removed_lines": 3,
      "replacements": 0
    }
  ]
}
```

## studio_freshness_report.md

# HSD Studio Freshness Gate v1.8

Generated: 2026-06-10T02:43:20.671111+00:00

- bundles checked: 1
- allowed: 1
- review: 0
- blocked: 0
- max fresh hours: 18.0
- strict missing event date: Yes

## Tonight in the W Preview

- Decision: **allow**
- Status: `fresh`
- Event date: `2026-06-10T00:00:00+00:00`
- Recommended label: none
- Reason: event date is within freshness window


## studio_freshness_gate.csv

```csv
bundle_slug,bundle_name,freshness_status,freshness_decision,event_date,event_age_hours,bundle_created_at,source_run_timestamp,is_carryover,requires_relabel,recommended_label,reason,source_evidence
tonight-in-the-w-preview,Tonight in the W Preview,fresh,allow,2026-06-10T00:00:00+00:00,2.7,,2026-06-10T02:43:09.245476+00:00,No,No,,event date is within freshness window,event_date

```

## studio_stale_packet_queue.csv

```csv
bundle_slug,bundle_name,freshness_status,freshness_decision,event_date,event_age_hours,bundle_created_at,source_run_timestamp,is_carryover,requires_relabel,recommended_label,reason,source_evidence

```

## player_image_fit_report.md

# HSD Player Image Fit Gate v1.8

Generated: 2026-06-10T02:43:20.704377+00:00

- checked: 1
- approved: 0
- review: 1
- blocked: 0

This gate does not prove identity by face recognition. It catches sourcing/team-context risks and gives the graphics chat crop rules to avoid wrong-team jersey exposure.

## Toronto Tempo

- Team: Los Angeles Sparks
- Status: **review**
- Usage mode: `tight_face_crop_only`
- Risk: medium | public-source image needs visual review
- Crop rule: Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.


## player_image_fit_gate.csv

```csv
bundle_slug,player_name,team_name,approved_asset_id,fit_status,usage_mode,risk_level,risk_reasons,recommended_crop,prompt_instruction
tonight-in-the-w-preview,Toronto Tempo,Los Angeles Sparks,appr_d1b2ad2066c091,review,tight_face_crop_only,medium,public-source image needs visual review,"Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks.",Use Toronto Tempo's image only for Toronto Tempo. Crop tightly if the jersey is not clearly Los Angeles Sparks.

```

## rendered_slide_qa_report.md

# HSD Rendered Slide QA v1.8

Generated: 2026-06-10T02:43:22.433671+00:00

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
  "generated_at_utc": "2026-06-10T02:43:20.566683+00:00",
  "counts": {
    "bundles": 1,
    "approved_assets": 4,
    "fact_warnings": 0,
    "warnings_propagated_to_prompts": 0
  }
}
```

## graphics_qa_manifest.json

```json
{
  "version": "hsd-graphics-qa-scorer-v1.8.1-event-date-bridge",
  "generated_at_utc": "2026-06-10T02:43:22.367587+00:00",
  "counts": {
    "bundles_scored": 1,
    "upload_status_rows": 1,
    "freshness_rows": 1,
    "player_fit_rows": 1
  }
}
```
