"""
System logowania dla gry Słowiańskie Dziedzictwo
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json

# Katalog logów
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Konfiguracja loggera
def setup_logger():
    """Konfiguruje system logowania"""
    
    # Format logów
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger główny
    logger = logging.getLogger('SlowianskieDziedzictwo')
    logger.setLevel(logging.DEBUG)
    
    # Handler do pliku (wszystkie logi)
    file_handler = logging.FileHandler(
        LOG_DIR / 'game.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler do konsoli (tylko INFO+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Wymuś flush po każdym logu
    sys.stdout.reconfigure(line_buffering=True)
    
    # Dodaj handlery
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Główny logger
logger = setup_logger()

# Specjalistyczne loggery
game_logger = logging.getLogger('SlowianskieDziedzictwo.game')
ai_logger = logging.getLogger('SlowianskieDziedzictwo.ai')
tts_logger = logging.getLogger('SlowianskieDziedzictwo.tts')
db_logger = logging.getLogger('SlowianskieDziedzictwo.db')


class GameLogger:
    """Klasa do logowania wydarzeń gry"""
    
    def __init__(self):
        self.session_log = []
        self.session_file = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    def log_postac_utworzona(self, postac: dict):
        """Loguje utworzenie postaci"""
        event = {
            "typ": "POSTAC_UTWORZONA",
            "czas": datetime.now().isoformat(),
            "dane": {
                "imie": postac.get('imie'),
                "lud": postac.get('lud_nazwa'),
                "klasa": postac.get('klasa_nazwa'),
                "statystyki": postac.get('statystyki'),
                "hp": postac.get('hp')
            }
        }
        self._zapisz_event(event)
        game_logger.info(f"🎭 Nowa postać: {postac.get('imie')} ({postac.get('lud_nazwa')}, {postac.get('klasa_nazwa')})")
    
    def log_akcja_gracza(self, akcja: str, postac_imie: str = "Gracz"):
        """Loguje akcję gracza"""
        event = {
            "typ": "AKCJA_GRACZA",
            "czas": datetime.now().isoformat(),
            "dane": {
                "postac": postac_imie,
                "akcja": akcja
            }
        }
        self._zapisz_event(event)
        game_logger.info(f"🎮 [{postac_imie}] Akcja: {akcja[:100]}...")
    
    def log_odpowiedz_mg(self, odpowiedz: dict):
        """Loguje odpowiedź Mistrza Gry"""
        event = {
            "typ": "ODPOWIEDZ_MG",
            "czas": datetime.now().isoformat(),
            "dane": {
                "narracja": odpowiedz.get('narracja', '')[:200],
                "lokacja": odpowiedz.get('lokacja'),
                "hp_gracza": odpowiedz.get('hp_gracza'),
                "walka": odpowiedz.get('walka', False),
                "towarzysze": len(odpowiedz.get('towarzysze', [])),
                "opcje": odpowiedz.get('opcje', [])
            }
        }
        self._zapisz_event(event)
        ai_logger.info(f"🧙 MG odpowiedział. Lokacja: {odpowiedz.get('lokacja')}, HP: {odpowiedz.get('hp_gracza')}")
    
    def log_tts(self, tekst: str, glos: str, sukces: bool, plik: str = None):
        """Loguje syntezę TTS"""
        event = {
            "typ": "TTS_SYNTEZA",
            "czas": datetime.now().isoformat(),
            "dane": {
                "tekst_dlugosc": len(tekst),
                "glos": glos,
                "sukces": sukces,
                "plik": plik
            }
        }
        self._zapisz_event(event)
        if sukces:
            tts_logger.info(f"🔊 TTS OK: głos={glos}, długość={len(tekst)} znaków")
        else:
            tts_logger.warning(f"🔇 TTS BŁĄD: głos={glos}")
    
    def log_blad(self, modul: str, blad: str, szczegoly: dict = None):
        """Loguje błąd"""
        event = {
            "typ": "BLAD",
            "czas": datetime.now().isoformat(),
            "dane": {
                "modul": modul,
                "blad": blad,
                "szczegoly": szczegoly
            }
        }
        self._zapisz_event(event)
        logger.error(f"❌ [{modul}] {blad}")

    def log_admin_action(self, action: str, details: dict = None):
        """Loguje akcje administracyjne (zmiana modelu itp.)"""
        event = {
            "typ": "ADMIN_ACTION",
            "czas": datetime.now().isoformat(),
            "dane": {
                "action": action,
                "details": details or {}
            }
        }
        self._zapisz_event(event)
        logger.info(f"🛠️ ADMIN: {action} - {details}")
    
    def log_gemini_request(self, prompt_dlugosc: int, historia_dlugosc: int, model: str = None):
        """Loguje żądanie do Gemini (dodaje event do sesji)"""
        event = {
            "typ": "GEMINI_REQUEST",
            "czas": datetime.now().isoformat(),
            "dane": {
                "model": model,
                "prompt_length": prompt_dlugosc,
                "historia_length": historia_dlugosc
            }
        }
        self._zapisz_event(event)
        ai_logger.debug(f"📤 Gemini request (model={model}): prompt={prompt_dlugosc} znaków, historia={historia_dlugosc} wpisów")
    
    def log_gemini_response(self, response_dlugosc: int, czas_ms: int = 0, model: str = None, success: bool = True, error: str = None):
        """Loguje odpowiedź z Gemini (dodaje event do sesji)"""
        event = {
            "typ": "GEMINI_RESPONSE",
            "czas": datetime.now().isoformat(),
            "dane": {
                "model": model,
                "response_length": response_dlugosc,
                "duration_ms": czas_ms,
                "success": success,
                "error": error
            }
        }
        self._zapisz_event(event)
        if success:
            ai_logger.debug(f"📥 Gemini response (model={model}): {response_dlugosc} znaków, {czas_ms}ms")
        else:
            ai_logger.warning(f"⚠️ Gemini response ERROR (model={model}): {error} | duration:{czas_ms}ms")
    
    def _zapisz_event(self, event: dict):
        """Zapisuje event do logu sesji"""
        self.session_log.append(event)
        
        # Zapisz do pliku JSON
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd zapisu logu sesji: {e}")
    
    def pobierz_ostatnie_logi(self, ile: int = 20) -> list:
        """Zwraca ostatnie logi z sesji"""
        return self.session_log[-ile:]
    
    def pobierz_statystyki(self) -> dict:
        """Zwraca statystyki sesji"""
        akcje = [e for e in self.session_log if e['typ'] == 'AKCJA_GRACZA']
        odpowiedzi = [e for e in self.session_log if e['typ'] == 'ODPOWIEDZ_MG']
        bledy = [e for e in self.session_log if e['typ'] == 'BLAD']
        tts = [e for e in self.session_log if e['typ'] == 'TTS_SYNTEZA']
        tts_ok = [e for e in tts if e['dane'].get('sukces')]
        
        return {
            "akcje_gracza": len(akcje),
            "odpowiedzi_mg": len(odpowiedzi),
            "bledy": len(bledy),
            "tts_proby": len(tts),
            "tts_sukcesy": len(tts_ok),
            "czas_startu": self.session_log[0]['czas'] if self.session_log else None,
            "ostatni_event": self.session_log[-1]['czas'] if self.session_log else None
        }


# Globalny logger gry
game_log = GameLogger()
