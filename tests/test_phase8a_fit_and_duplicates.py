from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hsd_phase8a_editorial_engine import generate_editorial


def test_fit_caps_hold_for_tennis_and_lpga():
    for sport, a, b in [("tennis", "Coco Gauff", "Iga Swiatek"), ("lpga", "Nelly Korda", "The Field")]:
        copy = generate_editorial({"sport_id": sport, "kind": "preview", "primary_name": a, "secondary_name": b, "event_id": sport})
        assert len(copy["debate_question"]) <= 58
        assert len(copy["watch_title"]) <= 32
        assert len(copy["watch_body"]) <= 88
        assert copy["phase8a_duplicate_clause_count"] == 0


def test_banned_phrase_is_not_generated_for_softball_or_volleyball():
    banned = "TEAM IDENTITY|MATCHUP IMPACT|KEY EDGE|CONTROL TEST"
    for sport in ["ncaa_softball", "volleyball"]:
        copy = generate_editorial({"sport_id": sport, "kind": "spotlight", "primary_name": "Nebraska Cornhuskers", "secondary_name": "Wisconsin Badgers", "event_id": sport})
        text = "|".join(str(copy.get(k, "")).upper() for k in ["debate_question", "watch_title", "watch_body", "cta"])
        assert not any(token in text for token in banned.split("|"))
        assert copy["phase8a_editorial_quality_status"] == "passed_phase8a_editorial_quality"
