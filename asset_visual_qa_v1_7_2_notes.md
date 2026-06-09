# HSD Asset Visual QA v1.7.2 Notes

v1.7.2 is the hard prompt sanitizer release.

## What changed

- Added `generate_hsd_graphics_prompt_sanitizer_v1.py`.
- Added `graphics_clean_prompts/<post_slug>/00_PROMPT_TO_PASTE.md` output.
- The upload pack now prefers sanitized prompts automatically.
- The QA scorer now fails if banned/internal prompt language survives inside the upload prompt.
- Player image status now refreshes `asset_candidates_review.md` so the review packet is less misleading.
- Archive/review outputs now include the prompt sanitizer report and manifest.

## Main goal

Stop the graphics chat from seeing or rendering internal prompt-control language such as:

- Verified Final
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- Do not alter
