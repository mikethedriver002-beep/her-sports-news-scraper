from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_manual_surface_index_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_manual_surface_index_v1", SCRIPT)
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


def make_packet(
    latest_root: Path,
    packet: str,
    *,
    primary: str,
    report: str,
    csv_name: str,
    status: str,
    count_key: str,
    count_value: int,
) -> None:
    root = latest_root / packet
    write_json(
        root / "manifest.json",
        {
            "status": status,
            "generated_at_utc": "2026-07-05T17:00:00+00:00",
            count_key: count_value,
        },
    )
    write_text(root / primary, f"{packet} primary")
    write_text(root / report, f"# {packet} report\n")
    write_csv(root / csv_name, [{"id": packet, "operator_decision": ""}])


def test_wnba_manual_surface_index_prioritizes_current_surfaces_and_mirrors_latest(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "outputs/local/latest/files"
    output_dir = tmp_path / "outputs/local/tmp/wnba_manual_surface_index_v1"

    make_packet(
        latest_root,
        "wnba_fever_visual_rank_v1",
        primary="wnba_fever_visual_rank_board.html",
        report="wnba_fever_visual_rank_report.md",
        csv_name="wnba_fever_visual_rank_board.csv",
        status="wnba_fever_visual_rank_ready",
        count_key="row_count",
        count_value=5,
    )
    make_packet(
        latest_root / "wnba_fever_source_scout_v1",
        "review_deck",
        primary="action_photo_review_deck.html",
        report="action_photo_review_deck_report.md",
        csv_name="manual_decision_export_template.csv",
        status="action_photo_review_deck_ui_ready",
        count_key="candidate_item_count",
        count_value=5,
    )
    make_packet(
        latest_root,
        "wnba_storm_visual_rank_v1",
        primary="wnba_storm_visual_rank_board.html",
        report="wnba_storm_visual_rank_report.md",
        csv_name="wnba_storm_visual_rank_board.csv",
        status="wnba_storm_visual_rank_ready",
        count_key="row_count",
        count_value=5,
    )
    make_packet(
        latest_root,
        "wnba_official_source_expansion_next_v1",
        primary="wnba_storm_source_scout_report.md",
        report="wnba_storm_source_scout_report.md",
        csv_name="wnba_storm_source_scout_board.csv",
        status="wnba_storm_source_scout_ready",
        count_key="candidate_row_count",
        count_value=5,
    )
    make_packet(
        latest_root,
        "wnba_fever_source_scout_v1",
        primary="wnba_fever_source_scout_report.md",
        report="wnba_fever_source_scout_report.md",
        csv_name="wnba_fever_source_scout_intake.csv",
        status="wnba_fever_source_scout_ready",
        count_key="candidate_row_count",
        count_value=5,
    )
    make_packet(
        latest_root,
        "wnba_apcs039_score_command_refine_v2",
        primary="contact_sheet.png",
        report="visual_report.md",
        csv_name="manual_visual_review_intake.csv",
        status="wnba_apcs039_score_command_refine_v2_ready",
        count_key="variant_count",
        count_value=5,
    )
    make_packet(
        latest_root,
        "wnba_source_quality_next_v1",
        primary="wnba_source_quality_next_report.md",
        report="wnba_source_quality_next_report.md",
        csv_name="wnba_source_quality_next_board.csv",
        status="wnba_source_quality_next_ready",
        count_key="row_count",
        count_value=4,
    )

    manifest = module.build_packet(output_dir=output_dir, latest_files_root=latest_root)
    rows = read_csv(output_dir / "wnba_manual_surface_index.csv")
    html = (output_dir / "wnba_manual_surface_index.html").read_text(encoding="utf-8")
    report = (output_dir / "wnba_manual_surface_index.md").read_text(encoding="utf-8")
    mirror_manifest = json.loads((latest_root / "wnba_manual_surface_index_v1" / "manifest.json").read_text(encoding="utf-8"))
    mirror_rows = read_csv(latest_root / "wnba_manual_surface_index_v1" / "wnba_manual_surface_index.csv")

    assert manifest["status"] == "wnba_manual_surface_index_ready"
    assert manifest["surface_count"] == 7
    assert manifest["available_surface_count"] == 7
    assert manifest["download_approved"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["publish_ready"] is False
    assert [row["surface_id"] for row in rows] == [
        "wnba_fever_visual_rank",
        "wnba_fever_swipe_deck",
        "wnba_storm_visual_rank",
        "wnba_storm_source_scout",
        "wnba_fever_source_scout",
        "wnba_apcs039_score_command",
        "wnba_source_quality_next",
    ]
    assert rows[0]["priority"] == "P1_manual_review_now"
    assert rows[2]["surface_id"] == "wnba_storm_visual_rank"
    assert rows[2]["candidate_or_variant_count"] == "5"
    assert "Use the Fever visual-rank board first, then the Storm visual-rank board" in report
    assert "WNBA Storm visual-rank board" in html
    assert "WNBA Storm scout and deck" in html
    assert "download_approved=no" in html
    assert mirror_manifest["surface_count"] == 7
    assert mirror_rows[0]["surface_id"] == "wnba_fever_visual_rank"


def test_wnba_manual_surface_index_marks_missing_surfaces(tmp_path: Path) -> None:
    module = load_module()
    output_dir = tmp_path / "out"
    latest_root = tmp_path / "missing_latest"

    manifest = module.build_packet(output_dir=output_dir, latest_files_root=latest_root)
    rows = read_csv(output_dir / "wnba_manual_surface_index.csv")

    assert manifest["available_surface_count"] == 0
    assert all(row["available"] == "false" for row in rows)
    assert all(row["status"] == "missing" for row in rows)
