Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "==> $Label"
    & $Action
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host "Step failed: $Label"
        Write-Host "Exit code: $exitCode"
        exit $exitCode
    }
}

$currentRoot = [System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\', '/')
$gitRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
    Write-Host "Failed to determine the repository root with git."
    exit 1
}

$gitRoot = [System.IO.Path]::GetFullPath($gitRoot.Trim()).TrimEnd('\', '/')
if ($currentRoot -ne $gitRoot) {
    Write-Host "This script must be run from the repository root."
    Write-Host "Current location: $currentRoot"
    Write-Host "Repository root:  $gitRoot"
    exit 1
}

$pythonExe = Join-Path $currentRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    Write-Host "Missing Python executable: $pythonExe"
    exit 1
}

Invoke-Step -Label 'py_compile generate_hsd_operator_command_center_v2.py' -Action {
    & $pythonExe -m py_compile .\generate_hsd_operator_command_center_v2.py
}

Invoke-Step -Label 'generate_hsd_operator_command_center_v2.py' -Action {
    & $pythonExe .\generate_hsd_operator_command_center_v2.py
}

Invoke-Step -Label 'pytest tests/test_operator_command_center_v3.py -q' -Action {
    & $pythonExe -m pytest tests\test_operator_command_center_v3.py -q
}

Invoke-Step -Label 'pytest tests/test_guardrail_check.py tests/test_no_paid_sources.py -q' -Action {
    & $pythonExe -m pytest tests\test_guardrail_check.py tests\test_no_paid_sources.py -q
}

Invoke-Step -Label 'scripts/guardrail_check.py --base HEAD~1 --format markdown' -Action {
    & $pythonExe .\scripts\guardrail_check.py --base HEAD~1 --format markdown
}

Invoke-Step -Label 'scripts/guardrail_check.py --scan-dir outputs/local/latest/files --format json' -Action {
    & $pythonExe .\scripts\guardrail_check.py --scan-dir outputs\local\latest\files --format json
}

Write-Host '==> git status --short --branch'
$gitStatus = & git status --short --branch 2>&1
$statusExitCode = $LASTEXITCODE
if ($statusExitCode -ne 0) {
    Write-Host 'Step failed: git status --short --branch'
    Write-Host "Exit code: $statusExitCode"
    exit $statusExitCode
}

foreach ($line in @($gitStatus)) {
    Write-Host $line
}

Write-Host 'checks passed'
if (@($gitStatus).Count -gt 1) {
    Write-Host 'Workspace has uncommitted or untracked files; review before committing.'
} else {
    Write-Host 'Workspace is clean after checks.'
}
