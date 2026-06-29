# HSD Deterministic Guardrails

Status: review-only workflow safety layer.

`scripts/guardrail_check.py` is the first Workflow v2 brake. It is a local,
deterministic check that can run before PR review or after latest artifact
generation. It does not call external models, fetch sources, download assets,
approve assets, move files, publish, or change repo state.

## Commands

```powershell
python scripts\guardrail_check.py --base origin/main --format markdown
python scripts\guardrail_check.py --scan-dir outputs/local/latest/files --format json
```

## What It Checks

- Added branch file paths that point toward publish-ready or publishing lanes.
- Added `.approved` marker paths.
- Added truthy guardrail assignments such as `auto_approval=true`,
  `auto_publish=true`, `move_files=true`, `paid_apis=true`, and related fields.
- Generated CSV/JSON/JSONL artifacts with truthy guardrail fields.
- Protected asset write paths outside the review-only quarantine candidate
  exception.

The checker is intentionally conservative but repo-aware. It should avoid
failing on safe explanatory text such as "do not create a publish-ready lane" or
"download_approved=yes remains human-edited only."

## Configuration

Rules live in `config/hsd_guardrails.json` so future conductor tooling and lane
checks can share the same deterministic boundaries.
