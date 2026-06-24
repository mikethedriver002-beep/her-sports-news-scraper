# HSD Morning Source Discovery Board

Date: 2026-06-24

## Decision

The command center now has one morning source discovery queue:

- Official/free sources.
- Wire sources.
- Free cross-check sources.
- Reputable gray-area and public social discovery leads.
- Manual inbox leads.

The board is generated during local `review` and `full` runs as:

- `morning_source_discovery_board.csv`
- `morning_source_discovery_board.md`
- `morning_source_discovery_board.json`

## Review Rules

Green official, wire, primary, and operator-verified rows can move into editor review. Free cross-check rows can support confidence, but official or wire sources win on conflict. Gray-area and social rows stay discovery-only until confirmed by official, wire, primary, or operator-verified evidence.

The board does not fetch private sources, bypass paywalls, use paid APIs, auto-run in GitHub, or auto-publish. It is a local/manual operator queue.

## Command Center Impact

The daily command center now shows:

- Morning source row count.
- Gray/social lead count.
- A Sources tab with the morning board.
- A next-action item when a manual, social, discovery, or News Sync source lead needs review.

This makes the morning workflow less scattered: leads can come from free official sources, wire context, public gray-area/social discovery, or manual intake, but they all land in one review-safe place.
