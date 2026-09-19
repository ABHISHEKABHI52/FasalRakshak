# FasalRakshak — run the Phase 1 verification suite locally.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

Write-Host "== Backend tests ==" -ForegroundColor Cyan
Push-Location $backend
& $python -m pytest -q
Pop-Location

Write-Host "== Frontend typecheck ==" -ForegroundColor Cyan
Push-Location $frontend
npm run typecheck
Write-Host "== Frontend unit tests ==" -ForegroundColor Cyan
npm run test
Write-Host "== Frontend build ==" -ForegroundColor Cyan
npm run build
Pop-Location

Write-Host "All checks finished." -ForegroundColor Green