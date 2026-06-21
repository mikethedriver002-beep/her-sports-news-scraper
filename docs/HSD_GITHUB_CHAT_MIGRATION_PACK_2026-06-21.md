# HSD GitHub Chat Migration Pack — 2026-06-21

## Repository

- Repository: `mikethedriver002-beep/her-sports-news-scraper`
- Default branch: `main`
- Reconstructed main head at takeover: `569ae22946dbc0a72ee469a2b329ae47ec507eb8`
- Active continuation branch: `hsd-v4-phase6k-story-handoff-polish`

## Corrected project history

The prior chat handoff said Phase 5B was approximately 80–85% complete and not merge-ready. That note was stale. GitHub history showed that Phase 5B and its hotfix had already merged, followed by Phases 6A through 6J.

The latest completed development phase at takeover was Phase 6J, merged in PR #27. A subsequent main-branch commit updated the live visual approval decisions.

## Current release state

Phase 6J feed and Threads Final Score A renders received limited, hash-bound operator approvals. Final Score Story renders remained `needs_fix`.

The shared Story blockers were:

1. `LOCATION TBA` was visibly rendered when no verified venue existed.
2. The bottom Story question/CTA hierarchy remained generic and too weak.

Production cutover is not enabled. Auto-publish is not enabled. Human visual approval remains mandatory.

## Root cause

Renderer v4.5 inserted `LOCATION TBA` inside `render_final_c`. Its generic placeholder counter inspected source-row values rather than the fallback copy drawn by the renderer. The live gate also scanned only a limited set of manifest text fields. The human reviewer therefore caught a real rendered-copy validation blind spot.

## Phase 6K scope

Phase 6K is intentionally narrow:

- omit unknown Story date/location values instead of drawing TBA copy;
- strengthen the Story CTA into a matchup-specific `YOUR TAKE` module;
- add rendered context and CTA metadata to the manifest;
- add a dedicated Story handoff validator;
- extend the live gate with Phase 6K Story checks;
- preserve existing feed and Threads image behavior;
- require new exact-hash review for changed Story images.

## Files introduced by Phase 6K

- `scripts/hsd_phase6k_story_handoff.py`
- `scripts/generate_hsd_template_renderer_v4_phase6k.py`
- `scripts/validate_hsd_final_score_story_handoff_v4.py`
- `scripts/validate_hsd_live_post_ready_v4_phase6k.py`
- `config/graphics/v4/live_post_ready/live_post_ready_policy_phase6k_v4.json`
- `tests/test_renderer_v4_phase6k_story_handoff.py`
- `.github/workflows/hsd-v4-phase6k-story-handoff-polish.yml`
- `docs/HSD_PHASE6K_FINAL_SCORE_STORY_HANDOFF_POLISH.md`

## Required acceptance sequence

1. Run the Phase 6K pull-request fixture audit.
2. Confirm regression and Phase 6K tests pass.
3. Inspect the Story artifact/contact sheet visually.
4. Confirm no Story contains TBA/unknown context copy.
5. Confirm CTA hierarchy and wrapping are production-quality.
6. Run live-data mode when source packets contain finals.
7. Add fresh visual decisions for changed Story SHA-256 values.
8. Merge only after the branch is green and visual review passes.

## Non-negotiable safeguards

- Do not enable automatic posting.
- Do not enable production cutover.
- Do not reuse an approval across a changed image hash.
- Do not invent a venue, player statistic, or athlete identity.
- Do not weaken source-truth, exact-logo, mask, overflow, fidelity, or human-review gates to obtain a pass.
