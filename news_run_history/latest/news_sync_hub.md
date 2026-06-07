# Her Sports Daily News Sync v1.3 Hub

Run ID: `11e89692c6e4e963`
Generated: `2026-06-07T03:00:54.043404+00:00`

## Architecture

- Results Desk remains the scorer of record.
- News Sync consumes Results Desk outputs and builds source-backed editorial packets.
- The two systems are connected, but not merged into one fragile scraper.

## Run summary

- News candidates read: 9
- Source observations: 29
- Usable source observations: 29
- Fact packets built: 9
- Publish-ready packets: 9
- Production-ready packets: 9
- Manual review packets: 0
- P1 / Must Post packets: 4
- P2 / Strong Maybe packets: 5
- Source fetch flags: 0

## Manual review rules

- Hold if Results Desk marked the item for review.
- Hold if Must Post has neither top-performer data nor a primary/official source.
- Hold if no usable source context was captured.
- Never invent player stats, rankings, quotes, injuries, or milestones.
- Final score must be present, or packet is held.
- Store facts, summaries, and links only. Do not copy full article text.
