# HSD Graphics Law v1

Her Sports Daily graphics are built as a governed template system, not as one-off generated art.

## 1. Public logo law

For every public-facing HSD graphic:

- Use one official compact HSD badge/bug only.
- Place the badge top-left.
- Keep the badge small and secondary to the story.
- Do not recreate the logo as editable text.
- Do not use the full HSD + HER SPORTS DAILY lockup on public post templates.
- Do not add HER SPORTS DAILY wordmark text beside the badge.
- Do not use large masthead-style brand blocks on public social posts.

Allowed exception: spec sheets, approval boards, internal brand documents, pitch decks, and reports may use the full lockup.

Default public badge placement:

- 1080x1350: x 48 px, y 42 px, width 80 px.
- 1080x1920: x 52 px, y 48 px, width 88 px.

## 2. Visual identity law

HSD graphics must feel:

- premium
- dark
- cinematic
- high contrast
- editorial
- sports-media native
- social-first
- fast to read
- clean and confident

HSD graphics must not feel:

- dashboard-like
- generic Canva
- cluttered
- infographic-heavy
- fake-AI-athlete style
- over-branded
- low-contrast

## 3. One strong idea law

Every public graphic must lead with one strong idea.

Hierarchy order:

1. Main story, headline, or result.
2. Teams, player, score, or matchup.
3. Time, TV, context, stat, or why it matters.
4. Engagement question or utility CTA.

Branding certifies the post. Branding does not compete with the story.

## 4. Asset truth law

Allowed assets:

- approved official HSD badge
- approved team logos
- approved league logos
- approved player photos
- approved event logos
- text-only or logo-only layouts

Forbidden assets:

- fake athletes
- fake silhouettes in production graphics
- fake jerseys
- fake kits
- fake logos
- invented scores
- invented stats
- invented player names
- invented jersey numbers
- demo player faces in public exports
- generic sports logo marks in public exports

If no approved player image exists, use a text or logo fallback such as KEY MATCHUP, WATCH POINT, WHY IT MATTERS, or PLAYER SPOTLIGHT TEXT.

## 5. Template system law

Each HSD template family must include:

1. Finished template mockup PNG.
2. Blank/editable layout reference PNG.
3. Machine-readable JSON layout spec as a real file.
4. Short when-to-use guidance.

A screenshot of a JSON/code block is not a layout spec. The JSON must exist as an actual file.

## 6. Template approval law

Template status flow:

- draft
- review_only
- approved
- production_approved

New templates start as review_only. The renderer may create review artifacts from review_only templates, but production use requires explicit approval.

## 7. Renderer law

The renderer is a compiler, not a designer.

Renderer responsibilities:

- read approved template specs
- insert approved assets
- populate verified copy fields
- export platform-specific PNGs
- preserve safe zones
- preserve logo law
- produce review artifacts

Renderer non-responsibilities:

- inventing layout taste
- inventing assets
- inventing stats
- choosing fake players
- overriding brand law

## 8. Safe zone and readability law

Default safe zones:

- 1080x1350: top 90, right 60, bottom 90, left 60.
- 1080x1920: top 120, right 60, bottom 140, left 60.

Readability targets:

- Normal text contrast target: 4.5:1.
- Large text contrast target: 3:1.
- Non-text UI contrast target: 3:1.
- Metadata should generally be at least 30 px on 1080x1350.
- Question/body text should generally be at least 44 px on 1080x1350.
- Color must not be the only cue.

## 9. Priority template families

Build and approve templates in this order:

1. Game Recap / Final Score.
2. Tonight in the W.
3. Last Night in the W.
4. The Daily Debrief.
5. Women’s Soccer / NWSL / USWNT.
6. Tennis / WTA.
7. LPGA / Golf.

## 10. Current operating mode

The current repo stage is template-building and review-only rendering.

Do not promote generated graphics to production automatically. Use artifacts to review templates and rendered output before promotion.

## 11. Game Recap / Final Score template law

The Game Recap / Final Score family has three review-approved directions:

### Variant A: Logo-first final score

- Default Game Recap / Final Score template.
- No player photo required.
- Player photo is not allowed in Variant A public output.
- If no approved player image exists, use a text-only key performer strip.
- Use approved team logos only.
- Use PRIMARY TEAM / SECONDARY TEAM or WINNING TEAM / OPPONENT language so the template works even when the away team wins.

### Variant B: Approved-player-photo final score

- Use only when an approved player photo exists.
- Approved player identity and rights status must be verified before use.
- If no approved player photo exists, fall back to Variant A.
- Do not use demo player faces, fake silhouettes, fake jersey numbers, or unverified player positions.

### Variant C: Story/Reels quick final

- Use for fast vertical final-score posts.
- Export at 1080x1920.
- Keep the bottom hook above Story/Reels UI safe area.
- No player photo required.
- Use text-first and logo-first hierarchy.

### Shared Game Recap cuts

- No public-facing internal labels such as VARIANT A, VARIANT B, TEMPLATE A, or TEMPLATE B.
- Generic sports-logo placeholders are internal only.
- Crown/winner treatments are optional, not automatic.
- Brush-script hooks are optional, not required.
- Do not show 0,000 or fake stat placeholders in public examples.
- Do not use unnecessary metadata unless it serves the story.

## 12. Last Night in the W template law

The Last Night in the W family has three review-approved directions:

### Variant A: Feed / Threads recap

- Default Last Night in the W feed and Threads recap.
- Best for 3 to 4 game slates.
- Use one featured result and supporting finals underneath.
- Use one bottom takeaway or question.
- If the slate has 5 or more games, use the Story rolling recap or carousel package instead.

### Variant B: Story/Reels rolling recap

- Use for vertical rolling recaps after multiple finals.
- Export at 1080x1920.
- Best for fast scanning, IG Stories, and Reels slideshow frames.
- Can hold 3 to 5 result rows.
- Keep the bottom CTA above Story/Reels UI safe area.

### Variant C: Carousel cover / recap package

- Use as the carousel opener for bigger slates or recap posts that need swipeable context.
- Bottom area must be modular.
- Allowed bottom modes: featured finals plus swipe CTA, swipe CTA plus question, or featured finals only.
- Do not stack all bottom modules at once.

### Shared Last Night in the W cuts

- Badge must stay small and secondary.
- No repeated WIN tags on every row.
- Winner emphasis should come from row order, accent color, and score hierarchy.
- Slate subhead must be dynamic, not hardcoded to a fixed game count.
- Score placeholders should use simple 00-00 or SCORE SLOT formatting.
- Public mockups must not show internal variant/template/spec labels.
- Approved team logos only, or approved team logo slots in blank references.
- No invented scores, records, stats, or standings.
- No tiny tables or spreadsheet-style layout.

## 13. Daily Debrief template law

The Daily Debrief family has three review-approved directions:

### Variant A: Carousel system

- Use for the full Daily Debrief carousel experience.
- Must include a cover slide, reusable story slide, and end-question slide.
- Best for days with three strong cross-sport stories.
- Use a 3-story max structure.
- Each story slide needs room for story headline, sport/league label, short context, why it matters, and an approved image/logo slot or abstract editorial texture.
- The end-question slide should drive discussion.

### Variant B: Single-image summary card

- Use for one fast Feed or Threads graphic summarizing the day’s top three stories.
- Must use one hero story plus two supporting stories.
- Must include sport/league labels and a bottom question or CTA.
- Best when HSD needs a quick broad daily roundup without a full carousel.

### Variant C: Story/Reels vertical roundup

- Use for a quick vertical Daily Debrief on Stories or Reels.
- Export at 1080x1920.
- Must use three stacked story blocks.
- May include optional poll/question sticker space.
- Bottom area must stay clear for Story/Reels UI.

### Shared Daily Debrief rules

- Daily Debrief must feel broader than WNBA by default.
- It can include WNBA, NWSL, USWNT, tennis, LPGA, college sports, volleyball, Olympic sports, business, culture, and major women’s sports moments.
- Keep the system to three stories max unless explicitly approved.
- Badge must stay small and secondary.
- Strapline must be editable, not hardcoded.
- Use approved image/logo slots or abstract editorial textures.
- Do not bake platform UI icons into Story graphics.
- Public mockups must not show internal variant/template/spec labels.
- Use placeholder copy unless real details are provided.
- Do not present real scores, records, stats, quotes, injuries, or standings unless provided and verified.

## 14. Women’s Soccer / NWSL / USWNT template law

The Women’s Soccer / NWSL / USWNT family has three review-approved directions:

### Variant A: Match Preview / Result card

- Use for women’s soccer match previews and result cards.
- Must support preview mode and result mode.
- Preview mode uses matchup/date/time/competition fields.
- Result mode uses team scores and FINAL or FULL TIME fields.
- Preview and result language must not be mixed.
- Do not show FULL TIME on a preview card.
- Use approved club, league, country, or federation logo slots.

### Variant B: League / Roster / Callup story card

- Use for roster stories, callups, league-wide news, transfers, awards, milestones, and major women’s soccer moments.
- Headline should be clearly editable unless real details are provided.
- Use fields such as ROSTER STORY HEADLINE, TEAM NAMES ROSTER, CALLUP STORY HEADLINE, or PLAYER / TEAM STORY for public template mockups.
- Include short context, why it matters, and optional source note or CTA.

### Variant C: Story / Vertical soccer update

- Use for quick women’s soccer updates on Stories or Reels.
- Export at 1080x1920.
- Allowed modes: score/match update plus CTA, three quick story points plus CTA, or roster/callup note plus poll/question.
- Only one mode should be active at a time.
- Bottom area must stay clear for Story/Reels UI.

### Shared Women’s Soccer rules

- Keep a soccer-specific identity while still feeling like HSD.
- Approved club, league, country, and federation logos only.
- Approved player images only.
- Abstract soccer textures are allowed as editorial design backgrounds.
- Abstract textures must not imply real match photography or replace approved imagery.
- Do not use fake kits, fake crests, invented scores, invented stats, or real-sounding news without provided details.
- Public mockups must not show internal variant/template/spec labels.
- Use placeholder copy unless real details are provided.
