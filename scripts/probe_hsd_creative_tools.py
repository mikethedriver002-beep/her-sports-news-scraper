from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_creative_tools import (
    build_photoshop_cli_command,
    build_photoshop_wrapper_command,
    discover_local_creative_tools,
    photoshop_cli_wrapper_path,
    photoshop_wrapper_path,
)


def main() -> int:
    payload = discover_local_creative_tools(probe_photoshop_com=True)
    payload["photoshop"]["wrapper_probe_command"] = build_photoshop_wrapper_command(mode="probe")
    payload["photoshop"]["cli_probe_command"] = build_photoshop_cli_command(mode="probe")
    payload["photoshop"]["wrapper_script_exists"] = photoshop_wrapper_path().exists()
    payload["photoshop"]["cli_wrapper_script_exists"] = photoshop_cli_wrapper_path().exists()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
