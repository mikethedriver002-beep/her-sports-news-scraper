from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_hsd_mermaid_render_studio_v3_0_2 as approved_render_studio  # type: ignore


def main() -> None:
    approved_render_studio.main()


if __name__ == "__main__":
    main()
