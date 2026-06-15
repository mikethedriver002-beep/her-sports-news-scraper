# Her Sports Daily Results Desk Hub

Generated: 2026-06-15T19:45:49.121297+00:00

## What this system does
- Pulls structured women's sports results from scoreboard-style endpoints.
- Separates results and box scores from the broader news pipeline.
- Produces result-ready postgame graphic packets only for final games.

## Phase 1 coverage
- WNBA
- NCAA Women's Basketball
- NCAA Softball

## Output files
- `today_results_board.csv`
- `today_box_scores.csv`
- `top_performers.csv`
- `results_graphics_queue.md`
- `results_dashboard_seed.csv`

## Current run snapshot
- Date window queried: 20260614, 20260615, 20260616
- Games found: 6
- Final games: 2
- Result graphics ready: 2

## Accuracy rules
- Never infer a final score.
- Never invent a top performer stat line.
- If a game is not final, do not create a postgame result graphic.
- If confidence is not High, keep manual review enabled.
