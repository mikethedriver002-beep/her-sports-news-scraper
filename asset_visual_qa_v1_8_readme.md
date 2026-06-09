# HSD Asset Visual QA v1.8

v1.8 adds the missing guardrails exposed by the latest graphics test.

## Main additions

- Studio Freshness Gate
- Player Image Fit Gate
- Rendered Slide QA
- Freshness-aware upload pack status
- Prompt crop guidance for public-source player images

## New scripts

- `generate_hsd_studio_freshness_gate_v1.py`
- `generate_hsd_player_image_fit_gate_v1.py`
- `generate_hsd_rendered_slide_qa_v1.py`

## New outputs

- `studio_freshness_gate.csv`
- `studio_stale_packet_queue.csv`
- `studio_freshness_report.md`
- `studio_freshness_manifest.json`
- `player_image_fit_gate.csv`
- `player_image_fit_report.md`
- `player_image_fit_manifest.json`
- `rendered_slide_qa.csv`
- `rendered_slide_qa_report.md`
- `rendered_slide_qa_manifest.json`

## What it fixes

- Blocks stale packets when the event date is missing or older than the allowed freshness window.
- Forces yesterday/last-night/carryover labeling if older packets are intentionally used.
- Flags player photos that may show non-current-team, overseas, college, or national-team jersey context.
- Gives the graphics chat tight-crop instructions when a player image is usable but jersey context is risky.
- Lets you upload finished graphics into `rendered_graphics_input/` and rerun QA against the actual exported slides.
