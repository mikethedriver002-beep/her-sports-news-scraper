from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_event_builder_covers_every_sport(monkeypatch, tmp_path: Path):
    module = load_module(SCRIPTS / "build_hsd_phase7_event_packets.py", "phase7_event_builder")
    monkeypatch.setattr(module, "FIXTURES", ROOT / "config" / "graphics" / "v5" / "phase7" / "fixture_events_v1.json")
    report = module.build("fixture_audit")
    assert report["status"] == "passed_phase7_event_packets"
    assert report["event_count"] == 14
    assert all(count >= 2 for count in report["sport_counts"].values())
    assert report["blockers"] == []


def test_manual_ready_packet_maps_other_sport():
    module = load_module(SCRIPTS / "build_hsd_phase7_event_packets.py", "phase7_event_builder_manual")
    event = module.manual_packet_event(
        {
            "packet_id": "packet-nwsl-1",
            "content_readiness": "ready_with_review",
            "sport": "NWSL",
            "league": "NWSL",
            "story_type": "preview",
            "headline": "Orlando Pride at Washington Spirit",
            "teams": "Orlando Pride;Washington Spirit",
            "angle": "CAN ORLANDO PLAY THROUGH WASHINGTON'S PRESS?",
        },
        "test_packet",
    )
    assert event is not None
    assert event["sport_id"] == "nwsl"
    assert event["primary_name"] == "Orlando Pride"
    assert event["secondary_name"] == "Washington Spirit"
    assert event["fixture_only"] is False


def test_live_builder_rejects_fixture_escape(monkeypatch):
    module = load_module(SCRIPTS / "build_hsd_phase7_event_packets.py", "phase7_event_builder_escape")
    monkeypatch.setattr(module, "events_from_live_json", lambda: [{
        "event_id": "bad-fixture",
        "sport_id": "tennis",
        "kind": "preview",
        "primary_name": "A",
        "secondary_name": "B",
        "fixture_only": True,
    }])
    monkeypatch.setattr(module, "events_from_manual_packets", lambda: [])
    monkeypatch.setattr(module, "events_from_wnba_manifest", lambda: [])
    report = module.build("live_data")
    assert report["status"] == "blocked_phase7_event_packets"
    assert any("fixture_event_in_live_data" in reason for reason in report["blockers"])
