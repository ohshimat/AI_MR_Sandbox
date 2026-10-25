param(
    [string]$CommonRoot = $(
        if ($env:AI_MR_COMMON_ROOT) { $env:AI_MR_COMMON_ROOT }
        else { "C:\AI_MR_Sandbox" }
    ),
    [string]$PythonExecutable = $(
        if ($env:AI_MR_IMAGE_PYTHON) { $env:AI_MR_IMAGE_PYTHON }
        else { "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" }
    )
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = $PSScriptRoot
$GuiRoot = Join-Path $RepositoryRoot "image_learning_gui"
$RuntimeRoot = Join-Path $CommonRoot "runtime"
$GuiPackages = Join-Path $RuntimeRoot "image_gui_packages"
$TrainingPackages = Join-Path $RuntimeRoot "image_training_packages"
$LegacyGuiPackages = Join-Path $CommonRoot "image_learning_gui\.gui_packages"
$LegacyTrainingPackages = Join-Path $CommonRoot "image_learning_gui\.training_packages"
$TempRoot = Join-Path $CommonRoot "temp\pip"

if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    throw "Image AI Python was not found: $PythonExecutable"
}
if (-not (Test-Path -LiteralPath $GuiRoot -PathType Container)) {
    throw "Portable GUI source was not found: $GuiRoot"
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot, $TempRoot | Out-Null

function Install-Or-MigratePackages {
    param(
        [string]$Target,
        [string]$Legacy,
        [string]$Sentinel,
        [string]$Requirements
    )

    if (Test-Path -LiteralPath (Join-Path $Target $Sentinel)) {
        Write-Host "Using existing packages: $Target"
        return
    }

    if (
        -not (Test-Path -LiteralPath $Target) -and
        (Test-Path -LiteralPath (Join-Path $Legacy $Sentinel))
    ) {
        Write-Host "Migrating verified local packages to: $Target"
        Copy-Item -LiteralPath $Legacy -Destination $Target -Recurse
        return
    }

    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    Write-Host "Installing packages from: $Requirements"
    $env:TEMP = $TempRoot
    $env:TMP = $TempRoot
    & $PythonExecutable -m pip install --upgrade --target $Target `
        --requirement $Requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Package installation failed: $Requirements"
    }
}

Install-Or-MigratePackages `
    -Target $GuiPackages `
    -Legacy $LegacyGuiPackages `
    -Sentinel "gradio" `
    -Requirements (Join-Path $GuiRoot "requirements-gui-lock.txt")

Install-Or-MigratePackages `
    -Target $TrainingPackages `
    -Legacy $LegacyTrainingPackages `
    -Sentinel "datasets" `
    -Requirements (Join-Path $GuiRoot "requirements-training-lock.txt")

$env:AI_MR_COMMON_ROOT = $CommonRoot
$env:AI_MR_IMAGE_PYTHON = $PythonExecutable
$env:AI_MR_IMAGE_ACCELERATE = Join-Path `
    (Split-Path -Parent $PythonExecutable) "accelerate.exe"
$env:AI_MR_GUI_PACKAGES = $GuiPackages
$env:AI_MR_TRAINING_PACKAGES = $TrainingPackages
$env:AI_MR_WORKSPACE = Join-Path $env:USERPROFILE "AI_MR_Workspace"
$env:PYTHONPATH = "$GuiPackages;$TrainingPackages"

& $PythonExecutable -c `
    "import gradio, datasets; print('Gradio:', gradio.__version__); print('Datasets:', datasets.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Image GUI dependency verification failed."
}

& $PythonExecutable -m pytest -q (Join-Path $GuiRoot "tests")
if ($LASTEXITCODE -ne 0) {
    throw "Image GUI tests failed."
}

[PSCustomObject]@{
    PortableEntry = $RepositoryRoot
    GuiSource = $GuiRoot
    Python = $PythonExecutable
    GuiPackages = $GuiPackages
    TrainingPackages = $TrainingPackages
    Tests = "OK"
}
