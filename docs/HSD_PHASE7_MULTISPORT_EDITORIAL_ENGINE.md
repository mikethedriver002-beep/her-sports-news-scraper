# HSD Phase 7: Multi-Sport Editorial Engine

## Why this is Phase 7

Phase 6M solved asset continuity: missing logos and verified player images no longer need to crash rendering. The next change is larger than a Phase 6 polish step because it establishes a shared editorial and rendering contract across multiple sports.

Phase 7 therefore replaces the proposed Phase 6N name.

## Primary outcomes

### WNBA

Phase 7 replaces generic Tonight and TEAM SPOTLIGHT fallback copy such as:

- `WHO HAS THE EDGE TONIGHT?`
- `TEAM IDENTITY`
- `MATCHUP IMPACT`
- `KEY EDGE`
- `PACE • STARS • LATE-GAME EDGE`

with deterministic matchup-specific language. Example shapes include:

- `DALLAS OR SEATTLE: WHO SETS THE PACE?`
- `CAN DALLAS FORCE SEATTLE TO ADJUST?`
- `DALLAS' TEST`
- `WHAT HAS TO TRAVEL TONIGHT?`

No statistics, injuries, player identity, form, or tactical claims are invented.

### Other sports

Phase 7 activates the shared editorial review-card renderer for:

- NWSL
- USWNT
- Women's Tennis
- LPGA
- NCAA Softball
- Women's Volleyball

Every sport has sport-specific language rather than a renamed basketball template. Fixture audit produces preview and result cards for every supported sport.

## Live-source status

WNBA remains connected to the existing automated live pipeline.

The other sports now accept live, verified content through two existing/manual-compatible routes:

1. `manual_workflow_content_packets.csv` / `.jsonl`
2. Phase 7 normalized events in `data/phase7/live_events.json` or `operator/inbox/phase7_live_events.jsonl`

This is a real renderer and packet integration. It is not yet an automated live scraper for all six additional sports. Non-WNBA cards remain review-only until each sport receives a dedicated source-truth and handoff lane.

## Safety contract

- Fixture events cannot enter live mode.
- No fake official logos are created.
- Missing identity assets use clearly labelled HSD badges or no-photo nameplates.
- Non-WNBA cards do not enter the WNBA live handoff lane.
- Human visual approval remains required.
- Production cutover remains disabled.
- Auto-publish remains disabled.

## Workflow

`HSD V5 Phase 7 Multi-Sport Editorial Engine`

PR checks run `fixture_audit` with strict validation. After fixture acceptance and merge, run `live_data` on `main` with `strict: false` for the first current-data audit.

## Acceptance standard

Fixture acceptance requires:

- all seven sports present;
- preview and result fixtures for every sport;
- zero generic/banned editorial phrases;
- all Phase 6M WNBA safety and visual gates still passing;
- all fallback cards labelled review-only;
- no production or auto-publish permission.
