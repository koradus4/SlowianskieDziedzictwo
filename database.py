"""
Moduł bazy danych - wspiera SQLite (lokalnie) i PostgreSQL (Cloud SQL)
"""

import sqlite3
import os
from pathlib import Path
import json
from datetime import datetime
import gzip
import base64

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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
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
                    przeciwnicy_hp {text_type},
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
            
            # Migracja - dodaj kolumnę przeciwnicy_hp jeśli nie istnieje
            try:
                cursor.execute("ALTER TABLE postacie ADD COLUMN przeciwnicy_hp TEXT")
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
            
            # Tabela wydarzeń (dziennik przygód)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS wydarzenia (
                    id {id_type},
                    postac_id INTEGER,
                    typ {text_type} NOT NULL,
                    tytul {text_type} NOT NULL,
                    opis {text_type},
                    lokalizacja {text_type},
                    nagroda {text_type},
                    created_at {timestamp_default},
                    FOREIGN KEY (postac_id) REFERENCES postacie(id)
                )
            """)
            
            # Tabela kontekstu AI (kompresowana historia Gemini)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS ai_context (
                    id {id_type},
                    postac_id INTEGER,
                    historia_compressed {text_type} NOT NULL,
                    ostatnie_opcje {text_type},
                    created_at {timestamp_default},
                    FOREIGN KEY (postac_id) REFERENCES postacie(id)
                )
            """)
            
            # Migracja - dodaj kolumnę typ_zapisu jeśli nie istnieje
            try:
                cursor.execute("ALTER TABLE postacie ADD COLUMN typ_zapisu TEXT DEFAULT 'autosave'")
                conn.commit()
            except:
                conn.rollback()  # Rollback jeśli kolumna już istnieje
            
            conn.commit()
            conn.close()
            print("✅ Baza danych zainicjalizowana!")
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"❌ Błąd inicjalizacji bazy: {e}")
            raise
    
    def zapisz_postac(self, postac: dict, typ_zapisu: str = 'autosave') -> int:
        """Zapisuje postać do bazy z oznaczeniem typu zapisu"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        
        base_query = f"""
            INSERT INTO postacie 
            (imie, plec, lud, klasa, hp, hp_max, poziom, doswiadczenie, zloto, statystyki, ekwipunek, towarzysze, przeciwnicy_hp, lokacja, typ_zapisu)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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
            json.dumps(postac.get('przeciwnicy_hp', {})),
            postac.get('lokacja', 'gniezno'),
            typ_zapisu
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
        
        # PostgreSQL może zwrócić dict (RealDictCursor), sqlite3.Row działa jak mapping, ale nie ma .get()
        if isinstance(row, dict):
            przeciwnicy_hp_raw = row.get('przeciwnicy_hp')
        else:
            przeciwnicy_hp_raw = row['przeciwnicy_hp'] if 'przeciwnicy_hp' in row.keys() else None

        return {
            'id': row['id'],
            'imie': row['imie'],
            'plec': row['plec'],
            'lud': row['lud'],
            'klasa': row['klasa'],
            'hp': row['hp'],
            'hp_max': row['hp_max'],
            'poziom': row['poziom'],
            'doswiadczenie': row['doswiadczenie'],
            'zloto': row['zloto'],
            'statystyki': json.loads(row['statystyki']) if row['statystyki'] else {},
            'ekwipunek': json.loads(row['ekwipunek']) if row['ekwipunek'] else [],
            'towarzysze': json.loads(row['towarzysze']) if row['towarzysze'] else [],
            'przeciwnicy_hp': json.loads(przeciwnicy_hp_raw) if przeciwnicy_hp_raw else {},
            'lokacja': row['lokacja']
        }
    
    def aktualizuj_postac(self, postac_id: int, dane: dict):
        """Aktualizuje dane postaci"""
        print(f"🔧 aktualizuj_postac: postac_id={postac_id}, dane={dane}")
        conn = self._polacz()
        cursor = conn.cursor()
        
        ustawienia = []
        wartosci = []
        
        ph = self._placeholder()
        for klucz, wartosc in dane.items():
            if klucz in ['hp', 'zloto', 'poziom', 'doswiadczenie', 'lokacja']:
                ustawienia.append(f"{klucz} = {ph}")
                wartosci.append(wartosc)
            elif klucz in ['statystyki', 'ekwipunek', 'towarzysze', 'przeciwnicy_hp']:
                ustawienia.append(f"{klucz} = {ph}")
                wartosci.append(json.dumps(wartosc))
        
        print(f"🔧 ustawienia={ustawienia}, wartosci={wartosci}")
        
        if ustawienia:
            wartosci.append(postac_id)
            zapytanie = f"UPDATE postacie SET {', '.join(ustawienia)} WHERE id = {ph}"
            print(f"🔧 SQL: {zapytanie}")
            cursor.execute(zapytanie, wartosci)
            rowcount = cursor.rowcount
            print(f"🔧 Zaktualizowano {rowcount} wierszy")
            conn.commit()
            return rowcount
        else:
            print(f"❌ BRAK USTAWIEŃ - nic nie zapisano!")
        
        conn.close()
        return 0
    
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
            {'akcja': row['akcja_gracza'], 'odpowiedz': row['odpowiedz_mg'], 'czas': row['created_at']} 
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
        
        return [{'nazwa': row['nazwa'], 'opis': row['opis']} for row in rows]
    
    def lista_postaci(self, limit: int = 10, tylko_autosave: bool = False) -> list:
        """Lista zapisanych postaci do wczytania (z timestampem)"""
        print(f"🔍 lista_postaci: limit={limit}, tylko_autosave={tylko_autosave}")
        conn = self._polacz()
        cursor = conn.cursor()
        
        ph = self._placeholder()
        
        if tylko_autosave:
            where_clause = "WHERE typ_zapisu = 'autosave'"
        else:
            where_clause = ""
        
        zapytanie = f"""
            SELECT id, imie, lud, klasa, hp, poziom, lokacja, typ_zapisu, created_at
            FROM postacie 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT {ph}
        """
        print(f"🔍 SQL: {zapytanie}")
        cursor.execute(zapytanie, (limit,))
        
        rows = cursor.fetchall()
        print(f"🔍 Znaleziono {len(rows)} postaci")
        conn.close()
        
        wynik = [{
            'id': row['id'],
            'imie': row['imie'],
            'lud': row['lud'],
            'klasa': row['klasa'],
            'hp': row['hp'],
            'poziom': row['poziom'],
            'lokacja': row['lokacja'],
            'typ_zapisu': row['typ_zapisu'] if 'typ_zapisu' in row.keys() else 'autosave',
            'data': row['created_at']
        } for row in rows]
        print(f"🔍 Zwracam: {wynik}")
        return wynik
    
    def usun_postac(self, postac_id: int) -> bool:
        """Usuwa postać i wszystkie powiązane dane"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            # Usuń kontekst AI
            cursor.execute(f"DELETE FROM ai_context WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń historię
            cursor.execute(f"DELETE FROM historia WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń wydarzenia
            cursor.execute(f"DELETE FROM wydarzenia WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń questy
            cursor.execute(f"DELETE FROM questy WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń artefakty
            cursor.execute(f"DELETE FROM artefakty WHERE postac_id = {ph}", (postac_id,))
            
            # Usuń postać
            cursor.execute(f"DELETE FROM postacie WHERE id = {ph}", (postac_id,))
            
            conn.commit()
            print(f"✅ Usunięto postać {postac_id} i wszystkie powiązane dane")
            return True
        except Exception as e:
            print(f"❌ Błąd usuwania postaci {postac_id}: {e}")
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
            
            stare_ids = [row['id'] for row in cursor.fetchall()]
            
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
    
    def dodaj_wydarzenie(self, postac_id: int, typ: str, tytul: str, opis: str, lokalizacja: str, nagroda: dict = None):
        """Dodaje wydarzenie do dziennika gracza"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            cursor.execute(f"""
                INSERT INTO wydarzenia (postac_id, typ, tytul, opis, lokalizacja, nagroda)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (postac_id, typ, tytul, opis, lokalizacja, json.dumps(nagroda or {})))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Błąd zapisywania wydarzenia: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def pobierz_wydarzenia(self, postac_id: int, limit: int = 50, typ: str = None):
        """Pobiera wydarzenia gracza (opcjonalnie filtrowane po typie)"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            
            if typ:
                query = f"""
                    SELECT * FROM wydarzenia 
                    WHERE postac_id = {ph} AND typ = {ph}
                    ORDER BY created_at DESC
                    LIMIT {ph}
                """
                cursor.execute(query, (postac_id, typ, limit))
            else:
                query = f"""
                    SELECT * FROM wydarzenia 
                    WHERE postac_id = {ph}
                    ORDER BY created_at DESC
                    LIMIT {ph}
                """
                cursor.execute(query, (postac_id, limit))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Błąd pobierania wydarzeń: {e}")
            return []
        finally:
            conn.close()
    
    # ===== FUNKCJE KOMPRESJI =====
    
    def _kompresuj_json(self, data: dict) -> str:
        """Kompresuje JSON do base64-encoded gzip"""
        json_str = json.dumps(data, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        compressed = gzip.compress(json_bytes, compresslevel=6)
        return base64.b64encode(compressed).decode('ascii')
    
    def _dekompresuj_json(self, compressed_str: str) -> dict:
        """Dekompresuje base64-encoded gzip do JSON"""
        try:
            compressed_bytes = base64.b64decode(compressed_str.encode('ascii'))
            json_bytes = gzip.decompress(compressed_bytes)
            json_str = json_bytes.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            print(f"❌ Błąd dekompresji kontekstu AI: {e}")
            return []
    
    # ===== KONTEKST AI (HISTORIA GEMINI) =====
    
    def zapisz_ai_context(self, postac_id: int, historia_ai: list, ostatnie_opcje: list = None):
        """Zapisuje skompresowany kontekst AI dla autosave"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            historia_compressed = self._kompresuj_json(historia_ai)
            opcje_json = json.dumps(ostatnie_opcje or [])
            
            cursor.execute(f"""
                INSERT INTO ai_context (postac_id, historia_compressed, ostatnie_opcje)
                VALUES ({ph}, {ph}, {ph})
            """, (postac_id, historia_compressed, opcje_json))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu kontekstu AI: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def wczytaj_ai_context(self, postac_id: int) -> dict:
        """Wczytuje najnowszy kontekst AI dla danej postaci"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            cursor.execute(f"""
                SELECT historia_compressed, ostatnie_opcje, created_at
                FROM ai_context
                WHERE postac_id = {ph}
                ORDER BY created_at DESC
                LIMIT 1
            """, (postac_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return {'historia': [], 'opcje': []}
            
            historia = self._dekompresuj_json(row['historia_compressed'])
            opcje = json.loads(row['ostatnie_opcje']) if row['ostatnie_opcje'] else []
            
            return {
                'historia': historia,
                'opcje': opcje,
                'timestamp': row['created_at']
            }
        except Exception as e:
            print(f"❌ Błąd odczytu kontekstu AI: {e}")
            return {'historia': [], 'opcje': []}
        finally:
            conn.close()
    
    def usun_stare_autosavy(self, limit: int = 5):
        """Usuwa najstarsze autosave'y jeśli przekroczono limit (zachowuje ostatnie N)"""
        conn = self._polacz()
        cursor = conn.cursor()
        
        try:
            ph = self._placeholder()
            
            # Najpierw sprawdź ile jest autosave'ów
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM postacie
                WHERE typ_zapisu = 'autosave'
            """)
            result = cursor.fetchone()
            total = result['cnt'] if isinstance(result, dict) else result[0]
            
            # Jeśli jest więcej niż limit, usuń najstarsze
            if total > limit:
                ile_usunac = total - limit
                cursor.execute(f"""
                    SELECT p.id FROM postacie p
                    WHERE p.typ_zapisu = 'autosave'
                    ORDER BY p.created_at ASC
                    LIMIT {ph}
                """, (ile_usunac,))
                
                stare_ids = [row['id'] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
            else:
                stare_ids = []
            
            if stare_ids:
                placeholders = ','.join([ph] * len(stare_ids))
                
                # Usuń kontekst AI
                cursor.execute(f"DELETE FROM ai_context WHERE postac_id IN ({placeholders})", stare_ids)
                
                # Usuń historię
                cursor.execute(f"DELETE FROM historia WHERE postac_id IN ({placeholders})", stare_ids)
                
                # Usuń wydarzenia
                cursor.execute(f"DELETE FROM wydarzenia WHERE postac_id IN ({placeholders})", stare_ids)
                
                # Usuń postacie
                cursor.execute(f"DELETE FROM postacie WHERE id IN ({placeholders})", stare_ids)
                
                conn.commit()
                print(f"🗑️ Usunięto {len(stare_ids)} starych autosave'ów")
                return len(stare_ids)
            
            return 0
        except Exception as e:
            print(f"❌ Błąd usuwania starych autosave'ów: {e}")
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
