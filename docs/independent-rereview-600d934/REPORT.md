# NEON SHIFT 65 — niezależny re-review A-01–A-03

Data: 2026-10-18. Badany checkpoint: **600d934310b5ffb8e3fbf73a205f15a589a4efa6**.

**A-01: CLOSED. A-02: CLOSED. A-03: CLOSED**, w opisanym niżej zakresie kodu i emulatora. Nie wykryto nowej blokady kodowej wydania. Jest jedna nieblokująca nieścisłość opisu pamięci w raporcie RELEASE1.

To ograniczony re-review napraw po [pierwotnym audycie](../independent-audit-claude/REPORT.md), z odniesieniem do [raportu RELEASE1](../release1/REPORT.md). Nie powtarzano pełnego audytu, kampanii 60 poziomów, kwalifikacji grafiki ani odbioru właściciela.

## Badane obrazy i izolacja

Źródła oraz dostarczone ATR-y pobrano przez `git archive 600d934` do nowego katalogu `/private/tmp/neon-rereview-600d934-ucaikpu5/tree`. Nie odziedziczono obiektów ani buildów. Osobno skopiowano istniejącą binarkę obserwatora Atari800 i lokalny config ROM. Wszystkie uruchomienia emulatora miały `SDL_VIDEODRIVER=dummy` i `SDL_AUDIODRIVER=dummy`, PAL, 64 KB, BASIC/MAPRAM off. Historyczne `-windowed` trafiało do sterownika dummy. Nie uruchamiano GUI.

Wykonano pięć nowych buildów z tego checkpointu. Każdy wynik jest **bajtowo identyczny** z odpowiednim ATR-em wyjętym z commitu oraz ma ten sam SHA-256 co zastany plik właściciela. To wiąże testy z rzeczywistym checkpointem; nie przyjęto deklaracji PASS jako dowodu pochodzenia. Wszystkie obrazy mają 1 048 592 B, 8192 sektorów po 128 B i 16 B nagłówka.

| Obraz RELEASE1 | SHA-256 czystego obrazu |
|---|---|
| `neon-shift65-v1.0-candidate.atr` | `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82` |
| `neon-shift65-v1.0-test-01.atr` | `a52bbcd758d408b711250d93b0cd92c90fb7e32529f45cb37cad2394ff5ff676` |
| `neon-shift65-v1.0-test-16.atr` | `b1f0495504e26aa836115a460b37760f41e18fab4ef386f87f174fe14a88e1ae` |
| `neon-shift65-v1.0-test-31.atr` | `44c24ec48f436e4f40bb2bb972f983a2057d8dfc73c3694fa68a468cd45d25dd` |
| `neon-shift65-v1.0-test-46.atr` | `956f51e462b4bd8ce65ffbf60f0194ff650400046962a35945b333f703724aec` |

Kontrolę dodatnią pierwotnych reprodukcji wykonano na świeżych historycznych buildach:

| Obraz kontrolny | SHA-256 |
|---|---|
| RC2 zwykły | `f76a11e76a5a1f6cc4426104c59804cd614c6aa62022f51572d9474c2230acc0` |
| RC2 test-16 | `57e9551504dd7635dcd0665b0d8c29e83139f972d9d39bb8a4aa1583108a1830` |
| RC1 zwykły, świadek A-01 | `6ba10996b4150ac170a61aec529b350c8af7c310ed53d8150da2b63c888397c8` |

Źródła RC2 odtworzono z `docs/release1/source-inputs.zip`, katalog `rc2/`. Spośród 212 wpisów 211 zgadza się z hashami snapshotu pierwotnego audytu; jedyny odmienny wpis to przenośny config emulatora. Kod wejściowy nie różni się od snapshotu, a trzy powyższe ATR-y mają dokładne hashe audytu. Obserwator ma SHA-256 `bc8703dfd499dae210c07381c4600c4b3c2d31c26de142701b9f9cbf55195c82`; cc65/cl65/ca65/ld65/sim65 zgłaszają V2.18. ROM-y tylko odczytywano; ich hashe są w [environment.json](environment.json).

Emulator zawsze montował kolejną kopię pod `/private/tmp`. Modyfikacje rekordów, uszkodzenia pakietu i write-protect dotyczą wyłącznie tych kopii. [Manifest 154 uruchomień](image-runs.json) zapisuje hash ATR-a **przed i po** każdej próbie: 149 dla RELEASE1 oraz 5 kontroli historycznych. Obejmuje także obrazy z celowo zmienionymi zapisami. [Recepty 85 różnych obrazów wejściowych](input-image-recipes.json) zawierają bazowy hash, nagłówek i zmienione sektory, pozwalając odtworzyć te wejścia bez zapisu na oryginałach.

## Rzeczywisty zakres zmian

Checkpoint 0750a61 wprowadza naprawy audytu i zachowuje lokalne wejścia FINISH2. 21a2b25 dodaje końcową nakładkę grafiki oraz ponowne użycie zasobów po pauzie. 600d934 dostarcza obrazy i dowody; zawiera także zmiany narzędzi kwalifikacji. Ponowne buildy potwierdzają ich zgodność z dostarczonym produktem.

Porównanie wygenerowanych wejść produkcyjnych RC2 i końcowego zwykłego obrazu wykazało zmiany wyłącznie w `main.c`, `campaign.c` i `display.c` — [pełny diff](generated-source.diff). W `main.c` zmieniono moment ustawienia busy, wspólną ścieżkę Continue/autostartu oraz `play()`/`resume()`. `campaign.c` dodaje jeden bajt licznika poprawnych odczytów i warunek kompletnego skanu przed zapisem. `display.c` dopuszcza nową paletę Energy/Data. Nakładka offline zmienia ponadto glify ścian/dekoracji i palety w pakietach graficznych.

Wygenerowane `hardware.s`, `input.c`, `render.s`, `phase.s`, `move.s`, `undo-fast.s`, `sio.s`, `loader.c` i `link.cfg` są bajtowo identyczne z RC2. Wszystkie 60 sektorów plansz NSLV i katalog NSCD pozostały identyczne. Nie traktowano pomocniczego replaya fixture’ów uruchamianego przez builder jako nowego dowodu przejścia kampanii.

## A-01 — CLOSED

**Dowód pierwotny.** Uruchomiono niezmieniony `audit_fire_proof.py`: na RC2 i RC1 ponownie uzyskał niepożądane przejście do sceny 1. Na RELEASE1 ta sama asercja błędu zawodzi, ponieważ wykonuje się undo. Oddzielna walidacja sprawdziła rzeczywiste odczyty TRIG0, wejścia/wyjścia funkcji i stan opublikowanego obrazu; sam niezerowy exit starego testu nie był kryterium zamknięcia.

| Zdarzenie na zwykłym RELEASE1, te same piny audytu | Zegar ANTIC/CPU |
|---|---:|
| Wywołanie ustawiające busy | 40 514 767 |
| Wejście do `game_step` | 40 514 872 |
| Zewnętrzne FIRE | 40 516 352 |
| Faktyczny odczyt TRIG0=0 wewnątrz `game_step` | 40 516 729 |
| Wyjście z `game_step` | 40 517 204 |
| Wejście do skutecznego undo | 40 624 928 |

`input_read` oddaje SELECT=7, zachowując intencję undo; nie oddaje FIRE=5 w tym oknie. Pełne obrazy pchnięcia i cofnięcia występują osobno w rastrach **1141 i 1144**. Stan końcowy: scena 0, moves=1, gracz `(3,2)`, skrzynia `(4,2)`. Nie występuje dodatkowe świeże zbocze FIRE po gotowości.

**Testy celowane: 43 przebiegi.** Ponowiono 25 prób RELEASE1: świadek z pełnym śladem fetch, 17 przesunięć kierunku −600…+600 taktów co 75 wokół DLI, skuteczny ruch niewygrywający, 5 faz odrzuconego ruchu oraz świeży FIRE po gotowości. Dodano 12 niezależnych przesunięć FIRE: +3100, 3400, 3700, 4000, 4300, 4600, 4900, 5200, 5600, 9000, 18000 i 30000 taktów od wspólnej bazy; każde daje jedno skuteczne pchnięcie i jedno undo. Odrzucone ruchy zwalniają busy, a FIRE nadal cofa poprzedni skuteczny ruch. Świeży FIRE po ponownym rozwiązaniu przechodzi do następnego poziomu.

Na rzeczywistym poziomie 60 wykonano 5 faz wygrywającego ruchu i dodatkową próbę świeżego FIRE. Seed to poprawny rekord zapisu po legalnym prefiksie 175 kroków rozwiązania CAMP2-B, wczytany przez normalne Continue, bez podmiany RAM. Ruch 176 rozwiązuje poziom; FIRE zaobserwowany w `game_step` cofa do moves=175, phase=1, scene=59. Pełne rastry ponownie wynoszą 1141/1144. Osobne ponowne rozwiązanie i świeży FIRE dają phase=10 oraz save_complete=1.

**Publikacja i wejście.** Sprawdzono oracle faktycznych fetch ANTIC oraz planszę/HUD w trzech świadkach: wygrywający, niewygrywający i finał. Dodatkowo adaptacja niezależnego oracle pierwotnego audytu porównała 42 496 pikseli podłogi, robota, skrzyń i celów w sześciu pełnych rastrach z pakietami badanego ATR-a, używając końcowej palety. Stan obiektów i liczników zgadza się z wynikami skutecznych akcji w CSV. Maksima trzech świadków: przyjęcie ≤3,060 PAL, przyjęcie→pełny obraz ≤1,562 PAL, bodziec→pełny obraz ≤4,518 PAL.

**Ograniczenia.** Jest to skończona macierz faz na jednym modelu emulatora/ROM-u, bez dowodu wszystkich przeplotów IRQ/NMI i bez odbioru fizycznego joysticka. Próba niewygrywająca obejmuje FIRE podczas publikacji, a dwa świadki wygrywające mają potwierdzony odczyt FIRE wewnątrz samego `game_step`.

Dowody: [niezależna walidacja CSV i pikseli](independent-validation.json), [25 prób bazowych](fire-tests.json), [12 faz FIRE](fire-phases.json), [finał 60](finale.json), surowe ślady/RAM/PNG w [evidence.zip](evidence.zip).

## A-02 — CLOSED

**Dowód pierwotny.** Niezmieniony `audit_fault.py` ponownie wykazał na RC2 nadpisanie sektora 8101 i odzyskanie moves=1 zamiast ostatniego moves=2 po częściowym zapisie. Na końcowym wygenerowanym `campaign.c` z rzeczywistym `crc.s` stary harness zatrzymuje się na asercji oczekującej zapisu do 8101: zarejestrowany target wynosi **0**, czyli nie wywołano `sio_write`. To oczekiwana zmiana zachowania.

**Macierz sim65 została uruchomiona ponownie i przeczytana.** 1088 przypadków obejmuje obie lokalizacje nowszego slotu, generacje 2, 0, 65535 i 1, błąd każdego slotu oraz obu slotów, write-protect, poprawny zapis i wszystkie długości częściowego zapisu 0–127 B. Dla niekompletnego skanu test wymaga writes=0, błędu 4 i niezmienności obu rekordów. Gdy skan jest kompletny, częściowy zapis dotyczy starszego slotu; najnowszy wcześniejszy rekord zachowuje wszystkie 128 bajtów, a po ponownym skanie odzyskiwane jest moves=2. Poprawny pełny zapis odzyskuje moves=3. Asercje sprawdzają również skończoną liczbę odczytów.

**Dodatkowa kontrola gotowego ATR-a: 16 przebiegów.** Nowszy rekord umieszczano w każdym slocie, z czterema powyższymi generacjami, i oddzielnie wywoływano błąd odczytu 8100 albo 8101. Continue odzyskuje czytelny rekord. Następnie pauza→zapis kończy się phase=3/save_error=4; **cały roboczy ATR jest identyczny bajtowo z wejściem**, w tym oba sloty. Ślad zawiera po dwa odczyty slotów przy Continue i po dwa przy zapisie, z oczekiwanymi błędami — bez niekończącego się ponawiania. Zwykły write-protect, dwa kolejne zapisy i zimne Continue również ponowiono w macierzy runtime.

Naprawa zachowuje rozróżnienie: awaryjny odczyt może użyć czytelnego slotu, ale wybór sektora do zapisu wymaga wiedzy o obu slotach. Nowy bajt `save_read_ok` jest zerowany przy każdym skanie i nie zależy od nieaktualnego `save_error`.

**Ograniczenia.** Wszystkie długości częściowego zapisu wykonuje model interfejsu SIO w sim65 na rzeczywistym kodzie 6502. Nie jest to przerwanie zasilania karty SD ani kwalifikacja atomowości firmware SIO2SD. W emulatorze Atari800 sprawdzono odmowę zapisu przy awarii odczytu i rzeczywiste zachowanie całych rekordów.

Dowody: [1088 przypadków](save-faults.json), [16 prób ATR](disk-errors.json), [odczyty i DLI](postchecks.json), harness C i logi oryginalnej oraz końcowej próby w [evidence.zip](evidence.zip).

## A-03 — CLOSED

**Dowód pierwotny.** Niezmieniony `audit_test_resume.py` na historycznym test-16 ponownie utknął w phase=6/error=0 i odzyskał starszy zapis dopiero przez menu. Na końcowym test-16 zimny autostart od razu daje phase=1, scene=15, moves=3, undo=0, save_error=0. Stara asercja oczekująca phase=6 zawodzi z tej konkretnej przyczyny.

**Wszystkie cztery końcowe ATR-y.** Ponownie wykonano 59 prób `release1_runtime.py saves`, obejmujących rzeczywiste zapisy i zimne wznowienia. W każdym testowym obrazie sprawdzono nowszy rekord z graczem na ścianie, złą liczbą skrzyń i niezgodnym CRC planszy. Dla każdego rodzaju odrzucenia nowszy rekord znajdował się raz w 8100, raz w 8101; starszy miał generację 65535, nowszy 0. Wszystkie **24 kombinacje fallbacku** odzyskują zgodne współrzędne, skrzynie i liczniki starszego zapisu, bez błędu. Rekordy są CRC-poprawne na poziomie sektora; odrzucenie semantyczne następuje dopiero przy stosowaniu do planszy.

W każdym wariancie oba semantycznie błędne rekordy dają phase=8/save_error=2, a świeży FIRE wraca do tytułu. Pusty obraz rozpoczyna przypisany poziom 1/16/31/46; cztery takie zimne starty wykonano także przez zwykłe OS SIO z wyłączonym patchem. Zwykły obraz nadal startuje z menu. Dodatkowe 6 prób zwykłego menu potwierdza fallback przy błędnym terenie, CRC planszy i CRC rekordu w obu kolejnościach slotów.

**Izolacja.** Dodatkowy harness sprawdził wszystkie **20 skierowanych par** pomiędzy zwykłym obrazem i czterema testowymi obrazami. Żaden cudzy rekord nie został przyjęty: phase=8/save_error=2, wejściowy ATR niezmieniony. Identyfikatory pięciu namespace są różne. Dotyczy to także każdego testu względem pozostałych trzech, a nie tylko jednej pary reprezentatywnej.

**Ograniczenia.** Obejmuje wskazane klasy uszkodzeń semantycznych i formatowych; nie jest fuzzingiem wszystkich 128-bajtowych rekordów. Błędy pakietu zasobów pozostają oddzielną ścieżką phase=6. Nie zamieniano błędu nośnika/zasobów w dowód uszkodzenia save.

Dowody: [59 prób save/start/I/O](saves-tests.json), [pełna izolacja](isolation.json), [zwykły fallback](normal-fallback.json), [ponowione oryginalne reprodukcje](original-runs.json), [stany naprawionej reprodukcji](original-fixed-runtime.json).

## Bezpośrednie skutki dla pamięci, DLI i błędów

Mapy linkera wszystkich pięciu nowych buildów nie wykazują nakładania segmentów ani przekroczenia regionów. `link.cfg` jest identyczny z RC2. [Zestawienie pamięci](scope-memory.json):

| Obszar | RC2 zwykły | RELEASE1 zwykły | Każdy RELEASE1 testowy |
|---|---:|---:|---:|
| MAIN wolne | 68 B | 38 B | 18 B |
| LOW wolne | 18 B | 18 B | 18 B |
| ZP wolne | 52 B | 52 B | 52 B |
| PERSIST wolne | 249 B | 248 B | 248 B |
| Stos C zarezerwowany | 2048 B | 2048 B | 2048 B |
| Stos sprzętowy | 256 B | 256 B | 256 B |

Undo pozostaje 256 kroków. W 149 przebiegach RELEASE1 obserwator wykazał szczyt 21 B stosu C, 36 B stosu sprzętowego i zero próbek poza rezerwą stosu C. To pomiar tych ścieżek, nie globalny dowód maksimum.

Źródło DLI nie zmieniło się. Te same piny świadka A-01 przechodzą teraz przez istniejącą gałąź undo: maksimum mierzonego odcinka DLI rośnie z 464 do 482 taktów ANTIC i z 219 do 226 cykli CPU; maksymalna suma odcinków w rastrze 1325→1339. Granice: pierwsze PHA `native_dli`→`_dli_end`, przed epilogiem; pomiar nie obejmuje całego NMI ani nie dowodzi WCET.

Pauza→konfiguracja→pauza→resume zachowuje GameState i przywraca prawidłowy pełny obraz. Zbadano bezpośrednio bajty dziewięciu sekcji zasobów; dynamiczne banki robota zachowują się zgodnie z zatrzymaniem animacji w UI. Próba wadliwego pakietu daje phase=6, ponowny FIRE pozostaje w phase=6, START wraca do menu, a niepełna plansza nie jest aktywowana. Nie powtarzano całej kampanii dla tych lokalnych zmian.

**N-01 — nieblokująca korekta dokumentacji.** Zdanie RELEASE1, że pauza/konfiguracja „nie zapisują żadnej z dziewięciu sekcji pakietu gry”, jest zbyt szerokie. Sekcja `$9DE0`, długość 544 B, obejmuje również roboczy obszar display listy `$9F60–$9FFF`. UI zmienia tam 24 bajty. Wykonany test potwierdza, że właściwe 384 B deskryptora `$9DE0–$9F5F` pozostają identyczne, a po `show_play()` cały badany zakres 544 B jest odtworzony identycznie. Nie wykazano przez to błędu `loaded` ani kolizji pamięci. Wystarczy doprecyzować opis rezydentnych danych i odbudowy display listy; w tym re-review nie zmieniano dokumentu źródłowego ani kodu. [Dowód adresowy](descriptor-workspace.json).

## Odtworzenie i zachowanie wejść

Archiwum [evidence.zip](evidence.zip) zawiera nowe logi buildów, mapy/etykiety/linker config, wybrane surowe CSV/RAM/PNG, wejścia playback, oryginalne reprodukcje oraz dodatki harnessu `rereview_*.py`. Nie zawiera ROM-u ani binarki emulatora. Pełne duże ślady pozostają w odizolowanym katalogu podanym wyżej.

Po odtworzeniu checkpointu w nowej kopii z lokalnym obserwatorem/configiem zbuduj pięć obrazów poleceniami z raportu RELEASE1. Następnie wykonaj `release1_faults.py build/release1/final`, `release1_fire.py --build build/release1/final` i `release1_runtime.py saves`. Dodatki z archiwum uruchamia się w korzeniu izolowanej kopii: `rereview_targeted.py finale`, `disk_errors`, `isolation`, `side_effects`, potem `rereview_fire_phases.py`, `rereview_normal.py`, `rereview_validate.py`. Kontrole historyczne wymagają dodatkowych buildów RC2/RC1 z zachowanego katalogu `rc2/`; `rereview_original.py` przełącza wyłącznie prywatne dowiązania w `build/`. Nie wykonywać tych poleceń w obszarze właściciela.

Przy tworzeniu harnessu skorygowano trzy założenia testera: rozwiązany odzyskany save ma phase=2; ruch niewygrywający kończy się przed wybranym FIRE; pakiet deskryptora zawiera dynamiczną display listę. Wstępne nieudane asercje i poprawione przebiegi są zachowane w logach. Nie wymagało to zmiany produktu. Wyniki zamknięcia odnoszą się do poprawionych, wykonanych kontroli i ich surowych stanów.

Oryginalne pliki kodu i ATR-y właściciela nie zostały zmienione. Końcowa kontrola zachowania jest w [preservation.json](preservation.json); [SHA256SUMS](SHA256SUMS) obejmuje cały nowy katalog raportu. Bez commit, push, tagowania i publikacji.

## Blokady wydania i granice odbioru

**Nowe blokady wydania: brak wykrytych w zakresie re-review.** A-01 i A-02 nie wymagają dalszej naprawy na podstawie wykonanych reprodukcji; A-03 jest zamknięte także dla wszystkich czterech dostarczonych wariantów testowych. N-01 jest korektą opisu, bez potwierdzonej usterki działania.

Wcześniejsze odbiory sprzętu, wyglądu/sterowania i odsłuchu pozostają po stronie właściciela. Statusu praw OPEN nie badano ani nie zmieniano. Nie deklaruję odbioru Atari/SIO2SD, fizycznego przerwania zapisu SD ani akceptacji wyglądu za właściciela.
