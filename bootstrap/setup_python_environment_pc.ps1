
[CmdletBinding()]
param([switch]$Install, [switch]$CheckInstallSafety)

$ErrorActionPreference = "Stop"

# Resolve A / B / C environment paths
$envPaths = & (Join-Path $PSScriptRoot "resolve_environment.ps1")

$venvDir = Join-Path $envPaths.VenvRoot "AI_MR_Sandbox_Runtime"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$requirementsLock = Join-Path $PSScriptRoot "requirements-runtime-lock.txt"
$requirementsDirect = Join-Path $PSScriptRoot "requirements-runtime.txt"

$requirements = if (Test-Path -LiteralPath $requirementsLock -PathType Leaf) {
    $requirementsLock
} else {
    $requirementsDirect
}

if (-not (Test-Path -LiteralPath $requirements -PathType Leaf)) {
    throw "Requirements file not found: $requirements"
}

# Protect the portable repository
$repoPath = [IO.Path]::GetFullPath($envPaths.RepoRoot).TrimEnd([char[]]@('\','/'))
$venvPath = [IO.Path]::GetFullPath($venvDir).TrimEnd([char[]]@('\','/'))

if ($venvPath.Equals($repoPath, [StringComparison]::OrdinalIgnoreCase) -or
    $venvPath.StartsWith(($repoPath + '\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to create a virtual environment inside the portable repository."
}


$portableVolume = [IO.Path]::GetPathRoot($repoPath); $venvVolume = [IO.Path]::GetPathRoot($venvPath); if ([string]::Equals($portableVolume, $venvVolume, [StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to create a virtual environment on the portable repository volume: $portableVolume" }


# Do not use redirected virtual-environment directories
foreach ($path in @($envPaths.VenvRoot, $venvDir)) {
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing to use a redirected directory: $path"
        }
    }
}

Write-Host "Repository:    $($envPaths.RepoRoot)"
Write-Host "PC root:       $($envPaths.PcRoot)"
Write-Host "Workspace:     $($envPaths.WorkspaceRoot)"
Write-Host "Runtime venv:  $venvDir"
Write-Host "Python:        $venvPython"
Write-Host "Requirements:  $requirements"

# Default mode is read-only
if (-not $Install -and -not $CheckInstallSafety) {
    Write-Host ""
    Write-Host "PREVIEW ONLY: No files or environments were modified."
    return
}


# Explicit installation mode
if ($Install -and $CheckInstallSafety) { throw "Specify only one mode." }

if (Test-Path -LiteralPath $venvDir) {
    throw "Refusing to modify an existing Runtime environment: $venvDir"
}

# Safety-check mode: stop before installation
if ($CheckInstallSafety) {
    Write-Host "SAFETY CHECK PASS: No installation performed."
    return
}

$launcher = Get-Command "py.exe" -ErrorAction SilentlyContinue

if (-not $launcher) {
    throw "Python Launcher (py.exe) was not found."
}

& $launcher.Path -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 is not available."
}

New-Item -ItemType Directory -Path $envPaths.VenvRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Creating PC-local virtual environment..."
    & $launcher.Path -3.11 -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        throw "Virtual environment creation failed."
    }
}

Write-Host "Installing pinned dependencies..."
& $venvPython -m pip install --upgrade "pip==26.2.1"
if ($LASTEXITCODE -ne 0) {
    throw "pip installation failed."
}

& $venvPython -m pip install --requirement $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    throw "Dependency verification failed."
}

Write-Host "PC-local Runtime environment installation completed."
