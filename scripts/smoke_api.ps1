# FasalRakshak — API smoke test against a running backend (Phase 1 helper).
# Verifies: health, readiness, register, login, /me, RBAC denial, unauthenticated access.
# Credentials are passed in — nothing is stored in this file.

param(
    [string]$BaseUrl = "http://localhost:8000",

    [Parameter(Mandatory = $true)][string]$Phone,
    [Parameter(Mandatory = $true)][string]$Password,
    [string]$FullName = "Smoke Test User"
)

$ErrorActionPreference = "Stop"
$failures = 0

function Report([string]$name, [bool]$ok, [string]$detail) {
    $mark = if ($ok) { "PASS" } else { "FAIL" }
    if (-not $ok) { $script:failures++ }
    Write-Host ("[{0}] {1} {2}" -f $mark, $name, $detail)
}

# 1) health
$health = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -TimeoutSec 10
Report "health" ($health.status -eq "ok" -and $health.app -eq "FasalRakshak") ($health | ConvertTo-Json -Compress)

# 2) readiness
$ready = Invoke-RestMethod -Uri "$BaseUrl/api/v1/ready" -TimeoutSec 10
Report "readiness" ($ready.db -eq $true) ($ready | ConvertTo-Json -Compress)

# 3) register (409 tolerated: user may already exist from a previous run)
$registerBody = @{
    phone              = $Phone
    password           = $Password
    full_name          = $FullName
    preferred_language = "hi"
    consent_ml_use     = $true
} | ConvertTo-Json

try {
    $register = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/register" `
        -ContentType "application/json" -Body $registerBody -TimeoutSec 10
    Report "register" ($register.roles -contains "FARMER") ($register | ConvertTo-Json -Compress)
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    Report "register" ($status -eq 409) "already registered (HTTP $status)"
}

# 4) login
$login = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/login" `
    -ContentType "application/json" `
    -Body (@{ phone_or_email = $Phone; password = $Password } | ConvertTo-Json) -TimeoutSec 10
Report "login" ([bool]$login.access_token) ("expires_in=" + $login.expires_in + " roles=" + ($login.user.roles -join ","))

# 5) /me with token
$me = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" `
    -Headers @{ Authorization = "Bearer $($login.access_token)" } -TimeoutSec 10
Report "me" ($me.phone -eq $Phone) ("full_name=" + $me.full_name)

# 6) unauthenticated access must be denied
try {
    Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" -TimeoutSec 10 | Out-Null
    Report "me without token" $false "request unexpectedly succeeded"
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    Report "me without token" ($status -eq 401) "HTTP $status"
}

# 7) RBAC denial: a FARMER must not reach an ADMIN endpoint
try {
    Invoke-RestMethod -Uri "$BaseUrl/api/v1/admin/ping" `
        -Headers @{ Authorization = "Bearer $($login.access_token)" } -TimeoutSec 10 | Out-Null
    Report "rbac denial" $false "farmer reached admin endpoint"
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    Report "rbac denial" ($status -eq 403) "HTTP $status"
}

# 8) wrong password must fail generically
try {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/login" -ContentType "application/json" `
        -Body (@{ phone_or_email = $Phone; password = "$Password-wrong" } | ConvertTo-Json) -TimeoutSec 10 | Out-Null
    Report "invalid login" $false "login unexpectedly succeeded"
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    Report "invalid login" ($status -eq 401) "HTTP $status"
}

if ($failures -gt 0) {
    Write-Host "$failures check(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "All smoke checks passed." -ForegroundColor Green