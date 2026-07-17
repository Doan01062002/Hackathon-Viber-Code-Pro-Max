param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$IncludeArchivedSessions
)

$ErrorActionPreference = "Stop"

function Normalize-PathForMatch {
    param([string]$PathValue)
    try {
        return [System.IO.Path]::GetFullPath($PathValue).ToLowerInvariant()
    } catch {
        return $PathValue.ToLowerInvariant()
    }
}

function Get-PythonCommand {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return "python3"
    }
    return $null
}

function Test-SessionSafety {
    param(
        [string]$PythonCmd,
        [string]$RepoRoot,
        [string]$SessionFile
    )

    if (-not $PythonCmd) {
        return $true
    }

    $scanScript = Join-Path $RepoRoot "scripts\scan_secrets.py"
    if (-not (Test-Path -LiteralPath $scanScript)) {
        return $true
    }

    & $PythonCmd $scanScript $SessionFile | Out-Null
    return ($LASTEXITCODE -eq 0)
}

$repoRoot = (Get-Location).Path
$normalizedProjectPath = Normalize-PathForMatch -PathValue $ProjectPath
$codexHome = Join-Path $env:USERPROFILE ".codex"
$destDir = Join-Path $repoRoot "docs\ai-log\sessions"
$pythonCmd = Get-PythonCommand

if (-not (Test-Path -LiteralPath $codexHome)) {
    throw "Khong tim thay thu muc $codexHome"
}

New-Item -ItemType Directory -Force -Path $destDir | Out-Null

$roots = @(
    @{
        Path = Join-Path $codexHome "sessions"
        Prefix = "codex"
    }
)

if ($IncludeArchivedSessions) {
    $roots += @{
        Path = Join-Path $codexHome "archived_sessions"
        Prefix = "codex-archived"
    }
}

$copiedCount = 0
$skippedCount = 0

foreach ($root in $roots) {
    if (-not (Test-Path -LiteralPath $root.Path)) {
        continue
    }

    Get-ChildItem -LiteralPath $root.Path -Recurse -File -Filter "*.jsonl" | ForEach-Object {
        $sessionFile = $_.FullName
        $firstLine = Get-Content -LiteralPath $sessionFile -TotalCount 1
        if (-not $firstLine) {
            return
        }

        try {
            $json = $firstLine | ConvertFrom-Json
        } catch {
            return
        }

        if ($json.type -ne "session_meta") {
            return
        }

        $cwd = ""
        if ($null -ne $json.payload -and $null -ne $json.payload.cwd) {
            $cwd = [string]$json.payload.cwd
        }

        if ((Normalize-PathForMatch -PathValue $cwd) -ne $normalizedProjectPath) {
            return
        }

        if (-not (Test-SessionSafety -PythonCmd $pythonCmd -RepoRoot $repoRoot -SessionFile $sessionFile)) {
            Write-Warning "Bo qua file session vi scan_secrets.py bao co secret: $sessionFile"
            $script:skippedCount++
            return
        }

        $sourceStem = [System.IO.Path]::GetFileNameWithoutExtension($sessionFile)
        $timestamp = Get-Date ([string]$json.payload.timestamp)
        $day = $timestamp.ToString("yyyy-MM-dd")
        $destination = Join-Path $destDir "$day-$($root.Prefix)-$sourceStem.jsonl"

        Copy-Item -LiteralPath $sessionFile -Destination $destination -Force
        Write-Output "Copied: $(Split-Path -Leaf $destination)"
        $script:copiedCount++
    }
}

Write-Output "Codex sessions copied: $copiedCount"
Write-Output "Codex sessions skipped: $skippedCount"
