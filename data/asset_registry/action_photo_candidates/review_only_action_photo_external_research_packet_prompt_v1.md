# HSD Review-Only Action-Photo External Research Packet

Generated: `2026-06-28T00:00:00+00:00`

Use this as the exact prompt/export glue for ChatGPT Pro, Gemini, or manual research. It summarizes the local review-only action-photo source-map board, candidate research packet, run bundle, and paste-back target without fetching sources or downloading assets.

## What Mike Should Do Externally

1. Open the local artifacts listed below.
2. Paste this prompt plus the relevant task rows into ChatGPT Pro, Gemini, or your manual research notes.
3. Ask for URL/evidence rows only using the exact CSV schema below.
4. Paste returned rows into `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`.
5. Ask Codex/conductor to validate the pasted intake before any separate human quarantine-download decision.

## Guardrails

- Review-only and artifact-only.
- No paid APIs.
- No source fetching or scraping from this local helper.
- No automatic downloads.
- No source auto-enablement.
- No email sending.
- No auto-approval or approval-state changes.
- No headshot writes.
- No `.approved` markers.
- No publish-ready lane or file movement.
- No publishing.
- Leave manual operator fields blank unless Mike/human research fills them.

## Local Artifacts To Attach Or Paste

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
- `quality_fit_board_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md`
- `quality_fit_board_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.csv`
- `quality_fit_board_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.json`
- `quality_fit_operator_cue_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md`
- `quality_fit_operator_cue_csv`: `data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.csv`
- `quality_fit_operator_cue_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.json`
- `external_research_prompt_md`: `data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md`
- `external_research_manifest_json`: `data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_manifest_v1.json`

## Exact Paste-Back Schema

```csv
candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required
```

Return only rows for the candidate IDs you can support with evidence. Use `source_url` as the candidate/source page URL, not a downloaded file. Set `operator_verify_required=yes` when identity, rights posture, event context, or roster truth still needs human confirmation.

## Research Scope

- Source-map board rows: `16`
- Source discovery board rows: `12`
- Research task rows: `10`
- Paste-back intake rows: `10`
- Bundle steps: `6`
- ChatGPT Pro tasks: `7`
- Gemini Pro tasks: `1`
- Manual research tasks: `2`

## External Research Prompt

You are advising HSD from a review-only action-photo research packet. Review the source-map board and candidate research packet. Return only candidate URL/evidence rows that can be pasted into the exact schema above. Separate official/free/public, reputable public, editorial/wire, social, third-party creator, and gray-area leads. Do not download images, save files, enable sources, approve assets, mark anything render-ready or publish-ready, write headshots, create `.approved` markers, or publish. Flag rights and identity uncertainty conservatively.

## Paste-Back Target

`data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`

After paste-back, validation must happen locally before any later human-edited quarantine-only download decision. Download approval is not asset approval.
