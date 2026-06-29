# Review-Only Action Photo Research Run Bundle v1

Generated: `2026-06-28T00:00:00+00:00`

Operator alert bundle for running the existing action-photo research packet and pasting results into the return intake. This is artifact-only glue: it does not send email, download images, approve assets, mark render-ready state, or publish.

## Artifact Paths

- `source_map_board_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md`
- `source_map_board_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.csv`
- `source_map_board_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.json`
- `source_discovery_board_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.md`
- `source_discovery_board_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.csv`
- `source_discovery_board_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.json`
- `operator_worksheet_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.md`
- `operator_worksheet_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv`
- `operator_worksheet_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.json`
- `research_packet_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md`
- `research_packet_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.csv`
- `research_packet_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.json`
- `return_intake_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.md`
- `return_intake_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- `return_intake_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json`
- `external_research_prompt_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md`
- `external_research_manifest_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_manifest_v1.json`

## Email-Ready Text

Subject: Run HSD review-only action-photo research packet

```text
Mike, run the review-only action-photo research packet next. Open data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md, send the ChatGPT Pro/Gemini/manual prompts as marked, and paste returned CSV rows into data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv. Do not download images, approve assets, mark anything render-ready, or publish. After paste-back, ask the conductor to validate rows before any human quarantine-download decision.
```

## What Not To Do

- Do not download or fetch image files.
- Do not send email automatically from this lane.
- Do not approve assets or change approval state.
- Do not mark rows render-ready or publish-ready.
- Do not move files into publish-ready lanes or publish.

## Next Conductor Action

After Mike pastes returned rows into the intake, validate pasted rows. Only human-edited rows that satisfy `download_approved=yes` plus `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` can proceed toward a later quarantine-only candidate download. Approval/render-ready remains separate.

## Summary

- Bundle steps: `6`
- Validation issues: `0`
- Rows with `download_approved=yes`: `0`
- Review-only rows: `6`
- Publish-ready rows: `0`

## Bundle Steps

### APRB001: chatgpt_pro

- Scope: 7 research-packet task(s) marked chatgpt_pro
- Instruction: Open the research packet Markdown, copy each chatgpt_pro task prompt, run it in ChatGPT Pro, and request CSV-in-code-block URL/evidence rows only.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Next: After Mike pastes rows back, run the return-intake validator before any quarantine-download decision.

### APRB002: gemini_pro

- Scope: 1 research-packet task(s) marked gemini_pro
- Instruction: Open the research packet Markdown, copy each gemini_pro task prompt, run it in Gemini Pro, and request CSV-in-code-block URL/evidence rows only.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Next: After Mike pastes rows back, run the return-intake validator before any quarantine-download decision.

### APRB003: manual_research

- Scope: 2 research-packet task(s) marked manual_research
- Instruction: Use the research packet Markdown as a manual URL/evidence checklist; collect candidate page URLs, evidence URLs, identity anchors, and conservative rights/identity metadata only.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Next: After Mike pastes rows back, run the return-intake validator before any quarantine-download decision.

### APRB004: operator_worksheet

- Scope: Fill candidate source/context notes in the operator worksheet before paste-back
- Instruction: Open the operator worksheet CSV and fill only candidate URL, source/rights/context notes, event/date, athlete/team, crop/use-case, reviewer decision, and reviewer notes after manual inspection. Do not download image files.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv`
- Next: Keep download_approved=no; use the worksheet to decide which source/evidence rows are ready to paste into the return intake.

### APRB005: paste_back_intake

- Scope: Paste returned URL/evidence rows into the return intake CSV
- Instruction: Paste only URL/evidence schema fields returned by the research packet: candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Next: Validate pasted rows; rows with missing evidence, identity anchor, source URL, rights class, or identity confidence stay held for manual review.

### APRB006: conductor_validation

- Scope: Validate pasted rows, then stop for human download approval decisions
- Instruction: Run focused action-photo validation after paste-back. Do not download, approve, render, publish, or move files. Human-edited download_approved=yes remains a separate quarantine-only step.
- Paste back: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Next: Only human-approved rows with source_url, entity_id, rights_class, identity_confidence, intended_review_only_use, and quarantine target can proceed toward a later quarantine candidate download.
