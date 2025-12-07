#!/bin/bash

# Skrypt deploymentu na Google Cloud Run
# Użycie: ./deploy.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"slowianske-dziedzictwo"}
REGION=${2:-"europe-central2"}
SERVICE_NAME="slowianske-dziedzictwo"

echo "🚀 Deploying to Google Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"

# Ustaw projekt
gcloud config set project $PROJECT_ID

# Deploy na Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "FLASK_ENV=production" \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash"

echo "✅ Deployment complete!"
echo "🌐 URL: https://$SERVICE_NAME-xxx.run.app"
