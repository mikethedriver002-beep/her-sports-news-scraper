# HSD Womens Soccer Asset Registry

Review-only scaffold for womens soccer asset tracking.

## Guardrails

- No downloads are performed from this registry.
- No source is auto-approved.
- No asset slot is render-enabled.
- No file is moved into a publish-ready lane.
- Paid sources must stay `false`.
- Player rows should be added manually from official roster pages or operator-reviewed public sources.

## Layout

- `nwsl/leagues.csv` tracks league-level source context.
- `nwsl/teams.csv` tracks active NWSL team identity rows seeded from the official NWSL teams page.
- `nwsl/players.csv` is a header-only manual intake table for future player rows.
- `nwsl/source_urls.csv` tracks official league, team, roster, and team-site source URLs.
- `nwsl/provider_ids.csv` tracks provider IDs without implying approval or downloads.
- `nwsl/asset_slots.csv` tracks proposed asset slots and target paths only.
- `nwsl/approval_status.csv` keeps approval state separate from source discovery.

Run `python scripts/validate_hsd_womens_soccer_asset_registry_v1.py --root .` to refresh the review report.
