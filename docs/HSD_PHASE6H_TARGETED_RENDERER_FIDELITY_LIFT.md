# HSD Phase 6H Targeted Renderer Fidelity Lift

Phase 6H is a targeted polish pass after the Phase 6G live-data gate.

It does not enable production cutover, does not auto-publish, and does not treat fixture approvals as live approvals.

## Why this exists

Phase 6G proved the live-data lane was working, but surfaced two renderer-quality issues:

1. Final-score live-data rows had blank derived headlines and duplicated output filenames such as `item__final_a.png`.
2. Final Score A/B/C rows were hard-blocked by a single public-mockup fidelity threshold, even when they passed source truth, exact-logo, mask, placeholder, and overflow checks.

Phase 6H fixes the renderer metadata issue and separates technical live candidacy from release-grade handoff.

## Renderer v4.3 changes

- Adds deterministic derived headlines for final rows when `headline` is missing.
- Parses live `final_score_display` strings such as `Washington Mystics 88 · Connecticut Sun 81`.
- Uses `home_score` / `away_score` and winner/loser teams to populate the correct score order.
- Uses unique output slugs from `event_id`, `event_uid`, `canonical_key`, or headline to prevent same-name overwrite collisions.
- Keeps all output review-only and still requires Phase 6G/6H live visual approval.

## Live gate changes

The live gate now separates:

- **Technical floor**: the render is clean enough to enter live visual review.
- **Release recommendation threshold**: the render is polished enough to be eligible for limited operator handoff after approval.

Final-score templates may enter visual review if they meet the technical floor, but they cannot enter operator handoff until they meet the higher release threshold.

## Expected first live-data result

Phase 6H should increase the number of technical live candidates by fixing score parsing, output uniqueness, and marginal Tonight A thresholds.

Expected status remains conservative:

```json
{
  "production_cutover_allowed": false,
  "auto_publish_allowed": false
}
```

## Modes

- `fixture_audit`: proves fixture/test rows do not escape into the live lane.
- `live_data`: runs current live data and reports release-ready vs needs-polish candidates.

## Next phase after Phase 6H

If live_data shows final-score rows as `needs_visual_polish_before_handoff`, Phase 6I should focus on final-score template-specific polish rather than additional workflow gates.
