# Her Sports Daily Studio Command Center v1.2

Generated: `2026-06-07T04:51:47.224366+00:00`

## What this file is

This is the production bridge from Results Desk + News Sync into the graphics workflow.

Results Desk controls scores. News Sync controls context. Studio Bridge controls what to make, how to make it, and what must be checked before posting.

## Run summary

- Studio graphics queued: 14
- Make First / Make Next: 5
- Roundup bank: 5
- Diversity Watch: 4
- Manual review graphics: 0
- Bundle Mode posts: 4

## Open first

1. `studio_bundle_packets.md`
2. `studio_top_graphic_packets.md`
3. `studio_accuracy_checklist.csv`
4. `studio_bundle_caption_bank.md`
5. `brand_assets/hsd_watermark_bug.svg`

## Bundle Mode recommended posts

### Bundle 1: Main WNBA Result

- Priority: **POST FIRST**
- Asset: 4-slide carousel (1080x1350)
- Slides: 4
- Source items: 1
- Source headlines: Dallas Wings beat Los Angeles Sparks

### Bundle 2: Tonight in the W Mini-Roundup

- Priority: **POST NEXT**
- Asset: bundled carousel (1080x1350)
- Slides: 5
- Source items: 3
- Source headlines: Las Vegas Aces beat Golden State Valkyries | Minnesota Lynx beat Seattle Storm | Phoenix Mercury beat Portland Fire

### Bundle 3: Volleyball Results Roundup

- Priority: **ROUNDUP WINDOW**
- Asset: bundled carousel (1080x1350)
- Slides: 5
- Source items: 6
- Source headlines: USA W beat France W | Belgium W beat Thailand W | Brazil W beat Bulgaria W | Canada W beat France W | China W beat Serbia W | Italy W beat Turkey W

### Bundle 4: Women's Soccer Radar

- Priority: **DIVERSITY SLOT**
- Asset: bundled carousel (1080x1350)
- Slides: 5
- Source items: 4
- Source headlines: Brazil U20 W beat Korea Republic U20 W | Brazil W beat USA W | Japan W beat South Africa W | Mexico W beat Australia W

## Individual backup production order

### 1. Dallas Wings beat Los Angeles Sparks

- Bucket: **MAKE FIRST**
- Asset: 4-slide carousel (1080x1350)
- Template: Tonight in the W: High-Scoring Result Carousel
- Final score: Dallas Wings 104, Los Angeles Sparks 96
- Safety mode: verified_stats_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

### 2. Las Vegas Aces beat Golden State Valkyries

- Bucket: **MAKE NEXT**
- Asset: 4-slide carousel (1080x1350)
- Template: Tonight in the W: Close Finish Carousel
- Final score: Las Vegas Aces 84, Golden State Valkyries 79
- Safety mode: verified_stats_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

### 3. Minnesota Lynx beat Seattle Storm

- Bucket: **MAKE NEXT**
- Asset: 4-slide carousel (1080x1350)
- Template: Tonight in the W: Statement Win Carousel
- Final score: Minnesota Lynx 88, Seattle Storm 68
- Safety mode: verified_stats_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

### 4. Phoenix Mercury beat Portland Fire

- Bucket: **MAKE NEXT**
- Asset: 4-slide carousel (1080x1350)
- Template: Tonight in the W: Close Finish Carousel
- Final score: Phoenix Mercury 78, Portland Fire 72
- Safety mode: verified_stats_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

### 5. USA W beat France W

- Bucket: **MAKE NEXT**
- Asset: single result card + story crop (1080x1350 + 1080x1920)
- Template: Around Women's Sports: Volleyball Roundup Card
- Final score: USA W 3 - France W 2
- Safety mode: score_safe_volleyball_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

### 6. Belgium W beat Thailand W

- Bucket: **ROUNDUP BANK**
- Asset: roundup card (1080x1350)
- Template: Around Women's Sports: Volleyball Roundup Card
- Final score: Belgium W 3 - Thailand W 2
- Safety mode: score_safe_volleyball_text_forward
- Watermark: Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.

## Non-negotiable production rules

- Never fabricate jersey numbers, fake uniforms, logos, player teams, quotes, injuries, rankings, or milestones.
- Use the locked watermark bug from `brand_assets/hsd_watermark_bug.svg` every time.
- Every carousel gets a branded end slide.
- Check scoreboard sides manually before posting.
- If no approved player image/reference exists, use the safe text-forward prompt.

## Source health from News Sync

```text
# Her Sports Daily News Sync v1.8 Hub Run ID: `b361826aeda272a3` Generated: `2026-06-07T04:41:01.602794+00:00` ## Architecture - Results Desk remains the scorer of record. - News Sync consumes Results Desk outputs and builds source-backed editorial packets. - The two systems are connected, but not merged into one fragile scraper. ## Run summary - News candidates read: 14 - Source observations: 55 - Usable source observations: 51 - Fact packets built: 14 - Publish-ready packets: 14 - Production-ready packets: 14 - Manual review packets: 0 - P1 / Must Post packets: 5 - P2 / Strong Maybe plus diversity packets: 9 - Diversity Watch packets: 4 - Source fetch flags: 4 ## Manual review rules - Hold if Results Desk marked the item for review. - Hold if Must Post has neither top-performer data nor a primary/official source. - Hold if no usable source context was captured. - Never invent player stats, rankings, quotes, injuries, or milestones. - Final score must be present, or packet is held. - Store facts, summaries, and links only. Do not copy full article text.
```
