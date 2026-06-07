# Her Sports Daily News Sync v1.1 Notes

The first News Sync run produced 0 candidates. That means the workflow itself ran, but it did not locate or parse the Results Desk priority queue.

v1.1 fixes that by adding:

- input discovery across repo root and `results_run_history/latest/`
- `news_input_status_report.csv`
- fallback parser for `daily_results_recommendations.md`
- `news_setup_error.md` if no candidates are found
- dashboard input-status section

The systems are still connected but separate:

`Results Desk v4.3 -> News Sync v1.1 -> Social / Brief / Graphics Handoff`
