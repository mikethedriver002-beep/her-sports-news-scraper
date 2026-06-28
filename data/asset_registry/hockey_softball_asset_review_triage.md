# Hockey/Softball Asset Review Triage

Generated: `2026-06-28T12:46:04.013576+00:00`

Review-only operator triage worksheet built from hockey/softball source-priority rows. Advisory source candidates remain in `advisory_source_candidate_urls`; generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.

## Summary

- Triage rows: `38`
- Women's hockey rows: `25`
- Softball rows: `13`
- Logo rows: `20`
- Athlete rows: `18`
- Download-approved yes rows: `0`
- Blank download-law source_url rows: `38`

## Primary Manual Actions

- official_roster_team_source_check: `18`
- source_reviewed_waiting_for_local_asset: `20`

## Safe Operator Path

- Work `official_roster_team_source_check` rows first; they group official PWHL/AUSL roster/team source candidates by team.
- Work logo rows as source-reviewed or source-check holds only; this worksheet does not approve logo identity or write local logo files.
- Treat `advisory_source_candidate_urls` as evidence to open manually, not as download-law `source_url` values.
- Keep `download_approved=no` and leave `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` blank in generated rows.
- Do not download assets, write headshots/logos, create `.approved` markers, move files, or publish from this worksheet.

## Worksheet Preview

| Rank | Action | Sport | Asset | Entity | Source Rows | Verify Sources | Missing Local | Safe Next Action |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | official_roster_team_source_check | womens_hockey | athlete_photo | boston_fleet | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 2 | official_roster_team_source_check | womens_hockey | athlete_photo | detroit | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 3 | official_roster_team_source_check | womens_hockey | athlete_photo | hamilton | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 4 | official_roster_team_source_check | womens_hockey | athlete_photo | las_vegas | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 5 | official_roster_team_source_check | womens_hockey | athlete_photo | minnesota_frost | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 6 | official_roster_team_source_check | womens_hockey | athlete_photo | montreal_victoire | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 7 | official_roster_team_source_check | womens_hockey | athlete_photo | new_york_sirens | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 8 | official_roster_team_source_check | womens_hockey | athlete_photo | ottawa_charge | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 9 | official_roster_team_source_check | womens_hockey | athlete_photo | san_jose | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 10 | official_roster_team_source_check | womens_hockey | athlete_photo | seattle_torrent | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 11 | official_roster_team_source_check | womens_hockey | athlete_photo | toronto_sceptres | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 12 | official_roster_team_source_check | womens_hockey | athlete_photo | vancouver_goldeneyes | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 13 | official_roster_team_source_check | softball | athlete_photo | carolina_blaze | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 14 | official_roster_team_source_check | softball | athlete_photo | chicago_bandits | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 15 | official_roster_team_source_check | softball | athlete_photo | oklahoma_city_spark | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 16 | official_roster_team_source_check | softball | athlete_photo | portland_cascade | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 17 | official_roster_team_source_check | softball | athlete_photo | texas_volts | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 18 | official_roster_team_source_check | softball | athlete_photo | utah_talons | 3 | 3 | 3 | Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank. |
| 19 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | boston_fleet | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 20 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | detroit | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 21 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | hamilton | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 22 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | las_vegas | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 23 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | minnesota_frost | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 24 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | montreal_victoire | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 25 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | new_york_sirens | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 26 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | ottawa_charge | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 27 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | pwhl | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 28 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | san_jose | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 29 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | seattle_torrent | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 30 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | toronto_sceptres | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 31 | source_reviewed_waiting_for_local_asset | womens_hockey | logo | vancouver_goldeneyes | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 32 | source_reviewed_waiting_for_local_asset | softball | logo | ausl | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 33 | source_reviewed_waiting_for_local_asset | softball | logo | carolina_blaze | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 34 | source_reviewed_waiting_for_local_asset | softball | logo | chicago_bandits | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 35 | source_reviewed_waiting_for_local_asset | softball | logo | oklahoma_city_spark | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 36 | source_reviewed_waiting_for_local_asset | softball | logo | portland_cascade | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 37 | source_reviewed_waiting_for_local_asset | softball | logo | texas_volts | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
| 38 | source_reviewed_waiting_for_local_asset | softball | logo | utah_talons | 1 | 0 | 1 | Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake. |
