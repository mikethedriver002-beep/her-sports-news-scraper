# Her Sports Daily News Sync v1.6 Hub

Run ID: `1fd93daeeb129960`
Generated: `2026-06-07T03:33:53.831401+00:00`

## Architecture

- Results Desk remains the scorer of record.
- News Sync consumes Results Desk outputs and builds source-backed editorial packets.
- The two systems are connected, but not merged into one fragile scraper.

## Run summary

- News candidates read: 14
- Source observations: 31
- Usable source observations: 31
- Fact packets built: 14
- Publish-ready packets: 10
- Production-ready packets: 10
- Manual review packets: 4
- P1 / Must Post packets: 5
- P2 / Strong Maybe plus diversity packets: 9
- Diversity Watch packets: 0
- Source fetch flags: 0

## Manual review rules

- Hold if Results Desk marked the item for review.
- Hold if Must Post has neither top-performer data nor a primary/official source.
- Hold if no usable source context was captured.
- Never invent player stats, rankings, quotes, injuries, or milestones.
- Final score must be present, or packet is held.
- Store facts, summaries, and links only. Do not copy full article text.
