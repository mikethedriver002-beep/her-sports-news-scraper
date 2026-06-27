# Softball Review Walkthrough

Generated: `2026-06-27 09:26 Cuba Daylight Time`

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
1. Carolina Blaze | operator_add_player_candidate | roster=https://theausl.com/blaze/roster
2. Chicago Bandits | operator_add_player_candidate | roster=https://theausl.com/bandits/roster
3. Oklahoma City Spark | operator_add_player_candidate | roster=https://theausl.com/spark/roster
4. Portland Cascade | operator_add_player_candidate | roster=https://theausl.com/cascade/roster
5. Texas Volts | operator_add_player_candidate | roster=https://theausl.com/volts/roster
6. Utah Talons | operator_add_player_candidate | roster=https://theausl.com/talons/roster

## How To Fill The Intake CSV

- Logo rows: keep `source_reviewed=yes` and `identity_match=yes` only after you manually open the source candidate page and confirm the mark matches the league or club.
- Athlete rows: keep `identity_verified=yes`, `source_reviewed=yes`, `local_file_reviewed=no`, `source_allowed_for_review_only=yes`, and `rights_reviewed=yes` only after you manually verify the roster/source evidence.
- `source_url_to_record` should be the exact source page you reviewed.
- `registry_action` must remain a hold-only action; do not change approval state from this helper.
- Guardrails stay false: `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads`.

## Safe Pace

Start with the first row in each packet, then work top-to-bottom. The helper keeps the workflow batchable without changing approval state for Athletes Unlimited Softball League.
