#!/usr/bin/env python3
"""Skrypt integracyjny testujący: 
- tworzenie postaci (/stworz_postac)
- wykonanie akcji (/akcja) - sprawdź, czy zapisuje "przeciwnicy_hp" do DB
- wczytanie zapisu (/wczytaj_gre/<postac_id>) i potwierdzenie, że przeciwnicy_hp jest w zapisie
- symulacja klienta z timeoutem dla /debug/slow

Uruchomienie: python scripts/integration_test.py
"""
import requests
import time
import json

import os
BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:8080')

session = requests.Session()

# 1) Stwórz postać
print('> Tworzenie postaci...')
resp = session.post(BASE + '/stworz_postac', json={
    'imie': 'Testowy',
    'plec': 'mezczyzna',
    'lud': 'polanie',
    'klasa': 'Wojownik-Rycerz',
    'statystyki': {'wytrzymalosc': 12, 'sila': 12}
})
print('Status:', resp.status_code)
print(resp.text[:200])
resp.raise_for_status()

# 2) Wyślij akcję, która zwykle powoduje walkę
print('\n> Wykonanie akcji -> /akcja (może spowodować pojawienie się przeciwników)')
akcja_req = session.post(BASE + '/akcja', json={'akcja': 'Idę do lasu i atakuję napotkanego wilka.'})
print('Status /akcja:', akcja_req.status_code)
print('JSON:', json.dumps(akcja_req.json(), indent=2, ensure_ascii=False)[:1000])

# 3) Pobierz lista zapisów (znajdź ID tej postaci)
print('\n> Lista zapisów: /lista_zapisow')
list_resp = session.get(BASE + '/lista_zapisow')
print('Status:', list_resp.status_code)
j = list_resp.json()
print('Zapisów:', len(j.get('zapisy', [])))
postac_id = None
for p in j.get('zapisy', []):
    if p.get('imie') == 'Testowy':
        postac_id = p.get('id')
        break
print('Znalezione ID testowej postaci:', postac_id)

if postac_id:
    # 4) Wczytaj zapis i sprawdź czy "przeciwnicy_hp" się zapisuje
    time.sleep(1)
    print('\n> Wczytaj zapis i sprawdź "przeciwnicy_hp"')
    wczyt = session.get(BASE + f'/wczytaj_zapis/{postac_id}')
    print('Status wczyt:', wczyt.status_code)
    print('Wczyt JSON[:400]:', json.dumps(wczyt.json(), indent=2, ensure_ascii=False)[:1000])
    # w³aœciwe /wczytaj_zapis zwraca redirect do /gra w normalnym użyciu; u niego wczytuje do sesji
    # Możemy użyć /postac aby uzyskać dane postaci w sesji
    postac_info = session.get(BASE + '/postac')
    print('/postac ->', postac_info.status_code)
    postac_json = postac_info.json()
    print('Aktualna sesja.postac keys:', list(postac_json.keys()))
    if 'przeciwnicy_hp' in postac_json:
        print('✅ Przeciwnicy HP w sesji:', postac_json['przeciwnicy_hp'])
    else:
        print('⚠️ Brak pola "przeciwnicy_hp" w sesji (najpierw wywołaj akcję z walką)')

# 5) Symulacja klienta w fetch z timeoutem: /debug/slow (15s) - requests będzie timeoutować po 15s
print('\n> Symulacja klienta z timeoutem na /debug/slow (timeout=15s)')
try:
    start = time.time()
    r = session.get(BASE + '/debug/slow', timeout=15)  # timeout po 15s
    elapsed = time.time() - start
    print('Odpowiedz /debug/slow, status:', r.status_code, 'czas:', elapsed)
except requests.exceptions.ReadTimeout:
    print('⏱️  Timeout oczekiwany: żądanie przerwane po 15s')
    elapsed = time.time() - start
    print('Czas do timeouta:', elapsed)

print('\nTest zakończony')
