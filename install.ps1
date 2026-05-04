# Brevix installer (PowerShell). Run with:
#   irm https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.ps1 | iex

[CmdletBinding()]
param(
    [string]$Repo = "Yash-Koladiya30/brevix",
    [string]$Branch = "main",
    [switch]$DryRun,
    [switch]$Minimal,
    [switch]$All,
    [switch]$Force,
    [string]$Only = "",
    [switch]$WithHooks,
    [switch]$WithMcpShrink,
    [switch]$List
)

$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host ">> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow }

if ($List) {
    Write-Host "Available targets: claude-code, cursor, windsurf, codex, antigravity, copilot, aider, continue, cline, roo, zed, agents-md, all"
    exit 0
}

if (-not (Get-Command python -ErrorAction SilentlyContinue) -and `
    -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Error "python is required."
    exit 1
}

$pip = if (Get-Command pipx -ErrorAction SilentlyContinue) { "pipx" } else { "pip" }

Step "Installing brevix CLI via $pip"
if ($DryRun) {
    Write-Host "[dry-run] would run: $pip install --user --upgrade git+https://github.com/$Repo.git@$Branch"
} else {
    if ($pip -eq "pipx") {
        & pipx install --force "git+https://github.com/$Repo.git@$Branch"
    } else {
        & pip install --user --upgrade "git+https://github.com/$Repo.git@$Branch"
    }
}

if (Get-Command brevix -ErrorAction SilentlyContinue) {
    & brevix --version
    Step "Brevix CLI installed."
} else {
    Warn "'brevix' not on PATH. Add Python user site to PATH and re-open shell."
}

if (-not $Minimal -and ($All -or $WithHooks)) {
    Step "Installing Claude Code hooks (Windows)"
    Write-Host "  See hooks\install.ps1 in your local repo clone."
}

Write-Host ""
Step "Claude Code plugin install:"
Write-Host "  /plugin marketplace add $Repo"
Write-Host "  /plugin install brevix@brevix"
Write-Host ""
Step "Project-level rules: brevix install <target> --path <project>"
