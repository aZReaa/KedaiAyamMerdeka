$env:APP_ENV = "local"

if (-not (Test-Path ".env.local")) {
    Write-Host ".env.local belum ada. Copy .env.local.example menjadi .env.local lalu isi konfigurasi lokal Anda." -ForegroundColor Yellow
    exit 1
}

Write-Host "Menjalankan app dalam mode lokal..." -ForegroundColor Cyan
Write-Host "Database target akan dibaca dari .env.local" -ForegroundColor Cyan

py app.py
