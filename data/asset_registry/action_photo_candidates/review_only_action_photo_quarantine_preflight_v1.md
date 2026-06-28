# Review-Only Action Photo Quarantine Preflight v1

Generated: `2026-06-28T00:00:00+00:00`

Preflight board for manually researched action-photo URL/evidence rows. This tells Mike which rows are ready for a human `download_approved=yes` decision under the local-download law. It does not download files, approve assets, write headshots, create `.approved` markers, move files to publish-ready lanes, or publish.

## Summary

- Preflight rows: `10`
- Ready for human download decision: `0`
- Lead-only / research return missing: `10`
- Validation issues: `0`
- Rows with `download_approved=yes`: `0`
- Review-only rows: `10`
- Publish-ready rows: `0`

## Required Fields For Any Future Human Download Decision

- `download_approved`
- `source_url`
- `entity_id`
- `rights_class`
- `identity_confidence`
- `intended_review_only_use`
- plus candidate/evidence fields: `candidate_photo_url`, `evidence_url`, `identity_anchor_url`

## Missing Field Counts

- `candidate_photo_url`: `10`
- `entity_id`: `10`
- `evidence_url`: `10`
- `identity_anchor_url`: `10`
- `identity_confidence`: `10`
- `intended_review_only_use`: `10`
- `rights_class`: `10`
- `source_url`: `10`

## Queue Preview

| Preflight ID | Queue ID | Ready? | Lead Status | Action Status | Identity Status | Missing Fields | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| APQP001 | APQ001 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP002 | APQ002 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP003 | APQ003 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP004 | APQ004 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP005 | APQ005 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP006 | APQ006 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP007 | APQ007 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP008 | APQ008 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP009 | APQ009 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP010 | APQ010 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
