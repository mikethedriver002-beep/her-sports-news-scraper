# HSD Womens Soccer Asset Foundation Inventory

Generated for workstream 3 review-only asset cataloging.

## Existing Structures

- `data/asset_registry/womens_soccer/nwsl/` exists with league, team, player, source URL, provider ID, asset slot, approval status, and review report files.
- NWSL coverage is seeded for 16 teams, with official NWSL team detail, roster, schedule, team-site, and logo review source rows.
- NWSL player intake exists as a header-only `players.csv`; no player identities or player photos are approved.
- NWSL asset slots include proposed league/team logo paths only. No files are downloaded, moved, render-enabled, or publish-ready.
- `data/asset_registry/womens_soccer/uswnt/` now exists with matching review-only structures for USWNT national-team cataloging.
- USWNT player intake exists as a header-only `players.csv`, plus a player headshot template slot that requires official profile/manual review before use.

## Official Source Foundation

- NWSL official league/team sources: `https://www.nwslsoccer.com/`
- USWNT official team source: `https://www.ussoccer.com/teams/uswnt`
- USWNT official roster source: `https://www.ussoccer.com/teams/uswnt/roster`
- USWNT official schedule source: `https://www.ussoccer.com/schedule-tickets/uswnt`
- USWNT official player index: `https://www.ussoccer.com/players`

## Gaps

- No player rows are populated for NWSL or USWNT.
- No player photo files are present or approved.
- No logo files are downloaded for the womens soccer registry paths.
- USWNT roster membership is time-sensitive and must be reviewed against a dated official roster page before player rows are added.
- Existing asset assurance configs still reference older `data/asset_registry/nwsl/...` paths, so this foundation is not wired into render or assurance code.
- There is no unified validator for the new USWNT folder; the current validator covers NWSL only.

## Review-Only Next Steps

- Add manual player rows only after an operator verifies official NWSL roster pages or official U.S. Soccer player profiles.
- For each player, record the official profile or roster source URL before adding a proposed `player_headshot` slot.
- Add logo review notes from official league/team pages, then have an operator decide whether a local asset can be introduced.
- Extend the validator/reporting layer to cover both `nwsl` and `uswnt` folders without enabling renders or publishing.
- Update downstream asset assurance configs only after human approval of source rows and target paths.
