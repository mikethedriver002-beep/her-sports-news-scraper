# HSD Canonical Template Contract v4

## Status

Phase 6A freezes the approved WNBA template package as an immutable visual contract. It does not activate Renderer v4 and does not change the current production renderer.

## Canonical families

| Family | Canonical templates |
|---|---|
| Tonight in the W | `hsd_tonight_in_the_w_a` |
| Game Recap / Final Score | `hsd_game_recap_final_score_a`, `hsd_game_recap_final_score_b`, `hsd_game_recap_final_score_c_story` |
| Last Night in the W | `hsd_last_night_in_the_w_variant_a_multi_game_feed`, `hsd_last_night_in_the_w_variant_b_story_rolling_recap`, `hsd_last_night_in_the_w_variant_c_carousel_cover_recap_package` |

## Sources of truth

1. JSON specifications define exact canvas sizes, safe zones, registered modules, and asset slots.
2. Layout-reference images define approved geometry.
3. Public mockups define approved visible composition and hierarchy.
4. `official_hsd_badge_reference.png` is the only approved HSD badge for these templates.
5. The registry hash-locks every canonical input.

## Frozen routing rules

- Preview without a player asset: Tonight A using a non-photo lower module.
- Preview with an approved player asset: Tonight A using only the approved lower player-photo module.
- Final without a player asset: Final Score A.
- Final with an approved player asset: Final Score B, falling back to A when unavailable.
- Quick vertical final: Final Score C.
- Multi-game feed recap: Last Night A.
- Multi-game Story/Reels recap: Last Night B.
- Carousel recap package: Last Night C.

## Prohibited renderer behavior

- Inventing a new layout family or moving assets outside registered zones.
- Recreating the HSD badge as text or adding an unapproved tile behind it.
- Reusing Feed geometry for Story/Reels.
- Adding player rails, dual-player cards, or other portrait structures not present in the selected spec.
- Showing internal variant labels, guides, or notes in public exports.
- Silently substituting a generic typeface.

## Typography status

Phase 6A declares free/open candidate fonts but intentionally does not select one. Phase 6B must render typography comparison sheets against the canonical public mockups before selecting font files. Renderer cutover remains blocked until that comparison passes.

## Validation

```bash
python scripts/validate_hsd_template_contract_v4.py --strict
pytest tests/test_template_contract_v4.py
```

Expected result:

```json
{
  "status": "passed_template_contract",
  "template_count": 7,
  "badge_hash_valid": true,
  "font_contract_status": "declared",
  "blockers": []
}
```

## Phase boundary

Phase 6A only freezes and validates canonical inputs. Phase 6B builds Renderer v4 beside Renderer v3 and must add baseline screenshot comparisons before any output is promoted into `HSD_QUALITY_GRAPHICS`.
