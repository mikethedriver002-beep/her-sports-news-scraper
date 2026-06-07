# Her Sports Daily News Sync v1.8 Hub

Run ID: `335a208c4ee50130`
Generated: `2026-06-07T16:04:25.779104+00:00`

## Architecture

- Results Desk remains the scorer of record.
- News Sync consumes Results Desk outputs and builds source-backed editorial packets.
- The two systems are connected, but not merged into one fragile scraper.

## Run summary

- News candidates read: 0
- Source observations: 0
- Usable source observations: 0
- Fact packets built: 0
- Publish-ready packets: 0
- Production-ready packets: 0
- Manual review packets: 0
- P1 / Must Post packets: 0
- P2 / Strong Maybe plus diversity packets: 0
- Diversity Watch packets: 0
- Source fetch flags: 0

## Manual review rules

- Hold if Results Desk marked the item for review.
- Hold if Must Post has neither top-performer data nor a primary/official source.
- Hold if no usable source context was captured.
- Never invent player stats, rankings, quotes, injuries, or milestones.
- Final score must be present, or packet is held.
- Store facts, summaries, and links only. Do not copy full article text.
