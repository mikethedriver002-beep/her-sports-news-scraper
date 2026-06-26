# WNBA Athlete Photo Catalog Inventory

Generated: 2026-06-26

## Guardrails

- Review-only workstream.
- Free source records only.
- No paid APIs.
- No auto-approval.
- No file movement into publish-ready lanes.
- No publishing.

## Current Registry Files

- `athletes.csv`: 200 WNBA athlete rows with `athlete_id`, display name, team, roster source URL, and status.
- `athlete_aliases.csv`: 610 name variants mapped to athlete IDs.
- `athlete_sources.csv`: 15 official roster source rows, one per WNBA team/source entry.
- `athlete_images.csv`: 400 expected image slots, split into headshot and cutout rows.
- `athlete_image_candidates.csv`: 294 candidate image rows with source/image URLs for review.
- `athlete_image_match_review.csv`: 200 review rows with provider player IDs, WNBA CDN image URLs, match method, confidence, target path, and review status.
- `athlete_image_approved_assets.csv`: 196 local approved-asset ledger rows with marker paths and decision provenance.
- `athlete_image_needs_fix.csv`: 4 headshot rows requiring fix.
- `athlete_image_rejected.csv`: 0 rejected rows.
- `missing_athlete_images.csv`: 204 missing image rows.
- `roster_entities.csv`: 200 roster-derived athlete entity rows.
- `roster_names.csv`: 610 roster name variant rows.

## New Review Catalog Outputs

- `athlete_photo_catalog.csv`: generated review-only catalog with 400 rows.
- `athlete_photo_catalog.json`: schema-shaped JSON version of the generated catalog.
- `athlete_photo_catalog.md`: human-readable review summary.
- `athlete_photo_catalog_review_template.csv`: explicit template for future source-backed review rows.
- `athlete_photo_catalog_review_template.json`: template field dictionary and allowed values.

## Current Coverage

- Catalog rows: 400.
- Approved rows: 196.
- Missing rows: 204.
- Headshot rows approved: 196.
- Headshot rows missing: 4.
- Cutout rows missing: 200.
- Approved rows requiring manual source recheck: 196.
- Headshot rows with blank provider player ID in the canonical catalog output: 0.
- Rows with explicit source URL: 400.
- Rows with identity confidence: 200.

## Field Mapping

- Player IDs: `athlete_id` and `provider_player_id`.
- Source URLs: `source_url` is explicit in the generated catalog and is backfilled from match-review image URLs or roster source URLs.
- Local asset paths: `local_asset_path` and `approved_marker_path`.
- Approval status: `status` and `approval_status` are explicit in the generated catalog and the review template.
- Identity confidence: `identity_confidence` is explicit in the generated catalog when match-review confidence is available.
- Missing assets: `status=missing`, `missing_athlete_images.csv`, `missing_asset_reason`, and template fields `missing_asset` plus `missing_asset_reason`.

## Gaps

- The generated catalog confirms local headshot files and markers, but all 196 approved rows still require manual source recheck because their decision provenance is `default`.
- Provider player IDs are backfilled into all 200 headshot rows from review/approval sidecars.
- Cutouts are effectively not populated yet: 200 cutout rows are missing.
- Four headshot rows are still missing and should be reconciled through the review queue, not downloaded directly by this workstream.
- `source_url` and `identity_confidence` should become first-class generated catalog columns in a future code change; for now the review template provides the target structure without altering scripts.

## Next Integration Steps

1. Run the identity audit and close all `default` decision-source rows through a human source-backed review process.
2. Add or approve cutout assets only after manual crop/identity review.
3. Reconcile the four missing headshot rows through the review queue, not direct auto-downloads.
4. Keep renderer photo slots gated until rows have explicit source-backed identity confirmation and approved marker evidence.
