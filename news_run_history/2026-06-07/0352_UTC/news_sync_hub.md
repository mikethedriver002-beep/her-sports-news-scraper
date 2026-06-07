# Her Sports Daily News Sync v1.7 Hub

Run ID: `a01df42dde31f8a8`
Generated: `2026-06-07T03:52:34.438087+00:00`

## Architecture

- Results Desk remains the scorer of record.
- News Sync consumes Results Desk outputs and builds source-backed editorial packets.
- The two systems are connected, but not merged into one fragile scraper.

## Run summary

- News candidates read: 14
- Source observations: 79
- Usable source observations: 69
- Fact packets built: 14
- Publish-ready packets: 14
- Production-ready packets: 14
- Manual review packets: 0
- P1 / Must Post packets: 5
- P2 / Strong Maybe plus diversity packets: 9
- Diversity Watch packets: 4
- Source fetch flags: 10

## Manual review rules

- Hold if Results Desk marked the item for review.
- Hold if Must Post has neither top-performer data nor a primary/official source.
- Hold if no usable source context was captured.
- Never invent player stats, rankings, quotes, injuries, or milestones.
- Final score must be present, or packet is held.
- Store facts, summaries, and links only. Do not copy full article text.
