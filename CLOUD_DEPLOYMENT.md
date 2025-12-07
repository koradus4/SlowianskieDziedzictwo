# 🚀 Google Cloud Run Deployment

Ten przewodnik opisuje jak wdrożyć **Słowiańskie Dziedzictwo** na Google Cloud Run.

---

## 📋 Wymagania

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) zainstalowane
- Konto Google Cloud z aktywną kartą płatniczą (free tier wystarczy na start)
- Klucz API Google Gemini

---

## 🔧 Krok 1: Przygotowanie Cloud Storage

Utwórz bucket dla plików audio:

```bash
# Zaloguj się do Google Cloud
gcloud auth login

# Ustaw projekt
gcloud config set project TWOJ_PROJEKT_ID

# Utwórz bucket (nazwa musi być globalmente unikalna)
gsutil mb -l europe-central2 gs://slowianske-audio

# Ustaw publiczny dostęp (dla odtwarzania audio)
gsutil iam ch allUsers:objectViewer gs://slowianske-audio
```

---

## 🗄️ Krok 2: Cloud SQL (Opcjonalnie - dla produkcji)

Dla testów możesz pominąć i używać SQLite w kontenerze.

```bash
# Utwórz instancję PostgreSQL
gcloud sql instances create slowianske-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-central2

# Ustaw hasło
gcloud sql users set-password postgres \
  --instance=slowianske-db \
  --password=TWOJE_HASLO

# Utwórz bazę danych
gcloud sql databases create gamedb --instance=slowianske-db
```

---

## 🚀 Krok 3: Deploy na Cloud Run

### Automatyczny deploy (Windows):

```powershell
.\deploy.ps1
```

### Automatyczny deploy (Linux/Mac):

```bash
chmod +x deploy.sh
./deploy.sh
```

### Ręczny deploy:

```bash
gcloud run deploy slowianske-dziedzictwo \
  --source . \
  --platform managed \
  --region europe-central2 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "FLASK_ENV=production" \
  --set-env-vars "GEMINI_API_KEY=AIzaSy..." \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash" \
  --set-env-vars "GCS_BUCKET_NAME=slowianske-audio"
```

**Opcjonalnie z Cloud SQL:**

```bash
gcloud run deploy slowianske-dziedzictwo \
  --source . \
  --platform managed \
  --region europe-central2 \
  --allow-unauthenticated \
  --memory 512Mi \
  --add-cloudsql-instances PROJECT_ID:europe-central2:slowianske-db \
  --set-env-vars "DATABASE_URL=postgresql://postgres:HASLO@/gamedb?host=/cloudsql/PROJECT_ID:europe-central2:slowianske-db" \
  --set-env-vars "GCS_BUCKET_NAME=slowianske-audio" \
  --set-env-vars "GEMINI_API_KEY=AIzaSy..." \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash" \
  --set-env-vars "FLASK_ENV=production"
```

---

## 🔐 Krok 4: Zmienne środowiskowe

Ustaw secrety w Secret Manager (bezpieczniejsze niż env vars):

```bash
# Utwórz secret dla API key
echo -n "AIzaSy..." | gcloud secrets create gemini-api-key --data-file=-

# Przypisz dostęp do Cloud Run
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

Następnie w deploy dodaj:

```bash
--set-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

---

## ✅ Weryfikacja

Po deploymencie:

1. **Sprawdź URL:**
   ```bash
   gcloud run services describe slowianske-dziedzictwo \
     --region europe-central2 \
     --format 'value(status.url)'
   ```

2. **Sprawdź logi:**
   ```bash
   gcloud run services logs read slowianske-dziedzictwo \
     --region europe-central2 \
     --limit 50
   ```

3. **Testuj aplikację:**
   Otwórz URL w przeglądarce i stwórz postać!

---

## 💰 Szacunkowe Koszty (Free Tier)

- **Cloud Run:** $0 (2M requestów/miesiąc free)
- **Cloud Storage:** $0 (5GB free)
- **Cloud SQL:** $7/miesiąc (db-f1-micro) lub $0 jeśli używasz SQLite
- **Gemini API:** $0 (free tier: 15 req/min, 1500/dzień)

**Total dla małego ruchu:** ~$0-7/miesiąc 🎯

---

## 🔄 Aktualizacje

Redeploy po zmianach:

```bash
gcloud run deploy slowianske-dziedzictwo --source .
```

Lub użyj skryptu:

```powershell
.\deploy.ps1
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" podczas deploymentu

```bash
gcloud auth application-default login
```

### Problem: Audio nie działa

Sprawdź czy bucket jest publiczny:

```bash
gsutil iam get gs://slowianske-audio
```

### Problem: Baza danych nie łączy się

Sprawdź connection name:

```bash
gcloud sql instances describe slowianske-db --format='value(connectionName)'
```

---

## 📚 Więcej Informacji

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud Storage](https://cloud.google.com/storage/docs)
