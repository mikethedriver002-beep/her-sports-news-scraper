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

$script = Join-Path $PSScriptRoot "scripts\hsd_local.ps1"
if (-not (Test-Path -LiteralPath $script)) {
    throw "Missing local runner: $script"
}

& $script -Command $Command -Mode $Mode -UseNetwork:$UseNetwork -NoInstall:$NoInstall -ContinueOnError:$ContinueOnError
exit $LASTEXITCODE
