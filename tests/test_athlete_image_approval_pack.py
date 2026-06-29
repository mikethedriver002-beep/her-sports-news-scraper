from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_athlete_image_approval_pack_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_athlete_image_approval_pack_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_approval_pack_report_stays_review_only_without_approved_marker_literal(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)

    out_root = tmp_path / "outputs" / "latest" / "review_files" / "athlete_image_approval_pack"
    monkeypatch.setattr(module, "SRC", tmp_path / "data" / "asset_registry" / "wnba" / "athlete_image_match_review.csv")
    monkeypatch.setattr(module, "OUT_ROOT", out_root)
    monkeypatch.setattr(module, "DOWNLOAD_DIR", out_root / "downloads")
    monkeypatch.setattr(module, "SHEET_DIR", out_root / "contact_sheets")
    monkeypatch.setattr(module, "REPORT_MD", out_root / "athlete_image_approval_pack_report.md")
    monkeypatch.setattr(module, "MANIFEST_JSON", out_root / "athlete_image_approval_pack_manifest.json")
    monkeypatch.setattr(module, "DOWNLOAD_MANIFEST", out_root / "download_manifest.csv")
    monkeypatch.setattr(module, "APPROVAL_CSV", out_root / "approval_decisions.csv")
    monkeypatch.setattr(module, "SUMMARY", tmp_path / "outputs" / "latest" / "summary.json")
    module.SRC.parent.mkdir(parents=True, exist_ok=True)
    module.SRC.write_text("status\n", encoding="utf-8")

    module.main()

    report = module.REPORT_MD.read_text(encoding="utf-8")
    assert "This is a review-only approval pack." in report
    assert "separate human-reviewed marker record" in report
    assert ".approved" not in report
