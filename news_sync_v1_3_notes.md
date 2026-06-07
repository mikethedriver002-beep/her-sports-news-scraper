# Her Sports Daily News Sync v1.3 Notes

v1.2 fixed final-score extraction from markdown, but before deploying it we added the more important safeguard:

Results Desk CSV enrichment.

v1.3 reads these files when available:

- top_womens_results.csv
- reconciled_events.csv
- today_final_results.csv

It uses those files to fill final score, winner, loser, league, sport, source URL, confidence, and editorial bucket.

New output:

- news_daily_plan.md

New packet fields:

- context_quality
- quality_score
- production_ready
- content_format_recommendation
- result_record_source

This makes News Sync less fragile and much closer to the Results Desk maturity level.
