# Review-Only Action Photo Candidate Intake

Generated: `2026-06-28T19:18:57.609143+00:00`

Human-editable intake for future action/moment photo candidates. This packet stores research metadata only. It does not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or create a publish-ready lane.

Every discovered item is a candidate lead until a human verifies identity, source provenance, and rights posture.

## Local Download Law

- A future download is eligible only when a human-edited row has `download_approved=yes` plus `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`, `source_category`, photographer credit or `credit_not_visible_manual_review`, and `manual_reviewer` filled.
- Any future file must land under `data/assets/quarantine/review_only_candidates/`.
- Download approval is not asset approval; separate human visual/identity/rights approval is still required.
- `social_uncleared`, `third_party_creator_uncleared`, `gray_area_lead_only`, and `reject_do_not_pursue` rows cannot be download-approved by this validator.
- Generated rows default to `download_approved=no` and are not render-ready.

## Deep Research Paste Note

Ask ChatGPT Pro or Gemini to collect candidate URLs, source domains, source category, rights clues, player/team identity proof, event context, action relevance, credit lines, and why the moment would help future review renders. Do not ask it to download images, scrape photo files, fill approval fields, or claim publish readiness.

## Summary

- Intake template rows: `5`
- Rows with `download_approved=yes`: `0`
- Validation issues: `0`
- Quarantine root: `data/assets/quarantine/review_only_candidates`

## Source Categories

- editorial_wire: `1`
- gray_area_public_lead: `1`
- official_league_gallery: `1`
- official_team_gallery: `1`
- reputable_newsroom_gallery: `1`

## Board Preview

| Rank | Source Category | Source Name | Sport | League | Team | Player | Source URL | Download Approved | Manual Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AP01 | official_team_gallery |  |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP02 | official_league_gallery |  |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP03 | editorial_wire |  |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP04 | reputable_newsroom_gallery |  |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP05 | gray_area_public_lead |  |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
