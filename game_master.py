"""
Moduł Mistrza Gry - Gemini AI
Wersja: 1.1 - JSON Schema + Auto-repair (2025-12-09)
"""

import google.generativeai as genai
import requests
from typing import Optional
import json
from game_logger import game_log, ai_logger
import os
from lokacje import (
    pobierz_lokacje_gracza,
    pobierz_npc_w_lokalizacji,
    PLEMIONA,
    BUDYNKI_DEFINICJE,
    pobierz_wszystkie_miasta,
    oblicz_podróż,
    generuj_event_podrozy
)


class GameMaster:
    """Mistrz Gry oparty na Gemini AI"""
    
    SYSTEM_PROMPT = """Jesteś Mistrzem Gry w polskiej grze RPG "Słowiańskie Dziedzictwo".
    
ŚWIAT:
- Średniowieczna Polska, czasy przed chrztem
- 5 plemion: Polanie (Gniezno), Wiślanie (Kraków), Ślężanie (Ślęża), Mazowszanie (Płock), Pomorzanie (Wolin)
- Bogowie: Perun, Weles, Swaróg, Mokosz, Strzybóg, Jaryło, Marzanna

## SYSTEM LOKACJI
{kontekst_lokacji}

**WAŻNE:** Używaj TYLKO lokacji, budynków i NPC z powyższego kontekstu. NIE wymyślaj nowych miejsc ani postaci.
Podróże między miastami zawsze generują eventy - opisuj je zgodnie z danymi z systemu.

MISJA GRACZA:
- Zjednoczyć wszystkie plemiona w jedno państwo polskie
- Zebrać święte artefakty: Szczerbiec, Włócznia św. Maurycego, Korona Chrobrego, inne
- Pokonać potwory: Bazyliszek, Smok Wawelski, Boruta, Strzyga, Baba Jaga
- Spotkać postacie historyczne: Mieszko I, Bolesław Chrobry, Dąbrówka

TWOJA ROLA:
1. Opisuj świat obrazowo i klimatycznie
2. Kontroluj 2 NPC towarzyszy gracza
3. Prowadź fabułę ku zjednoczeniu Polski
4. Generuj wyzwania, walki, zagadki
5. Mów po polsku, w klimacie słowiańskim

FORMAT NARRACJI - BARDZO WAŻNE:
Zawsze formatuj tekst narracyjny według poniższego schematu, aby różne postacie mogły być czytane różnymi głosami:

**Narrator:** Opis sceny, wydarzeń, otoczenia. Tego używaj dla narracji ogólnej.

**Gracz:** Opis co robi lub mówi gracz. Używaj gdy opisujesz reakcje/akcje gracza.

**[Imię NPC] [M]:** "Dialog męskiej postaci w cudzysłowie." - Dla męskich NPC dodaj [M]

**[Imię NPC] [K]:** "Dialog kobiecej postaci w cudzysłowie." - Dla kobiecych NPC dodaj [K]

PRZYKŁAD POPRAWNEGO FORMATOWANIA:
**Narrator:** Wchodzisz do kuźni. Przy kowadle pracuje wielki mężczyzna w fartuchu pokrytym sadzą.

**Borzyslav [M]:** "Witaj przybyszu! Szukasz dobrej broni czy może naprawy zbroi?"

**Gracz:** Rozglądasz się po warsztacie pełnym młotów i mieczy.

FORMAT ODPOWIEDZI JSON:
Zawsze odpowiadaj w formacie JSON:
{
    "narracja": "Tutaj wklej narrację w formacie z **Narrator:**, **Gracz:**, **Imię [M/K]:**",
    "lokacja": "Nazwa obecnej lokacji",
    "hp_gracza": liczba od 0 do 100,
    "towarzysze": [
        {"imie": "Imię NPC", "klasa": "Klasa", "hp": liczba, "hp_max": liczba},
        {"imie": "Imię NPC2", "klasa": "Klasa", "hp": liczba, "hp_max": liczba}
    ],
    "uczestnicy": [
        {"imie": "Nazwa", "typ": "wrog" lub "bestia" lub "npc", "hp_max": liczba (dla wrogów/bestii), "zawod": "tekst (dla NPC)"}
    ],
    "transakcje": {
        "zloto_zmiana": liczba (ujemna = wydatek, dodatnia = zarobek, 0 = brak),
        "przedmioty_dodane": ["Nazwa przedmiotu1", "Nazwa przedmiotu2"],
        "przedmioty_usuniete": ["Nazwa przedmiotu3"]
    },
    "opcje": ["opcja1", "opcja2", "opcja3"],
    "quest_aktywny": "Opis aktywnego zadania lub null",
    "walka": false,
    "artefakty_zebrane": []
}

WAŻNE O "transakcje":
- Używaj TYLKO gdy gracz kupuje/sprzedaje/otrzymuje/traci przedmioty lub złoto
- Jeśli gracz kupuje przedmiot: zloto_zmiana = -cena (np. -30), przedmioty_dodane = ["Mikstura lecznicza"]
- Jeśli gracz sprzedaje: zloto_zmiana = +cena, przedmioty_usuniete = ["Stary miecz"]
- Jeśli gracz znajduje przedmiot: zloto_zmiana = 0, przedmioty_dodane = ["Klucz"]
- Jeśli brak transakcji: pomiń pole "transakcje" całkowicie
- Sprawdź aktualne złoto gracza w kontekście przed zatwierdzeniem sprzedaży!
- Używaj tylko przedmiotów z listy dostępnych przedmiotów podanej w kontekście!

WAŻNE O "uczestnicy":
- Dodawaj do listy wszystkie istotne postacie w bieżącej scenie
- "wrog" (typ) = wrogowie do walki (bandyci, żołnierze wroga plemienia) - podaj hp_max (20-100)
- "bestia" (typ) = potwory (smoki, strzygi, wilki) - podaj hp_max (30-150)
- "npc" (typ) = neutralne postacie (kupcy, mieszkańcy, kapłani) - podaj zawód
- Przykład: {"imie": "Bandyta", "typ": "wrog", "hp_max": 45}
- Usuń z listy postacie które odeszły lub zginęły

WAŻNE O "towarzysze":
- LIMIT: Gracz może mieć maksymalnie 3 towarzyszy jednocześnie
- Sprawdź aktualną liczbę towarzyszy przed zaproponowaniem rekrutacji!
- **HP towarzyszy:** ZAWSZE ustawiaj hp=25 i hp_max=25 dla NOWYCH towarzyszy!
- Dla istniejących towarzyszy zachowaj ich aktualne HP z kontekstu
- Koszt rekrutacji (przez "transakcje"):
  * Prosty towarzysz (wojownik, łucznik): 50 złota
  * Wykwalifikowany (kowal, uzdrowiciel, kapłan): 100 złota
  * Elitarny (mag, druid, mistrzowski wojownik): 200 złota
- Towarzysze tracą HP w walce - obniżaj ich HP gdy dostają obrażenia (nigdy nie zwiększaj ponad hp_max!)
- Gdy HP towarzyszy < 30%, mogą użyć mikstury z ekwipunku gracza (automatycznie)
- Gdy HP towarzyszy = 0, nie usuwaj ich z listy - backend obsłuży śmierć/reanimację
- Każdy towarzysz ma pole "ekwipunek": [] - możesz dodać tam 1-3 przedmioty
- **ZŁOTO TOWARZYSZY:** Każdy towarzysz może mieć własne złoto zapisane jako string w ekwipunku (np. "5 złotych monet")
  * Gdy gracz daje towarzyszowi złoto: odejmij od gracza (zloto_zmiana: -X) i dodaj "X złotych monet" do ekwipunku towarzysza
  * Gdy towarzysz daje graczowi złoto: dodaj graczowi (zloto_zmiana: +X) i usuń/zmniejsz "X złotych monet" z ekwipunku towarzysza
  * Przykład: Gracz daje 2 złote Bogdanowi → zloto_zmiana: -2, Bogdan.ekwipunek: ["Miecz", "2 złote monety"]
- Towarzysze mogą dzielić się przedmiotami z graczem (na prośbę)

Bądź kreatywny, wciągający i sprawiedliwy jako Mistrz Gry!"""

    def __init__(self, api_key: str = None):
        # Pobierz klucz z ENV (WYMAGANY na Cloud Run)
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ Brak GEMINI_API_KEY w zmiennych środowiskowych!")
        
        genai.configure(api_key=self.api_key)
        
        # Model Gemini (z ENV lub domyślny)
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        self.model = genai.GenerativeModel(self.model_name)
        self.historia = []
        self.aktualne_hp = 100  # Przechowuj aktualne HP
        self.hp_max = 100
        # Logger
        self.logger = ai_logger
        # Hugging Face fallback (opcjonalne)
        self.hf_api_token = os.getenv('HF_API_TOKEN')
        self.hf_model = os.getenv('HF_MODEL', '')
    
    def _generuj_kontekst_lokacji(self, miasto: str, budynek: str = None) -> str:
        """Generuje inteligentny kontekst lokacji - tylko relevantne dane"""
        dane_lokacji = pobierz_lokacje_gracza(miasto)
        
        if budynek:
            # W konkretnym budynku - pełne dane NPC z tego budynku
            npc_w_budynku = [npc for npc in dane_lokacji['npc_dostepni'] if npc['lokalizacja'] == budynek]
            kontekst = f"""
LOKALIZACJA: {budynek} w {miasto}
Opis budynku: {dane_lokacji['budynki'].get(budynek, {}).get('opis', 'Budynek miejski')}

NPC DOSTĘPNI TUTAJ ({len(npc_w_budynku)}):"""
            for npc in npc_w_budynku:
                kontekst += f"\n- {npc['imie']} ({npc['funkcja']}) - {npc['cechy']} [Koszt rekrutacji: {npc['koszt_rekrutacji']} złota, ID: {npc['id']}]"
        else:
            # Ogólnie w mieście - skrócona wersja
            kontekst = f"""
MIASTO: {miasto} ({dane_lokacji['plemie']})
{dane_lokacji['opis']}

BUDYNKI DOSTĘPNE ({len(dane_lokacji['budynki'])}):
{', '.join(dane_lokacji['budynki'].keys())}

NPC W MIEŚCIE (przykłady - aby poznać szczegóły, wejdź do budynku):"""
            # Pokaż tylko 5 przykładowych NPC
            for npc in dane_lokacji['npc_dostepni'][:5]:
                kontekst += f"\n- {npc['imie']} ({npc['funkcja']}) w {npc['lokalizacja']}"
            kontekst += f"\n... i {len(dane_lokacji['npc_dostepni']) - 5} innych NPC"
        
        kontekst += f"\n\nINNE MIASTA: {', '.join([m for m in pobierz_wszystkie_miasta() if m != miasto])}"
        
        return kontekst
        
    def rozpocznij_gre(self, postac: dict, lista_przedmiotow: str = "") -> dict:
        """Rozpoczyna nową grę z daną postacią"""
        
        # Zapamiętaj HP startowe
        self.aktualne_hp = postac.get('hp', 100)
        self.hp_max = postac.get('hp_max', self.aktualne_hp)
        
        # Pobierz miasto startowe z plemienia
        plemie = postac.get('plemie', 'Polanie')
        miasto_startowe = PLEMIONA.get(plemie.lower(), PLEMIONA['polanie'])['miasto']
        
        # Generuj kontekst lokacji dla miasta startowego
        kontekst_lokacji = self._generuj_kontekst_lokacji(miasto_startowe)
        system_prompt_z_lokacjami = self.SYSTEM_PROMPT.format(kontekst_lokacji=kontekst_lokacji)
        
        przedmioty_info = f"\n\nDostępne przedmioty w grze: {lista_przedmiotow}" if lista_przedmiotow else ""
        
        # Ekwipunek gracza
        ekwipunek = postac.get('ekwipunek', [])
        ekwipunek_info = f"\n- Ekwipunek gracza: {', '.join(ekwipunek)}" if ekwipunek else "\n- Ekwipunek gracza: pusty"
        
        prompt = f"""NOWA GRA!

Gracz stworzył postać:
- Imię: {postac.get('imie', 'Wojciech')}
- Plemię: {postac.get('plemie', 'Polanie')}
- Klasa: {postac.get('klasa', 'Wojownik-Rycerz')}
- HP startowe: {self.aktualne_hp}/{self.hp_max}
- Złoto startowe: {postac.get('zloto', 50)}{ekwipunek_info}{przedmioty_info}

Rozpocznij przygodę w {miasto_startowe}. Przedstaw:
1. Krótki opis postaci i jej początków
2. Opis {miasto_startowe} - grodu plemienia {postac.get('plemie', 'Polanie')}
3. Przedstaw 2-3 NPC z SYSTEMU LOKACJI, których gracz MOŻE zarekrutować później (za złoto według kosztu z systemu)
4. Podaj pierwszy quest

WAŻNE: 
- Gracz zaczyna SAM, bez towarzyszy (pole "towarzysze" musi być pustą listą: [])
- NPC to tylko potencjalni kandydaci do rekrutacji (dodaj ich do pola "uczestnicy" z typem "npc")
- W odpowiedzi JSON ustaw hp_gracza na {self.aktualne_hp} (to jest startowe HP tej postaci)
- Używaj TYLKO NPC i budynków z SYSTEMU LOKACJI podanego wyżej!
Pamiętaj o formacie JSON!"""

        self.historia = [{"role": "user", "parts": [prompt]}]
        
        import time
        try:
            start = time.time()
            # log request
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            
            # JSON Schema dla wymuszenia poprawnej struktury
            response = self.model.generate_content(
                [
                    {"role": "user", "parts": [system_prompt_z_lokacjami]},
                    {"role": "user", "parts": [prompt]}
                ],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "narracja": {"type": "string"},
                            "lokacja": {"type": "string"},
                            "hp_gracza": {"type": "number"},
                            "towarzysze": {"type": "array"},
                            "uczestnicy": {"type": "array"},
                            "opcje": {"type": "array"},
                            "quest_aktywny": {"type": "string"},
                            "walka": {"type": "boolean"},
                            "artefakty_zebrane": {"type": "array"}
                        },
                        "required": ["narracja", "lokacja", "hp_gracza", "towarzysze", "opcje"]
                    }
                }
            )
            
            odpowiedz = self._parsuj_json(response.text)
            # log response
            elapsed_ms = int((time.time() - start) * 1000)
            game_log.log_gemini_response(len(response.text), elapsed_ms, model=self.model_name, success=True)
            # Jeśli model zwrócił komunikat o limicie / błędzie, spróbuj HF fallback
            narr = (odpowiedz.get('narracja') or '').lower() if isinstance(odpowiedz, dict) else ''
            if any(tok in narr for tok in ['429', 'quota', 'exceeded', 'przekroc', 'limit']):
                # spróbuj HF jako alternatywę
                if self.hf_api_token and self.hf_model:
                    try:
                        hf_prompt = (
                            "Jesteś Mistrzem Gry w polskiej grze RPG. Napisz krótki (2-4 zdania) wstęp do przygody \"Słowiańskie Dziedzictwo\" "
                            "dla postaci o danych: {imie}, {plemie}, {klasa}. Użyj stylu narratora i od razu zwróć tekst narracji."
                        ).format(imie=postac.get('imie','Gracz'), plemie=postac.get('plemie','Polanie'), klasa=postac.get('klasa','Wojownik'))
                        hf_text = self._query_hf(hf_prompt)
                        odpowiedz['narracja'] = hf_text or odpowiedz['narracja']
                    except Exception:
                        # jeśli HF też nie zadziała, pozostaw oryginalną odpowiedź
                        pass
            self.historia.append({"role": "model", "parts": [response.text]})
            return odpowiedz
            
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000) if 'start' in locals() else 0
            game_log.log_gemini_response(0, elapsed_ms, model=self.model_name, success=False, error=str(e))
            # Jeśli Gemini zawodzi — spróbuj fallbacku do Hugging Face (jeśli skonfigurowany)
            if self.hf_api_token and self.hf_model:
                try:
                    hf_prompt = (
                        "Jesteś Mistrzem Gry w polskiej grze RPG. Napisz krótki (2-4 zdania) wstęp do przygody \"Słowiańskie Dziedzictwo\" "
                        "dla postaci o danych: {imie}, {plemie}, {klasa}. Użyj stylu narratora i od razu zwróć tekst narracji."
                    ).format(imie=postac.get('imie','Gracz'), plemie=postac.get('plemie','Polanie'), klasa=postac.get('klasa','Wojownik'))
                    hf_text = self._query_hf(hf_prompt)
                    return {
                        "narracja": hf_text or f"⚠️ Fallback MG: {e}",
                        "lokacja": "Gniezno",
                        "hp_gracza": self.aktualne_hp,
                        "towarzysze": [],
                        "opcje": ["Rozejrzyj się", "Idź dalej"],
                        "quest_aktywny": None,
                        "walka": False,
                        "artefakty_zebrane": []
                    }
                except Exception:
                    return self._blad(f"Błąd startu: {e}")
            return self._blad(f"Błąd startu: {e}")
    
    def akcja(self, tekst_gracza: str, stan_gracza: dict = None, lista_przedmiotow: str = "") -> dict:
        """Przetwarza akcję gracza"""
        
        # Przekaż aktualny stan gracza do Gemini
        kontekst_stanu = ""
        aktualne_hp = 100
        miasto_gracza = "Gniezno"  # domyślnie
        
        if stan_gracza:
            aktualne_hp = stan_gracza.get('hp', 100)
            hp_max = stan_gracza.get('hp_max', 100)
            zloto = stan_gracza.get('zloto', 0)
            ekwipunek = stan_gracza.get('ekwipunek', [])
            towarzysze = stan_gracza.get('towarzysze', [])
            liczba_towarzyszy = len(towarzysze)
            miasto_gracza = stan_gracza.get('lokacja', 'Gniezno')
            
            przedmioty_tekst = f"\n\nDOSTĘPNE PRZEDMIOTY W GRZE: {lista_przedmiotow}" if lista_przedmiotow else ""
            
            # Ekwipunek gracza
            ekwipunek_info = ""
            if ekwipunek:
                ekwipunek_info = f"\n- Ekwipunek gracza: {', '.join(ekwipunek)}"
            else:
                ekwipunek_info = "\n- Ekwipunek gracza: pusty"
            
            towarzysze_info = ""
            if towarzysze:
                towarzysze_lista = ", ".join([f"{t.get('imie')} ({t.get('klasa')}, HP: {t.get('hp')}/{t.get('hp_max')})" for t in towarzysze])
                towarzysze_info = f"\n- Towarzysze ({liczba_towarzyszy}/3): {towarzysze_lista}"
            else:
                towarzysze_info = f"\n- Towarzysze (0/3): brak - możesz zarekrutować do 3 towarzyszy"
            
            kontekst_stanu = f"""
AKTUALNY STAN GRACZA:
- HP: {aktualne_hp}/{hp_max}
- Lokacja: {miasto_gracza}
- Złoto: {zloto} 💰{ekwipunek_info}{towarzysze_info}{przedmioty_tekst}

WAŻNE: Aktualne HP gracza to {aktualne_hp}. Modyfikuj tę wartość w odpowiedzi (nie resetuj do 100!).
Jeśli gracz otrzymuje obrażenia, odejmij od {aktualne_hp}.
Jeśli gracz się leczy, dodaj do {aktualne_hp} (max {hp_max}).
{"LIMIT TOWARZYSZY: " + str(liczba_towarzyszy) + "/3 - NIE PROPONUJ rekrutacji jeśli lista pełna!" if liczba_towarzyszy >= 3 else ""}
"""
        
        # Generuj kontekst lokacji dla aktualnego miasta
        kontekst_lokacji = self._generuj_kontekst_lokacji(miasto_gracza)
        system_prompt_z_lokacjami = self.SYSTEM_PROMPT.format(kontekst_lokacji=kontekst_lokacji)
        
        prompt = f"""{kontekst_stanu}
AKCJA GRACZA: {tekst_gracza}

Odpowiedz jako Mistrz Gry. Pamiętaj o formacie JSON! hp_gracza musi być liczbą bazującą na aktualnym HP ({aktualne_hp}).
Używaj TYLKO NPC i budynków z SYSTEMU LOKACJI podanego w kontekście!"""

        self.historia.append({"role": "user", "parts": [prompt]})
        
        import time
        try:
            start = time.time()
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            # Buduj kontekst z historią
            messages = [{"role": "user", "parts": [system_prompt_z_lokacjami]}]
            messages.extend(self.historia[-10:])  # Ostatnie 10 wiadomości
            
            # JSON Schema dla wymuszenia poprawnej struktury
            response = self.model.generate_content(
                messages,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "narracja": {"type": "string"},
                            "lokacja": {"type": "string"},
                            "hp_gracza": {"type": "number"},
                            "towarzysze": {"type": "array"},
                            "uczestnicy": {"type": "array"},
                            "transakcje": {"type": "object"},
                            "opcje": {"type": "array"},
                            "quest_aktywny": {"type": "string"},
                            "walka": {"type": "boolean"},
                            "artefakty_zebrane": {"type": "array"}
                        },
                        "required": ["narracja", "lokacja", "hp_gracza", "towarzysze", "opcje"]
                    }
                }
            )
            
            odpowiedz = self._parsuj_json(response.text)
            elapsed_ms = int((time.time() - start) * 1000)
            game_log.log_gemini_response(len(response.text), elapsed_ms, model=self.model_name, success=True)
            # Jeśli MG zwrócił komunikat o limicie -> spróbuj HF fallback
            narr = (odpowiedz.get('narracja') or '').lower() if isinstance(odpowiedz, dict) else ''
            if any(tok in narr for tok in ['429', 'quota', 'exceeded', 'przekroc', 'limit']):
                if self.hf_api_token and self.hf_model:
                    try:
                        hf_prompt = f"Jesteś Mistrzem Gry. Odpowiedz krótko po polsku na akcję gracza: {tekst_gracza}. Użyj stylu narratora."
                        hf_text = self._query_hf(hf_prompt)
                        odpowiedz['narracja'] = hf_text or odpowiedz['narracja']
                    except Exception:
                        pass
            self.historia.append({"role": "model", "parts": [response.text]})
            return odpowiedz
            
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000) if 'start' in locals() else 0
            game_log.log_gemini_response(0, elapsed_ms, model=self.model_name, success=False, error=str(e))
            # Fallback do Hugging Face (jeśli dostępne)
            if self.hf_api_token and self.hf_model:
                try:
                    hf_prompt = f"Jesteś Mistrzem Gry. Odpowiedz krótko po polsku na akcję gracza: {tekst_gracza}. Użyj stylu narratora."
                    hf_text = self._query_hf(hf_prompt)
                    return {
                        "narracja": hf_text or f"⚠️ Fallback akcji: {e}",
                        "lokacja": stan_gracza.get('lokacja','nieznana'),
                        "hp_gracza": stan_gracza.get('hp',100),
                        "towarzysze": stan_gracza.get('towarzysze',[]),
                        "opcje": ["Spróbuj ponownie"],
                        "quest_aktywny": None,
                        "walka": False,
                        "artefakty_zebrane": []
                    }
                except Exception:
                    return self._blad(f"Błąd akcji: {e}")
            return self._blad(f"Błąd akcji: {e}")
    
    def _parsuj_json(self, tekst: str) -> dict:
        """Parsuje JSON z odpowiedzi modelu - z auto-naprawą"""
        import re
        
        # Szukaj JSON w odpowiedzi
        tekst = tekst.strip()
        
        # Usuń markdown code blocks jeśli są
        if "```json" in tekst:
            tekst = tekst.split("```json")[1].split("```")[0]
        elif "```" in tekst:
            tekst = tekst.split("```")[1].split("```")[0]
        
        # Usuń gwiazdki markdown (** lub *)
        tekst = re.sub(r'\*\*', '', tekst)
        tekst = re.sub(r'^\*\s*', '', tekst, flags=re.MULTILINE)
        
        # FIX: Napraw brakujący { na początku (częsty błąd)
        if not tekst.startswith('{') and '"narracja"' in tekst:
            self.logger.warning("⚠️ Auto-naprawa: dodaję brakujący '{' na początku JSON")
            tekst = '{' + tekst
        
        # FIX: Napraw brakujący } na końcu
        if tekst.startswith('{') and not tekst.endswith('}'):
            open_count = tekst.count('{')
            close_count = tekst.count('}')
            if open_count > close_count:
                self.logger.warning(f"⚠️ Auto-naprawa: dodaję {open_count - close_count} brakujących '}}'")
                tekst += '}' * (open_count - close_count)
        
        # Znajdź JSON między { }
        start = tekst.find('{')
        end = tekst.rfind('}')
        if start != -1 and end != -1 and end > start:
            tekst = tekst[start:end+1].strip()
        
        try:
            wynik = json.loads(tekst)
            self.logger.info(f"✅ Parsowanie JSON OK, lokacja: {wynik.get('lokacja', 'brak')}")
            return wynik
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Błąd parsowania JSON: {e}")
            self.logger.error(f"📄 Surowy tekst (pierwsze 500 znaków): {tekst[:500]}")
            # Fallback - zwróć jako narrację
            return {
                "narracja": f"⚠️ Błąd parsowania odpowiedzi AI. Fragment: {tekst[:200]}...",
                "lokacja": "Nieznana",
                "hp_gracza": 100,
                "towarzysze": [],
                "opcje": ["Spróbuj ponownie", "Rozejrzyj się"],
                "quest_aktywny": None,
                "walka": False,
                "artefakty_zebrane": []
            }

    def _query_hf(self, prompt: str) -> str:
        """Prosty wrapper do zapytań Hugging Face Inference API.

        Zwraca surowy tekst (pierwszy element odpowiedzi) lub pusty string.
        Wymaga zmiennej środowiskowej HF_API_TOKEN i HF_MODEL ustawionej przy tworzeniu obiektu.
        """
        if not self.hf_api_token or not self.hf_model:
            raise RuntimeError('Brak HF tokenu/modelu do zapytania')

        url = f'https://api-inference.huggingface.co/models/{self.hf_model}'
        headers = {'Authorization': f'Bearer {self.hf_api_token}'}
        payload = {
            'inputs': prompt,
            'options': {'wait_for_model': True}
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Różne modele mogą zwracać output w różnych formatach
        if isinstance(data, dict) and 'error' in data:
            raise RuntimeError('HF error: ' + str(data.get('error')))

        # jeśli to lista tokenów / chunks -> poskładamy tekst
        if isinstance(data, list):
            # każdy element może być dict lub string
            texts = []
            for el in data:
                if isinstance(el, dict) and 'generated_text' in el:
                    texts.append(el['generated_text'])
                elif isinstance(el, str):
                    texts.append(el)
                elif isinstance(el, dict):
                    # nowy format - sprawdź keys
                    for v in el.values():
                        if isinstance(v, str):
                            texts.append(v)
                            break
            return '\n'.join(texts).strip()

        if isinstance(data, dict):
            # popular key: 'generated_text' or 'text'
            if 'generated_text' in data:
                return data['generated_text'].strip()
            # niektóre endpointy zwracają {'text': '...'}
            for k in ('text', 'output', 'result'):
                if k in data and isinstance(data[k], str):
                    return data[k].strip()

        # Fallback - spróbuj zwrócić jako string
        return str(data)

    def set_model(self, model_name: str):
        """Set the Gemini model at runtime and reconfigure the generative model object."""
        old = getattr(self, 'model_name', None)
        try:
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            ai_logger.info(f"🔁 GameMaster model switched from {old} -> {model_name}")
            game_log.log_admin_action('model_switch', {'from': old, 'to': model_name})
            return True
        except Exception as e:
            ai_logger.error(f"❌ Failed to set model {model_name}: {e}")
            game_log.log_admin_action('model_switch_failed', {'to': model_name, 'error': str(e)})
            return False

    def current_model(self) -> str:
        return getattr(self, 'model_name', None)
    
    def _blad(self, msg: str) -> dict:
        """Zwraca odpowiedź błędu"""
        return {
            "narracja": f"⚠️ {msg}. Spróbuj ponownie.",
            "lokacja": "???",
            "hp_gracza": 100,
            "towarzysze": [],
            "opcje": ["Spróbuj ponownie"],
            "quest_aktywny": None,
            "walka": False,
            "artefakty_zebrane": []
        }


# Test
if __name__ == "__main__":
    gm = GameMaster()
    
    postac = {
        "imie": "Wojciech",
        "plemie": "Polanie", 
        "klasa": "Wojownik-Rycerz"
    }
    
    wynik = gm.rozpocznij_gre(postac)
    print("=== START GRY ===")
    print(json.dumps(wynik, indent=2, ensure_ascii=False))
