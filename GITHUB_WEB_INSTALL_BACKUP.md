# GitHub web install backup for the workflow file

If copying the hidden `.github` folder is the problem, do this in GitHub:

1. Open the repo.
2. Go to `.github/workflows/hsd-pipeline-control-v1.yml`.
3. Click edit.
4. Replace the whole file with the contents of:

```text
VISIBLE_COPY_OF_GITHUB_WORKFLOW/hsd-production-controller-v3-2-4-bebe-v2-3.yml
```

5. Commit directly to `main`.

This fixes the visible workflow name, strict freshness label, and artifact name.
