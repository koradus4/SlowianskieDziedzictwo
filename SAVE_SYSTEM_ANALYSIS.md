# 🔍 Analiza Systemu Zapisu - Co Zapisujemy vs Co Traciny

## ✅ ZAPISYWANE (w autosave)

### 1. **Tabela `postacie`** (zapisz_postac)
- ✅ `imie` - nazwa postaci
- ✅ `plec` - płeć (mezczyzna/kobieta)
- ✅ `lud` - plemię (polanie, pomorzanie...)
- ✅ `klasa` - klasa (wojownik, zielarz...)
- ✅ `hp` - aktualne HP
- ✅ `hp_max` - maksymalne HP
- ✅ `poziom` - poziom postaci
- ✅ `doswiadczenie` - punkty doświadczenia
- ✅ `zloto` - ilość złota
- ✅ `statystyki` - JSON {sila, zrecznosc, inteligencja...}
- ✅ `ekwipunek` - JSON ["Nóż", "Chleb"...]
- ✅ `towarzysze` - JSON [{imie, klasa, hp...}...]
- ✅ `przeciwnicy_hp` - JSON {enemy_id: hp}
- ✅ `lokacja` - nazwa lokacji (Gniezno, Las...)
- ✅ `typ_zapisu` - "autosave"

### 2. **Tabela `ai_context`** (zapisz_ai_context)
- ✅ `historia_compressed` - pełna konwersacja z Gemini (gzip)
- ✅ `ostatnie_opcje` - JSON ["Zaatakuj", "Uciekaj"...]
- ✅ `ostatni_uczestnicy` - JSON [{imie, typ, hp...}...] ← **NOWE!**

### 3. **Tabela `historia`** (zapisz_historie)
- ✅ Historia tekstowa (akcje gracza + narracje AI)

---

## ❌ NIE ZAPISYWANE (generowane na nowo)

### **Z odpowiedzi `/akcja`:**

1. ❌ **`audio`** - URL do pliku MP3 (Google Cloud Storage)
   - **Dlaczego:** Narracja jest w `historia`, TTS można wygenerować ponownie
   - **Skutek:** Brak audio po wczytaniu (trzeba kliknąć "Kontynuuj")

2. ❌ **`quest_aktywny`** - aktualny quest tekstowy
   - **Dlaczego:** Nie ma tabeli `questy` w użyciu!
   - **Skutek:** Po wczytaniu tracisz informację o aktywnym queście
   - **⚠️ PROBLEM:** Quest znika z UI

3. ❌ **`ladownosc`** - {zajete, max}
   - **Dlaczego:** Obliczane dynamicznie z ekwipunku
   - **Skutek:** Brak - przelicza się przy każdym ładowaniu

---

## ⚠️ POTENCJALNE PROBLEMY

### **1. Quest System - KRYTYCZNY BUG**
```javascript
// Frontend otrzymuje:
"quest_aktywny": "Oczyść święty gaj pod Gnieznem"

// Ale nie zapisujemy w bazie!
// Po wczytaniu: quest_aktywny = null
```

**Co się dzieje:**
- Rozpoczynasz quest od kapłana
- Quest pokazuje się w UI
- Zapisujesz grę (autosave)
- Wczytasz → **Quest zniknął!**

**Rozwiązanie:**
- Dodać `quest_aktywny` do tabeli `postacie`
- Lub użyć tabeli `questy` (ale aktualnie nie jest używana)

---

### **2. Audio URL**
```javascript
// Frontend otrzymuje:
"audio": "https://storage.googleapis.com/.../ea81db8e.mp3"

// Nie zapisujemy!
// Po wczytaniu: brak audio dla ostatniej narracji
```

**Co się dzieje:**
- Wczytasz grę → **cisza** (trzeba kliknąć opcję żeby usłyszeć nową narrację)

**Czy naprawić?**
- NIE - nie warto, TTS można wygenerować ponownie jeśli trzeba
- Audio jest w cloud storage więc link będzie działał przez ~30 dni

---

### **3. Obrazenia (damage log)**
```python
# W wynik z AI:
"obrazenia": {
    "cel": "Wilk #1",
    "wartosc": 15,
    "typ": "fizyczne"
}

# NIE ZAPISUJEMY!
# Ale to OK - to tylko efekt wizualny jednej tury
```

**Czy naprawić?**
- NIE - to jednorazowa informacja, nie potrzebna po wczytaniu

---

## 📊 PODSUMOWANIE

### ✅ Dobrze zapisane (100% przywracalne):
- Postać (HP, złoto, lokacja, ekwipunek)
- Towarzysze (imiona, HP, klasy)
- Przeciwnicy HP (wilki, bandyci...)
- **Pełna historia AI** (pamięć rozmowy)
- Ostatnie opcje do wyboru
- **NPC w scenie** (nowość!)

### ⚠️ Wymaga poprawki:
1. **Quest aktywny** - **KRYTYCZNE**
   - Symptom: Quest znika po wczytaniu
   - Fix: Dodać `quest_aktywny TEXT` do `postacie`

### ℹ️ Świadomie pomijane (OK):
- Audio URL (regenerujemy TTS)
- Ładowność (przeliczamy z ekwipunku)
- Obrazenia (efekt jednej tury)

---

## 🔧 REKOMENDOWANE POPRAWKI

### **Priorytet 1: Quest Aktywny**
```sql
-- Migracja
ALTER TABLE postacie ADD COLUMN quest_aktywny TEXT;
```

```python
# database.py - zapisz_postac
params = (
    # ...
    postac.get('quest_aktywny'),  # DODAJ
    # ...
)
```

```python
# app.py - autosave
nowy_postac_id = db.zapisz_postac(postac, typ_zapisu='autosave')
# postac już ma quest_aktywny z wynik['quest_aktywny']
```

### **Priorytet 2: Audio (opcjonalne)**
Jeśli chcesz zachować audio:
```python
# ai_context - dodaj kolumnę
ostatnie_audio TEXT

# Przy zapisie
db.zapisz_ai_context(..., ostatnie_audio=audio_url)
```

---

## 📝 CHECKLIST dla przyszłych feature'ów

Gdy dodajesz nową funkcjonalność do gry, zadaj pytania:

1. ✅ **Czy to stan postaci?** → Dodaj do `postacie`
2. ✅ **Czy to AI/NPC dane?** → Dodaj do `ai_context`
3. ✅ **Czy to historia?** → Dodaj do `historia`
4. ❌ **Czy to jednorazowy efekt?** → Nie zapisuj
5. ❌ **Czy da się przeliczyć z innych danych?** → Nie zapisuj

**Testy po dodaniu zapisu:**
1. Zagraj 3 tury
2. Wczytaj autosave
3. Sprawdź czy **wszystko wygląda tak samo**
   - HP, złoto, lokacja
   - NPC (imiona, ilość)
   - Quest w UI
   - Opcje do wyboru
   - Towarzysze
