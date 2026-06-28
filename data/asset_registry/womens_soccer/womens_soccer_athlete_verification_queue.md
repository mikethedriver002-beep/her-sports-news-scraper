# Women's Soccer Athlete Verification Queue

Generated: `2026-06-28T16:09:52.677745+00:00`

Review-only operator queue built from existing women's soccer athlete candidate rows, download-intake rows, and external research intake rows. It does not download images, approve assets, write `headshot.png`, create `.approved` markers, change current candidate state, move files into publish-ready lanes, publish, or use paid APIs.

## Summary

- Queue rows: `21`
- NWSL team rows: `16`
- Europe league rows: `5`
- P0 NWSL roster-verification rows: `6`
- Gray-area source rows: `8`
- Missing local candidate asset rows: `509`
- Download-approved yes rows: `0`

## Buckets

- p0_nwsl_roster_verification_first: `6`
- p1_europe_gray_area_source_review: `5`
- p1_nwsl_local_candidate_assets_missing: `10`

## Safe Operator Path

- Work NWSL P0 roster-verification rows first.
- Treat Europe rows as source-map candidates only; they are not render-ready.
- Keep all download intake rows at `download_approved=no` unless a human edits the intake with the required quarantine fields.
- Sam Kerr/Reuters and other gray-area leads remain parked for manual verification only.

## Top Queue Rows

| Rank | Bucket | Scope | League | Team | Candidates | External | Missing Local | Safe Next Action |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | p0_nwsl_roster_verification_first | nwsl | nwsl | Angel City FC | 26 | 4 | 26 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 2 | p0_nwsl_roster_verification_first | nwsl | nwsl | Denver Summit FC | 26 | 2 | 26 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 3 | p0_nwsl_roster_verification_first | nwsl | nwsl | Gotham FC | 27 | 4 | 27 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 4 | p0_nwsl_roster_verification_first | nwsl | nwsl | Houston Dash | 28 | 10 | 28 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 5 | p0_nwsl_roster_verification_first | nwsl | nwsl | Kansas City Current | 31 | 4 | 31 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 6 | p0_nwsl_roster_verification_first | nwsl | nwsl | San Diego Wave FC | 25 | 2 | 25 | Review current official NWSL/team roster metadata before any later human-edited candidate-state change. |
| 7 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Bay FC | 30 | 0 | 30 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 8 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Boston Legacy FC | 26 | 0 | 26 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 9 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Chicago Stars FC | 28 | 1 | 28 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 10 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | North Carolina Courage | 27 | 0 | 27 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 11 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Orlando Pride | 28 | 2 | 28 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 12 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Portland Thorns FC | 31 | 0 | 31 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 13 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Racing Louisville FC | 29 | 0 | 29 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 14 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Seattle Reign | 27 | 1 | 27 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 15 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Utah Royals FC | 27 | 1 | 27 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 16 | p1_nwsl_local_candidate_assets_missing | nwsl | nwsl | Washington Spirit | 27 | 2 | 27 | Review source and rights fields, then use human-edited download intake before any quarantine candidate asset. |
| 17 | p1_europe_gray_area_source_review | europe_top_flight | wsl_england | Wsl England | 12 | 13 | 12 | Park gray-area/non-official leads; verify official source pages before any player-level intake. |
| 18 | p1_europe_gray_area_source_review | europe_top_flight | liga_f_spain | Liga F Spain | 16 | 17 | 16 | Park gray-area/non-official leads; verify official source pages before any player-level intake. |
| 19 | p1_europe_gray_area_source_review | europe_top_flight | frauen_bundesliga_germany | Frauen Bundesliga Germany | 14 | 15 | 14 | Park gray-area/non-official leads; verify official source pages before any player-level intake. |
| 20 | p1_europe_gray_area_source_review | europe_top_flight | serie_a_women_italy | Serie A Women Italy | 12 | 13 | 12 | Park gray-area/non-official leads; verify official source pages before any player-level intake. |
| 21 | p1_europe_gray_area_source_review | europe_top_flight | arkema_premiere_ligue_france | Arkema Premiere Ligue France | 12 | 13 | 12 | Park gray-area/non-official leads; verify official source pages before any player-level intake. |
