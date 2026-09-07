param(
    [int]$TeamAId = 2809,
    [int]$TeamBId = 2805
)

# Script này cố ý KHÔNG crawl web. Nó dùng snapshot SQLite đã có để buổi demo
# không phụ thuộc Wi-Fi hoặc thay đổi HTML bất ngờ trên nguồn dữ liệu.
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $projectRoot ".venv-vscode\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv-vscode. Run scripts/setup_vscode.ps1 first."
}

function Invoke-DemoStep {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step '$Name' failed with exit code $LASTEXITCODE."
    }
}

Push-Location $projectRoot
try {
    # Thứ tự dưới đây phản ánh đúng tư duy DA/DS: kiểm tra môi trường và dữ liệu
    # trước, phân tích/visualize sau, rồi mới đánh giá model và đóng gói report.
    Invoke-DemoStep -Name "1. Health check" -Arguments @("-m", "src.cli", "health")
    Invoke-DemoStep -Name "2. Unit tests" -Arguments @("-m", "unittest", "discover", "-s", "tests", "-v")
    Invoke-DemoStep -Name "3. Data quality" -Arguments @("-m", "src.cli", "quality-check")
    Invoke-DemoStep -Name "4. Pandas EDA" -Arguments @("-m", "src.cli", "pandas-eda")
    Invoke-DemoStep -Name "5. Statistical comparison" -Arguments @(
        "-m", "src.cli", "statistics-report", "--team-a-id", "$TeamAId", "--team-b-id", "$TeamBId"
    )
    Invoke-DemoStep -Name "6. Visual comparison" -Arguments @(
        "-m", "src.cli", "visualize", "--team-a-id", "$TeamAId", "--team-b-id", "$TeamBId"
    )
    Invoke-DemoStep -Name "7. Walk-forward backtest" -Arguments @("-m", "src.cli", "backtest")
    Invoke-DemoStep -Name "8. Final handoff report" -Arguments @("-m", "src.cli", "final-report")
}
finally {
    Pop-Location
}

Write-Host "`nOffline demo completed. Open reports/final-project-report.md and reports/figures/." -ForegroundColor Green
