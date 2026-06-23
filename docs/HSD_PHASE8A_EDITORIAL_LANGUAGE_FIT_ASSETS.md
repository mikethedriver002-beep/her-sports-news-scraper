# HSD Phase 8A Editorial Language, Fit Safety, and Exact Assets

## Install

Create branch:

```text
hsd-v5-phase8a-editorial-language-fit-assets
```

Upload everything inside `UPLOAD_TO_REPO/` to the repository root on that branch, preserving paths.

Open a draft PR into `main`. The workflow should appear as:

```text
HSD V5 Phase 8A Editorial Language Fit Assets / phase8a-editorial-fit-assets
```

Run/inspect `fixture_audit` first. Do not merge until the fixture artifact is audited.

## Scope

Phase 8A fixes the visible editorial product quality problems:

- replaces generic Tonight and spotlight copy with sport-specific phrase libraries;
- adds fit-safe ranked variants for CTA/debate/watch zones;
- adds duplicate-clause validation so CTA/body do not repeat the same thought;
- adds a WNBA exact-logo registry gate and explicit Sparks repair policy;
- preserves Phase 6M asset assurance, human review, artifact-only output, and auto-publish off.

Phase 8A does not claim full non-WNBA automated collection. That starts in Phase 8B/8C/8D.

## Acceptance Criteria

- Zero generic-language hits.
- Zero duplicate clause hits.
- Zero fit-limit escapes for Tonight rows.
- Sparks exact-logo row present and approved.
- No fallback badge rows can be approved without human override.
