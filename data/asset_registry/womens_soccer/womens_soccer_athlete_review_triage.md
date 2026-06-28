# Women's Soccer Athlete Review Triage

Generated: `2026-06-28T16:09:52.677745+00:00`

Review-only operator triage worksheet built from the verification queue and source-priority rows. Advisory source candidates remain in `advisory_source_candidate_urls`; generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.

## Summary

- Triage rows: `21`
- NWSL rows: `16`
- Europe rows: `5`
- Download-approved yes rows: `0`
- Blank download-law source_url rows: `21`

## Primary Manual Actions

- gray_area_reputable_lead_review: `5`
- identity_verification: `2`
- missing_local_asset: `5`
- official_roster_check: `6`
- source_candidate_review: `3`

## Safe Operator Path

- Work official NWSL roster checks first.
- Treat gray-area and reputable public leads as manual review leads only, never as official/current roster confirmation.
- Keep Europe rows source-candidate-only and not render-ready unless a later human intake and local assets support them.
- Do not copy advisory source candidates into download-law `source_url` without a later human-edited intake row.

## Worksheet Preview

| Rank | Action | Scope | League | Team | Sources | Named Players | Missing Local | Safe Next Action |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | official_roster_check | nwsl | nwsl | Angel City FC | 4 | 4 | 26 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 2 | official_roster_check | nwsl | nwsl | Denver Summit FC | 1 | 1 | 26 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 3 | official_roster_check | nwsl | nwsl | Gotham FC | 3 | 3 | 27 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 4 | official_roster_check | nwsl | nwsl | Houston Dash | 3 | 3 | 28 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 5 | official_roster_check | nwsl | nwsl | Kansas City Current | 4 | 4 | 31 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 6 | official_roster_check | nwsl | nwsl | San Diego Wave FC | 1 | 1 | 25 | Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback. |
| 7 | gray_area_reputable_lead_review | europe_top_flight | wsl_england | Wsl England | 13 | 0 | 12 | Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use. |
| 8 | gray_area_reputable_lead_review | europe_top_flight | liga_f_spain | Liga F Spain | 17 | 0 | 16 | Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use. |
| 9 | gray_area_reputable_lead_review | europe_top_flight | frauen_bundesliga_germany | Frauen Bundesliga Germany | 15 | 0 | 14 | Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use. |
| 10 | gray_area_reputable_lead_review | europe_top_flight | serie_a_women_italy | Serie A Women Italy | 13 | 0 | 12 | Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use. |
| 11 | gray_area_reputable_lead_review | europe_top_flight | arkema_premiere_ligue_france | Arkema Premiere Ligue France | 13 | 0 | 12 | Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use. |
| 12 | identity_verification | nwsl | nwsl | Orlando Pride | 1 | 1 | 28 | Verify named player identity against official source metadata before any future intake or asset work. |
| 13 | identity_verification | nwsl | nwsl | Washington Spirit | 1 | 1 | 27 | Verify named player identity against official source metadata before any future intake or asset work. |
| 14 | source_candidate_review | nwsl | nwsl | Chicago Stars FC | 1 | 0 | 28 | Open advisory source-candidate pages manually and classify source quality; keep Europe source-candidate-only. |
| 15 | source_candidate_review | nwsl | nwsl | Seattle Reign | 1 | 0 | 27 | Open advisory source-candidate pages manually and classify source quality; keep Europe source-candidate-only. |
| 16 | source_candidate_review | nwsl | nwsl | Utah Royals FC | 1 | 0 | 27 | Open advisory source-candidate pages manually and classify source quality; keep Europe source-candidate-only. |
| 17 | missing_local_asset | nwsl | nwsl | Bay FC | 0 | 0 | 30 | Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved. |
| 18 | missing_local_asset | nwsl | nwsl | Boston Legacy FC | 0 | 0 | 26 | Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved. |
| 19 | missing_local_asset | nwsl | nwsl | North Carolina Courage | 0 | 0 | 27 | Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved. |
| 20 | missing_local_asset | nwsl | nwsl | Portland Thorns FC | 0 | 0 | 31 | Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved. |
| 21 | missing_local_asset | nwsl | nwsl | Racing Louisville FC | 0 | 0 | 29 | Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved. |
