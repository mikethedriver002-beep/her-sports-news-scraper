# HSD Phase 6I Final Score Template Polish

Phase 6I is the targeted follow-up to Phase 6H.

The Tonight A handoff lane is close. The remaining blocker is Final Score A/B/C visual readiness.

## Scope

Phase 6I targets only these final-score templates:

- `hsd_game_recap_final_score_a`
- `hsd_game_recap_final_score_b`
- `hsd_game_recap_final_score_c_story`

It does not enable production cutover and does not auto-publish.

## Why this exists

Phase 6H showed that Final Score rows were structurally clean enough for live review, but still below public-mockup release thresholds. Some final-score rows were already visually close, so Phase 6I adds a more specific final-score polish check instead of continuing to judge all templates only by global image-similarity score.

## Renderer v4.4 changes

- Adds `final_score_polish_status`, `final_score_polish_score`, and `final_score_polish_reasons` into the Renderer v4 manifest.
- Strengthens final-score metadata fallback without inventing results.
- Keeps scores and winner/loser order tied to source fields.
- Keeps exact team-logo requirement.
- Keeps all outputs review-only.
- Keeps human render-hash approval required before handoff.

## Gate change

Phase 6I does not lower live safety requirements. Final Score rows still need:

- source truth pass
- exact approved team logos
- no text-logo fallback
- no fixture player asset
- zero placeholder layers
- zero zone overflow
- passed mask compliance
- human visual approval by render hash

Phase 6I adds a final-score-specific release-review path:

- public-mockup fidelity may remain below the old release threshold
- but Final Score A/B/C can become `release_ready_recommended` if `final_score_polish_status` passes and the render remains technically clean

## Expected result

The expected first live-data result is:

```json
{
  "renderer_version": "v4.4-phase6i-final-score-template-polish",
  "source_truth_status": "passed_source_truth_guard",
  "asset_preparation_status": "passed_live_asset_preparation",
  "production_cutover_allowed": false,
  "auto_publish_allowed": false
}
```

If Final Score A/B/C rows become release-ready recommended, they still must be reviewed visually and approved by hash before limited handoff.
