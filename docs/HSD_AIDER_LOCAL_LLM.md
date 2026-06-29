# HSD Aider Local LLM Workflow

This is the repo-visible operating note for using Aider with a free local model on HSD work.

## Installed Local Stack

- Aider: `aider-chat`
- Local model host: Ollama
- Default local model: `qwen2.5-coder:7b`
- Repo launcher: `scripts\hsd_aider_local.ps1`

The local model is for low-risk assistance. It does not replace conductor review, focused validation, or human approval gates.

## Start Aider

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\hsd_aider_local.ps1
```

To pass specific files or Aider flags:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\hsd_aider_local.ps1 -AiderArgs docs\HSD_OPERATING_WORKFLOW_V1.md scripts\guardrail_check.py
```

To use a different local Ollama model for a session:

```powershell
$env:HSD_AIDER_MODEL = "ollama/qwen2.5-coder:14b"
powershell -ExecutionPolicy Bypass -File scripts\hsd_aider_local.ps1
```

## HSD Guardrails

Aider sessions must stay inside the same HSD guardrails as Codex lanes:

- No paid APIs.
- No automatic downloads of athlete, team, logo, or action-photo assets.
- No source auto-enablement.
- No render auto-approval.
- No `.approved` markers.
- No moving files into a publish-ready lane.
- No publishing.
- No `--yes-always`.
- No automatic commits.

The launcher adds `--no-auto-commits` and `--no-watch-files` by default. Keep that posture unless Mike explicitly asks for a different Aider mode.

## Recommended Use

Good local Aider use cases:

- Drafting small helper scripts or tests.
- Explaining a local file before a PR packet.
- Mechanical refactors where Codex/conductor still validates the diff.
- Reviewing docs for clarity.
- Generating first-pass test ideas for guardrails.

Avoid local Aider for:

- Renderer taste calls that need editorial judgment.
- Source credibility decisions.
- Approval-state changes.
- Anything involving image downloads, asset intake writes, or publish flow.
- Large cross-lane architecture moves without a conductor packet.

## Model Routing

Use this ladder:

- `qwen2.5-coder:7b` through Aider for free local code help, docs, and low-risk refactors.
- `gpt-5.5 medium` for normal implementation lanes when the change is narrow and well-scoped.
- `gpt-5.5 high` for renderer polish, source architecture, public-signal logic, asset workflow design, and conductor decisions.
- ChatGPT Pro or Gemini Pro deep research for external research, design critique, source-map exploration, and competitive/editorial analysis.
- Spark audits are useful but non-blocking. If unavailable, continue with equivalent local/read-only validation.

## Required Validation

Before trusting any Aider-assisted repo change, run the relevant focused tests plus the deterministic guardrail check:

```powershell
python scripts\guardrail_check.py --base origin/main --format markdown
python scripts\guardrail_check.py --scan-dir outputs/local/latest/files --format json
```

For generated artifacts, inspect counts and review-only fields rather than relying on a pass/fail summary alone.
