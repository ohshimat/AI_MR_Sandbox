
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Resolve A / B / C environments
$paths = & (Join-Path $PSScriptRoot "resolve_environment.ps1")

# Required portable source files
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

$missing = @(
    $coreFiles | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $paths.RepoRoot $_) -PathType Leaf)
    }
)

$runtimeExists = Test-Path -LiteralPath $paths.RuntimePython -PathType Leaf
$imageExists = Test-Path -LiteralPath $paths.ImagePython -PathType Leaf

[pscustomobject]@{
    Computer           = $env:COMPUTERNAME
    RepoRoot           = $paths.RepoRoot
    PcRoot             = $paths.PcRoot
    WorkspaceRoot      = $paths.WorkspaceRoot
    WorkspaceExists    = Test-Path -LiteralPath $paths.WorkspaceRoot -PathType Container
    RuntimePython      = $paths.RuntimePython
    RuntimeExists      = $runtimeExists
    ImagePython        = $paths.ImagePython
    ImageExists        = $imageExists
    CoreFilesChecked   = $coreFiles.Count
    CoreFilesMissing   = $missing.Count
    MissingFiles       = ($missing -join "; ")
    LegacyVenvPresent  = Test-Path -LiteralPath (Join-Path $paths.RepoRoot ".venv")
    RuntimeStatus      = if ($runtimeExists) { "PRESENT - not validated" } else { "NOT INSTALLED" }
} | Format-List

Write-Host "Level 2 environment inspection completed."
Write-Host "No installation or modification was performed."
