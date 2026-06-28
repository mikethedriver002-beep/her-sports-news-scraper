# HSD External Research Packet Template

Status: packet template for ChatGPT Pro and Gemini Pro research.

Use this template as the README inside any research packet sent outside Codex. The external tool should advise; Codex remains responsible for implementation, tests, guardrails, and PRs.

## Research Alert

Tool:

Why now:

Email alert sent to:

Codex continues while this runs:

Expected output:

## Current Repo State

- Repo:
- Main commit:
- Latest Command Center:
- Current active lanes:
- Open PRs:

## Guardrails

- Review-only unless human-edited intake explicitly says otherwise.
- No paid APIs.
- No automatic downloads.
- Local downloads require `download_approved=yes` and the required quarantine metadata.
- No auto-approval.
- No asset approval-state changes without explicit human-edited intake.
- No publish-ready lane.
- No publishing.

## Files Included

List each included file and why it matters:

| File | Why included |
| --- | --- |
| `operator_command_center.html` | Current operator surface |
| `operator_command_center.md` | Searchable command-center summary |
| `manual_review_renderer_visual_comparison_board.md` | Renderer visual QA context |
| `draft_preview_visual_contact_sheet.png` | Current render comparison |
| `*.csv` or `*.json` manifests | Machine-readable candidate or QA data |

## Research Questions

1. What are the highest-impact improvements?
2. Which ideas are safe under the guardrails?
3. Which ideas require human-edited intake or policy approval first?
4. What are the top five PR-sized implementation packets?
5. What should not be attempted yet?

## Required Output Format

Return:

1. Ranked findings.
2. Guardrail-safe recommendations.
3. Risky or blocked recommendations.
4. Five PR-sized packets with lane owner, scope, files likely touched, validation, and artifact expectations.
5. Any suggested human decision prompts.

## Notes For External Tools

- Do not propose paid APIs as the default path.
- Do not propose automatic publishing.
- Do not propose auto-approval.
- Do not ask Codex to download assets without the quarantine intake policy.
- Gray-area public/fair-use-tolerant source candidates may be suggested as candidates, but approval remains human and review-only.
