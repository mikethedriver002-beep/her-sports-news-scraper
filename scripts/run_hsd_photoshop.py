from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_creative_tools import build_photoshop_wrapper_command, resolve_photoshop_execution


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["probe", "open", "jsx"], default="probe")
    parser.add_argument("--input-path", action="append", default=[])
    parser.add_argument("--jsx-path", default="")
    parser.add_argument("--visible", default="true")
    parser.add_argument("--quit-after", default="false")
    parser.add_argument("--launch-if-needed", default="true")
    parser.add_argument("--timeout-sec", type=int, default=75)
    args = parser.parse_args()

    photoshop = resolve_photoshop_execution(probe_com=False)
    command = build_photoshop_wrapper_command(
        mode=args.mode,
        input_paths=args.input_path,
        jsx_path=args.jsx_path or None,
        visible=parse_bool(args.visible),
        quit_after=parse_bool(args.quit_after),
        launch_if_needed=parse_bool(args.launch_if_needed),
        timeout_sec=args.timeout_sec,
        executable_path=photoshop.get("executable_path") or None,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=args.timeout_sec,
        )
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "available": False,
                    "error": f"Photoshop wrapper timed out after {args.timeout_sec} seconds.",
                    "wrapper_command": command,
                    "executable_path": photoshop.get("executable_path", ""),
                }
            )
        )
        return 1

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    payload: dict[str, object]
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {
                "mode": args.mode,
                "available": False,
                "error": "Wrapper returned non-JSON stdout.",
                "stdout": stdout,
                "stderr": stderr,
                "wrapper_command": command,
                "executable_path": photoshop.get("executable_path", ""),
            }
    else:
        payload = {
            "mode": args.mode,
            "available": False,
            "error": "Wrapper returned no stdout.",
            "stderr": stderr,
            "wrapper_command": command,
            "executable_path": photoshop.get("executable_path", ""),
        }

    payload.setdefault("wrapper_command", command)
    payload.setdefault("executable_path", photoshop.get("executable_path", ""))
    print(json.dumps(payload))
    return 0 if completed.returncode == 0 and payload.get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
