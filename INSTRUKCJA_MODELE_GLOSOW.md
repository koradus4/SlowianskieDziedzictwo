# 🔊 BRAKUJĄCE MODELE GŁOSÓW - Instrukcja

**Status:** ⚠️ Znaleziono tylko 1 z 5 wymaganych modeli głosów!

---

## 📊 AKTUALNY STAN

### Znalezione modele ✅
- `jarvis` - pl_PL-jarvis_wg_glos-medium.onnx

### Brakujące modele ❌
- `meski` - pl_PL-meski_wg_glos-medium.onnx
- `zenski` - pl_PL-zenski_wg_glos-medium.onnx
- `justyna` - pl_PL-justyna_wg_glos-medium.onnx
- `darkman` - pl_PL-darkman-medium.onnx

---

## ⚠️ CO TO OZNACZA

**Bez pełnych modeli:**
- Wielogłosowe TTS **NIE BĘDZIE DZIAŁAĆ** lokalnie
- Wszystkie postacie będą mówić głosem "jarvis"
- Naprawiony kod w `tts_engine.py` nie zadziała

**Co DZIAŁA:**
- Google Cloud TTS (5 różnych głosów) - jeśli masz konto Google Cloud ✅
- Piper TTS z jednym głosem (jarvis) - ale bez różnic między postaciami ⚠️

---

## 🛠️ ROZWIĄZANIA

### Opcja 1: Pobierz modele Piper (ZALECANE dla gry lokalnej)

**Krok 1: Pobierz modele**

Odwiedź repozytorium Piper:
https://github.com/rhasspy/piper/releases

**Krok 2: Znajdź polskie modele**

Szukaj plików `.tar.gz` z nazwą zawierającą `pl_PL-`:
- `pl_PL-meski_wg_glos-medium.tar.gz`
- `pl_PL-zenski_wg_glos-medium.tar.gz` (jeśli istnieje)
- Inne polskie modele

**Krok 3: Pobierz i wypakuj**

Dla każdego modelu:
```powershell
# Przykład dla modelu "meski"
cd C:\Users\klif\rpg_z_tts\PodcastGenerator\voices

# Utwórz folder
New-Item -ItemType Directory -Path "meski" -Force

# Wypakuj pobrany plik .tar.gz do tego folderu
# (użyj 7-Zip lub innego narzędzia)
```

**Struktura docelowa:**
```
PodcastGenerator/voices/
├── jarvis/
│   └── pl_PL-jarvis_wg_glos-medium.onnx
├── meski/
│   └── pl_PL-meski_wg_glos-medium.onnx
├── zenski/
│   └── pl_PL-zenski_wg_glos-medium.onnx
├── justyna/
│   └── pl_PL-justyna_wg_glos-medium.onnx
└── darkman/
    └── pl_PL-darkman-medium.onnx
```

**⚠️ UWAGA:** Niektóre nazwy modeli mogą się różnić od oczekiwanych przez kod. Jeśli nie znajdziesz dokładnie tych samych nazw, użyj dostępnych polskich modeli i zmień nazwę folderu.

**Przykład:** Jeśli pobierzesz `pl_PL-male-voice-medium.onnx`, możesz:
1. Utworzyć folder `meski`
2. Skopiować tam plik i **ZMIENIĆ NAZWĘ** na `pl_PL-meski_wg_glos-medium.onnx`

---

### Opcja 2: Użyj Google Cloud TTS (wymaga konta płatnego)

**Zalety:**
- ✅ Działa już teraz (kod gotowy)
- ✅ 5 różnych głosów (narrator, gracz M/K, NPC M/K)
- ✅ Wysoka jakość
- ✅ Bez pobierania modeli

**Wady:**
- ❌ Wymaga konta Google Cloud
- ❌ Płatne (choć tanie: ~$4 za 1M znaków)
- ❌ Wymaga internetu

**Jak włączyć:**
```powershell
# Zainstaluj biblioteki
pip install google-cloud-texttospeech google-cloud-storage

# Ustaw zmienne środowiskowe
$env:GCS_BUCKET_NAME = "twoja-nazwa-bucketu"
# Dodaj klucz API do Google Cloud
```

---

### Opcja 3: Pozostaw jeden głos (tymczasowe)

**Jeśli chcesz grać już teraz bez wielogłosowego TTS:**

Kod będzie próbował użyć różnych głosów, ale jeśli nie znajdzie pliku, użyje domyślnego `jarvis`.

**Co się stanie:**
- Narrator: jarvis ✅
- Gracz M: jarvis (powinno być meski) ⚠️
- Gracz K: jarvis (powinno być zenski) ⚠️
- NPC M: jarvis (powinno być darkman) ⚠️
- NPC K: jarvis (powinno być justyna) ⚠️

**Logi pokażą:**
```
Brak modelu głosu: meski
Brak modelu głosu: zenski
...
```

---

## 📝 ALTERNATYWA: Zmień kod na dostępne modele

Jeśli znajdziesz **INNE polskie modele** (nie te które oczekuje kod), możesz dostosować kod:

**1. Sprawdź jakie modele polskie są dostępne:**
https://huggingface.co/rhasspy/piper-voices/tree/main/pl

**2. Pobierz dostępne modele**

**3. Zmień mapowanie w `tts_engine.py` (linia ~40):**

```python
# PRZED (obecne):
self.glosy = {
    "jarvis": self.voices_dir / "jarvis" / "pl_PL-jarvis_wg_glos-medium.onnx",
    "meski": self.voices_dir / "meski" / "pl_PL-meski_wg_glos-medium.onnx",
    "zenski": self.voices_dir / "zenski" / "pl_PL-zenski_wg_glos-medium.onnx",
    "justyna": self.voices_dir / "justyna" / "pl_PL-justyna_wg_glos-medium.onnx",
    "darkman": self.voices_dir / "darkman" / "pl_PL-darkman-medium.onnx"
}

# PO (dostosuj do SWOICH modeli):
self.glosy = {
    "jarvis": self.voices_dir / "jarvis" / "pl_PL-jarvis_wg_glos-medium.onnx",
    "meski": self.voices_dir / "male1" / "pl_PL-NAZWA_MODELU.onnx",  # ZMIEŃ!
    "zenski": self.voices_dir / "female1" / "pl_PL-NAZWA_MODELU.onnx",  # ZMIEŃ!
    "justyna": self.voices_dir / "female2" / "pl_PL-NAZWA_MODELU.onnx",  # ZMIEŃ!
    "darkman": self.voices_dir / "male2" / "pl_PL-NAZWA_MODELU.onnx"  # ZMIEŃ!
}
```

---

## 🔍 JAK ZNALEŹĆ MODELE PIPER

### Metoda 1: GitHub Releases
https://github.com/rhasspy/piper/releases

Szukaj plików `.tar.gz` dla języka polskiego.

### Metoda 2: Hugging Face
https://huggingface.co/rhasspy/piper-voices/tree/main/pl

Przeglądaj foldery, znajdź modele z rozszerzeniem `.onnx`.

### Metoda 3: Piper Samples (posłuchaj głosów)
https://rhasspy.github.io/piper-samples/

Wybierz język "Polish" i posłuchaj przykładów.

---

## 🎯 ZALECENIA

### Dla szybkiego testowania:
✅ **Opcja 3** - Pozostaw jeden głos (jarvis)  
⏱️ Czas: 0 minut  
💰 Koszt: Darmowe  
📊 Jakość: Średnia (brak różnic między postaciami)

### Dla pełnej funkcjonalności (lokalnie):
✅ **Opcja 1** - Pobierz modele Piper  
⏱️ Czas: 30-60 minut  
💰 Koszt: Darmowe  
📊 Jakość: Wysoka (5 różnych głosów)

### Dla produkcji (w chmurze):
✅ **Opcja 2** - Google Cloud TTS  
⏱️ Czas: 30 minut (konfiguracja)  
💰 Koszt: ~$0.80 za 1000 tur gry  
📊 Jakość: Najwyższa (profesjonalne głosy)

---

## 🚨 TROUBLESHOOTING

### "Brak modelu głosu: meski"
**Przyczyna:** Brak pliku `pl_PL-meski_wg_glos-medium.onnx`  
**Rozwiązanie:** Pobierz model lub zmień kod na dostępny model

### "Wszyscy mówią głosem jarvis"
**Przyczyna:** Brak innych modeli  
**Rozwiązanie:** Zobacz Opcja 1 lub Opcja 2 powyżej

### "FileNotFoundError: voices/meski/..."
**Przyczyna:** Nieprawidłowa ścieżka do modelu  
**Rozwiązanie:** Sprawdź czy folder i plik istnieją, popraw nazwę jeśli trzeba

---

**Koniec dokumentu**

Jeśli pobierzesz modele, uruchom ponownie serwer:
```powershell
# Ctrl+C (stop)
python app.py
```
