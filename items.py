"""
Baza przedmiotów - Słowiańskie Dziedzictwo
Przedmioty zdefiniowane: broń, zbroje, mikstury, jedzenie, zwoje
Przedmioty questowe: generowane przez Gemini
"""

# ============================================
# BAZA PRZEDMIOTÓW
# ============================================

PRZEDMIOTY = {
    # ========== BROŃ 1-RĘCZNA ==========
    "Drewniany kij": {
        "dmg": 2,
        "cena": 5,
        "typ": "bron_1r",
        "opis": "Prosty kij z twardego drewna"
    },
    "Nóż żelazny": {
        "dmg": 3,
        "cena": 10,
        "typ": "bron_1r",
        "opis": "Ostry nóż wykuty z żelaza"
    },
    "Miecz żelazny": {
        "dmg": 5,
        "cena": 50,
        "typ": "bron_1r",
        "opis": "Solidny miecz żelazny"
    },
    "Topór bojowy": {
        "dmg": 6,
        "cena": 60,
        "typ": "bron_1r",
        "opis": "Ciężki topór do walki wręcz"
    },
    "Miecz stalowy": {
        "dmg": 8,
        "cena": 120,
        "typ": "bron_1r",
        "opis": "Miecz z hartowanej stali"
    },
    "Szabla": {
        "dmg": 7,
        "cena": 100,
        "typ": "bron_1r",
        "opis": "Lekka, zakrzywiona szabla"
    },
    
    # ========== BROŃ 2-RĘCZNA ==========
    "Młot bojowy": {
        "dmg": 10,
        "cena": 150,
        "typ": "bron_2r",
        "req_sila": 12,
        "opis": "Potężny młot wymagający siły"
    },
    "Wielki miecz": {
        "dmg": 12,
        "cena": 200,
        "typ": "bron_2r",
        "req_sila": 14,
        "opis": "Ogromny miecz dwuręczny"
    },
    "Topór dwuręczny": {
        "dmg": 11,
        "cena": 180,
        "typ": "bron_2r",
        "req_sila": 13,
        "opis": "Topór bojowy dla silnych wojowników"
    },
    
    # ========== BROŃ DYSTANSOWA ==========
    "Łuk krótki": {
        "dmg": 4,
        "cena": 40,
        "typ": "luk",
        "req_zrecznosc": 10,
        "opis": "Prosty łuk do polowania"
    },
    "Łuk długi": {
        "dmg": 6,
        "cena": 80,
        "typ": "luk",
        "req_zrecznosc": 12,
        "opis": "Potężny łuk bojowy"
    },
    "Kusza": {
        "dmg": 8,
        "cena": 150,
        "typ": "kusza",
        "req_zrecznosc": 10,
        "opis": "Mechaniczna kusza z dużą siłą rażenia"
    },
    "Strzały (10 szt)": {
        "amunicja": 10,
        "cena": 5,
        "typ": "amunicja",
        "opis": "Pęk 10 strzał do łuku"
    },
    "Bełty (10 szt)": {
        "amunicja": 10,
        "cena": 8,
        "typ": "amunicja",
        "opis": "Pęk 10 bełtów do kuszy"
    },
    
    # ========== ZBROJE ==========
    "Ubranie skórzane": {
        "def": 1,
        "cena": 20,
        "typ": "zbroja",
        "opis": "Proste ubranie ze wzmocnionej skóry"
    },
    "Kaftan skórzany": {
        "def": 3,
        "cena": 50,
        "typ": "zbroja",
        "opis": "Kaftan z grubej skóry"
    },
    "Kolczuga": {
        "def": 5,
        "cena": 150,
        "typ": "zbroja",
        "opis": "Kolczuga z metalowych ogniw"
    },
    "Zbroja płytowa": {
        "def": 8,
        "cena": 400,
        "typ": "zbroja",
        "req_sila": 12,
        "opis": "Ciężka zbroja z metalowych płyt"
    },
    "Zbroja rycerska": {
        "def": 10,
        "cena": 600,
        "typ": "zbroja",
        "req_sila": 14,
        "opis": "Najlepsza zbroja dla rycerzy"
    },
    
    # ========== TARCZE ==========
    "Tarcza drewniana": {
        "def": 2,
        "cena": 15,
        "typ": "tarcza",
        "opis": "Okrągła tarcza z drewna"
    },
    "Tarcza żelazna": {
        "def": 3,
        "cena": 40,
        "typ": "tarcza",
        "opis": "Tarcza okuta żelazem"
    },
    "Tarcza stalowa": {
        "def": 5,
        "cena": 100,
        "typ": "tarcza",
        "opis": "Wytrzymała tarcza stalowa"
    },
    
    # ========== MIKSTURY ==========
    "Mikstura lecznicza mała": {
        "hp_heal": 10,
        "cena": 15,
        "typ": "mikstura",
        "consumable": True,
        "opis": "Leczy 10 HP"
    },
    "Mikstura lecznicza": {
        "hp_heal": 20,
        "cena": 30,
        "typ": "mikstura",
        "consumable": True,
        "opis": "Leczy 20 HP"
    },
    "Mikstura lecznicza wielka": {
        "hp_heal": 50,
        "cena": 80,
        "typ": "mikstura",
        "consumable": True,
        "opis": "Leczy 50 HP"
    },
    "Mikstura siły": {
        "bonus_sila": 2,
        "czas_trwania": 3,
        "cena": 50,
        "typ": "mikstura_buff",
        "consumable": True,
        "opis": "Daje +2 Siły na 3 tury"
    },
    "Mikstura szybkości": {
        "bonus_zrecznosc": 2,
        "czas_trwania": 3,
        "cena": 50,
        "typ": "mikstura_buff",
        "consumable": True,
        "opis": "Daje +2 Zręczności na 3 tury"
    },
    "Antidotum": {
        "usuwa_trucizna": True,
        "cena": 25,
        "typ": "mikstura",
        "consumable": True,
        "opis": "Usuwa truciznę"
    },
    
    # ========== JEDZENIE ==========
    "Chleb": {
        "hp_heal": 5,
        "cena": 2,
        "typ": "jedzenie",
        "consumable": True,
        "opis": "Bochenek świeżego chleba"
    },
    "Ser": {
        "hp_heal": 7,
        "cena": 5,
        "typ": "jedzenie",
        "consumable": True,
        "opis": "Kawałek dojrzałego sera"
    },
    "Suszone mięso": {
        "hp_heal": 10,
        "cena": 8,
        "typ": "jedzenie",
        "consumable": True,
        "opis": "Porcja suszonego mięsa"
    },
    "Pieczony kurczak": {
        "hp_heal": 15,
        "cena": 12,
        "typ": "jedzenie",
        "consumable": True,
        "opis": "Smakowity pieczony kurczak"
    },
    
    # ========== NAPOJE ==========
    "Bukłak z wodą": {
        "hp_heal": 3,
        "cena": 1,
        "typ": "napoj",
        "consumable": True,
        "opis": "Bukłak czystej wody"
    },
    "Piwo": {
        "hp_heal": 5,
        "bonus_charyzma": 1,
        "cena": 3,
        "typ": "napoj",
        "consumable": True,
        "opis": "Kufel świeżego piwa"
    },
    "Miód pitny": {
        "hp_heal": 8,
        "bonus_szczescie": 1,
        "cena": 10,
        "typ": "napoj",
        "consumable": True,
        "opis": "Słodki miód pitny"
    },
    
    # ========== ZWOJE MAGICZNE ==========
    "Zwój Ognia": {
        "dmg_mag": 15,
        "cena": 50,
        "typ": "zwoj_atak",
        "consumable": True,
        "opis": "Zwój rzucający kulę ognia"
    },
    "Zwój Lodu": {
        "dmg_mag": 12,
        "spowolnienie": True,
        "cena": 45,
        "typ": "zwoj_atak",
        "consumable": True,
        "opis": "Zwój mrozu spowalniający wroga"
    },
    "Zwój Uzdrowienia": {
        "hp_heal": 30,
        "cena": 60,
        "typ": "zwoj_heal",
        "consumable": True,
        "opis": "Magiczny zwój leczący rany"
    },
    "Zwój Teleportacji": {
        "teleport": "gniezno",
        "cena": 100,
        "typ": "zwoj_util",
        "consumable": True,
        "opis": "Teleportuje do Gniezna"
    },
    "Zwój Ochrony": {
        "bonus_def": 5,
        "czas_trwania": 3,
        "cena": 70,
        "typ": "zwoj_buff",
        "consumable": True,
        "opis": "Daje +5 Obrony na 3 tury"
    },
    
    # ========== KLEJNOTY I BIŻUTERIA ==========
    "Bursztyn": {
        "cena": 20,
        "typ": "klejnot",
        "opis": "Kawałek słonecznego bursztynu"
    },
    "Srebrny pierścień": {
        "cena": 50,
        "bonus_charyzma": 1,
        "typ": "bizuteria",
        "opis": "Elegancki srebrny pierścień"
    },
    "Złoty naszyjnik": {
        "cena": 100,
        "bonus_charyzma": 2,
        "typ": "bizuteria",
        "opis": "Luksusowy złoty naszyjnik"
    },
    
    # ========== SUROWCE ==========
    "Ruda żelaza": {
        "cena": 5,
        "typ": "surowiec",
        "opis": "Kawałek rudy żelaza"
    },
    "Skóra": {
        "cena": 8,
        "typ": "surowiec",
        "opis": "Wyprawiona skóra zwierzęca"
    },
    "Zioła lecznicze": {
        "cena": 10,
        "typ": "surowiec",
        "opis": "Pęk ziół o właściwościach leczniczych"
    },
    
    # ========== NARZĘDZIA ==========
    "Młotek kowalski": {
        "cena": 15,
        "typ": "narzedzie",
        "opis": "Narzędzie kowalskie"
    },
    "Kilof": {
        "cena": 20,
        "typ": "narzedzie",
        "opis": "Kilof do kopania"
    },
    "Wędka": {
        "cena": 10,
        "typ": "narzedzie",
        "opis": "Wędka do łowienia ryb"
    },
    "Lina (10m)": {
        "cena": 5,
        "typ": "narzedzie",
        "opis": "10 metrów mocnej liny"
    },
    "Pochodnia": {
        "cena": 2,
        "typ": "narzedzie",
        "opis": "Pochodnia oświetlająca drogę"
    },
    "Sakwa": {
        "pojemnosc": 10,
        "cena": 15,
        "typ": "narzedzie",
        "opis": "Skórzana sakwa zwiększająca ekwipunek"
    },
    
    # ========== ARTEFAKTY LEGENDARNE ==========
    "Szczerbiec": {
        "dmg": 20,
        "legendarny": True,
        "cena": 9999,
        "typ": "artefakt",
        "opis": "Legendarny miecz koronacyjny królów Polski"
    },
    "Włócznia Św. Maurycego": {
        "dmg": 18,
        "bonus_szczescie": 3,
        "legendarny": True,
        "cena": 9999,
        "typ": "artefakt",
        "opis": "Święta włócznia przynoszca szczęście w boju"
    },
    "Korona Chrobrego": {
        "bonus_charyzma": 5,
        "legendarny": True,
        "cena": 9999,
        "typ": "artefakt",
        "opis": "Korona pierwszego króla Polski"
    },
    "Amulet Peruna": {
        "bonus_sila": 3,
        "odpornosc_piorun": True,
        "cena": 500,
        "typ": "amulet",
        "opis": "Amulet boga piorunów dający siłę"
    },
    
    # ========== EKWIPUNEK I TRANSPORT ==========
    "Worek lniany": {
        "cena": 10,
        "typ": "worek",
        "slots": 30,
        "opis": "Prosty worek z lnu zwiększający ładowność o 30 slotów"
    },
    "Worek skórzany": {
        "cena": 25,
        "typ": "worek",
        "slots": 30,
        "opis": "Wytrzymały worek skórzany zwiększający ładowność o 30 slotów"
    },
    "Koń": {
        "cena": 100,
        "typ": "zwierze",
        "slots": 50,
        "szybkosc": True,
        "opis": "Wierzchowiec zwiększający ładowność o 50 slotów i przyspieszający podróże"
    },
    "Osioł": {
        "cena": 60,
        "typ": "zwierze",
        "slots": 50,
        "opis": "Zwierzę juczne zwiększające ładowność o 50 slotów"
    },
    "Wóz": {
        "cena": 200,
        "typ": "transport",
        "slots": 100,
        "wymaga": "Koń",
        "opis": "Wóz zaprzęgowy (wymaga konia) zwiększający ładowność o 100 slotów"
    },
}


# ============================================
# FUNKCJE POMOCNICZE
# ============================================

def get_item(nazwa: str) -> dict:
    """Zwraca statystyki przedmiotu lub None jeśli nie istnieje"""
    return PRZEDMIOTY.get(nazwa)


def is_defined_item(nazwa: str) -> bool:
    """Sprawdza czy przedmiot jest w bazie (nie questowy)"""
    return nazwa in PRZEDMIOTY


def can_use_item(nazwa: str, postac: dict) -> tuple:
    """
    Sprawdza czy postać może użyć przedmiotu.
    Zwraca (bool, str) - (czy może użyć, komunikat błędu)
    """
    item = get_item(nazwa)
    
    if not item:
        return (False, "Nieznany przedmiot")
    
    # Sprawdź wymagania siły
    if 'req_sila' in item:
        if postac.get('statystyki', {}).get('sila', 0) < item['req_sila']:
            return (False, f"Wymaga {item['req_sila']} Siły")
    
    # Sprawdź wymagania zręczności
    if 'req_zrecznosc' in item:
        if postac.get('statystyki', {}).get('zrecznosc', 0) < item['req_zrecznosc']:
            return (False, f"Wymaga {item['req_zrecznosc']} Zręczności")
    
    return (True, "OK")


def use_item(nazwa: str, postac: dict) -> dict:
    """
    Używa przedmiotu consumable i zwraca zmiany w postaci.
    Zwraca dict z zmianami: {"hp": +20, "usun_przedmiot": True, "komunikat": "..."}
    """
    item = get_item(nazwa)
    
    if not item:
        return {"error": "Nieznany przedmiot"}
    
    if not item.get('consumable', False):
        return {"error": "Tego przedmiotu nie można użyć"}
    
    zmiany = {"usun_przedmiot": True, "komunikat": ""}
    
    # HP Heal
    if 'hp_heal' in item:
        heal = item['hp_heal']
        zmiany['hp'] = heal
        zmiany['komunikat'] = f"Użyto {nazwa}. Przywrócono {heal} HP."
    
    # Bonusy tymczasowe (TODO: implementacja buffs)
    if 'bonus_sila' in item:
        zmiany['komunikat'] = f"Użyto {nazwa}. Czujesz przypływ siły!"
    
    if 'bonus_zrecznosc' in item:
        zmiany['komunikat'] = f"Użyto {nazwa}. Czujesz się szybszy!"
    
    if 'bonus_def' in item:
        zmiany['komunikat'] = f"Użyto {nazwa}. Magiczna ochrona otacza cię!"
    
    # Zwoje ataku
    if 'dmg_mag' in item:
        zmiany['komunikat'] = f"Użyto {nazwa}. Zwój rozbłyska magią!"
        zmiany['atak_magiczny'] = item['dmg_mag']
    
    # Teleportacja
    if 'teleport' in item:
        zmiany['lokacja'] = item['teleport']
        zmiany['komunikat'] = f"Użyto {nazwa}. Teleportujesz się do {item['teleport'].capitalize()}!"
    
    # Antidotum
    if item.get('usuwa_trucizna'):
        zmiany['komunikat'] = f"Użyto {nazwa}. Trucizna zostaje zneutralizowana!"
    
    return zmiany


def get_items_by_type(typ: str) -> list:
    """Zwraca listę przedmiotów danego typu"""
    return [nazwa for nazwa, data in PRZEDMIOTY.items() if data.get('typ') == typ]


def get_all_item_names() -> list:
    """Zwraca listę wszystkich nazw przedmiotów"""
    return list(PRZEDMIOTY.keys())
