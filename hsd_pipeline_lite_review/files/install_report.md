# HSD Install Verification

Verifier: hsd-install-verifier-v3.2.13-bebe-ops-v2.11
Expected pipeline version: `v3.2.13-bebe-ops-v2.11`
Installed pipeline version: `v3.3.6-mermaid-assignment-handoff-v2.6`
Generated: 2026-06-14T17:00:07.063820+00:00

- issues: 0
- warnings: 2
- version status: warning
- stale files removed before run: 24
- stale directories removed before run: 1

## Warnings

- pipeline_version mismatch: 'v3.3.6-mermaid-assignment-handoff-v2.6'; expected 'v3.2.13-bebe-ops-v2.11'. This no longer blocks the run; update config/pipeline_version.json for cleaner GitHub/operator display.
- .github/workflows/hsd-pipeline-control-v1.yml: visible workflow name/artifact name does not show v3.2.13-bebe-ops-v2.11; copy the hidden .github workflow to fix GitHub display.

Install verification passed for safe execution. Version/display mismatches are warnings, not blockers, in BeBe Ops v2.11.
