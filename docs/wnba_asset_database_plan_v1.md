# WNBA Asset Database Plan v1

Yes, we should build this.

A structured asset database is the fastest way to make Mermaid 10x easier and safer. The current render pipeline can now block missing logos, but a database will prevent most blocks by making approved assets deterministic.

## Core idea

Build a league asset registry that maps every team and player to exact approved local assets.

This starts with WNBA and then expands to every HSD league using the same schema.

## Repo structure

```text
data/reference/wnba/
  team_logo_registry.csv
  team_aliases.csv
  player_asset_registry.csv
  player_aliases.csv
  asset_debt.csv

assets/reference/wnba/team_logos/
assets/reference/wnba/player_headshots/
assets/reference/wnba/player_cutouts/
```

## Team logo registry fields

```text
league
team_id
team_name
team_slug
city
nickname
aliases
logo_type
file_path
source_url
source_type
approved_for_render
last_verified_utc
notes
```

## Player asset registry fields

```text
league
player_id
player_name
player_slug
team_id
team_name
aliases
asset_type
file_path
source_url
source_type
approved_for_render
preferred_for_preview
preferred_for_result
last_verified_utc
notes
```

## Alias tables

Aliases prevent naming failures.

Examples:

```text
Aces -> Las Vegas Aces
LV -> Las Vegas Aces
NY Liberty -> New York Liberty
Mercury -> Phoenix Mercury
```

## Render policy

Team-based cards require exact team logos.

No generated logos.
No fuzzy substitutions.
No plain-text fallback when a team logo is required.

If a required logo is missing, Render Studio blocks the card and writes the missing asset into QA.

## Expansion path

After WNBA:

```text
NWSL
USWNT
WTA
LPGA
college softball
women's college basketball
volleyball
Olympic sports
```

Same schema, different league folder.

## Recommended next build

WNBA Asset Database v1:

1. Create WNBA team registry with every current team.
2. Add exact approved team logos.
3. Add alias map.
4. Add player registry shell.
5. Add validator script.
6. Add asset debt report.

The render engine should read this database first, then block missing required assets instead of guessing.
