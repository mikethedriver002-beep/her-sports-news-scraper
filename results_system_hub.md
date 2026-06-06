# Her Sports Daily Results Desk v4.1 Hub

Run ID: `4bff93dc66058b4d`
Generated: `2026-06-06T22:19:57.418945+00:00`
Date window: `2026-06-05, 2026-06-06, 2026-06-07`

## Source strategy

- API-Sports is the scoring backbone.
- ESPN WNBA is backup/verification.
- v4.1 adds draw handling and editorial queue caps.

## Run summary

- Raw source observations: 1821
- Reconciled events: 1809
- Women's events surfaced: 224
- Women's finals: 139
- Graphics-ready results: 134
- Manual review items: 0
- Must Post: 58
- Strong Maybe: 47
- Watchlist: 57

## Observations by source

- api_sports: 1812
- espn_wnba: 9

## Women's events by sport

- basketball: 44
- handball: 4
- rugby: 29
- soccer: 101
- volleyball: 46

## Graphics gate

- `include_in_graphics` requires women-only, final, confidence >= 0.85, and manual_review = No.
- v4.1 treats tied soccer/rugby/handball/hockey finals as draws, not errors.
- The graphics queue is capped: 5 Must Post, 10 Strong Maybe, 15 Watchlist.
- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.
