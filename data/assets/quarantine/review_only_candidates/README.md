# Review-Only Asset Candidate Quarantine

This is the only sanctioned local landing zone for human-approved asset candidate downloads.

Files in this folder are not approved assets. They must stay review-only until a separate human-edited approval workflow records a source, rights, identity, and renderer-use decision.

Guardrails:

- No automatic downloads.
- A human-edited intake row must set `download_approved=yes`.
- Required intake metadata: `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.
- Do not write `.approved` markers here.
- Do not move files from here into approved asset folders or publish-ready lanes automatically.
- Do not publish from this folder.
