# HSD Phase 6E Vertical Story Overflow Hotfix

This hotfix targets the failed Phase 6E run where the renderer validator blocked on:

```text
zone_overflow:hsd_game_recap_final_score_c_story:vertical_quick_final
```

## Cause

The Story Final Score C label used a very narrow side strip for `KEY PERFORMER`.
On GitHub's Linux runner, the selected Noto Sans Display font made `PERFORMER`
slightly wider than the slot at the minimum allowed size. The local fixture package
passed because local font fallback metrics were narrower.

## Fix

- Make `fit_font` respect the actual stroke width used at draw time.
- Replace the narrow `KEY PERFORMER` two-line label with two safe labels:
  `KEY` and `PLAYER`.
- Keep Renderer v4.2 clean-plate mode, review-only status, and near-post-ready
  cutover block unchanged.

## Expected result

The existing Phase 6E workflow should pass the renderer validation step:

```json
{
  "status": "passed_renderer_v4_validation",
  "blockers": [],
  "warnings": ["final_score_b_uses_fixture_only_reference_asset"]
}
```

Production cutover remains blocked. Human visual approval is still required.
