# HSD Phase 2G Retry Package, No Workflow Push

## Why this exists

The first Phase 2G installer run cleaned the repo successfully, but failed at `git push` because the local commit included a change to:

```text
.github/workflows/hsd-v3-repo-state-sanity.yml
```

GitHub Actions blocks workflow-file updates from the default `GITHUB_TOKEN` unless the token has `workflows` permission. That is why the error said:

```text
refusing to allow a GitHub App to create or update workflow `.github/workflows/hsd-v3-repo-state-sanity.yml` without `workflows` permission
```

The cleanup itself worked before that failure:

```text
Initial generated paths: 2114
Deleted paths: 2114
Remaining generated paths: 0
Status: ready_to_commit
```

## What changed in this retry

This v2 installer does **not** patch any workflow files during the Actions run.

It will still:

1. scan tracked generated output
2. delete confirmed generated-output files
3. patch `.gitignore`
4. run Phase 2 tests
5. commit and push cleanup to `main`
6. write `phase2_closure_v1.json/md`
7. upload the installer artifact

## Install

Upload these extracted files to the same repo paths:

```text
.github/workflows/hsd-v4-phase2g-installer.yml
scripts/report_hsd_phase2_closure_v1.py
tests/test_v4_phase2g_phase2_closure.py
README_PHASE2G_RETRY_NO_WORKFLOW_PUSH.md
PHASE2G_RETRY_MANIFEST.json
```

Commit directly to `main`.

## Run

Go to:

```text
Actions → HSD V4 Phase 2G Installer v2 → Run workflow
```

Use:

```text
confirm = CLOSE_PHASE_2
```

## Expected success

The workflow should push successfully because it should no longer touch `.github/workflows/*`.

Upload the artifact named like:

```text
hsd-v4-phase2g-installer-v2-<run number>
```

Check:

```text
phase2_closure_v1.json
```

Expected:

```json
{
  "phase2_closed": true,
  "status": "phase2_closed",
  "blockers": []
}
```

## Note

The permanent normal sanity workflow closure gate is intentionally deferred. We can add it manually later, but not from the installer Action.
