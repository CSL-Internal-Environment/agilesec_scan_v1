$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $repoRoot

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m app.app
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m app.app
    exit $LASTEXITCODE
}

if (Test-Path $bundledPython) {
    & $bundledPython -m app.app
    exit $LASTEXITCODE
}

throw "Python 3.10+ was not found. Install Python or run with a Python interpreter directly: python -m app.app"
