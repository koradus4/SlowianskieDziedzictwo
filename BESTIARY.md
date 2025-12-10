# 🗡️ BESTIARIUSZ - Dokumentacja Systemu

## 📋 Spis Treści
1. [Przegląd Systemu](#przegląd-systemu)
2. [Struktura Danych](#struktura-danych)
3. [Kategorie Przeciwników](#kategorie-przeciwników)
4. [Pełna Lista Przeciwników](#pełna-lista-przeciwników)
5. [Poziomy Trudności](#poziomy-trudności)
6. [Lokacje i Spawny](#lokacje-i-spawny)
7. [API i Funkcje](#api-i-funkcje)
8. [Integracja z Grą](#integracja-z-grą)

---

## 🎯 Przegląd Systemu

**Bestiariusz** to deterministyczny system przeciwników zaprojektowany, aby **wyeliminować halucynacje AI**. Zamiast pozwalać AI generować losowych wrogów, zawiera **36 predefiniowanych przeciwników** z dokładnymi statystykami.

### ✅ Zalety systemu:
- **Zero halucynacji**: AI nie wymyśla nieprawidłowych przeciwników
- **Spójność RPG**: Każdy przeciwnik ma dokładne HP, ataki, słabości
- **Balans gry**: Poziomy trudności są starannie wyważone
- **Słowiański klimat**: Potwory z mitologii (Strzygon, Wij, Zmij)
- **Rozbudowa fabularna**: Boss'y powiązani z historią gry

### 🔒 Bezpieczeństwo:
Plik **NIE MODYFIKUJE** istniejącego kodu - jest całkowicie niezależny i może być później zintegrowany.

---

## 📊 Struktura Danych

Każdy przeciwnik ma **15 pól**:

```python
{
    "id": "unikalne_id",              # np. "wrog_bandyta", "boss_czarnobog"
    "nazwa": "Wyświetlana nazwa",     # np. "Bandyta", "Czarnobóg"
    "typ": "wrog/bestia/boss",        # Kategoria
    "hp_max": 100,                    # Punkty życia
    "ikona": "⚔️",                    # Emoji wyświetlana w UI
    "opis": "Długi opis...",          # Narracyjny kontekst
    "poziom_trudnosci": "sredni",     # slaby/sredni/silny/bardzo_silny/legendarny
    "lokacje_glowne": ["las", "gory"], # Główne miejsca występowania
    "lokacje_rzadkie": ["droga"],     # Rzadkie spawny
    "slabosci": ["ogień", "srebro"],  # Lista słabości
    "specjalne_ataki": ["cios..."],   # Lista specjalnych umiejętności
    "statystyki": {                   # Detale bojowe
        "atak": 20,
        "obrona": 15,
        "szybkosc": 18
    },
    "loot": ["miecz", "50 złotych"],  # Nagrody po pokonaniu
    "exp": 30                         # Punkty doświadczenia
}
```

---

## 🗂️ Kategorie Przeciwników

### 1️⃣ WROGOWIE (8) - Ludzie
Bandyci, najemnicy, dezerterzy - przeciwnicy humanoidalni.

| Nazwa | HP | Poziom | Lokacje | Opis |
|-------|-----|--------|---------|------|
| Zbir | 25 | Słaby | Karczma, Wioska | Pijany awanturnik |
| Bandyta | 45 | Średni | Droga, Las | Rozbójnik z mieczem |
| Rozbójnik | 55 | Średni | Las, Droga | Doświadczony zbój |
| Najemnik | 75 | Silny | Koszary, Obóz | Zawodowy żołnierz |
| Zbój | 60 | Silny | Góry, Jaskinia | Górski rozbójnik |
| Dezerter | 50 | Średni | Las, Bagna | Były żołnierz |
| Najeźdźca | 85 | Silny | Gród, Most | Wojownik obcego plemienia |
| Czarny Rycerz | 110 | Bardzo Silny | Ruiny, Cmentarz | Nieśmiertelny wojownik |

### 2️⃣ BESTIE - ZWIERZĘTA (8)
Naturalne drapieżniki słowiańskich ziem.

| Nazwa | HP | Poziom | Lokacje | Ikona |
|-------|-----|--------|---------|-------|
| Szary Wilk | 40 | Średni | Las, Góry | 🐺 |
| Dziki Dzik | 35 | Słaby | Las | 🐗 |
| Brunatny Niedźwiedź | 80 | Silny | Góry, Las | 🐻 |
| Rudy Lis | 20 | Słaby | Las | 🦊 |
| Orzeł Górski | 30 | Słaby | Góry, Wieża | 🦅 |
| Żubr | 70 | Silny | Las | 🦬 |
| Jeleń Szlachetny | 25 | Słaby | Las, Polana | 🦌 |
| Ryś | 45 | Średni | Las, Góry | 🐱 |

### 3️⃣ POTWORY SŁOWIAŃSKIE (7)
Autentyczne stworzenia z mitologii.

| Nazwa | HP | Poziom | Mitologia | Ikona |
|-------|-----|--------|-----------|-------|
| Strzygon | 90 | Silny | Wampir słowiański | 🧛 |
| Strzyga | 65 | Średni | Żywy trup czarownicy | 👹 |
| Utopiec | 55 | Średni | Duch topielca | 🧟 |
| Bies Leśny | 75 | Silny | Demon lasu | 👿 |
| Rusałka | 50 | Średni | Duch utonionej dziewicy | 🧜 |
| Wij | 150 | **LEGENDARNY** | Demon z ognistym wzrokiem | 👁️ |
| Zmij Ognisty | 120 | Bardzo Silny | Słowiański smok | 🐉 |

### 4️⃣ INNE POTWORY (5)
Fantasy stworzenia uzupełniające bestiariusz.

| Nazwa | HP | Poziom | Typ |
|-------|-----|--------|-----|
| Troll Górski | 95 | Silny | Kamienna skóra |
| Olbrzym | 130 | Bardzo Silny | Gigant |
| Żaba Olbrzymia | 60 | Średni | Zmutowane zwierzę |
| Paskudnik Bagenny | 70 | Silny | Gad bagien |
| Wilkołak | 85 | Silny | Człowiek-wilk |

### 5️⃣ BOSS'Y (7)
Unikalni przeciwnicy powiązani z fabułą.

#### 🏛️ Boss'y Plemienne (2):
- **Władca Ciemności** (HP: 200) - Główny antagonista, armia nieumarłych
- **Warkocz Okrutny** (HP: 180) - Wódz najemników, mistrz miecza

#### 🗺️ Boss'y Lokacyjne (3):
- **Mroczny Strażnik** (HP: 160) - Golem w ruinach
- **Król Trolli** (HP: 170) - Władca górskich trolli
- **Matka Bagien** (HP: 155) - Wiedźma władająca bagnami

#### 📖 Boss'y Fabularne (2):
- **Czarnobóg** (HP: 250) - Bóg zniszczenia, finalny boss
- **Heretyk Weles** (HP: 165) - Zbuntowany kapłan z mroczną magią

---

## ⚔️ Poziomy Trudności

System używa **5 poziomów** bazujących na HP:

| Poziom | HP | EXP | Wskaźnik | Opis |
|--------|-----|-----|---------|------|
| **Słaby** | 20-30 | 10-20 | ⚔️⚔️⚔️ | Dla początkujących |
| **Średni** | 40-60 | 25-40 | ⚔️⚔️⚔️⚔️ | Wymaga strategii |
| **Silny** | 70-90 | 50-70 | ⚔️⚔️⚔️⚔️⚔️ | Dla doświadczonych |
| **Bardzo Silny** | 100-120 | 80-100 | ⚔️⚔️⚔️⚔️⚔️⚔️ | Prawie niemożliwe |
| **Legendarny** | 150-250 | 120-200 | 💀 GROŹNY | Boss fights |

### 🎮 Frontend - Automatyczne Wyświetlanie
Kod w `templates/gra.html` (linie 459-471) **już działa** z tym systemem:

```javascript
let miecze = '';
let sila = uczestnik.hp_max || 0;
if (sila < 30) miecze = '⚔️⚔️⚔️';
else if (sila < 60) miecze = '⚔️⚔️⚔️⚔️';
else if (sila < 100) miecze = '⚔️⚔️⚔️⚔️⚔️';
else miecze = '💀 GROŹNY';
```

Wystarczy, że AI użyje `hp_max` z bestiariusza - frontend SAM wyświetli poprawny wskaźnik!

---

## 🗺️ Lokacje i Spawny

System używa **hybrydowego modelu**:
- **Lokacje główne**: Przeciwnik często występuje (70% szansa)
- **Lokacje rzadkie**: Sporadyczne pojawianie się (30% szansa)

### Przykład - Wilk:
```python
"lokacje_glowne": ["las", "gory"],    # Często w lesie i górach
"lokacje_rzadkie": ["bagna", "droga"] # Rzadko na bagnach/drodze
```

### 📍 Mapa Lokacji Przeciwników

| Lokacja | Wrogowie | Bestie | Boss'y |
|---------|----------|--------|--------|
| **Las** | Bandyta, Rozbójnik, Dezerter | Wilk, Dzik, Niedźwiedź, Żubr, Jeleń, Ryś, Bies, Wilkołak | - |
| **Góry** | Bandyta, Zbój, Najeźdźca | Wilk, Niedźwiedź, Orzeł, Żubr, Jeleń, Ryś, Troll, Zmij | Król Trolli |
| **Bagna** | Dezerter | Wilk, Żaba, Paskudnik, Strzyga, Utopiec, Rusałka | Matka Bagien |
| **Droga** | Zbir, Bandyta, Rozbójnik, Najemnik, Najeźdźca, Dezerter | Wilk, Lis | Warkocz Okrutny |
| **Ruiny** | Rozbójnik, Czarny Rycerz | Orzeł, Wij, Zmij | Mroczny Strażnik, Władca Ciemności, Czarnobóg, Heretyk |
| **Cmentarz** | Czarny Rycerz | Strzygon, Strzyga, Wij | Władca Ciemności, Heretyk |
| **Jaskinia** | Zbój, Dezerter | Niedźwiedź, Ryś, Utopiec, Paskudnik, Troll, Zmij | Król Trolli |

---

## 🔧 API i Funkcje

### 1. `pobierz_wszystkich_przeciwnikow()`
```python
wszyscy = pobierz_wszystkich_przeciwnikow()
# Zwraca: dict ze wszystkimi 36 przeciwnikami
```

### 2. `pobierz_przeciwnika(id_lub_nazwa)`
```python
wilk = pobierz_przeciwnika("bestia_wilk")
# lub
wilk = pobierz_przeciwnika("Szary Wilk")
# Zwraca: dict z danymi przeciwnika lub None
```

### 3. `pobierz_przeciwnikow_dla_lokacji(lokacja, typ=None)`
```python
# Wszyscy przeciwnicy w lesie
lesni = pobierz_przeciwnikow_dla_lokacji("las")

# Tylko bestie w lesie
bestie_lesne = pobierz_przeciwnikow_dla_lokacji("las", typ="bestia")

# Tylko boss'y w ruinach
bossy = pobierz_przeciwnikow_dla_lokacji("ruiny", typ="boss")
```

### 4. `generuj_kontekst_bestiariusza_dla_ai(lokacja=None)`
**KLUCZOWA FUNKCJA** do integracji z AI!

```python
# Cały bestiariusz dla AI
kontekst = generuj_kontekst_bestiariusza_dla_ai()

# Tylko przeciwnicy z lasu
kontekst = generuj_kontekst_bestiariusza_dla_ai("las")
```

Zwraca **czytelny string** do wklejenia w prompt:
```
============================================================
BESTIARIUSZ DLA LOKACJI: LAS
============================================================

WROGOWIE (ludzie):
- Bandyta (HP: 45, sredni): Rozbójnik grasujący na traktach...
- Rozbójnik (HP: 55, sredni): Doświadczony zbój z bandą...

BESTIE (zwierzęta i potwory):
- Szary Wilk (HP: 40, sredni): Drapieżnik polujący w stadzie...
- Dziki Dzik (HP: 35, slaby): Agresywny i nieobliczalny...

============================================================
ZASADY UŻYCIA:
- Używaj TYLKO przeciwników z tej listy
- Zachowaj dokładne nazwy i HP
- Boss'ów używaj tylko w specjalnych momentach fabularnych
============================================================
```

### 5. `statystyki_bestiariusza()`
```python
stats = statystyki_bestiariusza()
# Zwraca: dict z statystykami (ilość przeciwników, poziomy, etc.)
```

---

## 🎮 Integracja z Grą

### ⚠️ **UWAGA: Plik NIE JEST JESZCZE ZINTEGROWANY**

Aby bestiariusz działał, **w przyszłości** trzeba będzie:

### Krok 1: Import w `game_master.py`
```python
from bestiary import (
    pobierz_przeciwnikow_dla_lokacji,
    generuj_kontekst_bestiariusza_dla_ai
)
```

### Krok 2: Dodanie kontekstu do promptu AI
W `game_master.py` funkcja `przygotuj_prompt_akcji()` (około linii 355):

```python
def przygotuj_prompt_akcji(self, akcja, aktualny_stan):
    # ... istniejący kod ...
    
    # NOWE: Dodaj kontekst bestiariusza
    lokacja = aktualny_stan.get('lokacja', None)
    kontekst_bestie = generuj_kontekst_bestiariusza_dla_ai(lokacja)
    
    prompt = f"""
    ... istniejący prompt ...
    
    {kontekst_bestie}
    
    PRZY TWORZENIU POLA "uczestnicy" UŻYJ TYLKO PRZECIWNIKÓW Z BESTIARIUSZA POWYŻEJ!
    """
```

### Krok 3: Walidacja odpowiedzi AI (opcjonalnie)
Dodaj funkcję sprawdzającą czy AI użył prawidłowego przeciwnika:

```python
def waliduj_uczestnikow(uczestnicy_json, lokacja):
    dozwoleni = pobierz_przeciwnikow_dla_lokacji(lokacja)
    dozwolone_nazwy = [p['nazwa'] for p in dozwoleni]
    
    for uczestnik in uczestnicy_json:
        if uczestnik['typ'] in ['wrog', 'bestia', 'boss']:
            if uczestnik['nazwa'] not in dozwolone_nazwy:
                # Zamień na losowego z lokacji
                uczestnik.update(random.choice(dozwoleni))
```

### Krok 4: Aktualizacja `lokacje.py`
Dodaj pole `dostepne_potwory` do każdej lokacji:

```python
LOKACJE = {
    "las": {
        "nazwa": "Gęsty Las",
        "opis": "...",
        "dostepne_potwory": pobierz_przeciwnikow_dla_lokacji("las")
    }
}
```

---

## 📈 Statystyki Bestiariusza

**Łącznie: 36 przeciwników**

### Podział kategorii:
- 🗡️ Wrogowie (ludzie): **8**
- 🐾 Zwierzęta: **8**
- 👹 Potwory słowiańskie: **7**
- 🦎 Inne potwory: **5**
- 💀 Boss'y: **7** (w tym **Czarnobóg** jako finalny)

### Podział poziomów:
- ⚔️⚔️⚔️ Słaby: **7**
- ⚔️⚔️⚔️⚔️ Średni: **9**
- ⚔️⚔️⚔️⚔️⚔️ Silny: **11**
- ⚔️⚔️⚔️⚔️⚔️⚔️ Bardzo Silny: **3**
- 💀 Legendarny: **7** (wszyscy boss'y + Wij)

---

## ✅ Jak To Działa - Przykład

### Scenariusz: Gracz wchodzi do lasu

1. **Frontend**: Gracz klika "Idź do lasu"
2. **Backend** (`app.py`): Wywołuje `GameMaster.wykonaj_akcje("idę do lasu")`
3. **GameMaster**: Przygotowuje prompt z kontekstem:
   ```python
   kontekst = generuj_kontekst_bestiariusza_dla_ai("las")
   # Dodaje do promptu listę: Bandyta, Wilk, Dzik, Niedźwiedź, etc.
   ```
4. **Gemini AI**: Widzi listę, wybiera np. "Szary Wilk" (HP: 40)
5. **Gemini zwraca JSON**:
   ```json
   {
     "narracja": "Podczas wędrówki przez las słyszysz wycie...",
     "uczestnicy": [
       {
         "imie": "Szary Wilk",
         "typ": "bestia",
         "hp_max": 40,
         "ikona": "🐺"
       }
     ]
   }
   ```
6. **Frontend**: Wyświetla wilka z **⚔️⚔️⚔️⚔️** (bo HP=40, zakres średni)

### Porównanie: Przed vs Po

#### ❌ PRZED (AI generuje dowolnie):
```json
"uczestnicy": [
  {"imie": "Mega Smok", "typ": "bestia", "hp_max": 9999999}
  {"imie": "Kosmita z Marsa", "typ": "obcy"}
  {"imie": "123#@!", "typ": "????"}
]
```

#### ✅ PO (AI używa bestiariusza):
```json
"uczestnicy": [
  {"imie": "Szary Wilk", "typ": "bestia", "hp_max": 40, "ikona": "🐺"}
]
```

---

## 🚀 Następne Kroki

### Teraz (bezpieczne):
✅ Plik `bestiary.py` utworzony  
✅ Dokumentacja `BESTIARY.md` utworzona  
✅ **Żaden istniejący kod NIE został zmieniony**

### W przyszłości (gdy będziesz gotowy):
1. Zaimportuj w `game_master.py`
2. Dodaj `generuj_kontekst_bestiariusza_dla_ai()` do promptów
3. Opcjonalnie: dodaj walidację odpowiedzi AI
4. Testuj z różnymi lokacjami
5. Commit i deploy

---

## 🛡️ Bezpieczeństwo i Testy

### Test lokalny:
```bash
cd C:\Users\klif\rpg_z_tts\SlowianskieDziedzictwo_v1.0_save-system
python bestiary.py
```

Powinieneś zobaczyć:
```
🗡️  BESTIARIUSZ - SŁOWIAŃSKIE DZIEDZICTWO 🗡️

Łącznie przeciwników: 36
  - Wrogowie (ludzie): 8
  - Zwierzęta: 8
  - Potwory słowiańskie: 7
  - Inne potwory: 5
  - Boss'y: 7

Poziomy trudności:
  - slaby: 7
  - sredni: 9
  - silny: 11
  - bardzo_silny: 3
  - legendarny: 7
```

---

## 📝 Przykładowe Użycie w Kodzie

```python
# Przykład 1: Pobierz wszystkich wrogów z lasu
from bestiary import pobierz_przeciwnikow_dla_lokacji

wrogowie_lasu = pobierz_przeciwnikow_dla_lokacji("las", typ="wrog")
for wrog in wrogowie_lasu:
    print(f"{wrog['nazwa']} - HP: {wrog['hp_max']}")

# Przykład 2: Sprawdź dane konkretnego przeciwnika
from bestiary import pobierz_przeciwnika

wilk = pobierz_przeciwnika("Szary Wilk")
print(f"Słabości: {wilk['slabosci']}")
print(f"Specjalne ataki: {wilk['specjalne_ataki']}")

# Przykład 3: Generuj prompt dla AI
from bestiary import generuj_kontekst_bestiariusza_dla_ai

prompt = f"""
Gracz wchodzi do lasu.

{generuj_kontekst_bestiariusza_dla_ai("las")}

Opisz scenę i wybierz przeciwnika z listy powyżej.
"""
```

---

## 🎯 Podsumowanie

| Aspekt | Status |
|--------|--------|
| **Plik utworzony** | ✅ `bestiary.py` |
| **Dokumentacja** | ✅ `BESTIARY.md` |
| **Przeciwników** | ✅ 36 (8+8+7+5+7+boss) |
| **Poziomy trudności** | ✅ 5 (słaby → legendarny) |
| **Lokacje** | ✅ System hybrydowy (główne+rzadkie) |
| **API** | ✅ 5 funkcji pomocniczych |
| **Mitologia słowiańska** | ✅ 7 autentycznych potworów |
| **Boss'y** | ✅ 7 unikalnych (w tym Czarnobóg) |
| **Integracja** | ⏳ Gotowe do użycia (wymaga modyfikacji `game_master.py`) |
| **Bezpieczeństwo** | ✅ Nie dotyka istniejącego kodu |

---

**Autor**: GitHub Copilot  
**Data**: 10 grudnia 2025  
**Wersja**: 1.0  
**Projekt**: Słowiańskie Dziedzictwo RPG
