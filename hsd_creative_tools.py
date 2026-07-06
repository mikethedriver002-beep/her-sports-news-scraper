from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None  # type: ignore[assignment]


def repo_root() -> Path:
    return Path(__file__).resolve().parent


DEFAULT_PHOTOSHOP_COM_TIMEOUT_SEC = 45


def photoshop_wrapper_path() -> Path:
    return repo_root() / "scripts" / "run_hsd_photoshop_com.ps1"


def photoshop_cli_wrapper_path() -> Path:
    return repo_root() / "scripts" / "run_hsd_photoshop.py"


def build_photoshop_wrapper_command(
    *,
    mode: str = "probe",
    input_paths: list[str] | None = None,
    jsx_path: str | None = None,
    visible: bool = True,
    quit_after: bool = False,
    launch_if_needed: bool = True,
    timeout_sec: int = DEFAULT_PHOTOSHOP_COM_TIMEOUT_SEC,
    executable_path: str | None = None,
) -> list[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Sta",
        "-File",
        str(photoshop_wrapper_path()),
        "-Mode",
        mode,
        "-Visible",
        "true" if visible else "false",
        "-QuitAfter",
        "true" if quit_after else "false",
        "-LaunchIfNeeded",
        "true" if launch_if_needed else "false",
        "-TimeoutSec",
        str(int(timeout_sec)),
    ]
    if executable_path:
        command.extend(["-ExecutablePath", executable_path])
    for input_path in input_paths or []:
        command.extend(["-InputPath", input_path])
    if jsx_path:
        command.extend(["-JsxPath", jsx_path])
    return command


def build_photoshop_cli_command(
    *,
    mode: str = "probe",
    input_paths: list[str] | None = None,
    jsx_path: str | None = None,
    visible: bool = True,
    quit_after: bool = False,
    launch_if_needed: bool = True,
    timeout_sec: int = DEFAULT_PHOTOSHOP_COM_TIMEOUT_SEC,
) -> list[str]:
    command = [
        sys.executable,
        str(photoshop_cli_wrapper_path()),
        "--mode",
        mode,
        "--visible",
        "true" if visible else "false",
        "--quit-after",
        "true" if quit_after else "false",
        "--launch-if-needed",
        "true" if launch_if_needed else "false",
        "--timeout-sec",
        str(int(timeout_sec)),
    ]
    for input_path in input_paths or []:
        command.extend(["--input-path", input_path])
    if jsx_path:
        command.extend(["--jsx-path", jsx_path])
    return command


def _query_registry_app_path(exe_name: str) -> Path | None:
    if winreg is None or os.name != "nt":
        return None
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    for root, base in roots:
        try:
            with winreg.OpenKey(root, fr"{base}\{exe_name}") as key:
                value, _ = winreg.QueryValueEx(key, None)
        except OSError:
            continue
        if value:
            return Path(str(value))
    return None


def _query_uninstall_install_location(display_name_fragment: str) -> Path | None:
    if winreg is None or os.name != "nt":
        return None
    uninstall_roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    needle = display_name_fragment.casefold()
    for root, base in uninstall_roots:
        try:
            with winreg.OpenKey(root, base) as uninstall_key:
                subkey_count, _, _ = winreg.QueryInfoKey(uninstall_key)
                for index in range(subkey_count):
                    try:
                        child_name = winreg.EnumKey(uninstall_key, index)
                        with winreg.OpenKey(uninstall_key, child_name) as child:
                            display_name, _ = winreg.QueryValueEx(child, "DisplayName")
                            if needle not in str(display_name).casefold():
                                continue
                            install_location, _ = winreg.QueryValueEx(child, "InstallLocation")
                            if install_location:
                                return Path(str(install_location))
                    except OSError:
                        continue
        except OSError:
            continue
    return None


def _first_existing_path(candidates: list[Path | None]) -> Path | None:
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


def _discover_tool(display_name_fragment: str, exe_name: str, fallbacks: list[Path]) -> dict[str, Any]:
    app_path = _query_registry_app_path(exe_name)
    install_location = _query_uninstall_install_location(display_name_fragment)
    exe_from_install = install_location / exe_name if install_location else None
    resolved = _first_existing_path([app_path, exe_from_install, *fallbacks])
    install_dir = resolved.parent if resolved else install_location
    return {
        "available": bool(resolved),
        "display_name": display_name_fragment,
        "executable_path": resolved.as_posix() if resolved else "",
        "install_dir": install_dir.as_posix() if install_dir else "",
        "app_path_registry": app_path.as_posix() if app_path else "",
        "install_location_registry": install_location.as_posix() if install_location else "",
    }


def probe_photoshop_com(timeout_sec: int = DEFAULT_PHOTOSHOP_COM_TIMEOUT_SEC) -> dict[str, Any]:
    if os.name != "nt":
        return {"available": False, "version": "", "error": "non-windows"}
    photoshop = _discover_tool(
        "Adobe Photoshop",
        "Photoshop.exe",
        [
            Path(r"C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe"),
            Path(r"E:\Installed Programs\Creative Cloud\Adobe Photoshop 2025\Photoshop.exe"),
        ],
    )
    command = build_photoshop_cli_command(
        mode="probe",
        visible=False,
        quit_after=True,
        launch_if_needed=True,
        timeout_sec=timeout_sec,
    )
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_sec + 15,
        )
    except Exception as exc:  # pragma: no cover
        return {"available": False, "version": "", "error": str(exc)}
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    payload: dict[str, Any] | None = None
    if stdout:
        try:
            payload = json.loads(stdout)
        except Exception:
            payload = None
    if not payload:
        error_bits = [bit for bit in [stdout, stderr] if bit]
        return {
            "available": False,
            "version": "",
            "error": " | ".join(error_bits) if error_bits else "wrapper returned no JSON payload",
        }
    return {
        "available": bool(payload.get("available")),
        "version": str(payload.get("version", "") or ""),
        "error": str(payload.get("error", "") or ""),
    }


def resolve_photoshop_execution(*, probe_com: bool = False) -> dict[str, Any]:
    photoshop = _discover_tool(
        "Adobe Photoshop",
        "Photoshop.exe",
        [
            Path(r"C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe"),
            Path(r"E:\Installed Programs\Creative Cloud\Adobe Photoshop 2025\Photoshop.exe"),
        ],
    )
    com_result = {"available": False, "version": "", "error": ""}
    if probe_com and photoshop["available"]:
        com_result = probe_photoshop_com()
    execution_mode = ""
    if com_result["available"]:
        execution_mode = "com"
    elif photoshop["available"]:
        execution_mode = "exe"
    photoshop.update(
        {
            "com_available": bool(com_result["available"]),
            "com_version": com_result["version"],
            "com_error": com_result["error"],
            "preferred_execution_mode": execution_mode,
            "wrapper_script_path": photoshop_wrapper_path().as_posix(),
        }
    )
    return photoshop


def discover_local_creative_tools(*, probe_photoshop_com: bool = False) -> dict[str, dict[str, Any]]:
    return {
        "photoshop": resolve_photoshop_execution(probe_com=probe_photoshop_com),
        "lightroom": _discover_tool(
            "Lightroom Classic",
            "Lightroom.exe",
            [
                Path(r"C:\Program Files\Adobe\Adobe Lightroom Classic\Lightroom.exe"),
                Path(r"E:\Installed Programs\Creative Cloud\Adobe Lightroom Classic\Lightroom.exe"),
            ],
        ),
        "topaz_photo": _discover_tool(
            "Topaz Photo",
            "Topaz Photo AI.exe",
            [
                Path(r"C:\Program Files\Topaz Labs LLC\Topaz Photo AI\Topaz Photo AI.exe"),
                Path(r"E:\Installed Programs\Topaz Labs LLC\Topaz Photo AI\Topaz Photo AI.exe"),
            ],
        ),
    }
