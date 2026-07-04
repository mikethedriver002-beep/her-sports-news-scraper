from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_source_selector_board_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_source_selector_board_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wnba_source_selector_board_builds_review_only_board(tmp_path: Path, monkeypatch) -> None:
    out_root = tmp_path / "outputs" / "local" / "tmp" / "wnba_source_selector_board_v1"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", out_root.as_posix())

    module = load_module()
    rc = module.main()
    assert rc == 0

    contact_sheet = out_root / "wnba_source_selector_contact_sheet.png"
    board_md = out_root / "wnba_source_selector_board.md"
    intake_csv = out_root / "manual_source_review_intake.csv"
    manifest_json = out_root / "manifest.json"
    lead_thumb = out_root / "source_thumbnails" / "apcs039_operator_review.png"

    assert contact_sheet.exists()
    assert board_md.exists()
    assert intake_csv.exists()
    assert manifest_json.exists()
    assert lead_thumb.exists()

    with intake_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 4
    lead_row = next(row for row in rows if row["recommended_lead_source"] == "yes")
    assert lead_row["source_id"] == "apcs039_operator_review"
    assert lead_row["crop_viability"] == "very_high"
    assert lead_row["width"] == "1080"
    assert lead_row["height"] == "1920"
    assert rows[0]["source_id"] == "apq001_review_only_candidate"
    assert rows[0]["width"] == "2560"
    assert rows[0]["height"] == "1440"

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["status"] == "wnba_source_selector_board_ready"
    assert manifest["recommended_lead_source"] == "apcs039_operator_review"
    assert manifest["review_only"] is True

    with Image.open(contact_sheet) as sheet:
        assert sheet.width > 1200
        assert sheet.height > 1000
        assert sheet.mode == "RGB"

    board_text = board_md.read_text(encoding="utf-8")
    assert "Jackie Young APCS039" in board_text
    assert "Recommended lead source" in board_text
