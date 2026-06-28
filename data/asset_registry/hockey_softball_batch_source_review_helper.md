# Hockey/Softball Batch Source Review Helper

- Generated: `2026-06-28T00:00:00+00:00`
- Rows: `74`
- Source-reviewable now: `54`
- Already source-reviewed or waiting on local assets: `20`
- Local assets needed later: `74`
- Next batch rows shown: `10`
- Guardrails: review-only, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.

## Batch Rules

1. Open each `evidence_to_open` URL manually.
2. If the page is the expected official/team/roster/profile source, fill only `fields_mike_can_fill_now` in `intake_to_fill`.
3. Keep every value in `fields_to_keep_blank_or_held` unchanged until visual identity/local asset review exists.
4. Do not touch anything listed in `do_not_touch` during a source-review batch.
5. Stop on any row where the source page is stale, missing, paywalled, ambiguous, or mismatched.

## Next 10 Source-Review Rows

### next_01 - Softball / operator_add_player_from_league_player_index

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_02 - Softball / operator_add_player_from_team_profile_source

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/blaze/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_03 - Softball / operator_add_player_from_team_roster

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/blaze/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_04 - Softball / operator_add_player_from_league_player_index

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_05 - Softball / operator_add_player_from_team_profile_source

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/bandits/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_06 - Softball / operator_add_player_from_team_roster

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/bandits/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_07 - Softball / operator_add_player_from_league_player_index

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_08 - Softball / operator_add_player_from_team_profile_source

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/spark/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_09 - Softball / operator_add_player_from_team_roster

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/spark/roster`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`

### next_10 - Softball / operator_add_player_from_league_player_index

- Bucket: `source_review_now`
- Evidence source to open: `https://theausl.com/players/`
- Board: `data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md`
- Intake to fill: `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`
- Fields Mike can fill now: `source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local`
- Keep blank or held: `operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false`
- Do not touch: `operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files`


## Bucket Counts

- source_already_reviewed_wait_for_local_asset: `20`
- source_review_now: `54`

## CSV Workflow

- Open `data/asset_registry/hockey_softball_batch_source_review_helper.csv` and filter `batch_bucket=source_review_now` to continue past the first 10 rows.
- Keep `local_asset_needed_later=yes` rows out of visual identity or approval review until a human supplies a local candidate asset.
