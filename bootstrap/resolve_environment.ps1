
# AI-MR Sandbox Environment Resolver
# Read-only configuration resolver

$ErrorActionPreference = "Stop"

# C: Portable repository
$repoRoot = (Resolve-Path (
    Join-Path $PSScriptRoot ".."
)).Path

# A: PC configuration
$machineFile = if ($env:AI_MR_MACHINE_CONFIG) {
    $env:AI_MR_MACHINE_CONFIG
} else {
    "C:\AI_MR_Sandbox\config\machine.json"
}

# B: User configuration
$userFile = Join-Path $env:APPDATA "AI_MR_Sandbox\user.json"

function Read-EnvironmentConfig {
    param(
        [string]$Path,
        [string[]]$RequiredKeys
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Configuration file not found: $Path"
    }

    $config = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 |
        ConvertFrom-Json

    if ($config.schema_version -ne 1) {
        throw "Unsupported schema version: $Path"
    }

    foreach ($key in $RequiredKeys) {
        $property = $config.PSObject.Properties[$key]

        if ($null -eq $property -or
            -not ($property.Value -is [string]) -or
            [string]::IsNullOrWhiteSpace($property.Value)) {
            throw "Invalid configuration field '$key': $Path"
        }

        if (-not [System.IO.Path]::IsPathRooted($property.Value)) {
            throw "Path must be absolute: $key"
        }
    }

    return $config
}

$machine = Read-EnvironmentConfig $machineFile @(
    "pc_root", "venv_root"
)

$user = Read-EnvironmentConfig $userFile @(
    "workspace_root"
)

# Resolved paths
[pscustomobject]@{
    RepoRoot      = $repoRoot
    PcRoot        = $machine.pc_root
    VenvRoot      = $machine.venv_root
    RuntimePython = Join-Path $machine.venv_root "AI_MR_Sandbox_Runtime\Scripts\python.exe"
    ImagePython   = Join-Path $machine.venv_root "AI_MR_Sandbox\Scripts\python.exe"
    ModelsRoot    = Join-Path $machine.pc_root "models"
    CacheRoot     = Join-Path $machine.pc_root "cache"
    WorkspaceRoot = $user.workspace_root
}
