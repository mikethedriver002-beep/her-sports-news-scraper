# HSD Lane Packet Contract

Status: PR packet standard for Codex implementation lanes.

Every lane packet should be small enough to review, validate, and merge without changing unrelated project behavior.

## Required Packet Shape

Each packet must define:

- Lane owner.
- Starting `main` commit.
- Branch name with `codex/` prefix.
- One visible improvement.
- Files expected to change.
- Artifacts expected to regenerate.
- Focused tests.
- Guardrail scan.
- Draft PR handoff.

## Branch Rules

- Start from current `origin/main`.
- Do not continue on an old merged branch.
- Keep one lane per branch.
- Do not merge your own PR from the lane chat.
- If stale, rebase or recreate from main before opening or marking ready.

## PR Body Checklist

Each PR body should include:

- Summary.
- Review-only artifact paths if display-facing.
- Validation commands and results.
- Guardrail statement.
- Known limitations.
- Whether external research or audit agents were used.

## Validation Rules

Minimum validation:

- `python -m py_compile` for touched Python files.
- Focused pytest for the lane.
- Regenerate display-facing artifacts when the display changes.
- Inspect generated artifacts for freshness and links.
- Run guardrail scans for approval, download, publish, and publish-ready regressions.

## Guardrail Language

Every lane must preserve:

- No paid APIs.
- No automatic downloads.
- No auto-approval.
- No approval-state changes without explicit human-edited intake.
- No publishing.
- No publish-ready lane.
- No movement into publish-ready lanes.

## External Research Intake

If a lane uses ChatGPT Pro or Gemini Pro research:

- Cite the research packet path.
- Summarize which findings were accepted.
- Mark which findings were rejected or deferred.
- Keep the implementation PR smaller than the research report.

## Stop Conditions

Stop and return to the conductor when:

- Human intake is required.
- Approval state would need to change.
- A download would be needed without approved quarantine intake.
- A PR requires cross-lane changes.
- Tests reveal an unrelated repo failure that should not be fixed inside the packet.
