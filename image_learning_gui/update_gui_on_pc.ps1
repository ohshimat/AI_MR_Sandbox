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
if (-not (Test-Path -LiteralPath $TargetRoot -PathType Container)) {
    throw "Operational GUI was not found. Run deploy_gui_to_pc.cmd first: $TargetRoot"
}
if ($SourceRoot.Equals($TargetRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Do not run the updater inside the operational GUI. Run update_gui_on_pc.cmd from the Git repository source."
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
$TemporaryRoot = Join-Path $TargetParent (".image_learning_gui.update-" + [guid]::NewGuid().ToString("N"))
$BackupParent = Join-Path $ExpectedParent "backups"
$BackupRoot = Join-Path $BackupParent (
    "image_learning_gui-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-" +
    [guid]::NewGuid().ToString("N").Substring(0, 8)
)

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

function Copy-TreeContents {
    param(
        [string]$FromRoot,
        [string]$ToRoot
    )
    $FromRoot = [System.IO.Path]::GetFullPath($FromRoot).TrimEnd("\")
    $PrefixLength = $FromRoot.Length + 1
    New-Item -ItemType Directory -Force -Path $ToRoot | Out-Null
    Get-ChildItem -LiteralPath $FromRoot -Force -Recurse | ForEach-Object {
        $RelativePath = $_.FullName.Substring($PrefixLength)
        $Destination = Join-Path $ToRoot $RelativePath
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        }
        else {
            $DestinationParent = Split-Path -Parent $Destination
            New-Item -ItemType Directory -Force -Path $DestinationParent | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $Destination -Force
        }
    }
}

$BackupCreated = $false
try {
    New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
    Get-ChildItem -LiteralPath $SourceRoot -Force | ForEach-Object {
        Copy-ProjectItem -Item $_ -DestinationRoot $TemporaryRoot
    }

    $CriticalFiles = @(
        "app.py",
        "start_gui.cmd",
        "config\defaults.yaml",
        "core\config.py",
        "core\training.py",
        "core\captions.py",
        "vendor\diffusers-0.41.0\examples\dreambooth\train_dreambooth_lora_sdxl.py"
    )
    $Hashes = @()
    foreach ($RelativePath in $CriticalFiles) {
        $SourceFile = Join-Path $SourceRoot $RelativePath
        $StagedFile = Join-Path $TemporaryRoot $RelativePath
        if (-not (Test-Path -LiteralPath $StagedFile -PathType Leaf)) {
            throw "Required update file is missing: $StagedFile"
        }
        $SourceHash = (Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash
        $StagedHash = (Get-FileHash -LiteralPath $StagedFile -Algorithm SHA256).Hash
        if ($SourceHash -ne $StagedHash) {
            throw "SHA-256 verification failed: $RelativePath"
        }
        $Hashes += [ordered]@{ path = $RelativePath; sha256 = $StagedHash }
    }

    $DeploymentRecord = [ordered]@{
        deployed_at = (Get-Date).ToString("o")
        source = $SourceRoot
        target = $TargetRoot
        gui_version = "0.7.7"
        workspace_root = (Join-Path $env:USERPROFILE "AI_MR_Workspace")
        temp_root = (Join-Path $ExpectedParent "temp")
        update_backup = $BackupRoot
        files = $Hashes
    }
    $DeploymentRecord | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $TemporaryRoot "deployment_manifest.json") -Encoding UTF8

    New-Item -ItemType Directory -Force -Path $BackupParent | Out-Null
    Copy-Item -LiteralPath $TargetRoot -Destination $BackupRoot -Recurse
    $BackupCreated = $true
    Copy-TreeContents -FromRoot $TemporaryRoot -ToRoot $TargetRoot

    foreach ($RelativePath in $CriticalFiles) {
        $TargetFile = Join-Path $TargetRoot $RelativePath
        $TargetHash = (Get-FileHash -LiteralPath $TargetFile -Algorithm SHA256).Hash
        $ExpectedHash = ($Hashes | Where-Object path -eq $RelativePath).sha256
        if ($TargetHash -ne $ExpectedHash) {
            throw "Final SHA-256 verification failed: $RelativePath"
        }
    }

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
    Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force
}
catch {
    if ($BackupCreated -and (Test-Path -LiteralPath $BackupRoot)) {
        Copy-TreeContents -FromRoot $BackupRoot -ToRoot $TargetRoot
    }
    if (Test-Path -LiteralPath $TemporaryRoot) {
        Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force
    }
    throw
}

Write-Host "GUI update completed and verified."
Write-Host "Operational GUI: $TargetRoot"
Write-Host "Previous version backup: $BackupRoot"
Write-Host "Common temporary data: $(Join-Path $ExpectedParent 'temp')"
Write-Host "Launcher: $(Join-Path $TargetRoot 'start_gui.cmd')"
