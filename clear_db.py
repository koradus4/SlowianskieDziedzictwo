import sqlite3

conn = sqlite3.connect('game.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM postacie')
total = cursor.fetchone()[0]
print(f'Zapisow w bazie: {total}')

cursor.execute('DELETE FROM ai_context')
cursor.execute('DELETE FROM historia')
cursor.execute('DELETE FROM wydarzenia')
cursor.execute('DELETE FROM questy')
cursor.execute('DELETE FROM artefakty')
cursor.execute('DELETE FROM postacie')
cursor.execute('DELETE FROM sqlite_sequence WHERE name="postacie"')

conn.commit()
print(f'Usunieto {total} zapisow!')

cursor.execute('SELECT COUNT(*) FROM postacie')
remaining = cursor.fetchone()[0]
print(f'Pozostalo: {remaining}')

conn.close()
print('Baza wyczyszczona!')
