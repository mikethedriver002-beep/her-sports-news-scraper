# Softball Asset Workflow Board

- Generated: `2026-06-27T17:20:53.297840+00:00`
- League: `Athletes Unlimited Softball League`
- Status: `review_only_workflow_ready`
- Scope: review-only operator workflow board; it reads source/contact/intake artifacts and writes no assets.
- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.

## Review Order

1. Open `data/asset_registry/softball/softball_logo_contact_sheet.csv` and compare logo candidates against source pages.
2. Record logo holds or source notes in `data/asset_registry/softball/softball_logo_review_intake.csv`; keep registry actions hold-only until a human explicitly approves later.
3. Open `data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv` and the team boards listed below.
4. Record athlete source and identity notes in `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`; keep local-file review false until Mike manually supplies a candidate file.
5. Use `data/asset_registry/softball/softball_review_walkthrough.md` for row-by-row pacing when doing a batch review sweep.

## Candidate Layer Clarity

- `local_candidate_path` values are proposed manual target paths only; this report does not create `headshot.png` files.
- `approved_marker_path` values are proposed manual marker paths only; this report does not create `.approved` markers.
- Proposed headshot path refs: `6`; files currently present: `0`.
- Proposed `.approved` path refs: `6`; markers currently present: `0`.
- Unsafe logo intake rows detected: `0`.
- Unsafe athlete intake rows detected: `0`.

## Logo Queue

1. Athletes Unlimited Softball League | league_mark | source=https://theausl.com/
2. Carolina Blaze | primary_logo | source=https://theausl.com/blaze/
3. Chicago Bandits | primary_logo | source=https://theausl.com/bandits/
4. Oklahoma City Spark | primary_logo | source=https://theausl.com/spark/
5. Portland Cascade | primary_logo | source=https://theausl.com/cascade/
6. Texas Volts | primary_logo | source=https://theausl.com/volts/
7. Utah Talons | primary_logo | source=https://theausl.com/talons/

## Athlete Team Boards

1. Carolina Blaze | board=`data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md` | roster=https://theausl.com/blaze/roster
2. Chicago Bandits | board=`data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md` | roster=https://theausl.com/bandits/roster
3. Oklahoma City Spark | board=`data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md` | roster=https://theausl.com/spark/roster
4. Portland Cascade | board=`data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md` | roster=https://theausl.com/cascade/roster
5. Texas Volts | board=`data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md` | roster=https://theausl.com/volts/roster
6. Utah Talons | board=`data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md` | roster=https://theausl.com/talons/roster
