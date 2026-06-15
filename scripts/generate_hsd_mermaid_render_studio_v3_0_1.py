from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_hsd_mermaid_render_studio_v3_0 as render_v3  # type: ignore


def choose_template(packet: Dict[str, Any]) -> str:
    headline = str(packet.get("headline", "")).lower()
    content_type = str(packet.get("content_type", "")).lower()
    league = str(packet.get("league", "")).upper()

    if league == "WNBA":
        if "last night in the w" in headline:
            return "last_night_scoreboard"
        if "preview" in content_type or " at " in headline or " vs " in headline:
            return "preview_matchup"
        if "beat" in headline or "result" in content_type or "recap" in content_type:
            return "result_final"
        return "storyline_feature"

    # Non-WNBA stories must not become matchup graphics just because the headline contains
    # words like "at" as part of an event title, e.g. "at the Dow Championship".
    return "storyline_feature"


def main() -> None:
    render_v3.VERSION = "v3.0.1-router-fix-logo-gap-pack"
    render_v3.choose_template = choose_template
    render_v3.main()


if __name__ == "__main__":
    main()
