from __future__ import annotations

import generate_hsd_mermaid_render_studio_v3_0 as base_render  # type: ignore
import generate_hsd_mermaid_render_studio_v3_0_2 as approved_render  # type: ignore


def main() -> None:
    approved_render.parse_packet = base_render.parse_packet
    approved_render.main()


if __name__ == "__main__":
    main()
