# HSD Tennis / WTA Final Cleanup — JSON Specs

This markdown contains the real machine-readable JSON layout specs for the final cleanup package for:

**TENNIS / WTA**

## Package contents

- `public_mockups/`
- `layout_references/`
- `json_specs/`
- `WHEN_TO_USE.md`
- `HSD_Tennis_WTA_Final_Cleanup_JSON_Specs.md`

## Global HSD rules

- Use the uploaded official compact HSD badge exactly as provided.
- Place one badge only in the top-left.
- Keep the badge small and secondary to the content.
- Feed / Threads badge: `x: 48`, `y: 42`, `width: 80–96`.
- Stories / Reels badge: `x: 52`, `y: 48`, `width: 88–104`.
- Use approved player image slots only when a real approved image exists.
- Use approved tournament/event logo slots only when available.
- For public template mockups, tour/event logo areas should be optional and labeled `APPROVED TOUR / EVENT LOGO SLOT` unless an approved logo is provided.
- Abstract tennis textures are allowed as design backgrounds.
- Public mockups must be clean and publish-ready.
- Blank references may include labels such as `APPROVED IMAGE SLOT` and `APPROVED LOGO SLOT`.
- Use placeholder copy unless real details are provided.
- Do not invent scores, opponents, tournament names, rounds, records, rankings, quotes, injuries, stats, faces, kits, or athletes.

## Variants

- **A:** Match Result / Match Preview Card
- **B:** Tournament Story / Advancement Card
- **C:** Story / Vertical Tennis Update

## Variant A — Match Result / Match Preview Card

**When to use:** Use for a WTA match result or preview where the core information is player, opponent, tournament, round, and scoreline or next-match context.

```json
{
  "template_id": "hsd_tennis_wta_variant_a_match_result_card",
  "family": "tennis_wta",
  "variant": "A",
  "template_name": "Match Result Card",
  "format": "ig_feed_threads",
  "canvas": {
    "width": 1080,
    "height": 1350
  },
  "safe_zones": {
    "top": 90,
    "right": 60,
    "bottom": 90,
    "left": 60
  },
  "badge": {
    "asset": "official_hsd_badge_reference.png",
    "x": 48,
    "y": 42,
    "width_min": 80,
    "width_max": 96,
    "placement": "top-left",
    "rules": [
      "Use official compact HSD badge exactly as uploaded.",
      "Use one badge only.",
      "Keep badge small and secondary.",
      "Do not recreate logo as text.",
      "Do not add HER SPORTS DAILY beside the badge."
    ]
  },
  "public_mockup": "public_mockups/01_tennis_wta_A_match_result_public.png",
  "layout_reference": "layout_references/02_tennis_wta_A_match_result_layout_reference.png",
  "center_result_area": {
    "mode_rule": "Only one mode should be active at a time.",
    "result_mode": {
      "primary_line": "PLAYER NAME def. OPPONENT",
      "secondary_line": "SET SCORELINE",
      "editable_fields": [
        "PLAYER NAME",
        "OPPONENT NAME",
        "RESULT / SCORELINE"
      ]
    },
    "preview_mode": {
      "primary_line": "PLAYER NAME vs OPPONENT",
      "secondary_line": "ROUND / TIME / TOURNAMENT",
      "editable_fields": [
        "PLAYER NAME",
        "OPPONENT NAME",
        "ROUND NAME",
        "TOURNAMENT NAME",
        "NEXT MATCH"
      ]
    }
  },
  "zones": {
    "round_name": {
      "x": 365,
      "y": 140,
      "w": 350,
      "h": 62,
      "text_role": "ROUND NAME"
    },
    "tournament_name": {
      "x": 285,
      "y": 235,
      "w": 510,
      "h": 55,
      "text_role": "TOURNAMENT NAME"
    },
    "player_name": {
      "x": 150,
      "y": 330,
      "w": 780,
      "h": 330,
      "text_role": "PLAYER NAME"
    },
    "opponent_line": {
      "x": 250,
      "y": 705,
      "w": 580,
      "h": 85,
      "text_role": "def. OPPONENT NAME or vs OPPONENT NAME"
    },
    "result_scoreline": {
      "x": 275,
      "y": 815,
      "w": 530,
      "h": 70,
      "text_role": "RESULT / SCORELINE"
    },
    "why_it_matters": {
      "x": 230,
      "y": 955,
      "w": 700,
      "h": 90,
      "text_role": "WHY IT MATTERS"
    },
    "question_cta": {
      "x": 230,
      "y": 1095,
      "w": 700,
      "h": 110,
      "text_role": "QUESTION / CTA"
    },
    "approved_tour_event_logo_slot": {
      "x": 825,
      "y": 60,
      "w": 180,
      "h": 160,
      "asset_role": "APPROVED TOUR / EVENT LOGO SLOT",
      "optional": true
    },
    "approved_image_slot_or_abstract_texture": {
      "x": 760,
      "y": 760,
      "w": 240,
      "h": 300,
      "asset_role": "APPROVED IMAGE SLOT or abstract tennis texture",
      "optional": true
    }
  },
  "placeholder_fields": [
    "PLAYER NAME",
    "OPPONENT NAME",
    "TOURNAMENT NAME",
    "ROUND NAME",
    "RESULT / SCORELINE",
    "NEXT MATCH",
    "WHY IT MATTERS",
    "QUESTION / CTA"
  ],
  "renderer_notes": [
    "Do not require result mode and preview mode at the same time.",
    "WIN / RESULT should be an editable field, not hardcoded.",
    "Use confirmed scorelines only.",
    "Use approved tour/event logo only when provided.",
    "Abstract tennis textures are allowed as design backgrounds.",
    "Public mockups must be clean and publish-ready."
  ],
  "when_to_use": "Use for a WTA match result or preview where the core information is player, opponent, tournament, round, and scoreline or next-match context."
}
```

## Variant B — Tournament Story / Advancement Card

**When to use:** Use for WTA advancement stories, title runs, upset stories, milestones, seed stories, bracket movement, or broader tournament moments.

```json
{
  "template_id": "hsd_tennis_wta_variant_b_tournament_story_advancement",
  "family": "tennis_wta",
  "variant": "B",
  "template_name": "Tournament Story / Advancement Card",
  "format": "ig_feed_threads",
  "canvas": {
    "width": 1080,
    "height": 1350
  },
  "safe_zones": {
    "top": 90,
    "right": 60,
    "bottom": 90,
    "left": 60
  },
  "badge": {
    "asset": "official_hsd_badge_reference.png",
    "x": 48,
    "y": 42,
    "width_min": 80,
    "width_max": 96,
    "placement": "top-left",
    "rules": [
      "Use official compact HSD badge exactly as uploaded.",
      "Use one badge only.",
      "Keep badge small and secondary.",
      "Do not recreate logo as text.",
      "Do not add HER SPORTS DAILY beside the badge."
    ]
  },
  "public_mockup": "public_mockups/03_tennis_wta_B_tournament_story_public.png",
  "layout_reference": "layout_references/04_tennis_wta_B_tournament_story_layout_reference.png",
  "headline_options": [
    "PLAYER NAME ADVANCES",
    "TOURNAMENT STORY HEADLINE",
    "TITLE RUN CONTINUES",
    "UPSET STORY HEADLINE",
    "MILESTONE STORY HEADLINE"
  ],
  "zones": {
    "round_name": {
      "x": 365,
      "y": 140,
      "w": 350,
      "h": 62,
      "text_role": "ROUND NAME"
    },
    "tournament_name": {
      "x": 285,
      "y": 235,
      "w": 510,
      "h": 55,
      "text_role": "TOURNAMENT NAME"
    },
    "story_headline": {
      "x": 90,
      "y": 320,
      "w": 780,
      "h": 430,
      "text_role": "PLAYER NAME ADVANCES / TOURNAMENT STORY HEADLINE"
    },
    "short_context": {
      "x": 120,
      "y": 825,
      "w": 810,
      "h": 105,
      "text_role": "SHORT CONTEXT"
    },
    "why_it_matters": {
      "x": 120,
      "y": 960,
      "w": 810,
      "h": 115,
      "text_role": "WHY IT MATTERS"
    },
    "source_note_or_cta": {
      "x": 120,
      "y": 1110,
      "w": 810,
      "h": 110,
      "text_role": "SOURCE NOTE OR CTA / QUESTION / CTA"
    },
    "approved_tour_event_logo_slot": {
      "x": 825,
      "y": 60,
      "w": 180,
      "h": 160,
      "asset_role": "APPROVED TOUR / EVENT LOGO SLOT",
      "optional": true
    },
    "approved_image_slot_or_abstract_texture": {
      "x": 735,
      "y": 290,
      "w": 275,
      "h": 420,
      "asset_role": "APPROVED IMAGE SLOT or abstract tennis texture",
      "optional": true
    }
  },
  "placeholder_fields": [
    "PLAYER NAME",
    "TOURNAMENT NAME",
    "ROUND NAME",
    "SHORT CONTEXT",
    "WHY IT MATTERS",
    "SOURCE NOTE OR CTA",
    "QUESTION / CTA"
  ],
  "renderer_notes": [
    "Use a clearly editable headline option.",
    "Do not make the public mockup look like a specific real event unless real details are provided.",
    "Use approved tour/event logo slot only unless an approved logo is provided.",
    "Do not include website URLs on public templates.",
    "Abstract tennis textures are allowed as backgrounds."
  ],
  "when_to_use": "Use for WTA advancement stories, title runs, upset stories, milestones, seed stories, bracket movement, or broader tournament moments."
}
```

## Variant C — Story / Vertical Tennis Update

**When to use:** Use for quick vertical tennis updates, including match results, next-match previews, tournament story updates, and player spotlights.

```json
{
  "template_id": "hsd_tennis_wta_variant_c_story_vertical_update",
  "family": "tennis_wta",
  "variant": "C",
  "template_name": "Story / Vertical Tennis Update",
  "format": "ig_story_reels",
  "canvas": {
    "width": 1080,
    "height": 1920
  },
  "safe_zones": {
    "top": 120,
    "right": 60,
    "bottom": 140,
    "left": 60
  },
  "badge": {
    "asset": "official_hsd_badge_reference.png",
    "x": 52,
    "y": 48,
    "width_min": 88,
    "width_max": 104,
    "placement": "top-left",
    "rules": [
      "Use official compact HSD badge exactly as uploaded.",
      "Use one badge only.",
      "Keep badge small and secondary.",
      "Do not recreate logo as text.",
      "Do not add HER SPORTS DAILY beside the badge."
    ]
  },
  "public_mockup": "public_mockups/05_tennis_wta_C_story_vertical_public.png",
  "layout_reference": "layout_references/06_tennis_wta_C_story_vertical_layout_reference.png",
  "mode_rule": "Only one mode should be active at a time.",
  "allowed_modes": {
    "mode_1": {
      "name": "match result + question",
      "active_modules": [
        "player_name",
        "opponent_name",
        "result_scoreline",
        "why_it_matters",
        "question_cta"
      ]
    },
    "mode_2": {
      "name": "next match preview + question",
      "active_modules": [
        "player_name",
        "opponent_name",
        "next_match",
        "why_it_matters",
        "question_cta"
      ]
    },
    "mode_3": {
      "name": "tournament story update + why it matters",
      "active_modules": [
        "player_name",
        "tournament_name",
        "round_name",
        "story_summary",
        "why_it_matters"
      ]
    },
    "mode_4": {
      "name": "player spotlight + poll/question",
      "active_modules": [
        "player_name",
        "approved_image_slot",
        "story_summary",
        "optional_poll_question_sticker",
        "question_cta"
      ]
    }
  },
  "zones": {
    "round_name": {
      "x": 330,
      "y": 150,
      "w": 420,
      "h": 65,
      "text_role": "ROUND NAME"
    },
    "tournament_name": {
      "x": 220,
      "y": 250,
      "w": 650,
      "h": 60,
      "text_role": "TOURNAMENT NAME"
    },
    "headline": {
      "x": 120,
      "y": 360,
      "w": 840,
      "h": 380,
      "text_role": "NEXT MATCH / TENNIS UPDATE"
    },
    "player_opponent_module": {
      "x": 115,
      "y": 805,
      "w": 850,
      "h": 240,
      "text_role": "PLAYER NAME vs OPPONENT NAME"
    },
    "next_match_or_result_area": {
      "x": 110,
      "y": 1065,
      "w": 860,
      "h": 135,
      "text_role": "NEXT MATCH or RESULT / SCORELINE"
    },
    "why_it_matters": {
      "x": 110,
      "y": 1235,
      "w": 860,
      "h": 115,
      "text_role": "WHY IT MATTERS"
    },
    "question_cta": {
      "x": 110,
      "y": 1395,
      "w": 860,
      "h": 130,
      "text_role": "QUESTION / CTA"
    },
    "approved_image_slot": {
      "x": 110,
      "y": 1580,
      "w": 860,
      "h": 185,
      "asset_role": "APPROVED IMAGE SLOT or abstract tennis texture",
      "optional": true
    },
    "approved_tour_event_logo_slot": {
      "x": 760,
      "y": 70,
      "w": 200,
      "h": 155,
      "asset_role": "APPROVED TOUR / EVENT LOGO SLOT",
      "optional": true
    },
    "story_ui_clear_zone": {
      "x": 0,
      "y": 1780,
      "w": 1080,
      "h": 140,
      "role": "Keep critical content above this zone"
    },
    "optional_poll_question_sticker": {
      "x": 115,
      "y": 1535,
      "w": 850,
      "h": 130,
      "role": "Optional poll/question sticker space",
      "optional": true
    }
  },
  "placeholder_fields": [
    "PLAYER NAME",
    "OPPONENT NAME",
    "TOURNAMENT NAME",
    "ROUND NAME",
    "RESULT / SCORELINE",
    "NEXT MATCH",
    "WHY IT MATTERS",
    "QUESTION / CTA"
  ],
  "renderer_notes": [
    "Only one mode should be active in a real use case.",
    "Do not include platform UI icons inside the graphic.",
    "Keep bottom clear for Story UI.",
    "Do not use fake athlete silhouettes or implied real player photography.",
    "Use abstract tennis textures or approved images only."
  ],
  "when_to_use": "Use for quick vertical tennis updates, including match results, next-match previews, tournament story updates, and player spotlights."
}
```

