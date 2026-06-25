# HSD Daily Debrief Final Cleanup — JSON Specs

This markdown contains the real machine-readable JSON layout specs for **THE DAILY DEBRIEF** final cleanup package.

## Included files

- `public_mockups/01_daily_debrief_A_cover_slide_public.png`
- `public_mockups/02_daily_debrief_A_story_slide_public.png`
- `public_mockups/03_daily_debrief_A_end_question_slide_public.png`
- `layout_references/04_daily_debrief_A_carousel_system_layout_reference.png`
- `public_mockups/05_daily_debrief_B_summary_card_public.png`
- `layout_references/06_daily_debrief_B_summary_card_layout_reference.png`
- `public_mockups/07_daily_debrief_C_story_vertical_public.png`
- `layout_references/08_daily_debrief_C_story_vertical_layout_reference.png`
- `json_specs/*.json`
- `WHEN_TO_USE.md`

## Global rules

- Use the official compact HSD badge exactly as provided.
- One badge only, top-left.
- Keep the badge small and secondary.
- Feed / Threads badge: `x: 48`, `y: 42`, `width: 80–96`.
- Stories badge: `x: 52`, `y: 48`, `width: 88–104`.
- Public mockups must be publish-ready and free of internal labels.
- Use approved image/logo slots or abstract editorial textures.
- Keep text mobile-readable and inside safe zones.
- Use placeholder copy unless real details are provided.
- The Daily Debrief is broad women’s sports, not WNBA-only.

## Variant A — Carousel System

**When to use:** Use when HSD wants a full flagship daily roundup carousel with a cover, one slide per story, and an engagement-focused close.

```json
{
  "template_id": "hsd_daily_debrief_variant_a_carousel_system",
  "family": "the_daily_debrief",
  "variant": "A",
  "template_name": "Daily Debrief Carousel System",
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
    "placement": "top-left",
    "rules": [
      "Use the uploaded official compact HSD badge exactly as provided.",
      "Use one badge only.",
      "Keep the badge small and secondary to the content.",
      "Do not recreate the logo as text.",
      "Do not add HER SPORTS DAILY beside the badge."
    ]
  },
  "public_mockups": {
    "cover_slide": "public_mockups/01_daily_debrief_A_cover_slide_public.png",
    "story_slide": "public_mockups/02_daily_debrief_A_story_slide_public.png",
    "end_question_slide": "public_mockups/03_daily_debrief_A_end_question_slide_public.png"
  },
  "layout_reference": "layout_references/04_daily_debrief_A_carousel_system_layout_reference.png",
  "slides": {
    "cover_slide": {
      "purpose": "Set the tone for the daily broad women\u2019s sports roundup.",
      "zones": {
        "franchise_title": {
          "x": 80,
          "y": 150,
          "w": 700,
          "h": 480,
          "text_role": "THE DAILY DEBRIEF"
        },
        "editable_strapline": {
          "x": 80,
          "y": 930,
          "w": 850,
          "h": 90,
          "text_role": "strapline",
          "examples": [
            "3 STORIES. WHAT MATTERS TODAY.",
            "3 STORIES. ONE DAILY RESET.",
            "THE TOP STORIES IN WOMEN\u2019S SPORTS."
          ]
        },
        "story_count_cue": {
          "x": 80,
          "y": 1080,
          "w": 500,
          "h": 70,
          "text_role": "1 / 3 or swipe cue"
        },
        "optional_approved_image_slot_or_abstract_texture": {
          "x": 650,
          "y": 190,
          "w": 360,
          "h": 660,
          "asset_role": "approved_image_slot_or_abstract_editorial_texture",
          "optional": true
        }
      }
    },
    "story_slide": {
      "purpose": "Tell one story with context and why it matters.",
      "zones": {
        "story_number": {
          "x": 865,
          "y": 60,
          "w": 160,
          "h": 130,
          "text_role": "01 / 02 / 03"
        },
        "story_headline": {
          "x": 60,
          "y": 245,
          "w": 520,
          "h": 260,
          "text_role": "STORY HEADLINE"
        },
        "sport_league": {
          "x": 60,
          "y": 560,
          "w": 380,
          "h": 55,
          "text_role": "SPORT / LEAGUE"
        },
        "why_it_matters": {
          "x": 60,
          "y": 690,
          "w": 470,
          "h": 150,
          "text_role": "WHY IT MATTERS"
        },
        "short_context": {
          "x": 60,
          "y": 905,
          "w": 470,
          "h": 210,
          "text_role": "SHORT CONTEXT"
        },
        "source_note": {
          "x": 60,
          "y": 1190,
          "w": 430,
          "h": 75,
          "text_role": "SOURCE NOTE"
        },
        "optional_approved_image_slot": {
          "x": 560,
          "y": 210,
          "w": 470,
          "h": 1000,
          "asset_role": "approved_image_slot_or_abstract_texture",
          "optional": true
        }
      }
    },
    "end_question_slide": {
      "purpose": "Close the carousel with engagement.",
      "zones": {
        "engagement_headline": {
          "x": 80,
          "y": 330,
          "w": 820,
          "h": 270,
          "text_role": "YOUR TAKE?"
        },
        "question_cta": {
          "x": 80,
          "y": 760,
          "w": 880,
          "h": 250,
          "text_role": "QUESTION / CTA"
        },
        "support_line": {
          "x": 80,
          "y": 1130,
          "w": 820,
          "h": 90,
          "text_role": "conversation support line"
        },
        "abstract_conversation_graphic": {
          "x": 610,
          "y": 120,
          "w": 380,
          "h": 330,
          "role": "abstract speech bubble motif",
          "optional": true
        }
      }
    }
  },
  "story_fields": [
    "STORY HEADLINE",
    "SPORT / LEAGUE",
    "WHY IT MATTERS",
    "SHORT CONTEXT",
    "SOURCE NOTE",
    "QUESTION / CTA",
    "APPROVED IMAGE SLOT",
    "APPROVED LOGO SLOT"
  ],
  "renderer_notes": [
    "Carousel is capped at three stories max.",
    "Public mockups must not show internal labels, variant labels, spec labels, guide lines, or production notes.",
    "Cover, story slide, and end-question slide should feel like one cohesive system.",
    "Use placeholder copy unless real details are provided.",
    "Use approved image/logo slots or abstract editorial textures only.",
    "Do not use fake athletes, fake logos, real stats, real standings, real quotes, injuries, or scores unless provided.",
    "Daily Debrief should feel broad across women\u2019s sports, not WNBA-only."
  ],
  "when_to_use": "Use when HSD wants a full flagship daily roundup carousel with a cover, one slide per story, and an engagement-focused close."
}
```

## Variant B — Single-Image Summary Card

**When to use:** Use when HSD needs one feed or Threads card that quickly summarizes the day’s top three women’s sports stories.

```json
{
  "template_id": "hsd_daily_debrief_variant_b_summary_card",
  "family": "the_daily_debrief",
  "variant": "B",
  "template_name": "Daily Debrief Single-Image Summary Card",
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
    "placement": "top-left",
    "rules": [
      "Use the uploaded official compact HSD badge exactly as provided.",
      "Use one badge only.",
      "Keep the badge small and secondary to the content.",
      "Do not recreate the logo as text."
    ]
  },
  "public_mockup": "public_mockups/05_daily_debrief_B_summary_card_public.png",
  "layout_reference": "layout_references/06_daily_debrief_B_summary_card_layout_reference.png",
  "zones": {
    "franchise_title": {
      "x": 170,
      "y": 45,
      "w": 850,
      "h": 190,
      "text_role": "THE DAILY DEBRIEF"
    },
    "editable_strapline": {
      "x": 170,
      "y": 250,
      "w": 820,
      "h": 60,
      "text_role": "strapline",
      "examples": [
        "3 STORIES. WHAT MATTERS TODAY.",
        "3 STORIES. ONE DAILY RESET.",
        "THE TOP STORIES IN WOMEN\u2019S SPORTS."
      ]
    },
    "hero_story_block": {
      "x": 45,
      "y": 335,
      "w": 990,
      "h": 435,
      "role": "hero story"
    },
    "hero_approved_image_slot_or_texture": {
      "x": 80,
      "y": 380,
      "w": 330,
      "h": 320,
      "asset_role": "approved_image_slot_or_abstract_texture",
      "optional": true
    },
    "hero_story_text": {
      "x": 440,
      "y": 365,
      "w": 550,
      "h": 360,
      "text_role": "hero story headline, sport/league, short context, why it matters"
    },
    "supporting_story_1": {
      "x": 45,
      "y": 805,
      "w": 480,
      "h": 360,
      "role": "supporting story 2"
    },
    "supporting_story_2": {
      "x": 555,
      "y": 805,
      "w": 480,
      "h": 360,
      "role": "supporting story 3"
    },
    "bottom_question_cta": {
      "x": 45,
      "y": 1190,
      "w": 990,
      "h": 120,
      "text_role": "QUESTION / CTA"
    }
  },
  "story_fields": [
    "STORY HEADLINE",
    "SPORT / LEAGUE",
    "SHORT CONTEXT",
    "WHY IT MATTERS",
    "SOURCE NOTE",
    "QUESTION / CTA",
    "APPROVED IMAGE SLOT",
    "APPROVED LOGO SLOT"
  ],
  "renderer_notes": [
    "Use one hero story and two supporting stories.",
    "Use approved image/logo slots or abstract editorial textures.",
    "Blank references should label visual areas APPROVED IMAGE SLOT or APPROVED LOGO SLOT.",
    "Keep type mobile-readable and avoid tiny text.",
    "Public mockups must remain clean and publish-ready.",
    "Do not include real facts unless provided."
  ],
  "when_to_use": "Use when HSD needs one feed or Threads card that quickly summarizes the day\u2019s top three women\u2019s sports stories."
}
```

## Variant C — Story / Vertical Roundup

**When to use:** Use when HSD needs a quick vertical Daily Debrief roundup for Stories or Reels with three stacked story blocks.

```json
{
  "template_id": "hsd_daily_debrief_variant_c_story_vertical",
  "family": "the_daily_debrief",
  "variant": "C",
  "template_name": "Daily Debrief Story / Vertical Roundup",
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
    "placement": "top-left",
    "rules": [
      "Use the uploaded official compact HSD badge exactly as provided.",
      "Use one badge only.",
      "Keep the badge small and secondary to the content.",
      "Do not recreate the logo as text."
    ]
  },
  "public_mockup": "public_mockups/07_daily_debrief_C_story_vertical_public.png",
  "layout_reference": "layout_references/08_daily_debrief_C_story_vertical_layout_reference.png",
  "zones": {
    "franchise_title": {
      "x": 150,
      "y": 110,
      "w": 800,
      "h": 300,
      "text_role": "THE DAILY DEBRIEF"
    },
    "editable_strapline": {
      "x": 150,
      "y": 425,
      "w": 760,
      "h": 70,
      "text_role": "strapline",
      "examples": [
        "3 STORIES. WHAT MATTERS TODAY.",
        "3 STORIES. ONE DAILY RESET.",
        "THE TOP STORIES IN WOMEN\u2019S SPORTS."
      ]
    },
    "optional_lead_visual_or_texture": {
      "x": 80,
      "y": 530,
      "w": 920,
      "h": 230,
      "asset_role": "approved_image_slot_or_abstract_texture",
      "optional": true
    },
    "story_blocks": [
      {
        "x": 80,
        "y": 800,
        "w": 920,
        "h": 250,
        "role": "story block 01"
      },
      {
        "x": 80,
        "y": 1070,
        "w": 920,
        "h": 250,
        "role": "story block 02"
      },
      {
        "x": 80,
        "y": 1340,
        "w": 920,
        "h": 250,
        "role": "story block 03"
      }
    ],
    "poll_question_sticker_safe_space": {
      "x": 80,
      "y": 1625,
      "w": 920,
      "h": 150,
      "role": "optional poll/question sticker space",
      "notes": "Keep above Story UI and do not include platform UI icons in public graphic."
    },
    "bottom_clear_area": {
      "x": 0,
      "y": 1780,
      "w": 1080,
      "h": 140,
      "role": "Story UI safe area"
    }
  },
  "story_fields": [
    "STORY HEADLINE",
    "SPORT / LEAGUE",
    "WHY IT MATTERS",
    "SHORT CONTEXT",
    "QUESTION / CTA",
    "APPROVED IMAGE SLOT",
    "APPROVED LOGO SLOT"
  ],
  "renderer_notes": [
    "Three-story max layout.",
    "Keep bottom clear for Story UI.",
    "Do not include platform UI icons inside the graphic.",
    "Reserve optional poll/question sticker space above UI area.",
    "Use approved image/logo slots or abstract editorial textures only.",
    "Public mockups must not show internal labels or guides."
  ],
  "when_to_use": "Use when HSD needs a quick vertical Daily Debrief roundup for Stories or Reels with three stacked story blocks."
}
```

