# Słowiańskie Dziedzictwo 🗡️⚔️

**Gra Fabularna RPG z AI (Gemini 2.5) + Polski TTS**

Zanurz się w świecie dawnej Polski, gdzie magia splata się z historią! Gra fabularna napędzana sztuczną inteligencją Google Gemini 2.5 z polskim syntezatorem mowy.

---

## 🎮 Opis

**Słowiańskie Dziedzictwo** to tekstowa gra RPG osadzona w X-wiecznej Polsce, w czasach Mieszka I i zjednoczenia plemion słowiańskich. Wciel się w postać z jednego z pięciu plemion i przeżyj epicką przygodę kierowaną przez AI Mistrza Gry.

### ✨ Główne Cechy

- 🤖 **AI Mistrz Gry** - Google Gemini 2.5 Flash generuje dynamiczną narrację
- 🎙️ **Polski TTS** - Synteza mowy z wieloma głosami (narrator, NPC, postacie)
- 📖 **System Zapisu/Wczytywania** - Zapisz swoją przygodę i wróć do niej później
- ⚔️ **System Walki** - Taktyczne starcia z wrogami
- 👥 **Towarzysze Drużyny** - Rekrutuj sojuszników do pomocy
- 💰 **Handel i Ekwipunek** - Kupuj przedmioty, zarządzaj inwentarzem z ładownością
- 🗺️ **Eksploracja** - Podróżuj po historycznych lokacjach Polski
- 🎲 **System Statystyk** - Siła, Zręczność, Wytrzymałość, Inteligencja, Charyzma, Szczęście

---

## 🛠️ Technologie

- **Backend:** Python 3.12 + Flask
- **AI:** Google Gemini 2.5 Flash (z fallbackiem na Hugging Face)
- **TTS:** Google Text-to-Speech (wielogłosowy)
- **Baza Danych:** SQLite
- **Frontend:** HTML5 + Jinja2 + Vanilla JavaScript
- **Logging:** Strukturalne logi JSON + game.log

---

## 📋 Wymagania

- Python 3.10+
- Klucz API Google Gemini ([pobierz tutaj](https://makersuite.google.com/app/apikey))
- (Opcjonalnie) Token Hugging Face dla fallbacku

---

## 🚀 Instalacja

### 1. Sklonuj repozytorium

```bash
git clone https://github.com/koradus4/SlowianskieDziedzictwo.git
cd SlowianskieDziedzictwo
```

### 2. Utwórz wirtualne środowisko

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# lub
source .venv/bin/activate  # Linux/Mac
```

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 4. Skonfiguruj zmienne środowiskowe

Utwórz plik `.env` w głównym katalogu projektu:

```env
GEMINI_API_KEY=AIzaSy...  # Twój klucz API Google Gemini
GEMINI_MODEL=gemini-2.5-flash  # Model (domyślnie gemini-2.5-flash)
HF_API_TOKEN=hf_...  # (Opcjonalnie) Token Hugging Face dla fallbacku
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2  # Model HF (opcjonalnie)
```

**Lub ustaw zmienne systemowe (Windows):**

```powershell
setx GEMINI_API_KEY "AIzaSy..."
setx GEMINI_MODEL "gemini-2.5-flash"
```

### 5. Uruchom grę

```bash
python app.py
```

Gra będzie dostępna pod adresem: **http://127.0.0.1:5000**

---

## 🎯 Jak Grać

1. **Stwórz Postać** - Wybierz plemię (Polanie, Wiślanie, Ślężanie, Mazowszanie, Pomorzanie), klasę (Wojownik, Kupiec, Druid, Kowal, Łowca) i imię
2. **Rozpocznij Przygodę** - AI Mistrz Gry przedstawi początek historii
3. **Podejmuj Decyzje** - Wpisuj swoje akcje lub wybieraj z sugerowanych opcji
4. **Walcz i Eksploruj** - Stawiaj czoła wrogom, odkrywaj lokacje, rozwiązuj zagadki
5. **Zapisuj Postępy** - Użyj systemu zapisu aby nie stracić swojej przygody

---

## 📂 Struktura Projektu

```
SlowianskieDziedzictwo/
├── app.py                 # Główna aplikacja Flask
├── game_master.py         # AI Mistrz Gry (Gemini + HF)
├── tts_engine.py          # Synteza mowy (Google TTS)
├── database.py            # Obsługa bazy danych SQLite
├── game_logger.py         # System logowania
├── items.py               # Definicje przedmiotów
├── requirements.txt       # Zależności Python
├── templates/             # Szablony HTML (Jinja2)
│   ├── index.html
│   ├── tworzenie_postaci.html
│   ├── gra.html
│   └── ...
├── audio/                 # Wygenerowane pliki audio TTS
├── logs/                  # Logi sesji (JSON + text)
└── game.db                # Baza danych SQLite
```

---

## 🎭 Plemiona i Klasy

### Plemiona:
- **Polanie** 🏛️ - Główne plemię Mieszka I (bonus: Charyzma +2, Siła +1)
- **Wiślanie** 📚 - Plemię z południa (bonus: Inteligencja +2, Wytrzymałość +1)
- **Ślężanie** ⛰️ - Plemię zachodnie (bonus: Siła +2, Zręczność +1)
- **Mazowszanie** 🌲 - Plemię wschodnie (bonus: Zręczność +2, Szczęście +1)
- **Pomorzanie** ⚓ - Plemię nadbałtyckie (bonus: Wytrzymałość +2, Inteligencja +1)

### Klasy:
- **Wojownik** ⚔️ - Mistrz broni (HP +10, Siła +2)
- **Kupiec** 💰 - Handlarz (Złoto +30, Charyzma +2)
- **Druid** 🌿 - Znawca magii i przyrody (Inteligencja +3, HP +5)
- **Kowal** 🔨 - Rzemieślnik (Siła +2, Wytrzymałość +2)
- **Łowca** 🏹 - Tropiciel (Zręczność +3, Szczęście +1)

---

## 🔧 Panel Administracyjny

Gra posiada wbudowane endpointy administracyjne:

### Przełączanie Modelu AI (bez restartu serwera)
```bash
# Sprawdź aktualny model
curl http://127.0.0.1:5000/admin/model

# Zmień model
curl -X POST http://127.0.0.1:5000/admin/model \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash"}'
```

### Statystyki Użycia
```bash
curl http://127.0.0.1:5000/admin/usage
```

---

## 🐛 Rozwiązywanie Problemów

### Błąd 429 / Quota Exceeded
- **Problem:** Przekroczono limit API Gemini
- **Rozwiązanie:** 
  - Sprawdź quota w [Google AI Studio](https://makersuite.google.com/)
  - Przełącz na inny model: `gemini-2.5-flash` lub `gemini-1.5-flash`
  - Skonfiguruj fallback na Hugging Face (ustaw `HF_API_TOKEN`)

### Audio się nie odtwarza
- **Problem:** Autoplay zablokowany przez przeglądarkę
- **Rozwiązanie:** Kliknij na odtwarzacz audio aby rozpocząć odtwarzanie

### Gra nie generuje tekstu
- **Problem:** Brak klucza API lub błędna konfiguracja
- **Rozwiązanie:** 
  - Sprawdź zmienne środowiskowe `GEMINI_API_KEY`
  - Sprawdź logi w `logs/game.log`
  - Otwórz konsolę przeglądarki (F12) i sprawdź błędy

---

## 📝 Licencja

MIT License - możesz swobodnie używać, modyfikować i dystrybuować projekt.

---

## 🙏 Podziękowania

- **Google Gemini** - za potężne AI do generowania narracji
- **Google Cloud TTS** - za polski syntezator mowy
- **Społeczność Open Source** - za narzędzia i biblioteki

---

## 🤝 Współpraca

Chętnie przyjmę Pull Requesty! Jeśli masz pomysły na ulepszenia:

1. Fork repozytorium
2. Utwórz branch (`git checkout -b feature/NowaFunkcja`)
3. Commit zmian (`git commit -m 'Dodano nową funkcję'`)
4. Push do brancha (`git push origin feature/NowaFunkcja`)
5. Otwórz Pull Request

---

## 📧 Kontakt

Masz pytania? Znalazłeś bug? Otwórz [Issue](https://github.com/koradus4/SlowianskieDziedzictwo/issues)!

---

**Miłej zabawy w świecie Słowiańskiego Dziedzictwa!** ⚔️🛡️🏰
