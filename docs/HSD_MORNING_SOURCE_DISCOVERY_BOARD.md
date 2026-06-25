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

## Review Rules

Green official, wire, primary, and operator-verified rows can move into editor review. Free cross-check rows can support confidence, but official or wire sources win on conflict. Gray-area and social rows stay discovery-only until confirmed by official, wire, primary, or operator-verified evidence.

The board does not fetch private sources, bypass paywalls, use paid APIs, auto-run in GitHub, or auto-publish. It is a local/manual operator queue.

Review runs now refresh the intake layer first:

- Manual story inbox rows become run-scoped manual candidates.
- Free official and wire pages are sampled for public story links, not crawled as a publishing feed.
- The source registry audit writes `source_coverage_map.csv` and a coverage map in `source_registry_audit.json` so sport/league gaps such as missing PWHL official/team sources are visible for manual follow-up.
- Coverage gaps also produce `source_registry_intake_template.csv` and `.md` proposal worksheets. These rows are disabled, review-only, and do not update `config/source_registry.json`.
- Manual source proposals in `operator/inbox/source_registry_proposals.csv` produce `source_registry_proposal_review.csv` and `.md`. The review flags duplicate, paid/API, login-only, social-only, and unsafe proposed sources before any human updates the trusted source registry.
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
