# Hockey/Softball Intake Readiness Summary

Generated: `2026-06-28T00:00:00+00:00`

Review-only summary of the existing hockey/softball logo and athlete manual intake CSVs. It validates the intake posture for operator visibility only; it does not download images, approve assets, write headshots or logos, create `.approved` markers, move files, or publish.

## Summary

- Intake groups: `4`
- Intake rows covered: `74`
- Logo source-reviewed rows: `20`
- Athlete source-pending rows: `54`
- Blank human-review metadata rows: `54`
- Unsafe guardrail rows: `0`
- Download-approved yes rows: `0`

## Operator Path

- Logo groups are source-reviewed, identity-confirmed, and still held because local logo candidate assets are missing.
- Athlete groups are intentionally source/identity/local-file pending; use the source verification checklist before editing athlete intake rows.
- Generated future download-law fields remain `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.
- Keep approval, publish, movement, headshot/logo writes, and `.approved` marker fields false/held unless a later explicit human-edited intake workflow authorizes a separate step.

## Intake Groups

| Order | Sport | Asset | Rows | Source yes | Source no | Metadata blank | Unsafe | Readiness | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IR01 | womens_hockey | logo | 13 | 13 | 0 | 0 | 0 | source_review_recorded_waiting_for_local_logo_asset | local_logo_asset_missing_before_renderer_trust |
| IR02 | womens_hockey | athlete_photo | 36 | 0 | 36 | 36 | 0 | source_and_identity_review_pending_waiting_for_named_local_athlete_asset | named_athlete_identity_and_local_headshot_candidate_missing |
| IR03 | softball | logo | 7 | 7 | 0 | 0 | 0 | source_review_recorded_waiting_for_local_logo_asset | local_logo_asset_missing_before_renderer_trust |
| IR04 | softball | athlete_photo | 18 | 0 | 18 | 18 | 0 | source_and_identity_review_pending_waiting_for_named_local_athlete_asset | named_athlete_identity_and_local_headshot_candidate_missing |
