$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $repoRoot

function Invoke-IfWorkingPython {
    param([string]$Command, [string[]]$Arguments = @())

    $resolved = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $resolved) {
        return $false
    }

    & $Command @Arguments --version *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $Command @Arguments -m app.app
    exit $LASTEXITCODE
}

Invoke-IfWorkingPython "python"
Invoke-IfWorkingPython "py" @("-3")

if (Test-Path $bundledPython) {
    & $bundledPython -m app.app
    exit $LASTEXITCODE
}

throw "Python 3.10+ was not found. Install Python or run with a Python interpreter directly: python -m app.app"
