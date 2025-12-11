# Start the Flask app via Waitress (Windows-friendly)
$ErrorActionPreference = "Stop"
Write-Host "🚀 Uruchamiam serwer (Waitress)..." -ForegroundColor Green

# Uruchom wirtualne środowisko Python z projektu
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"

if (-Not (Test-Path $venvPython)) {
    Write-Host "⚠️ Nie znaleziono virtualenv w .venv. Używam systemowego Pythona." -ForegroundColor Yellow
    $venvPython = "python"
}

# Ustaw zmienne środowiskowe (potrzebne do testów lokalnych)
$env:GEMINI_API_KEY = "test"

# Uruchom waitress
& $venvPython -m waitress --listen=0.0.0.0:8080 app:app

Write-Host "❌ Serwer zatrzymany" -ForegroundColor Red
