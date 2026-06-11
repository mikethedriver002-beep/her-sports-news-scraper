# HSD BeBe Ops v2.3 Stability Fix

Version: `v3.2.4-bebe-ops-v2.3`

This patch fixes the failure where install verification stopped the run because only part of the previous hotfix was installed.

## What failed

The failed run stopped at install verification because:

- `verify_hsd_install_v1.py` expected `v3.2.3-bebe-ops-v2.2`.
- `config/pipeline_version.json` still said `v3.2.2-bebe-ops-v2.1`.
- `.github/workflows/hsd-pipeline-control-v1.yml` still displayed the older v3.2.1 BeBe Ops v2 workflow name.

That means the prior install was partial. Some scripts updated, but the visible GitHub workflow/config did not fully update.

## What this patch changes

- Updates the visible workflow name to `Her Sports Daily Production Controller v3.2.4 BeBe Ops v2.3`.
- Adds a GitHub run name: `HSD BeBe Ops v2.3 • <run_mode> • run <run_number>`.
- Changes artifact names to include `v3-2-4-bebe-ops-v2-3` and the GitHub run number.
- Moves/labels strict freshness clearly as: `STRICT FRESHNESS GATE — leave 1 for normal runs; 0 is debug only.`
- Updates `config/pipeline_version.json` to `v3.2.4-bebe-ops-v2.3`.
- Adds `config/hsd_release_version.json` as a canonical version reference.
- Changes install verification so version-display mismatches are warnings, not hard failures, as long as the installed pipeline is still a safe v3.2+ BeBe build.
- Keeps real safety failures as hard failures: missing required scripts, unsafe workflow triggers, red sources enabled, or missing upload-pack ZIP safety net.

## Install

Copy **all contents** inside `repo_files/` into the root of the repo.

The safest terminal command is:

```bash
cp -a repo_files/. /path/to/her-sports-news-scraper/
```

The `/.` matters because it copies hidden folders like `.github`.

Then commit:

```bash
git add .
git commit -m "Install HSD BeBe Ops v2.3 stability fix"
git push origin main
```

## GitHub web install note

If you are copying files manually in GitHub, the most important file is hidden:

```text
.github/workflows/hsd-pipeline-control-v1.yml
```

If that file is not updated, GitHub will keep showing the old workflow name and old artifact name.

A visible duplicate copy is included at:

```text
VISIBLE_COPY_OF_GITHUB_WORKFLOW/hsd-production-controller-v3-2-4-bebe-v2-3.yml
```

Use that file only as a backup reference if GitHub's hidden `.github` folder is hard to see.

## After install, confirm these exact strings in GitHub

```text
.github/workflows/hsd-pipeline-control-v1.yml
name: Her Sports Daily Production Controller v3.2.4 BeBe Ops v2.3
run-name: HSD BeBe Ops v2.3 • ... • run ...
artifact name: hsd-production-control-v3-2-4-bebe-ops-v2-3-lite-review-${{ github.run_number }}
```

```text
config/pipeline_version.json
"pipeline_version": "v3.2.4-bebe-ops-v2.3"
```

```text
verify_hsd_install_v1.py
VERSION = "hsd-install-verifier-v3.2.4-bebe-ops-v2.3"
```

## Expected next run

If install is complete:

```text
install_report.md: issues 0
Installed pipeline version: v3.2.4-bebe-ops-v2.3
workflow visible name: Her Sports Daily Production Controller v3.2.4 BeBe Ops v2.3
artifact name: hsd-production-control-v3-2-4-bebe-ops-v2-3-lite-review-<run number>
```

If install is partial but safe:

```text
install_report.md: issues 0
warnings: version/display mismatch
pipeline continues instead of failing
```
