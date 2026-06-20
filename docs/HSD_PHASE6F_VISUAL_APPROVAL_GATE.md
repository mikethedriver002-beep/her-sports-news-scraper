# HSD Phase 6F: Human Visual Approval Gate and Production Cutover Prep

Phase 6F turns the Phase 6E near-post-ready output into a human-reviewable approval packet. It does not publish, does not change production routing, and does not replace `HSD_QUALITY_GRAPHICS`.

## What Phase 6F does

1. Rebuilds the Renderer v4.2 clean-plate proof lane.
2. Revalidates template contract, clean plates, renderer integrity, fidelity, and near-post-ready gates.
3. Generates a visual approval packet from the near-post-ready rows.
4. Creates a human decisions template keyed by `approval_id` and `render_sha256`.
5. Validates any human approval decisions that have been committed.
6. Produces an approved operator handoff manifest only after explicit approval.

## Approval policy

Approvals are by render hash, not filename. A filename can stay the same while pixels change, so the hash is the lock.

Rows cannot be approved if they are:

- fixture-only player references
- not near-post-ready candidates
- carrying placeholder layers
- carrying zone overflow
- failing mask compliance

## How to approve renders

After the workflow runs, download the artifact and review:

- `visual_approval_packet_v4.md`
- `visual_approval_contact_sheet_v4.jpg`
- `visual_approval_candidates_v4.csv`

Copy:

```text
outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/approval/visual_approval_decisions_template_v4.csv
```

to:

```text
config/graphics/v4/approval/visual_approval_decisions_v4.csv
```

For each approved row, fill:

```text
decision=approved
reviewer=<your name or handle>
reviewed_at=<ISO timestamp>
reason=<short approval note>
render_sha256=<exact hash from candidate row>
```

Use `rejected`, `needs_fix`, or `hold` for anything that is not ready.

## Cutover policy

Even after approvals exist, production cutover stays blocked in Phase 6F. The next phase must open a separate cutover PR that routes only approved Renderer v4.2 hashes into the operator handoff lane.
