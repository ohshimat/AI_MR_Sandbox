param(
    [string]$TargetRoot = "C:\AI_MR_Sandbox\image_learning_gui"
)

$ErrorActionPreference = "Stop"
$SourceRoot = $PSScriptRoot
$TargetRoot = [System.IO.Path]::GetFullPath($TargetRoot)
$TargetParent = Split-Path -Parent $TargetRoot
$ExpectedParent = [System.IO.Path]::GetFullPath("C:\AI_MR_Sandbox")

if (-not $TargetRoot.StartsWith($ExpectedParent + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Target must be inside C:\AI_MR_Sandbox."
}
if (Test-Path -LiteralPath $TargetRoot) {
    throw "Target already exists. No files were overwritten: $TargetRoot"
}

$ExcludedNames = @(
    ".git",
    ".gui_packages",
    ".training_packages",
    "__pycache__",
    ".pytest_cache",
    ".pip_temp",
    ".preview",
    ".datasets_cache",
    "test_artifacts",
    "deployment_manifest.json"
)
$TemporaryRoot = Join-Path $TargetParent (".image_learning_gui.partial-" + [guid]::NewGuid().ToString("N"))

function Copy-ProjectItem {
    param(
        [System.IO.FileSystemInfo]$Item,
        [string]$DestinationRoot
    )
    if ($ExcludedNames -contains $Item.Name) {
        return
    }
    $Destination = Join-Path $DestinationRoot $Item.Name
    if ($Item.PSIsContainer) {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        Get-ChildItem -LiteralPath $Item.FullName -Force | ForEach-Object {
            Copy-ProjectItem -Item $_ -DestinationRoot $Destination
        }
    }
    else {
        Copy-Item -LiteralPath $Item.FullName -Destination $Destination
    }
}

try {
    New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
    New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
    Get-ChildItem -LiteralPath $SourceRoot -Force | ForEach-Object {
        Copy-ProjectItem -Item $_ -DestinationRoot $TemporaryRoot
    }

    $CriticalFiles = @(
        "app.py",
        "start_gui.cmd",
        "config\defaults.yaml",
        "core\config.py",
        "requirements-gui-lock.txt",
        "requirements-training-lock.txt",
        "vendor\diffusers-0.41.0\examples\dreambooth\train_dreambooth_lora_sdxl.py"
    )
    $Hashes = @()
    foreach ($RelativePath in $CriticalFiles) {
        $SourceFile = Join-Path $SourceRoot $RelativePath
        $TargetFile = Join-Path $TemporaryRoot $RelativePath
        if (-not (Test-Path -LiteralPath $TargetFile -PathType Leaf)) {
            throw "Required deployed file is missing: $TargetFile"
        }
        $SourceHash = (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash
        $TargetHash = (Get-FileHash -LiteralPath $TargetFile -Algorithm SHA256).Hash
        if ($SourceHash -ne $TargetHash) {
            throw "SHA-256 verification failed: $RelativePath"
        }
        $Hashes += [ordered]@{
            path = $RelativePath
            sha256 = $TargetHash
        }
    }

    $DeploymentRecord = [ordered]@{
        deployed_at = (Get-Date).ToString("o")
        source = $SourceRoot
        target = $TargetRoot
        gui_version = "0.8.0"
        workspace_root = (Join-Path $env:USERPROFILE "AI_MR_Workspace")
        temp_root = (Join-Path $ExpectedParent "temp")
        files = $Hashes
    }
    $DeploymentRecord | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $TemporaryRoot "deployment_manifest.json") -Encoding UTF8

    Move-Item -LiteralPath $TemporaryRoot -Destination $TargetRoot

    $CommonTempRoot = Join-Path $ExpectedParent "temp"
    New-Item -ItemType Directory -Force -Path (Join-Path $CommonTempRoot "preview") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $CommonTempRoot "datasets") | Out-Null

    $CommonManifestRoot = Join-Path $ExpectedParent "manifests"
    New-Item -ItemType Directory -Force -Path $CommonManifestRoot | Out-Null
    $WorkspaceManifestRoot = Join-Path $env:USERPROFILE "AI_MR_Workspace\gui_records"
    $LatestWorkspaceManifest = Get-ChildItem -LiteralPath $WorkspaceManifestRoot `
        -Filter "workspace_migration_*.json" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($LatestWorkspaceManifest) {
        Copy-Item -LiteralPath $LatestWorkspaceManifest.FullName `
            -Destination (Join-Path $CommonManifestRoot $LatestWorkspaceManifest.Name) -Force
    }
}
catch {
    if (Test-Path -LiteralPath $TemporaryRoot) {
        Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force
    }
    throw
}

Write-Host "GUI deployment completed and verified."
Write-Host "Operational GUI: $TargetRoot"
Write-Host "Common temporary data: $(Join-Path $ExpectedParent 'temp')"
Write-Host "Launcher: $(Join-Path $TargetRoot 'start_gui.cmd')"
Write-Host "The development source was not deleted: $SourceRoot"
