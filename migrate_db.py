import sqlite3

# Dodaj brakującą kolumnę typ_zapisu do istniejącej bazy
conn = sqlite3.connect('game.db')
cursor = conn.cursor()

try:
    # Sprawdź czy kolumna istnieje
    cursor.execute("PRAGMA table_info(postacie)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'typ_zapisu' not in columns:
        print("⚠️ Kolumna typ_zapisu nie istnieje - dodaję...")
        cursor.execute("ALTER TABLE postacie ADD COLUMN typ_zapisu TEXT DEFAULT 'autosave'")
        conn.commit()
        print("✅ Dodano kolumnę typ_zapisu")
        
        # Ustaw wszystkie istniejące zapisy jako autosave
        cursor.execute("UPDATE postacie SET typ_zapisu = 'autosave' WHERE typ_zapisu IS NULL")
        conn.commit()
        print(f"✅ Zaktualizowano {cursor.rowcount} istniejących zapisów")
    else:
        print("✅ Kolumna typ_zapisu już istnieje")
    
    # Sprawdź czy tabela ai_context istnieje
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_context'")
    if cursor.fetchone():
        print("✅ Tabela ai_context istnieje")
    else:
        print("⚠️ Tabela ai_context NIE ISTNIEJE - trzeba zainicjalizować bazę!")
        
except Exception as e:
    print(f"❌ Błąd: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n🔍 Sprawdzam zapisy...")
conn = sqlite3.connect('game.db')
cursor = conn.cursor()
cursor.execute("SELECT id, imie, typ_zapisu, created_at FROM postacie ORDER BY created_at DESC LIMIT 10")
for row in cursor.fetchall():
    print(f"ID: {row[0]:3d} | {row[1]:15s} | Typ: {row[2] or 'NULL':10s} | {row[3]}")
conn.close()
