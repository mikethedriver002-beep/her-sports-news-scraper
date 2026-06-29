# Review-Only Action Photo Manual Source-Hunt Board v1

Generated: `2026-06-28T00:00:00+00:00`

Manual source-hunt board for finding real action-photo candidate pages without fetching, scraping, downloading, approving, or publishing. Each row starts from the action-photo candidate queue and tells Mike what source/evidence/identity anchors to collect before pasting into the research return intake.

## Operator Contract

- Paste target: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Collect source-page URLs and evidence only; do not save image files.
- Required paste fields: `candidate_photo_url`, `evidence_url`, `evidence_summary`, `identity_anchor_url`, `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`, and `operator_verify_required`.
- Existing schema field `candidate_photo_url` is human-provided only and should mean a candidate/source page URL, not a direct image file, cached binary, screenshot, or thumbnail.
- Generated local-download-law fields stay blank/no. Later human download-decision review is separate, quarantine-only, and not asset approval.

## Summary

- Source-hunt rows: `10`
- Validation issues: `0`
- Rows with source URL already filled: `0`
- Rows with download approval recorded: `0`
- Review-only rows: `10`
- Publish-ready rows: `0`

## Sport Counts

- basketball: `3`
- golf: `1`
- hockey: `1`
- soccer: `2`
- softball: `2`
- tennis: `1`

## Source Category Counts

- editorial_wire: `2`
- official_federation_or_tournament: `3`
- official_league_gallery: `4`
- reputable_newsroom_gallery: `1`

## Source-Hunt Ranking

- Tier 1: official league/team/federation/tournament portals such as official galleries, recap pages, and press releases.
- Tier 2: authorized agency or public preview/search references such as ISI Photos, Photoshelter, Getty-style, AP, Reuters, or Imagn pages; manual reference only and not a clearance signal.
- Tier 3: credited women's sports or specialist media coverage; verify photographer credit, provenance, rights posture, identity, and crop/use fit.
- Tier 4: verified team/player/league social posts; cautious manual reference only because overlays, reposts, platform terms, and crop issues are common.
- Candidate-ready means later human download-decision review only; it is never download approval, asset approval, render approval, or publish readiness.

## Source-Hunt Rows

| Hunt | Queue | Sport | Entity | Tier | Rights Review | Source Family | Primary Query | Secondary Query | Candidate Page Guidance | Red Flags / Hold Reasons | Paste Target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APSH001 | APQ001 | basketball | WNBA | tier_2_authorized_syndicator_public_reference | authorized_agency_preview_reference | Getty Images Editorial Sports | `{player_name} WNBA match action site:gettyimages.com` | `{player_name} {team} WNBA recap photos gallery action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | public preview is not clearance/watermark or license wall/terms restrict reuse/caption missing identity/direct image binary or thumbnail | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH002 | APQ002 | basketball | WNBA | tier_1_official_league_team_portal | official_editorial_page | WNBA official league/team galleries | `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap` | `{player_name} {team} WNBA recap photos gallery action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH003 | APQ003 | soccer | NWSL | tier_2_authorized_syndicator_public_reference | authorized_agency_preview_reference | ISI Photos Archive | `{player_name} {club} NWSL isiphotos photoshelter action` | `{player_name} {club} NWSL match recap gallery action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | public preview is not clearance/watermark or license wall/terms restrict reuse/caption missing identity/direct image binary or thumbnail | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH004 | APQ004 | soccer | USWNT / U.S. Soccer | tier_1_official_league_team_portal | official_editorial_page | ISI Photos / U.S. Soccer | `{player_name} USWNT match action ISI Photos OR ussoccer photos` | `{player_name} USWNT match recap gallery action identity anchor` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH005 | APQ005 | basketball | NCAA Women Basketball | tier_1_official_league_team_portal | official_editorial_page | NCAA Photos / Clarkson Creative | `{player_name} NCAA March Madness basketball ncaaphotos photoshelter` | `{player_name} action photo official recap gallery identity anchor` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH006 | APQ006 | softball | NCAA Women Softball | tier_1_official_league_team_portal | official_editorial_page | NCAA Photos / Clarkson Creative | `{player_name} Women College World Series softball ncaaphotos photoshelter` | `{player_name} softball recap gallery swing pitch slide action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH007 | APQ007 | hockey | PWHL | tier_2_authorized_syndicator_public_reference | authorized_agency_preview_reference | Getty / Ice Garden / Inside the Rink | `{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery` | `{player_name} PWHL game recap gallery jersey number action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | public preview is not clearance/watermark or license wall/terms restrict reuse/caption missing identity/direct image binary or thumbnail | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH008 | APQ008 | softball | AUSL / Pro Softball | tier_1_official_league_team_portal | official_editorial_page | Athletes Unlimited / AUSL Media Hub | `{player_name} AUSL softball action site:theausl.com OR Jade Hewitt` | `{player_name} softball recap gallery swing pitch slide action` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH009 | APQ009 | tennis | WTA Tennis | tier_1_official_league_team_portal | official_editorial_page | WTA / Getty | `{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com` | `{player_name} tournament match gallery serve action official profile` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
| APSH010 | APQ010 | golf | LPGA Golf | tier_1_official_league_team_portal | official_editorial_page | LPGA / Getty | `{player_name} LPGA swing site:lpga.com OR site:gettyimages.com` | `{player_name} tournament gallery swing celebration official profile` | Prefer candidate_page_url/evidence page/source page wording. If the existing return schema requires candidate_photo_url, keep it blank until a human supplies a page URL; do not paste hotlinked image files or cached binaries. | partner-licensed imagery may still need rights review/missing caption or event context/direct image binary or hotlink/page implies sales/license workflow | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` |
