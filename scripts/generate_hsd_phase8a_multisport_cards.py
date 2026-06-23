from __future__ import annotations

"""Phase 8A multi-sport review-card renderer wrapper."""

import argparse
import json
from pathlib import Path
from typing import List, Optional

import generate_hsd_phase7_multisport_cards as phase7_cards
from hsd_phase8a_editorial_engine import VERSION as EDITORIAL_VERSION, generate_editorial

VERSION = "v1.0-phase8a-multisport-review-card-renderer"

# Repoint the Phase 7 renderer module to Phase 8A copy and outputs.
phase7_cards.generate_editorial = generate_editorial
phase7_cards.VERSION = VERSION
phase7_cards.OUT_ROOT = Path("outputs/latest/HSD_PHASE8A_MULTISPORT")
phase7_cards.CARDS_ROOT = phase7_cards.OUT_ROOT / "review_cards"
phase7_cards.MANIFEST_JSON = phase7_cards.OUT_ROOT / "phase8a_multisport_manifest.json"
phase7_cards.MANIFEST_CSV = phase7_cards.OUT_ROOT / "phase8a_multisport_manifest.csv"
phase7_cards.CONTACT_SHEET = phase7_cards.OUT_ROOT / "phase8a_multisport_contact_sheet.jpg"
phase7_cards.REPORT_JSON = Path("phase8a_multisport_renderer_report.json")
phase7_cards.REPORT_MD = Path("phase8a_multisport_renderer_report.md")

_original_write = phase7_cards.write_outputs

def write_outputs(report):
    report = dict(report)
    report["version"] = VERSION
    report["phase8a_editorial_version"] = EDITORIAL_VERSION
    # Keep older row fields for renderer internals, but add a clear Phase 8A report.
    _original_write(report)
    if phase7_cards.REPORT_MD.exists():
        phase7_cards.REPORT_MD.write_text("\n".join([
            "# HSD Phase 8A Multi-Sport Review Card Renderer", "", f"Mode: `{report.get('mode')}`", f"Status: `{report.get('status')}`", f"Rendered: `{report.get('rendered_count')}`", f"Editorial failures: `{report.get('editorial_failed_count')}`", "Production cutover allowed: `false`", "Auto-publish allowed: `false`", "", "Phase 8A uses sport-specific phrase libraries and duplicate-clause validation.", "",
        ]) + "\n", encoding="utf-8")

phase7_cards.write_outputs = write_outputs


def main(argv: Optional[List[str]] = None) -> int:
    return phase7_cards.main(argv)

if __name__ == "__main__":
    raise SystemExit(main())
