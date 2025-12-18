"""
Słowiańskie Dziedzictwo - Gra Fabularna
Flask + Gemini AI + Piper TTS
"""

from flask import Flask, render_template, request, session, jsonify, send_file
from werkzeug.exceptions import HTTPException
from flask_session import Session
import sqlite3
import random
import os
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from game_master import GameMaster

# Załaduj zmienne z .env (tylko lokalnie)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # W produkcji (Cloud Run) używamy zmiennych środowiskowych
from tts_engine import TTSEngine
from database import Database
from game_logger import game_log, logger
from items import PRZEDMIOTY, get_item, get_all_item_names
from lokacje import pobierz_wszystkie_miasta, PLEMIONA, pobierz_podpowiedzi_dla_miasta

app = Flask(__name__)
app.secret_key = 'slowianski_sekret_2025'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_FILE_THRESHOLD'] = 500  # Maksymalna liczba sesji w pamięci
Session(app)

# Ścieżki
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "game.db"

# Inicjalizacja
db = Database(DB_PATH)
db.inicjalizuj()  # Tworzenie tabel przy starcie (dla Gunicorn na Cloud Run)
game_master = GameMaster()
tts = TTSEngine(BASE_DIR.parent / "PodcastGenerator")

# === AUTO-CZYSZCZENIE STARYCH PLIKÓW ===
def wyczysc_stare_pliki():
    """Usuwa pliki audio i logi starsze niż 7 dni przy starcie serwera"""
    try:
        now = time.time()
        days_7 = 7 * 24 * 60 * 60  # 7 dni w sekundach
        
        # Czyszczenie audio
        audio_dir = BASE_DIR / "audio"
        if audio_dir.exists():
            usunięte_audio = 0
            for plik in audio_dir.glob("*.wav"):
                if now - plik.stat().st_mtime > days_7:
                    plik.unlink()
                    usunięte_audio += 1
            if usunięte_audio > 0:
                logger.info(f"🗑️ Usunięto {usunięte_audio} starych plików audio (>7 dni)")
        
        # Czyszczenie logów sesji
        logs_dir = BASE_DIR / "logs"
        if logs_dir.exists():
            usunięte_logi = 0
            for plik in logs_dir.glob("session_*.json"):
                if now - plik.stat().st_mtime > days_7:
                    plik.unlink()
                    usunięte_logi += 1
            if usunięte_logi > 0:
                logger.info(f"🗑️ Usunięto {usunięte_logi} starych logów sesji (>7 dni)")
                
    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas czyszczenia starych plików: {e}")

# Uruchom czyszczenie przy starcie
wyczysc_stare_pliki()

# === FUNKCJE POMOCNICZE ===

def stackuj_ekwipunek(ekwipunek_lista):
    """
    Przekształca listę przedmiotów w dict z ilościami.
    ['Chleb', 'Chleb', 'Mikstura'] -> {'Chleb': 2, 'Mikstura': 1}
    """
    stackowane = {}
    for przedmiot in ekwipunek_lista:
        stackowane[przedmiot] = stackowane.get(przedmiot, 0) + 1
    return stackowane


def przetworz_hp_przeciwnikow(uczestnicy, narracja, obrazenia_data=None):
    """
    Przetwarza HP przeciwników - inicjalizuje nowych, aktualizuje istniejących.
    
    Args:
        uczestnicy: Lista uczestników z AI
        narracja: Tekst narracji (używany tylko jako fallback jeśli brak obrazenia_data)
        obrazenia_data: Dict z polami 'gracz_otrzymal' i 'zadane' (preferowane źródło obrażeń)
    """
    if 'przeciwnicy_hp' not in session:
        session['przeciwnicy_hp'] = {}
    
    przeciwnicy_hp = session['przeciwnicy_hp']
    wynik = []
    
    for uczestnik in uczestnicy:
        typ = uczestnik.get('typ', 'npc')
        imie = uczestnik.get('imie', 'Nieznajomy')
        
        # NPC - bez HP (przepuść bez zmian)
        if typ == 'npc':
            wynik.append(uczestnik)
            continue
        
        # Wrogowie i bestie - zarządzaj HP
        if typ in ['wrog', 'bestia', 'boss']:
            hp_max = uczestnik.get('hp_max', 50)
            
            # Unikalny ID: jeśli uczestnik ma 'uid', użyj go; w przeciwnym razie wygeneruj
            uid = uczestnik.get('uid')
            if not uid:
                uid = uuid.uuid4().hex[:8]
                uczestnik['uid'] = uid
            
            klucz = f"{typ}_{imie}_{uid}"  # Unikalny klucz z ID
            
            # Sprawdź czy przeciwnik już istnieje w sesji
            if klucz not in przeciwnicy_hp:
                # NOWY przeciwnik - inicjalizuj z pełnym HP
                przeciwnicy_hp[klucz] = {
                    'hp': hp_max,
                    'hp_max': hp_max,
                    'imie': imie,
                    'typ': typ,
                    'ikona': uczestnik.get('ikona', '⚔️')
                }
                logger.info(f"🆕 Nowy przeciwnik: {imie} ({typ}) - HP: {hp_max}/{hp_max}")
            
            # PRIORYTET 1: Jeśli AI zwrócił 'hp' w JSON - użyj tego
            hp_od_ai = uczestnik.get('hp')
            
            if hp_od_ai is not None:
                # AI podał HP - ZAUFAJ MU!
                hp_aktualny = hp_od_ai
                hp_poprzedni = przeciwnicy_hp[klucz]['hp']
                if hp_aktualny != hp_poprzedni:
                    logger.info(f"🤖 AI zaktualizował HP {imie}: {hp_poprzedni} → {hp_aktualny}")
                przeciwnicy_hp[klucz]['hp'] = hp_aktualny
            else:
                # AI NIE podał HP - użyj pola "obrazenia" lub regex jako fallback
                hp_aktualny = przeciwnicy_hp[klucz]['hp']
                
                # PRIORYTET 2: Sprawdź pole "obrazenia" (strukturalne dane)
                obrazenia = 0
                if obrazenia_data and 'zadane' in obrazenia_data:
                    for obr in obrazenia_data['zadane']:
                        if obr.get('cel', '').lower() == imie.lower():
                            obrazenia = obr.get('wartosc', 0)
                            logger.info(f"💥 Strukturalne obrażenia dla {imie}: {obrazenia} HP")
                            break
                
                # PRIORYTET 3: Fallback regex (jeśli brak strukturalnych danych)
                if obrazenia == 0 and narracja:
                    import re
                    wzorce_obrazen = [
                        rf"zadajesz[^.]*?(\d+)[^.]*?(obrażeń|obrażenia)[^.]*?{imie}",
                        rf"zadajesz[^.]*?{imie}[^.]*?(\d+)[^.]*?(obrażeń|punktów obrażeń)",
                        rf"{imie}[^.]*?(otrzymuje|dostaje|traci)[^.]*?(\d+)[^.]*?(obrażeń|punktów obrażeń|HP|zdrowia)",
                        rf"zadajesz[^.]*?(\d+)[^.]*?(obrażeń|obrażenia|punktów obrażeń)",
                    ]
                    
                    for wzorzec in wzorce_obrazen:
                        match = re.search(wzorzec, narracja, re.IGNORECASE)
                        if match:
                            try:
                                obrazenia = int(match.group(2) if match.lastindex >= 2 else match.group(1))
                                logger.info(f"💥 Regex wykrył obrażenia dla {imie}: {obrazenia} HP")
                                break
                            except (ValueError, IndexError):
                                continue
                
                if obrazenia > 0:
                    hp_aktualny = max(0, hp_aktualny - obrazenia)
                    przeciwnicy_hp[klucz]['hp'] = hp_aktualny
                    logger.info(f"⚔️ {imie}: {hp_aktualny + obrazenia} → {hp_aktualny} HP")
            
            # Sprawdź czy przeciwnik zginął
            if hp_aktualny <= 0:
                logger.info(f"💀 {imie} zginął! Usuwam z sesji.")
                # Usuń z sesji (nie pojawi się w następnej turze)
                del przeciwnicy_hp[klucz]
                # NIE dodawaj do wyniku (martwy przeciwnik znika)
                continue
            
            # Dodaj aktualny HP do uczestnika
            uczestnik_z_hp = uczestnik.copy()
            uczestnik_z_hp['hp'] = hp_aktualny
            uczestnik_z_hp['hp_max'] = hp_max
            uczestnik_z_hp['uid'] = uid  # Zachowaj UID dla frontendu
            wynik.append(uczestnik_z_hp)
        else:
            # Inny typ - przepuść bez zmian
            wynik.append(uczestnik)
    
    # Zapisz zaktualizowany słownik HP do sesji
    session['przeciwnicy_hp'] = przeciwnicy_hp
    session.modified = True
    
    logger.info(f"🔚 Zwracam {len(wynik)} uczestników z HP")
    return wynik


def oblicz_ladownosc(postac):
    """
    Oblicza maksymalną ładowność gracza.
    :return: (zajete_sloty, max_slotow, ma_worki, ma_zwierze)
    """
    ekwipunek = postac.get('ekwipunek', [])
    zajete_sloty = len(ekwipunek)
    
    # Bazowa ładowność
    max_slotow = 10
    
    # Worki (+30 slotów każdy, max 2)
    worki = ekwipunek.count('Worek skórzany') + ekwipunek.count('Worek lniany')
    worki = min(worki, 2)  # Max 2 worki
    max_slotow += worki * 30
    
    # Zwierzęta juczne
    ma_konia = 'Koń' in ekwipunek
    ma_osla = 'Osioł' in ekwipunek
    ma_woz = 'Wóz' in ekwipunek
    
    if ma_konia:
        max_slotow += 50
        if ma_woz:
            max_slotow += 100  # Wóz wymaga konia
    elif ma_osla:
        max_slotow += 50
    
    return zajete_sloty, max_slotow, worki, (ma_konia or ma_osla)


def generuj_liste_przedmiotow(kategorie=None, max_items=25):
    """
    Generuje string z listą przedmiotów dla Gemini.
    :param kategorie: lista kategorii do wyświetlenia (None = wszystkie)
    :param max_items: maksymalna liczba przedmiotów
    """
    przedmioty_tekst = []
    count = 0
    
    for nazwa, info in PRZEDMIOTY.items():
        if kategorie and info['typ'] not in kategorie:
            continue
        if count >= max_items:
            break
        
        # Format: "Nazwa (cena: X złota, DMG: Y)" lub "Nazwa (cena: X, HP+Y)"
        opis = f"{nazwa} (cena: {info['cena']} złota"
        if info.get('dmg'):
            opis += f", DMG: {info['dmg']}"
        if info.get('def'):
            opis += f", DEF: {info['def']}"
        if info.get('hp_heal'):
            opis += f", HP+{info['hp_heal']}"
        opis += ")"
        
        przedmioty_tekst.append(opis)
        count += 1
    
    return ", ".join(przedmioty_tekst)


def waliduj_i_aplikuj_transakcje(postac, transakcje):
    """
    Waliduje transakcje i aplikuje je do postaci.
    :param postac: dict postaci ze zloto i ekwipunek
    :param transakcje: dict z 'zloto_zmiana', 'przedmioty_dodane', 'przedmioty_usuniete'
    :return: (sukces: bool, komunikat: str)
    """
    if not transakcje:
        return True, ""
    
    zloto_zmiana = transakcje.get('zloto_zmiana', 0)
    przedmioty_dodane = transakcje.get('przedmioty_dodane', [])
    przedmioty_usuniete = transakcje.get('przedmioty_usuniete', [])
    
    # WALIDACJA: Czy gracz ma wystarczająco złota?
    nowe_zloto = postac.get('zloto', 0) + zloto_zmiana
    if nowe_zloto < 0:
        brakuje = abs(nowe_zloto)
        return False, f"BRAK WYSTARCZAJĄCYCH ŚRODKÓW! Potrzebujesz jeszcze {brakuje} złota."
    
    # WALIDACJA: Czy przedmioty do usunięcia są w ekwipunku?
    ekwipunek = postac.get('ekwipunek', [])
    for przedmiot in przedmioty_usuniete:
        if przedmiot not in ekwipunek:
            return False, f"NIE MASZ przedmiotu '{przedmiot}' w ekwipunku!"
    
    # WALIDACJA: Czy starczy miejsca na nowe przedmioty?
    zajete, max_slotow, worki, zwierze = oblicz_ladownosc(postac)
    nowe_przedmioty_count = len(przedmioty_dodane) - len(przedmioty_usuniete)
    
    if zajete + nowe_przedmioty_count > max_slotow:
        brakuje = (zajete + nowe_przedmioty_count) - max_slotow
        sugestia = ""
        if worki == 0:
            sugestia = " Kup worek, aby zwiększyć ładowność o 30 slotów!"
        elif worki == 1:
            sugestia = " Możesz kupić drugi worek (+30 slotów) lub zwierzę juczne (+50 slotów)!"
        elif not zwierze:
            sugestia = " Kup konia lub osła, aby zwiększyć ładowność o 50 slotów!"
        
        return False, f"BRAK MIEJSCA W EKWIPUNKU! Zajęte: {zajete}/{max_slotow}, brakuje {brakuje} slotów.{sugestia}"
    
    # APLIKACJA: Zaktualizuj złoto
    postac['zloto'] = nowe_zloto
    
    # APLIKACJA: Dodaj przedmioty
    for przedmiot in przedmioty_dodane:
        ekwipunek.append(przedmiot)
    
    # APLIKACJA: Usuń przedmioty
    for przedmiot in przedmioty_usuniete:
        ekwipunek.remove(przedmiot)  # remove() usuwa pierwsze wystąpienie
    
    postac['ekwipunek'] = ekwipunek
    
    return True, ""


def przetworz_towarzyszy(towarzysze_z_gemini, postac):
    """
    Przetwarza towarzyszy z odpowiedzi Gemini:
    - Waliduje HP (0-hp_max)
    - Auto-leczenie gdy HP < 30% (używa mikstur gracza)
    - Sprawdza śmierć i reanimację (50%)
    - Zapisuje do bazy danych
    
    Returns: (towarzysze_po_przetworzeniu, komunikaty_do_narracji)
    """
    import random
    
    towarzysze_baza = postac.get('towarzysze', [])
    komunikaty = []
    ekwipunek = postac.get('ekwipunek', [])
    
    # Normalizuj nowych towarzyszy (dodaj hp_max, ekwipunek)
    for t in towarzysze_z_gemini:
        if 'hp_max' not in t and 'hp' in t:
            t['hp_max'] = t['hp']
        elif 'hp_max' not in t:
            t['hp_max'] = 25
        if 'hp' not in t:
            t['hp'] = t.get('hp_max', 25)
        if 'ekwipunek' not in t:
            t['ekwipunek'] = []
    
    # Sprawdź śmierć i reanimację
    towarzysze_finalni = []
    for t in towarzysze_z_gemini:
        if t['hp'] <= 0:
            # Towarzysz padł - 50% szansa na powrót z 1 HP
            szansa = random.randint(1, 100)
            if szansa <= 50:
                t['hp'] = 1
                komunikaty.append(f"💚 **{t['imie']}** odzyskuje przytomność z 1 HP!")
                towarzysze_finalni.append(t)
            else:
                komunikaty.append(f"💀 **{t['imie']}** ginie w walce...")
                # Nie dodajemy do listy - towarzysz przepada
        else:
            # Towarzysz żyje - sprawdź auto-leczenie
            if t['hp'] < t['hp_max'] * 0.3 and t['hp'] > 0:
                # HP < 30%, próbuj się wyleczyć
                mikstura_idx = next((i for i, item in enumerate(ekwipunek) if 'mikstura' in item.lower() or 'napój' in item.lower()), None)
                if mikstura_idx is not None:
                    mikstura = ekwipunek.pop(mikstura_idx)
                    wyleczenie = min(20, t['hp_max'] - t['hp'])  # +20 HP lub do max
                    t['hp'] = min(t['hp'] + wyleczenie, t['hp_max'])
                    komunikaty.append(f"🩹 **{t['imie']}** używa {mikstura} i regeneruje {wyleczenie} HP!")
            
            towarzysze_finalni.append(t)
    
    # Aktualizuj bazę danych
    postac['towarzysze'] = towarzysze_finalni
    postac['ekwipunek'] = ekwipunek  # Zapisz zmieniony ekwipunek (po zużyciu mikstur)
    
    return towarzysze_finalni, komunikaty

# === DANE GRY ===

LUDY = {
    "polanie": {
        "nazwa": "Polanie",
        "opis": "Główne plemię Mieszka I, zamieszkujące okolice Gniezna",
        "bonus": {"charyzma": 2, "sila": 1},
        "umiejetnosc": "Zjednoczenie - bonus +2 do dyplomacji"
    },
    "wislanie": {
        "nazwa": "Wiślanie",
        "opis": "Plemię z południa, okolice Krakowa",
        "bonus": {"inteligencja": 2, "wytrzymalosc": 1},
        "umiejetnosc": "Handel - lepsze ceny u kupców"
    },
    "slezanie": {
        "nazwa": "Ślężanie",
        "opis": "Plemię zachodnie, Śląsk",
        "bonus": {"sila": 2, "zrecznosc": 1},
        "umiejetnosc": "Góralska Krew - odporność na zimno"
    },
    "mazowszanie": {
        "nazwa": "Mazowszanie",
        "opis": "Plemię wschodnie, puszcze i bagna",
        "bonus": {"zrecznosc": 2, "szczescie": 1},
        "umiejetnosc": "Puszczański Trop - bonus w lasach"
    },
    "pomorzanie": {
        "nazwa": "Pomorzanie",
        "opis": "Plemię północne, wybrzeże morza",
        "bonus": {"wytrzymalosc": 2, "sila": 1},
        "umiejetnosc": "Żeglarz - bonus nad wodą"
    }
}

KLASY = {
    "wojownik_rycerz": {
        "nazwa": "Wojownik-Rycerz",
        "opis": "Ciężkozbrojny wojownik, honor i siła",
        "bonus_hp": 10,
        "umiejetnosci": ["Potężne Uderzenie", "Tarcza", "Wyzwanie"]
    },
    "wojownik_zbojnik": {
        "nazwa": "Wojownik-Zbójnik",
        "opis": "Szybki i podstępny, lekka zbroja",
        "bonus_hp": 5,
        "umiejetnosci": ["Zasadzka", "Unik", "Cios w Plecy"]
    },
    "lowca": {
        "nazwa": "Łowca",
        "opis": "Mistrz łuku i tropienia",
        "bonus_hp": 6,
        "umiejetnosci": ["Strzał Precyzyjny", "Tropienie", "Pułapka"]
    },
    "zielarz": {
        "nazwa": "Zielarz",
        "opis": "Leczenie, mikstury, trucizny",
        "bonus_hp": 4,
        "umiejetnosci": ["Leczenie", "Trucizna", "Mikstura Siły"]
    },
    "zerca": {
        "nazwa": "Żerca",
        "opis": "Kapłan pogański, magia i rytuały",
        "bonus_hp": 4,
        "umiejetnosci": ["Błogosławieństwo", "Klątwa", "Wizja"]
    },
    "kowal": {
        "nazwa": "Kowal",
        "opis": "Crafting, mocne ciosy, naprawa",
        "bonus_hp": 8,
        "umiejetnosci": ["Młot Kowala", "Naprawa", "Ulepszenie"]
    },
    "guslar": {
        "nazwa": "Guslar",
        "opis": "Bard, pieśni bojowe, buffy",
        "bonus_hp": 5,
        "umiejetnosci": ["Pieśń Bojowa", "Pieśń Lecznicza", "Opowieść"]
    },
    "kupiec": {
        "nazwa": "Kupiec",
        "opis": "Złoto, przekupstwo, znajomości",
        "bonus_hp": 4,
        "umiejetnosci": ["Targowanie", "Przekupstwo", "Kontakty"]
    },
    "rolnik": {
        "nazwa": "Rolnik",
        "opis": "Wytrzymały, improwizacja",
        "bonus_hp": 7,
        "umiejetnosci": ["Wytrzymałość", "Improwizacja", "Znajomość Terenu"]
    },
    "wloczega": {
        "nazwa": "Włóczęga",
        "opis": "Przetrwanie, kradzież, informacje",
        "bonus_hp": 5,
        "umiejetnosci": ["Skradanie", "Kradzież", "Plotki"]
    }
}


def rzut_kostka(ilosc=2, scianki=6):
    """Rzut kostkami"""
    return sum(random.randint(1, scianki) for _ in range(ilosc))


def generuj_statystyki():
    """Generuje losowe statystyki postaci (2k6 dla każdej)"""
    return {
        "sila": rzut_kostka(2, 6),
        "zrecznosc": rzut_kostka(2, 6),
        "wytrzymalosc": rzut_kostka(2, 6),
        "inteligencja": rzut_kostka(2, 6),
        "charyzma": rzut_kostka(2, 6),
        "szczescie": rzut_kostka(2, 6)
    }


@app.route('/')
def index():
    """Strona główna"""
    return render_template('index.html')


@app.route('/nowa_gra')
def nowa_gra():
    """Ekran tworzenia postaci"""
    session.clear()
    return render_template('tworzenie_postaci.html', ludy=LUDY, klasy=KLASY)


@app.route('/losuj_statystyki', methods=['POST'])
def losuj_statystyki():
    """Losuje statystyki dla postaci + 10 punktów bonusowych do rozdania"""
    stats = generuj_statystyki()
    stats['punkty_bonusowe'] = 10  # 10 punktów do rozdania
    return jsonify(stats)


@app.route('/stworz_postac', methods=['POST'])
def stworz_postac():
    """Tworzy postać i rozpoczyna grę"""
    data = request.json
    
    imie = data.get('imie', 'Bezimiennik')
    plec = data.get('plec', 'mezczyzna')
    lud = data.get('lud')
    klasa = data.get('klasa')
    statystyki = data.get('statystyki', {})
    
    # Dodaj bonusy ludu
    lud_data = LUDY.get(lud, {})
    for stat, bonus in lud_data.get('bonus', {}).items():
        if stat in statystyki:
            statystyki[stat] += bonus
    
    # Oblicz HP
    klasa_data = KLASY.get(klasa, {})
    hp = 10 + statystyki.get('wytrzymalosc', 10) + klasa_data.get('bonus_hp', 0)
    
    # Pobierz miasto odpowiadające ludowi - mapowanie lud -> plemię -> miasto
    mapa_lud_plemie = {
        'polanie': 'polanie',
        'wislanie': 'wislanie',
        'pomorzanie': 'pomorzanie',
        'mazowszanie': 'mazowszanie',
        'slezanie': 'slezanie'
    }
    plemie = mapa_lud_plemie.get(lud, 'polanie')
    miasto = PLEMIONA.get(plemie, {}).get('miasto', 'Gniezno')
    
    # Stwórz postać
    postac = {
        "imie": imie,
        "plec": plec,
        "lud": lud,
        "lud_nazwa": lud_data.get('nazwa', lud),
        "klasa": klasa,
        "klasa_nazwa": klasa_data.get('nazwa', klasa),
        "statystyki": statystyki,
        "hp": hp,
        "hp_max": hp,
        "poziom": 1,
        "doswiadczenie": 0,
        "zloto": random.randint(10, 30),
        "ekwipunek": ["Nóż", "Chleb", "Bukłak z wodą"],
        "umiejetnosci": klasa_data.get('umiejetnosci', []),
        "lokacja": miasto,
        "questy": ["Zjednoczenie Plemion"]
    }
    
    # Zapisz do sesji i bazy
    session['postac'] = postac
    session['historia'] = []
    
    postac_id = db.zapisz_postac(postac)
    session['postac_id'] = postac_id
    session.modified = True  # Wymuś zapis sesji
    
    # Loguj utworzenie postaci
    game_log.log_postac_utworzona(postac)
    
    return jsonify({"success": True, "postac": postac})


@app.route('/gra')
def gra():
    """Główny ekran gry"""
    if 'postac' not in session:
        # Sprawdź czy jest zapisana gra w bazie
        return render_template('index.html')
    return render_template('gra.html', postac=session['postac'])


@app.route('/wczytaj_gre/<int:postac_id>')
def wczytaj_gre(postac_id):
    """Wczytuje zapisaną grę"""
    postac = db.wczytaj_postac(postac_id)
    if postac:
        # Uzupełnij dane które nie są w bazie
        lud_data = LUDY.get(postac.get('lud'), {})
        klasa_data = KLASY.get(postac.get('klasa'), {})
        postac['lud_nazwa'] = lud_data.get('nazwa', postac.get('lud'))
        postac['klasa_nazwa'] = klasa_data.get('nazwa', postac.get('klasa'))
        postac['umiejetnosci'] = klasa_data.get('umiejetnosci', [])
        postac['hp_max'] = postac.get('hp_max', 100)
        
        session['postac'] = postac
        session['postac_id'] = postac_id
        session['historia'] = db.wczytaj_historie(postac_id)
        session['gra_wczytana'] = True  # Flaga że gra jest wczytana
        
        return render_template('gra.html', postac=postac)
    return render_template('index.html')


@app.route('/stan_gry')
def stan_gry():
    """Zwraca aktualny stan gry z sesji"""
    postac = session.get('postac', {})
    return jsonify({
        'postac': postac,
        'historia_dlugosc': len(session.get('historia', [])),
        'gra_aktywna': 'postac' in session,
        'gra_wczytana': session.get('gra_wczytana', False),
        'towarzysze': postac.get('towarzysze', [])
    })


@app.route('/ostatnia_narracja')
def ostatnia_narracja():
    """Zwraca ostatnią narrację z historii do wyświetlenia po F5"""
    try:
        historia = session.get('historia', [])
        postac = session.get('postac', {})
        
        if not historia:
            return jsonify({
                'narracja': None,
                'opcje': ['Rozejrzyj się', 'Idź dalej', 'Porozmawiaj z kimś']
            })
        
        # Znajdź ostatnią narrację narratora (pomijając akcje gracza)
        ostatnia = None
        for wpis in reversed(historia):
            if isinstance(wpis, dict) and wpis.get('typ') == 'narrator':
                ostatnia = wpis.get('tekst', '')
                break
        
        return jsonify({
            'narracja': ostatnia,
            'opcje': session.get('ostatnie_opcje', ['Rozejrzyj się', 'Idź dalej', 'Kontynuuj']),
            'uczestnicy': session.get('ostatni_uczestnicy', []),  # NOWE: przywróć NPC
            'hp_gracza': postac.get('hp'),
            'zloto': postac.get('zloto'),
            'ekwipunek': postac.get('ekwipunek', []),
            'towarzysze': postac.get('towarzysze', []),
            'lokacja': postac.get('lokacja')
        })
    except Exception as e:
        logger.error(f"❌ Błąd w /ostatnia_narracja: {e}")
        # Fallback - zwróć pustą odpowiedź
        return jsonify({
            'narracja': None,
            'opcje': ['Rozejrzyj się', 'Idź dalej', 'Porozmawiaj z kimś']
        })


@app.route('/zapisz_gre', methods=['POST'])
def zapisz_gre():
    """Zapisuje aktualną grę (max 10 zapisów)"""
    try:
        postac = session.get('postac', {})
        postac_id = session.get('postac_id')
        
        logger.info(f"💾 Próba zapisu - postac_id: {postac_id}, postac: {postac.get('imie', 'BRAK')}")
        
        if not postac_id:
            logger.error(f"❌ Brak postac_id w sesji! Session keys: {list(session.keys())}")
            return jsonify({'ok': False, 'error': 'Brak aktywnej gry (brak postac_id w sesji)'})
        
        if not postac:
            logger.error(f"❌ Brak postaci w sesji!")
            return jsonify({'ok': False, 'error': 'Brak danych postaci w sesji'})
        
        # Zapisz postać do bazy (bez json.dumps - database.py to robi)
        rows = db.aktualizuj_postac(postac_id, {
            'hp': postac.get('hp', 100),
            'lokacja': postac.get('lokacja', 'gniezno'),
            'zloto': postac.get('zloto', 0),
            'ekwipunek': postac.get('ekwipunek', []),
            'towarzysze': postac.get('towarzysze', []),
            'przeciwnicy_hp': session.get('przeciwnicy_hp', {})
        })
        if rows == 0:
            logger.warning(f"⚠️ Aktualizacja postaci zwróciła 0 wierszy (postac_id={postac_id}). Tworzę nowy zapis.")
            new_id = db.zapisz_postac(postac)
            session['postac_id'] = new_id
            logger.info(f"🔁 Nowy zapis utworzony z ID: {new_id}")
        
        # Usuń najstarsze zapisy jeśli > 10
        usuniete = db.usun_najstarsze_zapisy(limit=10)
        if usuniete > 0:
            logger.info(f"🗑️ Usunięto {usuniete} najstarszych zapisów (limit: 10)")
        
        logger.info(f"💾 Gra zapisana: {postac.get('imie')} (ID: {postac_id})")
        return jsonify({'ok': True, 'message': f'Zapisano: {postac.get("imie")}'})
        
    except Exception as e:
        logger.error(f"❌ Błąd zapisu gry: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/lista_zapisow')
def lista_zapisow():
    """Zwraca listę autosave'ów (max 5 najnowszych)"""
    try:
        zapisy = db.lista_postaci(limit=5, tylko_autosave=True)
        return jsonify({'zapisy': zapisy})
    except Exception as e:
        logger.error(f"❌ Błąd listowania zapisów: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/usun_zapis/<int:postac_id>', methods=['DELETE'])
def usun_zapis(postac_id):
    """Usuwa zapisaną grę"""
    try:
        logger.info(f"🗑️ Próba usunięcia zapisu ID: {postac_id}")
        sukces = db.usun_postac(postac_id)
        
        if sukces:
            logger.info(f"✅ Usunięto zapis ID: {postac_id}")
            game_log.log_blad('DELETE_SAVE', f'Usunięto zapis {postac_id}', {'postac_id': postac_id, 'success': True})
            return jsonify({'ok': True, 'message': f'Zapis #{postac_id} usunięty pomyślnie'})
        else:
            logger.warning(f"⚠️ Nie znaleziono zapisu ID: {postac_id}")
            return jsonify({'ok': False, 'error': f'Nie znaleziono zapisu #{postac_id}'})
            
    except Exception as e:
        logger.error(f"❌ Błąd usuwania zapisu {postac_id}: {e}")
        game_log.log_blad('DELETE_SAVE', str(e), {'postac_id': postac_id})
        return jsonify({'ok': False, 'error': f'Błąd: {str(e)}'})


@app.route('/wyczysc_stare_autosavy', methods=['POST'])
def wyczysc_stare_autosavy():
    """Czyści wszystkie stare autosave'y poza ostatnimi 5"""
    try:
        logger.info("🧹 Czyszczenie starych autosave'ów...")
        usunietych = db.usun_stare_autosavy(limit=5)
        logger.info(f"✅ Usunięto {usunietych} starych zapisów")
        return jsonify({'ok': True, 'usuniete': usunietych, 'message': f'Usunięto {usunietych} starych zapisów'})
    except Exception as e:
        logger.error(f"❌ Błąd czyszczenia: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/wczytaj_zapis/<int:postac_id>')
def wczytaj_zapis(postac_id):
    """Wczytuje zapisaną grę z pełnym kontekstem AI"""
    try:
        postac = db.wczytaj_postac(postac_id)
        
        if not postac:
            return jsonify({'ok': False, 'error': 'Nie znaleziono zapisu'}), 404
        
        # Wyczyść poprzednią sesję
        session.clear()
        
        # Załaduj dane postaci
        session['postac'] = postac
        session['postac_id'] = postac_id
        session['historia'] = db.wczytaj_historie(postac_id, limit=100)
        session['przeciwnicy_hp'] = postac.get('przeciwnicy_hp', {})
        session['gra_wczytana'] = True  # FLAGA: blokuj auto-start nowej gry
        session.modified = True  # Wymuś zapis sesji
        
        # NOWE: Przywróć pełny kontekst AI (historia Gemini + opcje + uczestnicy)
        ai_context = db.wczytaj_ai_context(postac_id)
        historia_ai = ai_context.get('historia', [])
        ostatnie_opcje = ai_context.get('opcje', [])
        ostatni_uczestnicy = ai_context.get('uczestnicy', [])  # NOWE: NPC
        
        if historia_ai:
            game_master.set_historia(historia_ai)
            logger.info(f"📂 Przywrócono historię AI: {len(historia_ai)} wiadomości")
        else:
            logger.warning(f"⚠️ Brak zapisanego kontekstu AI dla postaci {postac_id}")
        
        # Przywróć stan HP w GameMaster
        game_master.aktualne_hp = postac['hp']
        game_master.hp_max = postac['hp_max']
        
        # Zapisz opcje i uczestników do sesji (użyjemy ich w interfejsie)
        session['ostatnie_opcje'] = ostatnie_opcje
        session['ostatni_uczestnicy'] = ostatni_uczestnicy  # NOWE: przywróć NPC
        
        logger.info(f"📂 Gra wczytana: {postac.get('imie')} (ID: {postac_id}), opcje: {len(ostatnie_opcje)}, NPC: {len(ostatni_uczestnicy)}")
        return jsonify({'ok': True, 'redirect': '/gra'})
        
    except Exception as e:
        logger.error(f"❌ Błąd wczytywania gry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/rozpocznij_przygode', methods=['POST'])
def rozpocznij_przygode():
    """Gemini generuje wstęp do przygody"""
    postac = session.get('postac', {})

    # Bezpieczne domyślne wartości jeśli sesja jest pusta (np. testy bez stworzonej postaci)
    hp = postac.get('hp', 100)
    hp_max = postac.get('hp_max', hp)
    
    # Inicjalizacja złota i ekwipunku jeśli nie istnieją
    if 'zloto' not in postac:
        postac['zloto'] = 50  # Startowe złoto
    if 'ekwipunek' not in postac:
        postac['ekwipunek'] = []
    
    # Generuj listę przedmiotów dostępnych w grze
    lista_przedmiotow = generuj_liste_przedmiotow(
        kategorie=['mikstura', 'jedzenie', 'napoj', 'bron_1r', 'tarcza', 'worek', 'zwierze'],
        max_items=25
    )
    
    # Użyj nowego API GameMaster z HP postaci + lista przedmiotów
    try:
        wynik = game_master.rozpocznij_gre({
            'imie': postac.get('imie'),
            'plemie': postac.get('lud_nazwa'),
            'klasa': postac.get('klasa_nazwa'),
            'hp': hp,
            'hp_max': hp_max,
            'zloto': postac.get('zloto', 50),
            'ekwipunek': postac.get('ekwipunek', [])
        }, lista_przedmiotow=lista_przedmiotow)
    except ValueError as e:
        # Błąd API key - wyraźny komunikat
        error_msg = str(e)
        if 'GEMINI_API_KEY' in error_msg or 'nieprawidłowy' in error_msg or 'wygasł' in error_msg:
            logger.error(f"❌ GEMINI API KEY ERROR: {e}")
            game_log.log_blad('GameMaster', str(e), {'endpoint': 'rozpocznij_przygode'})
            tekst = f"⚠️ **BŁĄD KONFIGURACJI:** Klucz API Google Gemini jest nieprawidłowy lub wygasł.\n\n" \
                    f"**Rozwiązanie:**\n" \
                    f"1. Wejdź na: https://aistudio.google.com/app/apikey\n" \
                    f"2. Stwórz nowy klucz API\n" \
                    f"3. Zaktualizuj plik `.env` → `GEMINI_API_KEY=twój_nowy_klucz`\n" \
                    f"4. Zrestartuj serwer\n\n" \
                    f"Szczegóły: {error_msg}"
            return jsonify({
                'tekst': tekst,
                'audio': None,
                'lokacja': postac.get('lokacja', 'Gniezno'),
                'towarzysze': postac.get('towarzysze', []),
                'opcje': ['Napraw klucz API i odśwież'],
                'quest_aktywny': None,
                'hp_gracza': hp,
                'zloto': postac.get('zloto', 0),
                'ekwipunek': postac.get('ekwipunek', []),
                'ladownosc': {'zajete': len(postac.get('ekwipunek', [])), 'max': 10}
            }), 200
        else:
            raise  # Inne ValueError
    except RuntimeError as e:
        # Błąd limitu/quota
        error_msg = str(e)
        if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            logger.warning(f"⚠️ GEMINI QUOTA: {e}")
            game_log.log_blad('GameMaster', str(e), {'endpoint': 'rozpocznij_przygode'})
            tekst = f"⚠️ **LIMIT API:** Przekroczono dozwoloną liczbę zapytań do Google Gemini.\n\n" \
                    f"Spróbuj ponownie za kilka minut.\n\n" \
                    f"Szczegóły: {error_msg}"
            return jsonify({
                'tekst': tekst,
                'audio': None,
                'lokacja': postac.get('lokacja', 'Gniezno'),
                'towarzysze': postac.get('towarzysze', []),
                'opcje': ['Spróbuj ponownie'],
                'quest_aktywny': None,
                'hp_gracza': hp,
                'zloto': postac.get('zloto', 0),
                'ekwipunek': postac.get('ekwipunek', []),
                'ladownosc': {'zajete': len(postac.get('ekwipunek', [])), 'max': 10}
            }), 200
        else:
            raise  # Inne RuntimeError
    except Exception as e:
        # Loguj PEŁNY traceback
        import traceback
        logger.error(f"❌ Błąd podczas komunikacji z GameMaster: {e}")
        logger.error(f"📄 Typ błędu: {type(e).__name__}")
        logger.error(f"📄 Pełny traceback:\n{traceback.format_exc()}")
        game_log.log_blad('GameMaster', str(e), {'endpoint': 'rozpocznij_przygode'})
        tekst = f"⚠️ Błąd połączenia z Mistrzem Gry: {e}"
        return jsonify({
            'tekst': tekst,
            'audio': None,
            'lokacja': postac.get('lokacja', 'Gniezno'),
            'towarzysze': postac.get('towarzysze', []),
            'opcje': ['Spróbuj ponownie'],
            'quest_aktywny': None,
            'hp_gracza': hp,
            'zloto': postac.get('zloto', 0),
            'ekwipunek': postac.get('ekwipunek', []),
            'ladownosc': {'zajete': len(postac.get('ekwipunek', [])), 'max': 10}
        }), 200
    
    # Wyciągnij narrację
    if not isinstance(wynik, dict):
        logger.error(f"❌ Niepoprawna odpowiedź MG (nie-dict): {wynik}")
        game_log.log_blad('GameMaster', 'Niepoprawna odpowiedź', {'endpoint': 'rozpocznij_przygode', 'wynik': str(wynik)})
        tekst = "⚠️ Mistrz Gry zwrócił nieoczekiwaną odpowiedź. Spróbuj ponownie za chwilę."
        return jsonify({
            'tekst': tekst,
            'audio': None,
            'lokacja': postac.get('lokacja', 'Gniezno'),
            'towarzysze': postac.get('towarzysze', []),
            'opcje': ['Spróbuj ponownie'],
            'quest_aktywny': None,
            'hp_gracza': hp,
            'zloto': postac.get('zloto', 0),
            'ekwipunek': postac.get('ekwipunek', []),
            'ladownosc': {'zajete': len(postac.get('ekwipunek', [])), 'max': 10}
        }), 200

    narracja = wynik.get('narracja', 'Przygoda się zaczyna...')
    
    # WALIDUJ I APLIKUJ TRANSAKCJE
    transakcje = wynik.get('transakcje', {})
    sukces, komunikat = waliduj_i_aplikuj_transakcje(postac, transakcje)
    
    if not sukces:
        # Jeśli transakcja odrzucona - dodaj komunikat do narracji
        narracja += f"\n\n**System:** {komunikat}"
        logger.warning(f"❌ Transakcja odrzucona: {komunikat}")
    else:
        # Loguj udane transakcje
        if transakcje.get('zloto_zmiana') or transakcje.get('przedmioty_dodane') or transakcje.get('przedmioty_usuniete'):
            logger.info(f"💰 Transakcja: złoto={transakcje.get('zloto_zmiana', 0)}, dodane={transakcje.get('przedmioty_dodane', [])}, usunięte={transakcje.get('przedmioty_usuniete', [])}")
    
    # Loguj odpowiedź MG
    game_log.log_odpowiedz_mg(wynik)
    
    # Przetworz towarzyszy (HP, auto-leczenie, śmierć/reanimacja)
    towarzysze_raw = wynik.get('towarzysze', [])
    towarzysze, komunikaty_towarzyszy = przetworz_towarzyszy(towarzysze_raw, postac)
    
    # Dodaj komunikaty do narracji jeśli są
    if komunikaty_towarzyszy:
        narracja += "\n\n" + "\n".join(komunikaty_towarzyszy)
    
    # Zapisz zaktualizowaną postać
    session['postac'] = postac
    
    # Dodaj do historii
    if 'historia' not in session:
        session['historia'] = []
    session['historia'].append({
        "typ": "narrator",
        "tekst": narracja
    })
    session.modified = True
    
    # Zapisz do bazy (postać + towarzysze)
    postac_id = session.get('postac_id')
    if not postac_id:
        logger.error("❌ KRYTYCZNY: Brak postac_id przy rozpoczęciu gry!")
        return jsonify({'error': 'Brak ID postaci - odśwież stronę i spróbuj ponownie'}), 500
    
    rows = db.aktualizuj_postac(postac_id, {
        'hp': postac.get('hp', hp),
        'zloto': postac.get('zloto', 0),
        'ekwipunek': postac.get('ekwipunek', []),
        'towarzysze': towarzysze,
        'przeciwnicy_hp': session.get('przeciwnicy_hp', {})
    })
    if rows == 0:
        logger.warning(f"⚠️ Aktualizacja postaci przy rozpoczęciu gry zwróciła 0 wierszy (postac_id={postac_id}). Tworzę nowy zapis.")
        new_id = db.zapisz_postac(postac)
        session['postac_id'] = new_id
        logger.info(f"🔁 Nowy zapis utworzony z ID: {new_id}")
    db.zapisz_historie(postac_id, "ROZPOCZĘCIE GRY", narracja)
    
    session.modified = True
    
    # Generuj audio z wieloma głosami
    plec_gracza = session['postac'].get('plec', 'mezczyzna')
    audio_path = tts.syntezuj_multi_voice(narracja, plec_gracza)
    game_log.log_tts(narracja, "multi-voice", audio_path is not None, str(audio_path) if audio_path else None)
    
    # Przygotuj URL audio (lokalnie: /audio/plik.wav, cloud: pełny URL)
    if audio_path:
        if audio_path.startswith('http'):
            # Cloud Storage - użyj pełnego URL
            audio_url = audio_path
        else:
            # Lokalny plik - użyj /audio/plik.wav
            audio_url = f"/audio/{os.path.basename(audio_path)}"
    else:
        audio_url = None
    
    # Oblicz ładowność
    zajete, max_slotow, worki, zwierze = oblicz_ladownosc(postac)
    
    return jsonify({
        "tekst": narracja,
        "audio": audio_url,
        "lokacja": wynik.get('lokacja', 'Gniezno'),
        "towarzysze": towarzysze,  # Używaj znormalizowanych towarzyszy
        "uczestnicy": wynik.get('uczestnicy', []),  # NOWE: wrogowie/NPC/bestie w scenie startowej
        "opcje": wynik.get('opcje', []),
        "quest_aktywny": wynik.get('quest_aktywny'),
        "hp_gracza": wynik.get('hp_gracza', 100),
        "zloto": postac.get('zloto', 0),
        "ekwipunek": postac.get('ekwipunek', []),
        "ladownosc": {"zajete": zajete, "max": max_slotow}
    })


@app.route('/akcja', methods=['POST'])
def akcja():
    """Gracz wykonuje akcję, Gemini odpowiada"""
    data = request.json
    akcja_gracza = data.get('akcja', '')
    
    postac = session.get('postac', {})
    historia = session.get('historia', [])
    
    # Inicjalizacja złota i ekwipunku jeśli nie istnieją
    if 'zloto' not in postac:
        postac['zloto'] = 50
    if 'ekwipunek' not in postac:
        postac['ekwipunek'] = []
    
    # Loguj akcję gracza
    game_log.log_akcja_gracza(akcja_gracza, postac.get('imie', 'Gracz'))
    
    # Generuj listę przedmiotów dostępnych w grze
    lista_przedmiotow = generuj_liste_przedmiotow(
        kategorie=['mikstura', 'jedzenie', 'napoj', 'bron_1r', 'tarcza', 'zbroja', 'worek', 'zwierze', 'transport'],
        max_items=30
    )
    
    # Przekaż stan gracza do GameMaster
    stan_gracza = {
        'hp': postac.get('hp', 100),
        'hp_max': postac.get('hp_max', 100),
        'lokacja': postac.get('lokacja', 'gniezno'),
        'zloto': postac.get('zloto', 0),
        'ekwipunek': postac.get('ekwipunek', []),
        'towarzysze': postac.get('towarzysze', [])
    }
    
    # Użyj nowego API GameMaster z aktualnym stanem + lista przedmiotów
    try:
        wynik = game_master.akcja(akcja_gracza, stan_gracza, lista_przedmiotow)
    except ValueError as e:
        # Błąd API key
        error_msg = str(e)
        if 'GEMINI_API_KEY' in error_msg or 'nieprawidłowy' in error_msg or 'wygasł' in error_msg:
            logger.error(f"❌ GEMINI API KEY ERROR: {e}")
            game_log.log_blad('GameMaster', str(e), {'endpoint': 'akcja', 'akcja': akcja_gracza})
            tekst = f"⚠️ **BŁĄD KONFIGURACJI:** Klucz API Google Gemini jest nieprawidłowy.\n\n" \
                    f"Sprawdź `.env` i zrestartuj serwer.\n\n" \
                    f"Szczegóły: {error_msg}"
            return jsonify({
                'tekst': tekst,
                'audio': None,
                'lokacja': stan_gracza.get('lokacja', 'nieznana'),
                'towarzysze': stan_gracza.get('towarzysze', []),
                'opcje': ['Napraw klucz API'],
                'quest_aktywny': None,
                'hp_gracza': stan_gracza.get('hp', 100),
                'zloto': stan_gracza.get('zloto', 0),
                'ekwipunek': session.get('postac', {}).get('ekwipunek', []),
                'ladownosc': {'zajete': len(session.get('postac', {}).get('ekwipunek', [])), 'max': 10}
            }), 200
        else:
            raise
    except RuntimeError as e:
        # Quota/limit
        error_msg = str(e)
        if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
            logger.warning(f"⚠️ GEMINI QUOTA: {e}")
            game_log.log_blad('GameMaster', str(e), {'endpoint': 'akcja', 'akcja': akcja_gracza})
            tekst = f"⚠️ **LIMIT API:** Przekroczono limit zapytań.\n\nSpróbuj ponownie za kilka minut."
            return jsonify({
                'tekst': tekst,
                'audio': None,
                'lokacja': stan_gracza.get('lokacja', 'nieznana'),
                'towarzysze': stan_gracza.get('towarzysze', []),
                'opcje': ['Spróbuj ponownie'],
                'quest_aktywny': None,
                'hp_gracza': stan_gracza.get('hp', 100),
                'zloto': stan_gracza.get('zloto', 0),
                'ekwipunek': session.get('postac', {}).get('ekwipunek', []),
                'ladownosc': {'zajete': len(session.get('postac', {}).get('ekwipunek', [])), 'max': 10}
            }), 200
        else:
            raise
    except TimeoutError as e:
        logger.error(f"❌ Timeout podczas akcji (GameMaster): {e}")
        game_log.log_blad('GameMaster', str(e), {'endpoint': 'akcja', 'akcja': akcja_gracza})
        tekst = "⚠️ Serwis AI (Mistrz Gry) nie odpowiada. Spróbuj ponownie za chwilę."
        return jsonify({
            'tekst': tekst,
            'audio': None,
            'lokacja': stan_gracza.get('lokacja', 'nieznana'),
            'towarzysze': stan_gracza.get('towarzysze', []),
            'opcje': ['Spróbuj ponownie'],
            'quest_aktywny': None,
            'hp_gracza': stan_gracza.get('hp', 100),
            'zloto': stan_gracza.get('zloto', 0),
            'ekwipunek': session.get('postac', {}).get('ekwipunek', []),
            'ladownosc': {'zajete': len(session.get('postac', {}).get('ekwipunek', [])), 'max': 10}
        }), 503
    except Exception as e:
        logger.error(f"❌ Błąd podczas akcji (GameMaster): {e}")
        game_log.log_blad('GameMaster', str(e), {'endpoint': 'akcja', 'akcja': akcja_gracza})
        # Przyjazny fallback
        tekst = f"⚠️ Błąd Mistrza Gry: {e}"
        return jsonify({
            'tekst': tekst,
            'audio': None,
            'lokacja': stan_gracza.get('lokacja', 'nieznana'),
            'towarzysze': stan_gracza.get('towarzysze', []),
            'opcje': ['Spróbuj ponownie'],
            'quest_aktywny': None,
            'hp_gracza': stan_gracza.get('hp', 100),
            'zloto': stan_gracza.get('zloto', 0),
            'ekwipunek': session.get('postac', {}).get('ekwipunek', []),
            'ladownosc': {'zajete': len(session.get('postac', {}).get('ekwipunek', [])), 'max': 10}
        }), 200
    
    # W przypadku gdy GameMaster zwróci błąd/komunikat o limicie (np. 429 quota)
    # — UWAGA: To nie powinno już się zdarzyć po nowych except blokach powyżej, ale zostawiam jako zabezpieczenie
    if not isinstance(wynik, dict):
        logger.error(f"❌ Niepoprawna odpowiedź MG (nie-dict): {wynik}")
        game_log.log_blad('GameMaster', 'Niepoprawna odpowiedź', {'endpoint': 'akcja', 'akcja': akcja_gracza, 'wynik': str(wynik)})
        tekst = "⚠️ Mistrz Gry zwrócił nieoczekiwaną odpowiedź. Spróbuj ponownie za chwilę."
        return jsonify({
            'tekst': tekst,
            'audio': None,
            'lokacja': stan_gracza.get('lokacja', 'nieznana'),
            'towarzysze': stan_gracza.get('towarzysze', []),
            'opcje': ['Spróbuj ponownie'],
            'quest_aktywny': None,
            'hp_gracza': stan_gracza.get('hp', 100),
            'zloto': stan_gracza.get('zloto', 0),
            'ekwipunek': session.get('postac', {}).get('ekwipunek', []),
            'ladownosc': {'zajete': len(session.get('postac', {}).get('ekwipunek', [])), 'max': 10}
        }), 200

    # Wyciągnij narrację
    narracja = wynik.get('narracja', 'Coś się dzieje...')
    
    # Loguj odpowiedź MG
    game_log.log_odpowiedz_mg(wynik)
    
    # WALIDUJ I APLIKUJ TRANSAKCJE
    transakcje = wynik.get('transakcje', {})
    sukces, komunikat = waliduj_i_aplikuj_transakcje(postac, transakcje)
    
    if not sukces:
        # Jeśli transakcja odrzucona - dodaj komunikat do narracji
        narracja += f"\n\n**System:** {komunikat}"
        logger.warning(f"❌ Transakcja odrzucona: {komunikat}")
    else:
        # Loguj udane transakcje
        if transakcje.get('zloto_zmiana') or transakcje.get('przedmioty_dodane') or transakcje.get('przedmioty_usuniete'):
            logger.info(f"💰 Transakcja: złoto={transakcje.get('zloto_zmiana', 0)}, dodane={transakcje.get('przedmioty_dodane', [])}, usunięte={transakcje.get('przedmioty_usuniete', [])}")
    
    # AKTUALIZUJ STAN POSTACI z odpowiedzi Gemini
    nowe_hp = wynik.get('hp_gracza')
    if nowe_hp is not None and isinstance(nowe_hp, (int, float)):
        # Walidacja - HP nie może być większe niż max ani mniejsze niż 0
        nowe_hp = int(nowe_hp)
        nowe_hp = max(0, min(nowe_hp, postac.get('hp_max', 100)))
        postac['hp'] = nowe_hp
    
    nowa_lokacja = wynik.get('lokacja')
    if nowa_lokacja:
        postac['lokacja'] = nowa_lokacja
    
    # Aktualizuj quest aktywny
    nowy_quest = wynik.get('quest_aktywny')
    if nowy_quest is not None:  # Może być None (quest zakończony) lub string
        postac['quest_aktywny'] = nowy_quest
    
    # Aktualizuj questy poboczne
    questy_poboczne = wynik.get('questy_poboczne')
    if questy_poboczne is not None:
        postac['questy_poboczne'] = questy_poboczne
    
    # Zapisz zaktualizowaną postać do sesji
    session['postac'] = postac
    
    # Zapisz do historii
    historia.append({"typ": "gracz", "tekst": akcja_gracza})
    historia.append({"typ": "narrator", "tekst": narracja})
    session['historia'] = historia
    session.modified = True
    
    # Zapisz do bazy (postać + historia)
    postac_id = session.get('postac_id')
    if not postac_id:
        logger.error("❌ KRYTYCZNY: Brak postac_id podczas akcji gracza!")
        return jsonify({'error': 'Sesja wygasła - wróć do menu głównego'}), 401
    
    # AUTOSAVE: Zapisz pełny stan gry (NOWY rekord za każdym razem)
    try:
        # 1. Zapisz historię tekstową (musi być przed nowym zapisem postaci)
        db.zapisz_historie(postac_id, akcja_gracza, narracja)
        
        # 2. Utwórz NOWY autosave (nie aktualizuj starego!)
        nowy_postac_id = db.zapisz_postac(postac, typ_zapisu='autosave')
        
        # 3. Zapisz kontekst AI dla nowego autosave (z uczestnikami!)
        historia_ai = game_master.get_historia()
        ostatnie_opcje = wynik.get('opcje', [])
        ostatni_uczestnicy = wynik.get('uczestnicy', [])  # NOWE: zapisz NPC
        db.zapisz_ai_context(nowy_postac_id, historia_ai, ostatnie_opcje, ostatni_uczestnicy)
        
        # 4. Zaktualizuj session z nowym ID
        session['postac_id'] = nowy_postac_id
        
        # 5. Usuń stare autosave'y (zachowaj max 5)
        usunietych = db.usun_stare_autosavy(limit=5)
        if usunietych > 0:
            logger.info(f"🗑️ Autosave: usunięto {usunietych} starych zapisów")
        
        logger.info(f"💾 Autosave: nowy_id={nowy_postac_id}, AI historia={len(historia_ai)} msg, opcje={len(ostatnie_opcje)}")
            
    except Exception as e:
        logger.error(f"❌ Błąd autosave: {e}")
        # Kontynuuj mimo błędu - nie przerywaj gry
    
    # AUTO-LOGOWANIE WYDARZEŃ
    try:
        # Walka
        if wynik.get('walka'):
            db.dodaj_wydarzenie(
                postac_id, 'walka', 'Walka!', 
                f"Starcie: {narracja[:150]}...", 
                postac.get('lokacja', 'nieznana'),
                {'uczestnicy': wynik.get('uczestnicy', [])}
            )
        
        # Rekrutacja towarzyszy
        nowi_towarzysze = wynik.get('towarzysze', [])
        starzy_towarzysze = postac.get('towarzysze', [])
        if len(nowi_towarzysze) > len(starzy_towarzysze):
            nowy = [t for t in nowi_towarzysze if t not in starzy_towarzysze]
            if nowy:
                db.dodaj_wydarzenie(
                    postac_id, 'rekrutacja', f'Rekrutacja: {nowy[0]}',
                    f'Nowy towarzysz dołącza do drużyny!',
                    postac.get('lokacja', 'nieznana')
                )
        
        # Handel/transakcje
        if transakcje.get('zloto_zmiana') or transakcje.get('przedmioty_dodane'):
            zloto_delta = transakcje.get('zloto_zmiana', 0)
            przedmioty = transakcje.get('przedmioty_dodane', [])
            if abs(zloto_delta) > 0 or przedmioty:
                db.dodaj_wydarzenie(
                    postac_id, 'handel', 'Transakcja',
                    f'Wymiana dóbr: złoto {zloto_delta:+d}, przedmioty: {", ".join(przedmioty) if przedmioty else "brak"}',
                    postac.get('lokacja', 'nieznana'),
                    {'zloto': zloto_delta, 'przedmioty': przedmioty}
                )
        
        # Zmiana lokacji (podróż)
        if nowa_lokacja and nowa_lokacja != historia[-3].get('lokacja') if len(historia) >= 3 else True:
            db.dodaj_wydarzenie(
                postac_id, 'podróż', f'Podróż do: {nowa_lokacja}',
                'Wyruszasz w drogę...',
                nowa_lokacja
            )
    except Exception as e:
        logger.warning(f"⚠️ Błąd auto-logowania wydarzeń: {e}")
    
    # Generuj audio z wieloma głosami
    plec_gracza = postac.get('plec', 'mezczyzna')
    audio_path = tts.syntezuj_multi_voice(narracja, plec_gracza)
    game_log.log_tts(narracja, "multi-voice", audio_path is not None)
    
    # Przygotuj URL audio (lokalnie: /audio/plik.wav, cloud: pełny URL)
    if audio_path:
        if audio_path.startswith('http'):
            audio_url = audio_path
        else:
            audio_url = f"/audio/{os.path.basename(audio_path)}"
    else:
        audio_url = None
    
    # Przetworz towarzyszy (HP, auto-leczenie, śmierć/reanimacja)
    towarzysze_raw = wynik.get('towarzysze', [])
    towarzysze, komunikaty_towarzyszy = przetworz_towarzyszy(towarzysze_raw, postac)
    
    # Dodaj komunikaty do narracji jeśli są
    if komunikaty_towarzyszy:
        narracja += "\n\n" + "\n".join(komunikaty_towarzyszy)
    
    # Oblicz ładowność
    zajete, max_slotow, worki, zwierze = oblicz_ladownosc(postac)
    
    # DEBUG: Loguj ekwipunek przed wysłaniem
    ekwipunek_aktualny = postac.get('ekwipunek', [])
    logger.info(f"🎒 Wysyłam ekwipunek do frontu: {ekwipunek_aktualny} (ilość: {len(ekwipunek_aktualny)})")
    
    # SYSTEM HP PRZECIWNIKÓW
    uczestnicy_raw = wynik.get('uczestnicy', [])
    obrazenia_data = wynik.get('obrazenia')  # Pobierz strukturalne dane o obrażeniach
    uczestnicy_z_hp = przetworz_hp_przeciwnikow(uczestnicy_raw, narracja, obrazenia_data)
    
    return jsonify({
        "tekst": narracja,
        "audio": audio_url,
        "lokacja": wynik.get('lokacja'),
        "towarzysze": towarzysze,
        "uczestnicy": uczestnicy_z_hp,  # NOWE: wrogowie/NPC/bestie z HP
        "opcje": wynik.get('opcje', []),
        "quest_aktywny": wynik.get('quest_aktywny'),
        "questy_poboczne": wynik.get('questy_poboczne', []),
        "hp_gracza": wynik.get('hp_gracza', 100),
        "zloto": postac.get('zloto', 0),
        "ekwipunek": ekwipunek_aktualny,
        "ladownosc": {"zajete": zajete, "max": max_slotow}
    })


@app.route('/audio/<filename>')
def audio(filename):
    """Serwuje pliki audio"""
    audio_dir = BASE_DIR / "audio"
    return send_file(audio_dir / filename, mimetype='audio/wav')


@app.route('/debug/slow')
def debug_slow():
    """Endpoint testowy - sztuczne opóźnienie, pomaga reprodukować timeouty klienta"""
    import time
    time.sleep(30)
    return jsonify({'ok': True, 'msg': 'done after sleep'})


@app.route('/postac')
def postac_info():
    """Zwraca dane postaci"""
    return jsonify(session.get('postac', {}))


@app.route('/health')
def health():
    """Healthcheck - prosty endpoint do sprawdzenia żywotności aplikacji"""
    try:
        # Prosty check DB
        _ = db.lista_postaci(limit=1)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"❌ Healthcheck failed: {e}")
        return jsonify({'status': 'error', 'detail': str(e)}), 500


# Globalny handler wyjątków - loguj i zwróć przyjazny JSON
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    logger.error(f"❌ Nieobsłużony wyjątek: {e}\n{tb}")
    game_log.log_blad('Unhandled', str(e), {'trace': tb})
    # Jeśli to błąd połączenia z Gemini/timeout zwróć 503
    # Pozwól HTTPException przejść (np. 404) — nie traktujemy jej jako 500
    if isinstance(e, HTTPException):
        return e

    if isinstance(e, TimeoutError):
        return jsonify({'error': 'Timeout zewnętrznego serwisu, spróbuj ponownie'}), 503
    return jsonify({'error': 'Wewnętrzny błąd serwera'}), 500


@app.route('/logi')
def panel_logow():
    """Panel administracyjny z logami"""
    return render_template('logi.html')


@app.route('/api/logi')
def api_logi():
    """API - zwraca ostatnie logi"""
    ile = request.args.get('ile', 50, type=int)
    logi = game_log.pobierz_ostatnie_logi(ile)
    stats = game_log.pobierz_statystyki()
    return jsonify({
        "logi": logi,
        "statystyki": stats
    })


# Map API removed — functionality intentionally disabled (feature removed)


@app.route('/api/dziennik/<int:postac_id>')
def api_dziennik(postac_id):
    """API - dziennik wydarzeń gracza"""
    try:
        typ_filter = request.args.get('typ')
        limit = request.args.get('limit', 50, type=int)
        
        wydarzenia = db.pobierz_wydarzenia(postac_id, limit=limit, typ=typ_filter)
        
        # Statystyki
        wszystkie = db.pobierz_wydarzenia(postac_id, limit=1000)
        statystyki = {
            "walki": len([e for e in wszystkie if e['typ'] == 'walka']),
            "podroze": len([e for e in wszystkie if e['typ'] == 'podróż']),
            "handel": len([e for e in wszystkie if e['typ'] == 'handel']),
            "rekrutacje": len([e for e in wszystkie if e['typ'] == 'rekrutacja']),
            "questy": len([e for e in wszystkie if e['typ'] == 'quest'])
        }
        
        # Konwersja Row na dict
        wydarzenia_list = []
        for w in wydarzenia:
            wydarzenia_list.append({
                "id": w['id'],
                "typ": w['typ'],
                "tytul": w['tytul'],
                "opis": w['opis'],
                "lokalizacja": w['lokalizacja'],
                "nagroda": json.loads(w['nagroda']) if w['nagroda'] else {},
                "created_at": w['created_at']
            })
        
        return jsonify({
            "wydarzenia": wydarzenia_list,
            "statystyki": statystyki
        })
    except Exception as e:
        logger.error(f"❌ Błąd API dziennika: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/model', methods=['GET', 'POST'])
def admin_model():
    """Admin endpoint: GET shows current model, POST changes model at runtime.

    Optional protection via ADMIN_TOKEN env variable (header X-ADMIN-TOKEN or JSON body 'token').
    """
    admin_token = os.getenv('ADMIN_TOKEN')

    if request.method == 'GET':
        return jsonify({"model": game_master.current_model()}), 200

    # POST -> change model
    data = request.json or {}
    token = request.headers.get('X-ADMIN-TOKEN') or data.get('token')

    if admin_token and token != admin_token:
        return jsonify({'ok': False, 'error': 'Unauthorized (invalid admin token)'}), 401

    new_model = data.get('model')
    if not new_model:
        return jsonify({'ok': False, 'error': 'missing model name'}), 400

    ok = game_master.set_model(new_model)
    if ok:
        return jsonify({'ok': True, 'model': game_master.current_model()}), 200
    return jsonify({'ok': False, 'error': 'failed to set model, check logs'}), 500


@app.route('/admin/usage')
def admin_usage():
    """Return basic usage / stats from game logs. Protected via ADMIN_TOKEN if present."""
    admin_token = os.getenv('ADMIN_TOKEN')
    token = request.headers.get('X-ADMIN-TOKEN')
    if admin_token and token != admin_token:
        return jsonify({'ok': False, 'error': 'Unauthorized (invalid admin token)'}), 401

    stats = game_log.pobierz_statystyki()
    recent = game_log.pobierz_ostatnie_logi(200)
    return jsonify({'ok': True, 'statystyki': stats, 'recent': recent})


@app.route('/api/logi/plik')
def api_logi_plik():
    """API - zwraca logi z pliku game.log"""
    log_file = BASE_DIR / "logs" / "game.log"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:]  # Ostatnie 100 linii
        return jsonify({"logi": lines})
    return jsonify({"logi": [], "error": "Brak pliku logów"})


@app.route('/wymien_przedmiot', methods=['POST'])
def wymien_przedmiot():
    """
    Wymiana przedmiotu z towarzyszem
    - typ: 'daj' (gracz -> towarzysz, 100% sukces) lub 'popros' (towarzysz -> gracz, 50% sukces)
    - towarzysz_imie: imię towarzyszy
    - przedmiot: nazwa przedmiotu
    """
    import random
    
    data = request.json
    typ = data.get('typ')  # 'daj' lub 'popros'
    towarzysz_imie = data.get('towarzysz_imie')
    przedmiot = data.get('przedmiot')
    
    postac = session.get('postac', {})
    towarzysze = postac.get('towarzysze', [])
    ekwipunek_gracza = postac.get('ekwipunek', [])
    
    # Znajdź towarzyszy
    towarzysz = next((t for t in towarzysze if t.get('imie') == towarzysz_imie), None)
    if not towarzysz:
        return jsonify({"sukces": False, "komunikat": f"Nie znaleziono towarzyszy {towarzysz_imie}!"})
    
    ekwipunek_towarzyszy = towarzysz.get('ekwipunek', [])
    
    if typ == 'daj':
        # Gracz daje przedmiot towarzyszowi (100% sukces)
        if przedmiot not in ekwipunek_gracza:
            return jsonify({"sukces": False, "komunikat": f"Nie masz {przedmiot} w ekwipunku!"})
        
        ekwipunek_gracza.remove(przedmiot)
        ekwipunek_towarzyszy.append(przedmiot)
        towarzysz['ekwipunek'] = ekwipunek_towarzyszy
        postac['ekwipunek'] = ekwipunek_gracza
        
        komunikat = f"✅ Dałeś **{przedmiot}** towarzyszowi **{towarzysz_imie}**."
        
    elif typ == 'popros':
        # Gracz prosi o przedmiot (50% sukces)
        if przedmiot not in ekwipunek_towarzyszy:
            return jsonify({"sukces": False, "komunikat": f"{towarzysz_imie} nie ma {przedmiot}!"})
        
        szansa = random.randint(1, 100)
        if szansa <= 50:
            # Sukces
            ekwipunek_towarzyszy.remove(przedmiot)
            ekwipunek_gracza.append(przedmiot)
            towarzysz['ekwipunek'] = ekwipunek_towarzyszy
            postac['ekwipunek'] = ekwipunek_gracza
            komunikat = f"✅ **{towarzysz_imie}** dał Ci **{przedmiot}**!"
        else:
            # Porażka
            komunikat = f"❌ **{towarzysz_imie}** odmawia oddania **{przedmiot}**..."
            return jsonify({"sukces": False, "komunikat": komunikat})
    else:
        return jsonify({"sukces": False, "komunikat": "Nieznany typ wymiany!"})
    
    # Zapisz zmiany
    postac['towarzysze'] = towarzysze
    session['postac'] = postac
    session.modified = True
    
    rows = db.aktualizuj_postac(session.get('postac_id'), {
        'ekwipunek': ekwipunek_gracza,
        'towarzysze': towarzysze
    })
    if rows == 0:
        pid = session.get('postac_id')
        logger.warning(f"⚠️ Aktualizacja ekwipunku/towarzyszy zwróciła 0 wierszy (postac_id={pid}). Tworzę nowy zapis.")
        new_id = db.zapisz_postac(postac)
        session['postac_id'] = new_id
        logger.info(f"🔁 Nowy zapis utworzony z ID: {new_id}")
    
    return jsonify({
        "sukces": True,
        "komunikat": komunikat,
        "ekwipunek": ekwipunek_gracza,
        "towarzysze": towarzysze
    })


@app.route('/api/podpowiedzi')
def api_podpowiedzi():
    """Endpoint zwracający podpowiedzi dla miasta gracza"""
    postac = session.get('postac')
    if not postac:
        return jsonify({"error": "Brak postaci"}), 400
    
    miasto = postac.get('lokacja', 'Gniezno')
    podpowiedzi = pobierz_podpowiedzi_dla_miasta(miasto)
    
    return jsonify(podpowiedzi)


if __name__ == '__main__':
    logger.info("🏰 Uruchamiam Słowiańskie Dziedzictwo...")
    db.inicjalizuj()
    
    # Dynamiczny port dla Cloud Run (lub 5000 lokalnie)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)

