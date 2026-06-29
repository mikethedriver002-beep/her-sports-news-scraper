# Review-Only Action Photo Source Discovery Board v1

Generated: `2026-06-28T00:00:00+00:00`

Operator-facing source discovery board for choosing where ChatGPT Pro, Gemini Pro, or manual researchers should look before filling action-photo candidate queue and return-intake rows. This board maps official, reputable/public, gray-area, and blocked/deprioritized lanes; it does not fetch, download, segment, remove backgrounds, approve assets, or change renderer behavior.

## Return Contract

Researchers should return URL/evidence leads only and paste usable results into `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`. Required return evidence: `candidate_photo_url`, `evidence_url`, `evidence_summary`, `identity_anchor_url`, `source_url`, `rights_class`, `identity_confidence`, `intended_review_only_use`, and `operator_verify_required`. Keep `download_approved=no` unless a later human-edited row satisfies the quarantine-only download law.

## Blocked And Deprioritized Source Rules

- Do not use broadcast/video stills, screenshots, hotlinked image files, image-search thumbnails, AI edits, wallpaper sites, or uncredited reposts as download candidates.
- Gray-area/public creator leads are parking-lot research clues only unless a human later supplies full source, identity, rights, and review-only use metadata.
- Download approval is not asset approval, and any future approved download must land only in `data/assets/quarantine/review_only_candidates/`.

## Summary

- Discovery rows: `12`
- Validation issues: `0`
- Rows with human yes in `download_approved`: `0`
- Review-only rows: `12`
- Publish-ready rows: `0`

## Lane Counts

- gray_area: `1`
- official: `8`
- reputable: `3`

## Sport Counts

- basketball: `2`
- college basketball: `1`
- golf: `1`
- hockey: `1`
- multi-sport: `1`
- soccer: `3`
- softball: `2`
- tennis: `1`

## Researcher Lane Counts

- chatgpt_pro: `6`
- manual_research: `6`

## Board Preview

| ID | Lane | Sport | League/Entity | Family | Category | Macro | Blocked Sources | Queue Hint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APSD001 | official | basketball | WNBA | WNBA official league/team galleries | official_league_gallery | `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap` | broadcast screenshots/Pinterest reposts/uncredited social reposts | APQ002 |
| APSD002 | reputable | basketball | WNBA | Getty Images Editorial Sports | editorial_wire | `{player_name} WNBA match action site:gettyimages.com` | preview downloads/watermarked image saves/AI upscaled copies | APQ001 |
| APSD003 | official | soccer | NWSL | NWSL official league/team galleries | official_league_gallery | `{player_name} {club} site:nwslsoccer.com photos OR gallery OR recap` | fan threads/screen captures/uncaptioned image search thumbnails | APQ003 |
| APSD004 | reputable | soccer | NWSL | ISI Photos Archive | reputable_newsroom_gallery | `{player_name} {club} NWSL isiphotos photoshelter action` | cropped social reposts/wire preview saves/uncredited blog embeds | APQ003 |
| APSD005 | official | soccer | USWNT / U.S. Soccer | U.S. Soccer media and match surfaces | official_federation_or_tournament | `{player_name} USWNT match action site:ussoccer.com` | match broadcast stills/social quote-post images/uncaptioned archive images | APQ004 |
| APSD006 | official | college basketball | NCAA Women Basketball | NCAA Photos / Clarkson Creative | official_federation_or_tournament | `{player_name} NCAA March Madness basketball ncaaphotos photoshelter` | school fan boards/AI-generated edits/social repost compilations | APQ005 |
| APSD007 | official | softball | NCAA Women Softball | NCAA Photos / Clarkson Creative | official_federation_or_tournament | `{player_name} Women College World Series softball ncaaphotos photoshelter` | team media-day portraits/dugout candids without captions/thumbnail cache URLs | APQ006 |
| APSD008 | official | softball | AUSL / Pro Softball | Athletes Unlimited / AUSL Media Hub | official_league_gallery | `{player_name} AUSL softball action site:theausl.com OR site:auprosports.com` | creator reposts without credit/screen captures/image CDN URLs without source page | APQ008 |
| APSD009 | reputable | hockey | PWHL | Getty / credentialed hockey galleries | editorial_wire | `{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery` | screenshots/low-resolution reposts/uncleared creator downloads | APQ007 |
| APSD010 | official | tennis | WTA Tennis | WTA tournament and match-note surfaces | official_league_gallery | `{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com` | random wallpaper sites/cropped social images/uncredited image-search results | APQ009 |
| APSD011 | official | golf | LPGA Golf | LPGA media and tournament surfaces | official_league_gallery | `{player_name} LPGA swing site:lpga.com OR site:gettyimages.com` | generic golf stock sites/uncaptioned image thumbnails/social repost images | APQ010 |
| APSD012 | gray_area | multi-sport | Gray-area parking lane | Public creator, fan, archive, and repost surfaces | gray_area_public_lead | `{player_name} action photo public archive OR Flickr OR Wikimedia OR fan gallery` | hotlinked image files/AI edited copies/unknown-credit reposts/video/broadcast frames | operator_triage_only |
