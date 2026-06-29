# Review-Only Action Photo Research Return Paste Worksheet v1

Generated: `2026-06-28T00:00:00+00:00`

Copy/paste-friendly landing worksheet for manual or external action-photo research returns. It places sport/entity/source context beside the exact return fields Mike should paste, then names what remains missing before a row can move only to later human download-decision review.

## Paste Schema

```csv
candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required
```

## Placeholder Example

`candidate_queue_id,<candidate_photo_page_url>,<evidence_page_url>,<caption_or_event_context>,<identity_anchor_url>,<source_page_url>,<entity_id>,<rights_class>,<identity_confidence>,<review_only_use>,<notes>,yes`

## Guardrails

- Generated rows keep URL/source/rights/identity fields blank unless a human-edited return intake already supplied them.
- Generated rows keep `download_approved=no` and do not fetch, download, approve, write assets, write headshots, create markers, move files, or publish.
- Candidate-ready means eligible only for later human download-decision review; it is not download approval and not asset approval.

## Summary

- Paste worksheet rows: `10`
- Validation issues: `0`
- Candidate-ready for later human download-decision review: `0`
- Rows missing source URL: `10`
- Rows missing candidate photo URL: `10`
- Download-approved yes rows: `0`

## Missing Field Counts

- `candidate_photo_url`: `10`
- `entity_id`: `10`
- `evidence_url`: `10`
- `identity_anchor_url`: `10`
- `identity_confidence`: `10`
- `intended_review_only_use`: `10`
- `operator_action_moment_review`: `10`
- `operator_crop_use_review`: `10`
- `rights_class`: `10`
- `source_url`: `10`

## Paste Rows

| ID | Queue | Sport | Entity | Source Lead | Missing Before Candidate-Ready | Ready? | Paste Target | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APRRP001 | APQ001 | basketball | WNBA | `{player_name} WNBA match action site:gettyimages.com` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP002 | APQ002 | basketball | WNBA | `{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP003 | APQ003 | soccer | NWSL | `{player_name} {club} NWSL isiphotos photoshelter action` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP004 | APQ004 | soccer | USWNT / U.S. Soccer | `{player_name} USWNT match action ISI Photos OR ussoccer photos` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP005 | APQ005 | basketball | NCAA Women Basketball | `{player_name} NCAA March Madness basketball ncaaphotos photoshelter` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP006 | APQ006 | softball | NCAA Women Softball | `{player_name} Women College World Series softball ncaaphotos photoshelter` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP007 | APQ007 | hockey | PWHL | `{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP008 | APQ008 | softball | AUSL / Pro Softball | `{player_name} AUSL softball action site:theausl.com OR Jade Hewitt` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP009 | APQ009 | tennis | WTA Tennis | `{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
| APRRP010 | APQ010 | golf | LPGA Golf | `{player_name} LPGA swing site:lpga.com OR site:gettyimages.com` | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url|operator_action_moment_review|operator_crop_use_review` | no | `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv` | Paste the missing URL/evidence/rights/identity/action/crop fields into the return intake; keep download_approved=no. |
