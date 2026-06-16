from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v5.0-expected-games-from-observations"
INFILE = Path("source_observations.csv")
OUTFILE = Path("config/hsd_expected_games_v5.csv")
REPORT = Path("expected_games_v5_report.md")
MANIFEST = Path("expected_games_v5_manifest.json")
FIELDS = ["date", "league", "sport", "home_team", "away_team", "expected_key"]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", clean(value).lower())).strip()


def key_for(sport, date, home, away):
    teams = sorted([norm(home), norm(away)])
    return "|".join([clean(sport), clean(date), teams[0], teams[1]])


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def build_rows():
    rows = []
    seen = set()
    skipped = 0
    for item in read_csv(INFILE):
        if clean(item.get("league_norm")) != "WNBA":
            skipped += 1
            continue
        date = clean(item.get("scheduled_date_local"))
        home = clean(item.get("home_team_raw"))
        away = clean(item.get("away_team_raw"))
        sport = clean(item.get("sport_norm") or "basketball")
        if not date or not home or not away:
            skipped += 1
            continue
        key = key_for(sport, date, home, away)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"date": date, "league": "WNBA", "sport": sport, "home_team": home, "away_team": away, "expected_key": key})
    rows.sort(key=lambda row: (row["date"], row["away_team"], row["home_team"]))
    return rows, skipped


def main():
    rows, skipped = build_rows()
    write_csv(OUTFILE, rows)
    manifest = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "input_file": INFILE.as_posix(), "expected_games": len(rows), "skipped_rows": skipped}
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = ["# HSD Expected Games v5", "", f"Generated: `{manifest['generated_at_utc']}`", "", f"- expected games: `{len(rows)}`", f"- skipped rows: `{skipped}`", "", "## Games", ""]
    lines += [f"- {row['date']} | {row['away_team']} at {row['home_team']} | `{row['expected_key']}`" for row in rows] or ["No expected games were generated. Run Results Desk v5 first."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"expected_games": len(rows), "skipped_rows": skipped}, indent=2))


if __name__ == "__main__":
    main()
