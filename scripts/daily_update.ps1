param(
    [int]$MaxGamesPerTeam = 3,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonCandidates = @(
    (Join-Path $projectRoot ".venv-vscode\Scripts\python.exe"),
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $projectRoot ".venv\bin\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
    throw "Python was not found in .venv-vscode or .venv. Run scripts/setup_vscode.ps1 first."
}

$forceArg = if ($Force) { @("--force") } else { @() }

function Invoke-ProjectStep {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step '$($Arguments -join ' ')' failed with exit code $LASTEXITCODE."
    }
}

$updateArguments = @("-m", "src.cli", "update-all", "--max-games-per-team", "$MaxGamesPerTeam", "--include-fullstats") + $forceArg
$scheduleArguments = @("-m", "src.cli", "update-schedule") + $forceArg
Invoke-ProjectStep -Arguments $updateArguments
Invoke-ProjectStep -Arguments @("-m", "src.cli", "quality-check")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "eda")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "pandas-eda")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "statistics-report")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "visualize")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "backtest")
Invoke-ProjectStep -Arguments $scheduleArguments
Invoke-ProjectStep -Arguments @("-m", "src.cli", "freshness")
Invoke-ProjectStep -Arguments @("-m", "src.cli", "final-report")
