# Review-Only Action Photo Sport/Entity Source-Map Board v1

Generated: `2026-06-28T00:00:00+00:00`

Operator board for WNBA, NWSL, USWNT, NCAA, tennis, golf, official/public discovery lanes, and known newsroom/social/manual-research slots. Rows are source-map prompts only; they do not fetch images, download files, enable sources, approve assets, move files, write headshots, create `.approved` markers, or publish.

## Operator Contract

- Paste researched lead rows into `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` only after human review.
- Leave generated operator decision fields blank until a human edits them.
- Keep `download_approved=no`; download approval is a later quarantine-only human decision, not asset approval.
- Keep `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` blank in generated board rows.

## Summary

- Board rows: `12`
- Validation issues: `0`
- Rows with human yes in `download_approved`: `0`
- Blank operator decision rows: `12`
- Blank source_url rows: `12`
- Review-only rows: `12`
- Publish-ready rows: `0`

## Lane Counts

- gray_area: `1`
- official: `7`
- public: `3`
- reputable_public: `1`

## Sport Counts

- basketball: `2`
- college basketball: `1`
- college soccer: `1`
- golf: `1`
- multi-sport: `3`
- soccer: `3`
- tennis: `1`

## Board Preview

| ID | Sport | Entity | Source type | Placeholder | Usefulness | Status | Risk notes | Slot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APSMB001 | basketball | WNBA | official league/team gallery | `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap` | high - likely game action, uniforms, arena context, and current team identity | official_free_public_review_needed | Official/public page is a lead only; no rights, download, or render approval is implied. | official_gallery |
| APSMB002 | basketball | WNBA | newsroom/editorial wire | `{player_name} WNBA action site:gettyimages.com OR site:apnews.com OR site:reuters.com` | high - strong action and emotion but rights-sensitive | public_rights_sensitive_manual_review | Wire/newsroom previews are evidence leads only; never save preview files or watermarked images. | known_newsroom |
| APSMB003 | soccer | NWSL | official league/team gallery | `{player_name} {club} site:nwslsoccer.com OR site:{club_domain} photos OR gallery OR recap` | high - match action with club context and roster anchors | official_free_public_review_needed | Team/league pages need manual rights review; use only source-page URL evidence. | official_gallery |
| APSMB004 | soccer | NWSL | newsroom/social/manual research | `{player_name} {club} NWSL action photo ISI OR local newsroom OR official social` | medium - may reveal strong action leads but provenance varies by surface | public_or_social_uncleared | Social and newsroom rows require source, credit, event, and identity review before any next step. | known_newsroom_social_manual |
| APSMB005 | soccer | USWNT / U.S. Soccer | official federation/tournament | `{player_name} USWNT match action site:ussoccer.com OR official tournament gallery` | high - national-team visuals and event context can lift premium renders later | official_free_public_review_needed | National-team context still needs manual event/date/rights review. | official_gallery |
| APSMB006 | college basketball | NCAA women's basketball | official tournament/school | `{player_name} NCAA women's basketball action site:ncaa.com OR ncaaphotos photoshelter OR site:{school}.edu recap` | medium - useful for tournament action but often partner/licensed | official_partner_or_school_public_review_needed | NCAA Photos and school pages are not download permission; keep as URL evidence. | official_gallery_manual |
| APSMB007 | college soccer | NCAA women's soccer | official tournament/school | `{player_name} NCAA women's soccer action site:ncaa.com OR ncaaphotos photoshelter OR site:{school}.edu recap` | medium - useful for match action when school/tournament context is clear | official_partner_or_school_public_review_needed | Verify school roster, event, and image credit; do not infer rights from official hosting. | official_gallery_manual |
| APSMB008 | tennis | WTA / Grand Slam / tournament | official tournament/newsroom | `{player_name} tennis action site:wtatennis.com OR official tournament gallery OR site:gettyimages.com` | medium - strong athletic motion, but many surfaces are editorial/licensed | official_or_public_rights_sensitive | Preserve tournament/page URL; no cropped, wallpaper, or image-search thumbnail leads. | official_newsroom_manual |
| APSMB009 | golf | LPGA / tournament | official tournament/newsroom | `{player_name} LPGA swing action site:lpga.com OR official tournament gallery OR site:gettyimages.com` | medium - swing/celebration images can help, generic stock-like golf images do not | official_or_public_rights_sensitive | Golf rows need player/event identity context; generic swing imagery is too weak. | official_newsroom_manual |
| APSMB010 | multi-sport | Official social slot | official social | `{player_name} action photo official Instagram OR X OR team social post source page` | low_to_medium - discovery clue only unless source, credit, and event proof are clear | social_uncleared_public_lead | Official social is not approval; paste only source-page leads and keep rights fields blank. | known_social |
| APSMB011 | multi-sport | Manual newsroom slot | local newsroom/public media | `{player_name} action photo local newsroom OR public media OR regional broadcaster gallery` | medium - often strong editorial context but rights-sensitive | public_rights_sensitive_manual_review | Newsroom photos require credit, source, identity, and rights review; no image downloads. | known_newsroom |
| APSMB012 | multi-sport | Gray-area parking slot | creator/fan/archive | `{player_name} action photo Flickr OR Wikimedia OR fan gallery OR creator portfolio` | low - discovery clue only, blocked from download by default | gray_area_public_lead_only | Gray-area leads are not candidate assets and cannot be used to approve downloads. | manual_research_parking |
