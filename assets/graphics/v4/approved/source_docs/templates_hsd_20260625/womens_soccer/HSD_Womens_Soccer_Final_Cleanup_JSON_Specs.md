# HSD Women’s Soccer Final Cleanup — JSON Specs

This markdown contains the real machine-readable JSON layout specs for the final cleanup package for:

**WOMEN’S SOCCER / NWSL / USWNT**

## Package contents

- `public_mockups/`
- `layout_references/`
- `json_specs/`
- `WHEN_TO_USE.md`
- `HSD_Womens_Soccer_Final_Cleanup_JSON_Specs.md`

## Global HSD rules

- Use the uploaded official compact HSD badge exactly as provided.
- Place one badge only in the top-left.
- Keep the badge small and secondary to the content.
- Feed / Threads badge: `x: 48`, `y: 42`, `width: 80–96`.
- Stories / Reels badge: `x: 52`, `y: 48`, `width: 88–104`.
- Use approved logo slots and approved image slots only.
- Abstract soccer textures are allowed as design backgrounds.
- Abstract soccer textures should not imply real match photography or replace approved player/team imagery.
- Public mockups must be clean and publish-ready.
- Blank references may include labels such as `APPROVED LOGO SLOT` and `APPROVED IMAGE SLOT`.
- Use placeholder copy unless real details are provided.
- Do not invent scores, records, stats, standings, quotes, injuries, callups, transfers, logos, kits, faces, or athletes.

## Variants

- **A:** Match Preview / Match Result
- **B:** League / Roster / Callup Story
- **C:** Story / Vertical Soccer Update

## Variant A — Match Preview / Match Result

**When to use:** Use for a single women’s soccer match preview or result card across Feed and Threads.

```json
{
  "template_id": "hsd_womens_soccer_variant_a_match_preview_result",
  "family": "womens_soccer_nwsl_uswnt",
  "variant": "A",
  "template_name": "Match Preview / Match Result Card",
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
      "One badge only.",
      "Keep badge small and secondary.",
      "Do not recreate logo as text."
    ]
  },
  "public_mockup": "public_mockups/01_variant_A_match_preview_public.png",
  "layout_reference": "layout_references/02_variant_A_match_preview_result_layout_reference.png",
  "modes": {
    "preview_mode": {
      "center_module": {
        "primary_line": "TEAM ONE vs TEAM TWO",
        "secondary_line": "DATE / TIME / COMPETITION"
      },
      "rules": [
        "Do not show FULL TIME in preview mode.",
        "Use clean matchup hierarchy.",
        "Approved logo slots only.",
        "Optional approved image slot may be used subtly."
      ]
    },
    "result_mode": {
      "center_module": {
        "line_1": "TEAM ONE 00",
        "line_2": "TEAM TWO 00",
        "status_line": "FINAL / FULL TIME"
      },
      "rules": [
        "Use only after result is confirmed.",
        "Score hierarchy should be clean and readable.",
        "Approved logo slots only.",
        "Do not invent scores."
      ]
    }
  },
  "zones": {
    "league_competition_label": {
      "x": 250,
      "y": 110,
      "w": 580,
      "h": 55,
      "text_role": "LEAGUE / COMPETITION"
    },
    "headline": {
      "x": 60,
      "y": 190,
      "w": 960,
      "h": 225,
      "text_role": "MATCHUP / RESULT"
    },
    "team_logo_slot_left": {
      "x": 95,
      "y": 470,
      "w": 280,
      "h": 250,
      "asset_role": "APPROVED LOGO SLOT"
    },
    "team_logo_slot_right": {
      "x": 705,
      "y": 470,
      "w": 280,
      "h": 250,
      "asset_role": "APPROVED LOGO SLOT"
    },
    "center_matchup_result_module": {
      "x": 395,
      "y": 490,
      "w": 290,
      "h": 220,
      "role": "preview or result module"
    },
    "context_bar": {
      "x": 80,
      "y": 930,
      "w": 920,
      "h": 120,
      "text_role": "MATCH CONTEXT"
    },
    "question_cta_bar": {
      "x": 80,
      "y": 1140,
      "w": 920,
      "h": 125,
      "text_role": "QUESTION / CTA"
    },
    "optional_image_slot": {
      "x": 785,
      "y": 880,
      "w": 185,
      "h": 190,
      "asset_role": "APPROVED IMAGE SLOT",
      "optional": true
    }
  },
  "renderer_notes": [
    "Public mockup shown in preview mode should not display FULL TIME.",
    "Use placeholder copy unless real details are provided.",
    "Abstract soccer textures are allowed as background design only.",
    "Keep all key content inside safe zones."
  ],
  "when_to_use": "Use for a single women\u2019s soccer match preview or result card across Feed and Threads."
}
```

## Variant B — League / Roster / Callup Story

**When to use:** Use for roster news, callups, transfers, awards, milestones, or other women’s soccer editorial stories that are not centered on one match result.

```json
{
  "template_id": "hsd_womens_soccer_variant_b_league_roster_callup_story",
  "family": "womens_soccer_nwsl_uswnt",
  "variant": "B",
  "template_name": "League / Roster / Callup Story Card",
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
    "placement": "top-left"
  },
  "public_mockup": "public_mockups/03_variant_B_league_roster_callup_public.png",
  "layout_reference": "layout_references/04_variant_B_league_roster_callup_layout_reference.png",
  "headline_examples": [
    "ROSTER STORY HEADLINE",
    "TEAM NAMES ROSTER",
    "CALLUP STORY HEADLINE",
    "PLAYER / TEAM STORY"
  ],
  "zones": {
    "family_label": {
      "x": 185,
      "y": 110,
      "w": 700,
      "h": 60,
      "text_role": "LEAGUE / TEAM / COUNTRY"
    },
    "main_headline": {
      "x": 60,
      "y": 220,
      "w": 500,
      "h": 580,
      "text_role": "editable headline"
    },
    "abstract_texture_or_visual_panel": {
      "x": 570,
      "y": 180,
      "w": 420,
      "h": 960,
      "asset_role": "APPROVED IMAGE SLOT or abstract editorial texture",
      "optional": true
    },
    "short_context": {
      "x": 60,
      "y": 840,
      "w": 440,
      "h": 130,
      "text_role": "SHORT CONTEXT"
    },
    "why_it_matters": {
      "x": 60,
      "y": 995,
      "w": 450,
      "h": 150,
      "text_role": "WHY IT MATTERS"
    },
    "source_note": {
      "x": 60,
      "y": 1180,
      "w": 500,
      "h": 110,
      "text_role": "SOURCE NOTE"
    },
    "optional_logo_slot": {
      "x": 705,
      "y": 830,
      "w": 180,
      "h": 150,
      "asset_role": "APPROVED LOGO SLOT",
      "optional": true
    }
  },
  "renderer_notes": [
    "Public mockup must read as an editable template, not a specific reported roster event.",
    "Do not imply real callups, rosters, or transfers unless details are provided.",
    "Abstract soccer textures are allowed as backgrounds and should not replace approved team imagery.",
    "Use approved image/logo slots only when real assets are available."
  ],
  "when_to_use": "Use for roster news, callups, transfers, awards, milestones, or other women\u2019s soccer editorial stories that are not centered on one match result."
}
```

## Variant C — Story / Vertical Soccer Update

**When to use:** Use for quick vertical women’s soccer updates in Stories or Reels, including match updates, roster notes, or fast editorial recap points.

```json
{
  "template_id": "hsd_womens_soccer_variant_c_story_vertical_update",
  "family": "womens_soccer_nwsl_uswnt",
  "variant": "C",
  "template_name": "Story / Vertical Soccer Update",
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
    "placement": "top-left"
  },
  "public_mockup": "public_mockups/05_variant_C_story_vertical_public.png",
  "layout_reference": "layout_references/06_variant_C_story_vertical_layout_reference.png",
  "placeholder_fields": [
    "STORY UPDATE",
    "MATCH CONTEXT",
    "WHY IT MATTERS",
    "KEY DETAIL",
    "QUESTION / CTA"
  ],
  "modes": {
    "mode_1": {
      "name": "score/match update + CTA",
      "active_modules": [
        "headline",
        "score_or_matchup",
        "match_context",
        "why_it_matters",
        "question_cta"
      ]
    },
    "mode_2": {
      "name": "three quick story points + CTA",
      "active_modules": [
        "headline",
        "story_point_1",
        "story_point_2",
        "story_point_3",
        "question_cta"
      ]
    },
    "mode_3": {
      "name": "roster/callup note + poll/question",
      "active_modules": [
        "headline",
        "story_update",
        "key_detail",
        "question_cta",
        "optional_poll_space"
      ]
    }
  },
  "zones": {
    "headline": {
      "x": 55,
      "y": 145,
      "w": 470,
      "h": 350,
      "text_role": "STORY UPDATE"
    },
    "optional_logo_or_image_panel": {
      "x": 665,
      "y": 215,
      "w": 320,
      "h": 420,
      "asset_role": "APPROVED LOGO SLOT or APPROVED IMAGE SLOT",
      "optional": true
    },
    "score_or_matchup_area": {
      "x": 60,
      "y": 695,
      "w": 940,
      "h": 210,
      "text_role": "scoreline or matchup summary"
    },
    "module_stack_area": {
      "x": 70,
      "y": 960,
      "w": 940,
      "h": 620,
      "role": "modular story content"
    },
    "question_cta_area": {
      "x": 70,
      "y": 1590,
      "w": 940,
      "h": 155,
      "text_role": "QUESTION / CTA"
    },
    "optional_poll_space": {
      "x": 610,
      "y": 1595,
      "w": 340,
      "h": 120,
      "role": "poll/question sticker safe space",
      "optional": true
    },
    "story_ui_clear_zone": {
      "x": 0,
      "y": 1780,
      "w": 1080,
      "h": 140,
      "role": "keep content above Story UI"
    }
  },
  "renderer_notes": [
    "Do not include platform UI icons inside the actual graphic.",
    "Bottom area must stay clear for Story UI.",
    "Not every module must be active at once.",
    "Abstract soccer textures may be used as background only and should not imply real photography."
  ],
  "when_to_use": "Use for quick vertical women\u2019s soccer updates in Stories or Reels, including match updates, roster notes, or fast editorial recap points."
}
```

