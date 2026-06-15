from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_hsd_mermaid_render_studio_v3_0_3 as render_runner  # type: ignore


def main() -> None:
    render_runner.main()


if __name__ == "__main__":
    main()
