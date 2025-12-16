from database import Database
from pathlib import Path

db = Database(Path('game.db'))

print("Czyszczenie starych zapisow...")
usunietych = db.usun_stare_autosavy(limit=5)
print(f"Usunieto: {usunietych} starych zapisow")

print("\nSprawdzanie po czyszczeniu...")
zapisy = db.lista_postaci(limit=10, tylko_autosave=True)
print(f"Pozostalo zapisow: {len(zapisy)}")
for z in zapisy:
    print(f"ID: {z['id']:3d} | {z['imie']:15s} | {z['data']}")
