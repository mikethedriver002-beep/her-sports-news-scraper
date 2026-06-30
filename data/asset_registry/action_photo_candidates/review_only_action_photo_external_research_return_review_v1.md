# Review-Only Action Photo External Research Return Review v1

Generated: `2026-06-30T00:00:00+00:00`

Reviews Mike's supplied external action-photo research return CSV against the shared action-photo return intake. This artifact does not write intake rows, fetch sources, download images, approve candidates or assets, write headshots/cutouts/logos, create `.approved` markers, move files, enable sources, or publish.

## Summary

- External return CSV: `C:\Users\Mike\Desktop\deep-research-report-md.md`
- Shared intake CSV: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Expected APQ rows: `10`
- External returned rows: `8`
- Missing external APQ rows: `2`
- Direct image / hotlink candidate URL holds: `8`
- Identity vocabulary mismatch rows: `8`
- Rows ready only for later human download-decision review: `0`
- Generated download approvals: `0`
- Validation issues: `0`

## Buckets

- external_return_direct_image_and_identity_vocab_hold: `8`
- external_return_missing: `2`

## Review Rows

| Review | Queue | Returned? | Direct Image Hold | Identity | Missing | Bucket | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| APER001 | APQ001 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/world/us/grow-up-caitlin-clark-commits-five-turnovers-fever-loss-sun-2025-06-18/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER002 | APQ002 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.wnba.com/watch/video/caitlin-clark-dials-from-long-distance-3); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER003 | APQ003 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/sports/soccer/washington-spirit-star-f-trinity-rodman-back-out-indefinitely-2025-04-19/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER004 | APQ004 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/sports/soccer/trinity-rodman-scores-uswnt-blanks-brazil-2025-04-06/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER005 | APQ005 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://uconnhuskies.com/sports/womens-basketball/roster/azzi-fudd/14968); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER006 | APQ006 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://texastech.com/sports/softball/roster/nijaree-canady/13952); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER007 | APQ007 | no | no | identity_missing | `candidate_photo_url/evidence_url/evidence_summary/identity_anchor_url/source_url/entity_id/rights_class/identity_confidence/intended_review_only_use` | external_return_missing | Ask the research operator to supply this APQ row before any import-review or quarantine-decision work. |
| APER008 | APQ008 | no | no | identity_missing | `candidate_photo_url/evidence_url/evidence_summary/identity_anchor_url/source_url/entity_id/rights_class/identity_confidence/intended_review_only_use` | external_return_missing | Ask the research operator to supply this APQ row before any import-review or quarantine-decision work. |
| APER009 | APQ009 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/sports/tennis/gauff-wary-grass-record-wimbledon-begins-2026-06-27/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
| APER010 | APQ010 | yes | yes | identity_vocabulary_requires_operator_normalization | `` | external_return_direct_image_and_identity_vocab_hold | Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/sports/golf/nelly-korda-maintains-competitive-mindset-while-pursuing-rare-heights--flm-2026-06-25/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. |
