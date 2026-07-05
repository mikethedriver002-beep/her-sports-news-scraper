from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_storm_visual_rank_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_storm_visual_rank_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def board_row(candidate_id: str, entity_id: str, alt: str, score: str = "94", identity: str = "strong_context") -> dict[str, str]:
    return {
        "board_rank": candidate_id[-1],
        "candidate_queue_id": candidate_id,
        "seed_id": candidate_id.replace("WSFS", "STORM"),
        "entity_id": entity_id,
        "source_type": "official_team_recap",
        "source_url": f"https://storm.wnba.com/news/{candidate_id.lower()}",
        "candidate_image_url": f"https://storm.wnba.com/images/{candidate_id.lower()}.jpg",
        "image_alt": alt,
        "score": score,
        "candidate_quality_tier": "A_primary_source_lead",
        "source_provenance_clarity": "clear",
        "identity_confidence": identity,
        "notes": "review-only synthetic Storm row",
    }


def intake_row(candidate_id: str, entity_id: str, evidence: str) -> dict[str, str]:
    return {
        "candidate_queue_id": candidate_id,
        "entity_id": entity_id,
        "source_url": f"https://storm.wnba.com/news/{candidate_id.lower()}",
        "candidate_photo_url": f"https://storm.wnba.com/images/{candidate_id.lower()}.jpg",
        "evidence_summary": evidence,
        "manual_next_action": "manual_inspect_for_formal_intake",
        "download_approved": "no",
        "review_only": "true",
    }


def write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    board_rows = [
        board_row("WSFS001", "wnba_seattle_storm_skylar_diggins", "Skylar Diggins logged 11 points and a triple-double."),
        board_row("WSFS002", "wnba_seattle_storm_nneka_ogwumike", "Storm rallied late as Skylar Diggins and teammates pushed the pace.", "82"),
        board_row("WSFS003", "wnba_seattle_storm_dominique_malonga", "Dominique Malonga had a career-high double-double.", "94", "medium"),
        board_row("WSFS004", "wnba_seattle_storm_gabby_williams", "Nneka Ogwumike and Skylar Diggins scored 21 points apiece.", "78"),
        board_row("WSFS005", "wnba_seattle_storm_erica_wheeler", "Gabby Williams scored 20, Dominique Malonga and Erica Wheeler sparked a rally.", "94", "medium"),
    ]
    intake_rows = [
        intake_row("WSFS001", "wnba_seattle_storm_skylar_diggins", "Skylar Diggins triple-double recap."),
        intake_row("WSFS002", "wnba_seattle_storm_nneka_ogwumike", "Nneka Ogwumike playoff context."),
        intake_row("WSFS003", "wnba_seattle_storm_dominique_malonga", "Dominique Malonga career-high context."),
        intake_row("WSFS004", "wnba_seattle_storm_gabby_williams", "Gabby Williams steal-heavy context."),
        intake_row("WSFS005", "wnba_seattle_storm_erica_wheeler", "Erica Wheeler rally context."),
    ]
    board_csv = tmp_path / "board.csv"
    intake_csv = tmp_path / "intake.csv"
    write_csv(board_csv, board_rows)
    write_csv(intake_csv, intake_rows)
    return board_csv, intake_csv


def test_storm_visual_rank_builds_review_only_board(tmp_path: Path) -> None:
    module = load_module()
    board_csv, intake_csv = write_inputs(tmp_path)
    output_dir = tmp_path / "storm_visual_rank"

    manifest = module.build_packet(board_csv=board_csv, intake_csv=intake_csv, output_dir=output_dir)

    board = read_csv(output_dir / "wnba_storm_visual_rank_board.csv")
    intake = read_csv(output_dir / "wnba_storm_visual_rank_intake.csv")
    html = (output_dir / "wnba_storm_visual_rank_board.html").read_text(encoding="utf-8")
    report = (output_dir / "wnba_storm_visual_rank_report.md").read_text(encoding="utf-8")
    disk_manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "wnba_storm_visual_rank_ready"
    assert disk_manifest["row_count"] == 5
    assert [row["candidate_queue_id"] for row in board[:3]] == ["WSFS001", "WSFS003", "WSFS005"]
    assert board[0]["identity_honesty"] == "subject_explicit_in_alt_text"
    assert board[-1]["candidate_queue_id"] == "WSFS004"
    assert board[-1]["identity_honesty"] == "subject_in_body_copy_only"
    assert all(row["download_approved"] == "no" for row in board)
    assert all(row["review_only"] == "true" for row in board)
    assert all(row["publish_ready"] == "false" for row in board)
    assert all(row["download_approved"] == "no" for row in intake)
    assert disk_manifest["guardrails"]["no_downloads"] is True
    assert "WNBA Storm Visual Rank Board" in report
    assert "WSFS001" in html
    assert "https://storm.wnba.com/images/" in html
    assert "download_approved=yes" not in html


def test_storm_visual_rank_requires_all_five_rows(tmp_path: Path) -> None:
    module = load_module()
    board_csv = tmp_path / "board.csv"
    intake_csv = tmp_path / "intake.csv"
    write_csv(board_csv, [board_row("WSFS001", "wnba_seattle_storm_skylar_diggins", "Skylar Diggins")])
    write_csv(intake_csv, [intake_row("WSFS001", "wnba_seattle_storm_skylar_diggins", "Skylar Diggins")])

    try:
        module.build_packet(board_csv=board_csv, intake_csv=intake_csv, output_dir=tmp_path / "out")
    except ValueError as exc:
        assert "Missing required Storm rows" in str(exc)
        assert "WSFS002" in str(exc)
    else:
        raise AssertionError("Expected missing Storm rows to fail fast")
