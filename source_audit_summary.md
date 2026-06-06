# Her Sports Daily Results Source Audit

Generated: `2026-06-06T01:24:14.464390+00:00`

## Purpose

This audit tests which sources are worth using for the next Results Desk rebuild.
It does not decide what to post. It measures source coverage, event access, women's-sports relevance, and possible role.

## Date window tested

2026-06-04, 2026-06-05, 2026-06-06, 2026-06-07

## Source summary

| Source | Tests | Successful Tests | Events Found | Likely Women's Events |
|---|---:|---:|---:|---:|
| API-Sports optional | 1 | 0 | 0 | 0 |
| ESPN public scoreboard | 24 | 16 | 11 | 11 |
| NCAA API / ncaa.com-derived | 96 | 48 | 48 | 24 |
| SofaScore public endpoints | 36 | 0 | 0 | 0 |
| TheSportsDB public API | 4 | 0 | 0 | 0 |

## How to read this

- **Events Found** means the endpoint returned events. It does not mean the source is ready for final graphics.
- **Likely Women's Events** is a keyword-based signal, not a final truth label.
- **Recommended Role** in the CSV tells us whether a source looks better for discovery, verification, box scores, or metadata.

## Next build decision

Use the highest-coverage discovery source to find events, then verify final scores with official or structured sources.
For result graphics, do not use one unofficial source alone unless it is clearly structured and later verified.

## Files created

- `source_coverage_report.csv`
- `source_event_samples.csv`
- `source_audit_raw.json`

## Early recommendation

If SofaScore returns broad event coverage in this audit, use it as a discovery layer.
If NCAA API returns college sport events, use it as the NCAA verification layer.
Keep ESPN as a secondary structured source, not the whole Results Desk.
Use API-Sports only if an API key is available and coverage is clearly better.
