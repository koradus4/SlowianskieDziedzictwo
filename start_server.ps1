# Start server script
$ErrorActionPreference = "Stop"

Write-Host "🚀 Uruchamiam serwer..." -ForegroundColor Green

# Aktywuj środowisko wirtualne i uruchom
& .\.venv\Scripts\python.exe app.py

Write-Host "`n❌ Serwer zatrzymany" -ForegroundColor Red
