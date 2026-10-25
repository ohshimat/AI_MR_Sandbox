[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$errorsFound = [System.Collections.Generic.List[string]]::new()

$coreFiles = @(
    "python\speech_to_unity_ollama.py",
    "python\mr_agent_gui.py",
    "python\mr_agent_backend.py",
    "python\mr_agent_commands.py",
    "unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test\Assets\MRConversation\MRConversationBridge.cs",
    "unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test\Assets\MRConversation\MRAgentPanel.cs",
    "unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test\Assets\MRConversation\Editor\MRConversationInstaller.cs",
    "unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test\Assets\Scenes\Main_Conversation.unity"
)

Write-Host "Repository: $repoRoot"

foreach ($relativePath in $coreFiles) {
    $fullPath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        [void]$errorsFound.Add("Missing core file: $relativePath")
    }
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    [void]$errorsFound.Add("Virtual environment Python was not found: $venvPython")
}
else {
    & $venvPython -c "import importlib.metadata as m, tkinter; import sounddevice; from faster_whisper import WhisperModel; print('Python environment: OK'); print('sounddevice:', m.version('sounddevice')); print('faster-whisper:', m.version('faster-whisper')); print('Tkinter:', tkinter.TkVersion)"
    if ($LASTEXITCODE -ne 0) {
        [void]$errorsFound.Add("Python package import verification failed.")
    }

    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) {
        [void]$errorsFound.Add("pip check reported broken requirements.")
    }
}

$ollamaCommand = Get-Command "ollama.exe" -ErrorAction SilentlyContinue
if (-not $ollamaCommand) {
    [void]$errorsFound.Add("Ollama was not found in PATH.")
}
else {
    $ollamaList = @(& $ollamaCommand.Path list 2>&1)
    if ($LASTEXITCODE -ne 0) {
        [void]$errorsFound.Add("Ollama is installed but 'ollama list' failed.")
    }
    elseif (-not ($ollamaList -match '^qwen3:8b\s')) {
        [void]$errorsFound.Add("Required Ollama model was not found: qwen3:8b")
    }
    else {
        Write-Host "Ollama model qwen3:8b: OK"
    }
}

try {
    $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 10
    if ($null -eq $tags.models) {
        [void]$errorsFound.Add("Ollama API returned an unexpected response.")
    }
    else {
        Write-Host "Ollama API: OK"
    }
}
catch {
    [void]$errorsFound.Add("Ollama API is unavailable at http://localhost:11434.")
}

[PSCustomObject]@{
    CoreFilesChecked = $coreFiles.Count
    ErrorCount       = $errorsFound.Count
} | Format-List

if ($errorsFound.Count -gt 0) {
    foreach ($message in $errorsFound) {
        Write-Error $message
    }
    exit 1
}

Write-Host "AI-MR Sandbox environment verification: OK"
