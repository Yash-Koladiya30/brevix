# Brevix statusline badge for Claude Code (PowerShell).
# Disable: $env:BREVIX_STATUSLINE = "0"

if ($env:BREVIX_STATUSLINE -eq "0") { exit 0 }

$null = [Console]::In.ReadToEnd()  # consume stdin

$saved = $null
if (Get-Command brevix -ErrorAction SilentlyContinue) {
    $line = brevix stats 2>$null | Select-String "Tokens saved"
    if ($line) {
        $m = [regex]::Match($line.Line, '~([\d,]+)')
        if ($m.Success) { $saved = [int64]($m.Groups[1].Value -replace ',', '') }
    }
}

if (-not $saved) {
    $statsPath = Join-Path $HOME ".brevix\stats.json"
    if (Test-Path $statsPath) {
        try {
            $j = Get-Content $statsPath -Raw | ConvertFrom-Json
            $saved = [int64]$j.total_tokens_estimated
        } catch { $saved = 0 }
    }
}

if (-not $saved -or $saved -eq 0) {
    Write-Output "[BREVIX]"
    exit 0
}

$human = if ($saved -ge 1000000) { "{0:N1}M" -f ($saved / 1000000) }
         elseif ($saved -ge 1000) { "{0:N1}k" -f ($saved / 1000) }
         else { "$saved" }

Write-Output "[BREVIX] # $human saved"
