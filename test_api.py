import requests
import json

session = requests.Session()
session.get('http://localhost:5000/')

data = {
    'imie': 'TestBot',
    'plec': 'mezczyzna',
    'lud': 'polanie',
    'klasa': 'wojownik',
    'statystyki': {
        'sila': 8, 'zrecznosc': 6, 'inteligencja': 4,
        'charyzma': 5, 'wytrzymalosc': 7, 'percepcja': 5
    }
}

print('Tworzę postać...')
r = session.post('http://localhost:5000/stworz_postac', json=data)
postac_data = r.json()
print(f"Postać: {postac_data['postac']['imie']}")

print('\nWywołuję rozpocznij_przygode...')
r2 = session.post('http://localhost:5000/rozpocznij_przygode')

print('\nWywołuję akcję z dialogiem NPC...')
r3 = session.post('http://localhost:5000/akcja', json={'akcja': 'Podchodzę do Bogdana i pytam o pracę'})
result = r3.json()
print(f"Audio: {result.get('audio')}")
print('\n=== SPRAWDŹ TERMINAL SERWERA - POWINNY BYĆ LOGI GŁOSÓW ===')
