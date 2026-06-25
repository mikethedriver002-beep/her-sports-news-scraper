# HSD Morning Source Discovery Board

Date: 2026-06-24

## Decision

The command center now has one morning source discovery queue:

- Official/free sources.
- Wire sources.
- Free cross-check sources.
- Reputable gray-area and public social discovery leads.
- Manual inbox leads.

The board is generated during local `review` and `full` runs as:

- `story_candidates_manual.csv`
- `story_candidates_manual.jsonl`
- `manual_story_inbox_report.md`
- `story_candidates_discovery.csv`
- `story_candidates_discovery.jsonl`
- `discovery_sources_report.md`
- `morning_source_discovery_board.csv`
- `morning_source_discovery_board.md`
- `morning_source_discovery_board.json`
- `morning_lead_promotion_recommendations.csv`
- `morning_lead_promotion_recommendations.md`
- `morning_lead_promotion_recommendations.json`
- `source_coverage_map.csv`
- `source_registry_intake_template.csv`
- `source_registry_intake_template.md`
- `source_registry_proposal_review.csv`
- `source_registry_proposal_review.md`
- `source_registry_proposal_draft.csv`
- `source_registry_proposal_draft.md`
- `source_registry_proposal_promotion_checklist.csv`
- `source_registry_proposal_promotion_checklist.md`
- `source_registry_update_worksheet.csv`
- `source_registry_update_worksheet.md`
- `source_registry_diff_review.csv`
- `source_registry_diff_review.md`
- `source_registry_verification_log.csv`
- `source_registry_verification_log.md`
- `source_registry_approval_packet.csv`
- `source_registry_approval_packet.md`
- `source_registry_patch_preview.csv`
- `source_registry_patch_preview.md`
- `source_registry_post_edit_validation.csv`
- `source_registry_post_edit_validation.md`
- `source_proposal_pack_readiness.csv`
- `source_proposal_pack_readiness.md`
- `source_proposal_packs.csv`
- `source_proposal_packs.md`
- `wnba_source_proposal_pack.csv`
- `wnba_source_proposal_pack.md`
- `nwsl_source_proposal_pack.csv`
- `nwsl_source_proposal_pack.md`
- `lpga_source_proposal_pack.csv`
- `lpga_source_proposal_pack.md`
- `pwhl_source_proposal_pack.csv`
- `pwhl_source_proposal_pack.md`

## Review Rules

Green official, wire, primary, and operator-verified rows can move into editor review. Free cross-check rows can support confidence, but official or wire sources win on conflict. Gray-area and social rows stay discovery-only until confirmed by official, wire, primary, or operator-verified evidence.

The board does not fetch private sources, bypass paywalls, use paid APIs, auto-run in GitHub, or auto-publish. It is a local/manual operator queue.

Review runs now refresh the intake layer first:

- Manual story inbox rows become run-scoped manual candidates.
- Free official and wire pages are sampled for public story links, not crawled as a publishing feed.
- The source registry audit writes `source_coverage_map.csv` and a coverage map in `source_registry_audit.json` so sport/league gaps such as missing PWHL official/team sources are visible for manual follow-up.
- Coverage gaps also produce `source_registry_intake_template.csv` and `.md` proposal worksheets. These rows are disabled, review-only, and do not update `config/source_registry.json`.
- Manual source proposals in `operator/inbox/source_registry_proposals.csv` produce `source_registry_proposal_review.csv` and `.md`. The review flags duplicate, paid/API, login-only, social-only, and unsafe proposed sources before any human updates the trusted source registry.
- Guided league proposal packs produce `source_registry_post_edit_validation.csv/.md`, `source_registry_patch_preview.csv/.md`, `source_registry_approval_packet.csv/.md`, `source_registry_verification_log.csv/.md`, `source_registry_diff_review.csv/.md`, `source_registry_update_worksheet.csv/.md`, `source_registry_proposal_promotion_checklist.csv/.md`, `source_registry_proposal_draft.csv/.md`, `source_proposal_pack_readiness.csv/.md`, `source_proposal_packs.csv/.md`, plus focused pack files such as `wnba_source_proposal_pack.csv/.md`, `nwsl_source_proposal_pack.csv/.md`, `lpga_source_proposal_pack.csv/.md`, and `pwhl_source_proposal_pack.csv/.md`. The checklist tells the operator which selected draft rows to verify/copy, hold, or discard before any trusted registry edit. The worksheet turns verify/copy rows into review-only registry change plans with proposed disabled JSON, before/after notes, and rollback notes. The diff review compares those proposed disabled source objects against `config/source_registry.json` for duplicate IDs, duplicate URLs/domains, risky trust bands, unsafe enablement, and missing rollback coverage before any human edit. The verification log gives the operator fill-in fields for URL checked, freshness result, duplicate decision, approval/hold outcome, and evidence notes. The approval packet summarizes only verification-log rows marked `approved_for_manual_registry_edit`, with exact JSON, evidence fields, and hold reasons for final human review. The patch preview turns ready approval-packet rows into side-by-side registry before/after guidance and copy/paste JSON instructions for a human. The post-edit validation report compares any human-added registry row back against the patch preview, flags drift, unsafe enablement, automation, publish-policy, paid/API, or login-only signals, and keeps the check read-only. The draft file stages selected pack rows with duplicate/freshness warnings preserved; the readiness report tells the operator which packs are ready for manual registry proposal review, need duplicate review, or need source freshness checks. These are curated free public official, team, tournament, and cross-check candidates for manual review only. The post-edit validation, patch preview, approval packet, verification log, diff review, worksheet, checklist, draft, and packs never import rows, enable sources, scrape private pages, use paid APIs, or publish.
- Top official and wire story links can be sampled once for public article metadata titles, dates, and short descriptions from signals such as OpenGraph, JSON-LD, or `<time datetime>`.
- Manual social inbox rows become discovery-only leads.
- Generic source scans remain `monitor_only` until a concrete lead appears.
- Discovery leads carry `quality_score`, `freshness_label`, `freshness_source`, `evidence_preview`, `freshness_score`, `urgency_score`, and `quality_reason` so current high-signal leads outrank stale or evergreen items.
- Related official and wire leads are grouped into `story_opportunity_*` fields so duplicate coverage becomes one operator-ready promotion recommendation while the original source rows stay reviewable.
- Story opportunities include a cleaner headline, an editorial angle, an advisory News-vs-Studio path, source coverage, confidence, confirmation, asset-readiness cues, and a suggested free second source for manual follow-up when the opportunity is not fully covered.

Article metadata sampling is capped by `HSD_DISCOVERY_MAX_ARTICLE_DATE_FETCHES_PER_SOURCE` and can be disabled with `HSD_DISCOVERY_ENABLE_ARTICLE_DATE_FETCH=false`. It uses free public page metadata only and does not publish, promote, or call paid APIs.

## Promotion Recommendations

Each source row now gets a manual promotion recommendation:

- `news_packet`: draft or refresh a News packet manually.
- `manual_story_candidate`: move the lead into manual story verification with evidence URLs and locked facts.
- `studio_brief`: manually draft a Studio brief after confirming facts and asset readiness.
- `cross_check_existing`: pair the source with a stronger lead.
- `monitor_only`: keep scanning; no concrete story lead yet.
- `no_promotion`: blocked or unusable source posture.

These are recommendations only. The generator does not write into `news_fact_packets.csv`, `story_candidates_manual.csv`, or `studio_bundle_queue.csv`.

## Command Center Impact

The daily command center now shows:

- Morning source row count.
- Gray/social lead count.
- Lead promotion count and News/manual/Studio split.
- Story opportunity count and grouped opportunity count.
- Publish-grade opportunity, source-check, and Studio asset-check counts.
- Source coverage gap and watch counts from the registry coverage map.
- Second-source suggestion counts for opportunities that need another official, wire, or reputable cross-check source.
- High-quality lead count and fresh lead count.
- A Sources tab with the morning board.
- A source coverage map showing official, team, wire, and cross-check coverage by sport/league.
- A source registry intake template for proposing free official/team/cross-check sources from coverage gaps without auto-enabling them.
- A source proposal review report showing holds and ready-for-registry-review rows before any trusted registry update.
- Lead promotion recommendations with metadata evidence previews, story angle, source coverage, readiness cues, suggested second-source checks, target artifacts, and next steps.
- A next-action item when a manual, social, discovery, or News Sync source lead needs review.

This makes the morning workflow less scattered: leads can come from free official sources, wire context, public gray-area/social discovery, or manual intake, but they all land in one review-safe place.
