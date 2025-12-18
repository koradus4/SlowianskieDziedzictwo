# Instrukcja Testowania

## Szybki start

### 1. Uruchom serwer
```powershell
python app.py
```

### 2. Uruchom testy (w drugim terminalu)
```powershell
python test_gry.py
```

## Co testuje `test_gry.py`?

1. **Server alive** - Sprawdza czy serwer odpowiada na http://localhost:5000
2. **Create character** - Tworzy testową postać (TestowyBohater)
3. **Quest system** - Sprawdza czy questy (główny + poboczne) działają
4. **TTS voices** - Weryfikuje czy wszystkie 5 głosów są dostępne
5. **Save/Load** - Testuje zapis i odczyt stanu gry
6. **Session persistence** - Wykonuje 3 akcje pod rząd (test trwałości sesji)
7. **Database connection** - Sprawdza połączenie z bazą danych
8. **Google Cloud TTS** - Weryfikuje konfigurację Cloud TTS

## Oczekiwany wynik

Wszystkie testy powinny zwrócić **PASS**:

```
============================================================
  AUTOMATYCZNE TESTOWANIE GRY RPG
  2025-12-18 20:30:00
============================================================

[1/8] Testowanie serwera...
✓ PASS | Server alive
       └─ Status: 200

[2/8] Testowanie tworzenia postaci...
✓ PASS | Create character
       └─ Status: 302

[3/8] Testowanie systemu questów...
✓ PASS | Quest system
       └─ Main quest: True, Side quests: True, Active: 'Odnajdź zaginioną relikwię słowiańską...'

[4/8] Testowanie dostępności głosów...
✓ PASS | TTS voices available
       └─ Found: 5/5 voices

[5/8] Testowanie zapisu i odczytu...
✓ PASS | Save/Load system
       └─ Historia zapisana w sesji

[6/8] Testowanie trwałości sesji...
✓ PASS | Session persistence
       └─ 3 akcje wykonane pomyślnie

[7/8] Testowanie połączenia z bazą...
✓ PASS | Database connection
       └─ Postaci w bazie: 12

[8/8] Testowanie Google Cloud TTS...
✓ PASS | Google Cloud TTS config
       └─ 5 głosów skonfigurowanych

============================================================
  PODSUMOWANIE
============================================================

  server               [PASS]
  character            [PASS]
  quests               [PASS]
  voices               [PASS]
  save                 [PASS]
  session              [PASS]
  database             [PASS]
  cloud_tts            [PASS]

============================================================
  ✓ Wszystkie testy zakończone pomyślnie (8/8)
  Gra gotowa do commita i wdrożenia!
============================================================
```

## Rozwiązywanie problemów

### Serwer nie odpowiada
```
✗ FAIL | Server alive
       └─ Connection refused
```

**Rozwiązanie**: Uruchom serwer w pierwszym terminalu:
```powershell
python app.py
```

### Brak głosów
```
✗ FAIL | TTS voices available
       └─ Found: 0/5 voices, Missing: jarvis, meski, zenski, justyna, darkman
```

**Rozwiązanie**: Sprawdź czy folder `glosy_lokalnie/` zawiera wszystkie modele:
```
glosy_lokalnie/
├── darkman/pl_PL-darkman-medium.onnx
├── jarvis/pl_PL-jarvis_wg_glos-medium.onnx
├── justyna/pl_PL-justyna_wg_glos-medium.onnx
├── meski/pl_PL-meski_wg_glos-medium.onnx
└── zenski/pl_PL-zenski_wg_glos-medium.onnx
```

### Session persistence fails
```
✗ FAIL | Session persistence
       └─ Akcja 2 failed: 500
```

**Rozwiązanie**: 
1. Sprawdź logi serwera (terminal gdzie uruchomiony jest `app.py`)
2. Sprawdź czy baza danych nie jest zablokowana
3. Zrestartuj serwer

### Database connection error
```
✗ FAIL | Database connection
       └─ database is locked
```

**Rozwiązanie**:
1. Zamknij wszystkie inne połączenia do bazy (np. DB Browser)
2. Usuń plik `game.db` i pozwól serwerowi utworzyć nowy
3. Sprawdź uprawnienia do zapisu w katalogu projektu

## Uruchamianie pojedynczych testów

Możesz edytować `test_gry.py` i zakomentować niepotrzebne testy w funkcji `run_all_tests()`.

## Testowanie manualne

Jeśli wolisz testować ręcznie:

1. Otwórz http://localhost:5000
2. Utwórz postać
3. Wykonaj kilka akcji (np. "rozejrzyj się", "idź dalej")
4. Sprawdź czy:
   - Questy się pojawiają (panel po prawej)
   - Audio jest generowane (przycisk odtwarzania)
   - Historia się zapisuje (odśwież stronę - sesja powinna zostać)
   - Różne głosy dla różnych postaci

## Deployment na Google Cloud

Po pomyślnych testach:

```powershell
git add .
git commit -m "Opis zmian"
git push origin main
```

Cloud Build automatycznie zdeployuje nową wersję na Cloud Run.

Sprawdź status deployment: https://console.cloud.google.com/cloud-build/
