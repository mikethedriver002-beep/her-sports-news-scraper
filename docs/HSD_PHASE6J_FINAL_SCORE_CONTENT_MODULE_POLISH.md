# HSD Phase 6J — Final Score Content Module Polish

Phase 6J addresses the visual-review failures that remained after Phase 6I.

It does not lower fidelity thresholds, does not auto-approve Final Score assets, does not enable production cutover, and does not touch the approved Tonight A layout.

## Artifact finding that triggered Phase 6J

The Phase 6I rerun correctly preserved only the existing Tonight A handoff approvals and kept every Final Score render out of handoff as `needs_fix`.

The remaining problems were content-module problems rather than source-truth or geometry failures:

- Final Score A could show an empty or weak `KEY PERFORMER` band.
- Final Score A takeaway copy could merely restate the score.
- Final Score B could pair a player image with no verified player stat line.
- Final Score C could show an underwritten `FINAL NOTE` band and a generic fixed prompt.

## Renderer v4.5 behavior

### Final Score A

- Uses a verified player-stat module only when a real named performer and explicit stats are present.
- Otherwise replaces the hollow performer band with a factual `GAME EDGE` module derived only from the verified final margin.
- Uses an editorial takeaway when real summary copy exists.
- Otherwise changes the lower band to a matchup-specific `YOUR TAKE` question instead of repeating the score.

### Final Score B

- Requires a matching real player asset, a real player name, and at least one explicit stat value.
- Downgrades to Final Score A when the verified player-stat package is incomplete.
- Never renders a decorative player card with an empty stat block.

### Final Score C Story

- Uses either a verified player-stat module or a factual `GAME EDGE` module.
- Replaces the generic fixed question with a margin-aware matchup prompt.
- Keeps all copy inside the approved Story zones.

## New gate

`scripts/validate_hsd_final_score_content_modules_v4.py` blocks:

- empty content-module titles or bodies;
- score-only fallback copy;
- generic `WHAT CHANGED THE GAME?` Story prompts;
- Final Score B without a verified player name and stat count;
- missing content-module metadata;
- content-module scores below policy.

## Safety

- Free only.
- No generated people.
- No invented player stats.
- No text-logo fallback in the live lane.
- Human visual approval remains mandatory by exact render hash.
- Production cutover remains false.
- Auto-publish remains false.
