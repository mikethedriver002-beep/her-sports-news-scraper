# Hockey/Softball Action-Photo First Paste Guide

Generated: `2026-06-28T00:00:00+00:00`

Review-only first-paste guide for the highest-priority hockey/softball action-photo handoff rows. It does not fetch sources, inspect URLs, download images, approve candidates/assets, write headshots/logos/cutouts, create `.approved` markers, move files, create a publish-ready lane, or publish.

## Summary

- First-paste rows: `4`
- Women's hockey rows: `2`
- Softball rows: `2`
- Generated ready rows: `0`
- Generated download approvals: `0`
- Shared action-photo return intake: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`

## First Rows To Work

| Paste Rank | Handoff Row | Sport | Tier | Source/Search Lead | Evidence Fields | Run After Paste |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `AH01` | womens_hockey | P0_OFFICIAL_FREE_PUBLIC | "[athlete]" PWHL "[team]" gallery OR recap site:thepwhl.com | `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required` | `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py` |
| 2 | `AH05` | softball | P0_OFFICIAL_FREE_PUBLIC | "[athlete]" AUSL softball action gallery OR recap site:theausl.com OR site:auprosports.com | `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required` | `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py` |
| 3 | `AH02` | womens_hockey | P1_RIGHTS_SENSITIVE_PUBLIC_REVIEW | "[athlete]" PWHL game action Getty OR AP OR Reuters OR Imagn OR Ice Garden OR Inside the Rink | `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required` | `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py` |
| 4 | `AH06` | softball | P1_RIGHTS_SENSITIVE_PUBLIC_REVIEW | "[athlete]" AUSL softball action Getty OR AP OR Reuters OR Imagn OR local sports gallery | `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required` | `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py` |

## Guardrails

- Work the H/S source return row and source-map ref manually before pasting anything into the shared action-photo intake.
- Keep generated readiness/download fields at `no`; this guide is not download approval, asset approval, render approval, or publish readiness.
- Leave source, entity, rights, identity, intended-use, decision, and notes fields blank until a human completes the gate.
