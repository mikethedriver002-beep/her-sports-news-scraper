# HSD Asset Availability Audit v1

Generated: `2026-06-26T01:51:02.051358+00:00`
Status: `review_required`

Review-only audit. This report does not approve assets, fetch files, move files into publish-ready lanes, publish, or change renderer behavior.

## Counts

- findings: `611`
- error: `206`
- info: `1`
- warning: `404`

## Finding Types

- logo_present_without_complete_approval: `3`
- missing_local_player_asset: `204`
- missing_or_unregistered_logo_asset: `2`
- player_photo_format_problem: `204`
- renderer_logo_audit_missing: `1`
- suspicious_logo_source_or_approval: `1`
- suspicious_or_default_player_approval: `196`

## Error And Warning Sample

- `error` `missing_local_player_asset` | player_photo | Aaliyah Nye | `assets/leagues/wnba/athletes/atlanta_dream_aaliyah_nye/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Aaliyah Nye | `assets/leagues/wnba/athletes/atlanta_dream_aaliyah_nye/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Aaliyah Nye | `assets/leagues/wnba/athletes/atlanta_dream_aaliyah_nye/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Allisha Gray | `assets/leagues/wnba/athletes/atlanta_dream_allisha_gray/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Allisha Gray | `assets/leagues/wnba/athletes/atlanta_dream_allisha_gray/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Allisha Gray | `assets/leagues/wnba/athletes/atlanta_dream_allisha_gray/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Amy Okonkwo | `assets/leagues/wnba/athletes/atlanta_dream_amy_okonkwo/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Amy Okonkwo | `assets/leagues/wnba/athletes/atlanta_dream_amy_okonkwo/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Amy Okonkwo | `assets/leagues/wnba/athletes/atlanta_dream_amy_okonkwo/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Angel Reese | `assets/leagues/wnba/athletes/atlanta_dream_angel_reese/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Angel Reese | `assets/leagues/wnba/athletes/atlanta_dream_angel_reese/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Angel Reese | `assets/leagues/wnba/athletes/atlanta_dream_angel_reese/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Brionna Jones | `assets/leagues/wnba/athletes/atlanta_dream_brionna_jones/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Brionna Jones | `assets/leagues/wnba/athletes/atlanta_dream_brionna_jones/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Brionna Jones | `assets/leagues/wnba/athletes/atlanta_dream_brionna_jones/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Indya Nivar | `assets/leagues/wnba/athletes/atlanta_dream_indya_nivar/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Indya Nivar | `assets/leagues/wnba/athletes/atlanta_dream_indya_nivar/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Indya Nivar | `assets/leagues/wnba/athletes/atlanta_dream_indya_nivar/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Isobel Borlase | `assets/leagues/wnba/athletes/atlanta_dream_isobel_borlase/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Isobel Borlase | `assets/leagues/wnba/athletes/atlanta_dream_isobel_borlase/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Isobel Borlase | `assets/leagues/wnba/athletes/atlanta_dream_isobel_borlase/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Jordin Canada | `assets/leagues/wnba/athletes/atlanta_dream_jordin_canada/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Jordin Canada | `assets/leagues/wnba/athletes/atlanta_dream_jordin_canada/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Jordin Canada | `assets/leagues/wnba/athletes/atlanta_dream_jordin_canada/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Madina Okot | `assets/leagues/wnba/athletes/atlanta_dream_madina_okot/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Madina Okot | `assets/leagues/wnba/athletes/atlanta_dream_madina_okot/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Madina Okot | `assets/leagues/wnba/athletes/atlanta_dream_madina_okot/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Naz Hillmon | `assets/leagues/wnba/athletes/atlanta_dream_naz_hillmon/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Naz Hillmon | `assets/leagues/wnba/athletes/atlanta_dream_naz_hillmon/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Naz Hillmon | `assets/leagues/wnba/athletes/atlanta_dream_naz_hillmon/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Rhyne Howard | `assets/leagues/wnba/athletes/atlanta_dream_rhyne_howard/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Rhyne Howard | `assets/leagues/wnba/athletes/atlanta_dream_rhyne_howard/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Rhyne Howard | `assets/leagues/wnba/athletes/atlanta_dream_rhyne_howard/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Sika Kone | `assets/leagues/wnba/athletes/atlanta_dream_sika_kone/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Sika Kone | `assets/leagues/wnba/athletes/atlanta_dream_sika_kone/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Sika Kone | `assets/leagues/wnba/athletes/atlanta_dream_sika_kone/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Te-Hina Paopao | `assets/leagues/wnba/athletes/atlanta_dream_te_hina_paopao/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Te-Hina Paopao | `assets/leagues/wnba/athletes/atlanta_dream_te_hina_paopao/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Te-Hina Paopao | `assets/leagues/wnba/athletes/atlanta_dream_te_hina_paopao/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Aicha Coulibaly | `assets/leagues/wnba/athletes/chicago_sky_aicha_coulibaly/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Aicha Coulibaly | `assets/leagues/wnba/athletes/chicago_sky_aicha_coulibaly/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Aicha Coulibaly | `assets/leagues/wnba/athletes/chicago_sky_aicha_coulibaly/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Azura Stevens | `assets/leagues/wnba/athletes/chicago_sky_azura_stevens/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Azura Stevens | `assets/leagues/wnba/athletes/chicago_sky_azura_stevens/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Azura Stevens | `assets/leagues/wnba/athletes/chicago_sky_azura_stevens/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Courtney Vandersloot | `assets/leagues/wnba/athletes/chicago_sky_courtney_vandersloot/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Courtney Vandersloot | `assets/leagues/wnba/athletes/chicago_sky_courtney_vandersloot/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Courtney Vandersloot | `assets/leagues/wnba/athletes/chicago_sky_courtney_vandersloot/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | DiJonai Carrington | `assets/leagues/wnba/athletes/chicago_sky_dijonai_carrington/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | DiJonai Carrington | `assets/leagues/wnba/athletes/chicago_sky_dijonai_carrington/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | DiJonai Carrington | `assets/leagues/wnba/athletes/chicago_sky_dijonai_carrington/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Elizabeth Williams | `assets/leagues/wnba/athletes/chicago_sky_elizabeth_williams/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Elizabeth Williams | `assets/leagues/wnba/athletes/chicago_sky_elizabeth_williams/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Elizabeth Williams | `assets/leagues/wnba/athletes/chicago_sky_elizabeth_williams/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Gabriela Jaquez | `assets/leagues/wnba/athletes/chicago_sky_gabriela_jaquez/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Gabriela Jaquez | `assets/leagues/wnba/athletes/chicago_sky_gabriela_jaquez/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Gabriela Jaquez | `assets/leagues/wnba/athletes/chicago_sky_gabriela_jaquez/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Jacy Sheldon | `assets/leagues/wnba/athletes/chicago_sky_jacy_sheldon/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Jacy Sheldon | `assets/leagues/wnba/athletes/chicago_sky_jacy_sheldon/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Jacy Sheldon | `assets/leagues/wnba/athletes/chicago_sky_jacy_sheldon/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Kamilla Cardoso | `assets/leagues/wnba/athletes/chicago_sky_kamilla_cardoso/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Kamilla Cardoso | `assets/leagues/wnba/athletes/chicago_sky_kamilla_cardoso/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Kamilla Cardoso | `assets/leagues/wnba/athletes/chicago_sky_kamilla_cardoso/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Maddy Westbeld | `assets/leagues/wnba/athletes/chicago_sky_maddy_westbeld/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Maddy Westbeld | `assets/leagues/wnba/athletes/chicago_sky_maddy_westbeld/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Maddy Westbeld | `assets/leagues/wnba/athletes/chicago_sky_maddy_westbeld/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Natasha Cloud | `assets/leagues/wnba/athletes/chicago_sky_natasha_cloud/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Natasha Cloud | `assets/leagues/wnba/athletes/chicago_sky_natasha_cloud/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Natasha Cloud | `assets/leagues/wnba/athletes/chicago_sky_natasha_cloud/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Rachel Banham | `assets/leagues/wnba/athletes/chicago_sky_rachel_banham/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Rachel Banham | `assets/leagues/wnba/athletes/chicago_sky_rachel_banham/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Rachel Banham | `assets/leagues/wnba/athletes/chicago_sky_rachel_banham/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Rickea Jackson | `assets/leagues/wnba/athletes/chicago_sky_rickea_jackson/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Rickea Jackson | `assets/leagues/wnba/athletes/chicago_sky_rickea_jackson/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Rickea Jackson | `assets/leagues/wnba/athletes/chicago_sky_rickea_jackson/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Saylor Poffenbarger | `assets/leagues/wnba/athletes/chicago_sky_saylor_poffenbarger/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Saylor Poffenbarger | `assets/leagues/wnba/athletes/chicago_sky_saylor_poffenbarger/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- `warning` `suspicious_or_default_player_approval` | player_photo | Saylor Poffenbarger | `assets/leagues/wnba/athletes/chicago_sky_saylor_poffenbarger/headshot.png` | recheck_decision_source_source_file_and_approval_timestamp
- `error` `missing_local_player_asset` | player_photo | Skylar Diggins | `assets/leagues/wnba/athletes/chicago_sky_skylar_diggins/cutout.png` | keep_photo_slot_disabled_until_asset_and_marker_are_reviewed
- `warning` `player_photo_format_problem` | player_photo | Skylar Diggins | `assets/leagues/wnba/athletes/chicago_sky_skylar_diggins/cutout.png` | replace_with_decodable_png_jpg_or_webp_before_renderer_use
- ...and 530 more error/warning findings in the CSV.

## Renderer Availability Notes

- `info` `renderer_logo_audit_missing` | `not_observed` | Template renderer logo status
