[CmdletBinding()]
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

# CH09 migration, limited to the canonical documents copy.
# Default = Preview; -Apply performs git mv and stages the cleaned document.
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$sourceRel = 'documents/CHECKPOINT-9.md'
$targetRel = 'documents/CH09-MREALIntegration.md'
$source = Join-Path $repoRoot 'documents\CHECKPOINT-9.md'
$target = Join-Path $repoRoot 'documents\CH09-MREALIntegration.md'
$alternate = Join-Path $repoRoot 'python\CHECKPOINT-9.md'

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Canonical source not found: $source"
}
if (Test-Path -LiteralPath $target) {
    throw "Target already exists; no overwrite allowed: $target"
}

$original = [System.IO.File]::ReadAllText($source, [System.Text.Encoding]::UTF8)
$eol = if ($original.Contains("`r`n")) { "`r`n" } else { "`n" }
$lines = @($original -split '\r?\n')

# Only the exact, expected conversation wrapper is removed. Nested code
# fences inside the document are retained without modification.
$opening = [Array]::IndexOf($lines, '```markdown')
$closing = -1
for ($i = $lines.Count - 1; $i -gt $opening; $i--) {
    if ($lines[$i] -ceq '```') {
        $closing = $i
        break
    }
}
if ($opening -lt 0 -or $closing -le ($opening + 2)) {
    throw 'Expected outer Markdown wrapper not found. No changes made.'
}
if ($lines[$opening + 1] -cne '# CHECKPOINT-9' -or
    $lines[$opening + 2] -cne '# MREAL × AI-MR Sandbox Integration') {
    throw 'Unexpected CH09 headings. No changes made.'
}

$documentLines = @($lines[($opening + 1)..($closing - 1)])
$fenceCount = @($documentLines | Where-Object { $_ -match '^```' }).Count
if (($fenceCount % 2) -ne 0) {
    throw 'Unbalanced internal Markdown fences. No changes made.'
}
$cleaned = [string]::Join($eol, $documentLines) + $eol

Write-Host '=== CH09 migration preview ==='
Write-Host "Repository:       $repoRoot"
Write-Host "Source:           $sourceRel"
Write-Host "Target:           $targetRel"
Write-Host "Source lines:     $($lines.Count)"
Write-Host "Document lines:   $($documentLines.Count)"
Write-Host "Internal fences:  $fenceCount"
Write-Host "First heading:    $($documentLines[0])"
Write-Host "Final line:       $($documentLines[-1])"
Write-Host "Other CP9 copy:   $(if (Test-Path -LiteralPath $alternate -PathType Leaf) { 'PRESERVED (python/CHECKPOINT-9.md)' } else { 'NOT FOUND' })"
Write-Host ''
Write-Host 'Changes: rename documents copy, strip ONLY the outer conversation wrapper.'
Write-Host 'Unchanged: python copy, all other documents, cross-references, existing environments.'

if (-not $Apply) {
    Write-Host 'PREVIEW ONLY: No files or Git index entries were modified.'
    return
}

# Guards for actual change; refuse if the tracked source has local edits.
$git = Get-Command 'git.exe' -ErrorAction SilentlyContinue
if (-not $git) {
    throw 'Git for Windows was not found in PATH.'
}
$gitSafePath = $repoRoot.Replace('\', '/')
$branch = @(& $git.Source -c "safe.directory=$gitSafePath" -C $repoRoot branch --show-current)
if ($LASTEXITCODE -ne 0 -or $branch.Count -ne 1 -or $branch[0] -ne 'portability-cleanup') {
    throw 'Expected Git branch portability-cleanup. No changes made.'
}
& $git.Source -c "safe.directory=$gitSafePath" -C $repoRoot ls-files --error-unmatch -- $sourceRel *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Source is not tracked by Git. No changes made.'
}
$sourceStatus = @(& $git.Source -c "safe.directory=$gitSafePath" -C $repoRoot status --porcelain -- $sourceRel)
if ($LASTEXITCODE -ne 0 -or $sourceStatus.Count -gt 0) {
    throw 'Source has uncommitted changes. No changes made.'
}

& $git.Source -c "safe.directory=$gitSafePath" -C $repoRoot mv -- $sourceRel $targetRel
if ($LASTEXITCODE -ne 0) {
    throw 'git mv failed; inspect repository status before retrying.'
}
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($target, $cleaned, $utf8NoBom)
    & $git.Source -c "safe.directory=$gitSafePath" -C $repoRoot add -- $targetRel
    if ($LASTEXITCODE -ne 0) {
        throw 'git add failed.'
    }
}
catch {
    Write-Warning 'Rename may have been performed. Inspect git status; no automatic rollback was attempted.'
    throw
}
Write-Host 'APPLIED: Canonical CH09 renamed and cleaned; changes staged, not committed.'
Write-Host ('Review: git -c safe.directory=' + $gitSafePath + ' -C ' + $repoRoot + ' diff --cached --stat')
