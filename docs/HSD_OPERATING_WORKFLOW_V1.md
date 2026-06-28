# HSD Operating Workflow V1

Status: review-only operating standard.

This document defines how HSD work should be coordinated across Codex implementation lanes, external research tools, and human review. It is an operating workflow, not a publishing workflow, and it does not change scraper, renderer, asset, or approval behavior.

## Operating Principles

- Keep `main` stable.
- Use this repo's generated artifacts as the source of operator truth.
- Keep every implementation packet lane-scoped and PR-sized.
- Prefer visible review artifacts over hidden behavior.
- Convert broad research into ranked, testable implementation packets.
- Keep all generated outputs review-only unless a human edits the relevant intake files.

## Conductor Role

The conductor chat coordinates the project but does not implement by default.

Responsibilities:

- Inspect open PRs and lane status.
- Validate branch freshness, tests, artifacts, and guardrails.
- Merge clean PRs after inspection.
- Refresh latest artifacts after merges when display-facing behavior changes.
- Nudge exactly one idle lane with the next highest-leverage packet.
- Convert external ChatGPT Pro or Gemini Pro reports into PR-sized work.
- Maintain the next action prompt and current 10x plan status.

The conductor should not:

- Change asset approval state.
- Publish or create publish-ready lanes.
- Start broad implementation work in the command-center chat unless explicitly redirected.
- Let a lane merge its own PR without conductor inspection.

## Implementation Lanes

Use separate Codex chats/worktrees for active implementation lanes.

| Lane | Owns | Typical PR packet |
| --- | --- | --- |
| Renderer quality | Manual review renderer visuals, preview QA, comparison boards | Layout, background, text hierarchy, visual QA improvements |
| Asset registry/contact sheets | Logo/photo source candidates, contact sheets, human intake worksheets | Review-only boards, intake bridges, operator clarity |
| Games/schedule/stats | Results, schedules, game intelligence, stats evidence | Review-only source confirmation and queue clarity |
| Breaking/public signal | News discovery, public-signal queue, confirmation evidence | Review-only evidence surfacing and social/public signal triage |
| Copy/editorial polish | Titles, deks, captions, tone, visual copy fit | Sharper review-only copy suggestions and fit cues |
| QA/release readiness | Guardrail scans, artifact freshness, merge safety | No-behavior audit reports and focused quality gates |

Each lane should start from current merged `main`, create a focused `codex/` branch, and open a draft PR when validation passes.

## External Research Lanes

ChatGPT Pro and Gemini Pro are advisory research lanes. They do not edit the repo.

Use ChatGPT Pro for:

- Deep research.
- Competitive editorial and product strategy.
- Source discovery strategies.
- Legal/fair-use policy review.
- Ranked roadmap synthesis.

Use Gemini Pro for:

- Image-heavy render critique.
- Contact-sheet visual review.
- Comparing current drafts against reference templates.
- Long-context cross-checking of manifests, screenshots, and visual boards.

External reports return to the conductor, which decides what is safe, what needs human intake, and which lane should implement the next packet.

## Research Alert System

Research alerts should be non-blocking. They tell Mike when an external tool would raise quality, without stopping active Codex lanes.

Primary delivery: email to Mike using `docs/HSD_RESEARCH_ALERT_EMAIL_TEMPLATE.md`.

Default recipient: `michael@brieffactory.com`.

The conductor should create or surface a research alert when any of these triggers occur:

- A render critique depends on visual taste, sports design norms, or competitive references.
- A source strategy question spans many leagues, teams, or athlete identity candidates.
- A legal/rights/fair-use judgment needs broader context than local repo guardrails.
- A roadmap decision affects more than one implementation lane.
- A contact sheet is complete enough for human visual review but too large for efficient in-chat inspection.

Email alert format:

```text
Research alert:
Tool: ChatGPT Pro or Gemini Pro
Why now: one sentence
Packet to upload: local zip/folder path
Prompt to paste: exact prompt
Expected output: ranked findings plus 5 PR-sized packets
Codex continues: yes/no and which lane continues
```

Default behavior: Codex lanes continue while Mike runs the external research, unless the active work explicitly depends on that answer.

The Command Center is not the primary alert channel because Mike may not be looking at it during active work. It can still archive research-packet artifacts later if a specific packet needs a durable repo link.

## Standard Research Packet

Each external research packet should include:

- Latest Command Center HTML and Markdown.
- Current render previews, contact sheets, or QA boards relevant to the question.
- Reference templates and approved layout references when visual quality is being reviewed.
- Relevant CSV/JSON manifests.
- Current guardrails.
- The exact research questions.
- A requested output format.

Use `docs/HSD_EXTERNAL_RESEARCH_PACKET_TEMPLATE.md` as the packet README template.

## Standard Report Intake

When a ChatGPT Pro or Gemini Pro report returns, the conductor should classify it into:

- Safe under current guardrails.
- Needs human-edited intake before implementation.
- Requires a new policy decision.
- Not suitable for current HSD scope.

Then it should produce:

- A ranked roadmap.
- The next five PR-sized packets.
- Lane ownership for each packet.
- Expected files touched.
- Validation and artifact requirements.
- Merge order.

## Guardrails

These stay in force across all lanes:

- No paid APIs.
- No automatic downloads.
- Local downloads only through the review-only quarantine policy in `docs/HSD_REVIEW_ONLY_ASSET_DOWNLOAD_POLICY.md`.
- No auto-approval.
- No asset approval-state changes without explicit human-edited intake.
- No `headshot.png` writes unless an approved human workflow explicitly owns that write.
- No `.approved` marker writes unless an approved human workflow explicitly owns that write.
- No publishing.
- No auto-publishing.
- No publish-ready lane.
- No file movement into publish-ready lanes.

## Seven-Day Execution Cadence

Day 1: Renderer quality and visual QA.

Day 2: Asset contact sheets, source candidates, and human intake clarity.

Day 3: Games, schedules, results, and stats evidence.

Day 4: Breaking news and public-signal evidence.

Day 5: Editorial copy, titles, deks, captions, and tone.

Day 6: QA, release readiness, guardrail scans, and artifact freshness.

Day 7: Consolidation, backlog pruning, external research digestion, and next sprint plan.

## Daily Conductor Checklist

1. Inspect `main`, HEAD, dirty state, and open PRs.
2. Merge clean PRs only after guardrail and validation checks.
3. Refresh latest artifacts after display-facing merges.
4. Identify idle lanes.
5. Nudge the highest-leverage idle lane with one PR-sized packet.
6. Create a research alert if external research would improve the next decision.
7. End with a copyable next prompt/action.
