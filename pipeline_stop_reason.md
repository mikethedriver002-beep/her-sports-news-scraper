# HSD Pipeline Stop

Stopped after Studio Bridge because `studio_bundle_queue.csv` had zero rows.

Asset Visual QA was not run because it would otherwise package stale committed bundle files.

Most likely causes:
- News Sync rows were created but marked production_ready=No.
- Event dates were still missing or outside the freshness window.
- Studio Bridge filtered all rows before bundle creation.

Check `news_fact_packets.csv`, `studio_fresh_packet_report.md`, and `studio_fresh_packet_gate.csv`.
