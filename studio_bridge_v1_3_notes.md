# Studio Bridge v1.3

Adds fresh packet selection.

## Key changes

- Reads event date fields from News Sync.
- Blocks undated or stale packets before bundle creation.
- Adds `studio_fresh_packet_report.md`.
- Adds `studio_fresh_packet_gate.csv`.
- Adds event date and freshness fields to `studio_bundle_queue.csv`.
- Writes event date into bundle prompts and accuracy locks.
