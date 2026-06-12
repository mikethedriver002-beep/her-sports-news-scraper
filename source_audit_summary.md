# Her Sports Daily Results Source Audit v3

Generated: `2026-06-12T18:23:55.178685+00:00`

## Purpose

This audit tests which sources are worth using for Results Desk v3.
v3 expands API-Sports testing across basketball, soccer, hockey, volleyball, handball, rugby, and baseball while keeping the v2 stale-data and blocked-source checks.

## Date window tested

2026-06-11, 2026-06-12, 2026-06-13, 2026-06-14

## Source summary

| Source | Tests | Successful Tests | Usable Events | Raw Events | Date-Matched Events | Stale Events Rejected | Likely Women's Events |
|---|---:|---:|---:|---:|---:|---:|---:|
| API-Sports expanded optional | 28 | 28 | 0 | 0 | 0 | 0 | 0 |
| ESPN public scoreboard | 24 | 16 | 12 | 12 | 12 | 0 | 12 |
| NCAA API / ncaa.com-derived | 96 | 48 | 0 | 48 | 0 | 48 | 0 |
| SofaScore public endpoints | 56 | 0 | 0 | 0 | 0 | 0 | 0 |
| TheSportsDB public API | 4 | 4 | 12 | 12 | 12 | 0 | 0 |

## Key interpretation rules

- **Usable Events** is the count we should care about for Results Desk v3.
- **Raw Events** may include stale/default events.
- **Stale Events Rejected** is critical for NCAA sources because some endpoints return championship results regardless of query date.
- SofaScore returning 403 means GitHub Actions cannot currently use that public endpoint directly.
- API-Sports expanded tests will only run if `APISPORTS_KEY` is set in GitHub Secrets.

## Files created

- `source_coverage_report.csv`
- `source_event_samples.csv`
- `source_audit_raw.json`

## Next build decision

Use sources only if they return usable/date-matched events. Discovery sources can suggest games, but final result graphics still need structured or official verification.
