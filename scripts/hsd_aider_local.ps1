param(
    [string]$Model = $env:HSD_AIDER_MODEL,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AiderArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Model)) {
    $Model = "ollama/qwen2.5-coder:7b"
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

function Resolve-Executable {
    param(
        [string]$Name,
        [string[]]$Fallbacks
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    foreach ($candidate in $Fallbacks) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Could not find $Name. Install it first, then rerun this launcher."
}

$Aider = Resolve-Executable "aider" @(
    (Join-Path $env:USERPROFILE ".local\bin\aider.exe")
)

$Ollama = Resolve-Executable "ollama" @(
    (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
    (Join-Path $env:ProgramFiles "Ollama\ollama.exe")
)

if ($Model.StartsWith("ollama/")) {
    $ollamaModel = $Model.Substring("ollama/".Length)
    $models = & $Ollama list
    if (($models -join "`n") -notmatch [regex]::Escape($ollamaModel)) {
        Write-Host "Missing Ollama model: $ollamaModel" -ForegroundColor Yellow
        Write-Host "Install it with: `"$Ollama`" pull $ollamaModel" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "HSD local Aider session" -ForegroundColor Cyan
Write-Host "Model: $Model"
Write-Host "Guardrails: no paid APIs, no auto-downloads, no auto-approval, no publish-ready movement, no publishing."
Write-Host "Aider is launched with --no-auto-commits and --no-watch-files."

$baseArgs = @(
    "--model", $Model,
    "--no-auto-commits",
    "--no-watch-files",
    "--read", "AGENTS.md",
    "--read", "docs\HSD_DETERMINISTIC_GUARDRAILS.md",
    "--read", "docs\HSD_AIDER_LOCAL_LLM.md"
)

$finalArgs = @()
$finalArgs += $baseArgs
if ($AiderArgs) {
    $finalArgs += $AiderArgs
}

& $Aider @finalArgs
