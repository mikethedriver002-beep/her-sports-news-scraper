# HSD Phase 6B Template Renderer v4

Phase 6B introduces a proof-only renderer for the canonical WNBA template contract frozen in Phase 6A.

## Scope

Renderer v4 covers:

- `hsd_tonight_in_the_w_a`
- `hsd_game_recap_final_score_a`
- `hsd_game_recap_final_score_b`
- `hsd_game_recap_final_score_c_story`

It does **not** render Last Night templates yet. Those belong to Phase 6D.

## Design principle

Renderer v4 is a template-contract compiler. It reads the Phase 6A canonical JSON specs and approved mockup assets. It does not invent new layouts.

## Output status

All Renderer v4 outputs remain review-only.

`renderer_cutover_allowed = false`

Nothing from Phase 6B replaces `HSD_QUALITY_GRAPHICS` or operator handoff yet.

## Local commands

```bash
python scripts/validate_hsd_template_contract_v4.py --strict
python scripts/generate_hsd_template_renderer_v4.py --fixtures --strict
python scripts/validate_hsd_template_renderer_v4.py --strict
pytest tests/test_template_renderer_v4_phase6b.py
```

## Next phase

Phase 6C adds visual baseline comparison and mockup-diff gates before any production cutover.
