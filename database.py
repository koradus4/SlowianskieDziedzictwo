"""
Moduł bazy danych - wspiera SQLite (lokalnie) i PostgreSQL (Cloud SQL)
"""

import sqlite3
import os
from pathlib import Path
import json
from datetime import datetime

# Spróbuj zaimportować psycopg2 dla PostgreSQL (opcjonalnie)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


class Database:
    """Obsługa bazy danych gry (SQLite lokalnie, PostgreSQL w Cloud)"""
    
    def __init__(self, db_path: Path = None):
        # Sprawdź czy jest DATABASE_URL (Cloud SQL)
        self.database_url = os.environ.get('DATABASE_URL')
        self.use_postgres = self.database_url and HAS_POSTGRES
        
        if self.use_postgres:
            print(f"🐘 Używam PostgreSQL (Cloud SQL)")
        else:
            self.db_path = Path(db_path) if db_path else Path("game.db")
            print(f"📁 Używam SQLite: {self.db_path}")
    
    def _polacz(self):
        """Zwraca połączenie do bazy (SQLite lub PostgreSQL)"""
        if self.use_postgres:
            return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
        else:
            return sqlite3.connect(self.db_path)
    
    def _placeholder(self):
        """Zwraca odpowiedni placeholder dla bazy (%s dla Postgres, ? dla SQLite)"""
        return '%s' if self.use_postgres else '?'
    
    def inicjalizuj(self):
        """Tworzy tabele w bazie danych"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            # Użyj odpowiedniej składni dla PostgreSQL lub SQLite
            if self.use_postgres:
                # PostgreSQL używa SERIAL zamiast AUTOINCREMENT
                id_type = "SERIAL PRIMARY KEY"
                text_type = "TEXT"
                timestamp_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            else:
                # SQLite
                id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
                text_type = "TEXT"
                timestamp_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            
            # Tabela postaci
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS postacie (
                    id {id_type},
                    imie {text_type} NOT NULL,
                    plec {text_type} DEFAULT 'mezczyzna',
                    lud {text_type},
                    klasa {text_type},
                    hp INTEGER DEFAULT 100,
                    hp_max INTEGER DEFAULT 100,
                    poziom INTEGER DEFAULT 1,
                    doswiadczenie INTEGER DEFAULT 0,
                    zloto INTEGER DEFAULT 10,
                    statystyki {text_type},
                    ekwipunek {text_type},
                    towarzysze {text_type},
                    lokacja {text_type} DEFAULT 'gniezno',
                    created_at {timestamp_default}
                )
            """)
            
            conn.commit()
            
            # Migracja - dodaj kolumnę towarzysze jeśli nie istnieje
            try:
                cursor.execute("ALTER TABLE postacie ADD COLUMN towarzysze TEXT")
                conn.commit()
            except:
                conn.rollback()  # Rollback jeśli kolumna już istnieje
            
            # Tabela historii gry
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS historia (
                    id {id_type},
                    postac_id INTEGER,
                    akcja_gracza {text_type},
                    odpowiedz_mg {text_type},
                    created_at {timestamp_default},
                    FOREIGN KEY (postac_id) REFERENCES postacie(id)
                )
            """)
            
            # Tabela questów
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS questy (
                    id {id_type},
                    postac_id INTEGER,
                    nazwa {text_type},
                    opis {text_type},
                    status {text_type} DEFAULT 'aktywny',
                    created_at {timestamp_default},
                    FOREIGN KEY (postac_id) REFERENCES postacie(id)
                )
            """)
            
            # Tabela zebranych artefaktów
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS artefakty (
                    id {id_type},
                    postac_id INTEGER,
                    nazwa {text_type},
                    opis {text_type},
                    zebrano_at {timestamp_default},
                    FOREIGN KEY (postac_id) REFERENCES postacie(id)
                )
            """)
            
            conn.commit()
            conn.close()
            print("✅ Baza danych zainicjalizowana!")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Błąd inicjalizacji bazy: {e}")
            raise
    
    def zapisz_postac(self, postac: dict) -> int:
        """Zapisuje postać do bazy"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        
        base_query = f"""
            INSERT INTO postacie 
            (imie, plec, lud, klasa, hp, hp_max, poziom, doswiadczenie, zloto, statystyki, ekwipunek, towarzysze, lokacja)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        """
        
        params = (
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
        )

        if self.use_postgres:
            cursor.execute(base_query + " RETURNING id", params)
            postac_id = cursor.fetchone()['id'] if isinstance(cursor, psycopg2.extras.RealDictCursor) else cursor.fetchone()[0]
        else:
            cursor.execute(base_query, params)
            postac_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return postac_id
    
    def wczytaj_postac(self, postac_id: int) -> dict:
        """Wczytuje postać z bazy"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        cursor.execute(f"SELECT * FROM postacie WHERE id = {ph}", (postac_id,))
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
        
        ph = self._placeholder()
        for klucz, wartosc in dane.items():
            if klucz in ['hp', 'zloto', 'poziom', 'doswiadczenie', 'lokacja']:
                ustawienia.append(f"{klucz} = {ph}")
                wartosci.append(wartosc)
            elif klucz in ['statystyki', 'ekwipunek', 'towarzysze']:
                ustawienia.append(f"{klucz} = {ph}")
                wartosci.append(json.dumps(wartosc))
        
        if ustawienia:
            wartosci.append(postac_id)
            cursor.execute(
                f"UPDATE postacie SET {', '.join(ustawienia)} WHERE id = {ph}",
                wartosci
            )
            conn.commit()
        
        conn.close()
    
    def zapisz_historie(self, postac_id: int, akcja: str, odpowiedz: str):
        """Zapisuje wpis historii"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        cursor.execute(f"""
            INSERT INTO historia (postac_id, akcja_gracza, odpowiedz_mg)
            VALUES ({ph}, {ph}, {ph})
        """, (postac_id, akcja, odpowiedz))
        
        conn.commit()
        conn.close()
    
    def wczytaj_historie(self, postac_id: int, limit: int = 20) -> list:
        """Wczytuje historię gry"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        cursor.execute(f"""
            SELECT akcja_gracza, odpowiedz_mg, created_at 
            FROM historia 
            WHERE postac_id = {ph} 
            ORDER BY created_at DESC 
            LIMIT {ph}
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
        
        ph = self._placeholder()
        cursor.execute(f"""
            INSERT INTO artefakty (postac_id, nazwa, opis)
            VALUES ({ph}, {ph}, {ph})
        """, (postac_id, nazwa, opis))
        
        conn.commit()
        conn.close()
    
    def pobierz_artefakty(self, postac_id: int) -> list:
        """Pobiera zebrane artefakty"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        cursor.execute(f"""
            SELECT nazwa, opis FROM artefakty WHERE postac_id = {ph}
        """, (postac_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'nazwa': row[0], 'opis': row[1]} for row in rows]
    
    def lista_postaci(self, limit: int = 10) -> list:
        """Lista zapisanych postaci do wczytania"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        cursor.execute(f"""
            SELECT id, imie, lud, klasa, hp, poziom, lokacja, created_at
            FROM postacie 
            ORDER BY created_at DESC 
            LIMIT {ph}
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
            ph = self._placeholder()
            # Usuń historię
            cursor.execute(f"DELETE FROM historia WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń postać
            cursor.execute(f"DELETE FROM postacie WHERE id = {ph}", (postac_id,))
            
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
            ph = self._placeholder()
            # Znajdź ID najstarszych zapisów do usunięcia
            cursor.execute(f"""
                SELECT id FROM postacie
                ORDER BY created_at DESC
                LIMIT -1 OFFSET {ph}
            """, (limit,))
            
            stare_ids = [row[0] for row in cursor.fetchall()]
            
            if stare_ids:
                placeholders = ','.join([ph] * len(stare_ids))
                
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
