from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_manual_surface_index_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_manual_surface_index_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_surface_packet(root: Path, *, status: str, generated_at_utc: str, count_key: str, count_value: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_json(
        root / "manifest.json",
        {
            "status": status,
            "generated_at_utc": generated_at_utc,
            count_key: count_value,
        },
    )


def test_manual_surface_index_scans_current_surfaces_and_mirrors_latest(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "outputs/local/latest/files"
    output_dir = tmp_path / "outputs/local/tmp/action_photo_manual_surface_index_v1"

    make_surface_packet(
        latest_root / "apcs048_visual_rescue_v1",
        status="apcs048_visual_rescue_ready",
        generated_at_utc="2026-07-04T02:03:01.751396+00:00",
        count_key="variant_count",
        count_value=6,
    )
    write_text(latest_root / "apcs048_visual_rescue_v1" / "contact_sheet.png", "png")
    write_text(latest_root / "apcs048_visual_rescue_v1" / "visual_report.md", "# APCS048\n")
    write_csv(
        latest_root / "apcs048_visual_rescue_v1" / "manual_visual_review_intake.csv",
        [{"candidate_id": "APCS048", "variant_id": "rescue_01_gold_confetti_hero"}],
    )

    make_surface_packet(
        latest_root / "action_photo_review_deck_official_source_expansion_v7",
        status="action_photo_review_deck_ui_ready",
        generated_at_utc="2026-07-04T18:17:55.000000+00:00",
        count_key="deck_item_count",
        count_value=6,
    )
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v7" / "action_photo_review_deck.html", "<html>purdue</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v7" / "action_photo_review_deck_report.md", "# Purdue\n")
    write_csv(
        latest_root / "action_photo_review_deck_official_source_expansion_v7" / "manual_decision_export_template.csv",
        [{"deck_item_id": "candidate_APCS001", "operator_decision": ""}],
    )

    make_surface_packet(
        latest_root / "action_photo_review_deck_official_source_expansion_v6",
        status="action_photo_review_deck_ui_ready",
        generated_at_utc="2026-07-04T17:48:36.190531+00:00",
        count_key="deck_item_count",
        count_value=6,
    )
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v6" / "action_photo_review_deck.html", "<html>uconn</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v6" / "action_photo_review_deck_report.md", "# UConn\n")
    write_csv(
        latest_root / "action_photo_review_deck_official_source_expansion_v6" / "manual_decision_export_template.csv",
        [{"deck_item_id": "candidate_APCS001", "operator_decision": ""}],
    )

    make_surface_packet(
        latest_root / "action_photo_review_deck_official_source_expansion_v5",
        status="action_photo_review_deck_ui_ready",
        generated_at_utc="2026-07-04T16:41:00.000000+00:00",
        count_key="deck_item_count",
        count_value=21,
    )
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v5" / "action_photo_review_deck.html", "<html>world rugby</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v5" / "action_photo_review_deck_report.md", "# World Rugby\n")
    write_csv(
        latest_root / "action_photo_review_deck_official_source_expansion_v5" / "manual_decision_export_template.csv",
        [{"deck_item_id": "candidate_APCS001", "operator_decision": ""}],
    )

    make_surface_packet(
        latest_root / "action_photo_ranker_review_deck_v3",
        status="action_photo_review_deck_ui_ready",
        generated_at_utc="2026-07-04T00:00:00.000000+00:00",
        count_key="deck_item_count",
        count_value=12,
    )
    write_text(latest_root / "action_photo_ranker_review_deck_v3" / "action_photo_review_deck.html", "<html>broad old</html>")
    write_text(latest_root / "action_photo_ranker_review_deck_v3" / "action_photo_review_deck_report.md", "# Broad old\n")
    write_csv(
        latest_root / "action_photo_ranker_review_deck_v3" / "manual_decision_export_template.csv",
        [{"deck_item_id": "candidate_APCS010", "operator_decision": ""}],
    )

    make_surface_packet(
        latest_root / "action_photo_ranker_review_deck_v17",
        status="action_photo_review_deck_ui_ready",
        generated_at_utc="2026-07-04T18:00:00.000000+00:00",
        count_key="deck_item_count",
        count_value=12,
    )
    write_text(latest_root / "action_photo_ranker_review_deck_v17" / "action_photo_review_deck.html", "<html>broad latest</html>")
    write_text(latest_root / "action_photo_ranker_review_deck_v17" / "action_photo_review_deck_report.md", "# Broad latest\n")
    write_csv(
        latest_root / "action_photo_ranker_review_deck_v17" / "manual_decision_export_template.csv",
        [{"deck_item_id": "candidate_APCS011", "operator_decision": ""}],
    )

    manifest = module.build_packet(output_dir=output_dir, latest_files_root=latest_root)
    rows = read_csv(output_dir / "action_photo_manual_surface_index.csv")
    report = (output_dir / "action_photo_manual_surface_index.md").read_text(encoding="utf-8")
    html = (output_dir / "action_photo_manual_surface_index.html").read_text(encoding="utf-8")
    mirror_rows = read_csv(latest_root / "action_photo_manual_surface_index_v1" / "action_photo_manual_surface_index.csv")
    mirror_manifest = json.loads((latest_root / "action_photo_manual_surface_index_v1" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_manual_surface_index_ready"
    assert manifest["surface_count"] == 5
    assert manifest["available_surface_count"] == 5
    assert manifest["literal_contact_sheet_count"] == 1
    assert manifest["latest_broad_deck_resolved"].endswith("action_photo_ranker_review_deck_v17")
    assert manifest["mirror_dir"].endswith("outputs/local/latest/files/action_photo_manual_surface_index_v1")

    assert [row["surface_id"] for row in rows] == [
        "apcs048_visual_rescue",
        "purdue_v7_focus_deck",
        "uconn_v6_focus_deck",
        "world_rugby_v5_focus_deck",
        "latest_broad_deck",
    ]
    assert rows[0]["attachment_mode"] == "literal_contact_sheet"
    assert "Attach the literal contact_sheet.png first" in report
    assert "Purdue women" in report
    assert "Latest broad deck" in html
    assert "action_photo_ranker_review_deck_v17" in html
    assert mirror_rows[0]["surface_id"] == "apcs048_visual_rescue"
    assert mirror_manifest["surface_count"] == 5
    assert mirror_manifest["latest_broad_deck_resolved"].endswith("action_photo_ranker_review_deck_v17")
