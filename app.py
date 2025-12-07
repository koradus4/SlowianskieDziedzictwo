"""
Słowiańskie Dziedzictwo - Gra Fabularna
Flask + Gemini AI + Piper TTS
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_session import Session
import sqlite3
import random
import os
import json
from pathlib import Path
from game_master import GameMaster
from tts_engine import TTSEngine
from database import Database
from game_logger import game_log, logger
from items import PRZEDMIOTY, get_item, get_all_item_names

app = Flask(__name__)
app.secret_key = 'slowianski_sekret_2025'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Ścieżki
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "game.db"

# Inicjalizacja
db = Database(DB_PATH)
game_master = GameMaster()
tts = TTSEngine(BASE_DIR.parent / "PodcastGenerator")

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
        "lokacja": "gniezno",
        "questy": ["Zjednoczenie Plemion"]
    }
    
    # Zapisz do sesji i bazy
    session['postac'] = postac
    session['historia'] = []
    
    postac_id = db.zapisz_postac(postac)
    session['postac_id'] = postac_id
    
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


@app.route('/zapisz_gre', methods=['POST'])
def zapisz_gre():
    """Zapisuje aktualną grę (max 10 zapisów)"""
    try:
        postac = session.get('postac', {})
        postac_id = session.get('postac_id')
        
        if not postac_id:
            return jsonify({'ok': False, 'error': 'Brak aktywnej gry'})
        
        # Zapisz postać do bazy (bez json.dumps - database.py to robi)
        db.aktualizuj_postac(postac_id, {
            'hp': postac.get('hp', 100),
            'lokacja': postac.get('lokacja', 'gniezno'),
            'zloto': postac.get('zloto', 0),
            'ekwipunek': postac.get('ekwipunek', []),
            'towarzysze': postac.get('towarzysze', [])
        })
        
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
    """Zwraca listę zapisanych gier (max 10)"""
    try:
        zapisy = db.lista_postaci(limit=10)
        return jsonify({'zapisy': zapisy})
    except Exception as e:
        logger.error(f"❌ Błąd listowania zapisów: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/usun_zapis/<int:postac_id>', methods=['DELETE'])
def usun_zapis(postac_id):
    """Usuwa zapisaną grę"""
    try:
        sukces = db.usun_postac(postac_id)
        
        if sukces:
            logger.info(f"🗑️ Usunięto zapis ID: {postac_id}")
            return jsonify({'ok': True, 'message': 'Zapis usunięty'})
        else:
            return jsonify({'ok': False, 'error': 'Nie znaleziono zapisu'})
            
    except Exception as e:
        logger.error(f"❌ Błąd usuwania zapisu: {e}")
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/wczytaj_zapis/<int:postac_id>')
def wczytaj_zapis(postac_id):
    """Wczytuje zapisaną grę"""
    try:
        postac = db.wczytaj_postac(postac_id)
        
        if not postac:
            return jsonify({'ok': False, 'error': 'Nie znaleziono zapisu'}), 404
        
        # Wyczyść poprzednią sesję
        session.clear()
        
        # Załaduj pełny stan
        session['postac'] = postac
        session['postac_id'] = postac_id
        session['historia'] = db.wczytaj_historie(postac_id, limit=100)
        
        # Przywróć kontekst AI
        game_master.aktualne_hp = postac['hp']
        game_master.hp_max = postac['hp_max']
        
        logger.info(f"📂 Gra wczytana: {postac.get('imie')} (ID: {postac_id})")
        return jsonify({'ok': True, 'redirect': '/gra'})
        
    except Exception as e:
        logger.error(f"❌ Błąd wczytywania gry: {e}")
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
            'hp_max': hp_max
        }, lista_przedmiotow=lista_przedmiotow)
    except Exception as e:
        # Loguj i zwróć przyjazny komunikat zamiast 500
        logger.error(f"❌ Błąd podczas komunikacji z GameMaster: {e}")
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

    # Wykryj czy MG zwraca komunikat o limicie / błędzie (np. 429/quota)
    narracja_lower = (narracja or '').lower()
    if any(token in narracja_lower for token in ['429', 'quota', 'exceeded', 'przekroc', 'ograniczen', 'limit', 'spróbuj ponownie']):
        logger.warning(f"⚠️ Odkryto komunikat o limicie/API w odpowiedzi MG (start gry): {narracja}")
        game_log.log_blad('GameMaster', 'Quota/Limit detected in response (start)', {'endpoint': 'rozpocznij_przygode', 'wynik': narracja})
        tekst = (
            "⚠️ Mistrz Gry: wystąpił problem z serwisem AI (limit lub błąd połączenia). "
            "Spróbuj ponownie za kilka sekund lub sprawdź ustawienia GEMINI_API_KEY."
        )
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
    
    # Zapisz do bazy (postać + towarzysze)
    db.aktualizuj_postac(session.get('postac_id'), {
        'hp': postac.get('hp', hp),
        'zloto': postac.get('zloto', 0),
        'ekwipunek': postac.get('ekwipunek', []),
        'towarzysze': towarzysze
    })
    db.zapisz_historie(session.get('postac_id'), "ROZPOCZĘCIE GRY", narracja)
    
    session.modified = True
    
    # Generuj audio z wieloma głosami
    plec_gracza = session['postac'].get('plec', 'mezczyzna')
    audio_path = tts.syntezuj_multi_voice(narracja, plec_gracza)
    game_log.log_tts(narracja, "multi-voice", audio_path is not None, str(audio_path) if audio_path else None)
    
    # Oblicz ładowność
    zajete, max_slotow, worki, zwierze = oblicz_ladownosc(postac)
    
    return jsonify({
        "tekst": narracja,
        "audio": f"/audio/{os.path.basename(audio_path)}" if audio_path else None,
        "lokacja": wynik.get('lokacja', 'Gniezno'),
        "towarzysze": towarzysze,  # Używaj znormalizowanych towarzyszy
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
        'towarzysze': postac.get('towarzysze', [])
    }
    
    # Użyj nowego API GameMaster z aktualnym stanem + lista przedmiotów
    try:
        wynik = game_master.akcja(akcja_gracza, stan_gracza, lista_przedmiotow)
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
    # Gemini potrafi zwrócić tekst z informacją o przekroczeniu limitu zamiast poprawnego JSON-a.
    # Wykryj typowe wskazówki (429, quota, exceeded, Spróbuj ponownie) i zrób przyjazny fallback.
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

    # Szukaj fragmentów wskazujących na błąd/quota
    narracja_lower = (narracja or '').lower()
    if any(token in narracja_lower for token in ['429', 'quota', 'exceeded', 'przekroc', 'ograniczen', 'limit', 'spróbuj ponownie']):
        logger.warning(f"⚠️ Odkryto komunikat o limicie/API w odpowiedzi MG: {narracja}")
        game_log.log_blad('GameMaster', 'Quota/Limit detected in response', {'endpoint': 'akcja', 'akcja': akcja_gracza, 'wynik': narracja})
        tekst = (
            "⚠️ Mistrz Gry: wystąpił problem z serwisem AI (limit lub błąd połączenia). "
            "Spróbuj ponownie za kilka sekund lub sprawdź ustawienia GEMINI_API_KEY."
        )
        # Zwróć przyjazny fallback — bez wywoływania TTS, aby uniknąć dodatkowych błędów
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
    
    # Zapisz zaktualizowaną postać do sesji
    session['postac'] = postac
    
    # Zapisz do historii
    historia.append({"typ": "gracz", "tekst": akcja_gracza})
    historia.append({"typ": "narrator", "tekst": narracja})
    session['historia'] = historia
    session.modified = True
    
    # Zapisz do bazy (postać + historia)
    db.aktualizuj_postac(session.get('postac_id'), {
        'hp': postac['hp'], 
        'lokacja': postac.get('lokacja', 'gniezno'),
        'zloto': postac.get('zloto', 0),
        'ekwipunek': postac.get('ekwipunek', []),
        'towarzysze': postac.get('towarzysze', [])
    })
    db.zapisz_historie(session.get('postac_id'), akcja_gracza, narracja)
    
    # Generuj audio z wieloma głosami
    plec_gracza = postac.get('plec', 'mezczyzna')
    audio_path = tts.syntezuj_multi_voice(narracja, plec_gracza)
    game_log.log_tts(narracja, "multi-voice", audio_path is not None)
    
    # Przetworz towarzyszy (HP, auto-leczenie, śmierć/reanimacja)
    towarzysze_raw = wynik.get('towarzysze', [])
    towarzysze, komunikaty_towarzyszy = przetworz_towarzyszy(towarzysze_raw, postac)
    
    # Dodaj komunikaty do narracji jeśli są
    if komunikaty_towarzyszy:
        narracja += "\n\n" + "\n".join(komunikaty_towarzyszy)
    
    # Oblicz ładowność
    zajete, max_slotow, worki, zwierze = oblicz_ladownosc(postac)
    
    return jsonify({
        "tekst": narracja,
        "audio": f"/audio/{os.path.basename(audio_path)}" if audio_path else None,
        "lokacja": wynik.get('lokacja'),
        "towarzysze": towarzysze,
        "uczestnicy": wynik.get('uczestnicy', []),  # NOWE: wrogowie/NPC/bestie
        "opcje": wynik.get('opcje', []),
        "quest_aktywny": wynik.get('quest_aktywny'),
        "hp_gracza": wynik.get('hp_gracza', 100),
        "zloto": postac.get('zloto', 0),
        "ekwipunek": postac.get('ekwipunek', []),
        "ladownosc": {"zajete": zajete, "max": max_slotow}
    })


@app.route('/audio/<filename>')
def audio(filename):
    """Serwuje pliki audio"""
    audio_dir = BASE_DIR / "audio"
    return send_file(audio_dir / filename, mimetype='audio/wav')


@app.route('/postac')
def postac_info():
    """Zwraca dane postaci"""
    return jsonify(session.get('postac', {}))


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
    
    db.aktualizuj_postac(session.get('postac_id'), {
        'ekwipunek': ekwipunek_gracza,
        'towarzysze': towarzysze
    })
    
    return jsonify({
        "sukces": True,
        "komunikat": komunikat,
        "ekwipunek": ekwipunek_gracza,
        "towarzysze": towarzysze
    })


if __name__ == '__main__':
    logger.info("🏰 Uruchamiam Słowiańskie Dziedzictwo...")
    db.inicjalizuj()
    app.run(debug=True, port=5000)
