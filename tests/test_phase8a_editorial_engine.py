from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hsd_phase8a_editorial_engine import generate_editorial, generate_renderer_editorial, similarity

BANNED = ["TEAM IDENTITY", "MATCHUP IMPACT", "KEY EDGE", "WHO HAS THE EDGE TONIGHT", "PLAYER FEATURE", "PLAYER SPOTLIGHT"]

def combined(copy):
    return " | ".join(str(copy.get(k, "")) for k in ["editorial_headline", "debate_question", "watch_title", "watch_body", "cta"]).upper()


def test_all_sports_generate_non_generic_copy():
    sports = ["wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"]
    for sport in sports:
        event = {"sport_id": sport, "kind": "preview", "primary_name": "New York Liberty" if sport == "wnba" else "Primary Team", "secondary_name": "Las Vegas Aces" if sport == "wnba" else "Secondary Team", "event_id": f"{sport}-preview"}
        copy = generate_editorial(event)
        text = combined(copy)
        assert copy["phase8a_editorial_quality_status"] == "passed_phase8a_editorial_quality", (sport, copy)
        assert not any(token in text for token in BANNED), (sport, text)


def test_renderer_copy_is_fit_safe_for_liberty_aces():
    row = {"event_id": "nyl-las", "away_team_name": "New York Liberty", "home_team_name": "Las Vegas Aces", "headline": "New York Liberty at Las Vegas Aces"}
    copy = generate_renderer_editorial(row)
    assert len(copy["debate_question"]) <= 28
    assert len(copy["watch_title"]) <= 24
    assert len(copy["watch_body"]) <= 54
    assert copy["phase8a_editorial_quality_status"] == "passed_phase8a_editorial_quality"


def test_duplicate_similarity_detects_redundant_clauses():
    assert similarity("CAN NEW YORK TAKE VEGAS OUT OF RHYTHM", "CAN NEW YORK TAKE VEGAS OUT OF RHYTHM?") >= 0.9
    assert similarity("WHO WINS SERVE-PASS", "COUNT THE SECOND CHANCES") < 0.5
