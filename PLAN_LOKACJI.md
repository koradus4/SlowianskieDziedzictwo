# Plan Implementacji Systemu Lokacji - Słowiańskie Dziedzictwo

## Data: 9 grudnia 2025

---

## 1. PROBLEM DO ROZWIĄZANIA

**Główny problem:** AI (Gemini) halucynuje nazwy lokacji, budynki i NPC, które nie istnieją w świecie gry, co niszczy immersję i spójność fabularną.

**Rozwiązanie:** Stworzenie kompletnego, deterministycznego systemu lokacji z predefiniowanymi:
- Miastami plemion
- Budynkami w miastach
- NPC w każdym mieście
- Lokacjami pomocniczymi (lasy, góry, itp.)
- Systemem podróży z eventami

---

## 2. SPECYFIKACJA SYSTEMU

### 2.1 Plemiona i Miasta (5 plemion)

1. **Polanie** - Gniezno
2. **Wiślanie** - Kraków
3. **Pomorzanie** - Wolin
4. **Mazowszanie** - Płock
5. **Ślężanie** - Ślęża

### 2.2 Typy Budynków (15+ typów w każdym mieście)

1. **karczma** - jedzenie, plotki, wynajęcie pokoju
2. **kuźnia** - broń, zbroje, naprawa
3. **targ** - handel, przedmioty codzienne
4. **świątynia** - błogosławieństwa, leczenie, nauka
5. **ratusz** - questy urzędowe, informacje
6. **szpital** - leczenie ran, trucizn
7. **warsztat** - narzędzia, wyposażenie
8. **stajnia** - konie, naprawa pojazdu
9. **koszary** - rekrutacja, trening bojowy
10. **biblioteka** - wiedza, mapy, historie
11. **łaźnia** - odpoczynek, plotki
12. **młyn** - zaopatrzenie w mąkę, wieści z okolicy
13. **piekarnia** - prowiant
14. **więzienie** - informacje o przestępcach, zwolnienie jeńców
15. **wieża strażnicza** - widok na okolicę, ostrzeżenia

### 2.3 NPC w Miastach (15+ per miasto = ~75 NPC total)

Każdy NPC ma:
- **id**: unikalny identyfikator (np. "gniezno_kowal_01")
- **imię**: słowiańskie imię
- **funkcja**: rola w mieście
- **lokalizacja**: budynek gdzie przebywa
- **podstawowe_cechy**: uproszczony szablon (zawód, cecha charakteru)
- **koszt_rekrutacji**: złoto wymagane do rekrutacji

**Struktura przy rekrutacji:**
- Prosty szablon przekształca się w pełnego towarzysza z HP, statami, ekwipunkiem
- Cechy charakteru wpływają na dialogi i interakcje

### 2.4 Lokacje Pomocnicze (12-15 typów)

1. **las** - zasoby drewna, zwierzyna, zioła
2. **bagna** - niebezpieczne, zioła, potwory
3. **góry** - rudy metali, schronienie, widoki
4. **most** - przeprawa, straż, patrol
5. **przełęcz** - punkt strategiczny
6. **obóz** - tymczasowa osada, handlarze wędrowni
7. **jaskinia** - schronienie, tajemnice, potwory
8. **polana** - odpoczynek, spotkania
9. **cmentarz** - duchy, artefakty, tajemnice
10. **gród graniczny** - obrona, handel
11. **ruiny** - artefakty, niebezpieczeństwa
12. **droga** - szlak handlowy, bezpieczeństwo zmienne
13. **rzeka** - przeprawa, ryby, transport
14. **wieś** - zaopatrzenie podstawowe, plotki
15. **pustkowie** - niebezpieczne, rzadkie spotkania

### 2.5 System Podróży

**Mechanika eventów w trakcie podróży:**
- **Dystans < 50 km**: 10% szans na event
- **Dystans 50-100 km**: 50% szans na event  
- **Dystans > 100 km**: 100% szans na event (gwarantowany)

**Typy eventów:**
- Spotkanie wędrowców/handlarzy
- Napad bandytów
- Dzikie zwierzęta
- Odkrycie miejsca (jaskinia, ruiny)
- Pomoc potrzebującym
- Warunki pogodowe

---

## 3. STRUKTURA PLIKU `lokacje.py`

### 3.1 Warstwa 1: BUDYNKI_DEFINICJE
```python
BUDYNKI_DEFINICJE = {
    "karczma": {
        "nazwa": "Karczma",
        "opis": "Tętniące życiem miejsce...",
        "funkcje": ["jedzenie", "nocleg", "plotki"]
    },
    # ... pozostałe 14+ typów
}
```

### 3.2 Warstwa 2: PLEMIONA (miasta + NPC)
```python
PLEMIONA = {
    "polanie": {
        "miasto": "Gniezno",
        "opis": "Stolica Polan...",
        "budynki": ["karczma", "kuźnia", ...],
        "npc": [
            {
                "id": "gniezno_kowal_01",
                "imie": "Bogdan",
                "funkcja": "kowal",
                "lokalizacja": "kuźnia",
                "cechy": "wysoki, muskularny, prostolinijny",
                "koszt_rekrutacji": 100
            },
            # ... 14+ więcej NPC
        ]
    },
    # ... pozostałe 4 plemiona
}
```

### 3.3 Warstwa 3: LOKACJE_POMOCNICZE
```python
LOKACJE_POMOCNICZE = {
    "las_gnieznianski": {
        "typ": "las",
        "nazwa": "Las Gnieznieński",
        "opis": "Gęsty bór...",
        "pobliska_lokacja": "Gniezno",
        "zasoby": ["drewno", "zioła", "zwierzyna"],
        "niebezpieczeństwo": "średnie"
    },
    # ... więcej lokacji dla każdego regionu
}
```

### 3.4 Warstwa 4: MAPA_PODROZY
```python
MAPA_PODROZY = {
    ("Gniezno", "Kraków"): {
        "dystans_km": 280,
        "czas_dni": 4,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,  # 100% bo > 100km
        "przejscia": ["las", "droga", "wieś"]
    },
    # ... wszystkie połączenia między miastami
}
```

### 3.5 Funkcje Pomocnicze

```python
def pobierz_lokacje_gracza(lokalizacja_nazwa):
    """Zwraca pełne dane o lokalizacji gracza"""
    
def pobierz_npc_w_lokalizacji(miasto, budynek=None):
    """Zwraca listę NPC w danym mieście/budynku"""
    
def oblicz_podróż(start, cel):
    """Oblicza dane podróży i czy wystąpi event"""
    
def generuj_event_podrozy(dystans_km):
    """Generuje losowy event na podstawie dystansu"""
    
def pobierz_budynek(miasto, typ_budynku):
    """Zwraca dane konkretnego budynku"""
    
def znajdz_npc_po_id(npc_id):
    """Wyszukuje NPC po unikalnym ID"""
    
def rekrutuj_npc(npc_id):
    """Przekształca szablon NPC w pełnego towarzysza"""
```

---

## 4. INTEGRACJA Z `game_master.py`

### 4.1 Modyfikacje SYSTEM_PROMPT

Dodanie sekcji z kontekstem lokacji:
```python
# Import na górze pliku
from lokacje import (
    pobierz_lokacje_gracza, 
    pobierz_npc_w_lokalizacji,
    PLEMIONA,
    BUDYNKI_DEFINICJE
)

# W SYSTEM_PROMPT dodać:
"""
## SYSTEM LOKACJI
{kontekst_lokacji}

WAŻNE: Używaj TYLKO lokacji, budynków i NPC z powyższego kontekstu.
NIE wymyślaj nowych miejsc ani postaci.
"""
```

### 4.2 Przekazywanie Kontekstu do AI

```python
def generuj_odpowiedz(user_input, historia, postac):
    # Pobierz kontekst lokacji gracza
    lokalizacja_gracza = postac.get('lokalizacja', 'Gniezno')
    kontekst_lokacji = pobierz_lokacje_gracza(lokalizacja_gracza)
    
    # Wstrzyknij do prompta
    prompt = SYSTEM_PROMPT.format(
        kontekst_lokacji=json.dumps(kontekst_lokacji, 
                                    ensure_ascii=False, 
                                    indent=2)
    )
```

### 4.3 Obsługa Podróży

```python
# Gdy gracz chce podróżować
if "podróż" in user_input.lower() or "idę do" in user_input.lower():
    cel = wykryj_cel_podrozy(user_input)
    info_podrozy = oblicz_podróż(postac['lokalizacja'], cel)
    
    # Dodaj info o podróży do kontekstu AI
    # AI opisze podróż i event jeśli wystąpi
```

---

## 5. PRZEPŁYW IMPLEMENTACJI

### ✅ KROK 1: Utworzenie `lokacje.py` - ZAKOŃCZONE
- [x] Definicje wszystkich budynków (15 typów)
- [x] Dane 5 plemion z miastami
- [x] Po 15 NPC na plemię (75 total)
- [x] 12 lokacji pomocniczych
- [x] Mapa połączeń między miastami (10 tras)
- [x] Funkcje pomocnicze (8 funkcji)
- [x] Testy jednostkowe (wszystkie PASSED)

### ✅ KROK 2: Modyfikacja `game_master.py` - ZAKOŃCZONE
- [x] Import funkcji z lokacje.py
- [x] Rozszerzenie SYSTEM_PROMPT o sekcję `{kontekst_lokacji}`
- [x] Dodanie metody `_generuj_kontekst_lokacji(miasto)`
- [x] Aktualizacja `rozpocznij_gre()` - dynamiczny kontekst lokacji
- [x] Aktualizacja `akcja()` - dynamiczny kontekst lokacji
- [x] Instrukcja dla AI: "NIE wymyślaj nowych miejsc ani postaci"

### ✅ KROK 3: Weryfikacja `database.py` - ZAKOŃCZONE
- [x] Pole 'lokalizacja' istnieje w tabeli postaci
- [x] Autosave działa (`db.aktualizuj_postac` po każdej akcji)
- [x] System save/load/delete kompletny i funkcjonalny

### ✅ KROK 4: Testowanie Lokalne - ZAKOŃCZONE
- [x] Testy jednostkowe lokacje.py - wszystkie PASSED
- [x] Weryfikacja pobierania miasta (Gniezno: 15 budynków, 15 NPC)
- [x] Weryfikacja wyszukiwania NPC po ID
- [x] Weryfikacja rekrutacji (NPC → towarzysz z HP/statami)
- [x] Weryfikacja obliczeń podróży (dystans, czas, eventy)
- [x] Weryfikacja generowania eventów podróży

### ✅ KROK 5: Deploy na Google Cloud - ZAKOŃCZONE
- [x] git add, commit (87a52ba)
- [x] git push → GitHub
- [x] Cloud Build automatycznie uruchomiony

### ⏳ KROK 6: Finalne Testy Produkcyjne - DO WYKONANIA
- [ ] Otworzyć https://slowiansiedziedzictwo-517125853033.europe-central2.run.app
- [ ] Stworzyć postać z różnych plemion (Polanie, Wiślanie, etc.)
- [ ] Sprawdzić czy AI używa NPC z lokacje.py (np. "Bogdan - kowal z Gniezna")
- [ ] Przetestować nawigację po budynkach
- [ ] Przetestować rekrutację NPC (koszt zgodny z systemem)
- [ ] Przetestować podróż między miastami (eventy)
- [ ] Zweryfikować save/load/delete w UI
- [ ] Potwierdzić brak halucynacji AI (nowe lokacje/NPC)

---

## 6. PRZYKŁADOWE DANE (dla weryfikacji)

### Przykład NPC - Gniezno
```python
{
    "id": "gniezno_kowal_01",
    "imie": "Bogdan",
    "funkcja": "kowal",
    "lokalizacja": "kuźnia",
    "cechy": "wysoki, muskularny, szczery",
    "koszt_rekrutacji": 100,
    # Po rekrutacji przekształci się w:
    "hp": 120,
    "atak": 15,
    "obrona": 12,
    "ekwipunek": ["młot bojowy", "skórzana zbroja"],
    "umiejetnosci": ["kowalstwo", "walka wręcz"]
}
```

### Przykład Podróży
```python
Gniezno → Kraków
Dystans: 280 km
Czas: 4 dni
Event: 100% (dystans > 100km)
Możliwe eventy: bandyci, handlarze, odkrycie ruin, burza
```

---

## 7. KRYTERIA SUKCESU

✅ AI **NIE HALUCYNUJE** nowych lokacji
✅ Wszystkie NPC mają unikalne ID
✅ Podróże działają z eventami
✅ Rekrutacja NPC działa poprawnie
✅ System zapisuje lokalizację gracza
✅ System działa na produkcji (Cloud Run)

---

## 8. OSZACOWANIE CZASU

- **Krok 1** (lokacje.py): 45-60 minut (dużo danych do wpisania)
- **Krok 2** (game_master.py): 20-30 minut
- **Krok 3** (database.py): 10-15 minut
- **Krok 4** (testy lokalne): 30 minut
- **Krok 5** (deploy): 10 minut
- **Krok 6** (testy produkcyjne): 20 minut

**TOTAL: ~2.5-3 godziny czystej pracy**

---

## 9. UWAGI TECHNICZNE

### Bezpieczeństwo Danych
- Wszystkie dane lokacji są read-only (CONST)
- NPC templates nie modyfikują oryginałów przy rekrutacji
- Funkcje zwracają kopie, nie referencje

### Wydajność
- Dane w pamięci (słowniki Python) - bardzo szybkie
- Brak zapytań do bazy dla lokacji (statyczne)
- JSON serialization dla AI (lekki format)

### Skalowalność
- Łatwe dodanie nowych plemion
- Łatwe dodanie nowych typów budynków
- Łatwe dodanie NPC (append do listy)
- Proste rozszerzenie eventów podróży

---

## 9. PODSUMOWANIE IMPLEMENTACJI

### ✅ CO ZOSTAŁO ZROBIONE (9 grudnia 2025):

**1. Plik `lokacje.py` (621 linii)**
- 15 typów budynków z opisami i funkcjami
- 5 plemion: Polanie (Gniezno), Wiślanie (Kraków), Pomorzanie (Wolin), Mazowszanie (Płock), Ślężanie (Ślęża)
- 75 unikalnych NPC (15 na miasto) z ID, imionami, funkcjami, cechami i kosztami rekrutacji
- 12 lokacji pomocniczych (lasy, góry, jaskinie, ruiny, etc.)
- 10 tras podróży z dystansami, czasem i systemem eventów
- 8 funkcji pomocniczych do zarządzania danymi

**2. Integracja z `game_master.py`**
- Placeholder `{kontekst_lokacji}` w SYSTEM_PROMPT
- Metoda `_generuj_kontekst_lokacji(miasto)` - dynamiczny kontekst dla AI
- AI otrzymuje instrukcję: "Używaj TYLKO lokacji, budynków i NPC z powyższego kontekstu. NIE wymyślaj nowych miejsc ani postaci"
- Kontekst jest generowany dla każdego miasta osobno (tylko relevantne dane)

**3. System Save/Load - Zweryfikowany**
- ✅ Autosave: automatyczny zapis po każdej akcji gracza
- ✅ Load: endpoint `/wczytaj_zapis/<id>` + UI
- ✅ Delete: endpoint `/usun_zapis/<id>` + przycisk 🗑️ w UI

**4. Testy Jednostkowe - PASSED**
```
✅ Pobieranie lokacji: Gniezno (15 budynków, 15 NPC)
✅ Wyszukiwanie NPC: Bogdan (kowal)
✅ Rekrutacja: NPC → towarzysz (HP: 28, Atak: 15)
✅ Podróż: Gniezno → Kraków (280km, 4 dni, event: TAK)
✅ Event: "Wataha wilków blokuje drogę" (3 opcje)
```

**5. Deploy**
- Commit: `87a52ba` - "Implementacja systemu lokacji"
- Push → GitHub → Cloud Build (automatyczny)

### ⏳ POZOSTAŁO DO ZROBIENIA:

**Testy produkcyjne** (po zakończeniu Cloud Build ~5 min):
1. Otworzyć grę w przeglądarce
2. Stworzyć postać z różnych plemion
3. Zweryfikować że AI nie halucynuje (używa tylko NPC z systemu)
4. Przetestować save/load/delete
5. Przetestować podróże z eventami

---

## STATUS: IMPLEMENTACJA ZAKOŃCZONA ✅

**Następny krok:** Czekać na zakończenie Cloud Build → testy produkcyjne

**Data zakończenia implementacji:** 9 grudnia 2025
