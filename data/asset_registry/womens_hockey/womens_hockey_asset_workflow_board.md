# Women's Hockey Asset Workflow Board

- Generated: `2026-06-27T17:52:16.248547+00:00`
- League: `Professional Women's Hockey League`
- Status: `review_only_workflow_ready`
- Scope: review-only operator workflow board; it reads source/contact/intake artifacts and writes no assets.
- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.

## Review Order

1. Open `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv` and compare logo candidates against source pages.
2. Record logo holds or source notes in `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`; keep registry actions hold-only until a human explicitly approves later.
3. Open `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv` and the team boards listed below.
4. Record athlete source and identity notes in `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`; keep local-file review false until Mike manually supplies a candidate file.
5. Use `data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md` for row-by-row pacing when doing a batch review sweep.

## Candidate Layer Clarity

- `local_candidate_path` values are proposed manual target paths only; this report does not create `headshot.png` files.
- `approved_marker_path` values are proposed manual marker paths only; this report does not create `.approved` markers.
- Proposed headshot path refs: `36`; files currently present: `0`.
- Proposed `.approved` path refs: `36`; markers currently present: `0`.
- Unsafe logo intake rows detected: `0`.
- Unsafe athlete intake rows detected: `0`.

## Logo Queue

1. Professional Women's Hockey League | league_mark | source=https://www.thepwhl.com/en/
2. Boston Fleet | primary_logo | source=https://www.thepwhl.com/en/teams/boston-fleet
3. PWHL Detroit | primary_logo | source=https://www.thepwhl.com/en/teams/detroit
4. PWHL Hamilton | primary_logo | source=https://www.thepwhl.com/en/teams/hamilton
5. PWHL Las Vegas | primary_logo | source=https://www.thepwhl.com/en/teams/las-vegas
6. Minnesota Frost | primary_logo | source=https://www.thepwhl.com/en/teams/minnesota-frost
7. Montreal Victoire | primary_logo | source=https://www.thepwhl.com/en/teams/montreal-victoire
8. New York Sirens | primary_logo | source=https://www.thepwhl.com/en/teams/new-york-sirens
9. Ottawa Charge | primary_logo | source=https://www.thepwhl.com/en/teams/ottawa-charge
10. PWHL San Jose | primary_logo | source=https://www.thepwhl.com/en/teams/san-jose
11. Seattle Torrent | primary_logo | source=https://www.thepwhl.com/en/teams/seattle-torrent
12. Toronto Sceptres | primary_logo | source=https://www.thepwhl.com/en/teams/toronto-sceptres
13. Vancouver Goldeneyes | primary_logo | source=https://www.thepwhl.com/en/teams/vancouver-goldeneyes

## Athlete Team Boards

1. Boston Fleet | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md` | roster=https://www.thepwhl.com/en/teams/boston-fleet/roster
2. Boston Fleet | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md` | roster=https://www.thepwhl.com/en/teams/boston-fleet
3. Boston Fleet | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md` | roster=https://www.thepwhl.com/en/stats/player-stats
4. PWHL Detroit | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md` | roster=https://www.thepwhl.com/en/teams/detroit/roster
5. PWHL Detroit | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md` | roster=https://www.thepwhl.com/en/teams/detroit
6. PWHL Detroit | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md` | roster=https://www.thepwhl.com/en/stats/player-stats
7. PWHL Hamilton | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md` | roster=https://www.thepwhl.com/en/teams/hamilton/roster
8. PWHL Hamilton | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md` | roster=https://www.thepwhl.com/en/teams/hamilton
9. PWHL Hamilton | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md` | roster=https://www.thepwhl.com/en/stats/player-stats
10. PWHL Las Vegas | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md` | roster=https://www.thepwhl.com/en/teams/las-vegas/roster
11. PWHL Las Vegas | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md` | roster=https://www.thepwhl.com/en/teams/las-vegas
12. PWHL Las Vegas | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md` | roster=https://www.thepwhl.com/en/stats/player-stats
13. Minnesota Frost | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md` | roster=https://www.thepwhl.com/en/teams/minnesota-frost/roster
14. Minnesota Frost | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md` | roster=https://www.thepwhl.com/en/teams/minnesota-frost
15. Minnesota Frost | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md` | roster=https://www.thepwhl.com/en/stats/player-stats
16. Montreal Victoire | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md` | roster=https://www.thepwhl.com/en/teams/montreal-victoire/roster
17. Montreal Victoire | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md` | roster=https://www.thepwhl.com/en/teams/montreal-victoire
18. Montreal Victoire | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md` | roster=https://www.thepwhl.com/en/stats/player-stats
19. New York Sirens | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md` | roster=https://www.thepwhl.com/en/teams/new-york-sirens/roster
20. New York Sirens | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md` | roster=https://www.thepwhl.com/en/teams/new-york-sirens
21. New York Sirens | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md` | roster=https://www.thepwhl.com/en/stats/player-stats
22. Ottawa Charge | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md` | roster=https://www.thepwhl.com/en/teams/ottawa-charge/roster
23. Ottawa Charge | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md` | roster=https://www.thepwhl.com/en/teams/ottawa-charge
24. Ottawa Charge | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md` | roster=https://www.thepwhl.com/en/stats/player-stats
25. PWHL San Jose | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md` | roster=https://www.thepwhl.com/en/teams/san-jose/roster
26. PWHL San Jose | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md` | roster=https://www.thepwhl.com/en/teams/san-jose
27. PWHL San Jose | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md` | roster=https://www.thepwhl.com/en/stats/player-stats
28. Seattle Torrent | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md` | roster=https://www.thepwhl.com/en/teams/seattle-torrent/roster
29. Seattle Torrent | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md` | roster=https://www.thepwhl.com/en/teams/seattle-torrent
30. Seattle Torrent | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md` | roster=https://www.thepwhl.com/en/stats/player-stats
31. Toronto Sceptres | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md` | roster=https://www.thepwhl.com/en/teams/toronto-sceptres/roster
32. Toronto Sceptres | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md` | roster=https://www.thepwhl.com/en/teams/toronto-sceptres
33. Toronto Sceptres | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md` | roster=https://www.thepwhl.com/en/stats/player-stats
34. Vancouver Goldeneyes | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md` | roster=https://www.thepwhl.com/en/teams/vancouver-goldeneyes/roster
35. Vancouver Goldeneyes | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md` | roster=https://www.thepwhl.com/en/teams/vancouver-goldeneyes
36. Vancouver Goldeneyes | board=`data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md` | roster=https://www.thepwhl.com/en/stats/player-stats
