# RELEASE1 — NEON SHIFT 65, kandydat 1.0

Data: 2026-10-18. **Kandydat gotowy do końcowego odbioru właściciela.**
Kwalifikacja emulatora: **PASS w opisanym zakresie**. Sprzęt Atari/SIO2SD:
**OWNER_PENDING**. Akceptacja wyglądu: **OWNER_PENDING**. Prawa: **OPEN**.
Bez push, publikacji, merge do main i tagu wydania. Funkcje są [zamrożone](FREEZE.md).

## Obrazy do odbioru

**Dokładnie jeden zwykły obraz do odbioru:**
[neon-shift65-v1.0-candidate.atr](neon-shift65-v1.0-candidate.atr).
Cztery pomocnicze obrazy uruchamiają pełny boot i I/O, następnie poziom
1/16/31/46. Zawierają ten sam silnik, 60 map i zasoby graficzne. Różnice
programowe ograniczają się do konfiguracji startu i osobnej tożsamości save.
Wszystkie pliki mają 1 048 592 B (8192 sektory po 128 B + nagłówek ATR).
Sumy dotyczą czystych dysków; graj na kopii.

| ATR | Początek | SHA-256 |
|---|---|---|
| [neon-shift65-v1.0-candidate.atr](neon-shift65-v1.0-candidate.atr) | menu | `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82` |
| [neon-shift65-v1.0-test-01.atr](neon-shift65-v1.0-test-01.atr) | 1 | `a52bbcd758d408b711250d93b0cd92c90fb7e32529f45cb37cad2394ff5ff676` |
| [neon-shift65-v1.0-test-16.atr](neon-shift65-v1.0-test-16.atr) | 16 | `b1f0495504e26aa836115a460b37760f41e18fab4ef386f87f174fe14a88e1ae` |
| [neon-shift65-v1.0-test-31.atr](neon-shift65-v1.0-test-31.atr) | 31 | `44c24ec48f436e4f40bb2bb972f983a2057d8dfc73c3694fa68a468cd45d25dd` |
| [neon-shift65-v1.0-test-46.atr](neon-shift65-v1.0-test-46.atr) | 46 | `956f51e462b4bd8ce65ffbf60f0194ff650400046962a35945b333f703724aec` |

[Sumy ATR](SHA256-ATR.txt), [instrukcja PL/EN](PLAYER-GUIDE-PL-EN.md),
[krótki smoke sprzętowy](HARDWARE-SMOKE.md), [autorzy i licencje](CREDITS-LICENSES.md).
Launcher: `python3 tools/release1_owner_smoke.py` albo
`docs/release1/PLAY-WINDOWED.command`. Jawne WINDOWED, OS SIO, osobny config
oraz roboczy ATR. Agent wykonał wyłącznie headless i launcher `--check`.

## Stan źródeł i pochodzenie

Punkt wyjścia: `ea4f4159c7bc8364825af55879a07f1f93c95520` **plus zastany
working tree FINISH2/RC2**, sześć zmian tracked i wymagane źródła untracked.
Nie cofano do RC1. W repo i przodkach nie znaleziono AGENTS.md; przeczytano
PROJECT_BRIEF, README, architekturę, kontrakt ENG4 i audyt z reprodukcjami.
[Preflight](preflight.json) obejmuje 6307 zastanych plików.
[Kontrola zachowania wejść](preservation.json): zero nieautoryzowanych zmian.
Pozostałe eksperymenty, referencje właściciela i jego dawne artefakty pozostały
poza checkpointami RELEASE1.

Checkpoint napraw: `0750a61b61594d749066fe98123a89211883ec72`.
Zamrożona implementacja produktu: `21a2b25`.
[Dokładne wejścia](build-inputs.json) wiążą pełny commit i hashe plików;
[source-inputs.zip](source-inputs.zip) zachowuje te wejścia i wygenerowane C/ASM,
linker mapy/etykiety oraz pakiety grafiki. Późniejsze zmiany narzędzi kwalifikacji
(analiza zimnego prefiksu, podmiana D1), raporty i checkpoint dostarczenia nie
zmieniają bajtów produktu.

Kampania `assets/levels/camp2-b/campaign.json` zachowana **byte-for-byte**:
`131c57e2692ffe121392e1260c13060960ac8f54425dd870dea28114cd6dae39`.
Normalny save ID `131c57e2`. Testowe namespace pozostały z FINISH2, osobne dla
każdego startu. Zimne bootowanie i wznowienie nie pomijają inicjalizacji ani I/O.
Wszystkie sektory NSLV oraz katalog NSCD są identyczne z audytowanym RC2;
całe 60 rekordów i pakietów NSRQ sprawdzono niezależnym CRC i parserem.
Historyczne fixture'y nie zastępują kampanii w wydawanym ATR.

Dwa źródłowe snapshoty bez odziedziczonych buildów dały dwa bajtowo identyczne
normalne ATR-y. Odtworzony RC2 także ma dokładnie hash audytu
`f76a11e76a5a1f6cc4426104c59804cd614c6aa62022f51572d9474c2230acc0`.
Toolchain i prywatne hashe ROM/obserwatora: [tools.json](tools.json).
Nie dystrybuujemy ROM-u ani emulatora. Istniejące ostrzeżenie linkera o
rozmiarze adresu `__EXEHDR__` pochodzi z zastanego nagłówka; nie ma overflow
regionów. Komplet logów budowy jest w archiwum dowodów.

## Naprawy audytu

| Ustalenie | Zmiana i wynik |
|---|---|
| **A-01 — PASS** | `eng4_accepted()` przed `game_step` i `undo_pop`. Wynik odrzuconej próby zwalnia busy; bezczynna pętla zachowuje barierę pełnego rastra. FIRE odczytany wewnątrz akcji zachowuje intencję undo. |
| **A-02 — PASS** | `save_scan()` zachowuje liczbę udanych odczytów w osobnym bajcie PERSIST. Continue nadal może odzyskać czytelny slot; zapis wymaga **dwóch** udanych odczytów. Brak zapisu do nieodczytanego slotu i brak nieskończonego retry. |
| **A-03 — PASS** | Menu i autostart używają jednej `continue_saved()`, z jedną próbą starszego slotu po odrzuceniu semantycznym nowszego. Pusty testowy nośnik rozpoczyna przypisany obszar; niepoprawny istniejący save prowadzi do phase=8 i właściwego komunikatu, FIRE wraca do tytułu. |

**A-01, rozstrzygający świadek:** niezmienione piny audytu, FIRE rzeczywiście
odczytany przez DLI wewnątrz `game_step`. Funkcja busy zaczyna się przy
40 514 767; game_step 40 514 872–40 517 204. Pchnięcie ma pełny raster
1141, cofnięcie 1144. Scena pozostaje 0, moves=1. RC2 przy tych samych pinach
przechodził do sceny 1. [Świadek i zegary](evidence/audit-witness-proof.json).
17 faz kierunku wokół DLI, pięć prób zablokowanych, osobny skuteczny ruch
niewygrywający oraz świeży FIRE po gotowości: PASS. Na rzeczywistym poziomie
60: pięć faz i odczyt FIRE wewnątrz kończącego ruchu; osobne rastry 1141/1144,
cofnięcie do gry zamiast finału. [Świadek finału](evidence/finale-fire-proof.json).
Pełny obraz wyznacza oracle rzeczywistych ANTIC fetch, banków, obiektów i HUD;
nie polegano wyłącznie na logicznych dumpach RAM. Maksima w trzech świadkach
mieszczą się w ENG4 6/4/10 PAL: przyjęcie około 3,06 PAL, od przyjęcia do
pełnego obrazu około 1,57 PAL, od zewnętrznego bodźca około 4,52 PAL.

**A-02:** 1088 przypadków w sim65 na końcowym wygenerowanym `campaign.c`
i rzeczywistym `crc.s`: oba sloty osobno i naraz, oba porządki generacji,
2/0/65535/1 (w tym wrap), wszystkie 128 długości częściowego zapisu,
write-protect i udany zapis. Ostatnia poprawna generacja zachowana bajtowo.
W gotowym ATR: awaria odczytu każdego slotu zwraca SAVE FAILED bez zmiany
**jakiegokolwiek bajtu obu slotów**. Zabezpieczenie zapisu także zachowuje
oba rekordy. Dwa rzeczywiste kolejne zapisy i zimne Continue: PASS.
Model częściowego zapisu w sim65 nie jest fizycznym przerwaniem zapisu SD.
[Macierz i log](evidence/save-faults.json), [kod harnessu](evidence/save-faults.c).

**A-03:** wszystkie cztery testowe ATR-y, oba położenia nowszego rekordu,
wrap 65535→0, gracz na ścianie, zła liczba skrzyń, zły CRC planszy, poprawny
starszy stan i oba stany niepoprawne: PASS. Normalne menu dodatkowo sprawdzono
z błędnym CRC rekordu, terenem i CRC planszy w obu położeniach slotów.
Brak poprawnego save daje phase=8 / save_error=2, bez pętli błędnego Retry.
Normal ↔ test oraz test ↔ inny test: zapis nie jest przyjmowany.
[59 prób save/start/I/O](evidence/saves-tests.json),
[normalny fallback](normal-fallback.json).

## Jedna runda grafiki

Najpierw obejrzano rzeczywiste natywne PNG RC2. Zachowano industrialny styl,
całą planszę bez przewijania, podłogę RC2 i ograniczone jasne wnętrza dekoracji.
Sylwetki robota, zamkniętego kontenera, pustego doku i kontenera z oznaczeniem
zadokowania pozostają rozróżnialne; wszystkie 40 klatek robota jest bajtowo
identycznych z RC2. Nie przebudowano renderera ani menu. Wybór i hierarchia
menu, trzy jego DLI i dwa DLI loadera pozostają z FINISH2.

Zmiany są jedną nakładką offline: zamknięte metalowe łączenia ścian, krótsze
szczeliny wentylacji i ciągłe obramowania paneli. Drobne czarne zagłębienia
nie przecinają konstrukcji jak przejście. Energy ma przygaszony żółty/mosiężny
PF1 `$EA`; Data fuksję `$4A`. Hydro `$BA` i Reactor `$3A` zachowane.
PF0 skrzyń `$EE`, ciemna stal i szare tło pozostają. Nie ma dodatkowych pasów,
zmian palety w połowie obiektów, nowego efektu w grze ani nowych banków.

Porównania tych samych poziomów i stanów **przed / po** z dwóch pełnych
zimnych replayów, z identycznymi pinami i configiem:

| Obszar | Stan początkowy | Stan rozwiązany |
|---|---|---|
| Energy 09 | [natywnie](screenshots/level-09-initial-before-after-1x.png) / [3× NN](screenshots/level-09-initial-before-after-3x.png) | [natywnie](screenshots/level-09-solved-before-after-1x.png) / [3× NN](screenshots/level-09-solved-before-after-3x.png) |
| Hydro 24 | [natywnie](screenshots/level-24-initial-before-after-1x.png) / [3× NN](screenshots/level-24-initial-before-after-3x.png) | [natywnie](screenshots/level-24-solved-before-after-1x.png) / [3× NN](screenshots/level-24-solved-before-after-3x.png) |
| Data 39 | [natywnie](screenshots/level-39-initial-before-after-1x.png) / [3× NN](screenshots/level-39-initial-before-after-3x.png) | [natywnie](screenshots/level-39-solved-before-after-1x.png) / [3× NN](screenshots/level-39-solved-before-after-3x.png) |
| Reactor 54 | [natywnie](screenshots/level-54-initial-before-after-1x.png) / [3× NN](screenshots/level-54-initial-before-after-3x.png) | [natywnie](screenshots/level-54-solved-before-after-1x.png) / [3× NN](screenshots/level-54-solved-before-after-3x.png) |

[Menu](screenshots/menu-before-after-3x.png), [loader](screenshots/loader-before-after-3x.png).
[Manifest zrzutów](screenshots.json) wiąże niezmodyfikowane PNG 336×240,
stan gry i numery klatek. Powiększenia wyłącznie integer nearest-neighbour;
podpisy leżą poza obrazem gry. Ostateczny wygląd: **OWNER_PENDING**.

## Ładowanie i ważność zasobów

Nie implementowano fast loadera. `loaded==1` może powstać wyłącznie po
kompletnej walidacji pakietu gry. Każde `load_package()` najpierw zeruje ten
znacznik; menu kończy się `loaded=4`, błąd pozostawia 0. `prepare()` zeruje go
przed odczytem planszy. Pauza/konfiguracja zmieniają SCREEN/HUD i roboczą display listę
`$9F60–$9FFF`, które `show_play()` odbudowuje. Właściwy deskryptor
`$9DE0–$9F5F` (384 B) pozostaje zachowany. Re-review potwierdził identyczne
odtworzenie całego badanego zakresu 544 B po `show_play()` (korekta N-01).
Zwykłe `resume()` używa więc zachowanych zwalidowanych danych. Menu, zmiana
poziomu i nieudane I/O nadal przechodzą pełne ładowanie z CRC i walidacją.
Lokalne wydzielenie wspólnego `play()` odzyskało miejsce bez zmiany rezerw.

| Ten sam etap / emulowane OS SIO | RC2 całość / SIO / reszta [s] | RELEASE1 całość / SIO / reszta [s] |
|---|---:|---:|
| Pierwsze przygotowanie planszy | 8,668 / 5,306 / 3,362 | 8,668 / 5,307 / 3,361 |
| Wznowienie po zwykłej pauzie | 8,428 / 5,158 / 3,269 | 0,164 / 0 / 0,164 |
| Wznowienie po menu | 8,428 / 5,157 / 3,271 | 8,428 / 5,158 / 3,269 |

Dla skróconego serwisu SIO emulatora ten sam resume: 3,293 / 0,0004 / 3,293
→ 0,164 / 0 / 0,164 s. To osobny tryb pomiaru, nie sprzętowy fast loader.
Zegar ANTIC_CPU_CLOCK, 35568 taktów/raster, 49,8607597 PAL/s. SIO: wejście
SIOV→powrót; reszta zawiera CRC, kopiowanie, renderer, przerwania, DMA i
oczekiwanie na raster, nie wyłączny koszt instrukcji CPU. Nie sumujemy etapów
zagnieżdżonych. **Czasy modelu Atari800 nie są czasami prawdziwego Atari/SIO2SD.**
[Surowe rozdzielenie czasu](loading.json).

Rzeczywista podmiana D1 w headless przez normalne API urządzenia emulatora,
podczas pauzy: resume zachowuje prawidłowy obraz RAM; późniejszy restart
odczytuje podmieniony pakiet i poprawnie go odrzuca. START wraca do menu.
Prywatny opt-in fixture nie zmienia RAM ani kodu gry.
[Dowód podmiany](media-swap.json). Poprawność po menu, restarcie, błędzie,
nowym poziomie i przejściach obszarów sprawdzona na końcowych ATR-ach.

## RAM, stosy, raster i DLI

| Build | MAIN wolne | LOW wolne | ZP wolne | PERSIST wolne | Ogon muzyki |
|---|---:|---:|---:|---:|---:|
| final | 38 | 18 | 52 | 248 | 18 |
| test-1 | 18 | 18 | 52 | 248 | 18 |
| test-16 | 18 | 18 | 52 | 248 | 18 |
| test-31 | 18 | 18 | 52 | 248 | 18 |
| test-46 | 18 | 18 | 52 | 248 | 18 |

Granice linkera i wszystkich regionów pozostają z RC2. Stos C **2048 B**,
stos sprzętowy **256 B**, undo **256 kroków**. Nie odebrano pamięci stosom
ani buforom bezpieczeństwa. Nowy bajt stanu skanu korzysta z wolnego PERSIST.
Minima wolnych glifów banków: **42 / 32 / 55 / 53 / 10**, po rezerwie robota.
Obserwowane szczyty 107 prób: **21 B C / 36 B sprzętowego**, zero próbek
poza stosem C. To obserwacja ścieżek, nie dowód globalnego WCET/stosu.
[Mapy, zakresy i wyniki](verification.json).

Handler DLI, akwizycja wejścia i kod renderera/undo/SIO są źródłowo identyczne
z RC2. Liczby poniżej mają zawsze te same granice: pierwszy PHA w native_dli
→ `_dli_end`, przed PLA/TAX/PLA/RTI. Upływający zegar ANTIC obejmuje WSYNC
oraz DMA; osobno liczymy cykle CPU. Pomiar **nie** obejmuje końcowych 16 cykli
CPU ani wejścia sprzętowego i dyspozytora NMI OS. Nie nazywamy go całym NMI.

| Identyczny pełny replay RC2 / RELEASE1 | DLI/raster | Max jedno ANTIC | Max CPU | Max suma/raster |
|---|---:|---:|---:|---:|
| Menu | 3 | 134 / 134 | 57 / 57 | 325 / 325 |
| Loader | 2 | 115 / 115 | 57 / 57 | 209 / 209 |
| Gra | 6 | 448 / 448 | 213 / 213 | 1333 / 1333 |

Nie ukrywamy droższej ścieżki szybkiego FIRE. Dla **tych samych pinów audytu**:
RC2 464 ANTIC / 219 CPU, RELEASE1 482 / 226; maksymalna suma w rastrze
1325→1339. Naprawa A-01 powoduje wykonanie właściwej istniejącej gałęzi undo.
W całej nowej macierzy faz zaobserwowano maksymalnie **486 ANTIC** jednego
pomiaru (0,013664 PAL), bez dodatkowego DLI lub instrukcji handlera.
To większy zakres testów niż zwykły replay; 448 nie jest globalnym maksimum.
[Porównywalny świadek DLI](DLI-witness-before-after.json).

## Końcowe bramki

| Kontrola końcowych obrazów | Wynik / dowód |
|---|---|
| Dwa czyste buildy normalnego ATR | PASS, identyczne bajty i SHA |
| Niezależny parser wszystkich 60 NSLV/NSRQ i CRC | PASS, oracle Python, źródło CAMP2-B |
| 60 rozwiązań z gotowego ATR, przejścia czterech obszarów, finał | PASS, 98 738 rastrów; brak podmiany RAM |
| 120 pełnych rastrów początkowych/rozwiązanych | PASS, 7 372 800 porównań pikseli końcowego produktu |
| Aktualne 60 map w ASan/UBSan i sim65 ASM ruchu/undo | PASS, każdy krok i zachowany prefiks po cofnięciu ostatnich 256; dziewięć ścieżek >256 |
| Undo256 z gotowego test-46 ATR | PASS: 270 ruchów, 256 cofnięć, dokładny prefiks 14 kroków; [dowód](undo256.json) |
| Restart, undo, zapis, zimne resume czterech startów | PASS, wszystkie pięć namespace izolowane |
| Normalny boot i cztery starty przez zwykły OS SIO | PASS, bez patcha, RAM64/PAL/BASIC off |
| Dwa zapisy i zimne Continue; write-protect | PASS, ostatnie generacje zachowane |
| A-01 / A-02 / A-03 | PASS w jawnie opisanej macierzy |
| Błąd pakietu, Retry, START do menu; podmiana D1 | PASS, częściowy obraz nie aktywuje się |
| Powrót muzyki po resume/menu/SIO | PASS dla postępu trackera i rejestrów POKEY SKCTL=3/AUDCTL=0; odsłuch OWNER_PENDING |
| Krótkie ścieżki 15→16, 30→31, 45→46, finał60 + zimny finał | PASS, rzeczywiste zimne I/O OS SIO; [dowód](hardware-routes.json) |
| WINDOWED launcher zwykły + cztery starty + cztery ścieżki | PASS `--check`; bez uruchomienia GUI przez agenta |
| Fizyczne Atari65XE PAL / SIO2SD / joystick / odbiór wyglądu | **OWNER_PENDING** |

## Odtwarzanie i ograniczenia

W nowym katalogu z zachowanymi wejściami (bez buildów) wykonaj:

```sh
python3 tools/v1_build.py --out build/release1/final
python3 tools/v1_build.py --out build/release1/test-1 --test-start 1
python3 tools/v1_build.py --out build/release1/test-16 --test-start 16
python3 tools/v1_build.py --out build/release1/test-31 --test-start 31
python3 tools/v1_build.py --out build/release1/test-46 --test-start 46
python3 tools/release1_core.py build/release1/final
python3 tools/release1_faults.py build/release1/final
python3 tools/release1_runtime.py campaign
python3 tools/release1_runtime.py saves
python3 tools/release1_runtime.py errors
python3 tools/release1_fire.py --build build/release1/final
python3 tools/release1_routes.py
python3 tools/release1_extra.py
```

Pełny izolowany builder użyty lokalnie: `python3 tools/release1_build.py`.
Odtworzenie porównań wymaga też niezmienionego RC2 z archiwum wejść audytu
lub dostarczonych źródeł FINISH2 sprzed napraw; RELEASE1 nie cofa repo.
Pomiary `release1_loading.py` oczekują obu buildów, a `--swap` tworzy prywatną
kopię istniejącego obserwatora. Dostarczony `source-inputs.zip` zawiera oba
źródła RC2/RELEASE1 oraz źródła kwalifikatorów. Zwykły Makefile i stare fixture'y
nie są podstawą kwalifikacji tego produktu.

[Dowody surowe RELEASE1](capture-evidence.zip), [dowody RC2 do porównania](capture-rc2-evidence.zip), [manifest paczki](manifest.json),
[sumy wszystkich plików](SHA256SUMS). Archiwum zawiera config/argv/input,
PNG/RAM, ślady SIO/routine/DLI, zegary A-01 i logi buildów. Nie deklarujemy
niezależnego reviewera RELEASE1; reprodukcje niezależnego audytu rozbudował
ten sam agent, korzystając z oddzielnych oracle. Brak fizycznego smoke,
zaniku zasilania SD, długiego odsłuchu i akceptacji obrazu pozostaje jawny.
Nie udzielono nowych praw autorskich ani licencji do niewyjaśnionych treści.

Po tym dostarczeniu rozwój funkcjonalny jest zamrożony. Następna iteracja
służy wyłącznie naprawie konkretnej usterki z odbioru właściciela.
