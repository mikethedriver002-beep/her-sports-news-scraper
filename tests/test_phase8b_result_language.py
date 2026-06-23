from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hsd_phase8b_result_language import generate_result_editorial, validate_result_editorial


def test_final_score_language_not_generic():
    row = {"headline":"Connecticut Sun beat Chicago Sky","editorial_scoreline":"Sun 92, Sky 63.","editorial_margin":"29","item_id":"fixture"}
    ed = generate_result_editorial(row)
    public = ed["phase8b_result_public_copy"].upper()
    assert "FINAL READ" not in public
    assert "CLEANEST STRETCH" not in public
    assert "BIGGEST REASON" not in public
    assert not validate_result_editorial(ed)


def test_close_game_language_has_decisive_lever():
    row = {"headline":"Dallas Wings beat Seattle Storm","scoreline":"Wings 84, Storm 82.","winner_score":"84","loser_score":"82","item_id":"close"}
    ed = generate_result_editorial(row)
    assert ed["phase8b_result_band"] == "close"
    assert ed["phase8b_result_language_status"] == "passed_phase8b_result_language"
