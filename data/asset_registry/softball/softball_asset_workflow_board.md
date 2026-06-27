# Softball Asset Workflow Board

- Generated: `2026-06-27T19:00:45.489288+00:00`
- League: `Athletes Unlimited Softball League`
- Status: `review_only_workflow_ready`
- Scope: review-only operator workflow board; it reads source/contact/intake artifacts and writes no assets.
- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.

## Next Human Action

- Open `data/asset_registry/hockey_softball_asset_review_action_queue.md` first.
- Work the queue top-to-bottom: open the listed board/contact sheet, then fill only the listed human-intake fields.
- Source-candidate-only athlete rows keep identity/local-file/approval fields held until a named athlete and local candidate asset exist.

## Review Order

1. Open `data/asset_registry/softball/softball_logo_contact_sheet.csv` and compare logo candidates against source pages.
2. Record logo holds or source notes in `data/asset_registry/softball/softball_logo_review_intake.csv`; keep registry actions hold-only until a human explicitly approves later.
3. Open `data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv` and the team boards listed below.
4. Record athlete source and identity notes in `data/asset_registry/softball/softball_athlete_photo_review_intake.csv`; keep local-file review false until Mike manually supplies a candidate file.
5. Use `data/asset_registry/softball/softball_review_walkthrough.md` for row-by-row pacing when doing a batch review sweep.

## Candidate Layer Clarity

- `local_candidate_path` values are proposed manual target paths only; this report does not create `headshot.png` files.
- `approved_marker_path` values are proposed manual marker paths only; this report does not create `.approved` markers.
- Proposed headshot path refs: `18`; files currently present: `0`.
- Proposed `.approved` path refs: `18`; markers currently present: `0`.
- Unsafe logo intake rows detected: `0`.
- Unsafe athlete intake rows detected: `0`.
- Source-candidate-only rows: `25`.
- Local asset present rows: `0`.

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
2. Carolina Blaze | board=`data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md` | roster=https://theausl.com/blaze/
3. Carolina Blaze | board=`data/asset_registry/softball/athlete_photo_contact_sheets/carolina_blaze.md` | roster=https://theausl.com/players/
4. Chicago Bandits | board=`data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md` | roster=https://theausl.com/bandits/roster
5. Chicago Bandits | board=`data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md` | roster=https://theausl.com/bandits/
6. Chicago Bandits | board=`data/asset_registry/softball/athlete_photo_contact_sheets/chicago_bandits.md` | roster=https://theausl.com/players/
7. Oklahoma City Spark | board=`data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md` | roster=https://theausl.com/spark/roster
8. Oklahoma City Spark | board=`data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md` | roster=https://theausl.com/spark/
9. Oklahoma City Spark | board=`data/asset_registry/softball/athlete_photo_contact_sheets/oklahoma_city_spark.md` | roster=https://theausl.com/players/
10. Portland Cascade | board=`data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md` | roster=https://theausl.com/cascade/roster
11. Portland Cascade | board=`data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md` | roster=https://theausl.com/cascade/
12. Portland Cascade | board=`data/asset_registry/softball/athlete_photo_contact_sheets/portland_cascade.md` | roster=https://theausl.com/players/
13. Texas Volts | board=`data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md` | roster=https://theausl.com/volts/roster
14. Texas Volts | board=`data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md` | roster=https://theausl.com/volts/
15. Texas Volts | board=`data/asset_registry/softball/athlete_photo_contact_sheets/texas_volts.md` | roster=https://theausl.com/players/
16. Utah Talons | board=`data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md` | roster=https://theausl.com/talons/roster
17. Utah Talons | board=`data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md` | roster=https://theausl.com/talons/
18. Utah Talons | board=`data/asset_registry/softball/athlete_photo_contact_sheets/utah_talons.md` | roster=https://theausl.com/players/
