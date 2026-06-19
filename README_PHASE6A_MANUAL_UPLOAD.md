# HSD Phase 6A Manual Source-Pack Upload

The canonical source ZIP is larger than the connector can safely transfer, so this single binary is uploaded through the GitHub website.

## Exact file

Filename:

`hsd_wnba_canonical_templates_v4.zip`

Repository destination:

`assets/graphics/v4/approved/hsd_wnba_canonical_templates_v4.zip`

Expected size:

`34,672,444 bytes`

Expected SHA-256:

`1bd7bddec9f1103694c5c001129f842f4059e8a0739378359dd78c89772278c7`

## GitHub website steps

1. Open the Phase 6A pull request.
2. Switch to branch `hsd-v4-phase6a-template-contract-final` if GitHub does not select it automatically.
3. Navigate to `assets/graphics/v4/approved/`.
4. Select **Add file → Upload files**.
5. Upload the ZIP itself. Do not extract it and do not rename it.
6. Commit the upload to the Phase 6A branch, not `main`.
7. Merge the PR only after the ZIP is present.
8. Run `HSD V4 Phase 6A Template Contract` from the Actions tab after merge.
9. Upload the resulting artifact for verification.

## Expected strict result

```json
{
  "status": "passed_template_contract",
  "template_count": 7,
  "source_pack_hash_valid": true,
  "badge_hash_valid": true,
  "font_contract_status": "declared_reference_match_required",
  "blockers": []
}
```
