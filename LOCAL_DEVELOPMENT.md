# Her Sports Daily Local Development

This repo now has a local control command:

```powershell
.\hsd.ps1 doctor
.\hsd.ps1 setup -UseNetwork
.\hsd.ps1 test
.\hsd.ps1 run -Mode results
.\hsd.ps1 run -Mode full
.\hsd.ps1 dashboard
```

If Windows blocks `.ps1` scripts, use the command wrapper instead:

```powershell
.\hsd.cmd doctor
.\hsd.cmd setup -UseNetwork
.\hsd.cmd run -Mode results
```

## Current Source Policy

Free is the operating constraint.

- Official/free public sources can support publish-ready facts.
- Free public scoreboards and major media pages can cross-check results.
- Public social and gray-area sources are discovery or manual-review inputs unless operator verified.
- Paid APIs are disabled for local runs.
- Do not scrape private, login-only, paywalled, or restricted sources.

The policy file is `config/hsd_free_source_policy_v1.json`.

## Current Test Status

The local runner can execute the existing test suite with `.\hsd.cmd test`. At the time this local layer was added, most tests passed, but some historical phase tests still asserted older renderer/policy version strings while the repo contained newer Phase 6J+ files. Treat those as repo-state alignment work, not local setup failure.

## First-Time Setup

Install Python 3.11 first. If Windows opens the Microsoft Store when you type `python`, Python is not installed for this terminal yet.

Recommended:

```powershell
winget install Python.Python.3.11
```

Then reopen the terminal and run:

```powershell
.\hsd.ps1 setup -UseNetwork
```

Use `-NoInstall` if dependencies are already installed or if you only want to create the virtual environment.

## Local Run Outputs

Existing pipeline scripts still write their normal CSV, JSON, Markdown, and HTML outputs in the repo root. The local runner also collects the most useful review files into:

```text
outputs/local/latest/
outputs/local/<timestamp>/
```

After each local `run`, the runner quarantines known generated state so Git does not show hundreds of daily asset, registry, and review-file changes. It still keeps the review bundle in `outputs/local/latest/`.

Use this only when you intentionally want to inspect or commit generated asset/registry changes:

```powershell
.\hsd.cmd run -Mode full -KeepGeneratedState
```

This is a bridge step. The next architecture move is to teach the pipeline to write directly into run-scoped folders instead of producing root-level artifacts first.

## Daily Operator Command Center

The review stage builds `operator_command_center.html`, `operator_command_center.md`, and `operator_command_center.json`.

The command center is a local/manual cockpit. It summarizes:

- the current publish decision and safety posture
- next operator actions
- the daily posting schedule
- content candidates and studio bundles
- source health, blockers, and artifact links

It does not publish, push to Git, call paid APIs, or run hidden handoff refresh scripts. It reads the current local artifacts and turns them into a daily operating view.

## Useful Modes

- `results`: free/public Results Desk v5 path.
- `news`: News Sync from result outputs and source registry.
- `studio`: Studio bridge and preview quality gates.
- `review`: operator status, publish guard, command center, lite review pack.
- `full`: results, news, studio, then review.
- `scraper`: legacy RSS/news scraper.
- `asset`: asset desk and visual QA support scripts.

## Guardrails

The local runner blanks `APISPORTS_KEY`, `SERPAPI_KEY`, and `BING_SEARCH_API_KEY` for child processes. That keeps free-first behavior honest even if keys exist elsewhere in the user environment.
