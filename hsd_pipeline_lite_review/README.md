# HSD Pipeline Lite Review

Generated: 2026-06-10T02:43:23.093028+00:00

## Counts

- results_freshness_rows: 29
- news_fact_packets: 5
- studio_bundle_rows: 1
- upload_pack_rows: 1
- player_image_requirements: 1

## Results freshness

- fresh: 6
- stale: 23
- missing/other: 0

### Examples

- Indiana Fever beat Washington Mystics | 2026-06-08 | 50.7h | stale | top_womens_results.csv
- New York Liberty beat Connecticut Sun | 2026-06-08 | 50.7h | stale | top_womens_results.csv
- Las Vegas Aces beat Seattle Storm | 2026-06-08 | 50.7h | stale | top_womens_results.csv
- Atlanta Dream beat Chicago Sky | 2026-06-09 | 26.7h | stale | top_womens_results.csv
- Minnesota Lynx beat Dallas Wings | 2026-06-09 | 26.7h | stale | top_womens_results.csv
- Phoenix Mercury vs Golden State Valkyrie | 2026-06-09 | 26.7h | stale | top_womens_results.csv
- Connecticut Sun vs Toronto Tempo | 2026-06-10 | 2.7h | fresh | top_womens_results.csv
- Los Angeles Sparks vs Seattle Storm | 2026-06-10 | 2.7h | fresh | top_womens_results.csv

## Studio

- fresh packet rows: 5
- status counts: `{"blocked_stale_event": 5}`

### Examples

- Indiana Fever beat Washington Mystics | 2026-06-08 | 50.7h | blocked_stale_event | block
- Atlanta Dream beat Chicago Sky | 2026-06-09 | 26.7h | blocked_stale_event | block
- Las Vegas Aces beat Seattle Storm | 2026-06-08 | 50.7h | blocked_stale_event | block
- Minnesota Lynx beat Dallas Wings | 2026-06-09 | 26.7h | blocked_stale_event | block
- New York Liberty beat Connecticut Sun | 2026-06-08 | 50.7h | blocked_stale_event | block

## Upload packs

- Tonight in the W Preview: ready_with_review | ready 4/4 | missing 

## Stop reason

```
# HSD Pipeline Stop

Stopped after Studio Bridge because `studio_bundle_queue.csv` had zero rows.

Asset Visual QA was not run because it would otherwise package stale committed bundle files.

Most likely causes:
- News Sync rows were created but marked production_ready=No.
- Event dates were still missing or outside the freshness window.
- Studio Bridge filtered all rows before bundle creation.

Check `news_fact_packets.csv`, `studio_fresh_packet_report.md`, and `studio_fresh_packet_gate.csv`.

```
