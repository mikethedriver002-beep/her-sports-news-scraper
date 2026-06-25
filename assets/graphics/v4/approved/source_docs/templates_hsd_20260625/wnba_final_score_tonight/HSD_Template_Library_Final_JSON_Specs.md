# HSD Template Library — Final Corrected JSON Specs

This markdown contains the real machine-readable JSON specs for the final corrected HSD template package.

## Final correction lock

- Public mockups are exported at exact platform sizes.
- IG Feed / Threads files are 1080 x 1350.
- Stories / Reels files are 1080 x 1920.
- Public mockups do not show internal labels like `VARIANT A`, `VARIANT B`, `VARIANT C`, or `TEMPLATE A`.
- Game Recap / Final Score uses `PRIMARY TEAM` / `SECONDARY TEAM` language so the template works even when the away team wins.
- Generic basketball-style logo marks are internal placeholders only.
- Blank layout references label logo areas as `APPROVED TEAM LOGO SLOT`.
- Crown / WINNER treatment is optional, not automatic.
- Brush-script hooks are optional, not required.
- The official compact HSD badge asset is the only badge. One badge only, top-left.
- Separate `.json` files are included in the `/json` folder.

## Game Recap / Final Score — Variant A

**When to use:** Default logo-first final score for IG Feed and Threads when no approved player photo is available.

```json
{
  "template_id": "hsd_game_recap_final_score_a",
  "family": "game_recap_final_score",
  "variant": "A",
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
    "w": 80,
    "h": 80,
    "rules": [
      "Use official compact HSD badge asset only",
      "Do not recreate as text",
      "Do not redesign the badge",
      "One badge only, top-left"
    ]
  },
  "zones": {
    "title": {
      "x": 60,
      "y": 120,
      "w": 960,
      "h": 170,
      "text_role": "game_recap_final_score_title"
    },
    "context_row": {
      "x": 60,
      "y": 330,
      "w": 960,
      "h": 68,
      "text_role": "date_location_competition_context"
    },
    "primary_logo_slot": {
      "x": 60,
      "y": 430,
      "w": 220,
      "h": 220,
      "asset_role": "approved_team_logo_slot"
    },
    "primary_team": {
      "x": 300,
      "y": 430,
      "w": 300,
      "h": 110,
      "text_role": "primary_team_name"
    },
    "primary_score": {
      "x": 600,
      "y": 390,
      "w": 420,
      "h": 360,
      "text_role": "primary_score"
    },
    "secondary_logo_slot": {
      "x": 60,
      "y": 680,
      "w": 220,
      "h": 220,
      "asset_role": "approved_team_logo_slot"
    },
    "secondary_team": {
      "x": 300,
      "y": 700,
      "w": 360,
      "h": 100,
      "text_role": "secondary_team_name"
    },
    "secondary_score": {
      "x": 660,
      "y": 690,
      "w": 280,
      "h": 250,
      "text_role": "secondary_score"
    },
    "key_performer": {
      "x": 60,
      "y": 960,
      "w": 960,
      "h": 150,
      "text_role": "optional_key_performer"
    },
    "hook_takeaway": {
      "x": 60,
      "y": 1130,
      "w": 960,
      "h": 160,
      "text_role": "optional_hook_or_question"
    }
  },
  "renderer_notes": [
    "Public mockup must not show internal variant labels.",
    "Use PRIMARY TEAM / SECONDARY TEAM or WINNING TEAM / OPPONENT only.",
    "Approved team logo slots only. Do not invent logos.",
    "Winner/crown treatment is optional and not automatic.",
    "Brush-script hook is optional, not required."
  ],
  "when_to_use": "Default logo-first final score for IG Feed and Threads when no approved player photo is available."
}
```

## Game Recap / Final Score — Variant B

**When to use:** Use when an approved player photo helps sell the final score story and there is a clear key performer angle.

```json
{
  "template_id": "hsd_game_recap_final_score_b",
  "family": "game_recap_final_score",
  "variant": "B",
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
    "w": 80,
    "h": 80,
    "rules": [
      "Use official compact HSD badge asset only",
      "Do not recreate as text",
      "Do not redesign the badge",
      "One badge only, top-left"
    ]
  },
  "zones": {
    "title": {
      "x": 60,
      "y": 120,
      "w": 960,
      "h": 170,
      "text_role": "game_recap_final_score_title"
    },
    "context_row": {
      "x": 60,
      "y": 330,
      "w": 960,
      "h": 68,
      "text_role": "date_time_location_competition"
    },
    "primary_logo_slot": {
      "x": 60,
      "y": 430,
      "w": 180,
      "h": 180,
      "asset_role": "approved_team_logo_slot"
    },
    "primary_team": {
      "x": 260,
      "y": 430,
      "w": 430,
      "h": 110,
      "text_role": "primary_team_name"
    },
    "primary_score": {
      "x": 60,
      "y": 560,
      "w": 620,
      "h": 300,
      "text_role": "primary_score"
    },
    "secondary_logo_slot": {
      "x": 60,
      "y": 880,
      "w": 180,
      "h": 180,
      "asset_role": "approved_team_logo_slot"
    },
    "secondary_team": {
      "x": 260,
      "y": 900,
      "w": 300,
      "h": 90,
      "text_role": "secondary_team_name"
    },
    "secondary_score": {
      "x": 260,
      "y": 980,
      "w": 220,
      "h": 120,
      "text_role": "secondary_score"
    },
    "approved_player_photo_slot": {
      "x": 700,
      "y": 430,
      "w": 320,
      "h": 520,
      "asset_role": "approved_player_photo_slot_only"
    },
    "key_performer": {
      "x": 700,
      "y": 970,
      "w": 320,
      "h": 120,
      "text_role": "optional_key_performer"
    },
    "hook_takeaway": {
      "x": 60,
      "y": 1130,
      "w": 960,
      "h": 160,
      "text_role": "optional_hook_or_takeaway"
    }
  },
  "renderer_notes": [
    "Public mockup must not show internal variant labels.",
    "Use only when an approved player photo exists.",
    "If no approved player photo exists, revert to Variant A.",
    "Approved team logo slots only. Do not invent logos.",
    "Winner/crown treatment is optional and not automatic.",
    "Brush-script hook is optional, not required."
  ],
  "when_to_use": "Use when an approved player photo helps sell the final score story and there is a clear key performer angle."
}
```

## Game Recap / Final Score — Variant C Stories/Reels

**When to use:** Fast vertical final-score post for Stories and Reels when speed and readability matter most.

```json
{
  "template_id": "hsd_game_recap_final_score_c_story",
  "family": "game_recap_final_score",
  "variant": "C",
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
    "x": 48,
    "y": 42,
    "w": 80,
    "h": 80,
    "rules": [
      "Use official compact HSD badge asset only",
      "Do not recreate as text",
      "Do not redesign the badge",
      "One badge only, top-left"
    ]
  },
  "zones": {
    "title": {
      "x": 80,
      "y": 160,
      "w": 920,
      "h": 180,
      "text_role": "quick_final_title"
    },
    "context_row": {
      "x": 80,
      "y": 380,
      "w": 920,
      "h": 70,
      "text_role": "game_context"
    },
    "primary_logo_slot": {
      "x": 80,
      "y": 500,
      "w": 260,
      "h": 260,
      "asset_role": "approved_team_logo_slot"
    },
    "primary_team": {
      "x": 380,
      "y": 520,
      "w": 300,
      "h": 120,
      "text_role": "primary_team_name"
    },
    "primary_score": {
      "x": 680,
      "y": 470,
      "w": 320,
      "h": 360,
      "text_role": "primary_score"
    },
    "secondary_logo_slot": {
      "x": 80,
      "y": 840,
      "w": 260,
      "h": 260,
      "asset_role": "approved_team_logo_slot"
    },
    "secondary_team": {
      "x": 380,
      "y": 870,
      "w": 320,
      "h": 120,
      "text_role": "secondary_team_name"
    },
    "secondary_score": {
      "x": 700,
      "y": 820,
      "w": 260,
      "h": 320,
      "text_role": "secondary_score"
    },
    "key_performer": {
      "x": 80,
      "y": 1220,
      "w": 920,
      "h": 140,
      "text_role": "optional_key_performer"
    },
    "hook_question": {
      "x": 80,
      "y": 1390,
      "w": 920,
      "h": 200,
      "text_role": "optional_hook_or_question"
    }
  },
  "renderer_notes": [
    "Public mockup must not show internal variant labels.",
    "Built for exact-size Stories/Reels.",
    "No player photo lane in this version.",
    "Approved team logo slots only. Do not invent logos.",
    "Winner/crown treatment is optional and not automatic.",
    "Brush-script hook is optional, not required."
  ],
  "when_to_use": "Fast vertical final-score post for Stories and Reels when speed and readability matter most."
}
```

## Tonight in the W — Template A

**When to use:** Premium matchup preview for IG Feed and Threads when you want a strong debate question plus one clean lower module.

```json
{
  "template_id": "hsd_tonight_in_the_w_a",
  "family": "matchup_preview",
  "variant": "A",
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
    "w": 80,
    "h": 80,
    "rules": [
      "Use official compact HSD badge asset only",
      "Do not recreate as text",
      "Do not redesign the badge",
      "One badge only, top-left"
    ]
  },
  "zones": {
    "headline": {
      "x": 60,
      "y": 90,
      "w": 960,
      "h": 220,
      "text_role": "tonight_in_the_w_headline"
    },
    "time_tv_context": {
      "x": 80,
      "y": 340,
      "w": 920,
      "h": 70,
      "text_role": "time_tv_context"
    },
    "left_logo_slot": {
      "x": 100,
      "y": 450,
      "w": 320,
      "h": 300,
      "asset_role": "approved_team_logo_slot"
    },
    "matchup_center": {
      "x": 450,
      "y": 500,
      "w": 180,
      "h": 150,
      "text_role": "versus_marker"
    },
    "right_logo_slot": {
      "x": 660,
      "y": 450,
      "w": 320,
      "h": 300,
      "asset_role": "approved_team_logo_slot"
    },
    "debate_question": {
      "x": 80,
      "y": 780,
      "w": 920,
      "h": 140,
      "text_role": "debate_question"
    },
    "active_lower_module": {
      "x": 80,
      "y": 960,
      "w": 920,
      "h": 290,
      "module_rule": "one_active_module_only"
    }
  },
  "allowed_modules": [
    "KEY MATCHUP",
    "WATCH POINT",
    "WHY IT MATTERS",
    "APPROVED PLAYER PHOTO SLOT"
  ],
  "renderer_notes": [
    "Public mockup must not show internal template labels.",
    "Approved team logo slots only. Do not invent logos.",
    "Only one lower module may be active per post.",
    "Do not stack Key Matchup, Watch Point, Why It Matters, and Approved Player Photo Slot together."
  ],
  "when_to_use": "Premium matchup preview for IG Feed and Threads when you want a strong debate question plus one clean lower module."
}
```

