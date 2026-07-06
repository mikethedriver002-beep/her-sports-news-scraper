# Review-Only Action Photo Quarantine Preflight v1

Generated: `2026-06-30T00:00:00+00:00`

Preflight board for manually researched action-photo URL/evidence rows. This tells Mike which rows are ready for a later human quarantine-download decision under the local-download law. It does not download files, approve assets, write headshots, create `.approved` markers, move files to publish-ready lanes, or publish.

## Summary

- Preflight rows: `12`
- Ready for human download decision: `3`
- Lead-only / research return missing: `9`
- Validation issues: `0`
- Human intake rows with a recorded yes download flag: `2`
- Generated preflight rows with a recorded yes download flag: `0`
- Review-only rows: `12`
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

- `candidate_photo_url`: `9`
- `entity_id`: `9`
- `evidence_url`: `9`
- `identity_anchor_url`: `9`
- `identity_confidence`: `9`
- `intended_review_only_use`: `9`
- `rights_class`: `9`
- `source_url`: `9`

## Queue Preview

| Preflight ID | Queue ID | Ready? | Lead Status | Action Status | Identity Status | Missing Fields | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| APQP001 | APQ001 | yes | research_return_pasted_preflight_only | action_photo_candidate | identity_ready_for_human_review | `` | Human intake records a yes download flag for quarantine-only review; this preflight still does not download files or approve assets. |
| APQP002 | APCS114 | yes | research_return_pasted_preflight_only | action_photo_candidate | identity_ready_for_human_review | `` | Human intake records a yes download flag for quarantine-only review; this preflight still does not download files or approve assets. |
| APQP003 | APQ002 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP004 | APQ003 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP005 | DRM002 | yes | research_return_pasted_preflight_only | action_photo_candidate | identity_ready_for_human_review | `` | Ready for a later human quarantine-download decision; do not download unless Mike separately records a quarantine-only approval in the intake and keeps the quarantine target. |
| APQP006 | APQ004 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP007 | APQ005 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP008 | APQ006 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP009 | APQ007 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP010 | APQ008 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP011 | APQ009 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
| APQP012 | APQ010 | no | lead_only_research_return_missing | missing_candidate_photo_url | identity_missing | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | Run the research bundle, paste URL/evidence rows into the return intake, then regenerate this preflight. |
