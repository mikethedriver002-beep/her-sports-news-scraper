# HSD Command Center Decision Audit

## Decision

The daily command center should behave like an operator cockpit, not a raw status dump.

It should answer four questions quickly:

- What is the current call?
- Why is that the call?
- What should the operator do next?
- Which local mode creates a missing artifact?

Guardrails stay unchanged:

- Free public sources remain the default.
- Local/manual operation remains the default.
- No paid APIs are required.
- No auto-runs, workflow triggers, or auto-publishing are added.

## Baseline Gaps

- The first action could expose internal blocker codes such as `no_content_ready`.
- Missing artifacts said only `Missing`, without telling the operator how to create them.
- The NO-GO callout was too generic when the real blocker was a missing graphics upload pack.
- QA actions could appear before the required graphics pack existed.

## Improvement

- The decision callout now explains the practical reason for the call, such as a missing graphics upload pack.
- Next actions now prioritize the highest-value unblocker before raw blocker details.
- Actions can include an explicit local command, such as `.\hsd.cmd run -Mode asset`.
- Missing artifact rows now include creation hints for `dashboards`, `asset`, `posts`, `stories`, `handoff`, and `launch` modes.
- Waiting actions are trimmed first when the action list needs room for source review or manual-only guardrails.

## Operator Rule

The command center remains the daily home base. Support dashboards and packs are created only through explicit local modes when the operator chooses them.
