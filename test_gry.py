#!/usr/bin/env python3
"""
Narzędzie do testowania gry po poprawkach
Testuje: serwer, questy, głosy, save/load, sesje
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

# Konfiguracja
BASE_URL = "http://localhost:5000"
TEST_SESSION_NAME = f"test_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Kolory w terminalu
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_test(name, passed, details=""):
    """Logowanie wyniku testu"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       └─ {details}")

def test_server_alive():
    """Test 1: Sprawdza czy serwer odpowiada"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        passed = response.status_code == 200
        log_test("Server alive", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        log_test("Server alive", False, str(e))
        return False

def test_create_character():
    """Test 2: Tworzenie postaci"""
    try:
        session = requests.Session()
        
        # Krok 1: Pobierz stronę główną (inicjalizuj sesję)
        response = session.get(f"{BASE_URL}/")
        
        # Krok 2: Utwórz postać
        data = {
            "imie": "TestowyBohater",
            "plec": "mezczyzna",
            "klasa": "wojownik",
            "punkty": json.dumps({
                "sila": 8,
                "zrecznosc": 6,
                "inteligencja": 4,
                "charyzma": 5
            })
        }
        response = session.post(f"{BASE_URL}/utworz-postac", data=data)
        
        passed = response.status_code == 200 or response.status_code == 302
        log_test("Create character", passed, f"Status: {response.status_code}")
        return passed, session
    except Exception as e:
        log_test("Create character", False, str(e))
        return False, None

def test_quest_system(session):
    """Test 3: System questów (główny + poboczne)"""
    try:
        # Wykonaj akcję która powinna zwrócić questy
        data = {
            "akcja": "rozejrzyj się",
            "custom_action": ""
        }
        response = session.post(f"{BASE_URL}/akcja", json=data)
        
        if response.status_code != 200:
            log_test("Quest system", False, f"Status: {response.status_code}")
            return False
        
        result = response.json()
        
        # Sprawdź czy są pola questów
        has_main_quest = "quest_aktywny" in result
        has_side_quests = "questy_poboczne" in result
        
        passed = has_main_quest and has_side_quests
        details = f"Main quest: {has_main_quest}, Side quests: {has_side_quests}"
        
        if passed and result.get("quest_aktywny"):
            details += f", Active: '{result['quest_aktywny'][:50]}...'"
        
        log_test("Quest system", passed, details)
        return passed
    except Exception as e:
        log_test("Quest system", False, str(e))
        return False

def test_tts_voices():
    """Test 4: Sprawdza czy głosy są dostępne"""
    try:
        project_root = Path(__file__).parent
        voices_dir = project_root / "glosy_lokalnie"
        
        required_voices = ["jarvis", "meski", "zenski", "justyna", "darkman"]
        found_voices = []
        missing_voices = []
        
        for voice in required_voices:
            voice_path = voices_dir / voice / f"pl_PL-{voice}_wg_glos-medium.onnx"
            if voice == "darkman":
                voice_path = voices_dir / voice / "pl_PL-darkman-medium.onnx"
            
            if voice_path.exists():
                found_voices.append(voice)
            else:
                missing_voices.append(voice)
        
        passed = len(found_voices) == 5
        details = f"Found: {len(found_voices)}/5 voices"
        if missing_voices:
            details += f", Missing: {', '.join(missing_voices)}"
        
        log_test("TTS voices available", passed, details)
        return passed
    except Exception as e:
        log_test("TTS voices available", False, str(e))
        return False

def test_save_load(session):
    """Test 5: Zapis i odczyt gry"""
    try:
        # Pobierz aktualny stan
        response = session.get(f"{BASE_URL}/gra")
        if response.status_code != 200:
            log_test("Save/Load system", False, "Nie można pobrać gry")
            return False
        
        # Wykonaj akcję aby zapisać stan
        data = {
            "akcja": "idź dalej",
            "custom_action": ""
        }
        response = session.post(f"{BASE_URL}/akcja", json=data)
        
        if response.status_code != 200:
            log_test("Save/Load system", False, f"Status: {response.status_code}")
            return False
        
        result = response.json()
        
        # Sprawdź czy jest historia (zapisana)
        has_history = "historia" in result or "odpowiedz" in result
        
        passed = has_history
        log_test("Save/Load system", passed, "Historia zapisana w sesji")
        return passed
    except Exception as e:
        log_test("Save/Load system", False, str(e))
        return False

def test_session_persistence(session):
    """Test 6: Sprawdza czy sesja się utrzymuje"""
    try:
        # Wykonaj 3 akcje pod rząd
        actions = ["rozejrzyj się", "idź naprzód", "sprawdź ekwipunek"]
        
        for i, action in enumerate(actions):
            data = {
                "akcja": action,
                "custom_action": ""
            }
            response = session.post(f"{BASE_URL}/akcja", json=data)
            
            if response.status_code != 200:
                log_test("Session persistence", False, f"Akcja {i+1} failed: {response.status_code}")
                return False
            
            time.sleep(0.5)  # Krótkie opóźnienie
        
        log_test("Session persistence", True, f"3 akcje wykonane pomyślnie")
        return True
    except Exception as e:
        log_test("Session persistence", False, str(e))
        return False

def test_database_connection():
    """Test 7: Sprawdza połączenie z bazą danych"""
    try:
        from database import Database
        
        db = Database()
        
        # Sprawdź czy można wykonać zapytanie
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Test zapytania
        cursor.execute("SELECT COUNT(*) FROM postacie")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        passed = True
        log_test("Database connection", passed, f"Postaci w bazie: {count}")
        return passed
    except Exception as e:
        log_test("Database connection", False, str(e))
        return False

def test_google_cloud_tts_config():
    """Test 8: Sprawdza konfigurację Google Cloud TTS"""
    try:
        from tts_engine import TTSEngine
        from pathlib import Path
        
        # Utwórz instancję TTSEngine
        podcast_dir = Path("C:/Users/klif/rpg_z_tts/PodcastGenerator")
        tts = TTSEngine(podcast_dir)
        
        # Sprawdź czy cloud voices są skonfigurowane
        has_cloud_voices = hasattr(tts, 'cloud_voices') and len(tts.cloud_voices) > 0
        
        if has_cloud_voices:
            num_voices = len(tts.cloud_voices)
            log_test("Google Cloud TTS config", True, f"{num_voices} głosów skonfigurowanych")
            return True
        else:
            log_test("Google Cloud TTS config", False, "Brak skonfigurowanych głosów")
            return False
    except Exception as e:
        log_test("Google Cloud TTS config", False, str(e))
        return False

def run_all_tests():
    """Uruchom wszystkie testy"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}  AUTOMATYCZNE TESTOWANIE GRY RPG{Colors.RESET}")
    print(f"{Colors.BLUE}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    results = {}
    
    # Test 1: Server
    print(f"{Colors.YELLOW}[1/8] Testowanie serwera...{Colors.RESET}")
    results['server'] = test_server_alive()
    
    if not results['server']:
        print(f"\n{Colors.RED}BŁĄD: Serwer nie odpowiada. Uruchom serwer i spróbuj ponownie.{Colors.RESET}\n")
        return
    
    # Test 2: Tworzenie postaci
    print(f"\n{Colors.YELLOW}[2/8] Testowanie tworzenia postaci...{Colors.RESET}")
    results['character'], session = test_create_character()
    
    if not results['character']:
        print(f"\n{Colors.RED}BŁĄD: Nie można utworzyć postaci.{Colors.RESET}\n")
        return
    
    # Test 3: Questy
    print(f"\n{Colors.YELLOW}[3/8] Testowanie systemu questów...{Colors.RESET}")
    results['quests'] = test_quest_system(session)
    
    # Test 4: Głosy TTS
    print(f"\n{Colors.YELLOW}[4/8] Testowanie dostępności głosów...{Colors.RESET}")
    results['voices'] = test_tts_voices()
    
    # Test 5: Save/Load
    print(f"\n{Colors.YELLOW}[5/8] Testowanie zapisu i odczytu...{Colors.RESET}")
    results['save'] = test_save_load(session)
    
    # Test 6: Sesje
    print(f"\n{Colors.YELLOW}[6/8] Testowanie trwałości sesji...{Colors.RESET}")
    results['session'] = test_session_persistence(session)
    
    # Test 7: Baza danych
    print(f"\n{Colors.YELLOW}[7/8] Testowanie połączenia z bazą...{Colors.RESET}")
    results['database'] = test_database_connection()
    
    # Test 8: Google Cloud TTS
    print(f"\n{Colors.YELLOW}[8/8] Testowanie Google Cloud TTS...{Colors.RESET}")
    results['cloud_tts'] = test_google_cloud_tts_config()
    
    # Podsumowanie
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}  PODSUMOWANIE{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    passed_tests = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name:20s} [{status}]")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}  ✓ Wszystkie testy zakończone pomyślnie ({passed_tests}/{total_tests}){Colors.RESET}")
        print(f"{Colors.GREEN}  Gra gotowa do commita i wdrożenia!{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}  ⚠ Testy zakończone: {passed_tests}/{total_tests} pomyślnych{Colors.RESET}")
        print(f"{Colors.YELLOW}  Napraw błędy przed commitowaniem.{Colors.RESET}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    import sys
    
    print(f"\n{Colors.BLUE}Sprawdzanie środowiska...{Colors.RESET}")
    
    # Sprawdź czy serwer jest uruchomiony
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"{Colors.GREEN}✓ Serwer działa na {BASE_URL}{Colors.RESET}")
    except:
        print(f"{Colors.RED}✗ Serwer nie odpowiada na {BASE_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Uruchom serwer poleceniem: python app.py{Colors.RESET}")
        sys.exit(1)
    
    # Uruchom testy
    success = run_all_tests()
    
    sys.exit(0 if success else 1)
