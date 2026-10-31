#requires -Version 5.1
<#
.SYNOPSIS
  Inspect legacy checkpoint documents without changing the repository.
.DESCRIPTION
  Lists checkpoint-like Markdown documents in documents/ and their first headings.
  Locates CP11 DOCX candidates in the repository root or documents/.
  It does NOT rename, convert, write, stage, or commit anything.
.EXAMPLE
  & '.\bootstrap\audit_checkpoint_documents.ps1'
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepoRoot).Path
$documents = Join-Path $root 'documents'
if (-not (Test-Path -LiteralPath $documents -PathType Container)) {
    throw "documents directory not found: $documents"
}

Write-Host '=== Checkpoint document audit (READ ONLY) ==='
Write-Host "Repository: $root"
Write-Host ''

$chapterPattern = '^(?:CHECKPOINT-\d+(?:\.\d+)?|CP[-_.]?\d+(?:\.\d+)?|CH\d+(?:\.\d+)?(?:-|$))'
$docs = @(Get-ChildItem -LiteralPath $documents -File -Filter '*.md' |
    Where-Object { $_.BaseName -match $chapterPattern } |
    Sort-Object Name)

Write-Host "Chapter-like Markdown files: $($docs.Count)"
foreach ($file in $docs) {
    $body = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    $headingMatches = [regex]::Matches($body, '(?m)^\s{0,3}#{1,3}\s+(.+?)\s*$')
    $headings = @($headingMatches | Select-Object -First 3 | ForEach-Object { $_.Groups[1].Value.Trim() })
    Write-Host "- $($file.Name)"
    if ($headings.Count -gt 0) {
        foreach ($title in $headings) { Write-Host "    Heading: $title" }
    }
    else {
        Write-Host '    Heading: (no Markdown heading found)'
        $firstLine = @($body -split '\r?\n' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if ($firstLine.Count -gt 0) { Write-Host "    First line: $($firstLine[0].Trim())" }
    }
}

Write-Host ''
Write-Host 'CP11 Word document candidates (not converted):'
$wordCandidates = @(@($root, $documents) | Select-Object -Unique | ForEach-Object {
    Get-ChildItem -LiteralPath $_ -File -Filter '*.docx' | Where-Object { $_.Name -match '(?i)^(?:CP[_-]?11|CHECKPOINT[_-]?11|CH11)' }
})
if ($wordCandidates.Count -eq 0) {
    Write-Host '  (not found in repository root or documents/)'
    Write-Host '  If stored elsewhere, provide its path before conversion.'
}
else {
    foreach ($file in $wordCandidates) {
        Write-Host "- $($file.FullName.Substring($root.Length).TrimStart([char[]]@('\','/')))"
    }
}

Write-Host ''
Write-Host '=== End of audit. No files were changed. ==='
