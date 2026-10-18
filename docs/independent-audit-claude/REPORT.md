# NEON SHIFT 65 — niezależny audyt przedwydaniowy

Data: 2026-10-17. Audyt kodu i lokalnego produktu, bez implementowania poprawek.

**Werdykt: wymaga poprawek przed 1.0.** Potwierdzono dwa błędy HIGH wspólne dla RC1 i RC2 oraz jeden MEDIUM dotyczący wyłącznie testowych ATR-ów FINISH2. Nie wykazano błędu BLOCKER, uszkodzenia RAM ani trwałego znikania obiektów na Energy 02. Pełny replay kampanii zakończył wszystkie 60 poziomów.

Przed końcowym smoke sprzętowym należy naprawić A-01 i A-02. A-03 należy poprawić przed ponownym przekazaniem czterech wariantów testowych. Wcześniejszy, rozpoznawczy test sprzętu pozostaje możliwy, ale nie zamknie tych ustaleń.

## 1. Audytowany stan i pochodzenie produktu

Repozytorium: `/Users/marcinkrzetowski/Projects/atari-sokoban`.

| Element | Ustalony stan |
|---|---|
| Branch | `feature/v1-art-final-energy` |
| HEAD | `ea4f4159c7bc8364825af55879a07f1f93c95520` — FINISH1 / RC1 |
| Poprzednia wskazana baza | `f5df6465ff6ef7d7b86d6ade3d3894a314cfb93c` |
| Główny przedmiot audytu | Bieżący working tree: lokalny FINISH2 / RC2, **nie commit HEAD** |
| Instrukcje | Nie znaleziono `AGENTS.md` w repozytorium ani katalogach nadrzędnych. Przeczytano `PROJECT_BRIEF.md`, README i aktualny kontrakt ENG4; odróżniono zastąpione wymagania historyczne |
| Kopia robocza audytu | `/private/tmp/neon-independent-zrka0xln/tree` |
| Zachowanie oryginału | Ponownie sprawdzono SHA-256 wszystkich 2160 skopiowanych plików wejściowych: zero zmian. HEAD i zastany tracked diff zachowane |

Sześć zastanych zmian tracked: `README.md`, `tools/product1_art.py`, `tools/product1_build.py`, `tools/product1_eng4.py`, `tools/product1_runtime.py`, `tools/v1_build.py` — 41 dodanych i 12 usuniętych linii. Były też pliki untracked, w tym `tools/finish2_*.py`, `experiments/finish2/art.py`, dokumentacja i obrazy FINISH2 oraz wcześniejsze eksperymenty. Ich pełny wykaz zawiera [stan początkowy](initial-status.txt), a zmiany tracked [local.diff](local.diff). [Snapshot](snapshot.json) wiąże kopię z hashami jej wejść; nie polegano na etykietach PASS.

Budowano wyłącznie w nowej kopii, bez odziedziczonego `build/`, obiektów, wygenerowanych pakietów czy ATR-ów. Kopia obejmowała bieżące pliki tracked i untracked potrzebne do budowania. Kopiowanie nie polegało na odtworzeniu samego HEAD. Wykonano siedem pełnych wywołań buildera: RC2, drugi czysty RC2, RC1 i cztery starty obszarów. Wszystkie próby dyskowe używały nowych kopii świeżo zbudowanych ATR-ów.

Nie wykonywano reset, checkout, clean, commit, push, publikacji, instalacji ani uruchamiania okien. Jedyną zmianą oryginalnego repozytorium jest nowy katalog tego raportu. [Weryfikacja zachowania wejść](evidence/preservation.json).

### Narzędzia i identyfikacja obrazów

Python 3.14.8; Node v26.11.1; cl65/cc65/ca65/ld65/sim65 **V2.18 - N/A**; Apple clang 21.0.0. To wersje faktycznych binarek, nie numer pakietu dystrybucji. Emulator: istniejący Atari800 7.1.2 z obserwatorem, skopiowany do izolacji; SHA-256 `bc8703dfd499dae210c07381c4600c4b3c2d31c26de142701b9f9cbf55195c82`. Hash ROM-u i źródła obserwatora zapisano w [tools.json](evidence/tools.json); ROM nie jest dołączony.

Każdy poniższy ATR ma 1 048 592 B: nagłówek 16 B i 8192 sektory po 128 B. Wszystkie sześć odtworzonych obrazów jest bajtowo identycznych z odpowiednimi zastanymi plikami `docs/finish{1,2}/owner-smoke/`. Zgodność ustalono bez zapisywania tych zastanych plików.

| ATR | SHA-256 |
|---|---|
| Zwykły RC2 | `f76a11e76a5a1f6cc4426104c59804cd614c6aa62022f51572d9474c2230acc0` |
| RC2 test-01 | `56f292857d8b45c3d08dddacc1b6b30a64a46efda05eece6d6df1c6ec6d43728` |
| RC2 test-16 | `57e9551504dd7635dcd0665b0d8c29e83139f972d9d39bb8a4aa1583108a1830` |
| RC2 test-31 | `638b273087a9ac98f0e9c48f333da6190e40672aecc8d8d1d0872777ed201008` |
| RC2 test-46 | `18ecd5fe7a5d44a85ba7dc39de0e15896e4cd3595bda4da040d747d5f4c8d2dc` |
| RC1, porównanie z HEAD | `6ba10996b4150ac170a61aec529b350c8af7c310ed53d8150da2b63c888397c8` |

Drugi czysty build RC2 daje ten sam SHA i identyczne bajty. Nie wystąpiła różnica wymagająca tłumaczenia timestampem lub stanem zapisu. [Wiązanie artefaktów](evidence/artifacts.json).

Źródło kampanii: `assets/levels/camp2-b/campaign.json`, SHA-256 `131c57e2692ffe121392e1260c13060960ac8f54425dd870dea28114cd6dae39`. Te bajty są takie same w `f5df646`, HEAD i working tree. Pierwsze cztery bajty skrótu stanowią identyfikator `131c57e2` zwykłego zapisu. Kod ruchu, undo oraz pliki `experiments/product1/{campaign.c,main.c,input.c}` są też niezmienione pomiędzy wskazanymi commitami.

## 2. Tabela ustaleń

### A. Potwierdzone błędy

| ID | Waga | Pewność | Ustalenie | Zakres |
|---|---|---|---|---|
| A-01 | HIGH | Potwierdzony w dokładnym ATR, z transakcją odczytu FIRE wewnątrz `game_step` | FIRE podczas wygrywającego pchnięcia może przejść dalej zamiast wykonać undo | RC1 i RC2 |
| A-02 | HIGH | Potwierdzony kodem 6502 przy częściowym zapisie; wybór sektora dodatkowo potwierdzony w dokładnym ATR | Nieudany odczyt nowszego slotu pozwala nadpisać ostatnią poprawną generację | Wspólny kod zapisu RC1/RC2 |
| A-03 | MEDIUM | Potwierdzony zimnym bootem test-16 i odzyskaniem tego samego zapisu przez menu | Automatyczne wznowienie testowego ATR-u pomija fallback do starszego poprawnego slotu | Lokalny FINISH2, cztery warianty testowe |

### A-01 — nieoznaczone okno wykonywania akcji

**Lokalizacja:** [main.c](../../experiments/product1/main.c), `main()`, linie 67–77 i 102–105; [input.c](../../experiments/product1/input.c), `eng4_accepted()` linia 22 i `input_read()` linie 38–50; [product1_build.py](../../tools/product1_build.py), generator `eng4_capture`, linie 44–60.

**Mechanizm:** `eng4_busy` zostaje ustawione dopiero przez `eng4_accepted()` po powrocie z `game_step()`. DLI może odczytać FIRE w trakcie wykonywania pchnięcia, kiedy ta flaga nadal wynosi zero. Generator ISR zamienia wtedy zbocze w zwykły FIRE; konwersja na intencję undo jest uzależniona wyłącznie od `eng4_busy`. Po zakończeniu publikacji `input_read()` oddaje zachowany FIRE. Jeżeli pchnięcie ukończyło poziom, `main()` interpretuje go już jako przejście poziomu. Wymóg świeżego FIRE po zakończeniu publikacji nie jest spełniony.

**Warunki i skutek:** szybkie FIRE przy wygrywającym pchnięciu i odpowiednia faza DLI. Gracz próbuje cofnąć ruch, ale przechodzi do kolejnego poziomu, otrzymuje pustą historię i automatyczny zapis nowego poziomu. Nie potrzeba uszkodzonego nośnika ani modyfikacji RAM.

**Reprodukcja:** zimny boot zwykłego ATR, FIRE w ramce wejścia 700, pierwszy ruch R w 1000. Kolejny R i FIRE podano na zewnętrzne piny w czasach z [fire-pins.csv](evidence/fire-pins.csv). Dla kończącego pchnięcia:

| Zdarzenie | Zegar ANTIC/CPU |
|---|---:|
| Wejście do `game_step` | 40 514 789 |
| Zewnętrzne naciśnięcie FIRE | 40 516 352 |
| Faktyczny odczyt TRIG0=0 przez grę w DLI | **40 516 729** |
| Powrót z `game_step` | 40 517 071 |
| Dopiero teraz wywołanie `eng4_accepted` | **40 517 193** |
| Oddanie `INPUT_FIRE`, a nie `INPUT_SELECT` | 40 624 571 |

Nie występuje drugie zbocze FIRE po ustaniu zajętości. Ostatecznie scena wynosi 1, ruchy=0, czyli Energy 02; oczekiwano sceny 0, ruchy=1 po undo. Ten sam świadek odtworzono również na świeżym RC1. W kontroli z R przesuniętym wcześniej o 300 taktów FIRE prawidłowo cofa; problem zależy od fazy, a nie od odmiennych zasad poziomu.

Dowody: [odczyty urządzeń](evidence/fire-device-reads.csv), [wejścia i powroty funkcji](evidence/fire-action-state.csv), [wynik RC2](evidence/audit-fire-proof.json), [wynik RC1](evidence/audit-fire-proof-rc1.json), [obraz następnego poziomu](evidence/fire-next-level-frame1450.png). Ramki służą identyfikacji tego testu; granice funkcji i odczytu określono zegarem, bez wnioskowania wyłącznie ze screenshotu.

**Minimalny kierunek naprawy:** rozpoznawać akcję będącą w trakcie wykonania już przed mutowaniem stanu albo wiązać semantykę zbocza FIRE z fazą, w której je zaobserwowano. Uwzględnić także odrzucone próby ruchu, aby wcześniejsze oznaczenie zajętości nie blokowało wejścia na stałe.

**Weryfikacja:** zachować powyższy świadek, przemiatać fazę drugiego R/FIRE wokół pierwszego DLI, sprawdzać undo i oddzielny pełny raster pchnięcia oraz cofnięcia. Osobny świeży FIRE po gotowości nadal musi przechodzić dalej. Nie wystarczy test z przyciskami oddalonymi o pełną ramkę.

### A-02 — wybór slotu po niepełnym odczycie

**Lokalizacja:** [campaign.c](../../experiments/product1/campaign.c), `save_scan()` linie 66–81, zwłaszcza 72 i 80; `save_write()` linie 106–121, zwłaszcza 111–112.

**Mechanizm:** `save_scan()` pomija błąd odczytu slotu i zgłasza `save_error=3` tylko wtedy, gdy nie znalazł żadnego poprawnego rekordu. Przy jednym poprawnym odczycie i jednym nieudanym błąd jest zerowany. `save_write()` uznaje ten skan za wystarczający do wyboru przeciwnego slotu. Nieodczytany slot może zawierać nowszą, ostatnią poprawną generację. Zostaje wtedy wybrany do zapisu.

Normalna ścieżka z dwoma udanymi odczytami zachowuje poprzednią generację. Błąd dotyczy połączenia nieudanego odczytu jednego slotu z kolejną awarią/przerwaniem zapisu tego slotu. Odczyt zwrotny i CRC wykrywają uszkodzenie, ale nie odzyskują nadpisanych bajtów.

**Warunki i skutek:** dwa poprawne zapisy, przejściowy błąd odczytu nowszego oraz częściowy następny zapis. Możliwy jest powrót do wcześniejszego checkpointu zamiast ostatniego poprawnego. Nie stwierdzono utraty obu slotów w tej reprodukcji, dlatego waga HIGH, a nie BLOCKER.

**Reprodukcja i granica dowodu:** gra sama wytworzyła generacje 1 i 2 (1 i 2 ruchy) na kopii ATR-u. Następnie:

1. Uruchomiono **bieżący wygenerowany `campaign.c` i rzeczywisty `crc.s` w sim65**, z tymi dwoma rekordami. Kod procedur zapisu i CRC pozostał bez zmian; harness dostarczył otoczenie testowe i model urządzenia: odczyt sektora 8101 zwraca błąd, a zapis kopiuje pierwsze 64 B i zwraca błąd.
2. `save_write()` wybiera sektor **8101**, zawierający generację 2. Po ustąpieniu awarii odczytu odzyskuje się generację 1, ruchy=1; ostatni poprawny stan miał ruchy=2.
3. W dokładnym ATR RC2, z istniejącą zewnętrzną injekcją błędu odczytu Atari800, potwierdzono wybór i zmianę właśnie nowszego sektora 8101. Ten emulatorowy przebieg zapisał pełny sektor; **nie przedstawiam go jako fizycznego częściowego zapisu na SIO2SD**.

Dowody: [log sim65](evidence/save-fault.log), [harness urządzenia](evidence/save-fault.c), [wynik i potwierdzenie ATR](evidence/save-fault.json). Test nie zmienia implementacji zapisu ani źródeł gry. [Dwa rekordy wejściowe](repro/save-slots.bin) pochodzą z nowych zapisów audytu.

**Minimalny kierunek naprawy:** oddzielić dopuszczalny odczyt awaryjny na potrzeby Continue od kompletnego skanu wymaganego do zapisu. Nie nadpisywać nieodczytanego slotu, jeżeli nie wiadomo, czy zawiera najnowszą generację; w takim stanie zwrócić błąd zapisu lub ponowić odczyt.

**Weryfikacja:** osobno awaria odczytu każdego z dwóch slotów, obie kolejności generacji, zawinięcie numeru generacji oraz przerwanie kolejnego zapisu. Ostatnia wcześniejsza poprawna generacja ma pozostać bajtowo zachowana. Zwykły test write-protect nie obejmuje tego mechanizmu.

### A-03 — odmienna obsługa uszkodzonego wznowienia w testowych ATR-ach

**Lokalizacja:** [finish2_overlay.py](../../tools/finish2_overlay.py), `install()`, linie 79–88, zwłaszcza wstrzyknięta ścieżka startowa w linii 83. Dla porównania poprawniejsza ścieżka menu: [main.c](../../experiments/product1/main.c), linie 55–60; walidacja semantyczna `save_apply()` w `campaign.c`, linie 86–94.

**Mechanizm:** autostart testowego obrazu wykonuje `save_scan()` i pojedyncze `prepare(..., restore)`. Jeżeli rekord ma poprawny CRC i podstawowy format, lecz jest niezgodny z terenem planszy, `save_apply()` go odrzuca. Autostart nie próbuje `save_previous()`; ustawia fazę 6 i pokazuje błąd odczytu/walidacji zasobów przy `error=0`. FIRE ponawia tę samą niepoprawną próbę. Menu Continue zawiera fallback do poprzedniego slotu.

**Reprodukcja:** test-16 wykonał trzy legalne ruchy i zapisał stan. Dodano w drugim slocie nowszy rekord z graczem `(0,0)` na ścianie i przeliczonym CRC. Starszy, autentyczny rekord zachowano. Zimny autostart i FIRE retry pozostają w fazie 6, `error=0`. START → tytuł → CONTINUE odzyskuje starszy stan, scena 15, ruchy=3. [Wynik](evidence/audit-test-resume.json).

To celowy test semantycznie niepoprawnego, CRC-poprawnego wejścia; zwykłe pojedyncze przekłamanie CRC jest odrzucane wcześniej. Błąd ogranicza się do ścieżki testowego autostartu i ma działające obejście przez menu. Nie dotyczy niezaimplementowanego FINISH2 w RC1.

**Minimalny kierunek naprawy:** użyć tej samej procedury wyboru/odtworzenia rekordu w autostarcie i menu, z zachowaniem oddzielnych identyfikatorów testów. Błędny save powinien otrzymać komunikat dotyczący zapisu, a starszy poprawny rekord szansę odtworzenia.

**Weryfikacja:** oba sloty w obu kolejnościach, błędny teren/liczba skrzyń/CRC planszy, poprawny starszy rekord oraz brak poprawnego rekordu. Ponownie sprawdzić izolację wszystkich pięciu identyfikatorów.

### B. Ryzyka wymagające potwierdzenia

Nie pozostawiono dodatkowej konkretnej hipotezy błędu kodu jako ustalenia. Ograniczenia sprzętowe, fizyczne przerwanie zapisu i brak dowodu globalnego WCET są jawnie wymienione w NOT_RUN poniżej. Nie traktuję 10 B wolnego MAIN wariantów testowych ani braku fizycznego Atari jako dowodu uszkodzenia pamięci.

## 3. Potwierdzone właściwości i metoda sprawdzenia

### Build, dane i stare kopie kampanii

Rzeczywista droga produktu:

`tools/v1_build.py` → `product1_build.py --campaign --art-final --finish1` → kopia `experiments/eng3-observed-input-3pal` + nakładki VIS1-r2/PRODUCT1/FINISH1/FINISH2 → generowanie i kompilacja C/ASM → XEX → strumień bootujący + sektory NSCD/NSLV/NSRQ → ATR.

`product1_data.load()` otrzymuje jawne `NEON_CAMPAIGN=assets/levels/camp2-b/campaign.json`. `visual_size` pochodzi z tego samego JSON-u. `product1_runtime.pack()` umieszcza 60 plansz w sektorach `1100+70*n`, a ich grafiki od następnego sektora. Niezależny parser audytu, z osobną implementacją CRC16, sprawdził **każdy kafel**, cele pod `+` i `*`, gracza, uporządkowane skrzynie, nazwę, area, wersje, ID, CRC i wszystkie 60 pakietów 8768 B. Pakiety w ATR są identyczne z nowo wygenerowanymi plikami. [Wynik](evidence/core-result.json), [parser i oracle](repro/audit_core.py).

Starsze mapy `src/levels_data.c` nie są linkowane do tego produktu. Historyczne mapy Python/C nadal uczestniczą w wytwarzaniu fixture'ów i testów pomocniczych, ale wydawane sektory plansz zostały sprawdzone przeciwko CAMP2-B. Pakowanie zeruje historyczne poziomy w sektorach 512–895 oraz wpisy katalogu kind 2/3; bieżący runtime ładuje kampanię jako kind 1. Nie stwierdzono drogi, którą starsza mapa zastępuje jedną z 60 plansz obecnego ATR-u.

Część zasobów bazowych, np. fonty, pochodzi świadomie z przypiętego `experiments/eng3-observed-input-3pal/reference/prototype_assets.c`, a nie z odświeżenia wszystkich dawnych JSON-ów grafiki. To rzeczywiste wejście buildu ujęte w snapshot. Samo zmienienie starego JSON-u/prototypowego Makefile nie oznacza zmiany obecnego produktu.

### Pamięć i ABI

Odczytano rzeczywiste mapy ld65 i wygenerowany `source/link.cfg`; `cfg/neon.cfg` głównego Makefile nie opisuje tej wersji produktu.

| Obszar | Rzeczywiste przeznaczenie |
|---|---|
| `$0082–$00CB` | ZP gry i runtime cc65; 52 B do `$00FF` |
| `$0100–$01FF` | Stos sprzętowy; osobny od stosu C |
| `$0200–$05FF` | Wektory, cienie, DCB i obszary OS; nie są wolnym RAM-em gry |
| `$0600–$13ED` | Kod/stałe i scratch LOW; granica rezerwacji `$1400` |
| `$1400–$171F` | Kompozycja kafli, 800 B |
| `$1720–$17FF` | Status i scratch loadera |
| `$1800–$1E0F` | Muzyka, dokładnie 1552 B |
| `$1E10–$1FED` | Dodatkowy kod kampanii; nie nakłada się na muzykę |
| `$2000–$7FBB` | MAIN zwykłego RC2, łącznie z BSS |
| `$8000–$87FF` | Rezerwa stosu programowego cc65, 2048 B |
| `$8800–$8BBF` | Ekran 40×24 |
| `$8C00–$8FFF`, `$A000–$AFFF` | Pięć fontów po 1 KB, poprawnie wyrównanych |
| `$9000–$93FF`, `$9400–$9597` | HUD i staging |
| `$9600–$9706` | PERSIST: rekord zapisu, stan i katalog |
| `$9800–$9B6F`, `$9B70–$9BFF`, `$9C00–$9C7F` | Baza ekranu, nagłówek pakietu, bufor sektora |
| `$9C80–$9DDF`, `$9DE0–$9F5F` | Wspólny font i deskryptor |
| `$9F60–$9FF7`, `$9FF8–$9FFF` | Display List i paleta |
| `$B160–$B65F`, `$B680–$B998` | 40 klatek robota i tymczasowy GameState |
| `$BA00–$BEFF`, `$BF00–$BF7F`, `$BF80–$BFFF` | Rezydentny obraz/lista loadera i bufor bootu, również poza główną mapą segmentów |

Menu i splash celowo korzystają z nakładek. Menu zapisuje m.in. `$A000–$AC7F`, `$B000–$B31F` i `$B400–$B8AF`, co nadpisuje zasoby robota i stan kandydata. Ścieżka przygotowania/resume ponownie je ładuje, a stan gry pozostaje w MAIN. Loader pokazuje własne dane podczas nadpisywania nakładek; aktywacja planszy następuje po walidacji. Parser BFS z buforami `$A000/$A2F8` jest wyłączony z docelowego kodu Atari; nie wykazano kolizji tych buforów z grą.

| Build | MAIN wolne | LOW wolne | ZP wolne |
|---|---:|---:|---:|
| RC1 | 36 B | 18 B | 52 B |
| RC2 menu | 68 B | 18 B | 52 B |
| RC2 test-01 | 16 B | 18 B | 52 B |
| RC2 test-16/31/46 | 10 B | 18 B | 52 B |

We wszystkich: EXTRA wolne 18 B. [Mapy i zestawienie](evidence/memory.json). Mały MAIN ogranicza przyszłe zmiany kodu, ale nie zmniejsza oddzielnej rezerwy stosu C.

W 58 profilach emulatora od wejścia do `main` zaobserwowano maksymalnie **20 B stosu C** i **36 B stosu sprzętowego**, zero próbek wskaźnika stosu C poza rezerwacją. Obserwator sprawdza instrukcje, nie tylko screenshoty. To obejmuje standardowe OS SIO, zapis, błędy, kampanię i kontrolki; nie jest formalnym maksimum wszystkich przeplotów IRQ/NMI. [Profile](evidence/stack.json).

Zweryfikowano układ GameState cc65: map=760 B, gracz offset 762, skrzynie 764, liczba skrzyń 784, liczniki 785 i 789, razem 793 B. Natywne ruch/undo korzystają z tego samego układu i zwracają rozszerzony wynik A/X. Sprawdzono zdejmowanie parametrów oraz rozdzielenie scratch ISR i foreground. Zasady porównano z [dokumentacją ABI cc65](https://cc65.github.io/doc/cc65-intern.html#ss2.1); zachowanie zweryfikowano także uruchomieniem kodu 6502. Nie znaleziono konkretnego mechanizmu przepełnienia stosu ani współbieżnego użycia pseudo-rejestrów cc65 przez ISR. Wyścig A-01 jest błędem klasyfikacji wejścia, nie uszkodzeniem ABI.

### Sokoban, undo i przejścia

Niezależny model Python jawnie odrzuca wejście w ścianę, wyjście poza planszę, pchanie w ścianę i pchanie na skrzynię. Nie używa parsera ani solvera repozytorium. Przeprowadził wszystkie **9741 kroków** zapisanych rozwiązań i sprawdził końcową równość zbiorów skrzyń i celów dla 60 poziomów. Nie wyciągano z długości ścieżek wniosków o jakości lub trudności.

Po każdym kroku sprawdzano 16-bitową sygnaturę współrzędnych i liczników wyliczoną przez ten model, w C z ASan/UBSan i w sim65 z rzeczywistymi `move.s` / `undo-fast.s`. Sygnatura nie jest dowodem pełnej równości bajtowej każdego stanu; po cofnięciu użyto dodatkowo pełnego porównania GameState, a końce wszystkich poziomów sprawdzono współrzędnymi w dokładnym ATR. Dodatkowo 240 prób z czterech kierunków na początkach poziomów sprawdza skuteczność lub blokadę ruchu. Kontrolowano wartowników obok GameState. Po cofnięciu `min(długość,256)` wynik porównywano bajtowo z właściwym wcześniejszym stanem; kolejne undo pustego bufora jest obojętne. Najdłuższa ścieżka ma 390 ruchów, więc test faktycznie przekracza pojemność pierścienia. Wszystkie symbole `#`, spacja, `@`, `$`, `.`, `*`, `+` występują w badanych danych.

Osobno zimno uruchomiony **dokładny ATR** rozegrał wszystkie poziomy przez PORTA/TRIG0/CONSOL. Sprawdzano rzeczywiste współrzędne, liczniki i fazę wygranej, a nie kod zakończenia replay. Przejścia 15/16, 30/31, 45/46 i finał po 60 wystąpiły w tym przebiegu. Kampania trwała 98 738 emulowanych ramek. [Wiązanie przebiegu](evidence/campaign-binding.json), [timing](evidence/campaign-timing.json).

Osobne próby potwierdziły zachowanie przytrzymanego kierunku, pojedyncze undo przy trzymanym FIRE/SELECT, pauzę i resume, restart z odtworzeniem pełnego GameState oraz brak ruchu z kierunku trzymanego przez ładowanie aż do zwolnienia. [Kontrolki](evidence/audit-controls.json). Kontrprzykładem do pełnego zachowania ENG4 pozostaje A-01.

Na dokładnym ATR, przez diagnostyczne kopie rekordów z poprawnym CRC, sprawdzono przeniesienia 9→10, 99→100, 999→1000, licznik 3999999999 oraz zawinięcie 4294967295→0 i cofnięcie. Liczniki GameState, dziesięć cyfr cache HUD i opublikowany cache live zgadzały się po ruchu i undo. To test granic liczników, nie twierdzenie, że gracz wykonał miliardy ruchów. [Wyniki](evidence/audit-counters.json).

### Zapis i błędy zasobów

Format NSAV v1: 128 B, poziom, opcje/finał, generacja 16-bitowa, identyfikator kampanii, CRC planszy, współrzędne, liczba skrzyń, liczniki 32-bitowe i CRC16 rekordu. Dwa sloty: sektory 8100/8101. Walidacja zakresów poprzedza indeksowanie mapy w `save_apply`; porównuje też liczbę skrzyń, CRC planszy, teren i nakładanie obiektów. Undo jest zerowane po zimnym wznowieniu.

Odtworzono dwie autentyczne generacje i sprawdzono wybór nowszej. Osobno testowano niepoprawne CRC, wersję, identyfikator, teren, nakładanie, liczbę skrzyń i znacznik finału. Dla uszkodzonego nowszego sektora kilka miejsc ucięcia rekordu pozostawiało do odtworzenia starszy prawidłowy slot. To próby danych na nośniku; fizyczne zerwanie zapisu nie było wykonywane. Write-protect zachowuje oba wcześniejsze sektory i pozostawia pauzę z błędem. Standardowe OS SIO bez patcha wykonało zapis i późniejsze zimne Continue ze zgodnym stanem. Wyjątki w zachowaniu awaryjnym opisują A-02 i A-03. [Próby zapisów](evidence/audit-saves.json).

Cztery testowe obrazy przechodzą pełny boot i inicjalizację, następnie rzeczywiście ładują poziomy 1/16/31/46. Potwierdzono to także przy wyłączonym patchu SIO. Każdy zawiera wszystkie 60 poziomów i ma odmienny save ID: `fc39188b`, `62485ba1`, `f164c7b8`, `eec63655`. Niezgodne zapisy nie są stosowane: normalny→test, test→normalny oraz test-16→test-31. Izolacja dotyczy identyfikacji rekordów; nie są to cztery oddzielne obszary sektorów na jednym wspólnym dysku.

Sprawdzono uszkodzoną planszę, uszkodzoną treść zasobu, CRC-poprawny nagłówek ze sfałszowanym adresem stosu `$8000`, rozmiarem 65535, brak sektorów i błąd odczytu. Wadliwe pakiety nie są aktywowane; retry lub powrót do tytułu działa. Atari800 przy obciętym pliku ATR może zwrócić sukces odczytu zerowych danych, które odrzuca walidacja NSLV — nie utożsamiam tego z zachowaniem fizycznego urządzenia przy krótkim odczycie. [Próby błędów](evidence/audit-errors.json).

### ANTIC, GTIA, DLI/VBI i Energy 02

Plansza korzysta z ANTIC 4; dwa wiersze HUD z ANTIC 2. Ekran `$8800–$8BBF` nie przekracza granicy 4 KB; fonty są wyrównane do 1 KB. Gameplay DL mieści się w `$9F60–$9FFF`, nie przekracza granicy 1 KB. Menu ma jawne LMS dla obrazów `$A000`, `$B000` i `$B400`. Splash przechodzi przez granicę `$B000` za pomocą LMS w wierszu 102; lista `$8800` ma 202 B. Loader używa własnej listy `$BF00`, obrazu `$BA00` i osobnych pól tekstu/progresu. Nie wykazano przekroczenia licznika adresowego ANTIC.

ISR zachowuje rejestry, instaluje font/kolory po WSYNC i dopiero potem wykonuje próbkę wejścia. Gameplay używa sześciu DLI; wartości PF1/PF2 dla wszystkich pięciu pasów planszy są jednakowe w obrębie obszaru. Dekoracja obok planszy nie jest osobną strefą koloru. Nie znaleziono w bieżącym RC2 aktywnego efektu zmieniającego kolor obiektów w zależności od ich wiersza. Diagnostyczny wariant `--band-colors-prototype` nie jest badanym wydaniem.

W RC2 nowe przełączenia palety dotyczą menu i loadera. Prześledzono inicjalizację list, VBI z łańcuchem OS, flagi DMA/loading oraz przejścia UI/gry. Runtime nie ma normalnej ścieżki wyjścia do DOS wymagającej odinstalowania wektorów. SIO wycisza muzykę, a wznowienie odtwarza rejestry POKEY; nie stwierdzono jednoczesnego odtwarzania muzyki podczas operacji dyskowych.

W osobnym oracle rastera, bez istniejących `live()`/`pixel_fast()`, dla każdej nieściennej komórki wyliczono oczekiwany kod i glif robota/skrzyni/celu/podłogi z pakietu oraz porównano faktyczne piksele PNG z paletą obszaru. Sprawdzono **1 833 984 piksele w 146 aktywnych ramkach**, wszystkie 60 poziomów na początku i po rozwiązaniu oraz dodatkowe ramki Energy 02. [Oracle](repro/audit_raster.py), [wynik](evidence/raster-result.json).

**Energy 02:** w ramkach 1241–1265 i 1316 stan jest stabilny: robot `(2,2)`, dwie skrzynie `(3,2)` i `(3,3)`, dwa cele. Kody ekranowe, glify i piksele wszystkich tych obiektów zgadzają się z pakietem. [Ramka 1246](evidence/energy02-frame1246.png), [ramka 1316](evidence/energy02-frame1316.png). Nie odtworzono trwałego problemu. Bez oryginalnego zrzutu z jego RAM/emulator frame nie da się rozstrzygnąć, czy poprzednia obserwacja pochodziła z ładowania, częściowej aktywacji lub innego buildu. Nie oznaczam jej arbitralnie jako potwierdzonego stanu przejściowego.

**„448 taktów”:** od pierwszego `PHA` `native_dli` do `_dli_end`, przed `PLA/TAX/PLA/RTI`. Pomiar obejmuje WSYNC i postoje DMA. Wyklucza końcowe 16 cykli CPU, sprzętowe wejście NMI i dispatch OS. Jest maksimum **jednego wywołania**, nie sumą wszystkich DLI w ramce.

| Faza | Maks. pojedynczego odcinka | Maks. suma odcinków w ramce | Maks. liczba DLI | CPU pojedynczego odcinka, bez postojów |
|---|---:|---:|---:|---:|
| Gra | 448 | 1333 | 6 | 213 |
| Menu | 134 | 325 | 3 | 57 |
| Loader rezydentny | 115 | 209 | 2 | 57 |

Ramka PAL ma w tej emulacji 35 568 taktów. Suma 1333 to około 3,75% ramki dla mierzonych odcinków; należy dodać epilogi i obsługę wejścia NMI. Nie jest to kompletny koszt wszystkich przerwań ani dowód globalnego WCET. [Surowe zestawienie](evidence/audit-dli.json). Najdłuższy zaobserwowany odcinek VBI w pełnej kampanii ma 7527 taktów; sprawdzane rastry nie wykazały spóźnionej publikacji, ale to nadal skończony pomiar.

## 4. Ładowanie i kompatybilność

Uruchomienia były headless: `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`. Argument `-windowed` z historycznego runnera trafia do sterownika dummy i nie otwiera okna. Użyto XL/XE, PAL, RAM=64, BASIC off, MAPRAM off, stereo off i RTC off. Hostowy `-turbo` usuwa pacing gospodarza; nie skraca emulowanych ramek. Zestawy z patchem SIO i z `-nopatch`/`ENABLE_SIO_PATCH=0` są wyraźnie rozdzielone. [Konfiguracja patch](evidence/emulator-patch.cfg), [konfiguracja stock](evidence/emulator-stock.cfg).

Nie ma nowego fast loadera w badanym RC2. Odczyt i zapis korzystają z OS SIOV `$E459`, urządzenia D1, komend R/W i sektorów 128 B. Standardowa ścieżka faktycznie bootowała i zapisywała. Wymagane jest wyłączenie BASIC, bo gra używa `$A000–$BFFF`; instrukcja właściciela to podaje. Nie wykazano zależności od rozszerzonej pamięci.

Pomiary poniżej dotyczą modelu Atari800 z jednym konkretnym ROM-em. Sekundy obliczono z zegarów PAL, **nie z czasu ściennego hosta ani pomiaru Atari/SIO2SD**. I/O to czas od SIOV do powrotu; reszta obejmuje m.in. C, CRC, walidację, VBI i DMA, nie jest samym kosztem instrukcji CPU.

| Operacja | Patch SIO | Standardowe OS SIO, model emulatora |
|---|---:|---:|
| Dekompresja wczesnego bitmapowego splash | 0,364 s | 0,364 s |
| Przygotowanie pierwszej planszy, łącznie | 3,353 s | 8,668 s |
| W tym SIO planszy/zasobów | 0,00038 s | 5,306 s |
| Reszta przygotowania, poza SIO | 3,353 s | 3,362 s |
| Samo `show_play`, wewnątrz przygotowania | 0,151 s | 0,162 s |

Pakiety rozgrywki są nieskompresowane; ich reszta czasu obejmuje głównie kopiowanie, wielokrotne CRC i walidację, a nie dekompresję. Podsumowania nie sumują ponownie `show_play` do `prepare`, ponieważ to zagnieżdżone odcinki. Przy analizie odrzucono przed-mainowe trafienia adresów, pod którymi najpierw działa wczesny bootstrap, a później rezydentny loader. [Pomiar i granice funkcji](evidence/audit-loading.json).

SIO2SD jest głównym celem, ale nie było fizycznego urządzenia do testu. Obraz 8192×128 B i surowe sektory 8100/8101 wymagają obsługi tego rozmiaru i zapisu przez konkretny firmware. **Nie jest to obraz mieszczący się na fizycznej dyskietce 720×256 B. Zgodności CA-2001 nie potwierdzono i nie zakładano.** Nie traktuję tego ograniczenia jako błędu głównej dystrybucji SIO2SD.

## 5. Wiarygodność testów i wykonane próby

Istniejące raporty, komentarze oraz oznaczenia PASS służyły do znalezienia ścieżek kodu, a nie do uznawania ich za poprawne. Rzeczywiste hashe odtworzonych produktów zgadzają się z dostarczonymi obrazami; nowa weryfikacja logiczna i rastera wiąże wyniki z tymi hashami.

Istotne ograniczenia wcześniejszych narzędzi:

- Główny Makefile i jego `make test/target-test` dotyczą starszego prototypu. Ich sukces nie kwalifikuje samodzielnie obecnego ATR-u.
- Wbudowany replay wykonywany przez builder nadal korzysta z `fixture-assets.c`. Sam komunikat udanego buildu nie dowodzi przejścia 60 map CAMP2-B.
- `tools/product1_gauntlet.py` ma historyczny domyślny `product1-campaign.json`. Audyt użył własnego jawnego odczytu CAMP2-B i niezależnych oczekiwań; ten runner wykorzystano tylko jako transport do headless emulatora.
- Nazwy `carry/stress/wrap/counter9/...` w obecnym buildzie nie oznaczają odmiennych executable: wszystkie osiem XEX-ów ma ten sam SHA. PRODUCT1 zastępuje główny plik bez historycznych gałęzi `#ifdef`. Nie zaliczano tych nazw jako osobnych prób liczników; wykonano opisane wyżej próby na dokładnym ATR przez diagnostyczne rekordy.
- Dotychczasowy skończony test ENG4 nie obejmuje okna pomiędzy wejściem do `game_step` a `eng4_accepted`. Test uszkodzonego nowszego slotu bez błędu jego odczytu nie obejmuje A-02.
- W używanym Atari800 log playback zawiera komunikaty `adler32 does not match`: generowany plik bodźców nie zawiera zgodnych nagrań checksum całego stanu. Nie uznano z tego powodu samego playback za dowód; sprawdzano piny/odczyty urządzeń i wynikowy RAM. Nie jest to komunikat CRC gry ani powód do uznania testu za udany bez asercji.

| Próba | Wynik i zakres |
|---|---|
| Czysty build RC2 ×2, RC1, cztery warianty | Odtworzone; dokładna zgodność z dostarczonymi ATR-ami |
| Niezależne rozpakowanie mediów | 60/60 map i pakietów, rozmiary/adresy/CRC/ID |
| Python + C ASan/UBSan + natywne ASM w sim65 | 9741 legalnych kroków, 240 prób kierunku, 60 stanów końcowych, undo256 i wartownicy |
| Pełna kampania z zimnego ATR | 60 wygranych, wszystkie granice obszarów, finał |
| Niezależne piksele komórek | 146 aktywnych ramek, 1 833 984 piksele, wszystkie poziomy |
| Zapis/wznowienie i wadliwe media | Zwykłe ścieżki działają; kontrprzykłady A-02/A-03 |
| Standardowe OS SIO | Pięć obrazów bootuje; normalny zapis i zimny Continue działają |
| Repeat, trzymane undo, pauza, restart, wejście podczas load | Sprawdzone w dokładnym ATR; kontrprzykład A-01 dla konkretnej fazy |
| Granice i zawijanie liczników | Pięć ziaren, zgodny stan i cache HUD po kroku/undo |
| Pamięć/DLI | Mapy i profile instrukcji; bez naruszeń obserwowanego zakresu stosu C |

### NOT_RUN i granice dowodów

- Fizyczny Atari 65XE PAL 64 KB, SIO2SD, jego firmware, zapis na karcie i przerwanie zasilania: brak sprzętu. Częściowy zapis A-02 jest modelem urządzenia na rzeczywistym kodzie 6502.
- Fizyczny CA-2001 i alternatywny format dystrybucji: niewykonane, poza głównym formatem 1 MB.
- Wszystkie rewizje OS, inne urządzenia SIO, NTSC/BASIC on/rozszerzona pamięć: niekwalifikowane; bieżący cel to PAL64/BASIC off.
- Globalny dowód WCET oraz wyczerpanie wszystkich faz IRQ/DLI/VBI i błędów SIO: niewykonane. A-01 pokazuje, dlaczego skończone PASS nie jest takim dowodem.
- Odsłuch muzyki na rzeczywistym POKEY i odbiór kolorów/czytelności na monitorze właściciela: niewykonane. Nie oceniano jakości zagadek ze statystyki solvera.
- Brak oryginalnego zrzutu Energy 02 z powiązanym buildem i RAM: nie ustalono jego pierwotnej przyczyny.

## 6. Minimalne naprawy konieczne przed 1.0

1. **A-01:** zamknąć okno nieoznaczonego wykonywania akcji; zachować semantykę undo dla FIRE zaobserwowanego podczas wygrywającego ruchu. Powtórzyć świadek i przemiatane fazy, także na poziomie 60.
2. **A-02:** przed wyborem slotu do zapisu wymagać kompletnej wiedzy o obu sektorach albo odmówić zapisu. Zweryfikować niezmienność ostatniej poprawnej generacji przy błędach odczytu i częściowym zapisie.
3. **A-03:** jeżeli nadal dostarczane są cztery testowe ATR-y, zrównać ich fallback wznowienia z menu. Zwykły RC2 ma już działające obejście przez tę ścieżkę.

Po zmianach zbudować nowe obrazy w izolacji, nadać im nowe hashe, powtórzyć odpowiednie reprodukcje oraz podstawowy boot/kampanię/save. Nie trzeba zmieniać kampanii, powiększać undo ani wdrażać fast loadera, aby naprawić opisane błędy. Żadna poprawka nie została wykonana w ramach tego audytu.

## 7. Krótki smoke właściciela na Atari

Po naprawach A-01/A-02:

1. Czyste, osobne kopie nowych ATR-ów na SIO2SD; PAL, 64 KB, BASIC wyłączony. Zanotować model/firmware i standard/turbo SIO. Potwierdzić menu i cztery rzeczywiste starty obszarów.
2. Sprawdzić rastry tytułu/loadera/HUD/gry, robota i skrzynie na różnych wysokościach, pchnięcie na cel oraz Energy 02 po 1 i 5 sekundach. Posłuchać powrotu muzyki po load/save.
3. Ruch/undo/repeat, szybkie FIRE przy wygranej, SELECT po wygranej, pauza/resume/restart. Przejścia 15→16, 30→31, 45→46 i finał 60 należy potwierdzić w odbiorze kampanii.
4. Dwa następujące zapisy, zimne Continue, pusty undo po wznowieniu, write-protect i retry. Próby przerwania zapisu wykonywać wyłącznie na przeznaczonych do tego kopiach; ocenić zachowanie faktycznego firmware, nie emulatorowego modelu.
5. Zmierzyć osobno zimny boot, wejście w poziom, restart i resume; zapisać czasy, ustawienia oraz ewentualne pasy/migotanie. Wynik dotyczy wyłącznie faktycznie użytego sprzętu.

## 8. C. Usprawnienia do odłożenia po wydaniu

**C-01 — LOW, potwierdzony koszt zbędnego ponownego ładowania.** `experiments/product1/main.c`, `resume()` linie 21–28, zawsze wykonuje pełne `load_package(1)`, również po pauzie, której UI nie wymaga utraty wszystkich fontów. `board_load()` w `campaign.c`, linie 32–37, ponownie czyta stały katalog kampanii przy każdym ładowaniu. `loader.c` wykonuje CRC sekcji i całego korpusu oraz kopiuje każdy bajt. Mechanizm jest widoczny w kodzie; pomiar pierwszej planszy pozostawia około 3,36 s poza SIO. Nie klasyfikuję tego jako błąd stabilności ani warunek wydania.

Minimalny kierunek: po profilowaniu rozważyć zachowanie rezydentnych zasobów bieżącego poziomu przy pauzie/restartach i tańsze sprawdzanie bajtów. Zachować pełną inwalidację po menu, zmianie poziomu, uszkodzonym pakiecie i zmianie nośnika. Weryfikować te same piksele oraz błąd/retry przy zmianie zasobów. Pomiary nie uzasadniają automatycznego wyboru konkretnego fast loadera.

Warto też wyraźniej oddzielić historyczne polecenia testów i nazwy wariantów od bieżącej kwalifikacji ATR. To utrzymanie narzędzi; nie jest dodatkową blokadą gry.

Reprodukcje i sposób uruchomienia: [REPRODUCE.md](REPRODUCE.md). Pełne duże CSV i komplet RAM/PNG pozostawiono w izolowanej kopii; do repo dołączono małe świadki, wyniki oraz hashe przebiegów. Nie zadeklarowano poprawności na prawdziwym Atari na podstawie emulatora.
