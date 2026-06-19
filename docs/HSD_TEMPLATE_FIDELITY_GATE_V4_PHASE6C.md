# HSD Phase 6C Template Fidelity Gate

Phase 6C adds the first visual fidelity gate for Template Renderer v4.

It compares rendered proof-lane outputs against the Phase 6A approved public mockups and layout references.
It does not promote anything to production and does not approve operator handoff.

## What it produces

- `template_fidelity_v4_report.json`
- `template_fidelity_v4_report.md`
- `outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/fidelity/template_fidelity_v4_rows.csv`
- `outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/fidelity/template_fidelity_v4_contact_sheet.jpg`
- `outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/fidelity/template_fidelity_v4_diff_sheet.jpg`
- per-template comparison and diff images under `fidelity/comparisons/`

## What it checks

- required Phase 6B templates are rendered
- approved baseline image exists
- approved layout reference image exists
- dimensions match
- tone score
- edge-layout similarity
- dark-background ratio distance
- palette distance
- overall structure score

## Policy

The fidelity gate may pass setup while still reporting review-required outputs.
That is intentional. Phase 6C is about creating measurement and review evidence.
Production cutover remains blocked until Phase 6D or later.

## Command

```bash
python scripts/validate_hsd_template_fidelity_v4.py --strict
```

Expected setup pass:

```json
{
  "status": "passed_fidelity_setup",
  "cutover_allowed": false,
  "blockers": []
}
```
