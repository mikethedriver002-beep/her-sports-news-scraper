from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from hsd_phase7_editorial_engine import generate_editorial

POLICY = ROOT / "config" / "graphics" / "v5" / "phase7" / "editorial_policy_v1.json"
FIXTURES = ROOT / "config" / "graphics" / "v5" / "phase7" / "fixture_events_v1.json"


def fixture_events():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["events"]


def test_every_supported_sport_generates_passing_copy():
    rows = [generate_editorial(event, policy_path=POLICY) for event in fixture_events()]
    sports = {row["sport_id"] for row in rows}
    assert sports == {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"}
    assert all(row["phase7_editorial_quality_status"] == "passed_phase7_editorial_quality" for row in rows)
    assert all(int(row["phase7_editorial_banned_count"]) == 0 for row in rows)


def test_wnba_preview_replaces_generic_fallback_language():
    event = next(row for row in fixture_events() if row["event_id"] == "fixture-wnba-preview")
    editorial = generate_editorial(event, policy_path=POLICY)
    public = editorial["phase7_editorial_public_copy"].upper()
    assert "DALLAS" in public or "SEATTLE" in public
    for generic in [
        "TEAM IDENTITY",
        "MATCHUP IMPACT",
        "KEY EDGE",
        "WHO HAS THE EDGE TONIGHT",
        "PACE • STARS",
        "PLAYER FEATURE",
    ]:
        assert generic not in public


def test_team_spotlight_uses_matchup_specific_question():
    event = {
        "event_id": "dallas-seattle-spotlight",
        "sport_id": "wnba",
        "kind": "spotlight",
        "primary_name": "Dallas Wings",
        "secondary_name": "Seattle Storm",
        "primary_short": "Dallas",
        "secondary_short": "Seattle",
    }
    editorial = generate_editorial(event, policy_path=POLICY)
    combined = editorial["phase7_editorial_public_copy"].upper()
    assert "DALLAS" in combined
    assert "SEATTLE" in combined or "DALLAS'" in combined
    assert "WHAT HAS TO TRAVEL TONIGHT?" in combined or "WHAT HAS TO CLICK?" in combined or "ROAD QUESTION" in combined


def test_editorial_selection_is_deterministic():
    event = next(row for row in fixture_events() if row["event_id"] == "fixture-tennis-preview")
    first = generate_editorial(event, policy_path=POLICY)
    second = generate_editorial(event, policy_path=POLICY)
    assert first["phase7_editorial_public_copy"] == second["phase7_editorial_public_copy"]


def test_concise_verified_angle_can_be_used_but_banned_angle_cannot():
    base = {
        "event_id": "manual-nwsl",
        "sport_id": "nwsl",
        "kind": "preview",
        "primary_name": "Orlando Pride",
        "secondary_name": "Washington Spirit",
        "primary_short": "Orlando",
        "secondary_short": "Washington",
    }
    good = generate_editorial({**base, "verified_angle": "CAN ORLANDO PLAY THROUGH WASHINGTON'S PRESS?"}, policy_path=POLICY)
    assert good["watch_body"] == "CAN ORLANDO PLAY THROUGH WASHINGTON'S PRESS?"
    bad = generate_editorial({**base, "verified_angle": "TEAM IDENTITY • MATCHUP IMPACT • KEY EDGE"}, policy_path=POLICY)
    assert "TEAM IDENTITY" not in bad["watch_body"].upper()


def test_wnba_one_point_result_uses_survives_language():
    event = next(row for row in fixture_events() if row["event_id"] == "fixture-wnba-result")
    editorial = generate_editorial(event, policy_path=POLICY)
    assert editorial["editorial_headline"] == "Dallas SURVIVES"
