# HSD Last Night in the W — Final Clean JSON Specs

This markdown contains the real machine-readable JSON specs for the final clean **Last Night in the W** template family.

## Package contents

- `public_mockups/` — public-facing mockup PNGs.
- `layout_references/` — blank/editable internal layout reference PNGs.
- `json_specs/` — separate machine-readable JSON files.
- `WHEN_TO_USE.md` — short usage notes.
- `HSD_Last_Night_In_The_W_Final_JSON_Specs.md` — this markdown file.

## Global HSD rules

- Use the uploaded official compact HSD badge exactly as provided.
- One badge only, top-left.
- Keep the badge small and secondary to the content.
- Do not recreate the logo as text.
- Do not add HER SPORTS DAILY beside the badge.
- No fake athletes, fake jerseys, fake kits, fake logos, or invented stats.
- Use approved team logo slots only in blank layouts.
- Public mockups must not show internal labels such as variant labels, template names, spec sheet labels, or production notes.
- Use flexible slate subheads, not hardcoded slate counts.
- Use score placeholders such as `00–00` or `SCORE SLOT`.
- Winner emphasis comes from row order, accent color, and score hierarchy.
- Repeated WIN tags are not allowed.
- Real JSON specs are provided as separate `.json` files.

## Template variants

- **A:** Multi-game Feed / Threads recap
- **B:** Story rolling recap
- **C:** Carousel cover / recap package

## Variant A — Multi-game Feed / Threads recap

**When to use:** Use when recapping a WNBA slate of roughly 3 to 5 games on feed or Threads, with one result carrying the main emphasis.

```json
{
  "template_id": "hsd_last_night_in_the_w_variant_a_multi_game_feed",
  "family": "last_night_in_the_w",
  "variant": "A",
  "template_name": "Multi-game Feed / Threads recap",
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
    "w_min": 80,
    "w_max": 96,
    "rules": [
      "Use the official compact HSD badge exactly as provided.",
      "Use one badge only, top-left.",
      "Do not recreate the logo as text.",
      "Keep the badge small and secondary to the content."
    ]
  },
  "zones": {
    "headline": {
      "x": 120,
      "y": 70,
      "w": 840,
      "h": 260,
      "text_role": "LAST NIGHT IN THE W"
    },
    "slate_subhead": {
      "x": 170,
      "y": 345,
      "w": 740,
      "h": 70,
      "text_role": "dynamic_editable_subhead",
      "examples": [
        "[X] GAMES. ALL THE FINALS.",
        "[X] FINALS. ONE RECAP.",
        "TOP RESULTS. BIG MOMENTS."
      ]
    },
    "featured_result_row": {
      "x": 35,
      "y": 470,
      "w": 1010,
      "h": 165,
      "role": "lead_result_row"
    },
    "featured_result_tag_optional": {
      "x": 35,
      "y": 445,
      "w": 130,
      "h": 34,
      "optional": true
    },
    "supporting_result_rows": [
      {
        "x": 35,
        "y": 665,
        "w": 1010,
        "h": 135
      },
      {
        "x": 35,
        "y": 810,
        "w": 1010,
        "h": 135
      },
      {
        "x": 35,
        "y": 955,
        "w": 1010,
        "h": 135
      }
    ],
    "left_logo_slots": "Every result row contains APPROVED TEAM LOGO SLOT on the left.",
    "right_logo_slots": "Every result row contains APPROVED TEAM LOGO SLOT on the right.",
    "score_placeholder": {
      "allowed_values": [
        "00\u201300",
        "SCORE SLOT"
      ]
    },
    "bottom_takeaway_question": {
      "x": 40,
      "y": 1130,
      "w": 1000,
      "h": 150,
      "optional": true
    }
  },
  "renderer_notes": [
    "Use row order, accent color, and score hierarchy to make the primary result clear.",
    "Use one optional featured-result tag only on the lead result.",
    "Do not place the same tag on every row.",
    "Use approved team logo slots only for blank layouts.",
    "Keep public mockups clean: no internal labels, notes, or guides."
  ],
  "when_to_use": "Use when recapping a WNBA slate of roughly 3 to 5 games on feed or Threads, with one result carrying the main emphasis."
}
```

## Variant B — Story rolling recap

**When to use:** Use for Stories or Reels when you want a fast, scan-friendly vertical recap of multiple WNBA finals.

```json
{
  "template_id": "hsd_last_night_in_the_w_variant_b_story_rolling_recap",
  "family": "last_night_in_the_w",
  "variant": "B",
  "template_name": "Story rolling recap",
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
    "w_min": 88,
    "w_max": 104,
    "rules": [
      "Use the official compact HSD badge exactly as provided.",
      "Use one badge only, top-left.",
      "Do not recreate the logo as text.",
      "Keep the badge small and secondary to the content."
    ]
  },
  "zones": {
    "headline": {
      "x": 130,
      "y": 150,
      "w": 820,
      "h": 300,
      "text_role": "LAST NIGHT IN THE W"
    },
    "story_subhead": {
      "x": 110,
      "y": 485,
      "w": 860,
      "h": 90,
      "text_role": "dynamic_editable_subhead",
      "examples": [
        "[X] FINALS. ONE RECAP.",
        "TOP RESULTS. BIG MOMENTS.",
        "[X] GAMES. ALL THE FINALS."
      ]
    },
    "result_cards": [
      {
        "x": 90,
        "y": 640,
        "w": 900,
        "h": 140
      },
      {
        "x": 90,
        "y": 790,
        "w": 900,
        "h": 140
      },
      {
        "x": 90,
        "y": 940,
        "w": 900,
        "h": 140
      },
      {
        "x": 90,
        "y": 1090,
        "w": 900,
        "h": 140
      },
      {
        "x": 90,
        "y": 1240,
        "w": 900,
        "h": 140
      }
    ],
    "score_placeholder": {
      "allowed_values": [
        "00\u201300",
        "SCORE SLOT"
      ]
    },
    "takeaway_question_zone": {
      "x": 90,
      "y": 1460,
      "w": 900,
      "h": 160,
      "optional": true
    },
    "cta_zone": {
      "x": 90,
      "y": 1660,
      "w": 900,
      "h": 110,
      "optional": true
    }
  },
  "renderer_notes": [
    "Make the first result card slightly more prominent through order and hierarchy only.",
    "Do not repeat WIN tags on every row.",
    "Use approved team logo slots only for blank layouts.",
    "Keep public mockups clean: no internal labels, notes, or guides."
  ],
  "when_to_use": "Use for Stories or Reels when you want a fast, scan-friendly vertical recap of multiple WNBA finals."
}
```

## Variant C — Carousel cover / recap package

**When to use:** Use when you want a swipeable Instagram recap package with a strong cover, a featured final, a multi-game recap slide, and an end-question slide.

```json
{
  "template_id": "hsd_last_night_in_the_w_variant_c_carousel_cover_recap_package",
  "family": "last_night_in_the_w",
  "variant": "C",
  "template_name": "Carousel cover / recap package",
  "format": "ig_carousel",
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
    "w_min": 80,
    "w_max": 96,
    "rules": [
      "Use the official compact HSD badge exactly as provided.",
      "Use one badge only, top-left.",
      "Do not recreate the logo as text.",
      "Keep the badge small and secondary to the content."
    ]
  },
  "cover_slide": {
    "headline": {
      "x": 80,
      "y": 80,
      "w": 920,
      "h": 250,
      "text_role": "LAST NIGHT IN THE W"
    },
    "slate_subhead": {
      "x": 190,
      "y": 360,
      "w": 700,
      "h": 60,
      "text_role": "dynamic_editable_subhead",
      "examples": [
        "[X] GAMES. ALL THE FINALS.",
        "[X] FINALS. ONE RECAP.",
        "TOP RESULTS. BIG MOMENTS."
      ]
    },
    "modular_bottom_area": {
      "mode_1": "Featured finals row + swipe CTA",
      "mode_2": "Swipe CTA + question",
      "mode_3": "Featured finals only"
    },
    "featured_finals_row": {
      "x": 40,
      "y": 860,
      "w": 1000,
      "h": 230,
      "placeholders": "APPROVED TEAM LOGO SLOT + 00\u201300"
    },
    "swipe_cta": {
      "x": 140,
      "y": 1180,
      "w": 800,
      "h": 70,
      "optional": true
    }
  },
  "package_slides": {
    "slide_2_featured_final": "Single-game featured final slide with one final score and optional top performer.",
    "slide_3_multi_game_recap": "Multi-game recap slide for additional results.",
    "final_slide_question": "End-question slide to drive engagement."
  },
  "renderer_notes": [
    "Public mockup should show one clean example of the modular cover, not all bottom modes at once.",
    "Internal layout reference may show all three allowed bottom-area modes.",
    "Use approved team logo slots only for blank layouts.",
    "Keep public mockups clean: no internal labels, notes, or guides."
  ],
  "when_to_use": "Use when you want a swipeable Instagram recap package with a strong cover, a featured final, a multi-game recap slide, and an end-question slide."
}
```

