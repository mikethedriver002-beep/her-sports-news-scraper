# Her Sports Daily Results Desk v4.3 Hub

Run ID: `cc84c917103a2a20`
Generated: `2026-06-07T00:09:13.518869+00:00`
Date window: `2026-06-05, 2026-06-06, 2026-06-07`

## Source strategy

- API-Sports is the scoring backbone.
- ESPN WNBA is backup/verification.
- v4.3 adds strict date-window gating, major soccer nation boosts, angle tags, smarter context, and optional WNBA box-score audit.

## Run summary

- Raw source observations: 1447
- Reconciled events: 1427
- Women's events surfaced: 138
- Women's finals: 65
- Graphics-ready results: 64
- Manual review items: 0
- Carryover or outside-window events archived: 0
- Must Post: 5
- Strong Maybe: 10
- Watchlist: 15

## Observations by source

- api_sports: 1438
- espn_wnba: 9

## Women's events by sport

- basketball: 24
- handball: 4
- rugby: 17
- soccer: 61
- volleyball: 32

## Graphics gate

- `include_in_graphics` requires women-only, final, confidence >= 0.85, and manual_review = No.
- v4.3 treats tied soccer/rugby/handball/hockey finals as draws, not errors.
- The graphics queue is globally capped: 5 Must Post, 10 Strong Maybe, 15 Watchlist.
- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.
