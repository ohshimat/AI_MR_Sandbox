[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsDirect = Join-Path $PSScriptRoot "requirements-runtime.txt"
$requirementsLock = Join-Path $PSScriptRoot "requirements-runtime-lock.txt"
$requirements = if (Test-Path -LiteralPath $requirementsLock -PathType Leaf) {
    $requirementsLock
} else {
    $requirementsDirect
}

if (-not (Test-Path -LiteralPath $requirements -PathType Leaf)) {
    throw "Requirements file was not found: $requirements"
}

$pythonLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
if (-not $pythonLauncher) {
    throw "Python Launcher (py.exe) was not found. Install Python 3.11 first."
}

& $pythonLauncher.Path -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 is not available through py.exe."
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Creating virtual environment: $venvDir"
    & $pythonLauncher.Path -3.11 -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        throw "Virtual environment creation failed."
    }
}
else {
    Write-Host "Using existing virtual environment: $venvDir"
}

Write-Host "Installing the pinned pip version..."
& $venvPython -m pip install --upgrade "pip==26.2.1"
if ($LASTEXITCODE -ne 0) {
    throw "pip installation failed."
}

Write-Host "Installing AI-MR Sandbox Python dependencies..."
& $venvPython -m pip install --requirement $requirements
if ($LASTEXITCODE -ne 0) {
    throw "AI-MR Sandbox dependency installation failed."
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    throw "pip check reported broken requirements."
}

& $venvPython -c "import importlib.metadata as m, sys; print('Python:', sys.version.split()[0]); print('Executable:', sys.executable); print('sounddevice:', m.version('sounddevice')); print('faster-whisper:', m.version('faster-whisper'))"
if ($LASTEXITCODE -ne 0) {
    throw "Installed package verification failed."
}

Write-Host ""
Write-Host "AI-MR Sandbox Python bootstrap completed."
Write-Host "Next: powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\verify_runtime_environment.ps1`""
