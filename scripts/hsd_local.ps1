param(
    [Parameter(Position = 0)]
    [ValidateSet("doctor", "setup", "test", "run", "dashboard", "clean")]
    [string]$Command = "doctor",

    [ValidateSet("full", "results", "news", "studio", "asset", "review", "scraper")]
    [string]$Mode = "full",

    [switch]$UseNetwork,
    [switch]$NoInstall,
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$PolicyPath = Join-Path $Root "config\hsd_free_source_policy_v1.json"
$script:HsdExitCode = 0

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text =="
}

function Stop-Hsd([string]$Message, [int]$Code = 2) {
    Write-Warning $Message
    $script:HsdExitCode = $Code
    throw [System.OperationCanceledException]::new("__HSD_STOP__")
}

function Test-Python([string]$Exe, [string[]]$PrefixArgs = @()) {
    if ([IO.Path]::IsPathRooted($Exe)) {
        if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { return $null }
    } else {
        $cmd = Get-Command $Exe -ErrorAction SilentlyContinue
        if (-not $cmd -or $cmd.Source -like "*\WindowsApps\python*.exe") { return $null }
    }

    $probe = "import json,sys; print(json.dumps({'executable':sys.executable,'version':'.'.join(str(x) for x in sys.version_info[:3]),'ok':sys.version_info[:2] >= (3, 11)})); raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 9)"
    try {
        $args = @($PrefixArgs) + @("-c", $probe)
        $out = & $Exe @args 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
        $payload = $out | Select-Object -First 1 | ConvertFrom-Json
        if (-not $payload.ok) { return $null }
        return [pscustomobject]@{ Exe = $Exe; PrefixArgs = @($PrefixArgs); Executable = [string]$payload.executable; Version = [string]$payload.version; Display = (($Exe, $PrefixArgs | Where-Object { $_ }) -join " ") }
    } catch {
        return $null
    }
}

function Find-HsdPython {
    $candidates = @()
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) { $candidates += ,@($venvPython, @()) }
    $candidates += ,@("py", @("-3.11"))
    $candidates += ,@("python", @())
    $candidates += ,@("python3", @())
    if ($env:LOCALAPPDATA) {
        $candidates += ,@(Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe", @())
        $candidates += ,@(Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe", @())
    }

    foreach ($candidate in $candidates) {
        $found = Test-Python -Exe $candidate[0] -PrefixArgs @($candidate[1])
        if ($found) { return $found }
    }
    return $null
}

function Invoke-HsdPython($Python, [string[]]$CommandArgs, [switch]$Optional) {
    Write-Host ""
    Write-Host "> $($Python.Display) $($CommandArgs -join ' ')"
    & $Python.Exe @($Python.PrefixArgs) @CommandArgs
    $code = $LASTEXITCODE
    if ($code -ne 0 -and -not $Optional) { throw "Command failed with exit code $code" }
    if ($code -ne 0) { Write-Warning "Optional command failed with exit code $code" }
}

function Set-FreeSourceEnv {
    $env:HSD_FREE_SOURCE_POLICY = $PolicyPath
    $env:HSD_SOURCE_COST_MODE = "free_first"
    $env:HSD_PAID_APIS_DISABLED = "1"
    $env:HSD_GREY_SOURCE_MODE = "review_only"
    $env:HSD_NEWS_ENABLE_FETCH = "true"
    $env:HSD_ASSET_RIGHTS_MODE = "aggressive_public_review"
    $env:HSD_PLAYER_IMAGE_FREE_SEARCH = "1"
    $env:HSD_RESULTS_SOURCE_MODE = "free_public"
    $env:HSD_FINAL_SCORE_STORIES_NETWORK = "1"
    $env:APISPORTS_KEY = ""
    $env:SERPAPI_KEY = ""
    $env:BING_SEARCH_API_KEY = ""
}

function Show-InstallHint {
    Write-Host ""
    Write-Host "Real Python 3.11 was not found."
    Write-Host "Install Python 3.11, reopen the terminal, then run:"
    Write-Host "  .\hsd.cmd setup -UseNetwork"
}

function Invoke-Doctor {
    Write-Section "HSD local doctor"
    Write-Host "Project: $Root"
    Write-Host "Free source policy: $PolicyPath"
    if (Test-Path -LiteralPath $PolicyPath) { Write-Host "Free source policy file: found" } else { Write-Warning "Free source policy file is missing" }

    $python = Find-HsdPython
    if ($python) { Write-Host "Python: $($python.Version) at $($python.Executable)" } else { Write-Warning "Python: not ready"; Show-InstallHint }

    Write-Section "Source posture"
    Write-Host "Mode: free-first"
    Write-Host "Official/free public sources can support publish-ready facts."
    Write-Host "Gray-area and social sources are discovery/review inputs unless operator verified."
    Write-Host "Paid APIs are disabled for local runs."

    Write-Section "Project shape"
    foreach ($item in @("generate_hsd_results_desk_v5.py", "generate_hsd_news_sync_v1.py", "generate_hsd_studio_bridge_v1.py", "generate_hsd_operator_command_center_v2.py", "tests")) {
        if (Test-Path -LiteralPath (Join-Path $Root $item)) { Write-Host "[ok] $item" } else { Write-Warning "[missing] $item" }
    }

    if (Test-Path -LiteralPath (Join-Path $Root ".git")) { Write-Host "Git repo: yes" } else { Write-Warning "Git repo: no .git directory found" }
    $launchWorkflow = Join-Path $Root ".github\workflows\launch-control-v1.yml"
    if (Test-Path -LiteralPath $launchWorkflow) {
        $txt = Get-Content -LiteralPath $launchWorkflow -Raw
        if ($txt -match "(?m)^\s*schedule:" -or $txt -match "(?m)^\s*workflow_run:") { Write-Warning "launch-control-v1.yml still has automatic triggers. Keep local runs manual until this is reviewed." }
    }
}

function Invoke-Setup {
    $python = Find-HsdPython
    if (-not $python) { Show-InstallHint; Stop-Hsd "Python 3.11 is required before setup can continue." }

    Write-Section "Create virtual environment"
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) { Invoke-HsdPython -Python $python -CommandArgs @("-m", "venv", ".venv") } else { Write-Host ".venv already exists" }
    $venv = Test-Python -Exe $venvPython
    if (-not $venv) { throw "Virtual environment was created but did not pass the Python 3.11 check." }
    if ($NoInstall) { Write-Host "Skipping dependency install because -NoInstall was provided."; return }
    if (-not $UseNetwork) { Write-Host "Dependency install uses the public Python package index. Rerun with -UseNetwork to install."; return }

    $pipCache = Join-Path $Root ".pip-cache"
    $tmpDir = Join-Path $Root ".tmp"
    New-Item -ItemType Directory -Path $pipCache,$tmpDir -Force | Out-Null
    $env:PIP_CACHE_DIR = $pipCache
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    $env:TEMP = $tmpDir
    $env:TMP = $tmpDir

    Write-Section "Install dependencies"
    Invoke-HsdPython -Python $venv -CommandArgs @("-m", "pip", "install", "--cache-dir", $pipCache, "--upgrade", "pip")
    foreach ($req in (Get-ChildItem -LiteralPath $Root -Filter "requirements*.txt" -File | Sort-Object Name)) {
        Invoke-HsdPython -Python $venv -CommandArgs @("-m", "pip", "install", "--cache-dir", $pipCache, "-r", $req.FullName)
    }
    $devReq = Join-Path $Root "requirements-dev.txt"
    if (Test-Path -LiteralPath $devReq) { Invoke-HsdPython -Python $venv -CommandArgs @("-m", "pip", "install", "--cache-dir", $pipCache, "-r", $devReq) }
}

function Invoke-ScriptIfPresent($Python, [string]$Path, [switch]$Optional) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $Path))) {
        if ($Optional) { Write-Warning "Optional script missing: $Path"; return }
        throw "Required script missing: $Path"
    }
    Invoke-HsdPython -Python $Python -CommandArgs @($Path) -Optional:$Optional
}

function Invoke-ResultsStage($Python) {
    Write-Section "Results stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_results_desk_v5.py"
    Invoke-ScriptIfPresent $Python "scripts\generate_hsd_expected_games_v5.py" -Optional
    Invoke-ScriptIfPresent $Python "scripts\verify_hsd_wnba_schedule_independent_v5.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_results_desk_v5.py"
}

function Invoke-NewsStage($Python) {
    Write-Section "News stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_news_sync_v1.py"
    Invoke-ScriptIfPresent $Python "generate_news_dashboard_v1.py" -Optional
}

function Invoke-StudioStage($Python) {
    Write-Section "Studio stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_studio_bridge_v1.py"
    Invoke-ScriptIfPresent $Python "generate_hsd_tonight_preview_bridge_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_preview_quality_gate_v1.py" -Optional
}

function Invoke-AssetStage($Python) {
    Write-Section "Asset stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_asset_desk_v1.py"
    Invoke-ScriptIfPresent $Python "generate_hsd_player_image_assets_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_graphics_upload_pack_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_graphics_qa_v1.py" -Optional
}

function Invoke-ReviewStage($Python) {
    Write-Section "Review stage"
    Invoke-ScriptIfPresent $Python "publish_hsd_guard_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_operator_status_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_bebe_daily_ops_plan_v2.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_operator_command_center_v2.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_pipeline_review_lite_v1.py" -Optional
}

function Copy-IfPresent([string]$Relative, [string]$DestinationDir, [System.Collections.ArrayList]$Manifest) {
    $src = Join-Path $Root $Relative
    if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { return }
    $dest = Join-Path $DestinationDir ([IO.Path]::GetFileName($Relative))
    Copy-Item -LiteralPath $src -Destination $dest -Force
    [void]$Manifest.Add([pscustomobject]@{ path = $Relative; included_as = $dest; size = (Get-Item -LiteralPath $src).Length })
}

function Collect-HsdArtifacts {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $outRoot = Join-Path $Root "outputs\local\$stamp"
    $filesDir = Join-Path $outRoot "files"
    New-Item -ItemType Directory -Path $filesDir -Force | Out-Null
    $manifest = New-Object System.Collections.ArrayList
    foreach ($file in @("results_desk_v5_manifest.json", "results_desk_v5_report.md", "source_accuracy_v5.md", "missing_games_alert_v5.md", "top_womens_results.csv", "today_final_results.csv", "news_fact_packets.csv", "news_daily_plan.md", "news_sync_hub.md", "studio_bundle_queue.csv", "studio_bundle_packets.md", "operator_status.md", "operator_status.json", "publish_guard_report.md", "operator_command_center.html", "operator_command_center.md", "bebe_daily_ops_plan.md", "hsd_pipeline_lite_review.zip")) {
        Copy-IfPresent $file $filesDir $manifest
    }
    [pscustomobject]@{ generated_at_local = (Get-Date).ToString("s"); root = $Root.Path; free_source_policy = $PolicyPath; files = $manifest } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outRoot "local_run_manifest.json") -Encoding UTF8
    $latest = Join-Path $Root "outputs\local\latest"
    if (Test-Path -LiteralPath $latest) { Remove-Item -LiteralPath $latest -Recurse -Force }
    Copy-Item -LiteralPath $outRoot -Destination $latest -Recurse -Force
    Write-Host ""
    Write-Host "Collected local artifacts: $outRoot"
}

function Invoke-HsdRun {
    $python = Find-HsdPython
    if (-not $python) { Show-InstallHint; Stop-Hsd "Python 3.11 is required before the HSD pipeline can run." }
    Set-FreeSourceEnv
    Write-Section "Free-first local run"
    Write-Host "Mode: $Mode"
    Write-Host "Python: $($python.Version) at $($python.Executable)"
    Write-Host "Paid API keys are blanked for this process."
    try {
        switch ($Mode) {
            "results" { Invoke-ResultsStage $python }
            "news" { Invoke-NewsStage $python }
            "studio" { Invoke-StudioStage $python }
            "asset" { Invoke-AssetStage $python }
            "review" { Invoke-ReviewStage $python }
            "scraper" { Write-Section "Legacy scraper stage"; Invoke-ScriptIfPresent $python "womens_sports_scraper.py" }
            "full" { Invoke-ResultsStage $python; Invoke-NewsStage $python; Invoke-StudioStage $python; Invoke-ReviewStage $python }
        }
    } catch {
        if (-not $ContinueOnError) { throw }
        Write-Warning $_.Exception.Message
    } finally {
        Collect-HsdArtifacts
    }
}

function Open-Dashboard {
    $latest = Join-Path $Root "outputs\local\latest\files\operator_command_center.html"
    $html = Join-Path $Root "operator_command_center.html"
    if (Test-Path -LiteralPath $latest) { Start-Process $latest; return }
    if (Test-Path -LiteralPath $html) { Start-Process $html; return }
    Write-Host "No operator dashboard found yet. Run: .\hsd.cmd run -Mode review"
}

function Invoke-Clean {
    Write-Section "Clean local-only outputs"
    foreach ($path in @("outputs\local", ".pytest_cache")) {
        $full = Join-Path $Root $path
        if (Test-Path -LiteralPath $full) { Remove-Item -LiteralPath $full -Recurse -Force; Write-Host "Removed $path" }
    }
    Get-ChildItem -LiteralPath $Root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
}

Push-Location $Root
try {
    switch ($Command) {
        "doctor" { Invoke-Doctor }
        "setup" { Invoke-Setup }
        "test" { $python = Find-HsdPython; if (-not $python) { Show-InstallHint; Stop-Hsd "Python 3.11 is required before tests can run." }; Set-FreeSourceEnv; Invoke-HsdPython -Python $python -CommandArgs @("-m", "pytest", "-q") }
        "run" { Invoke-HsdRun }
        "dashboard" { Open-Dashboard }
        "clean" { Invoke-Clean }
    }
} catch [System.OperationCanceledException] {
    if ($_.Exception.Message -ne "__HSD_STOP__") { $script:HsdExitCode = 1; Write-Error $_.Exception.Message -ErrorAction Continue }
} catch {
    $script:HsdExitCode = 1
    Write-Error $_.Exception.Message -ErrorAction Continue
} finally {
    Pop-Location
}

exit $script:HsdExitCode
