# HSD Phase 6G — Production Polish and Live Post-Ready Gate

Phase 6G separates three different meanings that earlier phases intentionally kept apart:

1. **Fixture proof** — validates renderer mechanics and cannot enter the live lane.
2. **Near-post-ready** — clean plates, masks, dimensions, and fidelity pass, but real assets and live approval may still be missing.
3. **Live post-ready** — a real source event with exact team logos, real player assets where required, a passing technical gate, and explicit approval of the exact live render hash.

## Visual polish requirements

A live candidate must have:

- a non-fixture source event;
- source-truth guard status `passed_source_truth_guard`;
- two exact approved team logos and no text-logo fallback;
- no fixture-only player asset;
- a real player asset for player variants;
- zero placeholder layers;
- zero zone overflow;
- passing dynamic-mask compliance;
- the template-specific live fidelity threshold;
- no TBA, sample, placeholder, or fixture copy tokens;
- a human decision bound to the exact render SHA-256.

## Safety boundary

Passing Phase 6G permits only a limited operator handoff under:

`outputs/latest/HSD_LIVE_POST_READY/`

It does not publish, schedule, upload to social media, or enable automatic production cutover.

## Workflow modes

- `fixture_audit`: proves that previously approved fixture hashes cannot escape into the live lane.
- `live_data`: rebuilds current live data and assets, produces candidate renders, and waits for a separate live visual-approval decision file.

The live decision file is:

`config/graphics/v4/live_post_ready/live_visual_approval_decisions_v4.csv`
