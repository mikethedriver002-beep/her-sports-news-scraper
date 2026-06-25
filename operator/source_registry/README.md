# HSD Manual Source Registry Intake

Use `source_registry_intake_template.csv` as the field guide for proposing new free official, team, wire, or cross-check sources.

Daily review runs also generate `source_registry_intake_template.csv` from the current coverage gaps. Those generated rows are proposal-only, disabled by default, and never update `config/source_registry.json` automatically.

Guided league proposal packs generate `source_proposal_pack_readiness.csv/.md`, `source_proposal_packs.csv/.md`, plus focused files such as `wnba_source_proposal_pack.csv/.md`, `nwsl_source_proposal_pack.csv/.md`, `lpga_source_proposal_pack.csv/.md`, and `pwhl_source_proposal_pack.csv/.md` with specific free official league, team, tournament, and public cross-check candidates. Treat them as copy-ready review guides only; they do not enable sources, update the trusted registry, scrape private pages, call paid APIs, or publish. Use the readiness report to see which packs are ready for manual proposal review, need duplicate review, or need source freshness checks.

Copy the shape from `source_registry_proposals_template.csv` into `operator/inbox/source_registry_proposals.csv` when you want the review run to check real proposed sources. The proposal review report flags duplicate, paid, login-only, social-only, and unsafe rows before any trusted registry update.

Keep live drafts in `operator/inbox/` or the latest run folder. The trusted registry should only change after a deliberate human review.
