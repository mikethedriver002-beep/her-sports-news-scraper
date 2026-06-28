# Hockey/Softball Next Decision Worksheet

- Generated: `2026-06-28T00:00:00+00:00`
- Rows: `74`
- Logo decision rows: `20`
- Athlete source-only rows: `54`
- Missing local candidate asset rows: `74`
- Download-approved yes rows: `0`
- Guardrails: review-only worksheet, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.

## How To Use

1. Open each `source_to_open` manually, then the linked `board_to_open` if context is needed.
2. Use the worksheet CSV for the next human pass; every generated human-decision cell is intentionally blank.
3. Work `1_source_verification` rows first, then `2_missing_local_candidate_asset` rows that are already source-reviewed but still waiting for a local candidate asset.
4. Future quarantine-download metadata fields default to `download_approved=no` or blank; Mike must fill them in a human-edited intake before any later quarantine-only download workflow can act.
5. For logo rows, Mike may fill the listed source/identity fields after manual source review, but registry action stays hold-only until a local logo asset exists.
6. For athlete rows, Mike may fill source/rights fields after opening the source page, but identity/local-file/approval fields stay blank or held until a named athlete and local candidate asset exist.
7. Do not download assets, write headshots, create `.approved` markers, move files, or publish from this worksheet.

## First Action Buckets

- 1_source_verification: `54`
- 2_missing_local_candidate_asset: `20`

## Source Verification Buckets

- official_league_or_team_source_manual_verify: `54`
- source_reviewed_waiting_for_local_asset: `20`

## Future Quarantine-Download Fields

- Required future fields: `download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use`.
- Quarantine folder: `data/assets/quarantine/review_only_candidates`.
- Generated rows keep `download_approved=no`; `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` stay blank for human intake.
- This worksheet does not trigger downloads and does not write quarantine files.

## Next Decision Rows

### ND01 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=boston_fleet; candidate_id=boston_fleet_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND02 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/boston-fleet/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=boston_fleet; candidate_id=boston_fleet_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND03 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/boston-fleet`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/boston_fleet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=boston_fleet; candidate_id=boston_fleet_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND04 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=detroit; candidate_id=detroit_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND05 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/detroit/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=detroit; candidate_id=detroit_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND06 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/detroit`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/detroit.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=detroit; candidate_id=detroit_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND07 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=hamilton; candidate_id=hamilton_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND08 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/hamilton/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=hamilton; candidate_id=hamilton_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND09 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/hamilton`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/hamilton.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=hamilton; candidate_id=hamilton_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND10 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=las_vegas; candidate_id=las_vegas_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND11 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/las-vegas/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=las_vegas; candidate_id=las_vegas_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND12 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/las-vegas`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/las_vegas.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=las_vegas; candidate_id=las_vegas_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND13 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=minnesota_frost; candidate_id=minnesota_frost_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND14 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/minnesota-frost/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=minnesota_frost; candidate_id=minnesota_frost_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND15 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/minnesota-frost`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/minnesota_frost.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=minnesota_frost; candidate_id=minnesota_frost_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND16 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=montreal_victoire; candidate_id=montreal_victoire_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND17 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/montreal-victoire/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=montreal_victoire; candidate_id=montreal_victoire_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND18 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/montreal-victoire`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/montreal_victoire.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=montreal_victoire; candidate_id=montreal_victoire_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND19 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=new_york_sirens; candidate_id=new_york_sirens_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND20 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/new-york-sirens/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=new_york_sirens; candidate_id=new_york_sirens_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND21 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/new-york-sirens`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/new_york_sirens.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=new_york_sirens; candidate_id=new_york_sirens_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND22 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=ottawa_charge; candidate_id=ottawa_charge_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND23 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/ottawa-charge/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=ottawa_charge; candidate_id=ottawa_charge_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND24 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/ottawa-charge`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/ottawa_charge.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=ottawa_charge; candidate_id=ottawa_charge_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND25 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=san_jose; candidate_id=san_jose_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND26 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/san-jose/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=san_jose; candidate_id=san_jose_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND27 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/san-jose`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/san_jose.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=san_jose; candidate_id=san_jose_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND28 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=seattle_torrent; candidate_id=seattle_torrent_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND29 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/seattle-torrent/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=seattle_torrent; candidate_id=seattle_torrent_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND30 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/seattle-torrent`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/seattle_torrent.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=seattle_torrent; candidate_id=seattle_torrent_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND31 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=toronto_sceptres; candidate_id=toronto_sceptres_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND32 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/toronto-sceptres/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=toronto_sceptres; candidate_id=toronto_sceptres_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND33 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/toronto-sceptres`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/toronto_sceptres.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=toronto_sceptres; candidate_id=toronto_sceptres_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND34 - Women's Hockey / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/stats/player-stats`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=vancouver_goldeneyes; candidate_id=vancouver_goldeneyes_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND35 - Women's Hockey / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/vancouver-goldeneyes/roster`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=vancouver_goldeneyes; candidate_id=vancouver_goldeneyes_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND36 - Women's Hockey / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/vancouver-goldeneyes`
- Board: `data/asset_registry/womens_hockey/athlete_photo_contact_sheets/vancouver_goldeneyes.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=vancouver_goldeneyes; candidate_id=vancouver_goldeneyes_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND37 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=carolina_blaze; candidate_id=carolina_blaze_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND38 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/blaze/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=carolina_blaze; candidate_id=carolina_blaze_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND39 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/blaze/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=carolina_blaze; candidate_id=carolina_blaze_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND40 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=chicago_bandits; candidate_id=chicago_bandits_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND41 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/bandits/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=chicago_bandits; candidate_id=chicago_bandits_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND42 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/bandits/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=chicago_bandits; candidate_id=chicago_bandits_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND43 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=oklahoma_city_spark; candidate_id=oklahoma_city_spark_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND44 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/spark/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=oklahoma_city_spark; candidate_id=oklahoma_city_spark_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND45 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/spark/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=oklahoma_city_spark; candidate_id=oklahoma_city_spark_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND46 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=portland_cascade; candidate_id=portland_cascade_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND47 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/cascade/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=portland_cascade; candidate_id=portland_cascade_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND48 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/cascade/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=portland_cascade; candidate_id=portland_cascade_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND49 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=texas_volts; candidate_id=texas_volts_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND50 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/volts/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=texas_volts; candidate_id=texas_volts_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND51 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/volts/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=texas_volts; candidate_id=texas_volts_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND52 - Softball / athlete_photo / operator_add_player_from_league_player_index

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=utah_talons; candidate_id=utah_talons_league_player_index_candidate_03`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND53 - Softball / athlete_photo / operator_add_player_from_team_roster

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/talons/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=utah_talons; candidate_id=utah_talons_roster_source_candidate_01`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND54 - Softball / athlete_photo / operator_add_player_from_team_profile_source

- Section: `athlete_source_only_review`
- First action: `1_source_verification`
- Source bucket: `official_league_or_team_source_manual_verify`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/talons/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md`
- Intake: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=utah_talons; candidate_id=utah_talons_team_profile_source_candidate_02`
- Mike can fill now after manual review: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Must stay blank: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist`
- Must remain hold: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### ND55 - Women's Hockey / logo / Boston Fleet

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/boston-fleet`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=boston_fleet; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND56 - Women's Hockey / logo / PWHL Detroit

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/detroit`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=detroit; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND57 - Women's Hockey / logo / PWHL Hamilton

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/hamilton`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=hamilton; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND58 - Women's Hockey / logo / PWHL Las Vegas

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/las-vegas`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=las_vegas; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND59 - Women's Hockey / logo / Minnesota Frost

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/minnesota-frost`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=minnesota_frost; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND60 - Women's Hockey / logo / Montreal Victoire

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/montreal-victoire`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=montreal_victoire; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND61 - Women's Hockey / logo / New York Sirens

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/new-york-sirens`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=new_york_sirens; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND62 - Women's Hockey / logo / Ottawa Charge

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/ottawa-charge`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=ottawa_charge; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND63 - Women's Hockey / logo / Professional Women's Hockey League

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=pwhl; candidate_id=league_mark`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND64 - Women's Hockey / logo / PWHL San Jose

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/san-jose`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=san_jose; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND65 - Women's Hockey / logo / Seattle Torrent

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/seattle-torrent`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=seattle_torrent; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND66 - Women's Hockey / logo / Toronto Sceptres

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/toronto-sceptres`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=toronto_sceptres; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND67 - Women's Hockey / logo / Vancouver Goldeneyes

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://www.thepwhl.com/en/teams/vancouver-goldeneyes`
- Board: `data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md`
- Intake: `data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv`
- Row key: `sport_family=womens_hockey; entity_id=vancouver_goldeneyes; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND68 - Softball / logo / Athletes Unlimited Softball League

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=ausl; candidate_id=league_mark`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND69 - Softball / logo / Carolina Blaze

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/blaze/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=carolina_blaze; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND70 - Softball / logo / Chicago Bandits

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/bandits/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=chicago_bandits; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND71 - Softball / logo / Oklahoma City Spark

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/spark/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=oklahoma_city_spark; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND72 - Softball / logo / Portland Cascade

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/cascade/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=portland_cascade; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND73 - Softball / logo / Texas Volts

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/volts/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=texas_volts; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`

### ND74 - Softball / logo / Utah Talons

- Section: `logo_wait_for_local_asset_after_source_review`
- First action: `2_missing_local_candidate_asset`
- Source bucket: `source_reviewed_waiting_for_local_asset`
- Download law: `future_quarantine_download_intake_required` (download_approved: `no`)
- Source to open: `https://theausl.com/talons/`
- Board: `data/asset_registry/softball/softball_logo_contact_sheet.md`
- Intake: `data/asset_registry/softball/softball_logo_review_intake.csv`
- Row key: `sport_family=softball; entity_id=utah_talons; candidate_id=primary_logo`
- Mike can fill now after manual review: `none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review`
- Must stay blank: `generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source`
- Must remain hold: `registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads`


## CSV Reminder

- Worksheet CSV: `data/asset_registry/hockey_softball_next_decision_worksheet.csv`
- Blank `operator_*`, `source_url_to_record`, `reviewed_by`, and `reviewed_at_local` cells are intentional generated blanks for Mike's manual pass.
- This worksheet is advisory and does not write back to logo or athlete review intake files.
