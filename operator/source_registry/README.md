# HSD Manual Source Registry Intake

Use `source_registry_intake_template.csv` as the field guide for proposing new free official, team, wire, or cross-check sources.

Daily review runs also generate `source_registry_intake_template.csv` from the current coverage gaps. Those generated rows are proposal-only, disabled by default, and never update `config/source_registry.json` automatically.

Copy the shape from `source_registry_proposals_template.csv` into `operator/inbox/source_registry_proposals.csv` when you want the review run to check real proposed sources. The proposal review report flags duplicate, paid, login-only, social-only, and unsafe rows before any trusted registry update.

Keep live drafts in `operator/inbox/` or the latest run folder. The trusted registry should only change after a deliberate human review.
