# Her Sports Daily News Sync v1.3

News Sync v1.3 is not a replacement for Results Desk. It is a narrative layer that sits on top of Results Desk.

Results Desk answers:

```text
What happened?
Which results matter?
Is the score safe?
```

News Sync answers:

```text
How do we explain it?
What sources support the context?
What caption, short brief, and graphics handoff should we use?
```

## Should results and news be combined?

No. Keep them connected but separate.

The correct architecture is:

```text
Results Desk v4.3 -> News Sync v1.3 -> Graphics / Social / Website briefs
```

That means Results Desk stays the scorer of record, and News Sync consumes its outputs.

## Required existing input files

News Sync expects these files from the Results Desk run:

```text
results_graphics_queue.md
daily_results_recommendations.md
results_system_hub.md
wnba_box_score_summary.md
```

If `wnba_box_score_summary.md` is missing, the script still runs, but WNBA briefs will be less rich.

## Upload these files to repo root

```text
generate_hsd_news_sync_v1.py
generate_news_dashboard_v1.py
archive_news_runs_v1.py
news_source_registry.json
news_angle_rules.json
news_templates.json
requirements-news-sync.txt
```

## Workflow file

Create:

```text
.github/workflows/news-sync-v1.yml
```

using the included `news-sync-v1.yml`.

## Main outputs

```text
news_candidate_queue.csv
news_source_observations.csv
news_fact_packets.csv
news_brief_queue.md
news_social_packets.md
news_graphics_handoff.md
news_manual_review_queue.csv
news_sync_hub.md
news_dashboard/index.html
news_run_history/
```

## How to use the output

Open these first:

```text
news_sync_hub.md
news_brief_queue.md
news_social_packets.md
news_graphics_handoff.md
news_manual_review_queue.csv
```

## Manual review rules

The workflow holds a packet when:

```text
Results Desk marked it for manual review.
A Must Post item has neither top-performer data nor a primary source.
No usable source context was captured.
A source fetch failed and nothing else supports the packet.
```

## Accuracy rules

The news layer never overrides the result. It only adds context.

Do not invent:

```text
player stats
rankings
milestones
injuries
quotes
lineups
transaction details
```

Rights-safe rule:

```text
Store facts, links, titles, and short summaries only. Do not copy full article bodies.
```


## v1.1 first-run fix

v1.1 fixes the first-run problem where News Sync completed but read 0 candidates.

New behavior:

```text
1. Search repo root for Results Desk files.
2. Fall back to results_run_history/latest/.
3. If results_graphics_queue.md parses 0 items, try daily_results_recommendations.md.
4. Write news_input_status_report.csv so you can see exactly what it found.
5. Write news_setup_error.md if no candidates are found.
```

Open this first after the next run:

```text
news_input_status_report.csv
```


## v1.2 polish

v1.2 fixes the first real content-quality issue from the v1.1 run:

```text
Final score was blank in briefs and social packets.
```

Fixes included:

- Robust `results_graphics_queue.md` parser.
- Fallback final-score extraction from `daily_results_recommendations.md`.
- Winner/loser inference from headlines.
- Cleaner WNBA top-performer text.
- Manual review flag if a packet still has no final score.


## v1.3 improvements

v1.3 is the version I would deploy instead of v1.2.

Added:

```text
Results Desk CSV enrichment
CSV-only fallback if markdown queues change
context_quality
quality_score
production_ready
content_format_recommendation
news_daily_plan.md
```

Why this matters:

```text
The news layer no longer depends only on markdown parsing to find final scores.
It can recover score and context from top_womens_results.csv, reconciled_events.csv, or today_final_results.csv.
```
