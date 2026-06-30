# Review-Only Action Photo Manual Return Evidence Checklist v1

Generated: `2026-06-29T00:00:00+00:00`

This checklist is keyed to APFAC manual first-action cards and tells the operator what to verify before pasting a candidate return. It does not fetch sources, inspect URLs, download images, approve candidates/assets, write headshots, create marker files, move files, or publish.

## Summary

- Checklist rows: `2`
- Generated ready rows: `0`
- Generated download approvals: `0`
- Validation issues: `0`

## Checklist

### APFEC01 - APFAC01

- Source row: `data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv#row=2`
- Manual source lead: `https://bayfc.com/press-releases/bay-fc-acquire-midfielder-kennedy-fuller-from-angel-city-fc-20260612/`
- Paste target: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Candidate/source/evidence checks: `human_paste_candidate_page_or_candidate_url_only_after_manual_review` / `human_paste_source_url_from reviewed page; leave blank until verified` / `human_paste_evidence_page_url_with caption/event/source context`
- Identity checks: `human_paste official roster/profile or equivalent identity anchor` / `human_paste matching entity_id from current registry/intake row` / `human_set strong_context or equivalent only when source/evidence supports identity`
- Rights check: `human_select conservative review category; this is not clearance`
- Action/crop checks: `human_confirm game/action context and reject static/headshot-only candidates` / `human_note whether crop/composition can support future review-only render testing`
- Missing until human paste: `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required`
- Keep blank until human gate: `download_approved|quarantine_target_hint|operator_decision|operator_notes`
- Run after paste: `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py`

### APFEC02 - APFAC02

- Source row: `data/asset_registry/hockey_softball_action_photo_research_handoff.csv#row=2`
- Manual source lead: `"[athlete]" PWHL "[team]" gallery OR recap site:thepwhl.com`
- Paste target: `data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv`
- Candidate/source/evidence checks: `human_paste_candidate_page_or_candidate_url_only_after_manual_review` / `human_paste_source_url_from reviewed page; leave blank until verified` / `human_paste_evidence_page_url_with caption/event/source context`
- Identity checks: `human_paste official roster/profile or equivalent identity anchor` / `human_paste matching entity_id from current registry/intake row` / `human_set strong_context or equivalent only when source/evidence supports identity`
- Rights check: `human_select conservative review category; this is not clearance`
- Action/crop checks: `human_confirm game/action context and reject static/headshot-only candidates` / `human_note whether crop/composition can support future review-only render testing`
- Missing until human paste: `candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required`
- Keep blank until human gate: `download_approved|quarantine_target_hint|operator_decision|operator_notes`
- Run after paste: `.\.venv\Scripts\python.exe scripts\report_hsd_action_photo_research_return_import_stub_v1.py`

