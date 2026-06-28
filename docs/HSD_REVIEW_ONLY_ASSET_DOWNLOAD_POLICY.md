# HSD Review-Only Asset Download Policy

Status: proposed operating law for review-only local asset candidates.

This policy narrows the old "no downloads" guardrail into a safer workflow: no automatic downloads, but human-approved quarantine downloads are allowed when the operator explicitly records the required evidence first.

## Core Rules

- No automatic asset downloads.
- A local asset candidate download is allowed only when a human-edited intake row sets `download_approved=yes`.
- The intake row must include `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.
- Downloaded files must land only in `data/assets/quarantine/review_only_candidates/`.
- Downloaded files must not be written to approved asset folders, renderer-ready athlete folders, team logo folders, or any publish-ready lane.
- Download approval is not asset approval.
- Human asset approval remains a separate step after local visual/source/identity review.
- No `.approved` markers may be created by a download step.
- No publishing, auto-publishing, publish-ready movement, or file promotion is allowed from the download step.

## Required Intake Fields

The canonical intake template is `operator/inbox/review_only_asset_download_intake.csv`.

Required fields:

- `download_approved`
- `source_url`
- `entity_id`
- `rights_class`
- `identity_confidence`
- `intended_review_only_use`

The first implementation packet should validate these fields before any future downloader is allowed to fetch bytes.

## Quarantine Path

Sanctioned local landing zone:

`data/assets/quarantine/review_only_candidates/`

This folder is intentionally not an approved asset folder. Files here are review-only candidates until a separate human asset-approval workflow records a decision.

## First PR-Sized Implementation Packet

1. Add this policy document, the machine-readable config, the intake CSV template, and the quarantine README.
2. Add focused guardrail tests that assert the required intake fields, quarantine path, and no-auto-approval separation.
3. Do not add a downloader yet.
4. Follow-up packet: build a dry-run validator that reads the intake CSV and reports eligible rows without downloading anything.
5. Later packet: add a quarantine-only downloader that refuses rows missing required metadata and refuses all non-quarantine destinations.
