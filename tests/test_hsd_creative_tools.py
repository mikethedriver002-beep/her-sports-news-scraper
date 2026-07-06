from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hsd_creative_tools


def test_resolve_photoshop_execution_prefers_com_when_probe_enabled(monkeypatch) -> None:
    fake_path = Path(r"E:\Installed Programs\Creative Cloud\Adobe Photoshop 2025\Photoshop.exe")
    monkeypatch.setattr(hsd_creative_tools, "_query_registry_app_path", lambda exe_name: fake_path)
    monkeypatch.setattr(hsd_creative_tools, "_query_uninstall_install_location", lambda display_name: None)
    monkeypatch.setattr(hsd_creative_tools, "_first_existing_path", lambda candidates: fake_path)
    monkeypatch.setattr(
        hsd_creative_tools,
        "probe_photoshop_com",
        lambda timeout_sec=20: {"available": True, "version": "26.4.1", "error": ""},
    )

    result = hsd_creative_tools.resolve_photoshop_execution(probe_com=True)

    assert result["available"] is True
    assert result["executable_path"] == fake_path.as_posix()
    assert result["preferred_execution_mode"] == "com"
    assert result["com_available"] is True
    assert result["com_version"] == "26.4.1"


def test_discover_local_creative_tools_reports_photoshop_path_without_probe(monkeypatch) -> None:
    fake_path = Path(r"E:\Installed Programs\Creative Cloud\Adobe Photoshop 2025\Photoshop.exe")
    monkeypatch.setattr(hsd_creative_tools, "_query_registry_app_path", lambda exe_name: fake_path)
    monkeypatch.setattr(hsd_creative_tools, "_query_uninstall_install_location", lambda display_name: None)
    monkeypatch.setattr(hsd_creative_tools, "_first_existing_path", lambda candidates: fake_path if candidates else None)

    tools = hsd_creative_tools.discover_local_creative_tools(probe_photoshop_com=False)

    assert tools["photoshop"]["available"] is True
    assert tools["photoshop"]["executable_path"] == fake_path.as_posix()
    assert tools["photoshop"]["preferred_execution_mode"] == "exe"
    assert tools["photoshop"]["wrapper_script_path"].endswith("scripts/run_hsd_photoshop_com.ps1")


def test_build_photoshop_wrapper_command_uses_wrapper_script() -> None:
    command = hsd_creative_tools.build_photoshop_wrapper_command(
        mode="jsx",
        input_paths=["D:/tmp/input.png"],
        jsx_path="D:/tmp/task.jsx",
        visible=False,
        quit_after=True,
    )

    assert command[:6] == [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Sta",
        "-File",
    ]
    assert command[6] == str(hsd_creative_tools.photoshop_wrapper_path())
    assert "-Mode" in command
    assert "jsx" in command
    assert "D:/tmp/input.png" in command
    assert "D:/tmp/task.jsx" in command
    assert "false" in command
    assert "true" in command


def test_build_photoshop_cli_command_uses_python_wrapper() -> None:
    command = hsd_creative_tools.build_photoshop_cli_command(
        mode="open",
        input_paths=["D:/tmp/input.png"],
        visible=False,
        timeout_sec=33,
    )

    assert command[:4] == [
        "python",
        str(hsd_creative_tools.photoshop_cli_wrapper_path()),
        "--mode",
        "open",
    ]
    assert "--input-path" in command
    assert "D:/tmp/input.png" in command
    assert "--timeout-sec" in command
    assert "33" in command
