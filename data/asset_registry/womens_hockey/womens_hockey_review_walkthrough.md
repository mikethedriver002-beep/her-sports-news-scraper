# Women's Hockey Review Walkthrough

Generated: `2026-06-27 09:26 Cuba Daylight Time`

Review-only walkthrough for the logo and athlete candidate packets. It does not approve assets, download files, move files, publish, or create a publish-ready lane.

## Open First

- Logo contact sheet: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv`
- Logo intake CSV: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Athlete contact sheet: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv`
- Athlete intake CSV: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`

## Review Order

### Logo Packet
1. Professional Women's Hockey League | league | source=https://www.thepwhl.com/en/
2. Boston Fleet | team | source=https://www.thepwhl.com/en/teams/boston-fleet
3. PWHL Detroit | team | source=https://www.thepwhl.com/en/teams/detroit
4. PWHL Hamilton | team | source=https://www.thepwhl.com/en/teams/hamilton
5. PWHL Las Vegas | team | source=https://www.thepwhl.com/en/teams/las-vegas
6. Minnesota Frost | team | source=https://www.thepwhl.com/en/teams/minnesota-frost
7. Montreal Victoire | team | source=https://www.thepwhl.com/en/teams/montreal-victoire
8. New York Sirens | team | source=https://www.thepwhl.com/en/teams/new-york-sirens
9. Ottawa Charge | team | source=https://www.thepwhl.com/en/teams/ottawa-charge
10. PWHL San Jose | team | source=https://www.thepwhl.com/en/teams/san-jose
11. Seattle Torrent | team | source=https://www.thepwhl.com/en/teams/seattle-torrent
12. Toronto Sceptres | team | source=https://www.thepwhl.com/en/teams/toronto-sceptres
13. Vancouver Goldeneyes | team | source=https://www.thepwhl.com/en/teams/vancouver-goldeneyes

### Athlete Packet
1. Boston Fleet | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/boston-fleet/roster
2. PWHL Detroit | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/detroit/roster
3. PWHL Hamilton | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/hamilton/roster
4. PWHL Las Vegas | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/las-vegas/roster
5. Minnesota Frost | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/minnesota-frost/roster
6. Montreal Victoire | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/montreal-victoire/roster
7. New York Sirens | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/new-york-sirens/roster
8. Ottawa Charge | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/ottawa-charge/roster
9. PWHL San Jose | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/san-jose/roster
10. Seattle Torrent | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/seattle-torrent/roster
11. Toronto Sceptres | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/toronto-sceptres/roster
12. Vancouver Goldeneyes | operator_add_player_candidate | roster=https://www.thepwhl.com/en/teams/vancouver-goldeneyes/roster

## How To Fill The Intake CSV

- Logo rows: keep `source_reviewed=yes` and `identity_match=yes` only after you manually open the source candidate page and confirm the mark matches the league or club.
- Athlete rows: keep `identity_verified=yes`, `source_reviewed=yes`, `local_file_reviewed=no`, `source_allowed_for_review_only=yes`, and `rights_reviewed=yes` only after you manually verify the roster/source evidence.
- `source_url_to_record` should be the exact source page you reviewed.
- `registry_action` must remain a hold-only action; do not change approval state from this helper.
- Guardrails stay false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads`.

## Safe Pace

Start with the first row in each packet, then work top-to-bottom. The helper keeps the workflow batchable without changing approval state for Professional Women's Hockey League.
