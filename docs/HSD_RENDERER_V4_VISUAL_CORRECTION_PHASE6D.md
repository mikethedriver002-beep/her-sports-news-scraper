# HSD Phase 6D Renderer v4 Visual Correction Pass

Phase 6D replaces the Phase 6B visual treatment with a corrected `v4.1` renderer pass.

The important change is architectural: the renderer now uses the Phase 6A approved public mockup as the template skin and repaints only registered dynamic zones. Phase 6B blurred the approved mockup and added its own diagonal/planet styling. That passed the first fidelity setup gate but still looked too far from the approved templates. Phase 6D pulls the output back toward the real template family.

## What changes

- Renderer version becomes `v4.1-phase6d-visual-correction-template-skin`.
- Approved public mockups are used as the visual skin, not as a blurred loose reference.
- Static mastheads remain from the approved template skin.
- Dynamic fields are painted only into registered zones.
- Diagonal stripe overlays and invented large visual motifs are removed.
- Fidelity thresholds become stricter.
- Production cutover remains blocked.

## What still does not happen

- No `HSD_QUALITY_GRAPHICS` cutover.
- No operator handoff approval.
- No visual approval automation.
- No posting-ready promotion.

## Command

```bash
python scripts/generate_hsd_template_renderer_v4.py --strict
python scripts/validate_hsd_template_renderer_v4.py --strict
python scripts/validate_hsd_template_fidelity_v4.py --strict
```

Expected result:

```json
{
  "renderer_version": "v4.1-phase6d-visual-correction-template-skin",
  "status": "passed_renderer_v4_validation",
  "blockers": [],
  "cutover_allowed": false
}
```
