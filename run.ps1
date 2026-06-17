$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $appRoot
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Set-Location $repoRoot

if (-not $env:PORT) {
    $env:PORT = "8082"
}

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

    & $Command @Arguments (Join-Path $appRoot "app\app.py")
    exit $LASTEXITCODE
}

Invoke-IfWorkingPython "python"
Invoke-IfWorkingPython "py" @("-3")

if (Test-Path $bundledPython) {
    & $bundledPython (Join-Path $appRoot "app\app.py")
    exit $LASTEXITCODE
}

throw "Python 3.10+ was not found. Install Python or run with a Python interpreter directly."
