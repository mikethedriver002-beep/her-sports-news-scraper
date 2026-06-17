# HSD Reality Check Prompts

Use these at the top of repo, artifact, and build messages so the chat anchors to the latest state instead of repeating the previous step.

## General reality check

```txt
HSD REALITY CHECK.

Before answering, anchor to the latest user message and latest uploaded artifact, not your previous response. State the current expected task/version first. Do not repeat the last completed step. Do not silently rename versions. If I say v3, build v3. Verify the repo/artifact state before giving status or building. Then answer only the next action.
```

## Artifact check

```txt
HSD ARTIFACT CHECK.

Inspect the latest uploaded artifact as the source of truth. Do not answer from memory. Tell me: green/red status, exact renderer/template version found, what changed visually, what is still wrong, and whether it is time to build the next version. If building, use the next requested version exactly.
```

## Build mode

```txt
HSD BUILD MODE.

Use the latest verified repo/artifact state. Build and wire only the requested next version. Do not repeat the previous version. Fetch current files first, patch the repo, update guards, and tell me exact commits and what to run next.
```

## Version-specific build anchor

```txt
HSD REALITY CHECK. Latest artifact was v2.2. Next requested version is v2.3, not v2.2 again. Build Template Renderer v2.3 from the v2.2 visual findings.
```

## Current corrected anchor for this thread

```txt
HSD REALITY CHECK. Latest artifact was v2.33. Next requested version is v2.4, not v2.34 and not v2.33 again. Build Template Renderer v2.4 from the latest visual findings and fix local WNBA SVG logo rendering.
```
