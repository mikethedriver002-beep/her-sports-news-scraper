# Her Sports Daily Results Desk v4 Hub

Run ID: `62ec951579c45507`
Generated: `2026-06-06T22:05:02.452714+00:00`
Date window: `2026-06-05, 2026-06-06, 2026-06-07`

## Source strategy

- API-Sports is the scoring backbone.
- ESPN WNBA is backup/verification.
- NCAA is optional and stale-filtered.
- SofaScore wrapper is optional discovery/enrichment only.

## Run summary

- Raw source observations: 1821
- Reconciled events: 1809
- Women's events surfaced: 224
- Women's finals: 139
- Graphics-ready results: 122
- Manual review items: 12

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

- include_in_graphics requires women-only, final, confidence >= 0.85, and manual_review = No.
- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.
