# Asset Visual QA v1.8.2

This patch keeps the event-date freshness fix and expands people/player sourcing beyond WNBA-only posts.

## What changed

- `generate_hsd_player_image_assets_v1.py` now scans bundle queue rows and prompt text across all bundles.
- It extracts likely people/player names from performer/stat lines instead of only using the hardcoded Main WNBA Result set.
- Search queries are now sport-aware instead of forcing basketball/WNBA terms for every athlete.
- If approved people/player assets are present for a bundle, the graphics chat should use them. If none are present, it should stay text-forward.
