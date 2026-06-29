# HSD Conductor Runtime

Status: proposed runtime mailbox for Workflow v2.

The `conductor/runtime/` tree is intentionally ignored by Git except for its
`.gitkeep` placeholder. Future conductor loops can write cache files, lock
files, lane directives, and lane status snapshots there without causing
cross-branch merge conflicts.

Repo-visible schemas and deterministic guardrail tooling should be committed.
Runtime state should not.
