# Review-Only Action Photo Candidate Intake

Generated: `2026-06-28T18:03:21.279620+00:00`

Human-editable intake for future action/moment photo candidates. This packet stores research metadata only. It does not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or create a publish-ready lane.

## Local Download Law

- A future download is eligible only when a human-edited row has `download_approved=yes` plus `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` filled.
- Any future file must land under `data/assets/quarantine/review_only_candidates/`.
- Download approval is not asset approval; separate human visual/identity/rights approval is still required.
- Generated rows default to `download_approved=no` and are not render-ready.

## Deep Research Paste Note

Ask ChatGPT Pro or Gemini to collect candidate URLs, source domains, source type, rights class, player/team identity proof, event context, action relevance, and why the moment would help future review renders. Do not ask it to download images, scrape photo files, fill approval fields, or claim publish readiness.

## Summary

- Intake template rows: `3`
- Rows with `download_approved=yes`: `0`
- Validation issues: `0`
- Quarantine root: `data/assets/quarantine/review_only_candidates`

## Source Types

- gray_area_public_lead: `1`
- official_or_league_public_page: `1`
- reputable_media_or_wire_lead: `1`

## Board Preview

| Rank | Source Type | Sport | League | Team | Player | Source URL | Download Approved | Manual Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AP01 | official_or_league_public_page |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP02 | reputable_media_or_wire_lead |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
| AP03 | gray_area_public_lead |  |  |  |  |  | no | Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review. |
