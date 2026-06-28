# HSD Renderer QA Baseline Critique - 2026-06-28

Review-only baseline for future renderer/game-intelligence PRs. This document does not approve drafts, change asset state, download files, publish, or create a publish-ready lane.

## Baseline Inputs

- Latest reviewed packet: `render_prep_1_chicago-sky-beat-portland-fire`
- Renderer version: `hsd-manual-review-renderer-v1.25.0-square-context-hierarchy`
- Renderer generated: `2026-06-28T00:19:28.246915+00:00`
- Command Center generated: `2026-06-28T00:19:30.616869+00:00`
- Preview freshness: `generated_from_current_handoff_packet`
- Manual visual QA status: `human_review_required`
- Automated holds: `0`
- Render paths:
  - `outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png`
  - `outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_story.png`
  - `outputs/local/latest/files/render_handoff_top_packet/review_drafts/draft_preview_square.png`

## Top 5 Defects To Improve

1. Score block hierarchy feels oversized and loosely aligned.
   - Evidence: score lanes dominate the middle of all formats; `render_visual_delta.csv` flags feed/public mockup `review_minor_drift` score `83` with worst zone `context_row`, story/public mockup `86` with worst zone `title`, and square/public mockup `77` with worst zone `context_row`.
   - Acceptance check: scores should keep equal right-edge alignment, consistent vertical baselines between teams, and enough team-name/score separation that the numbers feel intentional rather than dropped in.

2. Lower proof/context modules are readable but not editorially satisfying.
   - Evidence: QA passes text-zone heuristics, but the feed and square lower modules are cramped; square compresses proof and matchup angle into a thin footer band. Pixel proxy lower-module bright ratios were low: feed `0.0465`, story `0.0270`, square `0.0341`.
   - Acceptance check: lower modules should preserve body-copy readability at social preview size, avoid ellipsized editorial proof when possible, and maintain clear label/body hierarchy.

3. Current draft is logo-first; no athlete-led render is proven.
   - Evidence: manifest reports `safe_no_photo_fallback` and `photo_not_rendered` for feed, story, and square. The selected Chicago/Portland packet has `no_verified_stat_text`, `score_only_fallback_manual_context_required`, and content module `game_edge_fallback`.
   - Acceptance check: future athlete-led PRs should show at least one review-only athlete-led feed/story/square proof, or explicitly explain why the selected packet cannot render an athlete without manual identity/source evidence.

4. Background polish still reads as generic scaffolding, not premium sports editorial.
   - Evidence: background style is labeled `hsd_premium_sports_editorial_v4_dimensional`, but the visible diagonal shards, low-contrast grid, and heavy red/blue panels compete with the score block rather than supporting it.
   - Acceptance check: premium polish should add depth and brand atmosphere without muddying text zones; future comparisons should call out whether texture/noise helps the story or merely fills space.

5. Review-only overlays interfere with the editorial read.
   - Evidence: bottom footer red ratios are high in the bottom 7 percent of each image: feed `0.5968`, story `0.4200`, square `0.5106`. The top-right `REVIEW DRAFT ONLY` badge and bottom banner both compete with the card hierarchy, especially in square.
   - Acceptance check: review-only markers must remain obvious but should not dominate the lower editorial modules or force square content into a cramped safe area.

## Recommended Acceptance Checks For Next PRs

- Grid: team rows, logo boxes, and score boxes align to a visible grid across feed/story/square; no row appears shifted or squeezed relative to its partner.
- Score: score numerals are large enough to anchor the graphic but do not overpower team names or lower proof modules.
- Copy: lower proof/context cards keep readable body copy without relying on ellipsis for the primary editorial claim.
- Athlete path: renderer manifest proves either `photo_rendered`/review-variant usage or a clear `photo_not_rendered` reason tied to missing verified stat/athlete evidence.
- Background: visual QA or PR notes explicitly compare background polish against the premium editorial target, not just pass/fail image nonblankness.
- Overlay: review-only markers stay present, but footer/top badge footprint does not consume the working editorial hierarchy.
- Guardrails: every future improvement remains review-only, with `auto_publish=false`, `publish_ready=false`, no downloads, and no approval-state changes.

## Current Go/No-Go Read

The current draft is technically openable and fresh, but it should not be treated as a visual-quality benchmark. It is a review-only baseline showing what future renderer and games packets need to beat: cleaner grid discipline, stronger editorial hierarchy, quieter overlays, more premium background depth, and a demonstrated athlete-led path when evidence supports one.
