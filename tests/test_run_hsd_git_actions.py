from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_hsd_git_actions.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_hsd_git_actions", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_args_collects_repeated_adds() -> None:
    module = load_module()
    args = module.parse_args(
        [
            "--add",
            "scripts/foo.py",
            "--add",
            "tests/bar.py",
            "--message",
            "checkpoint",
            "--push",
        ]
    )
    assert args.add == ["scripts/foo.py", "tests/bar.py"]
    assert args.message == "checkpoint"
    assert args.push is True


def test_main_rejects_conflicting_body_flags() -> None:
    module = load_module()
    with pytest.raises(SystemExit):
        module.main(
            [
                "--body",
                "hello",
                "--body-file",
                "body.md",
            ]
        )
