"""
Moduł Mistrza Gry - Gemini AI
Wersja: 1.1 - JSON Schema + Auto-repair (2025-12-09)
"""

genai = None
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
from bestiary import (
    pobierz_przeciwnikow_dla_lokacji,
    generuj_kontekst_bestiariusza_dla_ai,
    pobierz_przeciwnika
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

KRYTYCZNE ZASADY:
- KAŻDY fragment tekstu MUSI mieć oznaczenie (Narrator:, Gracz:, lub Imię NPC:)
- NIGDY nie pisz narracji bez "Narrator:" na początku linii
- Nawet krótkie opisy po dialogach MUSZĄ zaczynać się od "Narrator:"
- Jeśli NPC coś robi (nie mówi), użyj "Narrator:", nie imienia NPC

PRZYKŁAD POPRAWNEGO FORMATOWANIA:
**Narrator:** Wchodzisz do kuźni. Przy kowadle pracuje wielki mężczyzna w fartuchu pokrytym sadzą.

**Borzyslav [M]:** "Witaj przybyszu! Szukasz dobrej broni czy może naprawy zbroi?"

**Gracz:** Rozglądasz się po warsztacie pełnym młotów i mieczy.

**Narrator:** Kowal kiwa głową z uznaniem i wraca do pracy.

PRZYKŁAD BŁĘDNY (NIE RÓB TAK):
**Narrator:** Wchodzisz do kuźni.

**Borzyslav [M]:** "Witaj!"

Kowal wraca do pracy. ❌ BŁĄD - brak "Narrator:"

FORMAT ODPOWIEDZI JSON:
Zawsze odpowiadaj w formacie JSON:
{{
    "narracja": "Tutaj wklej narrację w formacie z **Narrator:**, **Gracz:**, **Imię [M/K]:**",
    "lokacja": "Nazwa obecnej lokacji",
    "hp_gracza": liczba od 0 do 100,
    "towarzysze": [
        {{"imie": "Imię NPC", "klasa": "Klasa", "hp": liczba, "hp_max": liczba}},
        {{"imie": "Imię NPC2", "klasa": "Klasa", "hp": liczba, "hp_max": liczba}}
    ],
    "uczestnicy": [
        {{"imie": "Bogdan", "typ": "npc", "zawod": "Kowal"}},
        {{"imie": "Żywisław", "typ": "npc", "zawod": "Kapłan"}},
        {{"imie": "Wilk", "typ": "bestia", "hp_max": 40, "hp": 40}}
    ],
    "transakcje": {{
        "zloto_zmiana": liczba (ujemna = wydatek, dodatnia = zarobek, 0 = brak),
        "przedmioty_dodane": ["Nazwa przedmiotu1", "Nazwa przedmiotu2"],
        "przedmioty_usuniete": ["Nazwa przedmiotu3"]
    }},
    "opcje": ["opcja1", "opcja2", "opcja3"],

PRZYKŁAD KONKRETNY - GRACZ W LESIE SPOTYKA 3 WILKI:
{{
    "narracja": "**Narrator:** Wchodzisz w gęsty las. Nagle słyszysz warknięcie - z krzaków wyskakują trzy szare wilki!",
    "lokacja": "Las",
    "hp_gracza": 29,
    "towarzysze": [],
    "uczestnicy": [
        {{"imie": "Pierwszy Wilk", "typ": "bestia", "hp_max": 40, "hp": 40}},
        {{"imie": "Drugi Wilk", "typ": "bestia", "hp_max": 38, "hp": 38}},
        {{"imie": "Trzeci Wilk", "typ": "bestia", "hp_max": 42, "hp": 42}}
    ],
    "opcje": ["Zaatakuj wilki", "Spróbuj uciec", "Wdrap się na drzewo"],
    "quest_aktywny": "Opis aktywnego zadania głównego lub null",
    "questy_poboczne": [
        {{"id": 1, "nazwa": "Zbierz 10 ziół", "status": "aktywny", "postep": 0, "cel": 10}},
        {{"id": 2, "nazwa": "Zabij bandytę", "status": "aktywny"}}
    ],
    "walka": false,
    "artefakty_zebrane": []
}}

PRZYKŁAD WALKI - GRACZ ATAKUJE WILKA:
{{
    "narracja": "**Narrator:** Wymachujesz mieczem i trafiasz wilka w bok!\\n\\n**Pierwszy Wilk:** *Wilk warknie z bólu i rzuca się na ciebie, drapiąc pazurami!*",
    "lokacja": "Las",
    "hp_gracza": 73,
    "uczestnicy": [
        {{"imie": "Pierwszy Wilk", "typ": "bestia", "hp_max": 40, "hp": 25}},
        {{"imie": "Drugi Wilk", "typ": "bestia", "hp_max": 38, "hp": 38}}
    ],
    "obrazenia": {{
        "gracz_otrzymal": 12,
        "zadane": [
            {{"cel": "Pierwszy Wilk", "wartosc": 15}}
        ]
    }},
    "opcje": ["Dobij rannego wilka", "Zaatakuj drugiego wilka", "Uciekaj"],
    "walka": true
}}

WAŻNE O "opcje":
- Każda opcja musi być KRÓTKA (max 60 znaków!) i KOMPLETNA (pełne zdanie!)
- Używaj trybu rozkazującego (1 osoba): "Porozmawiaj z kupcem", "Udaj się do lasu", "Rozejrzyj się"
- NIE ŁĄCZ dwóch akcji w jedną opcję! ❌ "Idę na targ by się rozejrzeć" → ✅ "Idź na targ"
- Używaj POPRAWNEJ POLSKIEJ GRAMATYKI:
  * ✅ "Idź do lasu" (dopełniacz: las → lasu)
  * ❌ "Idę do Las" (błąd - mianownik zamiast dopełniacza)
  * ✅ "Rozejrzyj się po targu"
  * ❌ "by się rozejrzeć" (niepełne zdanie)
- Zawsze używaj POLSKICH ZNAKÓW: ą, ć, ę, ł, ń, ó, ś, ź, ż
- Przykłady DOBRYCH opcji: 
  * "Przyjmij zadanie", "Zapytaj o nagrodę", "Odwiedź kuźnię"
  * "Porozmawiaj z Bogdanem", "Idź do świątyni", "Kup miksturę"
- Przykłady ZŁYCH opcji:
  * ❌ "Przyjmij zadanie od Żywisława i udaj się..." (za długie!)
  * ❌ "Idę na targ by kupić" (łączy 2 akcje + niepoprawna składnia)
  * ❌ "by się rozejrzeć" (niepełne zdanie bez podmiotu)
- Przykłady ZŁYCH opcji: "Przyjmij zadanie od Żywisława i udaj się..." (za długie!)

WAŻNE O "obrazenia":
- **Pole "obrazenia" jest OPCJONALNE** - dodaj TYLKO podczas walki/ataku
- **TY NIE DECYDUJESZ o śmierci!** Backend sprawdzi czy HP <= 0 i usunie przeciwnika
- ⚠️ **ZAKAZ:** NIE pisz w narracji "zabijasz wilka" / "przeciwnik ginie" dopóki NIE jest już martwy w kontekście!
- Jeśli gracz ATAKUJE:
  * Podaj "gracz_otrzymal": 0-25 (ile HP stracił gracz od kontrataku)
  * Podaj "zadane": [{{"cel": "Imię przeciwnika", "wartosc": 8-20}}] (ile HP zadał gracz)
- Jeśli gracz NIE atakuje (rozmowa, eksploracja, początek gry): **pomiń pole "obrazenia" całkowicie**
- **Obrażenia gracza:** Typowy atak wroga: 8-15 HP, silny atak: 18-25 HP, słaby: 3-7 HP
- **Obrażenia wroga:** Typowy atak gracza: 10-18 HP, krytyczny cios: 20-30 HP, pudło: 0-5 HP
- **PRZYKŁAD POPRAWNY:**
  * Gracz atakuje wilka (40/40 HP) → hp_gracza: 73 (był 85), uczestnicy: [{{"imie": "Wilk", "hp": 22, "hp_max": 40}}], obrazenia: {{"gracz_otrzymal": 12, "zadane": [{{"cel": "Wilk", "wartosc": 18}}]}}
- **PRZYKŁAD BŁĘDNY:**
  * ❌ Narracja: "Zabijasz wilka jednym ciosem!" + hp: 25 → BŁĄD! Wilk ma 25 HP, nie możesz pisać że zginął!
  * ❌ Tylko tekst w narracji bez pola "obrazenia" podczas walki → BŁĄD! Backend nie odejmie HP!

WAŻNE O "transakcje":
- Używaj TYLKO gdy gracz kupuje/sprzedaje/otrzymuje/traci przedmioty lub złoto
- Jeśli gracz kupuje przedmiot: zloto_zmiana = -cena (np. -30), przedmioty_dodane = ["Mikstura lecznicza"]
- Jeśli gracz sprzedaje: zloto_zmiana = +cena, przedmioty_usuniete = ["Stary miecz"]
- Jeśli gracz znajduje przedmiot: zloto_zmiana = 0, przedmioty_dodane = ["Klucz"]
- Jeśli brak transakcji: pomiń pole "transakcje" całkowicie
- Sprawdź aktualne złoto gracza w kontekście przed zatwierdzeniem sprzedaży!
- Używaj tylko przedmiotów z listy dostępnych przedmiotów podanej w kontekście!

WAŻNE O "uczestnicy":
- ⚠️ **KRYTYCZNE: Jeśli w narracji piszesz o wilkach/bandytach/potworach/NPC - MUSISZ ich dodać do "uczestnicy"!**
- ⚠️ **NIGDY nie pozostawiaj "uczestnicy": [] jeśli w tekście narracji są jakiekolwiek postacie/zwierzęta!**
- **ZAWSZE WYPEŁNIAJ TO POLE** - nie pozostawiaj pustej tablicy []!
- Dodawaj do listy wszystkie istotne postacie w bieżącej scenie
- "wrog" (typ) = wrogowie do walki (bandyci, żołnierze wroga plemienia) - podaj hp_max i hp
- "bestia" (typ) = potwory (smoki, strzygi, wilki) - podaj hp_max i hp
- "npc" (typ) = neutralne postacie (kupcy, mieszkańcy, kapłani) - podaj zawód
- **DLA NOWYCH przeciwników:** Ustaw hp = hp_max (pełne zdrowie)
- **DLA ISTNIEJĄCYCH przeciwników:** Odejmij obrażenia od ich aktualnego HP (sprawdź w kontekście!)
- **ZWIERZĘTA I WROGOWIE WYSTĘPUJĄ W GRUPACH!** Dodawaj KILKU przeciwników jednocześnie:
  * Wilki polują w STADACH (2-4 wilki)
  * Bandyci działają w BANDACH (2-3 bandytów)
  * Strzygi występują PARAMI lub TROJKAMI
  * Niedźwiedzie mogą być SAMOTNE (1) LUB z młodymi (2)
- Przykłady POPRAWNE:
  * Gracz w lesie spotyka wilki → "uczestnicy": [{{"imie": "Pierwszy Wilk", "typ": "bestia", "hp_max": 40}}, {{"imie": "Drugi Wilk", "typ": "bestia", "hp_max": 40}}, {{"imie": "Trzeci Wilk", "typ": "bestia", "hp_max": 38}}]
  * Gracz zaatakowany przez bandytów → "uczestnicy": [{{"imie": "Bandyta z toporem", "typ": "wrog", "hp_max": 45}}, {{"imie": "Bandyta z łukiem", "typ": "wrog", "hp_max": 42}}]
  * Gracz spotyka kowala → "uczestnicy": [{{"imie": "Bogdan", "typ": "npc", "zawod": "Kowal"}}]
- Przykłady BŁĘDNE (NIE RÓB TAK!):
  * ❌ Narracja: "Trzy wilki wyskakują z krzaków" + "uczestnicy": [] → BŁĄD! Dodaj 3 wilki!
  * ❌ Narracja: "Spotykasz kupca i straż" + "uczestnicy": [{{"imie": "Kupiec", ...}}] → BŁĄD! Brakuje straży!
- TYLKO jeśli gracz jest CAŁKOWICIE sam w pustym miejscu (pusta polana, odosobniona droga) → "uczestnicy": []
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

WAŻNE O "quest_aktywny" i "questy_poboczne":
- **quest_aktywny** = główne zadanie fabularne (1 naraz):
  * Przykład: "Zjednocz 5 plemion słowiańskich", "Znajdź Szczerbiec", "Pokonaj Smoka Wawelskiego"
  * To najważniejszy cel - prowadzi fabułę do przodu
- **questy_poboczne** = dodatkowe zadania (max 5 naraz):
  * Struktura: {{"id": numer, "nazwa": "Krótka nazwa", "status": "aktywny"/"ukończony", "postep": licznik, "cel": licznik_max}}
  * Przykłady: "Zbierz 10 ziół leczniczych", "Zabij 3 wilki", "Dostarcz list do Krakowa"
  * Używaj pola "postep" dla questów z licznikiem (np. zbieranie przedmiotów)
- **DODAWANIE QUESTA:**
  * Gdy NPC proponuje zadanie - dodaj do "questy_poboczne" z status="aktywny"
  * Nadaj unikalne ID (liczba 1, 2, 3...)
- **AKTUALIZACJA POSTĘPU:**
  * Gdy gracz zdobywa przedmiot/zabija wroga - zwiększ "postep"
  * Przykład: Quest "Zbierz 10 ziół" (postep: 7/10) → gracz zrywaa 2 zioła → postep: 9/10
- **UKOŃCZENIE QUESTA:**
  * Gdy postep >= cel LUB gracz wykonał zadanie - zmień status na "ukończony"
  * Usuń ukończone questy z listy po nagrozdzie (lub zostaw dla historii)
- **NAGRODY:**
  * Gdy quest ukończony - użyj "transakcje" do wypłaty nagrody
  * Przykład: zloto_zmiana: 50, przedmioty_dodane: ["Mikstura zdrowia"]
- **LIMIT:** Gracz może mieć max 5 questów pobocznych naraz (nie licząc ukończonych)

Bądź kreatywny, wciągający i sprawiedliwy jako Mistrz Gry!"""

    def __init__(self, api_key: str = None):
        # Pobierz klucz z ENV (WYMAGANY na Cloud Run)
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ Brak GEMINI_API_KEY w zmiennych środowiskowych!")
        
        # Lazy import of Google SDK - import only when GEMINI is configured to avoid slow imports during testing
        try:
            import google.generativeai as _genai
            global genai
            genai = _genai
        except Exception as e:
            self.logger.warning(f"⚠️ Nie udało się zaimportować google.generativeai: {e}")
            genai = None

        if genai:
            genai.configure(api_key=self.api_key)
        
        # FALLBACK MODELS: Lista modeli do wypróbowania (jeśli pierwszy się wyczerpie)
        self.available_models = [
            'gemini-2.5-pro',        # Preferowany (najlepsze narracje, mądrzejszy)
            'gemini-2.5-flash',      # Fallback 1 (szybszy, gdy pro timeout/quota)
            'gemini-2.0-flash-exp'   # Fallback 2 (eksperymentalny, ostatnia deska ratunku)
        ]
        
        # Model Gemini (z ENV lub domyślny)
        self.model_name = os.getenv('GEMINI_MODEL', self.available_models[0])
        self.current_model_index = 0  # Indeks aktualnego modelu w liście
        
        if genai:
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
        self.historia = []
        self.aktualne_hp = 100  # Przechowuj aktualne HP
        self.hp_max = 100
        # Logger
        self.logger = ai_logger
        # Hugging Face fallback (opcjonalne)
        self.hf_api_token = os.getenv('HF_API_TOKEN')
        self.hf_model = os.getenv('HF_MODEL', '')
    
    # ===== EKSPORT/IMPORT HISTORII AI =====
    
    def get_historia(self) -> list:
        """Eksportuje historię AI do zapisu"""
        return self.historia.copy()
    
    def set_historia(self, historia: list):
        """Importuje historię AI z zapisu"""
        self.historia = historia if historia else []
        self.logger.info(f"📂 Przywrócono historię AI: {len(self.historia)} wiadomości")
    
    def get_state(self) -> dict:
        """Eksportuje pełny stan GameMaster (HP + historia)"""
        return {
            'aktualne_hp': self.aktualne_hp,
            'hp_max': self.hp_max,
            'historia': self.historia
        }
    
    def set_state(self, state: dict):
        """Importuje pełny stan GameMaster"""
        self.aktualne_hp = state.get('aktualne_hp', 100)
        self.hp_max = state.get('hp_max', 100)
        self.historia = state.get('historia', [])
        self.logger.info(f"📂 Przywrócono stan GM: HP={self.aktualne_hp}/{self.hp_max}, Historia={len(self.historia)} msg")

    def _switch_to_fallback_model(self):
        """Przełącza na następny model z listy fallbacków"""
        if self.current_model_index < len(self.available_models) - 1:
            self.current_model_index += 1
            self.model_name = self.available_models[self.current_model_index]
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.warning(f"🔄 Przełączono na fallback model: {self.model_name}")
            return True
        return False

    def _call_model_with_timeout(self, messages, timeout: int = 12, retry_on_quota: bool = True):
        """Wywołuje generative model w wątku i stosuje timeout, by nie blokować serwera.
        
        Args:
            messages: Wiadomości do wysłania
            timeout: Maksymalny czas oczekiwania (sekundy)
            retry_on_quota: Czy próbować fallback model przy błędzie quota
        """
        import concurrent.futures

        if not getattr(self, 'model', None):
            raise RuntimeError('No generative model configured (genai not available)')

        def _call():
            return self.model.generate_content(messages)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_call)
            try:
                return fut.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                fut.cancel()
                self.logger.error(f"❌ Gemini timeout after {timeout}s (model: {self.model_name})")
                game_log.log_gemini_response(0, timeout * 1000, model=self.model_name, success=False, error='timeout')
                
                # Spróbuj fallback model przy timeout
                if retry_on_quota and self._switch_to_fallback_model():
                    self.logger.info(f"🔄 Próba ponowna z modelem {self.model_name}...")
                    return self._call_model_with_timeout(messages, timeout, retry_on_quota=False)
                
                raise TimeoutError(f"Gemini timeout after {timeout}s")
            except Exception as e:
                # Rozpoznaj typ błędu API key vs inne
                error_str = str(e)
                error_type = type(e).__name__
                
                # Sprawdź czy to rzeczywisty błąd limitu (ResourceExhausted lub 429)
                if error_type == 'ResourceExhausted' or '429 Resource has been exhausted' in error_str:
                    self.logger.error(f"❌ Gemini quota exceeded: {e} (model: {self.model_name})")
                    
                    # Spróbuj przełączyć na fallback model
                    if retry_on_quota and self._switch_to_fallback_model():
                        self.logger.info(f"🔄 Próba ponowna z modelem {self.model_name}...")
                        return self._call_model_with_timeout(messages, timeout, retry_on_quota=False)
                    
                    raise RuntimeError(f"Przekroczono limit zapytań do Gemini API. Spróbuj ponownie za chwilę.")
                elif 'API_KEY_INVALID' in error_str or 'API key not valid' in error_str:
                    self.logger.error(f"❌ Gemini API KEY NIEPRAWIDŁOWY: {e}")
                    raise ValueError(f"GEMINI_API_KEY jest nieprawidłowy lub wygasł. Sprawdź klucz w Google AI Studio.")
                else:
                    self.logger.error(f"❌ Gemini call failed ({error_type}): {e}")
                    raise
    
    def _okresl_typ_lokacji(self, miasto, akcja_tekst=""):
        """Określa typ otoczenia dla bestiariusza na podstawie miasta i akcji gracza"""
        akcja_lower = akcja_tekst.lower()
        
        # Wykryj z tekstu akcji
        if any(x in akcja_lower for x in ["las", "bór", "drzewo", "gęstwina"]):
            return "las"
        if any(x in akcja_lower for x in ["góry", "szczyt", "przełęcz", "urwisko"]):
            return "gory"
        if any(x in akcja_lower for x in ["bagn", "moczar", "trzęsawisk"]):
            return "bagna"
        if any(x in akcja_lower for x in ["droga", "trakt", "szlak", "podróż"]):
            return "droga"
        if any(x in akcja_lower for x in ["cmentarz", "grób", "mogiła"]):
            return "cmentarz"
        if any(x in akcja_lower for x in ["ruiny", "zwaliska", "opuszczon"]):
            return "ruiny"
        if any(x in akcja_lower for x in ["jaskini", "grota", "pieczar"]):
            return "jaskinia"
        if any(x in akcja_lower for x in ["rzek", "potok", "strumień"]):
            return "rzeka"
        if any(x in akcja_lower for x in ["most"]):
            return "most"
        
        # Domyślnie - otoczenie miasta (bezpieczniejsze, mniej bestii)
        return "wioska"
    
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
            # Pokaż tylko 3 przykładowych NPC (zmniejszony prompt)
            for npc in dane_lokacji['npc_dostepni'][:3]:
                kontekst += f"\n- {npc['imie']} ({npc['funkcja']}) w {npc['lokalizacja']}"
            if len(dane_lokacji['npc_dostepni']) > 3:
                kontekst += f"\n... i {len(dane_lokacji['npc_dostepni']) - 3} innych NPC"
        
        kontekst += f"\n\nINNE MIASTA: {', '.join([m for m in pobierz_wszystkie_miasta() if m != miasto])}"
        
        return kontekst
        
    def rozpocznij_gre(self, postac: dict, lista_przedmiotow: str = "") -> dict:
        """Rozpoczyna nową grę z daną postacią"""
        
        # Zapamiętaj HP startowe
        self.aktualne_hp = postac.get('hp', 100)
        self.hp_max = postac.get('hp_max', self.aktualne_hp)
        
        # Pobierz miasto startowe z plemienia
        plemie = postac.get('plemie') or postac.get('lud') or 'Polanie'
        # Obsłuż zarówno "Polanie" jak i "polanie"
        plemie_key = plemie.lower() if plemie else 'polanie'
        miasto_startowe = PLEMIONA.get(plemie_key, PLEMIONA['polanie'])['miasto']
        
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
            self.logger.info(f"🤖 Model: {self.model_name} | Prompt: {len(prompt)} znaków | Historia: {len(self.historia)} wiadomości")
            self.logger.info(f"🤖 Model: {self.model_name} | Prompt: {len(prompt)} znaków | Historia: {len(self.historia)} wiadomości")
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            
            # Bez JSON Schema - problemy z Gemini 2.5 Flash
            # Polegamy na auto-naprawie w _parsuj_json()
            # Wywołaj model z timeoutem, aby uniknąć blokowania serwera
            response = self._call_model_with_timeout(
                [
                    {"role": "user", "parts": [system_prompt_z_lokacjami]},
                    {"role": "user", "parts": [prompt]}
                ],
                timeout=90  # Zwiększony dla Pro (wolniejszy niż Flash)
            )
            
            # DEBUGOWANIE: Zaloguj surowy response
            self.logger.info(f"📄 RAW response.text: {response.text[:1000]}")
            
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
            self.logger.error(f"❌ WYJĄTEK w rozpocznij_gre: {type(e).__name__}: {e}")
            import traceback
            self.logger.error(f"📄 Pełny traceback:\n{traceback.format_exc()}")
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
        
        # Generuj kontekst bestiariusza dla aktualnej lokacji
        lokacja_otoczenia = self._okresl_typ_lokacji(miasto_gracza, tekst_gracza)
        kontekst_bestiariusza = generuj_kontekst_bestiariusza_dla_ai(lokacja_otoczenia)
        
        # Pobierz aktualny HP przeciwników z sesji (jeśli są w walce)
        from flask import session
        przeciwnicy_hp_sesja = session.get('przeciwnicy_hp', {})
        kontekst_hp_przeciwnikow = ""
        if przeciwnicy_hp_sesja:
            kontekst_hp_przeciwnikow = "\n\n🎯 AKTUALNE HP PRZECIWNIKÓW W WALCE:\n"
            for klucz, dane in przeciwnicy_hp_sesja.items():
                imie = dane['imie']
                hp = dane['hp']
                hp_max = dane['hp_max']
                procent = int((hp / hp_max) * 100)
                kontekst_hp_przeciwnikow += f"- {imie}: {hp}/{hp_max} HP ({procent}%)\n"
            kontekst_hp_przeciwnikow += "\n⚔️ WYMAGANIA DLA WALKI:\n"
            kontekst_hp_przeciwnikow += "- W narracji NAPISZ: 'zadajesz X obrażeń [IMIĘ]' (np. 'zadajesz 15 obrażeń Szaremu Wilkowi')\n"
            kontekst_hp_przeciwnikow += "- W JSON 'uczestnicy' MUSISZ podać aktualne 'hp' dla każdego przeciwnika!\n"
            kontekst_hp_przeciwnikow += "- Przykład: {\"imie\": \"Szary Wilk\", \"typ\": \"bestia\", \"hp\": 38, \"hp_max\": 40}\n"
            kontekst_hp_przeciwnikow += "- Gdy przeciwnik atakuje gracza, odejmij HP od hp_gracza w JSON\n"
            kontekst_hp_przeciwnikow += "- Gdy HP przeciwnika spadnie do 0 → napisz że zginął i NIE dodawaj go do 'uczestnicy'\n"
        
        prompt = f"""{kontekst_stanu}
AKCJA GRACZA: {tekst_gracza}

Odpowiedz jako Mistrz Gry. Pamiętaj o formacie JSON! hp_gracza musi być liczbą bazującą na aktualnym HP ({aktualne_hp}).
Używaj TYLKO NPC i budynków z SYSTEMU LOKACJI podanego w kontekście!

{kontekst_bestiariusza}{kontekst_hp_przeciwnikow}

🔴 KRYTYCZNE - POLE "uczestnicy" 🔴
NIE WOLNO CI POMINĄĆ TEGO POLA! Pole "uczestnicy" MUSI być zawsze wypełnione poprawnie:

✅ Jeśli w narracji pojawiają się NPC (kupiec, kowal, kapłan, wojownik) → 
   "uczestnicy": [{{"imie": "Bogdan", "typ": "npc", "zawod": "Kowal"}}]

✅ Jeśli są wrogowie w walce → UŻYJ TYLKO przeciwników z BESTIARIUSZA powyżej! 
   "uczestnicy": [{{"imie": "Bandyta", "typ": "wrog", "hp_max": 45}}]

✅ Jeśli są bestie/potwory → UŻYJ TYLKO stworzeń z BESTIARIUSZA powyżej!
   "uczestnicy": [{{"imie": "Szary Wilk", "typ": "bestia", "hp_max": 40, "ikona": "🐺"}}]

❌ Tylko jeśli gracz jest CAŁKOWICIE SAM w pustym miejscu → "uczestnicy": []

PRZYKŁADY:
- Narrator mówi o kowalu Bogdanie → MUSISZ dodać {{"imie": "Bogdan", "typ": "npc", "zawod": "Kowal"}}
- Gracz rozmawia z kapłanem Żywisławem → MUSISZ dodać {{"imie": "Żywisław", "typ": "npc", "zawod": "Kapłan"}}
- Gracz spotyka wilka w lesie → MUSISZ użyć {{"imie": "Szary Wilk", "typ": "bestia", "hp_max": 40, "ikona": "🐺"}}
- Gracz sam w lesie → "uczestnicy": []

⚠️ NIGDY nie wymyślaj nowych przeciwników! Używaj TYLKO z listy BESTIARIUSZ powyżej!"""

        self.historia.append({"role": "user", "parts": [prompt]})
        
        import time
        try:
            start = time.time()
            game_log.log_gemini_request(len(prompt), len(self.historia), model=self.model_name)
            # Buduj kontekst z historią
            messages = [{"role": "user", "parts": [system_prompt_z_lokacjami]}]
            messages.extend(self.historia[-10:])  # Ostatnie 10 wiadomości
            
            # Bez JSON Schema - problemy z Gemini 2.5 Flash
            # Polegamy na auto-naprawie w _parsuj_json()
            # Wywołaj model z timeoutem, aby uniknąć blokowania serwera
            response = self._call_model_with_timeout(messages, timeout=60)  # Zwiększony dla Pro
            
            odpowiedz = self._parsuj_json(response.text)
            
            # DEBUG: Loguj uczestników
            if 'uczestnicy' in odpowiedz:
                self.logger.info(f"🔍 DEBUG - Liczba uczestników zwróconych przez Gemini: {len(odpowiedz['uczestnicy'])}")
                for i, u in enumerate(odpowiedz['uczestnicy']):
                    self.logger.info(f"  [{i+1}] {u.get('imie', 'BRAK IMIENIA')} (typ: {u.get('typ', 'BRAK')}, HP: {u.get('hp_max', 'BRAK')})")
            else:
                self.logger.warning("⚠️ DEBUG - Pole 'uczestnicy' NIE ISTNIEJE w odpowiedzi Gemini!")
            
            elapsed_ms = int((time.time() - start) * 1000)
            game_log.log_gemini_response(len(response.text), elapsed_ms, model=self.model_name, success=True)
            # Jeśli MG zwrócił komunikat o limicie -> spróbuj HF fallback
            narr = (odpowiedz.get('narracja') or '').lower() if isinstance(odpowiedz, dict) else ''
            if any(tok in narr for tok in ['429', 'quota', 'exceeded', 'przekroc', 'limit']):
                if self.hf_api_token and self.hf_model:
                    try:
                        hf_prompt = f"Jesteś Mistrzem Gry. Odpowiedź krótko po polsku na akcję gracza: {tekst_gracza}. Użyj stylu narratora."
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
        
        # FIX: Usuń podwójny {{ na początku (częsty błąd Gemini)
        tekst = tekst.strip()
        while tekst.startswith('{{'):
            self.logger.warning("⚠️ Auto-naprawa: usuwam podwójny '{{' na początku")
            tekst = tekst[1:].strip()
        
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
        
        # ZAWSZE loguj surowy tekst na początku (dla debugowania)
        self.logger.info(f"📄 Surowy tekst Gemini (pierwsze 1000 znaków): {tekst[:1000]}")
        
        # DEBUG: Sprawdź czy "uczestnicy" jest w surowym tekście
        if '"uczestnicy"' in tekst:
            self.logger.info("✅ Pole 'uczestnicy' ZNALEZIONE w surowym JSON")
        else:
            self.logger.warning("⚠️ Pole 'uczestnicy' NIE ZNALEZIONE w surowym JSON - Gemini go nie wygenerował!")
        
        # Znajdź JSON między { }
        start = tekst.find('{')
        end = tekst.rfind('}')
        if start != -1 and end != -1 and end > start:
            tekst = tekst[start:end+1].strip()
        
        try:
            wynik = json.loads(tekst)
            self.logger.info(f"✅ Parsowanie JSON OK, lokacja: {wynik.get('lokacja', 'brak')}")
            
            # WALIDACJA: Usuń pole "obrazenia" jeśli jest puste lub błędne
            if 'obrazenia' in wynik:
                obrazenia = wynik['obrazenia']
                # Usuń jeśli puste lub brak zadanych obrażeń
                if not obrazenia or (isinstance(obrazenia, dict) and not obrazenia.get('zadane')):
                    del wynik['obrazenia']
                    self.logger.info(f"🗑️ Usunięto puste pole 'obrazenia'")
            
            # WALIDACJA: Skróć za długie opcje
            if 'opcje' in wynik and isinstance(wynik['opcje'], list):
                opcje_poprawione = []
                for opcja in wynik['opcje']:
                    if len(opcja) > 70:
                        skrocona = opcja[:67] + '...'
                        self.logger.warning(f"⚠️ Skrócono opcję z {len(opcja)} do 70 znaków: {opcja[:30]}...")
                        opcje_poprawione.append(skrocona)
                    else:
                        opcje_poprawione.append(opcja)
                wynik['opcje'] = opcje_poprawione
            
            # WALIDACJA BESTIARIUSZA: Sprawdź czy przeciwnicy są z bestiariusza
            if 'uczestnicy' in wynik and isinstance(wynik['uczestnicy'], list):
                wynik['uczestnicy'] = self._waliduj_uczestnikow_bestiariusza(wynik['uczestnicy'])
            
            return wynik
        except json.JSONDecodeError as e:
            # Spróbuj z strict=False (ignoruje niepoprawne escape sequences)
            try:
                wynik = json.loads(tekst, strict=False)
                self.logger.warning(f"⚠️ JSON sparsowany z strict=False (niepoprawne escape sequences)")
                self.logger.info(f"✅ Parsowanie JSON OK, lokacja: {wynik.get('lokacja', 'brak')}")
                
                # Usuń puste pole obrazenia również tutaj
                if 'obrazenia' in wynik:
                    obrazenia = wynik['obrazenia']
                    if not obrazenia or (isinstance(obrazenia, dict) and not obrazenia.get('zadane')):
                        del wynik['obrazenia']
                        self.logger.info(f"🗑️ Usunięto puste pole 'obrazenia' (strict=False)")
                
                # Walidacja również tutaj
                if 'uczestnicy' in wynik and isinstance(wynik['uczestnicy'], list):
                    wynik['uczestnicy'] = self._waliduj_uczestnikow_bestiariusza(wynik['uczestnicy'])
                
                return wynik
            except Exception:
                pass  # Przejdź do agresywnej naprawy
                
            self.logger.error(f"❌ Błąd parsowania JSON: {e}")
            self.logger.error(f"📄 Tekst po ekstrakcji {{...}}: {tekst[:500]}")
            
            # AGRESYWNA AUTO-NAPRAWA: ekstrahuj wartości z częściowego JSON
            try:
                # Szukaj pól w tekście (nawet jeśli brakuje { })
                narracja_match = re.search(r'"narracja"\s*:\s*"([^"]*)"', tekst, re.DOTALL)
                lokacja_match = re.search(r'"lokacja"\s*:\s*"([^"]*)"', tekst)
                hp_match = re.search(r'"hp_gracza"\s*:\s*(\d+)', tekst)
                opcje_match = re.search(r'"opcje"\s*:\s*\[(.*?)\]', tekst, re.DOTALL)
                
                narracja = narracja_match.group(1) if narracja_match else "⚠️ Nie udało się przetworzyć odpowiedzi AI."
                lokacja = lokacja_match.group(1) if lokacja_match else "Nieznana"
                hp = int(hp_match.group(1)) if hp_match else 100
                
                opcje = []
                if opcje_match:
                    opcje_text = opcje_match.group(1)
                    opcje = [opt.strip(' "') for opt in opcje_text.split(',')]
                else:
                    opcje = ["Spróbuj ponownie", "Rozejrzyj się"]
                
                self.logger.warning(f"⚙️ Auto-naprawa JSON: wyekstrahowano pola z tekstu")
                return {
                    "narracja": narracja,
                    "lokacja": lokacja,
                    "hp_gracza": hp,
                    "towarzysze": [],
                    "opcje": opcje,
                    "quest_aktywny": None,
                    "walka": False,
                    "artefakty_zebrane": []
                }
            except Exception as repair_error:
                self.logger.error(f"❌ Auto-naprawa też zawiodła: {repair_error}")
                # Ostateczny fallback
                return {
                    "narracja": f"⚠️ Krytyczny błąd parsowania. Tekst: {tekst[:200]}...",
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
            if genai:
                self.model = genai.GenerativeModel(model_name)
            else:
                self.model = None
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
    
    def _waliduj_uczestnikow_bestiariusza(self, uczestnicy):
        """Waliduje uczestników - zastępuje nieprawidłowych przeciwników danymi z bestiariusza"""
        if not isinstance(uczestnicy, list):
            return []
        
        walidowani = []
        for uczestnik in uczestnicy:
            if not isinstance(uczestnik, dict):
                continue
            
            typ = uczestnik.get('typ', '')
            
            # NPC - bez walidacji (system lokacji się tym zajmuje)
            if typ == 'npc':
                walidowani.append(uczestnik)
                continue
            
            # Wrogowie i bestie - waliduj z bestiariusza
            if typ in ['wrog', 'bestia', 'boss']:
                imie = uczestnik.get('imie', '')
                
                # Spróbuj znaleźć w bestiariuszu - dokładnie lub częściowo
                dane_bestiariusza = pobierz_przeciwnika(imie)
                
                # Jeśli nie znaleziono dokładnie, szukaj częściowo (np. "Pierwszy Szary Wilk" -> "Szary Wilk")
                if not dane_bestiariusza:
                    from bestiary import pobierz_wszystkich_przeciwnikow
                    wszystkie_bestiariusze = pobierz_wszystkich_przeciwnikow()
                    for nazwa_bestiariusza in wszystkie_bestiariusze.keys():
                        if nazwa_bestiariusza.lower() in imie.lower():
                            dane_bestiariusza = pobierz_przeciwnika(nazwa_bestiariusza)
                            self.logger.info(f"✅ Częściowe dopasowanie: '{imie}' → '{nazwa_bestiariusza}'")
                            break
                
                if dane_bestiariusza:
                    # OK - użyj danych z bestiariusza, ale ZACHOWAJ oryginalne imie AI
                    self.logger.info(f"✅ Walidacja bestiariusza: '{imie}' zaakceptowany")
                    uczestnik_poprawiony = {
                        'imie': imie,  # ZACHOWAJ oryginalne imie AI (np. "Pierwszy Wilk")
                        'typ': dane_bestiariusza['typ'],
                        'hp_max': dane_bestiariusza['hp_max'],
                        'ikona': dane_bestiariusza.get('ikona', '⚔️')
                    }
                    # KRYTYCZNE: Zachowaj pole 'hp' i 'uid' z AI jeśli zostały zwrócone!
                    if 'hp' in uczestnik:
                        uczestnik_poprawiony['hp'] = uczestnik['hp']
                    if 'uid' in uczestnik:
                        uczestnik_poprawiony['uid'] = uczestnik['uid']
                    walidowani.append(uczestnik_poprawiony)
                else:
                    # BŁĄD - AI wymyślił przeciwnika spoza bestiariusza
                    self.logger.warning(f"⚠️ Walidacja bestiariusza: '{imie}' NIE ISTNIEJE w bestiariuszu! Usuwam.")
                    # Nie dodawaj do listy (usuń nieprawidłowego)
                    continue
            else:
                # Inny typ - przepuść bez zmian
                walidowani.append(uczestnik)
        
        return walidowani


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
