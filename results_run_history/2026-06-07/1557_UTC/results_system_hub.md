# Her Sports Daily Results Desk v4.3 Hub

Run ID: `841ef8064a50cc21`
Generated: `2026-06-07T15:57:12.813845+00:00`
Date window: `2026-06-06, 2026-06-07, 2026-06-08`

## Source strategy

- API-Sports is the scoring backbone.
- ESPN WNBA is backup/verification.
- v4.3 adds strict date-window gating, major soccer nation boosts, angle tags, smarter context, and optional WNBA box-score audit.

## Run summary

- Raw source observations: 9
- Reconciled events: 9
- Women's events surfaced: 9
- Women's finals: 4
- Graphics-ready results: 0
- Manual review items: 0
- Carryover or outside-window events archived: 0
- Must Post: 0
- Strong Maybe: 0
- Watchlist: 0

## Observations by source

- espn_wnba: 9

## Women's events by sport

- basketball: 9

## Graphics gate

- `include_in_graphics` requires women-only, final, confidence >= 0.85, and manual_review = No.
- v4.3 treats tied soccer/rugby/handball/hockey finals as draws, not errors.
- The graphics queue is globally capped: 5 Must Post, 10 Strong Maybe, 15 Watchlist.
- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.
