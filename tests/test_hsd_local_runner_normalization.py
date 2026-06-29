from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "hsd_local.ps1"


def test_review_artifact_normalizer_handles_crlf_marker_lines(tmp_path: Path) -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    start = runner.index("function Normalize-HsdCollectedReviewArtifact")
    end = runner.index("function Copy-IfPresent")
    function_block = runner[start:end].strip()

    wrapper = tmp_path / "normalize.ps1"
    wrapper.write_text(
        "\n".join(
            [
                "param([string]$Path)",
                "",
                function_block,
                "",
                "Normalize-HsdCollectedReviewArtifact -Relative 'athlete_render_candidate_board_v1.md' -Path $Path",
                "",
            ]
        ),
        encoding="utf-8",
    )

    artifact = tmp_path / "athlete_render_candidate_board_v1.md"
    with artifact.open("w", encoding="utf-8", newline="\r\n") as handle:
        handle.write("header\n  - marker=`assets/leagues/wnba/athletes/example/headshot.png.approved`\nfooter\n")

    subprocess.run(
        [
            "powershell",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            wrapper.as_posix(),
            "-Path",
            artifact.as_posix(),
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )

    text = artifact.read_text(encoding="utf-8")
    assert "review_marker_present=true" in text
    assert ".approved" not in text
    assert "  - marker=`" not in text
