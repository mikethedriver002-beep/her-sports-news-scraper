# Review-Only Action Photo Download Decision Queue v1

Generated: `2026-06-28T00:00:00+00:00`

Human decision queue for action-photo candidates after URL/evidence paste-back and quarantine preflight. Generated rows are review-only and do not authorize file handling. Any later quarantine-only file step requires the manual fields listed below and remains separate from asset approval.

## Summary

- Decision rows: `10`
- Ready for human download decision: `0`
- Needs return fix first: `0`
- Needs research return first: `10`
- Download-approved yes rows: `0`
- Validation issues: `0`

## Required Human Edits Before Any Later Quarantine Download

- `download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|human_download_decision|manual_reviewer|reviewed_at_utc`
- Allowed destination only: `data/assets/quarantine/review_only_candidates/`
- Do not move candidates into approved asset folders.
- Do not write headshots, `.approved` markers, publish-ready state, or publishing actions.

## Queue Preview

| Decision ID | Queue ID | Priority | Ready? | Missing Fields | Destination | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| APDD001 | APQ001 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD002 | APQ002 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD003 | APQ003 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD004 | APQ004 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD005 | APQ005 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD006 | APQ006 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD007 | APQ007 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD008 | APQ008 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD009 | APQ009 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
| APDD010 | APQ010 | P3_run_research_before_decision | no | `source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|candidate_photo_url|evidence_url|identity_anchor_url` | `data/assets/quarantine/review_only_candidates` | Run the review-only research packet and paste URL/evidence-only returns before considering a human quarantine-download decision. |
