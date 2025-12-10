"""
Bestiariusz - System Przeciwników
Słowiańskie Dziedzictwo

Deterministyczny system przeciwników zapobiegający halucynacjom AI.
Każdy przeciwnik ma predefiniowane statystyki i lokacje występowania.
"""

# ============================================================================
# POZIOMY TRUDNOŚCI
# ============================================================================

POZIOMY_TRUDNOSCI = {
    "slaby": {
        "hp_range": (20, 30),
        "exp_range": (10, 20),
        "miecze": "⚔️⚔️⚔️"
    },
    "sredni": {
        "hp_range": (40, 60),
        "exp_range": (25, 40),
        "miecze": "⚔️⚔️⚔️⚔️"
    },
    "silny": {
        "hp_range": (70, 90),
        "exp_range": (50, 70),
        "miecze": "⚔️⚔️⚔️⚔️⚔️"
    },
    "bardzo_silny": {
        "hp_range": (100, 120),
        "exp_range": (80, 100),
        "miecze": "⚔️⚔️⚔️⚔️⚔️⚔️"
    },
    "legendarny": {
        "hp_range": (150, 250),
        "exp_range": (120, 200),
        "miecze": "💀 GROŹNY"
    }
}

# ============================================================================
# WROGOWIE (LUDZIE)
# ============================================================================

WROGOWIE = {
    "zbir": {
        "id": "wrog_zbir",
        "nazwa": "Zbir",
        "typ": "wrog",
        "hp_max": 25,
        "ikona": "⚔️",
        "opis": "Pijany awanturnik z karczmy, nie stanowi większego zagrożenia.",
        "poziom_trudnosci": "slaby",
        "lokacje_glowne": ["karczma", "wioska"],
        "lokacje_rzadkie": ["droga"],
        "slabosci": [],
        "specjalne_ataki": ["cios butelką"],
        "statystyki": {
            "atak": 8,
            "obrona": 5,
            "szybkosc": 10
        },
        "loot": ["garść miedzianych monet", "butelka miodu pitnego"],
        "exp": 15
    },
    
    "bandyta": {
        "id": "wrog_bandyta",
        "nazwa": "Bandyta",
        "typ": "wrog",
        "hp_max": 45,
        "ikona": "⚔️",
        "opis": "Rozbójnik grasujący na traktach. Uzbrojony w miecz i skórzaną zbroję.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["droga", "most", "las"],
        "lokacje_rzadkie": ["gory", "wioska"],
        "slabosci": [],
        "specjalne_ataki": ["szybki atak z zaskoczenia"],
        "statystyki": {
            "atak": 15,
            "obrona": 12,
            "szybkosc": 16
        },
        "loot": ["miecz", "10-20 złotych", "skórzana zbroja"],
        "exp": 30
    },
    
    "rozbojnik": {
        "id": "wrog_rozbojnik",
        "nazwa": "Rozbójnik",
        "typ": "wrog",
        "hp_max": 55,
        "ikona": "⚔️",
        "opis": "Doświadczony zbój z bandą. Znany z okrucieństwa i przebiegłości.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["las", "droga", "przeleczy"],
        "lokacje_rzadkie": ["ruiny", "oboz"],
        "slabosci": [],
        "specjalne_ataki": ["cios ogłuszający", "ukrycie w cieniu"],
        "statystyki": {
            "atak": 18,
            "obrona": 14,
            "szybkosc": 18
        },
        "loot": ["topór bojowy", "20-35 złotych", "futra", "pierścień"],
        "exp": 40
    },
    
    "najemnik": {
        "id": "wrog_najemnik",
        "nazwa": "Najemnik",
        "typ": "wrog",
        "hp_max": 75,
        "ikona": "⚔️",
        "opis": "Zawodowy żołnierz walczący dla najwyższej stawki. Świetnie wyszkolony.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["koszary", "grod_graniczny", "oboz"],
        "lokacje_rzadkie": ["droga", "most"],
        "slabosci": [],
        "specjalne_ataki": ["seria ciosów", "blok tarczą"],
        "statystyki": {
            "atak": 22,
            "obrona": 20,
            "szybkosc": 15
        },
        "loot": ["dobry miecz", "kolczuga", "30-50 złotych", "tarcza"],
        "exp": 60
    },
    
    "zboj": {
        "id": "wrog_zboj",
        "nazwa": "Zbój",
        "typ": "wrog",
        "hp_max": 60,
        "ikona": "⚔️",
        "opis": "Hardkorowy rozbójnik z gór. Okrutny i bezwzględny.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["gory", "przeleczy", "jaskinia"],
        "lokacje_rzadkie": ["las"],
        "slabosci": [],
        "specjalne_ataki": ["atak z góry", "podcinanie nóg"],
        "statystyki": {
            "atak": 20,
            "obrona": 16,
            "szybkosc": 17
        },
        "loot": ["siekiera", "25-40 złotych", "liny", "manierka"],
        "exp": 55
    },
    
    "dezerter": {
        "id": "wrog_dezerter",
        "nazwa": "Dezerter",
        "typ": "wrog",
        "hp_max": 50,
        "ikona": "⚔️",
        "opis": "Były żołnierz uciekły z wojska. Desperacki i niebezpieczny.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["las", "bagna", "jaskinia"],
        "lokacje_rzadkie": ["wioska", "droga"],
        "slabosci": [],
        "specjalne_ataki": ["atak desperacki (zwiększone obrażenia gdy HP<30%)"],
        "statystyki": {
            "atak": 17,
            "obrona": 13,
            "szybkosc": 14
        },
        "loot": ["zniszczona zbroja", "wojskowy miecz", "15-25 złotych"],
        "exp": 35
    },
    
    "najezdca": {
        "id": "wrog_najezdca",
        "nazwa": "Najeźdźca",
        "typ": "wrog",
        "hp_max": 85,
        "ikona": "⚔️",
        "opis": "Wojownik z wrogiego plemienia. Ciężko uzbrojony i agresywny.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["grod_graniczny", "most", "droga"],
        "lokacje_rzadkie": ["wioska"],
        "slabosci": [],
        "specjalne_ataki": ["szarża na koniu", "cios włócznią"],
        "statystyki": {
            "atak": 24,
            "obrona": 22,
            "szybkosc": 20
        },
        "loot": ["włócznia", "łuskowa zbroja", "40-60 złotych", "koń (rzadko)"],
        "exp": 70
    },
    
    "czarny_rycerz": {
        "id": "wrog_czarny_rycerz",
        "nazwa": "Czarny Rycerz",
        "typ": "wrog",
        "hp_max": 110,
        "ikona": "⚔️",
        "opis": "Tajemniczy wojownik w czarnej zbroi. Legenda mówi, że jest nieśmiertelny.",
        "poziom_trudnosci": "bardzo_silny",
        "lokacje_glowne": ["ruiny", "cmentarz"],
        "lokacje_rzadkie": ["grod_graniczny"],
        "slabosci": ["święcona broń"],
        "specjalne_ataki": ["mroczny cios", "regeneracja (2 HP/turę)"],
        "statystyki": {
            "atak": 28,
            "obrona": 26,
            "szybkosc": 16
        },
        "loot": ["czarna płytowa zbroja", "przeklęty miecz", "80-120 złotych", "amulet mroku"],
        "exp": 100
    }
}

# ============================================================================
# BESTIE - ZWIERZĘTA
# ============================================================================

ZWIERZETA = {
    "wilk": {
        "id": "bestia_wilk",
        "nazwa": "Szary Wilk",
        "typ": "bestia",
        "hp_max": 40,
        "ikona": "🐺",
        "opis": "Drapieżnik polujący w stadzie. Szybki i niebezpieczny w grupie.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["las", "gory"],
        "lokacje_rzadkie": ["bagna", "droga"],
        "slabosci": ["ogień"],
        "specjalne_ataki": ["ugryzione (szansa na krwawienie)", "wycie (przyzywa sojuszników)"],
        "statystyki": {
            "atak": 16,
            "obrona": 10,
            "szybkosc": 20
        },
        "loot": ["wilcza skóra", "wilcze kły", "wilcze mięso"],
        "exp": 28
    },
    
    "dzik": {
        "id": "bestia_dzik",
        "nazwa": "Dziki Dzik",
        "typ": "bestia",
        "hp_max": 35,
        "ikona": "🐗",
        "opis": "Agresywny i nieobliczalny. Atakuje gdy się go spłoszy.",
        "poziom_trudnosci": "slaby",
        "lokacje_glowne": ["las"],
        "lokacje_rzadkie": ["gory", "wioska"],
        "slabosci": [],
        "specjalne_ataki": ["szarża (zwiększone obrażenia)"],
        "statystyki": {
            "atak": 14,
            "obrona": 12,
            "szybkosc": 12
        },
        "loot": ["dzicze mięso", "kły dzika", "skóra"],
        "exp": 22
    },
    
    "niedzwiedz": {
        "id": "bestia_niedzwiedz",
        "nazwa": "Brunatny Niedźwiedź",
        "typ": "bestia",
        "hp_max": 80,
        "ikona": "🐻",
        "opis": "Potężny drapieżnik. Ogromna siła i gruba skóra chronią go przed atakami.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["gory", "las"],
        "lokacje_rzadkie": ["jaskinia"],
        "slabosci": [],
        "specjalne_ataki": ["cios łapą (ogłuszenie)", "przytulenie niedźwiedzie (2x obrażenia)"],
        "statystyki": {
            "atak": 26,
            "obrona": 20,
            "szybkosc": 10
        },
        "loot": ["niedźwiedzia skóra", "niedźwiedzie mięso", "pazury", "tłuszcz"],
        "exp": 65
    },
    
    "lis": {
        "id": "bestia_lis",
        "nazwa": "Rudy Lis",
        "typ": "bestia",
        "hp_max": 20,
        "ikona": "🦊",
        "opis": "Przebiegłe stworzenie, rzadko atakuje ludzi. Szybkie i zwinne.",
        "poziom_trudnosci": "slaby",
        "lokacje_glowne": ["las"],
        "lokacje_rzadkie": ["wioska", "droga"],
        "slabosci": [],
        "specjalne_ataki": ["unik (zwiększona szansa na unik)"],
        "statystyki": {
            "atak": 8,
            "obrona": 6,
            "szybkosc": 22
        },
        "loot": ["lisi ogon", "futro"],
        "exp": 12
    },
    
    "orzel": {
        "id": "bestia_orzel",
        "nazwa": "Orzeł Górski",
        "typ": "bestia",
        "hp_max": 30,
        "ikona": "🦅",
        "opis": "Dumny ptak drapieżny. Atakuje z powietrza ostrymi szponami.",
        "poziom_trudnosci": "slaby",
        "lokacje_glowne": ["gory", "wieza_straznicza"],
        "lokacje_rzadkie": ["ruiny"],
        "slabosci": [],
        "specjalne_ataki": ["nurkowanie (podwójne obrażenia przy pierwszym ataku)"],
        "statystyki": {
            "atak": 12,
            "obrona": 8,
            "szybkosc": 24
        },
        "loot": ["orlinie pióra", "szpony"],
        "exp": 18
    },
    
    "zubr": {
        "id": "bestia_zubr",
        "nazwa": "Żubr",
        "typ": "bestia",
        "hp_max": 70,
        "ikona": "🦬",
        "opis": "Potężne zwierzę z pradawnych lasów. Spokojne dopóki się go nie drażni.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["las"],
        "lokacje_rzadkie": ["polana"],
        "slabosci": [],
        "specjalne_ataki": ["tratowanie (wysokie obrażenia)", "szarża stada"],
        "statystyki": {
            "atak": 22,
            "obrona": 18,
            "szybkosc": 14
        },
        "loot": ["żubrze mięso", "skóra żubra", "rogi"],
        "exp": 58
    },
    
    "jelen": {
        "id": "bestia_jelen",
        "nazwa": "Jeleń Szlachetny",
        "typ": "bestia",
        "hp_max": 25,
        "ikona": "🦌",
        "opis": "Majestatyczne zwierzę leśne. Broni się tylko gdy jest zagrożone.",
        "poziom_trudnosci": "slaby",
        "lokacje_glowne": ["las", "polana"],
        "lokacje_rzadkie": ["gory"],
        "slabosci": [],
        "specjalne_ataki": ["cios porożem"],
        "statystyki": {
            "atak": 10,
            "obrona": 8,
            "szybkosc": 18
        },
        "loot": ["jelenie mięso", "skóra", "poroże"],
        "exp": 16
    },
    
    "rys": {
        "id": "bestia_rys",
        "nazwa": "Ryś",
        "typ": "bestia",
        "hp_max": 45,
        "ikona": "🐱",
        "opis": "Zwinny drapieżnik o ostrych zmysłach. Poluje skrycie z zaskoczenia.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["las", "gory"],
        "lokacje_rzadkie": ["jaskinia"],
        "slabosci": [],
        "specjalne_ataki": ["skok z zaskoczenia (podwójne obrażenia)", "rozdarcie pazurami"],
        "statystyki": {
            "atak": 18,
            "obrona": 12,
            "szybkosc": 22
        },
        "loot": ["rysia skóra", "pazury", "futro"],
        "exp": 32
    }
}

# ============================================================================
# BESTIE - POTWORY SŁOWIAŃSKIE
# ============================================================================

POTWORY = {
    "strzygon": {
        "id": "potwor_strzygon",
        "nazwa": "Strzygon",
        "typ": "bestia",
        "hp_max": 90,
        "ikona": "🧛",
        "opis": "Żywy trup pijący krew żywych. Boi się światła dziennego i srebrnej broni.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["cmentarz", "ruiny"],
        "lokacje_rzadkie": ["jaskinia", "wioska"],
        "slabosci": ["srebro", "światło słoneczne", "święcona woda"],
        "specjalne_ataki": ["wysysanie krwi (leczy się za zadane obrażenia)", "hipnoza"],
        "statystyki": {
            "atak": 24,
            "obrona": 16,
            "szybkosc": 18
        },
        "loot": ["wampirzy kieł", "mroczny amulet", "50-70 złotych"],
        "exp": 75
    },
    
    "strzyga": {
        "id": "potwor_strzyga",
        "nazwa": "Strzyga",
        "typ": "bestia",
        "hp_max": 65,
        "ikona": "👹",
        "opis": "Żywy trup powstały z pogrzebanej żywcem czarownicy. Atakuje w nocy.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["cmentarz", "bagna"],
        "lokacje_rzadkie": ["ruiny"],
        "slabosci": ["srebro", "ogień"],
        "specjalne_ataki": ["krzyk strzygi (ogłuszenie)", "pazury trujące"],
        "statystyki": {
            "atak": 20,
            "obrona": 14,
            "szybkosc": 16
        },
        "loot": ["kości strzygi", "ziemia z mogiły", "30-50 złotych"],
        "exp": 52
    },
    
    "utopiec": {
        "id": "potwor_utopiec",
        "nazwa": "Utopiec",
        "typ": "bestia",
        "hp_max": 55,
        "ikona": "🧟",
        "opis": "Duch topielca ciągnący żywych do wody. Wychodzi z rzek i bagien.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["bagna", "rzeka"],
        "lokacje_rzadkie": ["las", "most"],
        "slabosci": ["ogień", "święcona woda"],
        "specjalne_ataki": ["ciągnięcie pod wodę", "uduszenie"],
        "statystyki": {
            "atak": 18,
            "obrona": 12,
            "szybkosc": 14
        },
        "loot": ["wodorosty", "zatopione skarby", "20-40 złotych"],
        "exp": 45
    },
    
    "bies": {
        "id": "potwor_bies",
        "nazwa": "Bies Leśny",
        "typ": "bestia",
        "hp_max": 75,
        "ikona": "👿",
        "opis": "Mroczny demon zamieszkujący głębokie lasy. Zwodzi podróżnych na manowce.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["las"],
        "lokacje_rzadkie": ["bagna", "gory"],
        "slabosci": ["święcona broń", "modlitwy"],
        "specjalne_ataki": ["iluzja (przywołuje kopie)", "mroczna magia"],
        "statystyki": {
            "atak": 22,
            "obrona": 18,
            "szybkosc": 16
        },
        "loot": ["rogi biesa", "mroczny kryształ", "40-60 złotych"],
        "exp": 62
    },
    
    "rusalka": {
        "id": "potwor_rusalka",
        "nazwa": "Rusałka",
        "typ": "bestia",
        "hp_max": 50,
        "ikona": "🧜",
        "opis": "Duch utonionej dziewicy. Piękna i śmiertelnie niebezpieczna.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["rzeka", "bagna"],
        "lokacje_rzadkie": ["las"],
        "slabosci": ["święcona woda", "modlitwy"],
        "specjalne_ataki": ["urok (cel traci turę)", "śpiew śmierci"],
        "statystyki": {
            "atak": 16,
            "obrona": 10,
            "szybkosc": 18
        },
        "loot": ["perły", "srebrne włosy", "25-45 złotych"],
        "exp": 42
    },
    
    "wij": {
        "id": "potwor_wij",
        "nazwa": "Wij",
        "typ": "bestia",
        "hp_max": 150,
        "ikona": "👁️",
        "opis": "Pradawny demon z ognistym wzrokiem. Jego spojrzenie zabija na miejscu.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["ruiny"],
        "lokacje_rzadkie": ["jaskinia", "cmentarz"],
        "slabosci": ["nie patrzeć w oczy", "święcona broń"],
        "specjalne_ataki": ["wzrok śmierci (50% HP)", "przyzywanie demonów"],
        "statystyki": {
            "atak": 32,
            "obrona": 24,
            "szybkosc": 12
        },
        "loot": ["oko Wija", "demoniczny amulet", "150-200 złotych", "artefakt mroku"],
        "exp": 180
    },
    
    "zmij": {
        "id": "potwor_zmij",
        "nazwa": "Zmij Ognisty",
        "typ": "bestia",
        "hp_max": 120,
        "ikona": "🐉",
        "opis": "Smok słowiańskich ziem. Sieje zniszczenie ogniem i pazurami.",
        "poziom_trudnosci": "bardzo_silny",
        "lokacje_glowne": ["gory", "jaskinia"],
        "lokacje_rzadkie": ["ruiny"],
        "slabosci": ["woda", "lód"],
        "specjalne_ataki": ["oddech ognia (AOE)", "lot (zwiększona obrona)", "pazury smocze"],
        "statystyki": {
            "atak": 30,
            "obrona": 26,
            "szybkosc": 14
        },
        "loot": ["smocza łuska", "smocze serce", "100-150 złotych", "smoczi pazur"],
        "exp": 140
    }
}

# ============================================================================
# BESTIE - INNE POTWORY
# ============================================================================

INNE_POTWORY = {
    "troll_gorski": {
        "id": "potwor_troll",
        "nazwa": "Troll Górski",
        "typ": "bestia",
        "hp_max": 95,
        "ikona": "👹",
        "opis": "Olbrzymi humanoid z kamienną skórą. Żyje w górskich jaskiniach.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["gory", "jaskinia", "przeleczy"],
        "lokacje_rzadkie": ["most"],
        "slabosci": ["ogień", "światło słoneczne"],
        "specjalne_ataki": ["cios kamieniem", "regeneracja (kamiennej skóry)"],
        "statystyki": {
            "atak": 28,
            "obrona": 24,
            "szybkosc": 8
        },
        "loot": ["kamień trollowy", "grube futro", "60-90 złotych"],
        "exp": 78
    },
    
    "olbrzym": {
        "id": "potwor_olbrzym",
        "nazwa": "Olbrzym",
        "typ": "bestia",
        "hp_max": 130,
        "ikona": "🗿",
        "opis": "Gigant o niewyobrażalnej sile. Kroczy po ziemi niczym żywa góra.",
        "poziom_trudnosci": "bardzo_silny",
        "lokacje_glowne": ["gory"],
        "lokacje_rzadkie": ["pustkowie"],
        "slabosci": ["precyzyjne ciosy w słabe punkty"],
        "specjalne_ataki": ["tratowanie", "rzut głazem (wielkie obrażenia)", "trzęsienie ziemi"],
        "statystyki": {
            "atak": 35,
            "obrona": 28,
            "szybkosc": 6
        },
        "loot": ["klub olbrzyma", "olbrzymia skóra", "100-140 złotych", "magiczny kamień"],
        "exp": 125
    },
    
    "zaba_olbrzymia": {
        "id": "potwor_zaba",
        "nazwa": "Żaba Olbrzymia",
        "typ": "bestia",
        "hp_max": 60,
        "ikona": "🐸",
        "opis": "Zmutowana żaba rozmiaru wozu. Poluje językiem i trującą śliną.",
        "poziom_trudnosci": "sredni",
        "lokacje_glowne": ["bagna"],
        "lokacje_rzadkie": ["rzeka"],
        "slabosci": ["ogień"],
        "specjalne_ataki": ["wyrzut języka (ciągnięcie)", "trująca ślina"],
        "statystyki": {
            "atak": 17,
            "obrona": 14,
            "szybkosc": 12
        },
        "loot": ["żabi jad", "skóra żaby", "25-40 złotych"],
        "exp": 48
    },
    
    "paskudnik": {
        "id": "potwor_paskudnik",
        "nazwa": "Paskudnik Bagenny",
        "typ": "bestia",
        "hp_max": 70,
        "ikona": "🦎",
        "opis": "Odrażający gad żyjący w bagnach. Atakuje z zaskoczenia.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["bagna"],
        "lokacje_rzadkie": ["rzeka", "jaskinia"],
        "slabosci": ["ogień"],
        "specjalne_ataki": ["kwasna ślina (uszkodzenie zbroi)", "kamuflaż"],
        "statystyki": {
            "atak": 20,
            "obrona": 16,
            "szybkosc": 14
        },
        "loot": ["skóra paskudnika", "kwasny gruczoł", "30-50 złotych"],
        "exp": 56
    },
    
    "wilkolak": {
        "id": "potwor_wilkolak",
        "nazwa": "Wilkołak",
        "typ": "bestia",
        "hp_max": 85,
        "ikona": "🐺",
        "opis": "Człowiek-wilk, przekształcający się w pełnię. Szybki i śmiertelny.",
        "poziom_trudnosci": "silny",
        "lokacje_glowne": ["las"],
        "lokacje_rzadkie": ["gory", "wioska"],
        "slabosci": ["srebro"],
        "specjalne_ataki": ["rozszarpanie", "wycie (przyzywa wilki)", "przekleństwo wilkołactwa"],
        "statystyki": {
            "atak": 26,
            "obrona": 18,
            "szybkosc": 22
        },
        "loot": ["wilkołacza krew", "srebrne futro", "60-80 złotych", "klątwa"],
        "exp": 72
    }
}

# ============================================================================
# BOSS'Y
# ============================================================================

BOSSY = {
    # --- BOSS'Y PLEMIENNE (2) ---
    "wladca_ciemnosci": {
        "id": "boss_wladca_ciemnosci",
        "nazwa": "Władca Ciemności",
        "typ": "boss",
        "hp_max": 200,
        "ikona": "💀",
        "opis": "Mroczny władca dążący do zniszczenia plemion słowiańskich. Otoczony armią nieumarłych.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["ruiny"],
        "lokacje_rzadkie": ["cmentarz"],
        "slabosci": ["święcona broń", "światło"],
        "specjalne_ataki": [
            "mroczna fala (AOE)",
            "przywoływanie nieumarłych",
            "wysysanie życia",
            "tarcza cieni (absorpcja obrażeń)"
        ],
        "statystyki": {
            "atak": 35,
            "obrona": 30,
            "szybkosc": 16
        },
        "loot": ["korona władcy", "miecz mroku", "300-500 złotych", "księga zaklęć", "artefakt legendarny"],
        "exp": 250
    },
    
    "warkocz_okrutny": {
        "id": "boss_warkocz",
        "nazwa": "Warkocz Okrutny",
        "typ": "boss",
        "hp_max": 180,
        "ikona": "⚔️",
        "opis": "Bezwzględny wódz najemników terroryzujący ziemie. Niezwyciężony w walce wręcz.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["grod_graniczny", "oboz"],
        "lokacje_rzadkie": ["droga"],
        "slabosci": ["podstęp", "trucizna"],
        "specjalne_ataki": [
            "wir ostrzy",
            "cios wykonawczy",
            "wrzask wojenny (buff sojuszników)",
            "pancerz bojowy (zwiększona obrona)"
        ],
        "statystyki": {
            "atak": 38,
            "obrona": 32,
            "szybkosc": 18
        },
        "loot": ["zbroja Warkocza", "dwuręczny miecz", "250-400 złotych", "hełm wódza", "pierścień siły"],
        "exp": 220
    },
    
    # --- BOSS'Y LOKACYJNE (3) ---
    "straznik_ruin": {
        "id": "boss_straznik_ruin",
        "nazwa": "Mroczny Strażnik",
        "typ": "boss",
        "hp_max": 160,
        "ikona": "🗿",
        "opis": "Antyczny golem pilnujący zaginionych sekretów. Niezniszczalny bez odpowiedniej magii.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["ruiny"],
        "lokacje_rzadkie": [],
        "slabosci": ["magia", "starożytne zaklęcia"],
        "specjalne_ataki": [
            "cios kamiennej pięści",
            "trzęsienie fundamentów",
            "regeneracja (w ruinach)",
            "magia ochronna"
        ],
        "statystyki": {
            "atak": 32,
            "obrona": 35,
            "szybkosc": 10
        },
        "loot": ["serce golema", "starożytne tabliczki", "200-350 złotych", "magiczny amulet"],
        "exp": 200
    },
    
    "krol_trolli": {
        "id": "boss_krol_trolli",
        "nazwa": "Król Trolli",
        "typ": "boss",
        "hp_max": 170,
        "ikona": "👑",
        "opis": "Władca górskich trolli. Potężny, odporny i przebiegły mimo swojej wielkości.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["gory", "jaskinia"],
        "lokacje_rzadkie": [],
        "slabosci": ["ogień", "światło słoneczne"],
        "specjalne_ataki": [
            "kamienna skóra (tymczasowa niezniszczalność)",
            "lawina",
            "ryk królewski",
            "rzut głazem"
        ],
        "statystyki": {
            "atak": 34,
            "obrona": 30,
            "szybkosc": 12
        },
        "loot": ["korona trolli", "berło kamienne", "220-380 złotych", "runy górskie", "kryształ góry"],
        "exp": 210
    },
    
    "matka_bagien": {
        "id": "boss_matka_bagien",
        "nazwa": "Matka Bagien",
        "typ": "boss",
        "hp_max": 155,
        "ikona": "🧙",
        "opis": "Pradawna wiedźma władająca bagnami. Kontroluje wodę i trujące rośliny.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["bagna"],
        "lokacje_rzadkie": [],
        "slabosci": ["ogień", "święcona woda"],
        "specjalne_ataki": [
            "zatruty dym",
            "bagienne macki (unieruchomienie)",
            "leczenie z wody",
            "przyzywanie paskudników"
        ],
        "statystyki": {
            "atak": 28,
            "obrona": 24,
            "szybkosc": 14
        },
        "loot": ["laska wiedźmy", "eliksir życia", "200-320 złotych", "księga zaklęć bagiennych", "magiczny kocioł"],
        "exp": 190
    },
    
    # --- BOSS'Y FABULARNE (2) ---
    "czarnobog": {
        "id": "boss_czarnobog",
        "nazwa": "Czarnobóg",
        "typ": "boss",
        "hp_max": 250,
        "ikona": "👹",
        "opis": "Bóg ciemności i zniszczenia. Ostateczny przeciwnik dążący do zagłady świata.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["ruiny"],
        "lokacje_rzadkie": [],
        "slabosci": ["światło Swaroga", "zjednoczone plemiona"],
        "specjalne_ataki": [
            "wybuch czarnej energii",
            "przeklęta ziemia",
            "kradzież duszy",
            "forma mroczna (teleport + niewidzialność)"
        ],
        "statystyki": {
            "atak": 40,
            "obrona": 35,
            "szybkosc": 20
        },
        "loot": ["serce Czarnoboga", "korona bogów", "500+ złotych", "artefakt boski", "miecz legendy"],
        "exp": 300
    },
    
    "heretyk_weles": {
        "id": "boss_heretyk",
        "nazwa": "Heretyk Weles",
        "typ": "boss",
        "hp_max": 165,
        "ikona": "🧙",
        "opis": "Zbuntowany kapłan władający mroczną magią. Pragnie zniszczyć wszystkie świątynie.",
        "poziom_trudnosci": "legendarny",
        "lokacje_glowne": ["swiatynia", "ruiny"],
        "lokacje_rzadkie": ["cmentarz"],
        "slabosci": ["święcona broń", "modlitwy kapłanów"],
        "specjalne_ataki": [
            "kula mroku",
            "przekleństwo Welesa",
            "przyzywanie demonów",
            "oszukany los (losuje cel do instant-kill)"
        ],
        "statystyki": {
            "atak": 30,
            "obrona": 26,
            "szybkosc": 18
        },
        "loot": ["szaty heretyka", "mroczny posох", "240-400 złotych", "przeklęte relikwie", "księga zakazana"],
        "exp": 205
    }
}

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def pobierz_wszystkich_przeciwnikow():
    """Zwraca słownik wszystkich przeciwników"""
    return {
        **WROGOWIE,
        **ZWIERZETA,
        **POTWORY,
        **INNE_POTWORY,
        **BOSSY
    }

def pobierz_przeciwnika(id_lub_nazwa):
    """Pobiera przeciwnika po ID lub nazwie"""
    wszyscy = pobierz_wszystkich_przeciwnikow()
    
    # Szukaj po ID
    if id_lub_nazwa in wszyscy:
        return wszyscy[id_lub_nazwa]
    
    # Szukaj po nazwie
    for przeciwnik in wszyscy.values():
        if przeciwnik['nazwa'].lower() == id_lub_nazwa.lower():
            return przeciwnik
    
    return None

def pobierz_przeciwnikow_dla_lokacji(lokacja, typ=None):
    """Zwraca listę przeciwników występujących w danej lokacji
    
    Args:
        lokacja: nazwa lokacji (np. "las", "gory", "cmentarz")
        typ: opcjonalny filtr typu ("wrog", "bestia", "boss")
    
    Returns:
        Lista słowników przeciwników
    """
    wszyscy = pobierz_wszystkich_przeciwnikow()
    wynik = []
    
    for przeciwnik in wszyscy.values():
        # Sprawdź typ jeśli podano
        if typ and przeciwnik['typ'] != typ:
            continue
        
        # Sprawdź czy występuje w lokacji
        if lokacja in przeciwnik['lokacje_glowne'] or lokacja in przeciwnik['lokacje_rzadkie']:
            wynik.append(przeciwnik)
    
    return wynik

def generuj_kontekst_bestiariusza_dla_ai(lokacja=None):
    """Generuje kontekst dla AI z listą dostępnych przeciwników
    
    Args:
        lokacja: opcjonalnie - filtruj po lokacji
    
    Returns:
        String z formatowanym kontekstem
    """
    if lokacja:
        przeciwnicy = pobierz_przeciwnikow_dla_lokacji(lokacja)
        naglowek = f"BESTIARIUSZ DLA LOKACJI: {lokacja.upper()}"
    else:
        przeciwnicy = list(pobierz_wszystkich_przeciwnikow().values())
        naglowek = "PEŁNY BESTIARIUSZ"
    
    kontekst = f"\n{'='*60}\n{naglowek}\n{'='*60}\n\n"
    
    # Grupuj po typie
    wrogowie = [p for p in przeciwnicy if p['typ'] == 'wrog']
    bestie = [p for p in przeciwnicy if p['typ'] == 'bestia']
    bossy = [p for p in przeciwnicy if p['typ'] == 'boss']
    
    if wrogowie:
        kontekst += "WROGOWIE (ludzie):\n"
        for w in wrogowie:
            kontekst += f"- {w['nazwa']} (HP: {w['hp_max']}, {w['poziom_trudnosci']}): {w['opis']}\n"
        kontekst += "\n"
    
    if bestie:
        kontekst += "BESTIE (zwierzęta i potwory):\n"
        for b in bestie:
            kontekst += f"- {b['nazwa']} (HP: {b['hp_max']}, {w['poziom_trudnosci']}): {b['opis']}\n"
        kontekst += "\n"
    
    if bossy:
        kontekst += "BOSS'Y (unikalni przeciwnicy):\n"
        for boss in bossy:
            kontekst += f"- {boss['nazwa']} (HP: {boss['hp_max']}, LEGENDARNY): {boss['opis']}\n"
        kontekst += "\n"
    
    kontekst += f"\n{'='*60}\n"
    kontekst += "ZASADY UŻYCIA:\n"
    kontekst += "- Używaj TYLKO przeciwników z tej listy\n"
    kontekst += "- Zachowaj dokładne nazwy i HP\n"
    kontekst += "- Boss'ów używaj tylko w specjalnych momentach fabularnych\n"
    kontekst += f"{'='*60}\n"
    
    return kontekst

# ============================================================================
# STATYSTYKI
# ============================================================================

def statystyki_bestiariusza():
    """Zwraca statystyki bestiariusza"""
    wszyscy = pobierz_wszystkich_przeciwnikow()
    
    return {
        "total": len(wszyscy),
        "wrogowie": len(WROGOWIE),
        "zwierzeta": len(ZWIERZETA),
        "potwory_slowianskie": len(POTWORY),
        "inne_potwory": len(INNE_POTWORY),
        "bossy": len(BOSSY),
        "po_poziomach": {
            "slaby": len([p for p in wszyscy.values() if p['poziom_trudnosci'] == 'slaby']),
            "sredni": len([p for p in wszyscy.values() if p['poziom_trudnosci'] == 'sredni']),
            "silny": len([p for p in wszyscy.values() if p['poziom_trudnosci'] == 'silny']),
            "bardzo_silny": len([p for p in wszyscy.values() if p['poziom_trudnosci'] == 'bardzo_silny']),
            "legendarny": len([p for p in wszyscy.values() if p['poziom_trudnosci'] == 'legendarny'])
        }
    }

# Test
if __name__ == "__main__":
    print("🗡️  BESTIARIUSZ - SŁOWIAŃSKIE DZIEDZICTWO 🗡️\n")
    stats = statystyki_bestiariusza()
    print(f"Łącznie przeciwników: {stats['total']}")
    print(f"  - Wrogowie (ludzie): {stats['wrogowie']}")
    print(f"  - Zwierzęta: {stats['zwierzeta']}")
    print(f"  - Potwory słowiańskie: {stats['potwory_slowianskie']}")
    print(f"  - Inne potwory: {stats['inne_potwory']}")
    print(f"  - Boss'y: {stats['bossy']}")
    print(f"\nPoziomy trudności:")
    for poziom, ilosc in stats['po_poziomach'].items():
        print(f"  - {poziom}: {ilosc}")
    
    print("\n" + "="*60)
    print("Przykład: Przeciwnicy w lesie:")
    print("="*60)
    lesni = pobierz_przeciwnikow_dla_lokacji("las")
    for p in lesni[:5]:  # Pokaż pierwszych 5
        print(f"- {p['nazwa']} ({p['typ']}, HP: {p['hp_max']})")
