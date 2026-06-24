param(
    [Parameter(Position = 0)]
    [ValidateSet("doctor", "setup", "test", "run", "dashboard", "clean")]
    [string]$Command = "doctor",

    [ValidateSet("full", "results", "news", "studio", "asset", "stories", "handoff", "posts", "launch", "dashboards", "review")]
    [string]$Mode = "full",

    [switch]$UseNetwork,
    [switch]$NoInstall,
    [switch]$ContinueOnError,
    [switch]$KeepGeneratedState
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$PolicyPath = Join-Path $Root "config\hsd_free_source_policy_v1.json"
$script:HsdExitCode = 0
$GeneratedStatePathspecs = @(
    "hsd_pipeline_lite_review/**",
    "hsd_pipeline_lite_review.zip",
    "outputs/latest/**",
    "dashboard/**",
    "results_dashboard/**",
    "studio_dashboard/**",
    "news_dashboard/**",
    "run_history/**",
    "results_run_history/**",
    "launch_run_history/**",
    "launch_dashboard/**",
    "launch_analytics_dashboard/**",
    "asset_run_history/**",
    "generated_graphics/**",
    "graphics_chat_upload_pack/**",
    "graphics_chat_upload_pack_zips/**",
    "graphics_clean_prompts/**",
    "manual_workflow_packets/**",
    "manual_workflow_handoff_packs/**",
    "ig_story_results_upload_pack/**",
    "ig_story_results_upload_pack_zips/**",
    "mermaid_compiled_packets/**",
    "assignment_handoff_packets/**",
    "assignment_handoff_zips/**",
    "mermaid_assignment_compiled_packets/**",
    "mermaid_assignment_final_packets/**",
    "mermaid_director_compiled_packets/**",
    "mermaid_quality_compiled_packets/**",
    "mermaid_quality_compiled_packets_v2_2/**",
    "rendered_handoff_graphics/**",
    "rendered_handoff_zips/**",
    "runs/**",
    "operator/inbox/**",
    "assets/leagues/wnba/athletes/*/headshot.png",
    "assets/leagues/wnba/athletes/*/headshot.png.approved",
    "assets/leagues/wnba/teams/*/logo.png",
    "data/asset_registry/wnba/*",
    "approved_graphics_assets.*",
    "asset_candidates_review.md",
    "assignment_*",
    "bebe_*",
    "breaking_news_queue*.csv",
    "caption_bank.md",
    "content_director_*",
    "contract_validation_*",
    "daily_results_recommendations.md",
    "daily_slate_*",
    "dirty_tree_v1.*",
    "discovery_sources_report.md",
    "duplicate_game_audit_v5.csv",
    "expected_games_v5_manifest.json",
    "expected_games_v5_report.md",
    "final_score_story_guard_report.*",
    "first_comment_hooks.md",
    "generated_output_pollution_v1.*",
    "graphics_*",
    "ig_feed_*",
    "ig_story_*",
    "independent_schedule_verification_v5.*",
    "install_report.*",
    "latest_news_sync_run_summary.md",
    "launch_*",
    "legacy_dashboard_replacement.*",
    "manual_story_inbox_report.md",
    "manual_workflow_*",
    "mermaid_*",
    "missing_games_alert_v5.*",
    "multi_post_daily_board.*",
    "multisport_*",
    "news_brief_queue.md",
    "news_candidate_queue.csv",
    "news_daily_plan.md",
    "news_fact_packets.csv",
    "news_graphics_handoff.md",
    "news_input_status_report.csv",
    "news_manual_review_queue.csv",
    "news_social_packets.md",
    "news_source_observations.csv",
    "news_sync_manifest.json",
    "news_sync_hub.md",
    "official_player_headshot_*",
    "operator_*",
    "operator_command_center.*",
    "phase2_closure_v1.*",
    "phase2g_install_report.*",
    "pipeline_stop_reason.md",
    "player_asset_*",
    "player_assets.*",
    "player_image_*",
    "player_image_fit_manifest.json",
    "player_registry_*",
    "post_slot_status.csv",
    "preview_bundle_quality.*",
    "preview_player_focus.csv",
    "publish_guard_report.*",
    "reconciled_events.csv",
    "render_integrity_report.md",
    "rendered_handoff_*",
    "rendered_slide_qa.*",
    "repo_state_v3.*",
    "results_contract_v2.*",
    "results_contract_report.md",
    "results_desk_v5_manifest.json",
    "results_desk_v5_report.md",
    "results_graphics_queue.md",
    "results_system_hub.md",
    "rumor_watch_queue*.csv",
    "run_manifest.json",
    "social_rumor_*",
    "source_accuracy_v5.*",
    "source_health_report.csv",
    "source_observations.csv",
    "source_registry_audit.*",
    "stale_source_audit_v5.csv",
    "story_candidates_*",
    "config/hsd_expected_games_v5.csv",
    "studio_accuracy_checklist.csv",
    "studio_brand_config.json",
    "studio_bundle_*",
    "studio_caption_bank.md",
    "studio_command_center.md",
    "studio_fresh_packet_gate.csv",
    "studio_fresh_packet_report.md",
    "studio_freshness_*",
    "studio_graphics_*",
    "studio_image_prompts.md",
    "studio_manifest.json",
    "studio_manual_review_graphics.csv",
    "studio_post_schedule.md",
    "studio_preview_*",
    "studio_render_manifest_v2.json",
    "studio_top_graphic_packets.md",
    "studio_visual_upgrade_v2.md",
    "threads_*",
    "today_final_results.csv",
    "today_results_board.csv",
    "today_womens_results.csv",
    "top_womens_results.csv",
    "v4_source_truth_guard.*",
    "wnba_box_score_audit.csv",
    "wnba_box_score_summary.md"
)

function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host "== $Text =="
}

function Resolve-HsdChildPath([string]$Base, [string]$Relative) {
    $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\', '/')
    $candidate = [IO.Path]::GetFullPath((Join-Path $baseFull $Relative))
    $prefix = $baseFull + [IO.Path]::DirectorySeparatorChar
    if ($candidate -ne $baseFull -and -not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside target folder: $Relative"
    }
    return $candidate
}

function New-HsdRunContext {
    $baseStamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stamp = $baseStamp
    $index = 1
    $outRoot = Join-Path $Root "outputs\local\$stamp"
    while (Test-Path -LiteralPath $outRoot) {
        $index += 1
        $stamp = "$baseStamp-$index"
        $outRoot = Join-Path $Root "outputs\local\$stamp"
    }
    $filesDir = Join-Path $outRoot "files"
    $generatedStateDir = Join-Path $outRoot "generated_state"
    New-Item -ItemType Directory -Path $filesDir,$generatedStateDir -Force | Out-Null
    return [pscustomobject]@{
        Id = $stamp
        OutRoot = $outRoot
        FilesDir = $filesDir
        GeneratedStateDir = $generatedStateDir
        GeneratedStateManifest = (Join-Path $outRoot "generated_state_manifest.json")
        LocalRunManifest = (Join-Path $outRoot "local_run_manifest.json")
    }
}

function Stop-Hsd([string]$Message, [int]$Code = 2) {
    Write-Warning $Message
    $script:HsdExitCode = $Code
    throw [System.OperationCanceledException]::new("__HSD_STOP__")
}

function New-PythonCandidate([string]$Exe, [string[]]$PrefixArgs = @()) {
    return [pscustomobject]@{
        Exe = $Exe
        PrefixArgs = $PrefixArgs
    }
}

function Test-Python($Candidate) {
    if (-not $Candidate -or -not $Candidate.Exe) {
        return $null
    }

    $exe = [string]$Candidate.Exe
    $prefix = @($Candidate.PrefixArgs)

    if ([IO.Path]::IsPathRooted($exe)) {
        if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { return $null }
    } else {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if (-not $cmd -or $cmd.Source -like "*\WindowsApps\python*.exe") { return $null }
    }

    $probe = "import json,sys; print(json.dumps({'executable':sys.executable,'version':'.'.join(str(x) for x in sys.version_info[:3]),'ok':sys.version_info[:2] >= (3, 11)})); raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 9)"
    try {
        $args = @()
        $args += $prefix
        $args += "-c"
        $args += $probe
        $out = & $exe @args 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
        $payload = $out | Select-Object -First 1 | ConvertFrom-Json
        if (-not $payload.ok) { return $null }
        return [pscustomobject]@{
            Exe = $exe
            PrefixArgs = $prefix
            Executable = [string]$payload.executable
            Version = [string]$payload.version
            Display = (($exe, $prefix | Where-Object { $_ }) -join " ")
        }
    } catch {
        return $null
    }
}

function Find-HsdPython {
    $candidates = @()
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) { $candidates += New-PythonCandidate -Exe $venvPython }
    $candidates += New-PythonCandidate -Exe "py" -PrefixArgs @("-3.11")
    $candidates += New-PythonCandidate -Exe "python"
    $candidates += New-PythonCandidate -Exe "python3"
    if ($env:LOCALAPPDATA) {
        $candidates += New-PythonCandidate -Exe (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe")
        $candidates += New-PythonCandidate -Exe (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe")
    }

    foreach ($candidate in $candidates) {
        $found = Test-Python $candidate
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

function Set-RunScopedEnv($RunContext) {
    $env:HSD_LOCAL_RUN_ID = $RunContext.Id
    $env:HSD_LOCAL_RUN_ROOT = $RunContext.OutRoot
    $env:HSD_RUN_OUTPUT_DIR = $RunContext.FilesDir
    $env:HSD_GENERATED_STATE_DIR = $RunContext.GeneratedStateDir
    $env:HSD_OUTPUT_MODE = "run_scoped_local"
}

function Test-GitAvailable {
    if (-not (Test-Path -LiteralPath (Join-Path $Root ".git"))) { return $false }
    return [bool](Get-Command git -ErrorAction SilentlyContinue)
}

function Invoke-GitList([string[]]$GitArgs) {
    if (-not (Test-GitAvailable)) { return @() }
    try {
        $out = @(& git @GitArgs 2>$null)
        if ($LASTEXITCODE -ne 0) { return @() }
        return @($out | Where-Object { $_ })
    } catch {
        return @()
    }
}

function Get-GeneratedGitState {
    if (-not (Test-GitAvailable)) {
        return [pscustomobject]@{ enabled = $false; tracked_dirty = @(); untracked = @() }
    }

    $trackedArgs = @("diff", "--name-only", "--") + $GeneratedStatePathspecs
    $untrackedArgs = @("ls-files", "--others", "--exclude-standard", "--") + $GeneratedStatePathspecs
    $ignoredArgs = @("ls-files", "--others", "--ignored", "--exclude-standard", "--") + $GeneratedStatePathspecs
    $untracked = @((Invoke-GitList $untrackedArgs) + (Invoke-GitList $ignoredArgs) | Sort-Object -Unique)
    return [pscustomobject]@{
        enabled = $true
        tracked_dirty = @(Invoke-GitList $trackedArgs)
        untracked = $untracked
    }
}

function Remove-GeneratedUntrackedFiles([string[]]$Paths) {
    if (-not $Paths -or $Paths.Count -eq 0) { return 0 }

    $rootFull = [IO.Path]::GetFullPath($Root.Path).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $rootPrefix = $rootFull + [IO.Path]::DirectorySeparatorChar
    $removed = 0
    foreach ($rel in $Paths) {
        if (-not $rel) { continue }
        $full = [IO.Path]::GetFullPath((Join-Path $Root $rel))
        if (-not $full.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            Write-Warning "Skipping generated path outside repo: $rel"
            continue
        }
        if (Test-Path -LiteralPath $full -PathType Leaf) {
            Remove-Item -LiteralPath $full -Force
            $removed += 1
        }
    }
    return $removed
}

function Restore-GeneratedGitState($Baseline) {
    if ($KeepGeneratedState -or -not $Baseline -or -not $Baseline.enabled) { return }

    $current = Get-GeneratedGitState
    if (-not $current.enabled) { return }

    $trackedToRestore = @($current.tracked_dirty | Where-Object { $Baseline.tracked_dirty -notcontains $_ })
    $untrackedToRemove = @($current.untracked | Where-Object { $Baseline.untracked -notcontains $_ })

    if ($trackedToRestore.Count -gt 0) {
        $restoreArgs = @("restore", "--") + $trackedToRestore
        & git @restoreArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Generated-state quarantine could not restore tracked generated files."
        }
    }

    $removed = Remove-GeneratedUntrackedFiles $untrackedToRemove
    if ($trackedToRestore.Count -gt 0 -or $removed -gt 0) {
        Write-Section "Generated-state quarantine"
        Write-Host "Restored tracked generated files: $($trackedToRestore.Count)"
        Write-Host "Removed untracked generated files: $removed"
        Write-Host "Use -KeepGeneratedState when you intentionally want to review generated asset or registry file changes in Git."
    }
}

function Copy-HsdGeneratedRunState($RunContext, $Baseline) {
    $rows = New-Object System.Collections.ArrayList
    if (-not $Baseline -or -not $Baseline.enabled) {
        [pscustomobject]@{
            version = "hsd-local-generated-state-v1"
            run_id = $RunContext.Id
            generated_at_local = (Get-Date).ToString("s")
            enabled = $false
            root_cleanup = "disabled_no_git"
            files = $rows
        } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $RunContext.GeneratedStateManifest -Encoding UTF8
        return
    }

    $current = Get-GeneratedGitState
    $trackedToArchive = @($current.tracked_dirty | Where-Object { $Baseline.tracked_dirty -notcontains $_ })
    $untrackedToArchive = @($current.untracked | Where-Object { $Baseline.untracked -notcontains $_ })
    $byPath = @{}
    foreach ($path in $trackedToArchive) {
        if ($path) { $byPath[$path] = "tracked_modified_generated" }
    }
    foreach ($path in $untrackedToArchive) {
        if ($path -and -not $byPath.ContainsKey($path)) { $byPath[$path] = "untracked_generated" }
    }

    foreach ($path in ($byPath.Keys | Sort-Object)) {
        $normalized = ($path -replace "\\", "/").TrimStart("/")
        if (-not $normalized -or $normalized.StartsWith("outputs/local/", [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $src = Resolve-HsdChildPath $Root.Path $normalized
        $dest = Resolve-HsdChildPath $RunContext.GeneratedStateDir $normalized
        $destParent = Split-Path -Parent $dest
        if ($destParent) { New-Item -ItemType Directory -Path $destParent -Force | Out-Null }

        $action = "missing_at_archive_time"
        $size = 0
        $archivedAs = ""
        if (Test-Path -LiteralPath $src -PathType Leaf) {
            Copy-Item -LiteralPath $src -Destination $dest -Force
            $item = Get-Item -LiteralPath $src
            $size = $item.Length
            $action = "copied_file"
            $archivedAs = "generated_state/$normalized"
        } elseif (Test-Path -LiteralPath $src -PathType Container) {
            Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
            $action = "copied_directory"
            $archivedAs = "generated_state/$normalized"
        }

        [void]$rows.Add([pscustomobject]@{
            path = $normalized
            state = $byPath[$path]
            action = $action
            archived_as = $archivedAs
            size = $size
        })
    }

    $archivedCount = @($rows | Where-Object { $_.action -like "copied*" }).Count
    [pscustomobject]@{
        version = "hsd-local-generated-state-v1"
        run_id = $RunContext.Id
        generated_at_local = (Get-Date).ToString("s")
        enabled = $true
        keep_generated_state = [bool]$KeepGeneratedState
        root_cleanup = $(if ($KeepGeneratedState) { "skipped_keep_generated_state" } else { "restore_after_archive" })
        tracked_modified_count = $trackedToArchive.Count
        untracked_generated_count = $untrackedToArchive.Count
        archived_count = $archivedCount
        generated_state_dir = $RunContext.GeneratedStateDir
        files = $rows
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $RunContext.GeneratedStateManifest -Encoding UTF8

    Write-Section "Run-scoped generated outputs"
    Write-Host "Archived generated root changes: $archivedCount"
    Write-Host "Generated state folder: $($RunContext.GeneratedStateDir)"
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
    $venv = Test-Python (New-PythonCandidate -Exe $venvPython)
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

function Invoke-HandoffStage($Python) {
    Write-Section "Manual handoff stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_manual_workflow_merge_v1.py" -Optional
}

function Invoke-StoriesStage($Python) {
    Write-Section "Final score stories stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_final_score_stories_v1.py" -Optional
}

function Invoke-PostsStage($Python) {
    Write-Section "Multi-post desk stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_multi_post_desk_v1.py" -Optional
}

function Invoke-LaunchStage($Python) {
    Write-Section "Launch control stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_launch_control_v1.py" -Optional
}

function Invoke-DrilldownDashboardsStage($Python) {
    Write-Section "Drill-down dashboards stage"
    Invoke-ScriptIfPresent $Python "generate_results_dashboard_v4.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_studio_dashboard_v1.py" -Optional
}

function Invoke-ReviewStage($Python) {
    Write-Section "Review stage"
    Invoke-ScriptIfPresent $Python "generate_hsd_source_registry_audit_v2.py" -Optional
    Invoke-ScriptIfPresent $Python "publish_hsd_guard_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_operator_status_v1.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_bebe_daily_ops_plan_v2.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_operator_command_center_v2.py" -Optional
    Invoke-ScriptIfPresent $Python "generate_hsd_pipeline_review_lite_v1.py" -Optional
}

function Resolve-HsdArtifactSource([string]$Relative, [string]$RunFilesDir) {
    $candidates = @()
    if ($env:HSD_RUN_OUTPUT_DIR) {
        $candidates += Resolve-HsdChildPath $env:HSD_RUN_OUTPUT_DIR $Relative
    }
    if ($RunFilesDir -and $RunFilesDir -ne $env:HSD_RUN_OUTPUT_DIR) {
        $candidates += Resolve-HsdChildPath $RunFilesDir $Relative
    }
    $candidates += Resolve-HsdChildPath $Root.Path $Relative

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

function Copy-IfPresent([string]$Relative, [string]$DestinationDir, [System.Collections.ArrayList]$Manifest) {
    $src = Resolve-HsdArtifactSource $Relative $DestinationDir
    if (-not $src) { return }
    $dest = Resolve-HsdChildPath $DestinationDir $Relative
    $destParent = Split-Path -Parent $dest
    if ($destParent) { New-Item -ItemType Directory -Path $destParent -Force | Out-Null }
    $srcFull = [IO.Path]::GetFullPath($src)
    $destFull = [IO.Path]::GetFullPath($dest)
    if (-not $srcFull.Equals($destFull, [StringComparison]::OrdinalIgnoreCase)) {
        Copy-Item -LiteralPath $src -Destination $dest -Force
    }
    [void]$Manifest.Add([pscustomobject]@{ path = $Relative; source = $src; included_as = $dest; size = (Get-Item -LiteralPath $src).Length })
}

function Collect-HsdArtifacts($RunContext) {
    $outRoot = $RunContext.OutRoot
    $filesDir = $RunContext.FilesDir
    New-Item -ItemType Directory -Path $filesDir -Force | Out-Null
    $manifest = New-Object System.Collections.ArrayList
    $reviewFiles = @(
        "results_desk_v5_manifest.json",
        "results_desk_v5_report.md",
        "source_accuracy_v5.md",
        "missing_games_alert_v5.md",
        "source_registry_audit.csv",
        "source_registry_audit.md",
        "source_registry_audit.json",
        "top_womens_results.csv",
        "today_final_results.csv",
        "results_dashboard/index.html",
        "news_fact_packets.csv",
        "news_daily_plan.md",
        "news_sync_hub.md",
        "studio_bundle_queue.csv",
        "studio_bundle_packets.md",
        "studio_dashboard/index.html",
        "preview_bundle_quality.csv",
        "preview_bundle_quality.md",
        "preview_bundle_quality_summary.csv",
        "preview_player_focus.csv",
        "operator_status.md",
        "operator_status.json",
        "publish_guard_report.md",
        "publish_guard_report.json",
        "operator_command_center.html",
        "operator_command_center.md",
        "operator_command_center.json",
        "bebe_daily_ops_plan.md",
        "bebe_posting_schedule_today.md",
        "manual_workflow_handoff.md",
        "manual_workflow_pack_status.csv",
        "ig_story_results_queue.csv",
        "ig_story_results_upload_pack_status.csv",
        "final_score_story_guard_report.md",
        "multi_post_daily_board.md",
        "multi_post_daily_board.json",
        "post_slot_status.csv",
        "ig_feed_queue.csv",
        "ig_story_queue.csv",
        "threads_queue.csv",
        "caption_bank.md",
        "first_comment_hooks.md",
        "launch_command_center.md",
        "launch_daily_runbook.md",
        "launch_graphics_chat_brief.md",
        "launch_instagram_publish_queue.csv",
        "launch_caption_drafts.md",
        "launch_story_plan.md",
        "launch_quality_gate.csv",
        "launch_daily_operator_checklist.md",
        "launch_post_publish_tracker.csv",
        "launch_metrics_manual_input.csv",
        "launch_7_day_performance_dashboard.md",
        "launch_what_to_double_down_on.md",
        "launch_manifest.json",
        "hsd_pipeline_lite_review.zip"
    )
    foreach ($file in $reviewFiles) {
        Copy-IfPresent $file $filesDir $manifest
    }
    [pscustomobject]@{
        version = "hsd-local-run-manifest-v2"
        run_id = $RunContext.Id
        generated_at_local = (Get-Date).ToString("s")
        root = $Root.Path
        output_root = $RunContext.OutRoot
        files_dir = $RunContext.FilesDir
        generated_state_dir = $RunContext.GeneratedStateDir
        generated_state_manifest = $RunContext.GeneratedStateManifest
        output_mode = "run_scoped_local"
        free_source_policy = $PolicyPath
        manual_only = $true
        paid_apis_disabled = $true
        files = $manifest
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $RunContext.LocalRunManifest -Encoding UTF8
    $latest = Join-Path $Root "outputs\local\latest"
    if (Test-Path -LiteralPath $latest) { Remove-Item -LiteralPath $latest -Recurse -Force }
    Copy-Item -LiteralPath $outRoot -Destination $latest -Recurse -Force
    Write-Host ""
    Write-Host "Collected local artifacts: $outRoot"
}

function Invoke-HsdRun {
    $python = Find-HsdPython
    if (-not $python) { Show-InstallHint; Stop-Hsd "Python 3.11 is required before the HSD pipeline can run." }
    $runContext = New-HsdRunContext
    $generatedBaseline = Get-GeneratedGitState
    Set-FreeSourceEnv
    Set-RunScopedEnv $runContext
    Write-Section "Free-first local run"
    Write-Host "Mode: $Mode"
    Write-Host "Python: $($python.Version) at $($python.Executable)"
    Write-Host "Run output: $($runContext.OutRoot)"
    Write-Host "Paid API keys are blanked for this process."
    try {
        switch ($Mode) {
            "results" { Invoke-ResultsStage $python }
            "news" { Invoke-NewsStage $python }
            "studio" { Invoke-StudioStage $python }
            "asset" { Invoke-AssetStage $python }
            "stories" { Invoke-StoriesStage $python; Invoke-ReviewStage $python }
            "handoff" { Invoke-HandoffStage $python; Invoke-ReviewStage $python }
            "posts" { Invoke-PostsStage $python; Invoke-ReviewStage $python }
            "launch" { Invoke-LaunchStage $python; Invoke-ReviewStage $python }
            "dashboards" { Invoke-DrilldownDashboardsStage $python; Invoke-ReviewStage $python }
            "review" { Invoke-ReviewStage $python }
            "full" { Invoke-ResultsStage $python; Invoke-NewsStage $python; Invoke-StudioStage $python; Invoke-ReviewStage $python }
        }
    } catch {
        if (-not $ContinueOnError) { throw }
        Write-Warning $_.Exception.Message
    } finally {
        Copy-HsdGeneratedRunState $runContext $generatedBaseline
        Collect-HsdArtifacts $runContext
        Restore-GeneratedGitState $generatedBaseline
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
