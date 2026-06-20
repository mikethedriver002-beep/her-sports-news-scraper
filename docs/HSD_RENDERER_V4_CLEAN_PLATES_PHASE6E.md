# HSD Renderer v4.2 — Phase 6E Clean Plates and Near-Post-Ready Gate

## Purpose

Phase 6E removes flattened sample text, sample scores, sample logos, and sample-photo residue from the Phase 6A public mockups before dynamic content is rendered.

Renderer v4.2 no longer paints over a flattened public mockup. It uses:

1. a generated clean plate containing only approved static design,
2. a dynamic mask defining every editable region,
3. real team logos or the approved text fallback,
4. approved player assets when a player-photo variant is selected,
5. zero placeholder rendering layers.

## Clean-plate pipeline

`config/graphics/v4/clean_plates/clean_plate_recipes_v4.json` defines the dynamic regions for:

- Tonight in the W A,
- Final Score A,
- Final Score B,
- Final Score C Story.

`scripts/build_hsd_template_clean_plates_v4.py` creates:

- `assets/graphics/v4/approved/clean_plates/wnba/*_clean_plate.png`,
- `assets/graphics/v4/approved/dynamic_masks/wnba/*_dynamic_mask.png`,
- clean-plate hashes and mask-coverage evidence.

The generated plates and masks are runtime artifacts. The canonical Phase 6A public mockups remain immutable inputs.

## Renderer policy

Renderer v4.2:

- modifies only pixels inside the approved dynamic mask,
- preserves the approved static masthead, texture, light, badge, and composition,
- uses Noto Sans Display system fonts selected in the Phase 6E font contract,
- renders Tonight A in Watch Point and approved-player lower-module modes,
- renders Final Score A without a player image,
- renders Final Score B only when a readable player asset exists,
- downgrades Final Score B to A when a player asset is unavailable,
- renders Final Score C as the approved vertical quick-final family,
- never emits public placeholder labels such as `PRIMARY TEAM`, `APPROVED TEAM LOGO SLOT`, or `SCORE SLOT`.

## Near-post-ready definition

A render is a near-post-ready candidate when:

- clean-plate and dynamic-mask hashes match,
- placeholder-layer count is zero,
- zone-overflow count is zero,
- the image changes meaningfully inside the dynamic mask,
- changes outside the dynamic mask remain below threshold,
- team-logo mode is declared,
- no fixture-only player asset is used,
- the Phase 6C fidelity gate passes.

Near-post-ready does **not** mean approved to publish.

## Player fixtures

The dedicated Phase 6E workflow uses a fixture-only reference crop to prove player-slot geometry. Fixture-only player renders are automatically excluded from near-post-ready candidate counts. Real pipeline player variants become eligible only when the packaged approved player-asset lane supplies the image.

## Cutover policy

- `renderer_cutover_allowed` remains `false`.
- `cutover_allowed` remains `false`.
- Human visual approval is mandatory.
- No `HSD_QUALITY_GRAPHICS` production cutover occurs in Phase 6E.

## Free-only policy

Phase 6E uses repository assets, Pillow, CairoSVG, pytest, and free system fonts. It requires no paid API, paid feed, paid proxy, paid image provider, paid scraper, or paid LLM.
