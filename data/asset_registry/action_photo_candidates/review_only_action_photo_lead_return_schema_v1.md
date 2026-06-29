# Review-Only Action Photo Lead Return Schema v1

Generated: `2026-06-28T00:00:00+00:00`

Normalized schema for Gemini, ChatGPT Pro, or manual researchers returning action-photo leads. This is a paste-back contract only: it does not fetch sources, download images, write image files, segment subjects, remove backgrounds, approve assets, or move anything toward publishing.

## Operator Contract

Use this schema to normalize leads before pasting rows into `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`. `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` may be returned as metadata for human review, but generated rows here keep local-download-law fields blank/no and remain review-only.

## Summary

- Schema rows: `18`
- Validation issues: `0`
- Rows with human yes in `download_approved`: `0`
- Review-only rows: `18`
- Publish-ready rows: `0`

## Field Groups

- action_quality: `2`
- context: `3`
- editorial_context: `1`
- guardrail: `2`
- identity: `3`
- operator_notes: `1`
- rights: `2`
- routing: `1`
- source_lane: `1`
- url_evidence: `2`

## Schema Preview

| ID | Return Field | Group | Required When | Allowed Values / Format | Prompt Note |
| --- | --- | --- | --- | --- | --- |
| APLRS001 | `source_discovery_id` | source_lane | always | `APSD### or operator_triage_only` | Carry the source discovery row that produced the lead. |
| APLRS002 | `candidate_queue_id` | routing | always | `APQ###` | Map the lead back to the existing action-photo queue. |
| APLRS003 | `candidate_photo_url` | url_evidence | always | `https URL to source/candidate page; not a downloaded file URL` | Return the page where the candidate action photo is visible or described. |
| APLRS004 | `evidence_url` | url_evidence | always | `https URL to recap, gallery, match report, or source context` | Return separate evidence for event, source, or caption context when available. |
| APLRS005 | `identity_anchor_url` | identity | always | `official roster/player profile, stats page, game sheet, or verified profile URL` | Give the operator a way to verify athlete identity outside the image. |
| APLRS006 | `sport` | context | always | `controlled human-readable sport label` | Echo the sport from the source discovery/queue context. |
| APLRS007 | `league_entity` | context | always | `league/team/event entity label` | Echo league or event entity used for research. |
| APLRS008 | `match_or_event_context` | context | when_visible_or_claimed | `date, opponent, tournament, game, round, or recap context` | Capture why the moment is tied to a real sports event. |
| APLRS009 | `athlete_name_claimed` | identity | when_visible_or_claimed | `athlete/person/team name as claimed by source` | Capture the source-caption identity claim without treating it as final approval. |
| APLRS010 | `action_moment_type` | action_quality | always | `drive/shot/save/swing/pitch/slide/celebration/defense/serve/putt/operator_fill` | Describe the sports action or emotion visible in the candidate. |
| APLRS011 | `emotional_intensity_label` | action_quality | always | `high/medium/low/unclear` | Rate visible emotion or editorial energy from source context only. |
| APLRS012 | `stat_or_context_text` | editorial_context | when_available | `short text tying image to score, stat, milestone, recap, or storyline` | Capture why the lead could support a premium editorial render later. |
| APLRS013 | `source_category` | rights | always | `editorial_wire/gray_area_public_lead/official_federation_or_tournament/official_league_gallery/official_social/official_team_gallery/reputable_newsroom_gallery/third_party_creator_public/verification_only_player_page` | Use the existing action-photo source taxonomy. |
| APLRS014 | `rights_class` | rights | always | `editorial_wire_rights_sensitive/gray_area_lead_only/newsroom_photo_rights_sensitive/official_partner_licensed_manual_review/official_review_needed/reject_do_not_pursue/social_uncleared/third_party_creator_uncleared` | Return conservative rights metadata for manual review. |
| APLRS015 | `identity_confidence` | identity | always | `confirmed_official/mismatch_or_unknown/probable/strong_context/weak` | Return conservative identity confidence. |
| APLRS016 | `intended_review_only_use` | guardrail | always | `review_only_action_photo_candidate_research/review_only_cutout_scoring_prep` | State that the lead is for review-only research or scoring prep. |
| APLRS017 | `operator_verify_required` | guardrail | always | `yes/no` | Default to yes when identity, rights, event context, or action quality need human confirmation. |
| APLRS018 | `review_notes` | operator_notes | optional | `short notes, limitations, or red flags` | Capture uncertainty and red flags for the operator. |
