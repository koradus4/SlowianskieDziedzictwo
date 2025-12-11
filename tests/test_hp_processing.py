import pytest
from app import app, przetworz_hp_przeciwnikow


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_przetworz_hp_przeciwnikow_new_enemy(client):
    # Stwórz nową sesję z postacią
    resp = client.post('/stworz_postac', json={'imie':'TestUser','plec':'mezczyzna','lud':'polanie','klasa':'Wojownik','statystyki':{}})
    assert resp.status_code == 200

    # Wywołaj funkcję przetworz_hp_przeciwnikow przez POST /akcja
    akcja_resp = client.post('/akcja', json={'akcja': 'Atakuję wilka.'})
    assert akcja_resp.status_code in (200, 503) or isinstance(akcja_resp.json, dict)

    # Teraz manualnie wywołamy przetworz_hp_przeciwnikow z przykładowymi uczestnikami
    with client.session_transaction() as sess:
        sess['przeciwnicy_hp'] = {}
    uczestnicy = [{'imie': 'Test Wilk', 'typ': 'bestia', 'hp_max': 40}]
    wynik = app.test_request_context()
    # Użyj testowego klienta aby wywołać endpoint /postac i pobrać sesję
    # Teraz wywołaj bezpośrednio funkcję z app context
    with app.test_request_context('/akcja'):
        from flask import session
        session['przeciwnicy_hp'] = {}
        res = przetworz_hp_przeciwnikow(uczestnicy, 'Narracja: zadajesz 5 obrażeń Test Wilk')
        assert any(u['imie'] == 'Test Wilk' for u in res)
        # sprawdź czy sesja zaktualizowana
        assert 'przeciwnicy_hp' in session
        keys = list(session['przeciwnicy_hp'].keys())
        assert len(keys) == 1

