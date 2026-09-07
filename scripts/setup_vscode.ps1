param(
    [string]$EnvironmentName = ".venv-vscode"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentPath = Join-Path $projectRoot $EnvironmentName

# Prefer the official Windows Python launcher. The existing MSYS Python can
# run the scraper, but PyPI does not provide all scientific wheels for it.
$pythonCommand = $null
try {
    & py -3.12 -c "import sys; print(sys.executable)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = @("py", "-3.12")
    }
} catch {
    $pythonCommand = $null
}

if (-not $pythonCommand) {
    throw @"
Không tìm thấy Windows CPython 3.12.
Hãy cài Python 3.12 x64 từ python.org, chọn 'Add python.exe to PATH',
mở lại VS Code rồi chạy lại scripts/setup_vscode.ps1.
Không dùng C:\msys64\...\python.exe cho scientific stack.
"@
}

if (-not (Test-Path -LiteralPath $environmentPath)) {
    & $pythonCommand[0] $pythonCommand[1] -m venv $environmentPath
    if ($LASTEXITCODE -ne 0) { throw "Không thể tạo $environmentPath" }
}

$environmentPython = Join-Path $environmentPath "Scripts\python.exe"
& $environmentPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Không thể nâng cấp pip" }

& $environmentPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Không thể cài requirements.txt" }

& $environmentPython (Join-Path $projectRoot "scripts\verify_environment.py")
if ($LASTEXITCODE -ne 0) { throw "Scientific stack chưa đầy đủ" }

Write-Host "Môi trường VS Code đã sẵn sàng tại $environmentPython"
