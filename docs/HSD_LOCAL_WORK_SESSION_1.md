# HSD Local Work Session 1

Date: 2026-06-24

## Goal

Move the project from chat/upload/download work into a local operating loop that Codex can improve directly.

## What Changed

- Added `hsd.ps1` as the root local command.
- Added `hsd.cmd` so Windows can run the local command even when direct `.ps1` execution is blocked.
- Added `scripts/hsd_local.ps1` as the local runner and doctor.
- Added `config/hsd_free_source_policy_v1.json` to make free-first sourcing explicit.
- Added `requirements-dev.txt` for local test dependencies.
- Added `LOCAL_DEVELOPMENT.md` with first-use commands and source guardrails.

## Current Local Blocker

Resolved. Python 3.11.9 was installed and the project virtual environment now lives at `.venv/`.

Setup command:

```powershell
.\hsd.cmd setup -UseNetwork
```

If Windows blocks `.ps1` scripts, use `.\hsd.cmd` with the same arguments.

## Verification Results

Focused free-source/source-truth checks passed:

```text
17 passed
```

Full test suite status after local setup:

```text
174 passed, 13 failed
```

The remaining failures are historical renderer/template phase assertions that expect older Phase 6B/6D/6E/6H/6I version strings or earlier font-contract states while this repo contains newer Phase 6J+ files. The local setup and free-source Results/News path are not blocked by those failures.

## First Local Pipeline Run

Command:

```powershell
.\hsd.cmd run -Mode full
```

Result: passed.

Key counts:

- Results observations: 9
- Reconciled women's events: 9
- Final women's events: 4
- Graphics-ready results: 4
- Expected games: 9
- Missing expected games: 0
- News candidates: 4
- Fact packets: 4
- Publish-ready packets: 4
- Production-ready packets: 4
- Studio graphics queued: 0
- Publish allowed: false
- Graphics handoff allowed: false

The local review bundle was collected under:

```text
outputs/local/latest/
```

## Free-First Product Constraint

Free is the default mode.

- Green: official, league/team, primary, wire, and free public scoreboards.
- Green cross-check: public scoreboard or major media pages when freely reachable.
- Yellow: public social and gray-area sources. Discovery or review only unless operator verified.
- Red: paid APIs, paywalled text, login-only scraping, private feeds, and restricted endpoints.

The local runner blanks paid-source keys for child processes:

- `APISPORTS_KEY`
- `SERPAPI_KEY`
- `BING_SEARCH_API_KEY`

## Next Architecture Step

The next work session should package the current script sprawl behind a Python module and route outputs directly into run-scoped folders. The first target should be the high-value path:

1. Results Desk v5
2. News Sync
3. Studio Bridge
4. Review/Operator Command Center
