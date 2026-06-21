# HSD Phase 6K — Rendered Context, Story CTA, and Gate Integrity

## Trigger

The Phase 6J live-data artifact showed two classes of failure.

First, rendered copy remained below live quality:

- all five Final Score C Stories printed `LOCATION TBA`;
- the Story question/CTA panel remained weak;
- approved Tonight A previews visibly printed `TIME TBA` and `TV TBA` even though those tokens were already forbidden by policy.

Second, the handoff gate was not fail-closed:

- renderer validation was blocked;
- fidelity setup was blocked;
- near-post-ready setup was blocked;
- the live gate nevertheless reported handoff-ready and copied 14 approved assets.

## Additive implementation

Phase 6K leaves Phase 6J untouched. New wrapper scripts import the established Phase 6J implementation and activate a separate Phase 6K policy.

### Renderer v4.6

`scripts/generate_hsd_template_renderer_v4_phase6k.py`:

- omits unverified preview time/network instead of drawing TBA fallbacks;
- omits unverified final-score date/location context instead of drawing TBA fallbacks;
- dynamically lays out the remaining context segments;
- makes every Story prompt include the winner short name;
- replaces the oversized generic question treatment with `YOUR TAKE`, a larger matchup prompt, and `DROP YOUR READ BELOW.`;
- records the copy actually rendered in manifest metadata;
- counts forbidden rendered-copy tokens before near-ready candidacy;
- records every Final Score B route decision;
- keeps all outputs review-only.

### Conditional Final Score B

Final Score B remains valid only with:

- a matching real player asset;
- a real player name;
- at least one explicit verified stat.

When that package is incomplete, Renderer v4.6 records an intentional downgrade to Final Score A. The renderer, fidelity, and content-module validators excuse a missing B only when one valid downgrade route exists for every Final Score A source event. Partial, duplicate, malformed, or uncovered routing blocks the run. Fixture audit still requires B.

### Rendered-copy and Story validation

`scripts/validate_hsd_story_context_cta_v4.py` audits rendered-copy metadata for every template, then applies Story-specific checks:

- no forbidden rendered token;
- no context placeholder count;
- valid verified/omitted location state;
- nonempty context segment metadata;
- winner-specific prompt;
- exact `YOUR TAKE` label;
- nonempty CTA body;
- passing content module;
- zero placeholders and zero overflow;
- Story output file exists.

### Fail-closed live gate

`scripts/validate_hsd_live_post_ready_v4_phase6k.py` requires passing evidence from:

- clean-plate build;
- free live-asset preparation;
- renderer validation;
- fidelity setup;
- near-post-ready setup;
- final-score content modules;
- Story context/CTA.

If any report is missing or blocked, all rows receive a prerequisite blocker and limited handoff is disabled. Before every evaluation, stale live-handoff outputs are removed; the folder is recreated only from exact current-hash approvals after every current technical candidate has a completed current-hash decision. Partial current-hash approvals are recorded as deferred evidence, but no handoff files are exported while any candidate remains unreviewed. Prior decision rows without a current render-hash match are ignored, while blank current-hash rows remain unreviewed. Live source truth, exact logos, masks, release recommendation, and exact-hash human approval remain independently required by the inherited live gate.

## Safety invariants

- Free sources only.
- No generated people.
- No invented player stats.
- Exact approved logos required.
- Text-logo fallback blocked from live handoff.
- Fixture player assets blocked from live handoff.
- Human approval bound to exact render SHA-256.
- Production cutover false.
- Auto-publish false.

## Acceptance sequence

1. Install the additive files on a Phase 6K branch.
2. Run `fixture_audit`, `strict=true`.
3. Inspect the raw renders and all reports.
4. Run `live_data`, `strict=false`.
5. Review every changed Tonight and Story image.
6. Replace the decision CSV with the reviewed Phase 6K template so obsolete rows are removed.
7. Rerun `live_data`, `strict=true` only after the review CSV is updated.
