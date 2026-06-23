# Phase 8B manual multi-sport packet inbox

Drop verified daily non-WNBA event packets here as `.json` or `.csv` files.

Accepted JSON shapes:

```json
{"events": [{"sport_id":"nwsl","kind":"preview","primary_name":"Orlando Pride","secondary_name":"Washington Spirit"}]}
```

or a plain JSON list of event objects.

Required fields:
- `sport_id`: `nwsl`, `uswnt`, `tennis`, `lpga`, `ncaa_softball`, or `volleyball`
- `kind`: `preview`, `result`, or `story`
- `primary_name`

For result packets, include a scoreline or winner/loser scores.
For preview packets, include a secondary team/player or a verified event title.
