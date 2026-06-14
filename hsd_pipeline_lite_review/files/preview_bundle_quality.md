# HSD Preview Quality Gate

Version: hsd-preview-quality-gate-v3.2.5-bebe-ops-v2.4
Gate status: **PASS**
Target local date: 2026-06-14

## Checks

- **bundle_exists** [PASS] - Tonight in the W bundle exists.
- **preview_build_json_exists** [PASS] - studio_preview_build_v2.json exists.
- **target_date_present** [PASS] - Target date locked to 2026-06-14.
- **same_date_only** [PASS] - Only the target local date is present in the bundle.
- **no_robot_language** [PASS] - Prompt is sanitized for public-facing language.
- **complete_slate** [PASS] - All detected target-date games are represented.
- **mixed_dates** [PASS] - No mixed-date issue detected.
- **preview_has_no_scores_or_results** [PASS] - Preview copy does not contain score/final-result language.
- **slide_spec** [PASS] - Slide count and dimensions are locked to 4 x 1080x1350.
- **player_focus_present** [PASS] - Preview player focus rows are present.
- **premium_prompt** [PASS] - Prompt includes premium visual, slate-lock, and no-score instructions.

## Summary CSV

See `preview_bundle_quality_summary.csv` for the hard gate status used by BeBe Ops.
