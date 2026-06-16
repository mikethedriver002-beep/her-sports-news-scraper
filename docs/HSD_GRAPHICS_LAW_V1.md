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
