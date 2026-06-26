# HSD WNBA Logo Review Catalog

Generated: `2026-06-26T00:00:00+00:00`

Review-only catalog. This does not approve logos, download assets, move files into a publish-ready lane, or change renderer behavior.

## Inventory

- Active WNBA teams in registry: `15`
- Team PNG logo files present: `15`
- Team SVG logo files present: `10`
- Required team logo files missing: `0`
- Local team logos still held for human approval: `3`
- League-level WNBA marks present: `0`

## Key Gaps

- `Atlanta Dream`, `New York Liberty`, and `Washington Mystics` have local PNGs but `team_logos.csv` has `approved=false`.
- `Portland Fire` has local PNG/SVG files, but the current `logo_sources.csv` URL is blocked by `config/hsd_verified_logo_registry_v1.json` because it can match the legacy Fire identity.
- All current `logo_sources.csv` rows use Wikimedia URLs. They remain useful historical evidence, but they are not official-first source authority under this workstream.
- No local WNBA league logo or lockup asset exists at `assets/leagues/wnba/logo.*` or `assets/leagues/wnba/lockup.*`.

## Renderer Readiness

- `11` team rows are locally present and registry-approved, but need official source recheck before operator trust.
- `3` team rows are local-file review holds.
- `1` team row is blocked by stale-source policy.
- `2` league mark rows are optional/missing review slots.

## Official Source Candidates

Use official WNBA or team pages as the evidence starting point before any approval or source row replacement:

- Atlanta Dream: `https://dream.wnba.com/`
- Chicago Sky: `https://sky.wnba.com/`
- Connecticut Sun: `https://sun.wnba.com/`
- Dallas Wings: `https://wings.wnba.com/`
- Golden State Valkyries: `https://valkyries.wnba.com/team`
- Indiana Fever: `https://fever.wnba.com/`
- Las Vegas Aces: `https://aces.wnba.com/`
- Los Angeles Sparks: `https://sparks.wnba.com/`
- Minnesota Lynx: `https://lynx.wnba.com/`
- New York Liberty: `https://liberty.wnba.com/`
- Phoenix Mercury: `https://mercury.wnba.com/`
- Portland Fire: `https://fire.wnba.com/`
- Seattle Storm: `https://storm.wnba.com/`
- Toronto Tempo: `https://tempo.wnba.com/`
- Washington Mystics: `https://mystics.wnba.com/`
- WNBA league mark discovery: `https://www.wnba.com/`

## Next Integration Steps

1. Operator reviews local logos against official team pages and records official evidence URLs.
2. Replace or supplement `logo_sources.csv` with official/free source URLs only after review.
3. Keep `Atlanta Dream`, `New York Liberty`, `Washington Mystics`, and `Portland Fire` out of renderer-trusted status until the approval/source gaps are resolved.
4. Decide whether WNBA league marks are required by templates; if yes, create explicit league mark slots and source evidence before adding assets.
5. Run `scripts/validate_hsd_wnba_asset_registry_v1.py` and `scripts/report_hsd_logo_asset_catalog_v1.py` after source metadata cleanup.
