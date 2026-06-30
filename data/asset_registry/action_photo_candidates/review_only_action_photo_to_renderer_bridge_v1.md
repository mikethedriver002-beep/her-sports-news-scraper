# Review-Only Action Photo To Renderer Bridge v1

Generated: `2026-06-30T00:00:00+00:00`

This bridge aggregates the external action-photo research return review, shared return import review, manual research bridge, renderer-unblock triage, quarantine preflight, and current top render handoff. It is artifact-only: it does not fetch sources, download images, approve candidates or assets, write headshots/cutouts/logos, create `.approved` markers, move files, enable sources, unblock renderer automatically, or publish.

## Decision

- Bridge status: `action_photo_renderer_blocked_manual_gate`
- Renderer unblocked: `no`
- Operator decision: `hold_renderer_action_photo_manual_gate`
- Render packet: `Golden State Valkyries beat New York Liberty`
- Active asset stop/go: `hold_required_manual_asset_review`
- Blocking reasons: `no_human_download_approved_rows|render_handoff_asset_stop_go_hold_required_manual_asset_review|renderer_hero_asset_required_approved_local_athlete_photo`

## Gate Rollup

- External returned/missing APQ rows: `8/2`
- External direct-image/identity holds: `8/8`
- Shared import rows with data/ready rows: `1/1`
- Manual bridge lanes/source rows: `2/103`
- Renderer triage rows: `2`
- Quarantine ready/lead-only/download-approved rows: `1/9/0`

## First Manual Action

- Queue/review: `APQ001` / `APQP001`
- Candidate page lead: `https://fever.wnba.com/news/fevers-poise-clarks-gravity-earn-fever-commissioners-cup-win-to-advance-to-finals`
- Next action: APQ001/APQP001 now has human-reviewed source, identity, rights, action-context, and use metadata. Next step is a separate human quarantine-download decision; keep download_approved=no until Mike explicitly edits the intake for quarantine-only download review.

## Validation

- Validation issues: `0`
