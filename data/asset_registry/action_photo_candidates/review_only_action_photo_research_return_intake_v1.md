# Review-Only Action Photo Research Return Intake v1

Generated: `2026-06-28T00:00:00+00:00`

Human-editable paste-back worksheet for URL/evidence rows returned from the action-photo research packet. This intake is the safe landing zone before any quarantine download decision; it does not download images, approve assets, change approval state, or make anything render-ready.

## What To Paste Back

Paste returned ChatGPT/Gemini/manual research values into `candidate_photo_url`, `evidence_url`, `evidence_summary`, `identity_anchor_url`, `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`, `notes`, and `operator_verify_required`. Leave generated rows blank until real research is returned.

## Human-Only Law

`download_approved=yes` remains human-edited only after `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` are filled. Any later file must land in `data/assets/quarantine/review_only_candidates/`. Download approval is not asset approval, and render-ready status remains separate.

## Validation Checks

- Unknown or duplicate `candidate_queue_id`
- Pasted return rows missing `evidence_url`, `source_url`, `identity_anchor_url`, `rights_class`, or `identity_confidence`
- `download_approved=yes` without all local-download-law fields
- `publish_ready=true`
- Approval, publish-ready, or render-ready language in pasted notes/status fields

## Summary

- Intake rows: `10`
- Validation issues: `0`
- Rows with pasted return data: `0`
- Rows with `download_approved=yes`: `0`
- Review-only rows: `10`
- Publish-ready rows: `0`

## Queue IDs

- `APQ001` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ002` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ003` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ004` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ005` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ006` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ007` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ008` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ009` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
- `APQ010` -> Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.
