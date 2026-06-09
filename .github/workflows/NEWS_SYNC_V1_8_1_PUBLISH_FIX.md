# HSD News Sync v1.8.1 Publish Fix

## Problem

News Sync v1.8 is committing generated files first, then running:

```bash
git pull --rebase --autostash origin main
```

That fails when another workflow has already pushed changes to the same generated files.

The failed log shows conflicts in files like:

```text
latest_news_sync_run_summary.md
news_brief_queue.md
news_daily_plan.md
news_dashboard/index.html
news_graphics_handoff.md
news_social_packets.md
news_sync_hub.md
news_sync_manifest.json
news_run_history/latest/*
news_run_history/_index.md
```

There were also `add/add` conflicts in:

```text
news_run_history/2026-06-09/1306_UTC/*
```

That means at least two runs wrote the same minute-based history folder.

## Important

This did not corrupt the repo. The runner failed before pushing. The conflict exists only inside that failed GitHub Actions runner.

## Required fixes

### 1. Replace the News Sync publish block

Replace the current `git commit` and `git pull --rebase --autostash` block with the contents of:

```text
news_sync_safe_publish_v1_8_1.sh
```

The important change is that generated-output conflicts are auto-resolved by keeping this run's generated files.

### 2. Add concurrency to the News Sync workflow

Add this at the workflow top level, outside `jobs:`:

```yaml
concurrency:
  group: hsd-repo-writer-${{ github.ref }}
  cancel-in-progress: false
```

Every workflow that pushes to `main` should use the same group.

### 3. Make run history folders unique beyond minute precision

The conflict path included:

```text
news_run_history/2026-06-09/1306_UTC/
```

That folder only has hour and minute. If two runs start in the same minute, they collide.

Change the run folder timestamp from:

```python
now.strftime("%H%M_UTC")
```

to either:

```python
now.strftime("%H%M%S_UTC")
```

or better:

```python
f"{now.strftime('%H%M%S_UTC')}_{os.environ.get('GITHUB_RUN_ID', 'local')}"
```

Expected example:

```text
news_run_history/2026-06-09/130642_UTC_15928473821/
```

## Best long-term fix

The best pattern is:

1. Fetch and reset to `origin/main`
2. Generate outputs
3. Commit outputs
4. Push
5. If push fails, reset, regenerate, commit, and push again

That is cleaner than generating first and then rebasing. But the v1.8.1 patch is designed to work with the current News Sync structure without rebuilding the whole workflow.
