# Skrypt deploymentu na Google Cloud Run (Windows PowerShell)
# Użycie: .\deploy.ps1 [PROJECT_ID] [REGION]

param(
    [string]$ProjectId = "slowianske-dziedzictwo",
    [string]$Region = "europe-central2",
    [string]$ServiceName = "slowianske-dziedzictwo"
)

Write-Host "🚀 Deploying to Google Cloud Run..." -ForegroundColor Green
Write-Host "   Project: $ProjectId"
Write-Host "   Region: $Region"
Write-Host "   Service: $ServiceName"

# Ustaw projekt
gcloud config set project $ProjectId

# Deploy na Cloud Run
gcloud run deploy $ServiceName `
  --source . `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --set-env-vars "FLASK_ENV=production" `
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Service deployed successfully"
