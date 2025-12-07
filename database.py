"""
Moduł bazy danych SQLite
"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime


class Database:
    """Obsługa bazy danych gry"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
    
    def _polacz(self):
        return sqlite3.connect(self.db_path)
    
    def inicjalizuj(self):
        """Tworzy tabele w bazie danych"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        # Tabela postaci
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postacie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imie TEXT NOT NULL,
                plec TEXT DEFAULT 'mezczyzna',
                lud TEXT,
                klasa TEXT,
                hp INTEGER DEFAULT 100,
                hp_max INTEGER DEFAULT 100,
                poziom INTEGER DEFAULT 1,
                doswiadczenie INTEGER DEFAULT 0,
                zloto INTEGER DEFAULT 10,
                statystyki TEXT,
                ekwipunek TEXT,
                towarzysze TEXT,
                lokacja TEXT DEFAULT 'gniezno',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migracja - dodaj kolumnę towarzysze jeśli nie istnieje
        try:
            cursor.execute("ALTER TABLE postacie ADD COLUMN towarzysze TEXT")
            conn.commit()
        except:
            pass  # Kolumna już istnieje
        
        # Tabela historii gry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                postac_id INTEGER,
                akcja_gracza TEXT,
                odpowiedz_mg TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (postac_id) REFERENCES postacie(id)
            )
        """)
        
        # Tabela questów
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                postac_id INTEGER,
                nazwa TEXT,
                opis TEXT,
                status TEXT DEFAULT 'aktywny',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (postac_id) REFERENCES postacie(id)
            )
        """)
        
        # Tabela zebranych artefaktów
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artefakty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                postac_id INTEGER,
                nazwa TEXT,
                opis TEXT,
                zebrano_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (postac_id) REFERENCES postacie(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("Baza danych zainicjalizowana!")
    
    def zapisz_postac(self, postac: dict) -> int:
        """Zapisuje postać do bazy"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO postacie 
            (imie, plec, lud, klasa, hp, hp_max, poziom, doswiadczenie, zloto, statystyki, ekwipunek, towarzysze, lokacja)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            postac.get('imie'),
            postac.get('plec', 'mezczyzna'),
            postac.get('lud'),
            postac.get('klasa'),
            postac.get('hp', 100),
            postac.get('hp_max', 100),
            postac.get('poziom', 1),
            postac.get('doswiadczenie', 0),
            postac.get('zloto', 10),
            json.dumps(postac.get('statystyki', {})),
            json.dumps(postac.get('ekwipunek', [])),
            json.dumps(postac.get('towarzysze', [])),
            postac.get('lokacja', 'gniezno')
        ))
        
        postac_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return postac_id
    
    def wczytaj_postac(self, postac_id: int) -> dict:
        """Wczytuje postać z bazy"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM postacie WHERE id = ?", (postac_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'imie': row[1],
            'plec': row[2],
            'lud': row[3],
            'klasa': row[4],
            'hp': row[5],
            'hp_max': row[6],
            'poziom': row[7],
            'doswiadczenie': row[8],
            'zloto': row[9],
            'statystyki': json.loads(row[10]) if row[10] else {},
            'ekwipunek': json.loads(row[11]) if row[11] else [],
            'towarzysze': json.loads(row[12]) if row[12] else [],
            'lokacja': row[13]
        }
    
    def aktualizuj_postac(self, postac_id: int, dane: dict):
        """Aktualizuje dane postaci"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ustawienia = []
        wartosci = []
        
        for klucz, wartosc in dane.items():
            if klucz in ['hp', 'zloto', 'poziom', 'doswiadczenie', 'lokacja']:
                ustawienia.append(f"{klucz} = ?")
                wartosci.append(wartosc)
            elif klucz in ['statystyki', 'ekwipunek', 'towarzysze']:
                ustawienia.append(f"{klucz} = ?")
                wartosci.append(json.dumps(wartosc))
        
        if ustawienia:
            wartosci.append(postac_id)
            cursor.execute(
                f"UPDATE postacie SET {', '.join(ustawienia)} WHERE id = ?",
                wartosci
            )
            conn.commit()
        
        conn.close()
    
    def zapisz_historie(self, postac_id: int, akcja: str, odpowiedz: str):
        """Zapisuje wpis historii"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO historia (postac_id, akcja_gracza, odpowiedz_mg)
            VALUES (?, ?, ?)
        """, (postac_id, akcja, odpowiedz))
        
        conn.commit()
        conn.close()
    
    def wczytaj_historie(self, postac_id: int, limit: int = 20) -> list:
        """Wczytuje historię gry"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT akcja_gracza, odpowiedz_mg, created_at 
            FROM historia 
            WHERE postac_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (postac_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'akcja': row[0], 'odpowiedz': row[1], 'czas': row[2]} 
            for row in reversed(rows)
        ]
    
    def dodaj_artefakt(self, postac_id: int, nazwa: str, opis: str = ""):
        """Dodaje zebrany artefakt"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO artefakty (postac_id, nazwa, opis)
            VALUES (?, ?, ?)
        """, (postac_id, nazwa, opis))
        
        conn.commit()
        conn.close()
    
    def pobierz_artefakty(self, postac_id: int) -> list:
        """Pobiera zebrane artefakty"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nazwa, opis FROM artefakty WHERE postac_id = ?
        """, (postac_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'nazwa': row[0], 'opis': row[1]} for row in rows]
    
    def lista_postaci(self, limit: int = 10) -> list:
        """Lista zapisanych postaci do wczytania"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, imie, lud, klasa, hp, poziom, lokacja, created_at
            FROM postacie 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'imie': row[1],
            'lud': row[2],
            'klasa': row[3],
            'hp': row[4],
            'poziom': row[5],
            'lokacja': row[6],
            'data': row[7]
        } for row in rows]
    
    def usun_postac(self, postac_id: int) -> bool:
        """Usuwa postać i jej historię"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            # Usuń historię
            cursor.execute("DELETE FROM historia WHERE postac_id = ?", (postac_id,))
            
            # Usuń postać
            cursor.execute("DELETE FROM postacie WHERE id = ?", (postac_id,))
            
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def usun_najstarsze_zapisy(self, limit: int = 10) -> int:
        """Usuwa najstarsze zapisy jeśli przekroczono limit"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            # Znajdź ID najstarszych zapisów do usunięcia
            cursor.execute("""
                SELECT id FROM postacie
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            """, (limit,))
            
            stare_ids = [row[0] for row in cursor.fetchall()]
            
            if stare_ids:
                placeholders = ','.join('?' * len(stare_ids))
                
                # Usuń historię
                cursor.execute(f"DELETE FROM historia WHERE postac_id IN ({placeholders})", stare_ids)
                
                # Usuń postacie
                cursor.execute(f"DELETE FROM postacie WHERE id IN ({placeholders})", stare_ids)
                
                conn.commit()
                return len(stare_ids)
            
            return 0
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()


# Test
if __name__ == "__main__":
    db = Database(Path("test_game.db"))
    db.inicjalizuj()
    
    postac = {
        "imie": "Test",
        "lud": "polanie",
        "klasa": "wojownik_rycerz",
        "hp": 100,
        "statystyki": {"sila": 12, "zrecznosc": 10}
    }
    
    id = db.zapisz_postac(postac)
    print(f"Zapisano postać ID: {id}")
    
    wczytana = db.wczytaj_postac(id)
    print(f"Wczytano: {wczytana}")
