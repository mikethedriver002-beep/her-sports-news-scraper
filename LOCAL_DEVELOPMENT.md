# Her Sports Daily Local Development

This repo now has a local control command:

```powershell
.\hsd.ps1 doctor
.\hsd.ps1 setup -UseNetwork
.\hsd.ps1 test
.\hsd.ps1 run -Mode results
.\hsd.ps1 run -Mode full
.\hsd.ps1 run -Mode dashboards
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

Every local `run` creates one timestamped run folder before the pipeline starts:

```text
outputs/local/latest/
outputs/local/<timestamp>/
```

Each run folder has two useful surfaces:

```text
outputs/local/<timestamp>/files/
outputs/local/<timestamp>/generated_state/
```

- `files/` is the operator-friendly review bundle with the command center, guard reports, schedules, source reports, and handoff files.
- The biggest daily generators now write directly to `files/` when `HSD_RUN_OUTPUT_DIR` is set, and read same-run artifacts before falling back to legacy root files.
- `generated_state/` preserves generated root-level files and directories that changed during the run, using their repo-relative paths.
- `generated_state_manifest.json` records what was archived and whether root cleanup was applied.

After the archive is captured, the runner restores tracked generated files and removes new generated files from the repo root. That keeps Git clean while preserving the run output under `outputs/local/<timestamp>/` and `outputs/local/latest/`.

Use this only when you intentionally want to inspect or commit generated asset/registry changes:

```powershell
.\hsd.cmd run -Mode full -KeepGeneratedState
```

The runner also exposes run-scoped environment variables for newer generators:

```text
HSD_LOCAL_RUN_ID
HSD_LOCAL_RUN_ROOT
HSD_RUN_OUTPUT_DIR
HSD_GENERATED_STATE_DIR
HSD_OUTPUT_MODE=run_scoped_local
```

Legacy scripts can still write root-level files, but local operation now treats the run folder as the durable output location and collects run-scoped artifacts before looking in the repo root.

## Daily Operator Command Center

The review stage builds `operator_command_center.html`, `operator_command_center.md`, and `operator_command_center.json`.

The same command center pass also writes review-only render prep packets: `render_prep_packets.md`, `render_prep_packets.csv`, and `render_prep_packets.json`. These packets are created only from render-ready or render-prep story candidates that clear source, asset, format, and manual-path gates. They provide template fit, copy fields, asset requirements, and exact manual renderer steps, but they do not render files, auto-run graphics, call paid APIs, or publish. The top packet also gets a review-only handoff folder at `render_handoff_top_packet/` with `README.md`, `copy_sheet.md/.csv`, `asset_checklist.md/.csv`, `source_proof.md`, `manual_renderer_prompt.md`, and `handoff_manifest.json`.

To create a local draft preview from that handoff, run `.\hsd.cmd run -Mode render` manually after a review run. This mode reads `render_handoff_top_packet/` from the current run/root/latest local output, copies the handoff into a new run folder, and writes `render_handoff_top_packet/draft_preview.png` plus `manual_review_renderer_report.md`, `manual_review_renderer_manifest.json`, `manual_visual_qa_report.md`, `manual_visual_qa_manifest.json`, `manual_visual_qa_checklist.csv`, `manual_visual_qa_approval_intake.md/.csv/.json`, `manual_visual_qa_operator_decision_draft.md/.csv/.json`, `manual_visual_qa_operator_decision_template.md/.csv/.json`, `manual_visual_qa_operator_decision_intake.md/.csv/.json`, `manual_post_approval_render_staging.md/.csv/.json`, and `manual_visual_qa_operator_decision_walkthrough.md/.csv/.json`. The preview, visual QA report, approval intake, copy-safe operator decision draft, copy-only decision template, operator decision intake validation, staging guidance, and walkthrough are drafts for human review only; they are not approved, not publish-ready, and not generated by an automatic workflow. Human decisions can be copied into `operator/inbox/manual_visual_qa_operator_decisions.csv`; render mode validates that inbox against the generated draft before staging reads it, and placeholder template values are rejected.

The command center is a local/manual cockpit. It summarizes:

- the current publish decision and safety posture
- next operator actions
- the morning source discovery board
- the daily posting schedule
- content candidates and studio bundles
- render-readiness scores and review-only render prep packets
- source health, blockers, and artifact links

It does not publish, push to Git, call paid APIs, or run hidden handoff refresh scripts. It reads the current local artifacts and turns them into a daily operating view.

The review stage refreshes manual intake and discovery intake before the morning source board runs. Manual intake writes `story_candidates_manual.csv/.jsonl` and `manual_story_inbox_report.md`. Discovery intake writes `story_candidates_discovery.csv/.jsonl` and `discovery_sources_report.md`, using free public RSS/page links, wire/official pages, Reddit public JSON where registered, and manual social inbox rows. For top official and wire page leads, discovery can sample the public article page for metadata titles, publish dates, and short descriptions from signals such as OpenGraph, JSON-LD `datePublished`, or `<time datetime>`. Discovery rows include lead quality, freshness, freshness source, evidence previews, urgency, and evergreen/stale signals so the command center can prioritize the strongest current opportunities first.

Article metadata sampling is capped by `HSD_DISCOVERY_MAX_ARTICLE_DATE_FETCHES_PER_SOURCE` and can be disabled with `HSD_DISCOVERY_ENABLE_ARTICLE_DATE_FETCH=false`. It captures only public page metadata for operator review; no login, no paid APIs, no automatic promotion, and no publishing.

The morning source discovery board writes `morning_source_discovery_board.csv`, `.md`, and `.json` during review runs. It also writes `morning_lead_promotion_recommendations.csv`, `.md`, and `.json`. It combines official/free source scans, wire sources, reputable gray-area/social discovery inputs, News Sync source observations, and manual inbox leads into one review-safe queue. Related official/wire discovery leads are grouped into story opportunities so duplicate or matching coverage becomes one operator-ready recommendation while the original source rows remain visible. Story opportunities include a cleaner operator headline, angle, advisory News-vs-Studio path, source coverage, confidence, confirmation, asset-readiness cues, and suggested free second-source checks. The source registry audit also writes `source_coverage_map.csv` so gaps like missing PWHL official/team sources are visible in the command center, plus `source_registry_intake_template.csv/.md` so the operator can propose free source additions without auto-enabling or importing them. Guided league packs generate `trusted_registry_operator_playbook.md`, `source_registry_post_edit_validation.csv/.md`, `source_registry_patch_preview.csv/.md`, `source_registry_approval_packet.csv/.md`, `source_registry_verification_log.csv/.md`, `source_registry_same_domain_resolution.csv/.md`, `source_registry_diff_review.csv/.md`, `source_registry_update_worksheet.csv/.md`, `source_registry_proposal_promotion_checklist.csv/.md`, `source_registry_proposal_draft.csv/.md`, `source_proposal_pack_readiness.csv/.md`, `source_proposal_packs.csv/.md`, plus focused files such as `wnba_source_proposal_pack.csv/.md`, `nwsl_source_proposal_pack.csv/.md`, `lpga_source_proposal_pack.csv/.md`, and `pwhl_source_proposal_pack.csv/.md`, with curated free official, team, tournament, and public cross-check candidates for manual review only. The trusted-registry operator playbook is the front door for human registry work: it gives step-by-step stop/go decisions, exact files to open, and rollback steps. The checklist tells the operator which selected draft rows to verify/copy, hold, or discard before any trusted registry edit. The worksheet turns verify/copy rows into review-only registry change plans with proposed disabled JSON, before/after notes, and rollback notes. The diff review compares proposed disabled source objects against `config/source_registry.json` for duplicate IDs, duplicate URLs/domains, risky trust bands, unsafe enablement, and missing rollback coverage before any human edit. Same-domain HOLD rows are resolved through `operator/inbox/source_registry_same_domain_resolution.csv`, where the operator can mark `same_domain_ok`, `revise`, or `discard`; `same_domain_ok` requires an evidence URL plus an existing source ID or URL comparison before approval can proceed. The verification log gives the operator fill-in fields for URL checked, freshness result, duplicate decision, approval/hold outcome, and evidence notes. The approval packet summarizes only verification-log rows marked `approved_for_manual_registry_edit`, with exact JSON, evidence fields, and hold reasons for final human review. The patch preview turns ready approval-packet rows into side-by-side registry before/after guidance and copy/paste JSON instructions for a human. The post-edit validation report compares any human-added registry row back against the patch preview, flags drift, unsafe enablement, automation, publish-policy, paid/API, or login-only signals, and keeps the check read-only. The draft stages selected pack rows with duplicate/freshness warnings preserved, while the readiness report tells the operator which packs are ready for manual registry proposal review, need duplicate review, or need source freshness checks. Manual source proposals belong in `operator/inbox/source_registry_proposals.csv`; review runs write `source_registry_proposal_review.csv/.md` to flag duplicate, paid/API, login-only, social-only, or unsafe rows before any trusted registry update. Social and gray-area rows remain discovery-only until confirmed by official, wire, primary, or operator-verified evidence.

Promotion recommendations are advisory only. They can suggest that a lead should become a News packet, manual story candidate, or Studio brief, but the local runner does not write those target artifacts automatically.

The old generic `generate_hsd_dashboard.py` path has been replaced by the command center. If it is run directly, it only creates a compatibility page that points back to `operator_command_center.html`.

Results and Studio drill-down dashboards are still available when you deliberately want a close-up view:

```powershell
.\hsd.cmd run -Mode dashboards
```

That mode creates `results_dashboard/index.html` and `studio_dashboard/index.html` inside the run folder, then refreshes the command center. It does not publish, call paid APIs, or run as part of `full`.

## Useful Modes

- `results`: free/public Results Desk v5 path.
- `news`: News Sync from result outputs and source registry.
- `studio`: Studio bridge and preview quality gates.
- `review`: source registry audit, operator status, publish guard, morning source discovery board, command center, lite review pack.
- `full`: results, news, studio, then review.
- `asset`: asset desk and visual QA support scripts.
- `stories`: final-score IG Story packs, then review command center.
- `handoff`: manual inbox to handoff packs, then review command center.
- `posts`: multi-post daily board and platform queues, then review command center.
- `launch`: Launch Control runbook, publish queue, quality gates, dashboards, and review command center.
- `dashboards`: optional Results and Studio drill-down dashboards, then review command center.

The old `womens_sports_scraper.py` file remains as a standalone legacy reference, but it is no longer an active local runner mode. If that path is revived later, it should be rebuilt to write through `HSD_RUN_OUTPUT_DIR` before returning to the daily workflow.

## Guardrails

The local runner blanks `APISPORTS_KEY`, `SERPAPI_KEY`, and `BING_SEARCH_API_KEY` for child processes. That keeps free-first behavior honest even if keys exist elsewhere in the user environment.
