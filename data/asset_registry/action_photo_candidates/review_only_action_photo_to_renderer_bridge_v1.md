# Review-Only Action Photo To Renderer Bridge v1

Generated: `2026-06-30T00:00:00+00:00`

This bridge aggregates the external action-photo research return review, shared return import review, manual research bridge, renderer-unblock triage, quarantine preflight, and current top render handoff. It is artifact-only: it does not fetch sources, download images, approve candidates or assets, write headshots/cutouts/logos, create `.approved` markers, move files, enable sources, unblock renderer automatically, or publish.

## Decision

- Bridge status: `action_photo_renderer_blocked_manual_gate`
- Renderer unblocked: `no`
- Operator decision: `hold_renderer_action_photo_manual_gate`
- Render packet: `Golden State Valkyries beat New York Liberty`
- Active asset stop/go: `hold_required_manual_asset_review`
- Blocking reasons: `external_return_missing_rows|external_return_direct_image_url_holds|external_return_identity_vocabulary_holds|shared_return_intake_has_no_human_pasted_rows|shared_import_review_has_no_ready_rows|quarantine_preflight_has_no_ready_rows|no_human_download_approved_rows|render_handoff_asset_stop_go_hold_required_manual_asset_review|renderer_hero_asset_required_approved_local_athlete_photo`

## Gate Rollup

- External returned/missing APQ rows: `8/2`
- External direct-image/identity holds: `8/8`
- Shared import rows with data/ready rows: `0/0`
- Manual bridge lanes/source rows: `2/103`
- Renderer triage rows: `2`
- Quarantine ready/lead-only/download-approved rows: `0/10/0`

## First Manual Action

- Queue/review: `APQ001` / `APER001`
- Candidate page lead: `https://www.reuters.com/world/us/grow-up-caitlin-clark-commits-five-turnovers-fever-loss-sun-2025-06-18/`
- Next action: Start with APQ001/APER001: Use the source/evidence page URL as the candidate page lead (https://www.reuters.com/world/us/grow-up-caitlin-clark-commits-five-turnovers-fever-loss-sun-2025-06-18/); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification. Then paste the human-reviewed source, identity, rights, action-context, and use metadata into the shared return intake; rerun import review, quarantine preflight, this bridge, and only then re-check renderer handoff.

## Validation

- Validation issues: `0`
