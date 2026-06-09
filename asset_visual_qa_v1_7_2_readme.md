# HSD Asset Visual QA v1.7.2

Use this package to replace the v1.7.1 workflow files.

## Key upgrade

This version adds a hard prompt sanitizer layer and routes the graphics chat upload pack through sanitized prompt files before handoff.

## New outputs

- `graphics_clean_prompts/`
- `graphics_prompt_clean_report.md`
- `graphics_prompt_clean_manifest.json`

## Run order

1. Asset Desk
2. Player Image Assets
3. Visual Upgrade
4. Graphics Production Specs
5. Graphics Language Pack
6. Graphics Prompt Sanitizer
7. Graphics Upload Pack
8. Graphics QA
9. Archive
