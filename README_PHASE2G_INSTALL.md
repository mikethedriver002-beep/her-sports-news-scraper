# HSD V4 Phase 2G — Manual Installer

This package is the final Phase 2 repository-hygiene closure pass.

## What it does

The installer runs only when you press the GitHub Actions button and select
`CLOSE_PHASE_2`.

It will:

1. Inventory every tracked file.
2. Detect generated dashboards, run histories, review packs, root reports,
   queues, static write targets, caches, and generated files carrying explicit
   run markers.
3. Protect source code, tests, workflows, config, contracts, docs, reviewed
   assets, and the hand-written `studio_bridge_v1_3_notes.md`.
4. Re-scan and delete generated outputs for up to four passes.
5. Patch `.gitignore` from the actual deleted paths.
6. Wire a strict Phase 2 closure gate into the normal sanity workflow.
7. Run Phase 2 regression tests.
8. Commit and push the cleanup to `main`.
9. Produce a verification artifact.

The source-truth blockers remain explicitly deferred to Phase 3:

- `expected_games_baseline_is_observation_derived`
- `independent_schedule_verification_inconclusive`

## Upload

Do not upload the ZIP itself to the repository.

Extract the ZIP, then upload these files to the matching paths in the repo:

- `.github/workflows/hsd-v4-phase2g-installer.yml`
- `scripts/report_hsd_phase2_closure_v1.py`
- `tests/test_v4_phase2g_phase2_closure.py`
- `README_PHASE2G_INSTALL.md`
- `PHASE2G_PACKAGE_MANIFEST.json`

Commit the upload directly to `main`.

## Run

Open:

`Actions → HSD V4 Phase 2G Installer → Run workflow`

Choose:

`confirm = CLOSE_PHASE_2`

The workflow is expected to commit the cleanup to `main`.

## Success condition

The run must be green and its artifact must contain:

- `phase2g_install_report.json`
- `phase2g_install_report.md`
- `phase2g_deleted_paths.txt`
- `phase2_closure_v1.json`
- `phase2_closure_v1.md`

The authoritative result is:

`phase2_closure_v1.json → phase2_closed: true`

Upload that artifact back to the HSD V4 review chat for final verification.
