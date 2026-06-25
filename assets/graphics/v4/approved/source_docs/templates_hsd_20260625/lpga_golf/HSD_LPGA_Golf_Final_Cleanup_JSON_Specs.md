# HSD LPGA / Golf Final Cleanup — JSON Specs

This markdown contains the real machine-readable JSON layout specs for the final cleanup package for:

**LPGA / GOLF**

## Package contents

- `public_mockups/`
- `layout_references/`
- `json_specs/`
- `WHEN_TO_USE.md`
- `HSD_LPGA_Golf_Final_Cleanup_JSON_Specs.md`

## Global HSD rules

- Use the uploaded official compact HSD badge exactly as provided.
- Place one badge only in the top-left.
- Keep the badge small and secondary to the content.
- Feed / Threads badge: `x: 48`, `y: 42`, `width: 80–96`.
- Stories / Reels badge: `x: 52`, `y: 48`, `width: 88–104`.
- Use approved player image slots only when a real approved image exists.
- Use approved tournament/event logo slots only when available.
- Abstract golf textures are allowed as design backgrounds.
- Public mockups must be clean and publish-ready.
- Blank references may include labels such as `APPROVED IMAGE SLOT`, `APPROVED LOGO SLOT`, and `APPROVED EVENT LOGO SLOT`.
- Use placeholder copy unless real details are provided.
- Do not invent scores, leaderboard positions, tournament names, rounds, results, records, quotes, injuries, rankings, stats, faces, kits, or athletes.

## Variants

- **A:** Winner / Champion Card
- **B:** Leaderboard / Standings Update Card
- **C:** Story / Vertical Golf Update

## Variant A — Winner / Champion Card

**When to use:** Use for an LPGA winner, champion moment, major victory, trophy-focused result, or major final-round win.

```json
{
  "template_id": "hsd_lpga_golf_variant_a_winner_champion_card",
  "family": "lpga_golf",
  "variant": "A",
  "template_name": "Winner / Champion Card",
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
  "public_mockup": "public_mockups/01_lpga_golf_A_winner_champion_public.png",
  "layout_reference": "layout_references/02_lpga_golf_A_winner_champion_layout_reference.png",
  "zones": {
    "tournament_name": {
      "x": 230,
      "y": 100,
      "w": 600,
      "h": 70,
      "text_role": "TOURNAMENT NAME"
    },
    "tour_series_label": {
      "x": 230,
      "y": 175,
      "w": 420,
      "h": 55,
      "text_role": "LPGA TOUR / SERIES"
    },
    "player_name": {
      "x": 70,
      "y": 255,
      "w": 700,
      "h": 425,
      "text_role": "PLAYER NAME"
    },
    "winner_champion": {
      "x": 70,
      "y": 680,
      "w": 780,
      "h": 105,
      "text_role": "WINNER / CHAMPION"
    },
    "result_score": {
      "x": 140,
      "y": 830,
      "w": 600,
      "h": 130,
      "text_role": "RESULT / SCORE"
    },
    "why_it_matters": {
      "x": 90,
      "y": 1010,
      "w": 430,
      "h": 175,
      "text_role": "WHY IT MATTERS"
    },
    "question_cta": {
      "x": 560,
      "y": 1010,
      "w": 430,
      "h": 175,
      "text_role": "QUESTION / CTA"
    },
    "abstract_trophy_visual_area": {
      "x": 720,
      "y": 240,
      "w": 300,
      "h": 560,
      "role": "abstract trophy/golf editorial visual",
      "optional": true,
      "asset_rule": "Treat as abstract editorial design unless approved event imagery is provided."
    },
    "approved_image_slot_optional": {
      "x": 170,
      "y": 1195,
      "w": 740,
      "h": 90,
      "asset_role": "APPROVED IMAGE SLOT",
      "optional": true
    },
    "approved_logo_slot_optional": {
      "x": 850,
      "y": 80,
      "w": 155,
      "h": 100,
      "asset_role": "APPROVED LOGO SLOT",
      "optional": true
    }
  },
  "placeholder_fields": [
    "PLAYER NAME",
    "TOURNAMENT NAME",
    "WINNER / CHAMPION",
    "RESULT / SCORE",
    "WHY IT MATTERS",
    "QUESTION / CTA"
  ],
  "renderer_notes": [
    "Keep winner/champion hierarchy clean and dominant.",
    "Trophy and golf visuals are abstract editorial design elements unless approved event imagery is provided.",
    "Use confirmed score/result only.",
    "Do not invent scores, tournament names, results, or player details.",
    "Public mockups must be clean and publish-ready."
  ],
  "when_to_use": "Use for an LPGA winner, champion moment, major victory, trophy-focused result, or major final-round win."
}
```

## Variant B — Leaderboard / Standings Update Card

**When to use:** Use for LPGA leaderboard updates, top 5 standings, final-round positioning, projected cut context, tournament status, or leaderboard-based storylines.

```json
{
  "template_id": "hsd_lpga_golf_variant_b_leaderboard_standings_update",
  "family": "lpga_golf",
  "variant": "B",
  "template_name": "Leaderboard / Standings Update Card",
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
      "Do not recreate logo as text."
    ]
  },
  "public_mockup": "public_mockups/03_lpga_golf_B_leaderboard_public.png",
  "layout_reference": "layout_references/04_lpga_golf_B_leaderboard_layout_reference.png",
  "round_status_examples": [
    "ROUND 1",
    "ROUND 2",
    "ROUND 3",
    "FINAL ROUND",
    "AFTER 18",
    "AFTER 36",
    "PROJECTED CUT"
  ],
  "zones": {
    "tournament_name": {
      "x": 200,
      "y": 90,
      "w": 650,
      "h": 70,
      "text_role": "TOURNAMENT NAME"
    },
    "tour_series_label": {
      "x": 200,
      "y": 165,
      "w": 420,
      "h": 55,
      "text_role": "LPGA TOUR / SERIES"
    },
    "leaderboard_update_headline": {
      "x": 60,
      "y": 235,
      "w": 820,
      "h": 285,
      "text_role": "LEADERBOARD UPDATE"
    },
    "round_status": {
      "x": 115,
      "y": 535,
      "w": 700,
      "h": 80,
      "text_role": "ROUND / STATUS"
    },
    "leaderboard_rows": [
      {
        "rank": 1,
        "x": 70,
        "y": 640,
        "w": 820,
        "h": 90,
        "player_text_role": "PLAYER NAME 1",
        "score_text_role": "SCORE SLOT"
      },
      {
        "rank": 2,
        "x": 70,
        "y": 745,
        "w": 820,
        "h": 80,
        "player_text_role": "PLAYER NAME 2",
        "score_text_role": "SCORE SLOT"
      },
      {
        "rank": 3,
        "x": 70,
        "y": 835,
        "w": 820,
        "h": 80,
        "player_text_role": "PLAYER NAME 3",
        "score_text_role": "SCORE SLOT"
      },
      {
        "rank": 4,
        "x": 70,
        "y": 925,
        "w": 820,
        "h": 80,
        "player_text_role": "PLAYER NAME 4",
        "score_text_role": "SCORE SLOT"
      },
      {
        "rank": 5,
        "x": 70,
        "y": 1015,
        "w": 820,
        "h": 80,
        "player_text_role": "PLAYER NAME 5",
        "score_text_role": "SCORE SLOT"
      }
    ],
    "short_context": {
      "x": 100,
      "y": 1115,
      "w": 820,
      "h": 95,
      "text_role": "SHORT CONTEXT"
    },
    "question_cta": {
      "x": 100,
      "y": 1230,
      "w": 840,
      "h": 90,
      "text_role": "QUESTION / CTA"
    },
    "approved_event_logo_slot_optional": {
      "x": 820,
      "y": 85,
      "w": 190,
      "h": 120,
      "asset_role": "APPROVED EVENT LOGO SLOT",
      "optional": true
    }
  },
  "placeholder_fields": [
    "TOURNAMENT NAME",
    "LEADERBOARD UPDATE",
    "ROUND / STATUS",
    "PLAYER NAME 1",
    "PLAYER NAME 2",
    "PLAYER NAME 3",
    "PLAYER NAME 4",
    "PLAYER NAME 5",
    "SCORE SLOT",
    "SHORT CONTEXT",
    "QUESTION / CTA"
  ],
  "renderer_notes": [
    "Keep a readable top-5 leaderboard structure.",
    "Round/status is editable and should use the allowed examples where helpful.",
    "Avoid tiny spreadsheet formatting.",
    "Use confirmed leaderboard positions and scores only.",
    "Lead row may be emphasized with accent color and hierarchy.",
    "Use approved event logo only when provided."
  ],
  "when_to_use": "Use for LPGA leaderboard updates, top 5 standings, final-round positioning, projected cut context, tournament status, or leaderboard-based storylines."
}
```

## Variant C — Story / Vertical Golf Update

**When to use:** Use for quick LPGA or women’s golf Stories/Reels updates, including winner moments, leaderboard snapshots, final-round storylines, and player spotlights.

```json
{
  "template_id": "hsd_lpga_golf_variant_c_story_vertical_update",
  "family": "lpga_golf",
  "variant": "C",
  "template_name": "Story / Vertical Golf Update",
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
      "Do not recreate logo as text."
    ]
  },
  "public_mockup": "public_mockups/05_lpga_golf_C_story_vertical_public.png",
  "layout_reference": "layout_references/06_lpga_golf_C_story_vertical_layout_reference.png",
  "mode_rule": "Only one mode should be active at a time.",
  "allowed_modes": {
    "mode_1": {
      "name": "winner/champion update",
      "active_modules": [
        "player_name",
        "tournament_name",
        "winner_champion",
        "result_score",
        "why_it_matters",
        "question_cta"
      ]
    },
    "mode_2": {
      "name": "leaderboard snapshot",
      "active_modules": [
        "player_name",
        "tournament_name",
        "leaderboard_position",
        "leaderboard_snapshot",
        "round_status",
        "why_it_matters",
        "question_cta"
      ]
    },
    "mode_3": {
      "name": "final-round story",
      "active_modules": [
        "player_name",
        "tournament_name",
        "round_status",
        "final_round_note",
        "why_it_matters",
        "next_update"
      ]
    },
    "mode_4": {
      "name": "player spotlight",
      "active_modules": [
        "player_name",
        "tournament_name",
        "approved_image_slot",
        "story_summary",
        "poll_question_sticker_space"
      ]
    }
  },
  "zones": {
    "tournament_name": {
      "x": 190,
      "y": 115,
      "w": 700,
      "h": 75,
      "text_role": "TOURNAMENT NAME"
    },
    "tour_series_label": {
      "x": 190,
      "y": 195,
      "w": 700,
      "h": 55,
      "text_role": "LPGA TOUR / GOLF STORY"
    },
    "headline_player_name": {
      "x": 65,
      "y": 290,
      "w": 650,
      "h": 320,
      "text_role": "PLAYER NAME / HEADLINE"
    },
    "leaderboard_position": {
      "x": 65,
      "y": 645,
      "w": 640,
      "h": 95,
      "text_role": "LEADERBOARD POSITION"
    },
    "leaderboard_snapshot": {
      "x": 65,
      "y": 765,
      "w": 650,
      "h": 320,
      "text_role": "LEADERBOARD SNAPSHOT"
    },
    "round_status": {
      "x": 65,
      "y": 1110,
      "w": 700,
      "h": 90,
      "text_role": "ROUND STATUS"
    },
    "why_it_matters": {
      "x": 65,
      "y": 1235,
      "w": 430,
      "h": 175,
      "text_role": "WHY IT MATTERS"
    },
    "question_cta": {
      "x": 530,
      "y": 1235,
      "w": 430,
      "h": 175,
      "text_role": "QUESTION / CTA"
    },
    "poll_question_sticker_space": {
      "x": 65,
      "y": 1430,
      "w": 895,
      "h": 110,
      "role": "POLL / QUESTION STICKER SPACE",
      "optional": true
    },
    "next_update": {
      "x": 65,
      "y": 1580,
      "w": 720,
      "h": 90,
      "text_role": "NEXT UPDATE / ROUND STATUS / FINAL ROUND NOTE / WATCH THIS SPACE",
      "optional": true
    },
    "approved_image_slot_optional": {
      "x": 610,
      "y": 355,
      "w": 360,
      "h": 475,
      "asset_role": "APPROVED IMAGE SLOT",
      "optional": true
    },
    "approved_logo_slot_optional": {
      "x": 760,
      "y": 70,
      "w": 200,
      "h": 125,
      "asset_role": "APPROVED LOGO SLOT",
      "optional": true
    },
    "story_ui_clear_zone": {
      "x": 0,
      "y": 1780,
      "w": 1080,
      "h": 140,
      "role": "Keep critical content above this zone"
    }
  },
  "editable_lower_note_examples": [
    "NEXT UPDATE",
    "ROUND STATUS",
    "FINAL ROUND NOTE",
    "WATCH THIS SPACE"
  ],
  "placeholder_fields": [
    "PLAYER NAME",
    "TOURNAMENT NAME",
    "RESULT / SCORE",
    "LEADERBOARD POSITION",
    "FINAL ROUND",
    "ROUND STATUS",
    "WHY IT MATTERS",
    "QUESTION / CTA",
    "NEXT UPDATE",
    "WATCH THIS SPACE"
  ],
  "renderer_notes": [
    "Fix spelling to LEADERBOARD POSITION.",
    "Do not bake platform poll UI into the graphic.",
    "Use POLL / QUESTION STICKER SPACE or QUESTION / CTA as clean editable areas.",
    "NEXT UPDATE is editable.",
    "Only one mode should be active in a real use case.",
    "Keep bottom area clear for Story UI."
  ],
  "when_to_use": "Use for quick LPGA or women\u2019s golf Stories/Reels updates, including winner moments, leaderboard snapshots, final-round storylines, and player spotlights."
}
```

