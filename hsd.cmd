@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0hsd.ps1" %*
set "HSD_EXIT_CODE=%ERRORLEVEL%"
exit /b %HSD_EXIT_CODE%
