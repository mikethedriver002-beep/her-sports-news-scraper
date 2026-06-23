from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pathlib import Path
import json

from scripts.build_hsd_phase8b_multisport_daily_packets import normalize_event, validate_event


def test_non_wnba_packet_validates():
    event = normalize_event({"sport_id":"nwsl","kind":"preview","primary_name":"Orlando Pride","secondary_name":"Washington Spirit"}, 1)
    assert validate_event(event) == []
    assert event["sport_id"] == "nwsl"


def test_wnba_manual_packet_not_needed():
    event = normalize_event({"sport_id":"wnba","kind":"preview","primary_name":"A","secondary_name":"B"}, 1)
    assert "wnba_packet_not_needed_in_phase8b_manual_inbox" in validate_event(event)
