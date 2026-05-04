# Brevix uninstaller (Windows).
$ErrorActionPreference = "Continue"

Write-Host ">> Brevix uninstaller"

if (Get-Command pipx -ErrorAction SilentlyContinue) {
    & pipx uninstall brevix
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    & pip uninstall -y brevix
}

$settings = Join-Path $HOME ".claude\settings.json"
if (Test-Path $settings) {
    try {
        $j = Get-Content $settings -Raw | ConvertFrom-Json
        if ($j.hooks.SessionStart) {
            $j.hooks.SessionStart = @($j.hooks.SessionStart | Where-Object { $_.matcher -ne "brevix" })
        }
        if ($j.hooks.UserPromptSubmit) {
            $j.hooks.UserPromptSubmit = @($j.hooks.UserPromptSubmit | Where-Object { $_.matcher -ne "brevix" })
        }
        if ($j.statusLine -and $j.statusLine.command -match "brevix-statusline") {
            $j.PSObject.Properties.Remove("statusLine")
        }
        $j | ConvertTo-Json -Depth 10 | Set-Content $settings
        Write-Host ">> Removed Brevix hooks from $settings"
    } catch {
        Write-Warning "Could not edit ${settings}: $_"
    }
}

Write-Host ">> Done. Stats kept at ~\.brevix (delete manually if not needed)."
