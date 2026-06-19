# HSD Template Contract v4

## Status

Phase 6A freezes the approved WNBA template package as the visual source of truth. It does **not** activate Renderer v4 and does not modify the current production renderer.

## Canonical source pack

Repository path after manual upload:

`assets/graphics/v4/approved/hsd_wnba_canonical_templates_v4.zip`

Expected SHA-256:

`1bd7bddec9f1103694c5c001129f842f4059e8a0739378359dd78c89772278c7`

Expected size:

`34,672,444 bytes`

The source pack contains the exact corrected/final-clean JSON specifications, public mockups, layout references, source documentation, and official HSD badge selected from `Templates-hsd.zip`.

Older duplicate template packages are explicitly excluded by `source_manifest_v4.json`.

## Frozen WNBA families

1. `hsd_tonight_in_the_w_a`
2. `hsd_game_recap_final_score_a`
3. `hsd_game_recap_final_score_b`
4. `hsd_game_recap_final_score_c_story`
5. `hsd_last_night_in_the_w_variant_a_multi_game_feed`
6. `hsd_last_night_in_the_w_variant_b_story_rolling_recap`
7. `hsd_last_night_in_the_w_variant_c_carousel_cover_recap_package`

## Non-negotiable rendering rules

- The renderer must compile a registered template; it may not invent a new layout.
- The official badge is placed from the source pack and may not be recreated as text.
- Team logos must come from approved logo assets.
- Player imagery may appear only in the approved template slot or module.
- No approved player image means downgrade to the registered logos-first fallback.
- Feed geometry may not be reused for Story/Reels.
- Public exports may not include internal template labels, notes, or guides.
- Scores, stats, team names, and dates remain fact-locked upstream.
- Every output remains review-only until visual baselines and human approval pass.

## Player routing

- Preview without an approved player asset: Tonight A with a non-photo lower module.
- Preview with an approved player asset: Tonight A with `APPROVED PLAYER PHOTO SLOT` as the one active lower module.
- Single final without an approved player asset: Final Score A.
- Single final with an approved player asset: Final Score B.
- Story/Reels final: Final Score C.
- Multi-game feed recap: Last Night A.
- Multi-game vertical recap: Last Night B.
- Multi-slide recap: Last Night C.

## Typography contract

Phase 6A declares free/open candidates but intentionally does not select final fonts. Silent fallback is prohibited. Renderer cutover remains blocked until Phase 6B produces visual comparisons against the approved public mockups and records exact selected fonts and hashes.

Candidate families include Bebas Neue, League Gothic, Oswald, Inter, and Source Sans 3. No font files are distributed by this contract phase.

## Validation

Run:

```bash
python scripts/validate_hsd_template_contract_v4.py --strict
pytest tests/test_template_contract_v4.py
```

The strict validator checks:

- source archive path, size, and SHA-256
- exact seven-template registry
- semantic equality between repo specs and source-pack specs
- official badge hash and dimensions
- public mockup hashes and dimensions
- layout reference hashes and dimensions
- canvas and zone bounds
- player fallback routing
- font contract state
- duplicate and unknown template IDs

## Phase boundary

Phase 6A ends with a frozen, validated contract. Phase 6B starts the new Renderer v4 implementation in a shadow lane. Renderer v3 remains active until v4 passes visual baselines and explicit cutover approval.
