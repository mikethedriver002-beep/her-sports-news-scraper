# HSD Agent Defaults

- Default helper-agent model: `gpt-5.4-mini`.
- Use higher models only when the operator explicitly requests them or a task clearly needs deeper reasoning.
- Keep local/manual operation as the default.
- Do not add paid APIs.
- Do not auto-enable sources.
- Do not auto-approve renders.
- Do not perform automatic asset downloads.
- Review-only local asset candidate downloads are allowed only when a human-edited intake row sets `download_approved=yes` and includes `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.
- Downloaded asset candidates must land only in `data/assets/quarantine/review_only_candidates/`; never place them in approved asset folders.
- Download approval is not asset approval. Human asset approval remains a separate step and must not create `.approved` markers automatically.
- Do not move files into a publish-ready lane.
- Do not auto-publish.
- Generated reports should remain review-only unless a human operator edits the relevant manual intake files.
