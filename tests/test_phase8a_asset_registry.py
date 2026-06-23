import csv
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_hsd_phase8a_asset_registry import build_report


def test_sparks_is_required_in_asset_policy(tmp_path, monkeypatch):
    import validate_hsd_phase8a_asset_registry as mod
    policy = tmp_path / "policy.json"
    registry = tmp_path / "team_logos.csv"
    policy.write_text('{"required_wnba_team_ids":["los_angeles_sparks"]}', encoding="utf-8")
    with registry.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"])
        writer.writeheader()
        writer.writerow({"team_id": "los_angeles_sparks", "asset_type": "primary_logo", "file_path": "assets/leagues/wnba/teams/los_angeles_sparks/logo.png", "file_exists": "true", "approved": "true", "required": "true", "last_verified_utc": "now", "source_note": "test"})
    monkeypatch.setattr(mod, "POLICY", policy)
    monkeypatch.setattr(mod, "REGISTRY", registry)
    monkeypatch.setattr(mod, "MANIFEST", tmp_path / "manifest.json")
    report = mod.build_report("fixture_audit")
    assert report["status"] == "passed_phase8a_asset_registry"
    assert report["exact_ready_count"] == 1
