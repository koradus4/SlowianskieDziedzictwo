import sqlite3
from database import Database
from pathlib import Path

print("SPRAWDZANIE BAZY DANYCH\n")

# 1. Sprawdz tabele
conn = sqlite3.connect('game.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tabele w bazie:")
for t in tables:
    print(f"   - {t}")
print()

# 2. Sprawdz zapisy
db = Database(Path('game.db'))
zapisy_all = db.lista_postaci(limit=20, tylko_autosave=False)
zapisy_auto = db.lista_postaci(limit=20, tylko_autosave=True)

print(f"Wszystkich zapisow: {len(zapisy_all)}")
print(f"Tylko autosave: {len(zapisy_auto)}")
print()

print("Ostatnie 10 zapisow:")
print('-' * 80)
for z in zapisy_all[:10]:
    typ = z.get('typ_zapisu', 'BRAK')
    print(f'ID: {z["id"]:3d} | {z["imie"]:15s} | Typ: {typ:10s} | {z["data"]}')
