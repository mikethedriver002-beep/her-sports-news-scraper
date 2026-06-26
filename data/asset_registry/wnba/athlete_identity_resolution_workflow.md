# HSD WNBA Athlete Identity Resolution Workflow v1

Generated: 2026-06-26T22:56:03.232205+00:00
Status: **no_audit_issues_found**

## Policy

- Review-only identity resolution workflow.
- This does not approve, reject, move, fetch, publish, or mark athlete photos publish-ready.
- Renderer eligibility can be restored only from a human-filled operator inbox row with source evidence.

## Operator Inbox

- Copy reviewed rows into `operator/inbox/wnba_athlete_identity_resolution.csv`.
- Start with `data/asset_registry/wnba/athlete_identity_review_packet.csv` for hold-first identity review cues.
- Use `identity_verified_approved_for_review_renders` only after checking a trusted player/source page by eye.
- Use `hold_identity` when the person, team, provider ID, or source proof is uncertain.
- Use `revise_asset` when the row appears to be the wrong image or wrong crop.
- Use `backfill_provider_id_only` when the photo should remain held but the provider ID can be source-backed.

## Required Evidence For Renderer Eligibility

- `identity_verified=yes`
- `provider_player_id_verified=yes` or a clearly filled `backfill_provider_player_id`
- `approved_source_url` from a free official/team/reputable public source
- `operator_name`, `reviewed_at_local`, and `operator_notes` filled
- all guardrail columns remain false

## Focused Review Packet

- packet rows: 0
- identity hold rows: 0
- default approval rows: 0

## Priority Rows

- No audit issue rows found. Re-run the identity audit first if this seems wrong.
