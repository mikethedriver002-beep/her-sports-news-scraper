# HSD Logo Asset Catalog

Generated: `2026-06-26T20:19:24.996196+00:00`
Version: `hsd-logo-asset-catalog-v1`

Review-only catalog. This report does not approve logos, enable fallbacks, download assets, or change renderer behavior.

## Summary

- Rows: `17`
- Team logo rows: `15`
- League logo rows: `2`
- approved: `13`
- missing: `2`
- unapproved_review_required: `2`

## Source trust status

- blocked_stale_source_review_required: `1`
- league_logo_source_not_registered_review_required: `2`
- registered_source_policy_no_block_match: `14`

## Needs operator review

- `WNBA` league_logo `WNBA`: `missing`; readiness `optional_league_logo_file_missing_review_only`; fallback cue `league_mark_slot_stays_review_only_until_manual_source_and_file_review`; path `assets/leagues/wnba/logo.png`; action `optional_supply_league_logo_then_manual_review`
- `WNBA` team_logo `Atlanta Dream`: `unapproved_review_required`; readiness `local_logo_manual_review_required`; fallback cue `text_badge_or_placeholder_fallback_is_review_only_human_hold`; path `assets/leagues/wnba/teams/atlanta_dream/logo.png`; action `human_review_required_do_not_auto_enable`
- `WNBA` team_logo `Washington Mystics`: `unapproved_review_required`; readiness `local_logo_manual_review_required`; fallback cue `text_badge_or_placeholder_fallback_is_review_only_human_hold`; path `assets/leagues/wnba/teams/washington_mystics/logo.png`; action `human_review_required_do_not_auto_enable`
- `WOMENS_SOCCER` league_logo `WOMENS_SOCCER`: `missing`; readiness `optional_league_logo_file_missing_review_only`; fallback cue `league_mark_slot_stays_review_only_until_manual_source_and_file_review`; path `assets/leagues/womens_soccer/logo.png`; action `optional_supply_league_logo_then_manual_review`

## Manual source recheck

- `WNBA` team_logo `Portland Fire`: `blocked_stale_source_review_required`; source `https://upload.wikimedia.org/wikipedia/en/c/cf/Portland_Fire_logo.svg`; action `replace_or_reverify_blocked_source_before_manual_approval`

## Source policy warnings

- `WNBA` team_logo `Portland Fire`: blocked source substring `Portland_Fire_logo.svg`; source `https://upload.wikimedia.org/wikipedia/en/c/cf/Portland_Fire_logo.svg`; action `replace_or_reverify_blocked_source_before_manual_approval`

## Template scope

- `WNBA`: `game_recap_final_score.a.v1;game_recap_final_score.c.story.v1;last_night_in_the_w.a.v1;last_night_in_the_w.b.story.v1;last_night_in_the_w.c.carousel.v1;tonight_in_the_w.a.v1`
- `WOMENS_SOCCER`: `last_night_in_the_w.a.v1;last_night_in_the_w.b.story.v1;last_night_in_the_w.c.carousel.v1`
