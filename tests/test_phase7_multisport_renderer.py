from __future__ import annotations

import importlib.util
import json
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


def test_fixture_renderer_creates_every_sport_card(monkeypatch, tmp_path: Path):
    module = load_module(SCRIPTS / "generate_hsd_phase7_multisport_cards.py", "phase7_cards")
    fixtures = json.loads((ROOT / "config" / "graphics" / "v5" / "phase7" / "fixture_events_v1.json").read_text(encoding="utf-8"))
    events_path = tmp_path / "events.json"
    events_path.write_text(json.dumps({"events": fixtures["events"]}), encoding="utf-8")
    monkeypatch.setattr(module, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(module, "CARDS_ROOT", tmp_path / "out" / "review_cards")
    monkeypatch.setattr(module, "CONTACT_SHEET", tmp_path / "out" / "contact.jpg")
    report = module.build(events_path, "fixture_audit", True)
    assert report["status"] == "passed_phase7_multisport_renderer"
    assert report["rendered_count"] == 14
    assert report["editorial_failed_count"] == 0
    assert all(Path(row["output_path"]).exists() for row in report["rows"])
    assert all(row["human_visual_approval_required"] == "true" for row in report["rows"])


def test_live_renderer_allows_no_non_wnba_packets(monkeypatch, tmp_path: Path):
    module = load_module(SCRIPTS / "generate_hsd_phase7_multisport_cards.py", "phase7_cards_live")
    events_path = tmp_path / "events.json"
    events_path.write_text(json.dumps({"events": [{
        "event_id": "wnba-only",
        "sport_id": "wnba",
        "kind": "preview",
        "primary_name": "Dallas Wings",
        "secondary_name": "Seattle Storm",
        "fixture_only": False,
    }]}), encoding="utf-8")
    monkeypatch.setattr(module, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(module, "CARDS_ROOT", tmp_path / "out" / "review_cards")
    report = module.build(events_path, "live_data", False)
    assert report["status"] == "passed_phase7_multisport_renderer"
    assert report["rendered_count"] == 0
    assert "no_non_wnba_live_packets_available_for_phase7_cards" in report["warnings"]
