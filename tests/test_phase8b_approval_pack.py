from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_hsd_phase8b_live_approval_pack import decision_for


def test_approval_pack_holds_team_spotlight():
    row = {"technical_status":"live_technical_candidate","asset_assurance_player_route":"downgraded_player_to_non_player_team_spotlight"}
    decision, reason = decision_for(row)
    assert decision == "hold"
    assert "TEAM SPOTLIGHT" in reason


def test_approval_pack_blocks_technical_failures():
    row = {"technical_status":"blocked_live_candidate","technical_reasons":"fidelity_below_technical_floor"}
    decision, reason = decision_for(row)
    assert decision == "needs_fix"
    assert "fidelity" in reason
