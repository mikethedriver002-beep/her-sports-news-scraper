# Hockey/Softball Quarantine Download Intake

Generated: `2026-06-28T06:27:39.296763+00:00`

Review-only, human-edited intake for a future quarantine-only local asset candidate step. This generator does not download logos or athlete photos, write headshots, create `.approved` markers, approve identities, move files, publish, or create a publish-ready lane.

A row is not eligible for any future quarantine download unless a human edits the CSV with `download_approved=yes`, source URL, entity ID, rights class, identity confidence, intended review-only use, and a separate approval step remains required after local review.

## Summary

- Intake rows: `74`
- Rows with download_approved=yes: `0`
- Default download_approved value: `no`
- Quarantine folder only: `data/assets/quarantine/review_only_candidates`
- Download intake CSV: `data/asset_registry/hockey_softball_quarantine_download_intake.csv`
- Policy canonical intake template: `operator/inbox/review_only_asset_download_intake.csv`

## Buckets

- source_only_athlete_needs_manual_source_review_first: `54`
- source_reviewed_waiting_for_human_download_intake: `20`

## Operator Rules

1. Do not download from this packet.
2. A future download tool may only consider human-edited rows where `download_approved=yes` and the required source, entity, rights, identity, and intended-use fields are complete.
3. Any future file must land under `data/assets/quarantine/review_only_candidates/` and still requires separate visual identity and asset approval review.
4. Keep `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads` false in this generated intake.
