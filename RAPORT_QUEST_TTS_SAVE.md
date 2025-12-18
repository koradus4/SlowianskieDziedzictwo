# 📋 RAPORT TECHNICZNY: Questy, Save System i Głosy TTS

**Data:** 18 grudnia 2025  
**Temat:** Analiza i rozwiązania dla systemu questów, zapisów i wielogłosowego TTS  
**Przygotowano dla:** Laika (wyjaśnienia krok po kroku)

---

## 🎯 PODSUMOWANIE WYKONAWCZE (Dla Laika)

### Co działa dobrze ✅
1. **Zapisywanie podstawowych danych** - HP, złoto, ekwipunek, lokacja zapisują się poprawnie
2. **Autosave** - gra automatycznie tworzy kopię zapasową co turę
3. **System questów GŁÓWNY** - AI generuje zadania dla gracza
4. **Wielogłosowe TTS** - kod wspiera różne głosy dla różnych postaci

### Co nie działa ❌
1. **Questy giną po wczytaniu** - quest aktywny NIE jest przywracany z bazy
2. **Brak różnych głosów męskich/kobiecych** - wszyscy mówią tym samym głosem
3. **Brak systemu questów pobocznych** - tylko jeden quest naraz
4. **Tabela `questy` NIE jest używana** - istnieje w bazie, ale kod jej ignoruje

---

## 🔍 CZĘŚĆ 1: SYSTEM QUESTÓW - ANALIZA

### Jak to działa TERAZ (uproszczenie)

```
┌─────────────────────────────────────────────────────────┐
│ GRACZ ROZMAWIA Z KAPŁANEM                               │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ AI (Gemini) generuje:                                   │
│ - Narrację: "Kapłan daje Ci zadanie..."                │
│ - Quest: "Oczyść święty gaj pod Gnieznem"              │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Frontend (strona www) pokazuje quest w UI               │
│ session['postac']['quest_aktywny'] = "Oczyść gaj..."   │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ AUTOSAVE - zapis do bazy danych                         │
│ ✅ Zapisuje: HP, złoto, lokację                         │
│ ✅ TERAZ ZAPISUJE: quest_aktywny (po naprawie!)         │
└─────────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│ GRACZ WCZYTUJE GRĘ                                      │
│ ✅ Przywraca: HP, złoto, lokację                        │
│ ✅ TERAZ PRZYWRACA: quest_aktywny                       │
└─────────────────────────────────────────────────────────┘
```

### Problem 1: **QUEST GINIE PO WCZYTANIU** ❌

**Co się dzieje:**
1. AI generuje quest: `"quest_aktywny": "Zabij 3 wilki w lesie"`
2. Quest zapisuje się do sesji: `session['postac']['quest_aktywny']`
3. **AUTOSAVE zapisuje do bazy** - kolumna `quest_aktywny` ISTNIEJE (dodana w migracji)
4. ✅ **PROBLEM NAPRAWIONY** - wczytanie przywraca quest z bazy

**Dlaczego to było naprawione:**
```python
# database.py - linia 186
cursor.execute("ALTER TABLE postacie ADD COLUMN quest_aktywny TEXT")

# database.py - linia 230 - zapisywanie
postac.get('quest_aktywny')  # ✅ zapisuje

# database.py - wczytywanie
row['quest_aktywny']  # ✅ przywraca
```

### Problem 2: **BRAK QUESTÓW POBOCZNYCH** ⚠️

**Obecna sytuacja:**
- Gracz może mieć **tylko 1 quest naraz** (`quest_aktywny`)
- Nie ma listy ukończonych questów
- Nie ma nagradzania za questy
- Tabela `questy` w bazie **ISTNIEJE**, ale **KOD JEJ NIE UŻYWA**

**Dlaczego to problem:**
W prawdziwej grze RPG gracz powinien mieć:
- **Quest główny** (fabularny): "Zjednocz Polskę"
- **Questy poboczne** (3-5 naraz): "Zbierz 10 ziół", "Zabij bandytę"
- **Dziennik questów** - lista zakończonych zadań

---

## 🔍 CZĘŚĆ 2: SYSTEM TTS (GŁOSY) - ANALIZA

### Jak POWINNO działać (wielogłosowe TTS)

```
AI generuje narrację w formacie:

**Narrator:** Wchodzisz do kuźni. Przy kowadle stoi wielki mężczyzna.

**Bogdan [M]:** "Witaj wędrowcze! Szukasz broni?"

**Gracz:** Podchodzisz bliżej i oglądasz miecze.

**Żywia [K]:** "Może dam Ci zniżkę, jeśli pomożesz mojemu ojcu."
```

### Jak to NAPRAWDĘ działa

**1. LOKALNIE (Piper TTS):**
```python
# tts_engine.py - linia 364
def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
    return 'jarvis'  # ❌ ZAWSZE zwraca ten sam głos!
```

**Problem:**
- Kod PARSUJE dialogi (`_parsuj_dialogi`)
- Kod ROZPOZNAJE kto mówi (Narrator, NPC [M], NPC [K])
- Ale funkcja `_okresl_glos()` **IGNORUJE to wszystko** i zwraca `'jarvis'`

**Dlaczego:**
```python
# Komentarz w kodzie (linia 363):
# "Upraszczamy: niezależnie od mówiącego zwracamy jarvis, 
#  by uniknąć braków modeli"
```
Czyli: programista wyłączył różne głosy, bo bał się że brakuje plików modeli.

**2. W CHMURZE (Google Cloud TTS):**
```python
# tts_engine.py - linia 305-342
def _parsuj_dialogi_cloud(self, tekst: str, plec_gracza: str):
    # ✅ POPRAWNIE rozpoznaje:
    # - narrator → "pl-PL-Wavenet-B" (męski głęboki)
    # - gracz_m → "pl-PL-Wavenet-C" (męski spokojny)
    # - gracz_k → "pl-PL-Wavenet-E" (kobieta delikatna)
    # - npc_m → "pl-PL-Wavenet-D" (męski energiczny)
    # - npc_k → "pl-PL-Wavenet-A" (kobieta wyrazista)
```

**Wniosek:**
- **Google Cloud TTS działa poprawnie** ✅
- **Piper lokalnie NIE DZIAŁA** (zwraca jeden głos) ❌

---

## 🔍 CZĘŚĆ 3: SYSTEM ZAPISÓW - ANALIZA

### Co jest zapisywane ✅

```sql
-- Tabela: postacie
imie              -- "Wojciech"
plec              -- "mezczyzna" / "kobieta"
lud               -- "Polanie"
klasa             -- "Wojownik"
hp                -- 73 (obecne HP)
hp_max            -- 100
poziom            -- 1
doswiadczenie     -- 0
zloto             -- 45
statystyki        -- JSON: {sila: 10, zrecznosc: 8...}
ekwipunek         -- JSON: ["Miecz", "Chleb"...]
towarzysze        -- JSON: [{imie: "Bogdan", hp: 25...}...]
przeciwnicy_hp    -- JSON: {enemy_id: 40}
lokacja           -- "Gniezno"
typ_zapisu        -- "autosave" / "manual"
quest_aktywny     -- "Zabij 3 wilki" ✅ DZIAŁA!
```

```sql
-- Tabela: ai_context (pamięć AI)
historia_compressed    -- Cała rozmowa z AI (gzip)
ostatnie_opcje         -- ["Zaatakuj", "Uciekaj", "Rozejrzyj się"]
ostatni_uczestnicy     -- JSON: [{imie: "Wilk", typ: "bestia"...}]
```

### Co NIE jest zapisywane (ale to OK) ℹ️

1. **Audio URL** - nagranie głosowe (można wygenerować ponownie)
2. **Ładowność** - przeliczana z ekwipunku
3. **Obrazenia w turze** - tylko efekt wizualny

---

## 🛠️ CZĘŚĆ 4: ROZWIĄZANIA PROBLEMÓW

### PROBLEM 1: Questy poboczne ⚠️

**Stan obecny:**
- ✅ Quest główny działa (`quest_aktywny`)
- ❌ Brak questów pobocznych
- ❌ Tabela `questy` nie jest używana

**Rozwiązanie A - SZYBKIE (1 godzina pracy):**

Dodaj do `postacie` kolumnę `questy_poboczne` jako JSON:

```python
# database.py - migracja
cursor.execute("ALTER TABLE postacie ADD COLUMN questy_poboczne TEXT DEFAULT '[]'")

# Struktura JSON:
questy_poboczne = [
    {
        "id": 1,
        "nazwa": "Zbierz 10 ziół",
        "opis": "Zielarz w Gnieźnie potrzebuje 10 ziół leczniczych",
        "status": "aktywny",  # aktywny / ukończony / nieudany
        "postep": 7,          # Zebrano 7/10
        "cel": 10,
        "nagroda": "50 złota + Mikstura zdrowia"
    },
    {
        "id": 2,
        "nazwa": "Zabij bandytę",
        "status": "ukończony"
    }
]
```

**Zalety:**
- Szybkie do wdrożenia
- Wszystko w jednym rekordzie bazy
- Łatwe zapisywanie i wczytywanie

**Wady:**
- Limit ~5-10 questów naraz (JSON może się rozrosnąć)
- Trudniej wyszukiwać questy w bazie

---

**Rozwiązanie B - PROFESJONALNE (3-4 godziny pracy):**

Użyj istniejącej tabeli `questy`:

```python
# database.py - nowa funkcja
def dodaj_quest(postac_id: int, nazwa: str, opis: str) -> int:
    conn = self._polacz()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO questy (postac_id, nazwa, opis, status)
        VALUES (?, ?, ?, 'aktywny')
    """, (postac_id, nazwa, opis))
    conn.commit()
    quest_id = cursor.lastrowid
    conn.close()
    return quest_id

def pobierz_aktywne_questy(postac_id: int) -> list:
    conn = self._polacz()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM questy 
        WHERE postac_id = ? AND status = 'aktywny'
        ORDER BY created_at DESC
    """, (postac_id,))
    questy = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questy

def ukoncz_quest(quest_id: int, nagroda: str = None):
    conn = self._polacz()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE questy 
        SET status = 'ukończony' 
        WHERE id = ?
    """, (quest_id,))
    conn.commit()
    conn.close()
```

**Zalety:**
- Nieograniczona liczba questów
- Łatwe filtrowanie (aktywne/ukończone)
- Historia wszystkich questów gracza
- Można dodać więcej pól (nagroda, deadline...)

**Wady:**
- Więcej kodu do napisania
- Więcej zapytań do bazy

---

### PROBLEM 2: Brak różnych głosów (Piper) ❌

**Diagnoza:**
Kod CELOWO wyłączył różne głosy w linii 364:

```python
def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
    return 'jarvis'  # ❌ TUTAJ PROBLEM!
```

**Rozwiązanie SZYBKIE (15 minut):**

Przywróć oryginalną logikę:

```python
def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
    """Dobiera głos na podstawie mówiącego"""
    speaker_lower = speaker.lower()
    
    # Narrator
    if 'narrator' in speaker_lower:
        return 'jarvis'  # Głęboki męski głos
    
    # Gracz
    if 'gracz' in speaker_lower:
        return 'meski' if plec_gracza == 'mezczyzna' else 'zenski'
    
    # NPC - sprawdź oznaczenie [M] lub [K]
    if '[m]' in speaker_lower:
        return 'darkman'  # Męski NPC
    elif '[k]' in speaker_lower:
        return 'justyna'  # Kobieta NPC
    
    # Domyślnie narrator
    return 'jarvis'
```

**WARUNEK:** Musisz mieć pliki modeli głosów w folderze:
```
PodcastGenerator/
├── voices/
│   ├── jarvis/pl_PL-jarvis_wg_glos-medium.onnx
│   ├── meski/pl_PL-meski_wg_glos-medium.onnx
│   ├── zenski/pl_PL-zenski_wg_glos-medium.onnx
│   ├── justyna/pl_PL-justyna_wg_glos-medium.onnx
│   └── darkman/pl_PL-darkman-medium.onnx
```

**Sprawdź czy masz te pliki:**
```powershell
# Uruchom w PowerShell
Get-ChildItem "C:\Users\klif\rpg_z_tts\PodcastGenerator\voices" -Recurse -Filter "*.onnx"
```

**Jeśli NIE masz plików:**
1. Pobierz modele Piper z: https://github.com/rhasspy/piper/releases
2. Szukaj modeli polskich (`pl_PL-*`)
3. Wypakuj do `PodcastGenerator/voices/`

---

### PROBLEM 3: Google Cloud TTS działa, ale... 💰

**Stan:**
- ✅ Google Cloud TTS DZIAŁA poprawnie (5 różnych głosów)
- ⚠️ Wymaga konta Google Cloud (PŁATNE!)
- ⚠️ Koszt: ~$4 za 1 milion znaków (ok. $0.004 za 1000 znaków)

**Czy to dużo?**
- Przeciętna narracja: 200 znaków = **$0.0008** (mniej niż 1 grosz)
- 1000 tur gry: ~200,000 znaków = **$0.80** (80 groszy)

**Wniosek:** Google TTS jest tani, ale wymaga konfiguracji i karty kredytowej.

---

## 📊 CZĘŚĆ 5: REKOMENDACJE (CO ZROBIĆ)

### Priorytet 1: ✅ **Quest główny NAPRAWIONY**
- [x] Kolumna `quest_aktywny` dodana do bazy
- [x] Zapisywanie działa
- [x] Wczytywanie działa

**STATUS: ✅ GOTOWE**

---

### Priorytet 2: ⚠️ **Dodaj questy poboczne**

**Decyzja do podjęcia:**
- **Opcja A:** Szybka (JSON w `questy_poboczne`) ← ZALECANE dla MVP
- **Opcja B:** Profesjonalna (tabela `questy`)

**Moja rekomendacja:** Opcja A (szybsza), później można zmigrować do Opcji B

---

### Priorytet 3: ⚠️ **Napraw głosy Piper (lokalnie)**

**Kroki:**
1. Sprawdź czy masz pliki `.onnx` w `PodcastGenerator/voices/`
2. Jeśli NIE - pobierz z repozytorium Piper
3. Zmień kod w `tts_engine.py` (funkcja `_okresl_glos`)

**Czas:** 30 minut - 1 godzina

---

### Priorytet 4: ℹ️ **Dodaj UI dla questów**

**Frontend (HTML/JavaScript):**
```html
<!-- Panel questów -->
<div id="panel-questow">
    <h3>Questy</h3>
    
    <!-- Quest główny -->
    <div class="quest quest-glowny">
        <span class="quest-typ">⭐ GŁÓWNY</span>
        <h4>Zjednocz Polskę</h4>
        <p>Postęp: 1/5 plemion</p>
    </div>
    
    <!-- Questy poboczne -->
    <div class="quest quest-poboczny aktywny">
        <span class="quest-typ">📜 POBOCZNY</span>
        <h4>Zbierz 10 ziół</h4>
        <p>Postęp: 7/10</p>
    </div>
    
    <div class="quest quest-poboczny ukończony">
        <span class="quest-typ">✅ UKOŃCZONY</span>
        <h4>Zabij bandytę</h4>
    </div>
</div>
```

---

## 🔧 CZĘŚĆ 6: KOD DO WDROŻENIA

### 1. Napraw głosy Piper (tts_engine.py)

**GDZIE:** `tts_engine.py`, linia ~364

**ZMIEŃ Z:**
```python
def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
    """Wymusza użycie jednego głosu (jarvis) dla całej narracji."""
    return 'jarvis'
```

**NA:**
```python
def _okresl_glos(self, speaker: str, plec_gracza: str) -> str:
    """Dobiera głos na podstawie mówiącego"""
    speaker_lower = speaker.lower()
    
    # Narrator - głęboki męski
    if 'narrator' in speaker_lower:
        return 'jarvis'
    
    # Gracz - zależnie od płci
    if 'gracz' in speaker_lower:
        if plec_gracza == 'kobieta':
            return 'zenski'
        else:
            return 'meski'
    
    # NPC - sprawdź oznaczenie [M]/[K]
    if '[m]' in speaker_lower:
        return 'darkman'  # Mężczyzna NPC
    elif '[k]' in speaker_lower:
        return 'justyna'  # Kobieta NPC
    
    # Domyślnie narrator
    return 'jarvis'
```

**UWAGA:** Upewnij się że masz pliki modeli w `PodcastGenerator/voices/`!

---

### 2. Dodaj questy poboczne (OPCJA A - szybka)

**KROK 1:** Dodaj kolumnę do bazy

```python
# database.py - w funkcji inicjalizuj(), po linii 189
try:
    cursor.execute("ALTER TABLE postacie ADD COLUMN questy_poboczne TEXT DEFAULT '[]'")
    conn.commit()
except:
    conn.rollback()  # Kolumna już istnieje
```

**KROK 2:** Zapisywanie questów pobocznych

```python
# database.py - w zapisz_postac(), linia ~210
# DODAJ 'questy_poboczne' do INSERT:

base_query = f"""
    INSERT INTO postacie 
    (imie, plec, lud, klasa, hp, hp_max, poziom, doswiadczenie, 
     zloto, statystyki, ekwipunek, towarzysze, przeciwnicy_hp, 
     lokacja, typ_zapisu, quest_aktywny, questy_poboczne)
    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, 
            {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
"""

params = (
    # ... istniejące parametry ...
    postac.get('quest_aktywny'),
    json.dumps(postac.get('questy_poboczne', []))  # NOWY
)
```

**KROK 3:** Wczytywanie

```python
# database.py - w wczytaj_postac(), linia ~250
# JSON deserializacja (jak ekwipunek):
postac['questy_poboczne'] = json.loads(row.get('questy_poboczne') or '[]')
```

**KROK 4:** AI - aktualizuj prompt

```python
# game_master.py - SYSTEM_PROMPT (linia ~20)
# DODAJ do formatu JSON:

"questy_poboczne": [
    {
        "id": 1,
        "nazwa": "Nazwa questa",
        "status": "aktywny",  # aktywny / ukończony
        "postep": 7,
        "cel": 10
    }
],
```

---

## 📈 CZĘŚĆ 7: TESTY (Jak sprawdzić czy działa)

### Test 1: Quest główny
```
1. Zagraj 3 tury
2. Przyjmij quest od NPC (np. kapłan)
3. Sprawdź UI - quest powinien się pokazać
4. Zapisz grę (autosave lub ręcznie)
5. Odśwież stronę (F5)
6. ✅ Quest nadal widoczny? = DZIAŁA
```

### Test 2: Głosy TTS (Piper lokalnie)
```
1. Ustaw tryb lokalny (wyłącz Cloud TTS)
2. Zagraj turę z dialogiem NPC:
   - **Narrator:** Tekst...
   - **Bogdan [M]:** "Dialog..."
   - **Żywia [K]:** "Dialog..."
3. ✅ Słychać różne głosy? = DZIAŁA
4. ❌ Jeden głos dla wszystkich? = Brakuje modeli lub kod nie naprawiony
```

### Test 3: Questy poboczne (po wdrożeniu)
```
1. Przyjmij quest główny: "Zjednocz Polskę"
2. Przyjmij quest poboczny #1: "Zbierz 10 ziół"
3. Przyjmij quest poboczny #2: "Zabij bandytę"
4. Sprawdź ekwipunek - zbierz 7 ziół
5. Ukończ quest #2 (zabij bandytę)
6. Zapisz grę
7. Wczytaj grę
8. ✅ Sprawdź:
   - Quest główny: aktywny
   - Quest #1: aktywny, postęp 7/10
   - Quest #2: ukończony
```

---

## 🎓 CZĘŚĆ 8: WYJAŚNIENIA DLA LAIKA

### Czym jest "quest aktywny"?
To jest **zadanie główne**, które gracz wykonuje w danym momencie. Na przykład:
- "Oczyść święty gaj"
- "Znajdź 5 ziół"
- "Pokonaj smoka"

### Czym są "questy poboczne"?
To **dodatkowe zadania**, które gracz może wykonywać równocześnie. Na przykład:
- Quest główny: "Zjednocz Polskę"
- Poboczny 1: "Zbierz 10 ziół dla zielarza" (nagroda: 50 złota)
- Poboczny 2: "Zabij bandytę terroryzującego wieś" (nagroda: Miecz)

### Czym jest "autosave"?
To **automatyczny zapis** gry. Co turę (gdy klikasz akcję), gra tworzy kopię zapasową w bazie danych. Dzięki temu jeśli zamkniesz przeglądarkę, możesz wrócić i kontynuować.

### Czym jest TTS?
**Text-to-Speech** = zamiana tekstu na mowę. Program czyta na głos narrację gry.

**Wielogłosowe TTS** = różne postacie mówią różnymi głosami:
- Narrator: głęboki męski głos
- Bohater mężczyzna: spokojny męski
- Bohaterka kobieta: kobiecy delikatny
- NPC mężczyzna: energiczny męski
- NPC kobieta: wyrazisty kobiecy

### Czym jest "JSON"?
Format zapisu danych. Na przykład:
```json
{
    "imie": "Wojciech",
    "hp": 73,
    "ekwipunek": ["Miecz", "Tarcza"]
}
```
To jest jak "słownik" - każda rzecz ma nazwę i wartość.

---

## ✅ CHECKLIST: Co zrobić krok po kroku

### Zadanie 1: Napraw głosy Piper (30 min)
- [ ] Sprawdź czy masz pliki `.onnx` w `PodcastGenerator/voices/`
- [ ] Jeśli nie - pobierz z https://github.com/rhasspy/piper/releases
- [ ] Otwórz `tts_engine.py`
- [ ] Znajdź funkcję `_okresl_glos` (linia ~364)
- [ ] Zamień `return 'jarvis'` na pełną logikę (kod powyżej)
- [ ] Zapisz i zrestartuj serwer
- [ ] Testuj - zagraj turę z NPC

### Zadanie 2: Dodaj questy poboczne (1-2 godziny)
- [ ] Otwórz `database.py`
- [ ] Dodaj kolumnę `questy_poboczne` (kod powyżej)
- [ ] Zaktualizuj `zapisz_postac()` - dodaj parametr
- [ ] Zaktualizuj `wczytaj_postac()` - deserializuj JSON
- [ ] Otwórz `game_master.py`
- [ ] Zaktualizuj SYSTEM_PROMPT - dodaj pole `questy_poboczne`
- [ ] Otwórz `app.py`
- [ ] Dodaj endpoint `/questy` (zwraca listę questów)
- [ ] Stwórz UI w HTML (panel questów)
- [ ] Testuj - przyjmij 3 questy, zapisz, wczytaj

### Zadanie 3: Dodaj UI dla questów (1 godzina)
- [ ] Otwórz szablon HTML (`templates/gra.html`)
- [ ] Dodaj panel questów (kod powyżej)
- [ ] Dodaj CSS (stylowanie)
- [ ] Dodaj JavaScript (aktualizacja przy akcji)
- [ ] Testuj - sprawdź czy questy się pokazują

---

## 🚨 NAJCZĘSTSZE BŁĘDY I JAK JE NAPRAWIĆ

### Błąd 1: "Quest zniknął po wczytaniu"
**Diagnoza:** Kolumna `quest_aktywny` nie istnieje w bazie  
**Rozwiązanie:** Uruchom migrację
```python
python migrate_db.py
```

### Błąd 2: "Wszyscy mówią tym samym głosem"
**Diagnoza:** Brak plików modeli lub kod zwraca tylko `'jarvis'`  
**Rozwiązanie:**
1. Sprawdź czy `_okresl_glos()` ma pełną logikę (nie tylko `return 'jarvis'`)
2. Sprawdź czy pliki `.onnx` istnieją w `PodcastGenerator/voices/`

### Błąd 3: "Google TTS nie działa"
**Diagnoza:** Brak konfiguracji Google Cloud lub braku biblioteki `google-cloud-texttospeech`  
**Rozwiązanie:**
```powershell
pip install google-cloud-texttospeech google-cloud-storage
# Ustaw zmienną środowiskową z kluczem API
```

### Błąd 4: "Questy poboczne się nie zapisują"
**Diagnoza:** Kolumna `questy_poboczne` nie istnieje LUB kod nie serializuje JSON  
**Rozwiązanie:**
1. Sprawdź bazę: `SELECT * FROM postacie` - czy kolumna istnieje?
2. Sprawdź kod: `json.dumps(postac.get('questy_poboczne', []))`

---

## 📞 PODSUMOWANIE

### Co działa ✅
1. Quest główny (`quest_aktywny`) - zapisywanie i wczytywanie **DZIAŁA**
2. Google Cloud TTS - 5 różnych głosów **DZIAŁA**
3. Autosave - tworzenie kopii zapasowej co turę **DZIAŁA**
4. Podstawowe dane (HP, złoto, ekwipunek) **DZIAŁA**

### Co wymaga naprawy ⚠️
1. **Piper TTS** - zwraca tylko jeden głos (`jarvis`)
2. **Questy poboczne** - brak systemu (tylko 1 quest naraz)
3. **UI questów** - brak panelu z listą zadań

### Rekomendowane działania (w kolejności)
1. ✅ **Najpierw:** Napraw głosy Piper (30 min)
2. ⚠️ **Potem:** Dodaj questy poboczne (2 godziny)
3. ℹ️ **Na koniec:** Stwórz UI dla questów (1 godzina)

**Szacowany czas:** 3-4 godziny pracy

---

**Koniec raportu**  
Jeśli masz pytania - pisz!
