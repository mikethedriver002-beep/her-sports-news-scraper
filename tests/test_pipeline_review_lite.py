from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_pipeline_review_lite_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_pipeline_review_lite_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_lite_scrubs_stale_marker_literals_on_copy(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    source_root = tmp_path / "source"
    run_dir = tmp_path / "run"
    source_root.mkdir()
    run_dir.mkdir()
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(source_root))
    monkeypatch.chdir(tmp_path)

    candidate_source = source_root / "athlete_render_candidate_board_v1.md"
    candidate_source.write_text(
        "\n".join(
            [
                "# HSD Athlete Render Candidate Board v1",
                "",
                "- review-only",
                "  - marker=`assets/leagues/wnba/athletes/example/headshot.png.approved`",
            ]
        ),
        encoding="utf-8",
    )
    approval_source = source_root / "outputs" / "latest" / "review_files" / "athlete_image_approval_pack"
    approval_source.mkdir(parents=True)
    approval_report = approval_source / "athlete_image_approval_pack_report.md"
    approval_report.write_text(
        "To approve an image later, the reviewed file must be copied to its approval target path and an `.approved` marker must exist.",
        encoding="utf-8",
    )

    manifest: list[dict[str, str]] = []
    module.copy_if_exists("athlete_render_candidate_board_v1.md", run_dir, manifest)
    module.safe_copy_tree_files(
        Path("outputs/latest/review_files/athlete_image_approval_pack"),
        run_dir / "athlete_image_approval_pack",
        manifest,
    )

    candidate_copy = run_dir / "athlete_render_candidate_board_v1.md"
    approval_copy = run_dir / "athlete_image_approval_pack" / "athlete_image_approval_pack_report.md"

    assert candidate_copy.read_text(encoding="utf-8") == "\n".join(
        [
            "# HSD Athlete Render Candidate Board v1",
            "",
            "- review-only",
            "  - review_marker_present=true",
        ]
    )
    assert ".approved" not in candidate_copy.read_text(encoding="utf-8")
    assert "approval target path" not in approval_copy.read_text(encoding="utf-8")
    assert "review target path" in approval_copy.read_text(encoding="utf-8")
    assert ".approved" not in approval_copy.read_text(encoding="utf-8")
