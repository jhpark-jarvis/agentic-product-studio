param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = if (Test-Path '.venv\Scripts\python.exe') {
    Join-Path $projectRoot '.venv\Scripts\python.exe'
} else {
    'python'
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $python -c "import fastapi, uvicorn" *> $null
$pythonDependenciesAvailable = $LASTEXITCODE -eq 0
$ErrorActionPreference = $previousErrorActionPreference

if (-not $pythonDependenciesAvailable) {
    Write-Host 'Installing Python dependencies into the selected virtual environment...'
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path 'frontend\node_modules')) {
    npm run frontend:install
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

npm run frontend:build
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Agentic Product Studio is running at http://127.0.0.1:$Port/avatar-assets"
& $python -m uvicorn asgi:app --host 127.0.0.1 --port $Port --reload
