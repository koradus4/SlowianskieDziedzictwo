import sqlite3

print("Usuwanie wszystkich zapisow...")

conn = sqlite3.connect('game.db')
cursor = conn.cursor()

try:
    # Policz ile jest zapisow
    cursor.execute("SELECT COUNT(*) FROM postacie")
    total = cursor.fetchone()[0]
    print(f"Znaleziono zapisow: {total}")
    
    if total > 0:
        # Usun wszystko
        cursor.execute("DELETE FROM ai_context")
        cursor.execute("DELETE FROM historia")
        cursor.execute("DELETE FROM wydarzenia")
        cursor.execute("DELETE FROM questy")
        cursor.execute("DELETE FROM artefakty")
        cursor.execute("DELETE FROM postacie")
        
        # Zresetuj autoincremen ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='postacie'")
        
        conn.commit()
        print(f"Usunieto wszystkie {total} zapisow!")
    else:
        print("Baza juz jest pusta")
    
    # Sprawdz
    cursor.execute("SELECT COUNT(*) FROM postacie")
    remaining = cursor.fetchone()[0]
    print(f"Pozostalo zapisow: {remaining}")
    
except Exception as e:
    print(f"Blad: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nBaza wyczyszczona - mozesz zaczac od nowa!")
