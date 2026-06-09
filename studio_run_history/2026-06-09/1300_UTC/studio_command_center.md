# Her Sports Daily Studio Command Center v1.2

Generated: `2026-06-09T13:00:00.005818+00:00`

## What this file is

This is the production bridge from Results Desk + News Sync into the graphics workflow.

Results Desk controls scores. News Sync controls context. Studio Bridge controls what to make, how to make it, and what must be checked before posting.

## Run summary

- Studio graphics queued: 0
- Make First / Make Next: 0
- Roundup bank: 0
- Diversity Watch: 0
- Manual review graphics: 0
- Bundle Mode posts: 0

## Open first

1. `studio_bundle_packets.md`
2. `studio_top_graphic_packets.md`
3. `studio_accuracy_checklist.csv`
4. `studio_bundle_caption_bank.md`
5. `brand_assets/hsd_watermark_bug.svg`

## Bundle Mode recommended posts

No bundles created.

## Individual backup production order

## Non-negotiable production rules

- Never fabricate jersey numbers, fake uniforms, logos, player teams, quotes, injuries, rankings, or milestones.
- Use the locked watermark bug from `brand_assets/hsd_watermark_bug.svg` every time.
- Every carousel gets a branded end slide.
- Check scoreboard sides manually before posting.
- If no approved player image/reference exists, use the safe text-forward prompt.

## Source health from News Sync

```text
# Her Sports Daily News Sync v1.8 Hub Run ID: `182c0e606a7ea142` Generated: `2026-06-09T12:58:53.684353+00:00` ## Architecture - Results Desk remains the scorer of record. - News Sync consumes Results Desk outputs and builds source-backed editorial packets. - The two systems are connected, but not merged into one fragile scraper. ## Run summary - News candidates read: 0 - Source observations: 0 - Usable source observations: 0 - Fact packets built: 0 - Publish-ready packets: 0 - Production-ready packets: 0 - Manual review packets: 0 - P1 / Must Post packets: 0 - P2 / Strong Maybe plus diversity packets: 0 - Diversity Watch packets: 0 - Source fetch flags: 0 ## Manual review rules - Hold if Results Desk marked the item for review. - Hold if Must Post has neither top-performer data nor a primary/official source. - Hold if no usable source context was captured. - Never invent player stats, rankings, quotes, injuries, or milestones. - Final score must be present, or packet is held. - Store facts, summaries, and links only. Do not copy full article text.
```
