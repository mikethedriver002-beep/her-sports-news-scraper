# Her Sports Daily Results Desk v4.2 Hub

Run ID: `dc0c3cfee88628b3`
Generated: `2026-06-06T23:02:34.267263+00:00`
Date window: `2026-06-05, 2026-06-06, 2026-06-07`

## Source strategy

- API-Sports is the scoring backbone.
- ESPN WNBA is backup/verification.
- v4.2 adds WNBA reconciliation, WNBA-first ranking, league aliasing, and global queue buckets.

## Run summary

- Raw source observations: 1821
- Reconciled events: 1800
- Women's events surfaced: 215
- Women's finals: 138
- Graphics-ready results: 137
- Manual review items: 0
- Must Post: 5
- Strong Maybe: 10
- Watchlist: 15

## Observations by source

- api_sports: 1812
- espn_wnba: 9

## Women's events by sport

- basketball: 35
- handball: 4
- rugby: 29
- soccer: 101
- volleyball: 46

## Graphics gate

- `include_in_graphics` requires women-only, final, confidence >= 0.85, and manual_review = No.
- v4.2 treats tied soccer/rugby/handball/hockey finals as draws, not errors.
- The graphics queue is globally capped: 5 Must Post, 10 Strong Maybe, 15 Watchlist.
- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.
