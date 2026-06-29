# HSD Conductor Runtime

Status: proposed runtime mailbox for Workflow v2.

The `conductor/runtime/` tree is intentionally ignored by Git except for its
`.gitkeep` placeholder. Future conductor loops can write cache files, lock
files, lane directives, and lane status snapshots there without causing
cross-branch merge conflicts.

Repo-visible schemas and deterministic guardrail tooling should be committed.
Runtime state should not.

## Directive snapshots

Workflow v2 directives must be immutable snapshots, not a shared mutable
control file. Commit schema/docs and example snapshots only:

- `conductor/directive.schema.json`
- `conductor/directive.example.json`
- future snapshots under `conductor/directives/runs/<timestamp>-<slug>.json`
  or `conductor/directives/branches/<branch>/<timestamp>-<slug>.json`

Do not commit `conductor/directive.json`. A single live directive file would
create cross-branch collisions and make concurrent lanes overwrite each
other's instructions.

Validate the foundation with:

```powershell
python scripts\validate_hsd_conductor_directive_v1.py
```

This validator is review-only. It does not run a conductor loop, fetch sources,
download assets, approve renders, move files into a publish-ready lane, or
publish.
