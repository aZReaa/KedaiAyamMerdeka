$env:APP_ENV = "local"

param(
    [Parameter(Mandatory = $true)]
    [string]$Username,

    [string]$Password,

    [string]$Name
)

if (-not (Test-Path ".env.local")) {
    Write-Host ".env.local belum ada. Copy .env.local.example menjadi .env.local dulu." -ForegroundColor Yellow
    exit 1
}

$args = @("create_admin.py", "--username", $Username)

if ($Password) {
    $args += @("--password", $Password)
}

if ($Name) {
    $args += @("--name", $Name)
}

py @args
