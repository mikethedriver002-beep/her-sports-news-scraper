# Women's Soccer External Research Intake Board

Generated: `2026-06-28T04:40:17.049783+00:00`

Review-only intake board for external ChatGPT Pro research. These rows are advisory metadata candidates only. This packet does not download images, approve assets, write `headshot.png`, create `.approved` markers, change current candidate state, move files into publish-ready lanes, publish, or use paid APIs.

## Summary

- NWSL research rows: `37`
- Europe source-map rows: `71`
- Combined board rows: `108`
- Source CSVs: `nwsl_correction_enrichment_report.csv`, `europe_official_source_map.csv`
- Board CSV: `womens_soccer_external_research_intake_board.csv`

## Operator Buckets

- europe_gray_area_manual_verification_only: `7`
- europe_official_no_verify_metadata_candidate: `40`
- europe_operator_verify_required: `24`
- p0_nwsl_operator_verify_first: `14`
- p1_metadata_candidate_only: `22`
- p3_gray_area_manual_verification_only: `1`

## NWSL First

- P0 rows: verify duplicate/stale team assignments, loans, missing official roster candidates, expired/short-term holds, and stale candidates against official NWSL/team sources before any later human-edited intake change.
- P1 rows: source/profile enrichment metadata only.
- P3 rows: park gray-area or non-official leads for manual verification only. The Sam Kerr/Gotham Reuters row is not current official roster confirmation.

### NWSL Issue Counts

- expired_replacement_player_candidate: `1`
- gray_area_public_backup_candidate: `1`
- loan_duplicate_needs_status_metadata: `2`
- loan_status_missing: `3`
- missing_player_profile_candidate: `10`
- player_profile_candidate_gap: `1`
- public_display_alias_review: `6`
- source_domain_change_candidate: `4`
- source_url_enrichment_needed: `1`
- stale_or_short_term_candidate: `1`
- stale_player_candidate: `2`
- stale_team_assignment_duplicate_identity: `5`

## Europe Source Map

- Official/no-verify rows are source-map candidates for later manual player research only.
- `operator_verify_required=yes` rows must be checked by a human before player-level candidate intake.
- Gray-area/non-official backups are parked and cannot be treated as official roster confirmation.

### Europe League Counts

- arkema_premiere_ligue_france: `13`
- frauen_bundesliga_germany: `15`
- liga_f_spain: `17`
- serie_a_women_italy: `13`
- wsl_england: `13`

### Europe Verify Counts

- no: `40`
- yes: `31`

## Safe Next Action

Use this board to decide which source/roster metadata rows need manual verification first. Do not write current roster/candidate state from this artifact. A later human-edited intake must explicitly authorize any registry change.
