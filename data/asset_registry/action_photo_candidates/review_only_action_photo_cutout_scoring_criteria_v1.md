# Review-Only Action Photo Cutout Scoring Criteria v1

Generated: `2026-06-28T00:00:00+00:00`

Scoring rubric for human/Gemini/ChatGPT review of already-discovered action-photo leads. It records labels for boundary clarity, limb/equipment isolation, background complexity, crop fit, aspect alignment, emotional intensity, and grid-break potential. It does not analyze images automatically, fetch source pages, download files, segment subjects, remove backgrounds, approve assets, or mark anything publish-ready.

## Scoring Contract

Return score labels and evidence notes only after source-page review. These criteria can inform future manual review and cutout planning, but no row is an asset approval, file write, render input, or publish-ready state.

## Summary

- Scoring rows: `8`
- Validation issues: `0`
- Rows with human yes in `download_approved`: `0`
- Review-only rows: `8`
- Publish-ready rows: `0`

## Criterion Groups

- aspect_alignment: `1`
- background: `1`
- crop_fit: `2`
- editorial_energy: `1`
- grid_break: `1`
- pose_isolation: `1`
- subject_boundary: `1`

## Criteria Preview

| ID | Group | Criterion | Score Field | Labels | Grid-Break Use |
| --- | --- | --- | --- | --- | --- |
| APCSC001 | subject_boundary | boundary_hair_clarity | `boundary_hair_clarity_score` | `high/medium/low/blocked` | High score helps future transparent cutout planning; it does not create a cutout. |
| APCSC002 | pose_isolation | limb_equipment_isolation | `limb_equipment_isolation_score` | `high/medium/low/blocked` | High score supports grid-break potential for limbs/equipment crossing layout lines. |
| APCSC003 | background | background_complexity | `background_complexity_score` | `low/medium/high/blocked` | Lower complexity is better for later review-only cutout planning. |
| APCSC004 | crop_fit | hero_crop_fit_feed | `hero_crop_fit_feed_score` | `high/medium/low/blocked` | High score means the source lead is worth deeper operator review. |
| APCSC005 | crop_fit | hero_crop_fit_story | `hero_crop_fit_story_score` | `high/medium/low/blocked` | Story fit helps future social formats but does not approve asset use. |
| APCSC006 | aspect_alignment | aspect_alignment | `aspect_alignment_score` | `feed/story/both/neither/unclear` | Use labels only; do not download or inspect local pixels. |
| APCSC007 | editorial_energy | emotional_intensity | `emotional_intensity_score` | `high/medium/low/unclear` | High energy improves premium editorial render potential. |
| APCSC008 | grid_break | grid_break_potential | `grid_break_potential_score` | `high/medium/low/blocked` | This is a planning score only; no segmentation or background removal is performed. |
