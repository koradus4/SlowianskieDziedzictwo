import os
import tempfile
import json
from pathlib import Path
from database import Database


def test_zapisz_i_wczytaj_przeciwnicy_hp(tmp_path):
    db_file = tmp_path / "test_game.db"
    db = Database(db_file)
    db.inicjalizuj()

    postac = {
        'imie': 'Testowy',
        'plec': 'mezczyzna',
        'lud': 'polanie',
        'klasa': 'Wojownik',
        'hp': 100,
        'hp_max': 100,
        'przeciwnicy_hp': {
            'bestia_wilk_1': {'hp': 30, 'hp_max': 40, 'imie': 'Szary Wilk', 'typ': 'bestia'}
        }
    }

    postac_id = db.zapisz_postac(postac)
    assert postac_id is not None

    loaded = db.wczytaj_postac(postac_id)
    assert loaded is not None
    assert 'przeciwnicy_hp' in loaded
    assert isinstance(loaded['przeciwnicy_hp'], dict)
    assert 'bestia_wilk_1' in loaded['przeciwnicy_hp']
    assert loaded['przeciwnicy_hp']['bestia_wilk_1']['hp'] == 30


def test_aktualizuj_postac_zmiana_przeciwnicy_hp(tmp_path):
    db_file = tmp_path / "test_game2.db"
    db = Database(db_file)
    db.inicjalizuj()

    postac = {
        'imie': 'Testowy2',
        'plec': 'kobieta',
        'lud': 'polanie',
        'klasa': 'Kapłan',
        'hp': 80,
        'hp_max': 100,
        'przeciwnicy_hp': {}
    }

    postac_id = db.zapisz_postac(postac)
    assert postac_id > 0

    # Aktualizacja przeciwników
    nowe_przeciwnicy = {
        'bestia_bazyl_1': {'hp': 50, 'hp_max': 50, 'imie': 'Bazyl', 'typ': 'bestia'}
    }

    db.aktualizuj_postac(postac_id, {'przeciwnicy_hp': nowe_przeciwnicy})
    updated = db.wczytaj_postac(postac_id)
    assert 'bestia_bazyl_1' in updated['przeciwnicy_hp']
    assert updated['przeciwnicy_hp']['bestia_bazyl_1']['hp'] == 50
