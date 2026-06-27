# Softball Review Walkthrough

Generated: `2026-06-27 13:52 Cuba Daylight Time`

Review-only walkthrough for the logo and athlete candidate packets. It does not approve assets, download files, move files, publish, or create a publish-ready lane.

## Open First

- Logo contact sheet: `data/asset_registry/softball/softball_logo_contact_sheet.csv`
- Logo intake CSV: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Athlete contact sheet: `data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv`
- Athlete intake CSV: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`

## Review Order

### Logo Packet
1. Athletes Unlimited Softball League | league | source=https://theausl.com/
2. Carolina Blaze | team | source=https://theausl.com/blaze/
3. Chicago Bandits | team | source=https://theausl.com/bandits/
4. Oklahoma City Spark | team | source=https://theausl.com/spark/
5. Portland Cascade | team | source=https://theausl.com/cascade/
6. Texas Volts | team | source=https://theausl.com/volts/
7. Utah Talons | team | source=https://theausl.com/talons/

### Athlete Packet
1. Carolina Blaze | operator_add_player_from_team_roster | roster=https://theausl.com/blaze/roster
2. Carolina Blaze | operator_add_player_from_team_profile_source | roster=https://theausl.com/blaze/
3. Carolina Blaze | operator_add_player_from_league_player_index | roster=https://theausl.com/players/
4. Chicago Bandits | operator_add_player_from_team_roster | roster=https://theausl.com/bandits/roster
5. Chicago Bandits | operator_add_player_from_team_profile_source | roster=https://theausl.com/bandits/
6. Chicago Bandits | operator_add_player_from_league_player_index | roster=https://theausl.com/players/
7. Oklahoma City Spark | operator_add_player_from_team_roster | roster=https://theausl.com/spark/roster
8. Oklahoma City Spark | operator_add_player_from_team_profile_source | roster=https://theausl.com/spark/
9. Oklahoma City Spark | operator_add_player_from_league_player_index | roster=https://theausl.com/players/
10. Portland Cascade | operator_add_player_from_team_roster | roster=https://theausl.com/cascade/roster
11. Portland Cascade | operator_add_player_from_team_profile_source | roster=https://theausl.com/cascade/
12. Portland Cascade | operator_add_player_from_league_player_index | roster=https://theausl.com/players/
13. Texas Volts | operator_add_player_from_team_roster | roster=https://theausl.com/volts/roster
14. Texas Volts | operator_add_player_from_team_profile_source | roster=https://theausl.com/volts/
15. Texas Volts | operator_add_player_from_league_player_index | roster=https://theausl.com/players/
16. Utah Talons | operator_add_player_from_team_roster | roster=https://theausl.com/talons/roster
17. Utah Talons | operator_add_player_from_team_profile_source | roster=https://theausl.com/talons/
18. Utah Talons | operator_add_player_from_league_player_index | roster=https://theausl.com/players/

## How To Fill The Intake CSV

- Logo rows: keep `source_reviewed=yes` and `identity_match=yes` only after you manually open the source candidate page and confirm the mark matches the league or club.
- Athlete source rows: the generator leaves `source_reviewed=no`, `source_allowed_for_review_only=no`, `rights_reviewed=no`, `reviewed_by` blank, and `reviewed_at_local` blank for placeholder source slots.
- After Mike manually opens the roster/profile/index page and confirms source/rights posture, he may batch-mark `source_reviewed=yes`, `source_allowed_for_review_only=yes`, `rights_reviewed=yes`, `reviewed_by`, and `reviewed_at_local` in the intake CSV.
- Athlete identity rows: keep `identity_verified=no` when the row is still an `operator_add_player_*` source slot or has no concrete `player_id` and player name.
- Athlete local file rows: keep `local_file_reviewed=no` until Mike manually supplies and reviews the local candidate file.
- Athlete hold boundary: `registry_action` must stay `hold_no_registry_state_change_until_local_candidate_asset_exists` unless a later explicit human-edited intake file supplies named identity evidence and local asset review.
- Logo rows can complete source/identity match review before a local asset exists, but the registry action still remains hold-only until the asset is manually supplied and reviewed.
- `source_url_to_record` should be the exact source page you reviewed.
- `registry_action` must remain a hold-only action; do not change approval state from this helper.
- Guardrails stay false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads`.

## Safe Pace

Start with the first row in each packet, then work top-to-bottom. The helper keeps the workflow batchable without changing approval state for Athletes Unlimited Softball League.
