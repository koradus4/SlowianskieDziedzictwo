"""
System Lokacji - Słowiańskie Dziedzictwo
Deterministyczny system zapobiegający halucynacjom AI
"""

import random
import copy

# ============================================================================
# WARSTWA 1: DEFINICJE BUDYNKÓW
# ============================================================================

BUDYNKI_DEFINICJE = {
    "karczma": {
        "nazwa": "Karczma",
        "opis": "Tętniące życiem miejsce, gdzie spotykają się kupcy, wojownicy i wędrowcy. Zapach pieczeni miesza się z dymem z palenisk.",
        "funkcje": ["jedzenie", "nocleg", "plotki", "rekrutacja"]
    },
    "kuznia": {
        "nazwa": "Kuźnia",
        "opis": "Gorące palenisko i dźwięk młota uderzającego o kowadło. Kowal tworzy broń i zbroje dla najlepszych wojowników.",
        "funkcje": ["broń", "zbroje", "naprawa", "rekrutacja"]
    },
    "targ": {
        "nazwa": "Targ",
        "opis": "Ruchliwy plac handlowy pełen straganów. Handlarze oferują wszystko - od żywności po rzadkie przedmioty.",
        "funkcje": ["handel", "przedmioty", "plotki"]
    },
    "swiatynia": {
        "nazwa": "Świątynia",
        "opis": "Święte miejsce poświęcone słowiańskim bogom. Kapłani udzielają błogosławieństw i leczą chorych.",
        "funkcje": ["błogosławieństwa", "leczenie", "nauka", "rekrutacja"]
    },
    "ratusz": {
        "nazwa": "Ratusz",
        "opis": "Siedziba władz miejskich. Tu podejmowane są ważne decyzje i wydawane są rozkazy.",
        "funkcje": ["questy", "informacje", "polityka"]
    },
    "szpital": {
        "nazwa": "Szpital",
        "opis": "Miejsce leczenia ran i chorób. Zielarze i uzdrowiciele pomagają potrzebującym.",
        "funkcje": ["leczenie", "trucizny", "mikstury"]
    },
    "warsztat": {
        "nazwa": "Warsztat",
        "opis": "Pracownia rzemieślnika. Powstają tu narzędzia i wyposażenie podróżne.",
        "funkcje": ["narzędzia", "wyposażenie", "naprawa"]
    },
    "stajnia": {
        "nazwa": "Stajnia",
        "opis": "Zapachy siana i koni. Koński tabun gotowy do drogi.",
        "funkcje": ["konie", "wozy", "transport"]
    },
    "koszary": {
        "nazwa": "Koszary",
        "opis": "Miejsce treningu wojowników. Brzęk mieczy i okrzyki ćwiczących żołnierzy.",
        "funkcje": ["rekrutacja", "trening", "wojsko"]
    },
    "biblioteka": {
        "nazwa": "Biblioteka",
        "opis": "Zbiór wiedzy przodków. Stare zwoje i księgi kryją tajemnice dawnych czasów.",
        "funkcje": ["wiedza", "mapy", "historie", "nauka"]
    },
    "laznia": {
        "nazwa": "Łaźnia",
        "opis": "Gorące kąpiele i para. Miejsce odpoczynku i wymiany plotek.",
        "funkcje": ["odpoczynek", "plotki", "regeneracja"]
    },
    "mlyn": {
        "nazwa": "Młyn",
        "opis": "Koło młyńskie obraca się przy strumieniu. Młynarz wie wszystko o okolicy.",
        "funkcje": ["mąka", "zaopatrzenie", "plotki"]
    },
    "piekarnia": {
        "nazwa": "Piekarnia",
        "opis": "Zapach świeżego chleba rozchodzi się po okolicy. Piekarz oferuje prowiant na drogę.",
        "funkcje": ["prowiant", "żywność"]
    },
    "wiezienie": {
        "nazwa": "Więzienie",
        "opis": "Ciemne cele pod ziemią. Straże pilnują więźniów i przestępców.",
        "funkcje": ["informacje", "zwolnienie", "przesłuchania"]
    },
    "wieza_straznicza": {
        "nazwa": "Wieża Strażnicza",
        "opis": "Wysoka wieża z widokiem na okolicę. Strażnicy ostrzegają przed niebezpieczeństwem.",
        "funkcje": ["obserwacja", "ostrzeżenia", "obrona"]
    }
}

# ============================================================================
# WARSTWA 2: PLEMIONA (miasta + NPC)
# ============================================================================

PLEMIONA = {
    "polanie": {
        "miasto": "Gniezno",
        "opis": "Stolica Polan, gród Lecha. Potężne drewniane wały otaczają miasto, a w centrum wznosi się gród książęcy.",
        "budynki": ["karczma", "kuznia", "targ", "swiatynia", "ratusz", "szpital", "warsztat", "stajnia", "koszary", "biblioteka", "laznia", "mlyn", "piekarnia", "wiezienie", "wieza_straznicza"],
        "npc": [
            {"id": "gniezno_kowal_01", "imie": "Bogdan", "funkcja": "kowal", "lokalizacja": "kuznia", "cechy": "wysoki, muskularny, szczery", "koszt_rekrutacji": 100},
            {"id": "gniezno_kupiec_01", "imie": "Dobromir", "funkcja": "kupiec", "lokalizacja": "targ", "cechy": "przebiegły, gadatliwy, chciwy", "koszt_rekrutacji": 50},
            {"id": "gniezno_kaplan_01", "imie": "Żywisław", "funkcja": "kapłan", "lokalizacja": "swiatynia", "cechy": "mądry, spokojny, pobożny", "koszt_rekrutacji": 150},
            {"id": "gniezno_wojownik_01", "imie": "Boruta", "funkcja": "wojownik", "lokalizacja": "koszary", "cechy": "silny, odważny, lojalny", "koszt_rekrutacji": 120},
            {"id": "gniezno_uzdrowiciel_01", "imie": "Jaromira", "funkcja": "uzdrowicielka", "lokalizacja": "szpital", "cechy": "delikatna, mądra, troskliwa", "koszt_rekrutacji": 100},
            {"id": "gniezno_lowca_01", "imie": "Wlodzislaw", "funkcja": "łowca", "lokalizacja": "karczma", "cechy": "cichy, spostrzegawczy, samotnik", "koszt_rekrutacji": 80},
            {"id": "gniezno_rzemiesnik_01", "imie": "Przemysł", "funkcja": "rzemieślnik", "lokalizacja": "warsztat", "cechy": "zręczny, pracowity, cierpliwy", "koszt_rekrutacji": 70},
            {"id": "gniezno_straznik_01", "imie": "Bronisz", "funkcja": "strażnik", "lokalizacja": "wieza_straznicza", "cechy": "czujny, surowy, odpowiedzialny", "koszt_rekrutacji": 90},
            {"id": "gniezno_uczony_01", "imie": "Mszczuj", "funkcja": "uczony", "lokalizacja": "biblioteka", "cechy": "mądry, gadatliwy, roztargniony", "koszt_rekrutacji": 110},
            {"id": "gniezno_karczmarz_01", "imie": "Kazimierz", "funkcja": "karczmarz", "lokalizacja": "karczma", "cechy": "przyjacielski, plotkarz, dowcipny", "koszt_rekrutacji": 40},
            {"id": "gniezno_mag_01", "imie": "Radosław", "funkcja": "mag", "lokalizacja": "biblioteka", "cechy": "tajemniczy, potężny, samotny", "koszt_rekrutacji": 200},
            {"id": "gniezno_zielarka_01", "imie": "Dobrosława", "funkcja": "zielarka", "lokalizacja": "szpital", "cechy": "stara, mądra, łagodna", "koszt_rekrutacji": 85},
            {"id": "gniezno_lucznik_01", "imie": "Sambor", "funkcja": "łucznik", "lokalizacja": "koszary", "cechy": "precyzyjny, cierpliwy, spokojny", "koszt_rekrutacji": 95},
            {"id": "gniezno_kowal_02", "imie": "Wiesław", "funkcja": "kowal pomocnik", "lokalizacja": "kuznia", "cechy": "młody, utalentowany, ambitny", "koszt_rekrutacji": 60},
            {"id": "gniezno_wywiadowca_01", "imie": "Cieszym", "funkcja": "wywiadowca", "lokalizacja": "ratusz", "cechy": "przebiegły, cichy, podejrzliwy", "koszt_rekrutacji": 130}
        ]
    },
    
    "wislanie": {
        "miasto": "Kraków",
        "opis": "Gród Wiślan na Wzgórzu Wawelskim. Potężna twierdza góruje nad rzeką Wisłą.",
        "budynki": ["karczma", "kuznia", "targ", "swiatynia", "ratusz", "szpital", "warsztat", "stajnia", "koszary", "biblioteka", "laznia", "mlyn", "piekarnia", "wiezienie", "wieza_straznicza"],
        "npc": [
            {"id": "krakow_kowal_01", "imie": "Sędzisław", "funkcja": "kowal", "lokalizacja": "kuznia", "cechy": "doświadczony, surowy, perfekcjonista", "koszt_rekrutacji": 110},
            {"id": "krakow_kupiec_01", "imie": "Bogusław", "funkcja": "kupiec", "lokalizacja": "targ", "cechy": "bogaty, wpływowy, dyplomatyczny", "koszt_rekrutacji": 60},
            {"id": "krakow_kaplan_01", "imie": "Uniesław", "funkcja": "kapłan Peruna", "lokalizacja": "swiatynia", "cechy": "potężny, charyzmatyczny, surowy", "koszt_rekrutacji": 160},
            {"id": "krakow_wojownik_01", "imie": "Jarysław", "funkcja": "wojownik elitarny", "lokalizacja": "koszary", "cechy": "doświadczony, brutalny, skuteczny", "koszt_rekrutacji": 140},
            {"id": "krakow_uzdrowiciel_01", "imie": "Miłosława", "funkcja": "uzdrowicielka", "lokalizacja": "szpital", "cechy": "ciepła, empatyczna, utalentowana", "koszt_rekrutacji": 105},
            {"id": "krakow_lowca_01", "imie": "Radogost", "funkcja": "tropiciel", "lokalizacja": "karczma", "cechy": "wytrawny, nieufny, samodzielny", "koszt_rekrutacji": 85},
            {"id": "krakow_rzemiesnik_01", "imie": "Bogumił", "funkcja": "stolarz", "lokalizacja": "warsztat", "cechy": "perfekcjonista, spokojny, dokładny", "koszt_rekrutacji": 75},
            {"id": "krakow_straznik_01", "imie": "Światosław", "funkcja": "dowódca straży", "lokalizacja": "wieza_straznicza", "cechy": "doświadczony, twardy, sprawiedliwy", "koszt_rekrutacji": 100},
            {"id": "krakow_uczony_01", "imie": "Wisław", "funkcja": "kronikarz", "lokalizacja": "biblioteka", "cechy": "erudycyjny, pedantyczny, ciekawy", "koszt_rekrutacji": 115},
            {"id": "krakow_karczmarz_01", "imie": "Borzysław", "funkcja": "karczmarz", "lokalizacja": "karczma", "cechy": "wesoły, hojny, towarzyski", "koszt_rekrutacji": 45},
            {"id": "krakow_mag_01", "imie": "Niemysł", "funkcja": "czarodziej", "lokalizacja": "biblioteka", "cechy": "mroczny, potężny, tajemniczy", "koszt_rekrutacji": 210},
            {"id": "krakow_zielarka_01", "imie": "Sławomira", "funkcja": "zielarka", "lokalizacja": "szpital", "cechy": "wiedźma, surowa, skuteczna", "koszt_rekrutacji": 90},
            {"id": "krakow_lucznik_01", "imie": "Przybysław", "funkcja": "mistrz łuku", "lokalizacja": "koszary", "cechy": "legendarny, dumny, samotny", "koszt_rekrutacji": 105},
            {"id": "krakow_kowal_02", "imie": "Wojciech", "funkcja": "płatnerz", "lokalizacja": "kuznia", "cechy": "specjalista, drobiazgowy, skupiony", "koszt_rekrutacji": 90},
            {"id": "krakow_szpieg_01", "imie": "Chociemir", "funkcja": "szpieg", "lokalizacja": "ratusz", "cechy": "niewidoczny, sprytny, bezwzględny", "koszt_rekrutacji": 140}
        ]
    },
    
    "pomorzanie": {
        "miasto": "Wolin",
        "opis": "Potężne portowe miasto Pomorzan. Centrum handlu bałtyckiego, pełne wikingów i kupców.",
        "budynki": ["karczma", "kuznia", "targ", "swiatynia", "ratusz", "szpital", "warsztat", "stajnia", "koszary", "biblioteka", "laznia", "mlyn", "piekarnia", "wiezienie", "wieza_straznicza"],
        "npc": [
            {"id": "wolin_kowal_01", "imie": "Sobiesław", "funkcja": "kowal okrętowy", "lokalizacja": "kuznia", "cechy": "morski, wytrzymały, wynalaczy", "koszt_rekrutacji": 105},
            {"id": "wolin_kupiec_01", "imie": "Mściwoj", "funkcja": "handlarz morski", "lokalizacja": "targ", "cechy": "podróżnik, wielojęzyczny, chciwy", "koszt_rekrutacji": 70},
            {"id": "wolin_kaplan_01", "imie": "Świętobor", "funkcja": "kapłan Świętowita", "lokalizacja": "swiatynia", "cechy": "wizjoner, zagadkowy, potężny", "koszt_rekrutacji": 155},
            {"id": "wolin_wojownik_01", "imie": "Racibor", "funkcja": "wiking", "lokalizacja": "koszary", "cechy": "dziki, bezlitosny, odważny", "koszt_rekrutacji": 125},
            {"id": "wolin_uzdrowiciel_01", "imie": "Dąbrówka", "funkcja": "uzdrowicielka", "lokalizacja": "szpital", "cechy": "doświadczona, stanowcza, lojalna", "koszt_rekrutacji": 100},
            {"id": "wolin_zeglarz_01", "imie": "Gniewomir", "funkcja": "żeglarz", "lokalizacja": "karczma", "cechy": "doświadczony, opowieściowy, śmiały", "koszt_rekrutacji": 90},
            {"id": "wolin_szkutnik_01", "imie": "Boguchwał", "funkcja": "szkutnik", "lokalizacja": "warsztat", "cechy": "precyzyjny, morski, solidny", "koszt_rekrutacji": 80},
            {"id": "wolin_straznik_01", "imie": "Mieszko", "funkcja": "dowódca portu", "lokalizacja": "wieza_straznicza", "cechy": "czujny, twardy, doświadczony", "koszt_rekrutacji": 95},
            {"id": "wolin_uczony_01", "imie": "Wszebor", "funkcja": "skald", "lokalizacja": "biblioteka", "cechy": "poeta, opowieściowy, mądry", "koszt_rekrutacji": 100},
            {"id": "wolin_karczmarz_01", "imie": "Lubomysł", "funkcja": "karczmarz portowy", "lokalizacja": "karczma", "cechy": "gościnny, plotkarz, wesoły", "koszt_rekrutacji": 50},
            {"id": "wolin_mag_01", "imie": "Wołodysław", "funkcja": "wołchw", "lokalizacja": "swiatynia", "cechy": "starożytny, proroczy, mroczny", "koszt_rekrutacji": 205},
            {"id": "wolin_zielarka_01", "imie": "Bogna", "funkcja": "zielarka morska", "lokalizacja": "szpital", "cechy": "wiedźma, samotna, utalentowana", "koszt_rekrutacji": 88},
            {"id": "wolin_lucznik_01", "imie": "Świętopełk", "funkcja": "strzelec", "lokalizacja": "koszary", "cechy": "śmiertelny, cichy, lojalny", "koszt_rekrutacji": 98},
            {"id": "wolin_rybak_01", "imie": "Dobrogost", "funkcja": "rybak", "lokalizacja": "targ", "cechy": "prosty, silny, szczery", "koszt_rekrutacji": 40},
            {"id": "wolin_szpieg_01", "imie": "Czcibor", "funkcja": "wywiadowca", "lokalizacja": "ratusz", "cechy": "wielojęzyczny, przebiegły, bezwzględny", "koszt_rekrutacji": 135}
        ]
    },
    
    "mazowszanie": {
        "miasto": "Płock",
        "opis": "Gród Mazowszan na stromym brzegu Wisły. Ważny punkt strategiczny i handlowy.",
        "budynki": ["karczma", "kuznia", "targ", "swiatynia", "ratusz", "szpital", "warsztat", "stajnia", "koszary", "biblioteka", "laznia", "mlyn", "piekarnia", "wiezienie", "wieza_straznicza"],
        "npc": [
            {"id": "plock_kowal_01", "imie": "Budzisław", "funkcja": "kowal", "lokalizacja": "kuznia", "cechy": "tradycjonalista, solidny, nieufny", "koszt_rekrutacji": 100},
            {"id": "plock_kupiec_01", "imie": "Czcibogdan", "funkcja": "kupiec rzeczny", "lokalizacja": "targ", "cechy": "przebiegły, wyrachowany, bogaty", "koszt_rekrutacji": 55},
            {"id": "plock_kaplan_01", "imie": "Mstysław", "funkcja": "kapłan Welesa", "lokalizacja": "swiatynia", "cechy": "mądry, skryty, proroczy", "koszt_rekrutacji": 150},
            {"id": "plock_wojownik_01", "imie": "Grzymisław", "funkcja": "drużynnik", "lokalizacja": "koszary", "cechy": "wierny, silny, doświadczony", "koszt_rekrutacji": 115},
            {"id": "plock_uzdrowiciel_01", "imie": "Dobroniega", "funkcja": "uzdrowicielka", "lokalizacja": "szpital", "cechy": "matczyna, cierpliwa, utalentowana", "koszt_rekrutacji": 98},
            {"id": "plock_lowca_01", "imie": "Lesław", "funkcja": "leśniczy", "lokalizacja": "karczma", "cechy": "dziki, wolny, spostrzegawczy", "koszt_rekrutacji": 82},
            {"id": "plock_rzemiesnik_01", "imie": "Chrościsław", "funkcja": "kowal drewna", "lokalizacja": "warsztat", "cechy": "skromny, pracowity, uczciwy", "koszt_rekrutacji": 65},
            {"id": "plock_straznik_01", "imie": "Stoisław", "funkcja": "strażnik bramy", "lokalizacja": "wieza_straznicza", "cechy": "niezłomny, lojalny, czujny", "koszt_rekrutacji": 92},
            {"id": "plock_uczony_01", "imie": "Budzimir", "funkcja": "kronikarz", "lokalizacja": "biblioteka", "cechy": "starszy, mądry, cierpliwy", "koszt_rekrutacji": 108},
            {"id": "plock_karczmarz_01", "imie": "Żegota", "funkcja": "karczmarz", "lokalizacja": "karczma", "cechy": "rozmowny, pomocny, wesołkowaty", "koszt_rekrutacji": 42},
            {"id": "plock_druid_01", "imie": "Chwalibóg", "funkcja": "druid", "lokalizacja": "swiatynia", "cechy": "starożytny, mądry, naturalistyczny", "koszt_rekrutacji": 195},
            {"id": "plock_zielarka_01", "imie": "Miłosława", "funkcja": "ziołoleczka", "lokalizacja": "szpital", "cechy": "tradycyjna, dobra, skuteczna", "koszt_rekrutacji": 86},
            {"id": "plock_lucznik_01", "imie": "Jarosław", "funkcja": "łowczy", "lokalizacja": "koszary", "cechy": "precyzyjny, cierpliwy, samotniczy", "koszt_rekrutacji": 93},
            {"id": "plock_mlynarz_01", "imie": "Dobiesław", "funkcja": "młynarz", "lokalizacja": "mlyn", "cechy": "plotkarz, pomocny, poniżej", "koszt_rekrutacji": 38},
            {"id": "plock_wywiadowca_01", "imie": "Ścibor", "funkcja": "tropiciel", "lokalizacja": "ratusz", "cechy": "cichy, skuteczny, lojalny", "koszt_rekrutacji": 128}
        ]
    },
    
    "slezanie": {
        "miasto": "Ślęża",
        "opis": "Święte miejsce Ślężan u stóp Góry Ślęży. Tajemnicze sanktuarium pogańskie.",
        "budynki": ["karczma", "kuznia", "targ", "swiatynia", "ratusz", "szpital", "warsztat", "stajnia", "koszary", "biblioteka", "laznia", "mlyn", "piekarnia", "wiezienie", "wieza_straznicza"],
        "npc": [
            {"id": "sleza_kowal_01", "imie": "Sędomir", "funkcja": "kowal rytualny", "lokalizacja": "kuznia", "cechy": "mistyczny, utalentowany, skryty", "koszt_rekrutacji": 108},
            {"id": "sleza_kupiec_01", "imie": "Chwalimir", "funkcja": "kupiec", "lokalizacja": "targ", "cechy": "dyskretny, wykształcony, bogaty", "koszt_rekrutacji": 58},
            {"id": "sleza_kaplan_01", "imie": "Świętosław", "funkcja": "najwyższy kapłan", "lokalizacja": "swiatynia", "cechy": "charyzmatyczny, potężny, surowy", "koszt_rekrutacji": 170},
            {"id": "sleza_wojownik_01", "imie": "Krzesisław", "funkcja": "strażnik świątyni", "lokalizacja": "koszary", "cechy": "fanatyczny, bezwzględny, silny", "koszt_rekrutacji": 130},
            {"id": "sleza_uzdrowiciel_01", "imie": "Włodzimira", "funkcja": "kapłanka-uzdrowicielka", "lokalizacja": "szpital", "cechy": "święta, uzdolniona, mistyczna", "koszt_rekrutacji": 110},
            {"id": "sleza_lowca_01", "imie": "Radogost", "funkcja": "górski tropiciel", "lokalizacja": "karczma", "cechy": "dziki, samodzielny, nieustraszony", "koszt_rekrutacji": 87},
            {"id": "sleza_rzemiesnik_01", "imie": "Boguchwal", "funkcja": "kamieniarz", "lokalizacja": "warsztat", "cechy": "solidny, cierpliwy, precyzyjny", "koszt_rekrutacji": 72},
            {"id": "sleza_straznik_01", "imie": "Wnędzysław", "funkcja": "dowódca", "lokalizacja": "wieza_straznicza", "cechy": "surowy, wierny, doświadczony", "koszt_rekrutacji": 97},
            {"id": "sleza_uczony_01", "imie": "Radosław", "funkcja": "mistyk", "lokalizacja": "biblioteka", "cechy": "wizjoner, tajemniczy, mądry", "koszt_rekrutacji": 120},
            {"id": "sleza_karczmarz_01", "imie": "Cieszybor", "funkcja": "karczmarz", "lokalizacja": "karczma", "cechy": "cichy, obserwujący, mądry", "koszt_rekrutacji": 48},
            {"id": "sleza_mag_01", "imie": "Przemysław", "funkcja": "mag góry", "lokalizacja": "swiatynia", "cechy": "mroczny, potężny, samotny", "koszt_rekrutacji": 220},
            {"id": "sleza_zielarka_01", "imie": "Świętosława", "funkcja": "wiedźma ziół", "lokalizacja": "szpital", "cechy": "starożytna, mądra, surowa", "koszt_rekrutacji": 92},
            {"id": "sleza_lucznik_01", "imie": "Warcisław", "funkcja": "strażnik", "lokalizacja": "koszary", "cechy": "czujny, precyzyjny, surowy", "koszt_rekrutacji": 100},
            {"id": "sleza_prorok_01", "imie": "Dobromysł", "funkcja": "prorok", "lokalizacja": "swiatynia", "cechy": "wizjoner, szalony, prawdomówny", "koszt_rekrutacji": 150},
            {"id": "sleza_wywiadowca_01", "imie": "Wyszesław", "funkcja": "szpieg", "lokalizacja": "ratusz", "cechy": "niewidoczny, bezwzględny, lojalny", "koszt_rekrutacji": 132}
        ]
    }
}

# ============================================================================
# WARSTWA 3: LOKACJE STANDARDOWE (występują przy każdym mieście)
# ============================================================================

LOKACJE_STANDARDOWE = {
    "las": {
        "typ": "las",
        "ikona": "🌲",
        "nazwa": "Las",
        "opis": "Gęsty bór pełen zwierzyny i tajemnic.",
        "niebezpieczenstwo": "średnie"
    },
    "rzeka": {
        "typ": "rzeka",
        "ikona": "🌊",
        "nazwa": "Rzeka",
        "opis": "Płynąca woda, ryby i przeprawy.",
        "niebezpieczenstwo": "niskie"
    },
    "polana": {
        "typ": "polana",
        "ikona": "🌾",
        "nazwa": "Polana",
        "opis": "Otwarta przestrzeń, spokojne miejsce.",
        "niebezpieczenstwo": "niskie"
    },
    "droga": {
        "typ": "droga",
        "ikona": "🛤️",
        "nazwa": "Droga Handlowa",
        "opis": "Trakt łączący miasta, handlarze i rozbójnicy.",
        "niebezpieczenstwo": "średnie"
    },
    "cmentarz": {
        "typ": "cmentarz",
        "ikona": "💀",
        "nazwa": "Cmentarz Przodków",
        "opis": "Kurhany i mogiły, duchy krążą nocą.",
        "niebezpieczenstwo": "wysokie"
    },
    "ruiny": {
        "typ": "ruiny",
        "ikona": "🏚️",
        "nazwa": "Stare Ruiny",
        "opis": "Pozostałości dawnego grodu, tajemnice przeszłości.",
        "niebezpieczenstwo": "wysokie"
    },
    "most": {
        "typ": "most",
        "ikona": "🌉",
        "nazwa": "Most",
        "opis": "Przeprawa przez rzekę, miejsce spotkań.",
        "niebezpieczenstwo": "średnie"
    },
    "wioska": {
        "typ": "wioska",
        "ikona": "🏘️",
        "nazwa": "Wieś Okoliczna",
        "opis": "Mała osada chłopów, spokój i plotki.",
        "niebezpieczenstwo": "niskie"
    },
    "jaskinia": {
        "typ": "jaskinia",
        "ikona": "⛰️",
        "nazwa": "Jaskinia",
        "opis": "Ciemna grota w skale, niebezpieczne tajemnice.",
        "niebezpieczenstwo": "wysokie"
    },
    "oboz": {
        "typ": "oboz",
        "ikona": "⛺",
        "nazwa": "Obóz Obronny",
        "opis": "Tymczasowe umocnienie, żołnierze i strażnicy.",
        "niebezpieczenstwo": "niskie"
    }
}

# ============================================================================
# WARSTWA 4: LOKACJE SPECJALNE (unikalne dla konkretnych miast)
# ============================================================================

LOKACJE_SPECJALNE = {
    "bagna_goplo": {
        "typ": "bagna",
        "ikona": "🌫️",
        "nazwa": "Bagna koło Gopła",
        "opis": "Mgliste bagna pełne niebezpieczeństw. Strzygi i utopce.",
        "pobliska_lokacja": "Gniezno",
        "niebezpieczenstwo": "bardzo wysokie"
    },
    "gory_karpaty": {
        "typ": "gory",
        "ikona": "🏔️",
        "nazwa": "Karpaty",
        "opis": "Wysokie szczyty, górali i starzy bogowie.",
        "pobliska_lokacja": "Kraków",
        "niebezpieczenstwo": "średnie"
    },
    "jaskinia_smoka": {
        "typ": "jaskinia",
        "ikona": "🐉",
        "nazwa": "Jaskinia Smoka Wawelskiego",
        "opis": "Głęboka jaskinia pod Wawelem. Podobno mieszkał tu smok...",
        "pobliska_lokacja": "Kraków",
        "niebezpieczenstwo": "ekstremalne"
    },
    "morze_baltyckie": {
        "typ": "morze",
        "ikona": "🌊",
        "nazwa": "Morze Bałtyckie",
        "opis": "Zimne wody, wikingowie i handel morski.",
        "pobliska_lokacja": "Wolin",
        "niebezpieczenstwo": "wysokie"
    },
    "ruiny_wichlina": {
        "typ": "ruiny",
        "ikona": "🏛️",
        "nazwa": "Ruiny Wichlina",
        "opis": "Starożytne grodzisko, duchy przeszłości.",
        "pobliska_lokacja": "Wolin",
        "niebezpieczenstwo": "wysokie"
    },
    "droga_bursztynowa": {
        "typ": "droga",
        "ikona": "💎",
        "nazwa": "Szlak Bursztynowy",
        "opis": "Starożytna droga handlowa łącząca Bałtyk z Rzymem.",
        "pobliska_lokacja": "Wolin",
        "niebezpieczenstwo": "średnie"
    },
    "gora_sleza": {
        "typ": "gora",
        "ikona": "⛰️",
        "nazwa": "Góra Ślęża",
        "opis": "Święta góra, miejsce mocy i pogańskich rytów.",
        "pobliska_lokacja": "Ślęża",
        "niebezpieczenstwo": "bardzo wysokie"
    }
}

# Backwards compatibility - łączy stare lokacje
LOKACJE_POMOCNICZE = LOKACJE_SPECJALNE

# ============================================================================
# WARSTWA 4: MAPA PODRÓŻY
# ============================================================================

MAPA_PODROZY = {
    ("Gniezno", "Kraków"): {
        "dystans_km": 280,
        "czas_dni": 4,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["las", "droga", "wieś"]
    },
    ("Gniezno", "Wolin"): {
        "dystans_km": 320,
        "czas_dni": 5,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["las", "droga", "rzeka"]
    },
    ("Gniezno", "Płock"): {
        "dystans_km": 120,
        "czas_dni": 2,
        "trudnosc": "łatwa",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "wieś"]
    },
    ("Gniezno", "Ślęża"): {
        "dystans_km": 230,
        "czas_dni": 3,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["las", "droga", "góry"]
    },
    ("Kraków", "Wolin"): {
        "dystans_km": 520,
        "czas_dni": 7,
        "trudnosc": "trudna",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "las", "rzeka"]
    },
    ("Kraków", "Płock"): {
        "dystans_km": 350,
        "czas_dni": 5,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "wieś", "rzeka"]
    },
    ("Kraków", "Ślęża"): {
        "dystans_km": 180,
        "czas_dni": 3,
        "trudnosc": "łatwa",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "góry"]
    },
    ("Wolin", "Płock"): {
        "dystans_km": 380,
        "czas_dni": 5,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "las", "rzeka"]
    },
    ("Wolin", "Ślęża"): {
        "dystans_km": 450,
        "czas_dni": 6,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "las"]
    },
    ("Płock", "Ślęża"): {
        "dystans_km": 310,
        "czas_dni": 4,
        "trudnosc": "średnia",
        "szansa_eventu": 1.0,
        "przejscia": ["droga", "wieś", "las"]
    }
}

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def pobierz_lokacje_gracza(lokalizacja_nazwa):
    """Zwraca pełne dane o lokalizacji gracza (miasto + budynki + NPC)"""
    for plemie_key, plemie_data in PLEMIONA.items():
        if plemie_data["miasto"] == lokalizacja_nazwa:
            return {
                "miasto": plemie_data["miasto"],
                "plemie": plemie_key,
                "opis": plemie_data["opis"],
                "budynki": {
                    typ: BUDYNKI_DEFINICJE[typ] 
                    for typ in plemie_data["budynki"]
                },
                "npc_dostepni": plemie_data["npc"]
            }
    
    # Jeśli to lokacja pomocnicza
    if lokalizacja_nazwa in LOKACJE_POMOCNICZE:
        return {
            "lokacja": lokalizacja_nazwa,
            "dane": LOKACJE_POMOCNICZE[lokalizacja_nazwa]
        }
    
    # Domyślnie Gniezno
    return pobierz_lokacje_gracza("Gniezno")


def pobierz_npc_w_lokalizacji(miasto, budynek=None):
    """Zwraca listę NPC w danym mieście/budynku"""
    for plemie_data in PLEMIONA.values():
        if plemie_data["miasto"] == miasto:
            if budynek:
                return [
                    npc for npc in plemie_data["npc"] 
                    if npc["lokalizacja"] == budynek
                ]
            return plemie_data["npc"]
    return []


def oblicz_podróż(start, cel):
    """Oblicza dane podróży i czy wystąpi event"""
    klucz = (start, cel)
    klucz_odwrotny = (cel, start)
    
    if klucz in MAPA_PODROZY:
        dane = MAPA_PODROZY[klucz].copy()
    elif klucz_odwrotny in MAPA_PODROZY:
        dane = MAPA_PODROZY[klucz_odwrotny].copy()
    else:
        # Domyślne wartości dla nieznanych tras
        return {
            "dystans_km": 200,
            "czas_dni": 3,
            "trudnosc": "średnia",
            "szansa_eventu": 1.0,
            "przejscia": ["droga"],
            "wystapi_event": random.random() < 1.0
        }
    
    # Ustal czy wystąpi event
    dane["wystapi_event"] = random.random() < dane["szansa_eventu"]
    
    return dane


def generuj_event_podrozy(dystans_km):
    """Generuje losowy event na podstawie dystansu"""
    eventy = [
        {
            "typ": "spotkanie",
            "opis": "Spotkacie wędrownych kupców oferujących towary",
            "opcje": ["Handluj", "Porozmawiaj", "Idź dalej"]
        },
        {
            "typ": "napad",
            "opis": "Bandyci zastawili zasadzkę na drodze!",
            "opcje": ["Walcz", "Negocjuj", "Uciekaj"]
        },
        {
            "typ": "zwierzeta",
            "opis": "Wataha wilków blokuje drogę",
            "opcje": ["Walcz", "Płosz", "Obejdź"]
        },
        {
            "typ": "odkrycie",
            "opis": "Znajdujecie ukrytą jaskinię ze śladami dawnego obozu",
            "opcje": ["Zbadaj", "Idź dalej", "Obozuj tutaj"]
        },
        {
            "typ": "pomoc",
            "opis": "Raniony podróżny prosi o pomoc",
            "opcje": ["Pomóż", "Zignoruj", "Przesłuchaj"]
        },
        {
            "typ": "pogoda",
            "opis": "Nadciąga gwałtowna burza",
            "opcje": ["Szukaj schronienia", "Idź dalej", "Rozpal obóz"]
        }
    ]
    
    # Większy dystans = większa szansa na niebezpieczne eventy
    if dystans_km > 200:
        return random.choice(eventy)
    elif dystans_km > 100:
        return random.choice(eventy[:4])
    else:
        return random.choice(eventy[:3])


def pobierz_budynek(miasto, typ_budynku):
    """Zwraca dane konkretnego budynku w mieście"""
    for plemie_data in PLEMIONA.values():
        if plemie_data["miasto"] == miasto:
            if typ_budynku in plemie_data["budynki"]:
                budynek_def = BUDYNKI_DEFINICJE[typ_budynku].copy()
                # Dodaj NPC w tym budynku
                budynek_def["npc"] = [
                    npc for npc in plemie_data["npc"]
                    if npc["lokalizacja"] == typ_budynku
                ]
                return budynek_def
    return None


def znajdz_npc_po_id(npc_id):
    """Wyszukuje NPC po unikalnym ID"""
    for plemie_data in PLEMIONA.values():
        for npc in plemie_data["npc"]:
            if npc["id"] == npc_id:
                return npc.copy()
    return None


def rekrutuj_npc(npc_id):
    """Przekształca szablon NPC w pełnego towarzysza z HP i statami"""
    npc_szablon = znajdz_npc_po_id(npc_id)
    if not npc_szablon:
        return None
    
    # Przekształć w pełnego towarzysza
    towarzysz = npc_szablon.copy()
    
    # Dodaj staty w zależności od funkcji
    funkcja = npc_szablon["funkcja"].lower()
    
    if "wojownik" in funkcja or "wiking" in funkcja or "drużynnik" in funkcja:
        towarzysz["hp"] = 30
        towarzysz["hp_max"] = 30
        towarzysz["atak"] = 18
        towarzysz["obrona"] = 14
        towarzysz["ekwipunek"] = ["Miecz", "Tarcza", "Skórzana zbroja"]
    elif "kowal" in funkcja:
        towarzysz["hp"] = 28
        towarzysz["hp_max"] = 28
        towarzysz["atak"] = 15
        towarzysz["obrona"] = 12
        towarzysz["ekwipunek"] = ["Młot", "Skórzany fartuch"]
    elif "mag" in funkcja or "czarodziej" in funkcja or "druid" in funkcja or "wołchw" in funkcja:
        towarzysz["hp"] = 20
        towarzysz["hp_max"] = 20
        towarzysz["atak"] = 25
        towarzysz["obrona"] = 8
        towarzysz["ekwipunek"] = ["Różdżka", "Księga zaklęć", "Mikstury"]
    elif "kaplan" in funkcja or "kapłanka" in funkcja:
        towarzysz["hp"] = 24
        towarzysz["hp_max"] = 24
        towarzysz["atak"] = 12
        towarzysz["obrona"] = 10
        towarzysz["ekwipunek"] = ["Laska", "Święte symbole", "Mikstury lecznicze"]
    elif "uzdrowiciel" in funkcja or "zielarka" in funkcja:
        towarzysz["hp"] = 22
        towarzysz["hp_max"] = 22
        towarzysz["atak"] = 8
        towarzysz["obrona"] = 8
        towarzysz["ekwipunek"] = ["Zioła", "Bandaże", "Mikstury"]
    elif "łucznik" in funkcja or "łowca" in funkcja or "łowczy" in funkcja or "strzelec" in funkcja:
        towarzysz["hp"] = 26
        towarzysz["hp_max"] = 26
        towarzysz["atak"] = 16
        towarzysz["obrona"] = 10
        towarzysz["ekwipunek"] = ["Łuk", "Strzały", "Nóż"]
    elif "szpieg" in funkcja or "wywiadowca" in funkcja or "tropiciel" in funkcja:
        towarzysz["hp"] = 24
        towarzysz["hp_max"] = 24
        towarzysz["atak"] = 14
        towarzysz["obrona"] = 12
        towarzysz["ekwipunek"] = ["Sztylet", "Płaszcz", "Narzędzia"]
    else:
        # Domyślne dla innych (kupcy, rzemieślnicy, etc.)
        towarzysz["hp"] = 25
        towarzysz["hp_max"] = 25
        towarzysz["atak"] = 10
        towarzysz["obrona"] = 10
        towarzysz["ekwipunek"] = ["Nóż", "Sakwa"]
    
    return towarzysz


def pobierz_wszystkie_miasta():
    """Zwraca listę wszystkich miast"""
    return [plemie_data["miasto"] for plemie_data in PLEMIONA.values()]


def pobierz_info_miasta(miasto):
    """Zwraca szczegółowe info o mieście"""
    for plemie_key, plemie_data in PLEMIONA.items():
        if plemie_data["miasto"] == miasto:
            return {
                "nazwa": miasto,
                "plemie": plemie_key,
                "opis": plemie_data["opis"],
                "liczba_budynkow": len(plemie_data["budynki"]),
                "liczba_npc": len(plemie_data["npc"])
            }
    return None


def pobierz_podpowiedzi_dla_miasta(miasto):
    """Zwraca podpowiedzi (budynki + lokacje) dla danego miasta
    
    Returns:
        dict: {
            "budynki": [{nazwa, ikona, opis, funkcje}, ...],
            "lokacje_standardowe": [{nazwa, ikona, opis, niebezpieczenstwo}, ...],
            "lokacje_specjalne": [{nazwa, ikona, opis, niebezpieczenstwo}, ...]
        }
    """
    # Pobierz budynki miasta
    budynki = []
    for plemie_data in PLEMIONA.values():
        if plemie_data["miasto"] == miasto:
            for budynek_id in plemie_data["budynki"]:
                if budynek_id in BUDYNKI_DEFINICJE:
                    budynek = BUDYNKI_DEFINICJE[budynek_id].copy()
                    budynek["id"] = budynek_id
                    # Dodaj ikony dla budynków
                    ikony_budynkow = {
                        "karczma": "🍺", "kuznia": "🔨", "targ": "🛒", "swiatynia": "⛪",
                        "ratusz": "🏛️", "szpital": "⚕️", "warsztat": "🔧", "stajnia": "🐴",
                        "koszary": "⚔️", "biblioteka": "📚", "laznia": "🛁", "mlyn": "⚙️",
                        "piekarnia": "🍞", "wiezienie": "🔒", "wieza_straznicza": "🗼"
                    }
                    budynek["ikona"] = ikony_budynkow.get(budynek_id, "🏢")
                    budynki.append(budynek)
            break
    
    # Lokacje standardowe (10 dla każdego miasta)
    lokacje_std = [
        {
            "id": lok_id,
            "nazwa": lok["nazwa"],
            "ikona": lok["ikona"],
            "opis": lok["opis"],
            "typ": lok["typ"],
            "niebezpieczenstwo": lok["niebezpieczenstwo"]
        }
        for lok_id, lok in LOKACJE_STANDARDOWE.items()
    ]
    
    # Lokacje specjalne (tylko dla tego miasta)
    lokacje_spec = [
        {
            "id": lok_id,
            "nazwa": lok["nazwa"],
            "ikona": lok["ikona"],
            "opis": lok["opis"],
            "typ": lok["typ"],
            "niebezpieczenstwo": lok["niebezpieczenstwo"]
        }
        for lok_id, lok in LOKACJE_SPECJALNE.items()
        if lok.get("pobliska_lokacja") == miasto
    ]
    
    return {
        "budynki": budynki,
        "lokacje_standardowe": lokacje_std,
        "lokacje_specjalne": lokacje_spec
    }


# Test funkcji (można uruchomić ten plik bezpośrednio)
if __name__ == "__main__":
    print("=== TEST SYSTEMU LOKACJI ===\n")
    
    # Test 1: Pobierz dane Gniezna
    print("1. Pobieranie lokacji Gniezno:")
    gniezno = pobierz_lokacje_gracza("Gniezno")
    print(f"   Miasto: {gniezno['miasto']}")
    print(f"   Liczba budynków: {len(gniezno['budynki'])}")
    print(f"   Liczba NPC: {len(gniezno['npc_dostepni'])}\n")
    
    # Test 2: Znajdź NPC
    print("2. Wyszukiwanie NPC 'gniezno_kowal_01':")
    npc = znajdz_npc_po_id("gniezno_kowal_01")
    print(f"   Imię: {npc['imie']}, Funkcja: {npc['funkcja']}\n")
    
    # Test 3: Rekrutacja
    print("3. Rekrutacja NPC:")
    towarzysz = rekrutuj_npc("gniezno_kowal_01")
    print(f"   {towarzysz['imie']} - HP: {towarzysz['hp']}, Atak: {towarzysz['atak']}\n")
    
    # Test 4: Oblicz podróż
    print("4. Podróż Gniezno → Kraków:")
    podroz = oblicz_podróż("Gniezno", "Kraków")
    print(f"   Dystans: {podroz['dystans_km']} km, Czas: {podroz['czas_dni']} dni")
    print(f"   Event: {'TAK' if podroz['wystapi_event'] else 'NIE'}\n")
    
    # Test 5: Generuj event
    if podroz['wystapi_event']:
        print("5. Generowanie eventu podróży:")
        event = generuj_event_podrozy(podroz['dystans_km'])
        print(f"   Typ: {event['typ']}")
        print(f"   Opis: {event['opis']}")
        print(f"   Opcje: {', '.join(event['opcje'])}\n")
    
    print("=== TESTY ZAKOŃCZONE ===")


# ============================================================================
# INTEGRACJA Z BESTIARIUSZEM
# ============================================================================

def pobierz_przeciwnikow_lokacji(miasto):
    """
    Zwraca listę przeciwników dostępnych w danej lokacji.
    Funkcja pomocnicza dla integracji z bestiary.py
    
    Args:
        miasto: Nazwa miasta (np. "Gniezno", "Kraków")
    
    Returns:
        Lista typów lokacji (np. ["wioska", "las", "droga"])
    """
    # Każde miasto ma swoje lokalne otoczenie
    lokacje_bazowe = ["wioska", "droga"]  # Każde miasto
    
    # Specyficzne lokacje dla poszczególnych miast
    specjalne = {
        "Gniezno": ["las"],
        "Kraków": ["gory"],
        "Ślęża": ["gory", "swiatynia"],
        "Płock": ["rzeka", "las"],
        "Wolin": ["rzeka", "most"]
    }
    
    return lokacje_bazowe + specjalne.get(miasto, [])

