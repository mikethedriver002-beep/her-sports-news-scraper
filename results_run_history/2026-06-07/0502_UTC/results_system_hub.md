# Her Sports Daily Results Desk Hub

Generated: 2026-06-07T05:02:16.894548+00:00

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
- Date window queried: 20260606, 20260607, 20260608
- Games found: 9
- Final games: 4
- Result graphics ready: 4

## Accuracy rules
- Never infer a final score.
- Never invent a top performer stat line.
- If a game is not final, do not create a postgame result graphic.
- If confidence is not High, keep manual review enabled.
