# Review-Only Action Photo Candidate Queue v1

Generated: `2026-06-28T00:00:00+00:00`

Concrete candidate-research queue seeded from the action-photo source maps. These rows are prompts for finding real action-photo candidate URLs and evidence; they do not download images, approve assets, assert roster truth, or make anything render-ready.

## Operator Note

Fill `candidate_photo_url`, `evidence_url`, `evidence_summary`, and `identity_anchor_url` after manual or ChatGPT/Gemini research. `download_approved=yes` remains human-edited only, requires `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`, and any later file must land in quarantine. Asset approval and render-ready state remain separate.

## Summary

- Queue rows: `10`
- Validation issues: `0`
- Rows with `download_approved=yes`: `0`
- Review-only rows: `10`
- Publish-ready rows: `0`

## Sport Coverage

- basketball: `3`
- golf: `1`
- hockey: `1`
- soccer: `2`
- softball: `2`
- tennis: `1`

## Source Families

- Athletes Unlimited / AUSL Media Hub: `1`
- Getty / Ice Garden / Inside the Rink: `1`
- Getty Images Editorial Sports: `1`
- ISI Photos / U.S. Soccer: `1`
- ISI Photos Archive: `1`
- LPGA / Getty: `1`
- NCAA Photos / Clarkson Creative: `2`
- WNBA official league/team galleries: `1`
- WTA / Getty: `1`

## Queue Preview

| Queue ID | Sport | League/Entity | Source Family | Moment Type | Search Macro | Manual Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| APQ001 | basketball | WNBA | Getty Images Editorial Sports | transition_drive/block/rebound/celebration | `{player_name} WNBA match action site:gettyimages.com` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ002 | basketball | WNBA | WNBA official league/team galleries | game_action/bench_reaction/celebration | `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ003 | soccer | NWSL | ISI Photos Archive | dribble/shot/save/celebration | `{player_name} {club} NWSL isiphotos photoshelter action` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ004 | soccer | USWNT / U.S. Soccer | ISI Photos / U.S. Soccer | national_team_action/goal_celebration/defensive_play | `{player_name} USWNT match action ISI Photos OR ussoccer photos` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ005 | basketball | NCAA Women Basketball | NCAA Photos / Clarkson Creative | drive/jump_shot/celebration/defense | `{player_name} NCAA March Madness basketball ncaaphotos photoshelter` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ006 | softball | NCAA Women Softball | NCAA Photos / Clarkson Creative | swing/pitch/slide/fielding | `{player_name} Women College World Series softball ncaaphotos photoshelter` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ007 | hockey | PWHL | Getty / Ice Garden / Inside the Rink | skate/shot/save/celebration | `{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ008 | softball | AUSL / Pro Softball | Athletes Unlimited / AUSL Media Hub | swing/pitch/fielding/dugout_celebration | `{player_name} AUSL softball action site:theausl.com OR Jade Hewitt` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ009 | tennis | WTA Tennis | WTA / Getty | serve/forehand/backhand/celebration | `{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
| APQ010 | golf | LPGA Golf | LPGA / Getty | drive/approach/putt/celebration | `{player_name} LPGA swing site:lpga.com OR site:gettyimages.com` | Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law. |
