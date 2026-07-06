param(
    [ValidateSet("probe", "open", "jsx")]
    [string]$Mode = "probe",
    [string[]]$InputPath = @(),
    [string]$JsxPath = "",
    [string]$Visible = "true",
    [string]$QuitAfter = "false",
    [string]$LaunchIfNeeded = "true",
    [int]$TimeoutSec = 75,
    [string]$ExecutablePath = ""
)

$ErrorActionPreference = "Stop"

function ConvertTo-Bool {
    param(
        [string]$Value,
        [bool]$DefaultValue = $false
    )
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $DefaultValue
    }
    switch -Regex ($Value.Trim().ToLowerInvariant()) {
        "^(1|true|yes|y|on)$" { return $true }
        "^(0|false|no|n|off)$" { return $false }
        default { return $DefaultValue }
    }
}

function Resolve-StrictPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        throw "Path value is required."
    }
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Try-GetPhotoshopApplication {
    try {
        $app = New-Object -ComObject Photoshop.Application
        return @{
            app = $app
            connected_via = "com_create"
            launched = $false
        }
    }
    catch {
        return @{
            app = $null
            connected_via = ""
            launched = $false
            error = $_.Exception.Message
        }
    }
}

function Connect-PhotoshopApplication {
    param(
        [bool]$LaunchIfNeededFlag,
        [int]$TimeoutSecValue,
        [string]$ExecutablePathValue
    )

    $firstAttempt = Try-GetPhotoshopApplication
    if ($firstAttempt.app) {
        return $firstAttempt
    }

    if (-not $LaunchIfNeededFlag) {
        throw $firstAttempt.error
    }

    if ([string]::IsNullOrWhiteSpace($ExecutablePathValue)) {
        throw ("Initial COM activation failed and no executable path was supplied. " + $firstAttempt.error)
    }

    $resolvedExecutable = Resolve-StrictPath $ExecutablePathValue
    Start-Process -FilePath $resolvedExecutable | Out-Null

    $deadline = (Get-Date).AddSeconds([Math]::Max($TimeoutSecValue, 5))
    $lastError = $firstAttempt.error

    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 1500
        $attempt = Try-GetPhotoshopApplication
        if ($attempt.app) {
            $attempt.connected_via = "launch_then_com_create"
            $attempt.launched = $true
            return $attempt
        }
        if ($attempt.error) {
            $lastError = $attempt.error
        }
    }

    throw ("Photoshop COM connection did not become available after launch within $TimeoutSecValue seconds. Last error: $lastError")
}

$app = $null
$openedPaths = @()
$resolvedJsxPath = ""
$connectedVia = ""
$launchedByWrapper = $false
$visibleFlag = ConvertTo-Bool -Value $Visible -DefaultValue $true
$quitAfterFlag = ConvertTo-Bool -Value $QuitAfter -DefaultValue $false
$launchIfNeededFlag = ConvertTo-Bool -Value $LaunchIfNeeded -DefaultValue $true

try {
    $connection = Connect-PhotoshopApplication -LaunchIfNeededFlag $launchIfNeededFlag -TimeoutSecValue $TimeoutSec -ExecutablePathValue $ExecutablePath
    $app = $connection.app
    $connectedVia = $connection.connected_via
    $launchedByWrapper = [bool]$connection.launched

    $app.Visible = $visibleFlag
    $app.DisplayDialogs = 3

    foreach ($item in $InputPath) {
        $resolvedInput = Resolve-StrictPath $item
        $null = $app.Open($resolvedInput)
        $openedPaths += $resolvedInput
    }

    if ($Mode -eq "jsx") {
        $resolvedJsxPath = Resolve-StrictPath $JsxPath
        $null = $app.DoJavaScriptFile($resolvedJsxPath)
    }

    $result = [ordered]@{
        mode = $Mode
        available = $true
        version = "$($app.Version)"
        visible = [bool]$app.Visible
        connected_via = $connectedVia
        launched_by_wrapper = $launchedByWrapper
        opened_paths = $openedPaths
        jsx_path = $resolvedJsxPath
        quit_after = [bool]$quitAfterFlag
    }

    $result | ConvertTo-Json -Depth 5
}
catch {
    $result = [ordered]@{
        mode = $Mode
        available = $false
        error = $_.Exception.Message
        connected_via = $connectedVia
        launched_by_wrapper = $launchedByWrapper
        opened_paths = $openedPaths
        jsx_path = $resolvedJsxPath
        quit_after = [bool]$quitAfterFlag
    }
    $result | ConvertTo-Json -Depth 5
    exit 1
}
finally {
    if ($app -and (($Mode -eq "probe" -and $launchedByWrapper) -or $quitAfterFlag)) {
        try {
            $app.Quit()
        }
        catch {
        }
    }
}
