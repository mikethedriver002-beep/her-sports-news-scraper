#!/usr/bin/env bash
set -euo pipefail

git config user.name "github-actions"
git config user.email "github-actions@github.com"

FILES=(
  "news_input_status_report.csv"
  "news_setup_error.md"
  "news_candidate_queue.csv"
  "news_source_observations.csv"
  "news_fact_packets.csv"
  "news_brief_queue.md"
  "news_social_packets.md"
  "news_graphics_handoff.md"
  "news_daily_plan.md"
  "news_manual_review_queue.csv"
  "news_sync_hub.md"
  "news_sync_manifest.json"
  "news_dashboard/index.html"
  "latest_news_sync_run_summary.md"
  "news_run_history"
)

stage_outputs() {
  for file in "${FILES[@]}"; do
    if [ -e "$file" ]; then
      git add "$file"
    else
      echo "Optional output not present, skipping: $file"
    fi
  done
}

# This preserves the current run's generated outputs if another workflow pushed first.
# In a rebase conflict, --theirs means the commit being replayed, which is this run's generated files.
resolve_generated_conflicts_current_run_wins() {
  echo "Resolving generated-output conflicts by keeping this run's generated files..."
  conflicted="$(git diff --name-only --diff-filter=U || true)"
  if [ -z "$conflicted" ]; then
    return 0
  fi

  echo "$conflicted" | while IFS= read -r file; do
    if [ -n "$file" ]; then
      echo "Keeping current-run version of: $file"
      git checkout --theirs -- "$file" 2>/dev/null || true
      git add "$file" 2>/dev/null || true
    fi
  done

  git rebase --continue || git rebase --skip
}

stage_outputs

if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git commit -m "Update HSD News Sync v1.8.1"

for attempt in 1 2 3; do
  echo "Push attempt $attempt"

  # Abort any stale rebase state from a previous failed attempt in this runner.
  git rebase --abort 2>/dev/null || true

  git fetch origin main

  if git rebase origin/main; then
    echo "Rebase succeeded"
  else
    resolve_generated_conflicts_current_run_wins
  fi

  if git push origin HEAD:main; then
    echo "Push succeeded"
    exit 0
  fi

  echo "Push failed, retrying after short wait..."
  sleep 5
done

echo "Push failed after 3 attempts"
exit 1
