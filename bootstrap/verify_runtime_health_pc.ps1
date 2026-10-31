
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Level 3: Runtime health verification
$paths = & (Join-Path $PSScriptRoot "resolve_environment.ps1")

$pythonStatus = "SKIPPED - NOT INSTALLED"
$packagesStatus = "SKIPPED"
$pipStatus = "SKIPPED"
$ollamaStatus = "NOT FOUND IN PATH"
$modelStatus = "SKIPPED"
$apiStatus = "SKIPPED"

# Python runtime verification
if (Test-Path -LiteralPath $paths.RuntimePython -PathType Leaf) {

    $pythonStatus = "PRESENT"

    & $paths.RuntimePython -B -c "import tkinter, sounddevice; from faster_whisper import WhisperModel"

    if ($LASTEXITCODE -eq 0) {
        $packagesStatus = "PASS"
    }
    else {
        $packagesStatus = "FAIL"
    }

    & $paths.RuntimePython -B -m pip check

    if ($LASTEXITCODE -eq 0) {
        $pipStatus = "PASS"
    }
    else {
        $pipStatus = "FAIL"
    }
}

# Ollama verification
$ollama = Get-Command "ollama.exe" -ErrorAction SilentlyContinue

if ($ollama) {

    $ollamaStatus = "FOUND"

    $modelList = @(& $ollama.Source list 2>&1)
    $listExitCode = $LASTEXITCODE

    if ($listExitCode -ne 0) {
        $modelStatus = "FAIL - LIST COMMAND"
    }
    elseif ($modelList -match '^qwen3:8b\s') {
        $modelStatus = "PASS"
    }
    else {
        $modelStatus = "FAIL - MODEL NOT FOUND"
    }

    try {
        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3

        if ($null -ne $tags.models) {
            $apiStatus = "PASS"
        }
        else {
            $apiStatus = "FAIL - INVALID RESPONSE"
        }
    }
    catch {
        $apiStatus = "FAIL - API UNAVAILABLE"
    }
}

# Report
[pscustomobject]@{
    Computer       = $env:COMPUTERNAME
    RepoRoot       = $paths.RepoRoot
    RuntimePython  = $paths.RuntimePython
    PythonStatus   = $pythonStatus
    PackagesStatus = $packagesStatus
    PipStatus      = $pipStatus
    OllamaStatus   = $ollamaStatus
    ModelStatus    = $modelStatus
    ApiStatus      = $apiStatus
} | Format-List

Write-Host "Level 3 runtime health inspection completed."
Write-Host "No installation was performed."
