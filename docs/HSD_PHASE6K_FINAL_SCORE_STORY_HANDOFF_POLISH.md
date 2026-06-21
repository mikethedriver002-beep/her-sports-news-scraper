# HSD Phase 6K — Final Score Story Handoff Polish

Phase 6K is the narrow follow-up to the Phase 6J visual review. Phase 6J successfully moved Final Score A feed and Threads assets into limited, hash-bound operator handoff, but every Final Score C Story remained `needs_fix`.

## Triggering review findings

The rejected Story renders shared two visible defects:

- the context row rendered `LOCATION TBA` when the source packet had no verified venue;
- the bottom question module remained too generic and visually weak for live HSD Story quality.

The first defect also exposed a validation blind spot. Renderer v4.5 counted placeholders only from source-row values, while `LOCATION TBA` was inserted later by the drawing function. The automated placeholder gate therefore could not see the fallback that appeared in the image.

## Phase 6K behavior

### Adaptive Story context

- Draw verified date, verified location, and league when available.
- Omit an unknown location instead of drawing `LOCATION TBA`.
- Use `FINAL • WNBA` when both date and location are unavailable.
- Emit explicit context status, score, mode, reasons, and rendered-copy metadata into the manifest.

### Matchup-specific CTA hierarchy

- Every prompt includes the winning and losing matchup when both are known.
- Prompt language changes with the verified final margin.
- The old oversized question-mark block is replaced by a stronger `YOUR TAKE` rail.
- The prompt receives more usable space and a clear `DROP YOUR READ BELOW.` action line.
- Emit explicit CTA status, score, reasons, and prompt metadata into the manifest.

### Gate closure

The dedicated Story handoff gate blocks:

- any TBA, TBD, unknown, or equivalent context copy;
- missing Phase 6K renderer metadata;
- weak or generic CTA prompts;
- context or CTA scores below policy;
- content-module, template-polish, or overflow failures.

The Phase 6K live gate applies the same checks before an asset can become a technical live candidate.

## Compatibility

Phase 6K is installed as a narrow runtime patch over Renderer v4.5. The manifest keeps the v4.5 compatibility version so the established clean-plate, fidelity, and near-post-ready validators continue to run. It also records `effective_renderer_version: v4.6-phase6k-story-handoff-polish` so the new Story gate can require the patch explicitly.

## Safety and release policy

- Free-only sources and assets remain required.
- No generated people or invented statistics.
- Exact approved team logos remain required.
- Existing feed and Threads approvals remain valid only if their image hashes are unchanged.
- Every changed Story requires a fresh human approval bound to the new SHA-256.
- Production cutover remains false.
- Auto-publish remains false.
