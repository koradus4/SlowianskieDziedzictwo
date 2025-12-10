# Słowiańskie Dziedzictwo — Project Overview

⚔️ Kompletny opis projektu, architektury, przepływów danych i wskazówki developerskie.

---

## 1. Cel projektu

Słowiańskie Dziedzictwo to tekstowe RPG osadzone w średniowiecznej (X w.) Polsce, napędzane przez AI (Google Gemini) i korzystające z polskiego TTS. Gra łączy narrację generowaną przez AI z deterministycznym bestiariuszem i sesją gry zapisującą stan kontynuowany między turami.

## 2. Główne komponenty (at a glance)

- `app.py` — Flask webserver, routing, sesje, helpery, zarządzanie HP przeciwników i zwracanie JSON do frontendu
- `game_master.py` — GameMaster: buduje prompty, pyta Gemini / fallback HF, parsuje JSON, waliduje bestiariusz
- `bestiary.py` — Data-driven lista potworów, funkcje pomocnicze (pobierz_przeciwnika, generuj_kontekst_bestiariusza_dla_ai)
- `tts_engine.py` — Synthesizer: Google TTS + helpery multi-voice, zapis i upload audio
- `database.py` — SQLite DB wrapper: postacie, zapisy, historia i wydarzenia
- `items.py` — Lista przedmiotów i ich mechaniki (dmg, DEF, heal)
- `lokacje.py` — Lokacje, NPC, generatory podróży i eventów
- `templates/` — Jinja2 templates: `index.html`, `gra.html`, `tworzenie_postaci.html`, `logi.html` etc.
- `logs/` + `game_logger.py` — strukturalne logi i helpery

---

## 3. Jak działa system akcji (high-level flow)

1. Gracz wykonuje akcję w UI → zapytanie do endpointu `POST /akcja` (app.py)
2. `app.py` buduje kontekst (postać, lokacja, HP przeciwników z `session`) i przekazuje do `GameMaster.akcja()`
3. `game_master.py` generuje prompt, wysyła go do Gemini/HF i otrzymuje surowy tekst
4. `_parsuj_json()` w `GameMaster` wydobywa i waliduje JSON z odpowiedzi Gemini
5. Jeżeli w JSONie są `uczestnicy`, `game_master` uruchamia `_waliduj_uczestnikow_bestiariusza()`, który **zastępuje** pola z bestiariusza, jednocześnie zachowując `hp` i `uid` jeśli AI je podał
6. `app.py` otrzymuje `wynik` (JSON) i wywołuje `przetworz_hp_przeciwnikow(uczestnicy, narracja)`
   - Funkcja zarządza sesją `session['przeciwnicy_hp']`, inicjalizuje nowych przeciwników, aktualizuje HP (priorytet: AI-provided `hp`, fallback: regex detect z narracji)
   - Dla każdego uczestnika zostaje przypisany `uid` (jeśli AI go nie doda → generujemy `uuid`)
7. `app.py` zwraca JSON z `tekst`, `audio`, `uczestnicy` (z `hp` i `uid`) i `opcje` → frontend renderuje

---

## 4. Endpointy (wybrane)

- `GET /` — strona główna
- `GET /gra` — ładuje stronę gry
- `POST /stworz_postac` — tworzy postać (index)
- `POST /rozpocznij_przygode` — inicjalizuje grę / rozpoczyna przygodę
- `POST /akcja` — key endpoint: przetwarzanie akcji użytkownika (AI)
- `GET /stan_gry` — pobiera aktualny stan gry do frontendu
- `POST /zapisz` i `GET /wczytaj` — zapisy i wczytywanie
- `GET /audio/<plik>` — pobiera plik audio

---

## 5. Mechaniki gry (ważne detale)

- Statystyki: Siła, Zręczność, Wytrzymałość, Inteligencja, Charyzma, Szczęście (generowane przy tworzeniu postaci)
- Ekwipunek: Lista prostych przedmiotów; funkcja `stackuj_ekwipunek()` w `app.py` obsługuje stackowanie
- Ładowność: `oblicz_ladownosc(postac)` uwzględnia worki i wierzchowce (koń/ów)
- Walka:
  - `GameMaster` instruowany jest, by zwracać `uczestnicy` z `hp` i `hp_max` w JSONie
  - `przetworz_hp_przeciwnikow` utrzymuje HP w `session['przeciwnicy_hp']`
  - Priorytet aktualizacji: AI `hp` → fallback: regex parsowanie narracji (wzorce opisowe)
  - Unikalne ID: `uid` w `uczestnik` + klucz sesji `f"{typ}_{imie}_{uid}"` zapewnia niezależne HP dla identycznych przeciwników
  - Jeśli HP spadnie ≤ 0 → gracz dostaje informację i przeciwnik zostaje usunięty z sesji

---

## 6. AI (Game Master)

- `game_master.py` używa Google Gemini (`gemini-2.5-flash`) z fallbackem na Model Hugging Face
- Tworzy rozbudowane prompty:
  - Kontekst lokacji, bestiariusza, aktualne HP przeciwników
  - Instrukcja: AI **musi** zwrócić JSON z kluczami: `narracja`, `narrator`, `uczestnicy`, `opcje`, `hp_gracza`, `lokacja` itd.
- Parsowanie JSON: `_parsuj_json()` zawiera defensywne auto-naprawy JSON (znalezienie bloku code, naprawa braków klamer)
- Walidacja: `_waliduj_uczestnikow_bestiariusza()` zamienia przeciwników na canonical dane z `bestiary.py` (zachowywanie `hp` i `uid` jeśli AI je poda)

---

## 7. TTS (Text-to-Speech)

- `tts_engine.py` wspiera Google Cloud TTS i lokalne generowanie multi-voice (sklejanie segmentów)
- Pliki audio zapisywane do `audio/` i (opcjonalnie) przesyłane do Cloud Storage (konfigurowalne w `CLOUD_DEPLOYMENT.md`)
- `TTSEngine.syntezuj_multi_voice(tekst)` generuje nagranie narracji i NPC

---

## 8. Bestiariusz

- `bestiary.py` zawiera listę predefiniowanych przeciwników (ok. 35-36 entry) z polami: `id`, `nazwa`, `typ`, `hp_max`, `poziom_trudnosci`, `lokacje`, `slabosci`, `loot`, `exp`, `opis` i `statystyki`.
- Funkcje: `pobierz_przeciwnika`, `pobierz_przeciwnikow_dla_lokacji`, `pobierz_wszystkich_przeciwnikow`, `generuj_kontekst_bestiariusza_dla_ai` (przydatne do tworzenia promptów)
 - Zalecana praktyka: wybierać przeciwników z bestiariusza w promptach i w ai walidacji

### 8.1 Szczegóły Bestiariusza

 - Kategoriami są: Wrogowie (ludzie), Bestie (zwierzęta), Potwory słowiańskie, Inne potwory, Boss'y.
 - Poziomy trudności: słaby, średni, silny, bardzo_silny, legendarny — określone głównie przez `hp_max` i `statystyki`.
 - Każdy entry ma `id`, `nazwa`, `typ`, `hp_max`, `ikona`, `opis`, `poziom_trudnosci`, `lokacje_glowne`, `lokacje_rzadkie`, `slabosci`, `specjalne_ataki`, `statystyki`, `loot`, `exp`.
 - `generuj_kontekst_bestiariusza_dla_ai(lokacja=None)` zwraca czytelny fragment do wstrzyknięcia w prompt, ograniczający AI do listy dozwolonych przeciwników oraz powiązanych statystyk (HP/level/weakness).

### 8.2 Przykłady i API

```
from bestiary import pobierz_przeciwnika, pobierz_przeciwnikow_dla_lokacji, generuj_kontekst_bestiariusza_dla_ai

wilk = pobierz_przeciwnika("Szary Wilk")
lista = pobierz_przeciwnikow_dla_lokacji("las", typ="bestia")
prompt_kontekst = generuj_kontekst_bestiariusza_dla_ai("las")
```

Zaleca się: gdy `GameMaster` tworzy prompt, wstrzyknąć `kontekst_bestiariusza` tylko dla aktualnej lokacji, żeby AI nie używało potworów z innych regionów.
> NOTE: The content of the standalone `BESTIARY.md` has been merged into this `PROJECT_OVERVIEW.md` and the canonical data remain in `bestiary.py`. The doc file `BESTIARY.md` has been removed from the repo to avoid duplication.

---

## 9. Lokacje (Plan implementacji)

Sekcja Lokacji pochodzi z `lokacje.py` i planu implementacji: jest ona deterministyczna i ma na celu powstrzymanie AI przed wymyślaniem nowych miast, budynków i NPC.
> NOTE: The content of the standalone `PLAN_LOKACJI.md` has been merged into this `PROJECT_OVERVIEW.md` and the canonical data are in `lokacje.py`. The doc file `PLAN_LOKACJI.md` has been removed from the repo to avoid duplication.

Główne elementy:
 - 5 plemion/miast (Polanie/Gniezno, Wiślanie/Kraków, Pomorzanie/Wolin, Mazowszanie/Płock, Ślężanie/Ślęża)
 - 15 typów budynków w każdej miejscowości (karczma, kuźnia, targ, świątynia, ratusz, itp.)
 - 15 NPC na miasto (ok. 75 łącznie) — każdy z unikalnym `id`, imieniem, funkcją, lokalizacją i koszt_rekrutacji
 - Lokacje pomocnicze (las, bagna, góry, jaskinie, ruiny, drogi itp.) i `MAPA_PODROZY` z dystansami i eventami

### 9.1 Fakty implementacyjne i API

 - W `lokacje.py` są:
   - `BUDYNKI_DEFINICJE`, `PLEMIONA`, `LOKACJE_POMOCNICZE`, `MAPA_PODROZY`
   - funkcje: `pobierz_lokacje_gracza`, `pobierz_npc_w_lokalizacji`, `oblicz_podróż`, `generuj_event_podrozy`, `pobierz_budynek`, `znajdz_npc_po_id`, `rekrutuj_npc`

### 9.2 Integracja z AI i flow gry

 - `game_master.py` powinien wstrzykiwać `kontekst_lokacji` (wynik `pobierz_lokacje_gracza`) do SYSTEM_PROMPT dla każdego zapytania; dzięki temu AI otrzymuje tyko dozwolone nazwy lokacji i NPC.
 - Podczas podróży `oblicz_podróż` i `generuj_event_podrozy` mogą reprezentować probabilistyczne eventy zależne od dystansu i trasy.
 - Aby AI nie halucynowało: `SYSTEM_PROMPT` zawiera wyraźne instrukcje: "UŻYWAJ TYLKO LOKACJI I NPC WYMIENIONYCH W KONTEKŚCIE".

---

---

## 9. Database

- `database.py` — SQLite wrapper
  - Tworzy tabele: `postacie`, `zapis`, `wydarzenia` podczas `Database.inicjalizuj()`
  - API: `zapisz_postac`, `wczytaj_postac`, `aktualizuj_postac`, `zapisz_historie`, `pobierz_wydarzenia` itp.

---

## 10. Logger i Debug

- `game_logger.py` zapisuje logi do `logs/` w JSON (wiele helperów używanych przez app i GameMaster)
- Wskazówki debugowe:
  - Sprawdź `logs/game.log` i `logs/session_*.json`
  - Flask session pliki znajdują się w `flask_session/` — przydane do usuwania sesji (cache issues)
  - `przetworz_hp_przeciwnikow` loguje new enemies i HP changes (istotne podczas testów)

---

## 11. Frontend

- `templates/gra.html` renderuje:
  - Lista `uczestnicy` z `hp`, `hp_max`, `uid` — panele z `data-uid` do identyfikacji
  - `opcje`: przyciski do wyboru akcji
  - Audio (TTS) automatycznie odtwarzane po zaakceptowaniu akcji
- Styl: prosty CSS, gradientowe HP bars (zielony→żółty→czerwony)

---

## 12. Deployment (Cloud & Local)

- Lokalnie:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
# visit http://127.0.0.1:5000
```

- Cloud Run (opis: `CLOUD_DEPLOYMENT.md`):
  - Zbuduj kontener (Dockerfile) i skonfiguruj Cloud Storage dla audio
  - Cloud Build używa `cloudbuild.yaml` do deployu
  - GitHub integration: Commit/push to `main` triggers Cloud Build via `cloudbuild.yaml` (automatic build + deploy to Cloud Run). This CI step is configured to build a Docker image, run tests (if present), and deploy the new version to Cloud Run.
  - Placement: This behavior is part of the *deployment workflow* — it is triggered by a `git push` and is safe to use for production deploys.

---

## 13. Najważniejsze pliki i ich rola (quick map)

- `app.py`: Server + logika HTTP + helpery i HP system
- `game_master.py`: AI prompt & parsing; walidacja JSON
- `bestiary.py`: Data - canonical enemies
- `tts_engine.py`: TTS handling
- `database.py`: DB wrapper
- `items.py`: Item definitions
- `lokacje.py`: Map & location logic
- `templates/*.html`: Front-end UI
- `logs/`, `flask_session/` — debugging / sessions

---

## 14. Rozszerzanie gry — developer tips

1. **Dodanie nowego przeciwnika:**
   - Dodaj wpis do `bestiary.py` (unikalny `id`, `nazwa`, `hp_max`, `typ`, `poziom_trudnosci`, `lokacje`, `statystyki`, `loot`)
  - Zaktualizuj testy i dokumentację w `PROJECT_OVERVIEW.md` (jeśli jest dokumentowany ręcznie)

2. **Dodanie nowego przedmiotu:**
   - Dodaj do `PRZEDMIOTY` w `items.py` ze wszystkimi właściwościami i ewentualnymi efektami

3. **Dodanie nowej lokacji / NPC:**
   - Zaktualizuj `lokacje.py` → `POBIERZ_...` oraz `lokacja` kontekst w `GameMaster`

4. **Testy automatyczne:**
   - Brak pełnych testów unitowych; można dodać pytest z przypadkami: backend endpoints, HP update, session persistence

---

## 15. Najważniejsze edge case'y i dlaczego system działa

- **Duplicate Names**: Fixed by `uid` per participant — previously, 2 identyczne imiona dzieliły HP
- **AI JSON missing `hp`:** fallback to narrative regex
- **Session clearing**: removing `flask_session/*` i restart server to clear inconsistent states
- **Validation**: `_waliduj_uczestnikow_bestiariusza()` ensures no unknown enemies appear

---

## 16. Notatki o zmianach, które zostały wprowadzone (fixes)

- Naprawiłem problem gdzie `hp` generowane przez AI było tracone podczas walidacji i przetwarzania (zachowujemy `hp` i `uid`)
- Dodałem `uid` do `uczestnicy` i używam `typ_imie_uid` jako klucza sesji, teraz każdy przeciwnik jest śledzony niezależnie
- Dodałem `przetworz_hp_przeciwnikow()` w `app.py` z priorytetem AI 'hp' + regex fallback

---

## 17. Debug i szybkie komendy (developer)

- Uruchom lokalnie:
```powershell
.venv\Scripts\activate
python app.py
```

- Zrestartuj serwer i wyczyść sesje:
```powershell
Remove-Item -Path "flask_session\*" -Force
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
python app.py
```

- Sprawdź logi:
```powershell
Get-Content logs\game.log -Tail 200
```

- Wypchnij co zostało zmodyfikowane na GitHub:
```powershell
git add -A
git commit -m "Opis zmian w systemie HP, walidacja bestiariusza, uid" 
git push origin main
```

---

## 18. Where to start when continuing development

1. Przeczytaj `PROJECT_OVERVIEW.md` i `README.md`
2. Przetestuj lokalnie i obserwuj `logs/game.log`
3. Otwórz `game_master.py` i zapoznaj się z `_parsuj_json()` oraz `akcja()`
4. W razie konfliktów sesji — wyczyść `flask_session/`
5. Aby dodać testy, zaimplementuj pytest dla `przetworz_hp_przeciwnikow` oraz `GameMaster._parsuj_json` i `walidacja`

---

## 19. Kontakt / Maintainer

- Repozytorium: `github.com/koradus4/SlowianskieDziedzictwo`
- Maintainer: `koradus4` (root branch: `main`)

---

Jeśli chcesz, mogę teraz:
- dodać prosty `pytest` harness dla HP systemu
- dodać dokumentację developerską do `CONTRIBUTING.md`
- dodać `PROJECT_OVERVIEW.md` do `README.md` jako link

Powiedz którą z tych opcji chcesz, a przygotuję kolejny PR lub commit.
