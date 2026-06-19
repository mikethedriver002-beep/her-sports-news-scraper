# HSD Template Contract v4

## Authority

Phase 6A freezes one canonical WNBA source set from the uploaded `Templates-hsd.zip` archive:

- `hsd_template_final_corrected_with_json_markdown.zip`
- `hsd_last_night_in_the_w_final_clean_package_with_json_markdown.zip`

Older duplicate packages are explicitly excluded by `source_manifest_v4.json`.

## Canonical families

1. Tonight in the W — A
2. Game Recap / Final Score — A
3. Game Recap / Final Score — B with approved player photo
4. Game Recap / Final Score — C Story/Reels
5. Last Night in the W — A Feed/Threads
6. Last Night in the W — B Story/Reels
7. Last Night in the W — C Carousel package

## Non-negotiable rules

- The renderer compiles a registered template; it does not invent a house layout.
- The official badge is byte-locked by SHA-256: `2b58e41836539a918cccdc06f1776d6a4b2dc539553319c61c8e2a14c12ec444`.
- Only one badge appears, top-left.
- Public graphics contain no internal template or variant labels.
- Player imagery appears only in an approved player-photo slot.
- Final Score B downgrades to A when an approved player asset is unavailable.
- Tonight A keeps its approved upper geometry; a player image may occupy only the one active lower module.
- Feed, Story, and carousel variants are separate contracts.
- Silent font fallback is prohibited.
- Renderer v3 remains active while v4 is built in shadow mode; this contract does not cut over production.

## Canonical source pack

The binary source pack is stored at:

`assets/graphics/v4/approved/hsd_wnba_canonical_templates_v4.zip`

The registry locks the pack SHA-256 to:

`1bd7bddec9f1103694c5c001129f842f4059e8a0739378359dd78c89772278c7`

The pack contains exact public mockups, exact layout references, exact source JSON files, the official badge, and original source notes.

## Validation

```bash
python scripts/validate_hsd_template_contract_v4.py --strict
```

A passing report must contain:

```json
{
  "status": "passed_template_contract",
  "template_count": 7,
  "missing_assets": [],
  "invalid_zones": [],
  "duplicate_template_ids": [],
  "badge_hash_valid": true,
  "font_contract_status": "declared",
  "renderer_cutover_allowed": false
}
```

## Typography

The archive does not include font files. Phase 6A therefore freezes typography roles and prohibits silent substitution. Phase 6B must visually compare free/open candidates against the approved mockups before selecting them. No font file is committed by Phase 6A.
