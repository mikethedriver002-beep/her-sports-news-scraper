# HSD Graphics Copy Style Guide v1.7

Generated: 2026-06-09T20:17:39.833709+00:00

## Core rule

Keep verification and accuracy-lock language **internal**. Do not render it on the graphic.

The graphic can say:

- Final
- Final Score
- Dallas gets the win
- Dallas Wings Beat Los Angeles Sparks
- What stood out?

The graphic must not say:

- Verified Final
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- do not alter

## Voice

HSD should sound like a sharp women’s sports desk, not a database export.

Use short active headlines, human sports language, clean score echoes, and confident CTAs.

Avoid robotic verification language, harsh winner/loser tags, and internal QA terms.

## Separation of concerns

- `graphics_display_copy.csv` is the **display layer**. Only this language is meant to appear on graphics.
- `graphics_banned_language.csv` is the **guardrail layer**. These terms should be stripped from prompts and final graphics.
- `graphics_asset_usage_map.csv` is the **identity layer**. Every player image has a strict one-to-one mapping.
- `graphics_layout_blueprint.csv` is the **composition layer**. It tells the graphics chat what each slide must contain.

## Main WNBA display copy

- Slide 1: Dallas Wings Beat Los Angeles Sparks | Dallas handles L.A., 104-96 | 104-96
- Slide 2: Final Score | Dallas Wings 104, Los Angeles Sparks 96 | Dallas 104 · Sparks 96
- Slide 3: Top Performers | Dallas leaders and Sparks leaders from the same game | 
- Slide 4: What stood out? | Dallas 104, Los Angeles 96 | Final: 104-96

## Asset identity rule

Every player/person image has a one-to-one mapping. The graphics chat must use each image only for the named player in `graphics_asset_usage_map.csv`.
