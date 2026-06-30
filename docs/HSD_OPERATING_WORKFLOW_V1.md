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
Operational helper: build the upload bundle and Gmail-ready draft with `scripts/build_hsd_external_research_packet_v1.py`; usage notes live in `docs/HSD_RESEARCH_PACKET_BUILDER.md`.
Alert-only helper: build an email-ready alert and paste prompt from an existing packet path with `scripts/build_hsd_research_alert_draft_v1.py`.

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

## Lane Status Dashboard

The conductor can refresh a review-only lane dashboard with:

```powershell
python scripts\build_hsd_workflow_lane_status_v1.py
```

Outputs:

- `workflow_lane_status_dashboard.md`
- `workflow_lane_status_dashboard.csv`
- `workflow_lane_status_dashboard.json`
- `workflow_lane_nudge_synthesis.md`
- `workflow_lane_nudge_synthesis.csv`
- `workflow_lane_nudge_synthesis.json`

When `HSD_RUN_OUTPUT_DIR` is set, the dashboard writes into the run-scoped output folder and is collected into `outputs/local/latest/files` by the local review stage.

Optional human-maintained intake can live at `operator/inbox/workflow_lane_status_intake.csv` with these columns:

`lane_id,status,branch,pr,pending_thread,lane_owner_thread,last_pr_merged,restart_needed,next_packet,lifecycle_action,durable_lane_thread_status,durable_lane_recovery_cue,owner,last_update_utc,completed_merge_pr,completed_merge_commit,blocker,next_action,notes,review_only,paid_apis,source_fetching,automatic_downloads,auto_approval,approval_state_change,headshot_writes,approved_marker_writes,publish_ready,publishing`

Use `operator/inbox/workflow_lane_status_intake.example.csv` as a copyable review-only starter for conductor-visible completion rows. It is an example/template only; it does not become status truth unless a human copies reviewed rows into `operator/inbox/workflow_lane_status_intake.csv`.

Use `config/hsd_durable_lane_thread_roster.json` for reviewed durable lane thread refs that should travel with the repo after conductor recovery or conductor-confirmed persistent lane use. The dashboard reads this roster before marking expected durable lanes as missing, while preserving human intake precedence. Rostered action-photo, renderer, workflow-overhaul, and release-readiness owner threads prevent known persistent lanes from looking like invisible background work. The roster is visibility-only and does not create, close, archive, rebase, approve, download, enable sources, move publish-ready files, or publish.

Priority sublanes can also be listed in the durable roster with a blank `lane_owner_thread` when conductor evidence says the lane is active but no durable chat is visible. The dashboard turns those rows into manual missing-thread recovery prompts; it does not create threads automatically. Current priority sublanes include `womens_soccer_athlete_expansion` and `hockey_softball_asset_workflow`, both of which must stay review-only and must not change source, download, approval, asset, publish-ready, or publishing state from generated rows.

Use `pending_thread` for a delegated Codex thread id or URL that has active or waiting work but no PR yet. A pending thread is a visibility cue only; the conductor still checks the thread, branch, guardrails, and next action before nudging another lane.

Use `lane_owner_thread`, `last_pr_merged`, `restart_needed`, and `next_packet` after a merge wave when a durable lane should be restarted from current `origin/main`. These are conductor restart cues only; they do not create threads, branches, PRs, assets, sources, approvals, publish-ready movement, or publishing.

Use `lifecycle_action` only for manual conductor cues: `nudge`, `replace_reboot`, `pause`, `archive`, or `merge_ready`. The dashboard turns those into text-only `next_conductor_action` guidance and never closes branches, deletes worktrees, archives threads, rebases branches, or changes approval/download/source/publish state.

The workflow dashboard also flags expected durable lanes such as `games_schedule_stats` and `breaking_public_signal` when their thread reference is missing. Those rows use `durable_lane_thread_status` plus `durable_lane_recovery_cue` so the conductor can recover or relink the lane explicitly instead of assuming an invisible chat is still active.

The companion `workflow_durable_lane_recovery_packet.md` turns those missing-thread rows into exact operator prompts, including the lane-specific artifacts to open first and the manual recovery cue to use if the durable lane thread has gone quiet.

When no intake row exists, the dashboard also scans local Git worktrees for `codex/` branches whose names match lane hints such as `renderer`, `asset`, `games`, `breaking`, `copy`, `qa`, or `workflow`. These rows are marked as worktree hints and should be checked by the conductor before treating them as active lane truth. Use `--skip-worktree-lookup` for fixture tests or intentionally isolated runs.

If the workflow-overhaul row has no manual intake, open PR, current branch, or worktree hint, the dashboard keeps it visible as `heartbeat_visible_needs_conductor_check` instead of letting the conductor lose the lane in a fully unreported table. That heartbeat is a checklist/status cue only: confirm `origin/main`, open PR count, worktree hints, next-action synthesis, and conductor audit before nudging one small review-only workflow packet.

Manual intake rows with an active/review/blocked status, branch, PR, or blocker now carry deterministic activity metrics and a stale-lane brake. By default, `last_update_utc` older than 48 hours becomes `stale_lane_needs_conductor_check`; a missing timestamp becomes `missing_last_update_needs_conductor_check`. The dashboard also emits `activity_age_hours`, `activity_status`, `last_known_branch`, `last_known_head`, and `next_conductor_action`. The brake tells the conductor to refresh current proof, PR state, and branch freshness before nudging or merging. It does not edit the intake, branches, PRs, sources, assets, approvals, publish-ready folders, or publishing state.

The nudge synthesis artifact ranks only manual conductor prompts from the lane-status rows: stale brakes first, then restart-needed/lifecycle rows, then heartbeat or worktree-hint checks. It is a review-only queue for deciding whether to nudge, replace/reboot, pause, recommend archive, or mark merge-ready. It does not force-delete worktrees, close branches, archive user-owned threads, rebase branches, or change approval/download/source/publish state.

This dashboard is a conductor visibility aid only. It does not create branches, change approval state, download assets, move files, or publish.

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
