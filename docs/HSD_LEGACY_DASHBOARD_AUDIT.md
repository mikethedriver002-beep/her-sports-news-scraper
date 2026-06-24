# HSD Legacy Dashboard Audit

## Decision

The daily operator home base is `operator_command_center.html`.

Legacy dashboards should not become competing operator surfaces. Keep lane-specific dashboards only when they add a focused drill-down view, and keep the daily command center as the default local dashboard.

Guardrails stay unchanged:

- Local/manual operation remains the default.
- Free-source behavior remains the default.
- Paid APIs are not part of dashboard cleanup.
- No auto-publishing or workflow automation should be added.

## Dashboard Decisions

Replaced by the daily command center:

- `generate_hsd_dashboard.py`

This was the old generic dashboard for pre-command-center graphics files such as `master_posting_dashboard.csv`, `daily_command_file.csv`, and `caption_bank_v2.csv`. It now acts only as a compatibility pointer to `operator_command_center.html`, writing into `HSD_RUN_OUTPUT_DIR` when set and preserving legacy direct-script output when unset.

Keep as focused run-scoped support views:

- `generate_news_dashboard_v1.py`
- `generate_hsd_launch_control_v1.py` launch dashboards
- `generate_hsd_graphics_qa_v1.py` graphics QA dashboard
- `generate_results_dashboard_v4.py`
- `generate_hsd_studio_dashboard_v1.py`

Results and Studio dashboard decision:

These are manual workflow-era drill-down dashboards, but their inputs are still produced by the current Results and Studio stages. They now read same-run artifacts first, write into `HSD_RUN_OUTPUT_DIR` when set, and are exposed only through the explicit local `dashboards` mode. They are not part of `full`; the local operator workflow should still treat `operator_command_center.html` as the home base.
