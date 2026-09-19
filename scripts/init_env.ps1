# FasalRakshak — create .env from the template (never overwrites an existing file).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root ".env"
$template = Join-Path $root ".env.example"

if (Test-Path $target) {
    Write-Host ".env already exists — leaving it untouched."
} else {
    Copy-Item $template $target
    Write-Host "Created .env from .env.example. Fill in real values before running the stack."
}