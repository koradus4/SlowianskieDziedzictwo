"""
Moduł Mistrza Gry - Gemini AI
"""

import google.generativeai as genai
import requests
from typing import Optional
import json
from game_logger import game_log, ai_logger
import os


class GameMaster:
    """Mistrz Gry oparty na Gemini AI"""
    
    SYSTEM_PROMPT = """Jesteś Mistrzem Gry w polskiej grze RPG "Słowiańskie Dziedzictwo".
    
ŚWIAT:
- Średniowieczna Polska, czasy przed chrztem
- 5 plemion: Polanie (Gniezno), Wiślanie (Kraków), Ślężanie (Wrocław), Mazowszanie (Płock), Pomorzanie (Gdańsk)
- Bogowie: Perun, Weles, Swaróg, Mokosz, Strzybóg, Jaryło, Marzanna

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
- Koszt rekrutacji (przez "transakcje"):
  * Prosty towarzysz (wojownik, łucznik): 50 złota
  * Wykwalifikowany (kowal, uzdrowiciel, kapłan): 100 złota
  * Elitarny (mag, druid, mistrzowski wojownik): 200 złota
- Towarzysze tracą HP w walce - obniżaj ich HP gdy dostają obrażenia
- Gdy HP towarzyszy < 30%, mogą użyć mikstury z ekwipunku gracza (automatycznie)
- Gdy HP towarzyszy = 0, nie usuwaj ich z listy - backend obsłuży śmierć/reanimację
- Każdy towarzysz ma pole "ekwipunek": [] - możesz dodać tam 1-3 przedmioty
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
        # Hugging Face fallback (opcjonalne)
        self.hf_api_token = os.getenv('HF_API_TOKEN')
        self.hf_model = os.getenv('HF_MODEL', '')
        
    def rozpocznij_gre(self, postac: dict, lista_przedmiotow: str = "") -> dict:
        """Rozpoczyna nową grę z daną postacią"""
        
        # Zapamiętaj HP startowe
        self.aktualne_hp = postac.get('hp', 100)
        self.hp_max = postac.get('hp_max', self.aktualne_hp)
        
        przedmioty_info = f"\n\nDostępne przedmioty w grze: {lista_przedmiotow}" if lista_przedmiotow else ""
        
        prompt = f"""NOWA GRA!

Gracz stworzył postać:
- Imię: {postac.get('imie', 'Wojciech')}
- Plemię: {postac.get('plemie', 'Polanie')}
- Klasa: {postac.get('klasa', 'Wojownik-Rycerz')}
- HP startowe: {self.aktualne_hp}/{self.hp_max}
- Złoto startowe: 50{przedmioty_info}

Rozpocznij przygodę w Gnieźnie. Przedstaw:
1. Krótki opis postaci i jej początków
2. Opis Gniezna - grodu Polan
3. Wygeneruj 2 NPC towarzyszy (różne klasy)
4. Podaj pierwszy quest

WAŻNE: W odpowiedzi JSON ustaw hp_gracza na {self.aktualne_hp} (to jest startowe HP tej postaci).
Pamiętaj o formacie JSON!"""

        self.historia = [{"role": "user", "parts": [prompt]}]
        
        import time
        try:
            start = time.time()
            # log request
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            response = self.model.generate_content([
                {"role": "user", "parts": [self.SYSTEM_PROMPT]},
                {"role": "user", "parts": [prompt]}
            ])
            
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
        if stan_gracza:
            aktualne_hp = stan_gracza.get('hp', 100)
            hp_max = stan_gracza.get('hp_max', 100)
            zloto = stan_gracza.get('zloto', 0)
            towarzysze = stan_gracza.get('towarzysze', [])
            liczba_towarzyszy = len(towarzysze)
            
            przedmioty_tekst = f"\n\nDOSTĘPNE PRZEDMIOTY W GRZE: {lista_przedmiotow}" if lista_przedmiotow else ""
            
            towarzysze_info = ""
            if towarzysze:
                towarzysze_lista = ", ".join([f"{t.get('imie')} ({t.get('klasa')}, HP: {t.get('hp')}/{t.get('hp_max')})" for t in towarzysze])
                towarzysze_info = f"\n- Towarzysze ({liczba_towarzyszy}/3): {towarzysze_lista}"
            else:
                towarzysze_info = f"\n- Towarzysze (0/3): brak - możesz zarekrutować do 3 towarzyszy"
            
            kontekst_stanu = f"""
AKTUALNY STAN GRACZA:
- HP: {aktualne_hp}/{hp_max}
- Lokacja: {stan_gracza.get('lokacja', 'nieznana')}
- Złoto: {zloto} 💰{towarzysze_info}{przedmioty_tekst}

WAŻNE: Aktualne HP gracza to {aktualne_hp}. Modyfikuj tę wartość w odpowiedzi (nie resetuj do 100!).
Jeśli gracz otrzymuje obrażenia, odejmij od {aktualne_hp}.
Jeśli gracz się leczy, dodaj do {aktualne_hp} (max {hp_max}).
{"LIMIT TOWARZYSZY: " + str(liczba_towarzyszy) + "/3 - NIE PROPONUJ rekrutacji jeśli lista pełna!" if liczba_towarzyszy >= 3 else ""}
"""
        
        prompt = f"""{kontekst_stanu}
AKCJA GRACZA: {tekst_gracza}

Odpowiedz jako Mistrz Gry. Pamiętaj o formacie JSON! hp_gracza musi być liczbą bazującą na aktualnym HP ({aktualne_hp})."""

        self.historia.append({"role": "user", "parts": [prompt]})
        
        import time
        try:
            start = time.time()
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            # Buduj kontekst z historią
            messages = [{"role": "user", "parts": [self.SYSTEM_PROMPT]}]
            messages.extend(self.historia[-10:])  # Ostatnie 10 wiadomości
            
            response = self.model.generate_content(messages)
            
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
        """Parsuje JSON z odpowiedzi modelu"""
        # Szukaj JSON w odpowiedzi
        tekst = tekst.strip()
        
        # Usuń markdown code blocks jeśli są
        if "```json" in tekst:
            tekst = tekst.split("```json")[1].split("```")[0]
        elif "```" in tekst:
            tekst = tekst.split("```")[1].split("```")[0]
        
        try:
            return json.loads(tekst)
        except json.JSONDecodeError:
            # Fallback - zwróć jako narrację
            return {
                "narracja": tekst,
                "lokacja": "Nieznana",
                "hp_gracza": 100,
                "towarzysze": [],
                "opcje": ["Rozejrzyj się", "Idź dalej", "Odpoczywaj"],
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
