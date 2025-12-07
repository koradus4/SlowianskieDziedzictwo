# Używamy lekkiego obrazu Python 3.12
FROM python:3.12-slim

# Ustawienia dla Cloud Run
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Katalog roboczy
WORKDIR /app

# Kopiuj requirements i zainstaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiuj cały projekt
COPY . .

# Stwórz foldery (jeśli używasz lokalnie, w Cloud będą ignorowane)
RUN mkdir -p audio logs

# Uruchom aplikację na porcie z zmiennej środowiskowej PORT
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
