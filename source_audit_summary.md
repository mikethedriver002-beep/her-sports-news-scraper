# Her Sports Daily Results Source Audit v2

Generated: `2026-06-06T01:35:20.092166+00:00`

## Purpose

This audit tests which sources are worth using for Results Desk v3.
v2 specifically checks for blocked sources, stale/default college data, and blank API-key mistakes.

## Date window tested

2026-06-04, 2026-06-05, 2026-06-06, 2026-06-07

## Source summary

| Source | Tests | Successful Tests | Usable Events | Raw Events | Date-Matched Events | Stale Events Rejected | Likely Women's Events |
|---|---:|---:|---:|---:|---:|---:|---:|
| API-Sports optional | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| ESPN public scoreboard | 24 | 16 | 11 | 11 | 11 | 0 | 11 |
| NCAA API / ncaa.com-derived | 96 | 48 | 0 | 48 | 0 | 48 | 0 |
| SofaScore public endpoints | 56 | 0 | 0 | 0 | 0 | 0 | 0 |
| TheSportsDB public API | 4 | 4 | 12 | 12 | 12 | 0 | 0 |

## Key interpretation rules

- **Usable Events** is the count we should care about for Results Desk v3.
- **Raw Events** may include stale/default events.
- **Stale Events Rejected** is critical for NCAA sources because some endpoints return championship results regardless of query date.
- SofaScore returning 403 means GitHub Actions cannot currently use that public endpoint directly.
- API-Sports will only test if `APISPORTS_KEY` is set in GitHub Secrets.

## Files created

- `source_coverage_report.csv`
- `source_event_samples.csv`
- `source_audit_raw.json`

## Next build decision

Use sources only if they return usable/date-matched events. Discovery sources can suggest games, but final result graphics still need structured or official verification.
