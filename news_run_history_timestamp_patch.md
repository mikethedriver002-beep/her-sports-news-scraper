# News Sync run-history timestamp patch

Find the code that creates the time folder for News Sync run history.

It probably looks like one of these:

```python
tm = now.strftime("%H%M_UTC")
```

or:

```python
run_time = now.strftime("%H%M_UTC")
```

Change it to:

```python
import os

tm = f"{now.strftime('%H%M%S_UTC')}_{os.environ.get('GITHUB_RUN_ID', 'local')}"
```

This prevents two runs from creating the same folder, such as:

```text
news_run_history/2026-06-09/1306_UTC/
```

The new folder will look like:

```text
news_run_history/2026-06-09/130642_UTC_15928473821/
```
