# HSD Phase 6L — Editorial Language and Visual Quirk Polish

Phase 6L is a focused quality pass after Phase 6K.

Phase 6K made the renderer safer and cleaner, but the public language could still sound like a fallback engine. Phase 6L blocks that.

## What changes

- Adds a score-safe HSD editorial language helper.
- Converts score-only fallback phrases into short public reads.
- Replaces weak language such as `closed with a 20-point victory`.
- Removes `MARGIN` as a public editorial punchline by suppressing the margin-render path.
- Adds a public copy quality gate before live handoff.
- Keeps Phase 6K safety gates intact.

## Approved language direction

Good:

- `Dallas Survives`
- `Phoenix Rolls`
- `Atlanta Pulls Away`
- `Minnesota Handles Business`
- `Wings 93, Sky 92.`

Not good:

- `Dallas survived the finish`
- `Phoenix Mercury closed with a 20-point victory.`
- `finished 17 points clear`
- `+20 MARGIN`
- `WHAT FUELED MERCURY'S SEPARATION?`

## Safety

- No invented stats.
- No invented venues.
- No generated people.
- No automatic publishing.
- No production cutover.
- Human visual approval remains required and SHA-bound.
