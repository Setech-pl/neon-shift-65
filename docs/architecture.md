# Decyzje i pomiary NEON SHIFT65

Aktualny kontrakt2026-10-09: główny target SIO2SD/emulatory,65XE/64KB/PAL.
Duży ATR dozwolony; wiele plików lub dwa obrazy są opcją z rzeczywistą potrzebą.
Preferujemy jeden sprawdzony obraz. CA-2001 i pojemność fizycznej dyskietki nie
ograniczają głównego wydania. Poniższe D01–Dxx opisują także historyczne etapy;
aktualny bank, RAM, NSWP/NSWD, boot oraz pomiary SIO:
[warehouse checkpoint](checkpoints/warehouse-variety-asset-loading/report.md).
Wcześniejsze limity dysku, brak loadera i budżety M1 są historią.
M1 OWNER PASS PENDING, pełny preloader SETECH i M2 pozostają do wykonania.

## D01 — pamięć przed oprawą

Autorytatywne zakresy: cfg/memory.json (adres początku, koniec wyłączny, rozmiar, właściciel, wyrównanie, fazy życia, ceiling i źródło). Linker cfg/neon.cfg; tools/budget.py odczytuje rzeczywiste segmenty/etykiety/XEX i sprawdza zakresy, kolizje faz, wyrównanie i drift konfiguracji. tests/budget_test.py odtwarza błędy tych kontroli. $0000–$FFFF ma jawną klasyfikację RAM/ROM/I/O i rezerwacji; każda współdzielona część ma rozłączne fazy. MAIN obejmuje resident C/ASM/dane/grę/undo/player; dane szczegółowe są w mapie modułów. Nie używamy malloc ani RAM pod OS ROM. BASIC wyłączony, PORTB bit1=1; OS pozostaje włączony, OS VBI/IRQ i ROM vectors działają. $A000–$B7FF to zwykły RAM po wyłączeniu BASIC.

Start sp = MEMTOP ($BC20 w profilu64K) minus __RESERVED_MEMORY__ ($3420) = $8800; C stack $8000–$87FF. __STACKSIZE__=$0800; linker kończy MAIN na $7FFF. Ekran/charset/PMG/staging/resources są odrębnymi regionami. Początkowy SYSCHK $2E00 jest wykonywany przez INITAD PRZED załadowaniem main; później jego bajty są odzyskane, nie jest to kolizja rezydentna. OS screen $BC20–$BFFF pozostaje zarezerwowany. NMI/DLI nie dotyka parsera/undo; gra nie bankuje ROM.

Zastany pomiar z audytu: kod/dane rezydentne 9645 B + ZP26, XEX8871 B, GameState789 B na cc65. M0 po 32-bitowych licznikach i parserze: GameState793 B (cc65/sim65); mapa w build/budget.json. Ring:256 B + 5 B stanu; pierwotny parser M0 bitset95 B; aktualny parser BFS: visited760 B i Point queue1520 B (max648 pól/1296 B użytych). Host ma inne wyrównanie, nie zastępuje pomiaru cc65. Szczyt aplikacyjny podczas przyszłego load/decode liczymy jako pełny MAIN+stack+video+font+PMG+staging+decoded resources, czyli 38912 B; planowany boot peak osobno z bitmapą i źródłem kompresji. To ceiling, nie zmierzony szczyt. OS low RAM1536 B i OS screen992 B raportowane osobno. Preloader bitmap $8000–$9DFF, dlist $9E00–$9FFF i packed input $A000–$B7FF tylko w boot. Po zamknięciu prezentacji obszary oddawane stosowi/rendererowi/zasobom; C frontend zaczyna dopiero po wyłączeniu splash DMA/DLI/audio.

Specyfikacja cc65 potwierdza zależność stosu od MEMTOP i rezerwacji: https://cc65.github.io/doc/atari.html . Bez przenoszenia INIT/DATA/BSS poza kontrakt głównego bloku XEX.

## D02 — budżet dysku

W cfg/memory.json: aktualny koszt XEX w generowanym budget.json, surowy plan każdej kategorii i zapas. Plan 102400 B z rezerwą: kod24576, boot/preloader10240, wspólne2048, grafika rozdziałów12288, plansze4096, muzyka/SFX28672, katalog/padding4096, zapas16384. Nie traktować tych ceilingów jako gotowych danych. Kandydaci 720×128=92160 (brakuje10240 B dla obecnego planu) i1040×128=133120 (zapas30720 B). Format UNDECIDED: M2 wybierze po kompresji i testach boot/loader/SIO2SD; CA-2001 test dodatkowy. Nie obiecujemy obsługi ED na podstawie budżetu. Każdy asset ma raport raw/packed; kompresja tylko ze sprawdzonym round-trip i limitem decode.

## D03 — naprawy M0

Parser przed commit sprawdza bounded długość (również ponad255), prostokąt, granice, symbole, jednego gracza, 1..10 skrzyń i równe cele, spójność podłogi. Niepowodzenie zachowuje GameState. Ring usuwa najstarszy krok po przepełnieniu, cofanie odtwarza planszę i oba liczniki. Liczniki uint32_t w host i cc65; arytmetyka modulo2^32 jest odwracalna przez undo, obejmuje test granicy65535 i2^32; bez saturacji/kar. game_start i game_step są wspólną ścieżką Atari i replay. Solver FIFO BFS dowodzi minimum kroków gracza dla rozwiązanego wyniku przed limitem; pchnięcia są liczone w replay, bez deklaracji minimum pchnięć. Weryfikator sprawdza C/Python, duplikaty D4, minimum i replay, kończy exit1 przy błędzie.

## D04 — baza preloadera i loadera, M2

Osobna kopia /private/tmp/neon-shift-65-void-reference, detached85fccb76821dcc11aa4a8068cc8a64336af2ee1e. Checkout właściciela Void Strike nietknięty. Przeczytano src/boot-splash.s, assets/audio/boot-splash.json, scripts/loader-assets.mjs, assets/graphics/loader-bitmap.json oraz src/hybrid/sector-reader.s i disk-guard.s. Bitmap źródłowy ma natywne320×192 (7680 B), mieszane ANTIC E/F i DLI, pakowany LZSS z limitem źródłowym1997 B. Adaptacja ilustracji i relocation są M2 po odbiorze formatu M1. Żadnych zasobów okrętu w grze.

Kontrakt zachowany w adaptacji: 250 klatek; 12 komórek×26 scanlines PAL =600 baud; markAUDF5/space7, AUDC$A0, volume10→2 i odcięcie, fade od176; segmenty SILENCE5/LEADER60/DATA55/SILENCE10/DATA_LOW50/SILENCE10/DATA60; $55×2, framing start0/8LSB/stop1, środkowy blok oktawę niżej. Świeży SPACE/FIRE, uzbrojenie dopiero po zwolnieniu, po skip czekanie na release zanim frontend widzi FIRE. ASM splash ma512 B, źródłowe $0500 nie nadaje się do kopiowania bez kontraktu OS; nasz boot region $0600–$1FFF i całkowita regeneracja stanu przy wejściu.

Mechanizmy do wydzielenia: standardowy SIO cmd$52, carry-wrap checksum sektora, retry3 wire/device probes2, timeout liczony PAL VCOUNT (TX2/ACK3/COMPLETE200/DATA2/SETTLE2), integralność całego zasobu i brak aktywacji częściowego odczytu. Źródłowy limit levelid16, 16sektorów/bufor2048 i zależności fighter/director/summary/save nie są naszym API. Własny katalog planowany NS65 v1: zasób typu chapter/level/music/decor, id u16, first_sector u16, sectors u16, packed_length u16, raw_length u16, codec u8, CRC16 u16. 60 level entries plus muzyka/grafika; zasoby dzielone przy limicie staging1920 + sector128. Aktywacja atomowa po complete read/CRC/decode/level validation, błąd pozostawia poprzedni poprawny stan i menu retry. Brak zapisu stanu na dysk i turbo SIO. Katalog/CRC/decode wymagają runtime M2, obecnie NOT_RUN.

## D05 — grafika M1 (prototyp do odbioru)

Dobór po pomiarach M0: testujemy ANTIC4, 160×192 pikseli koloru o podwójnej szerokości, odpowiadających rastrowi Atari 320×192 punktów w jednostkach hi-res. Te punkty nie są pikselami panelu Maca. 40×24 znaki; znak ma 4×8 pikseli koloru / 8×8 punktów rastra, kafel 2×2 znaki = 8×16 pikseli koloru / 16×16 punktów rastra. Do20×10 pól + HUD. 4 playfield kolory z piątym przez bit7 kodu znaku: czarny/żółć/cyjan/stal/światło. Jeden własny1024-B charset, screen960 B, dlist32 B, bez DLI/PMG w pierwszym pomiarze. To kandydat, nie zatwierdzony format kampanii. Wszystkie20 zastanych plansz mieszczą się; validator renderer będzie odrzucał większe. Live robot glyph aktualizowany w blanking, stabilny screen i dirty cells; nie przerysowujemy idle planszy. Dane pixel source i packing generowane do build/, preview dekoduje dokładnie te same bajty.

Rzeczywista display list w `src/display.c:display_init`: $8BC0, trzy $70 (24 puste linie), LMS $44 na $8800, następnie 23×$04, JVB $41 na $8BC0. Wszystkie 24 wiersze obrazu, także tekst/menu/tytuł, używają ANTIC4. Nie ma osobnego obszaru ANTIC2 ani zmiany trybu przez DLI.

| Obszar gry | Znaki / pola | Piksele koloru ANTIC4 | Raster Atari (jednostki hi-res) |
|---|---|---|---|
| Cały aktywny obraz | 40×24 znaki | 160×192 | 320×192 |
| HUD, wiersze 0–1 podczas gry | 40×2 znaki | 160×16 | 320×16 |
| Plansza i dekoracje, wiersze 2–21 | 40×20 znaków / maks. 20×10 pól | 160×160 | 320×160 |
| Stopka, wiersze 22–23 podczas gry | 40×2 znaki | 160×16 | 320×16 |
| Jeden kafel | 2×2 znaki | 8×16 | 16×16 |
| REACTOR STORE | 13×6 pól | 104×96 | 208×96 |
| FOUNDRY BAY | 20×10 pól | 160×160 | 320×160 |
| FIRST DOCK | 6×3 pola | 48×48 | 96×48 |

Podział HUD/plansza/stopka dotyczy rozgrywki; menu i tytuł wykorzystują tę samą pełną siatkę. Kadrowanie emulatora TV/TV w PAL obejmuje 336×240 punktów rastra z obramowaniem, nie zwiększa rozdzielczości gry. Launcher kopiuje profil wyświetlania używany przez Void Strike, a wielkość okna i backing Retina mierzymy osobno: [korekta launchera M1](checkpoints/m1/display-launch-correction.md).

## D06 — audio M1

Kanał1 bass,2 lead,3 rhythm/noise,4 SFX. SFX priorytety win>push>undo>blocked; niezależne MUSIC/SFX mute w menu. Odtwarzacz ASM w deferred OS VBI, dane aktualnego utworu są immutable podczas gry, patch VBI zachowuje A/X/Y i nie używa cc65 ZP/stosu C. Frontend zleca efekt atomowym pojedynczym bajtem; ISR ma własny stan. SFX nie blokuje ruchu. M1 trzy oryginalne32-row fragmenty (SHIFT SIGNAL / FOUNDRY CIRCUIT / NIGHT TERMINAL) z warstwami/obwiedniami, dalsza biblioteka w M4. SIO w M2 suspend całego playera i wyciszenie wszystkich kanałów; po odczycie przywrócić AUDCTL/SKCTL i kanały, dopiero potem resume. Nie stosować shootera muzyki podczas serial read bez osobnego pomiaru.

## D07 — korekta dowodu M0 i wynik M1

Pierwotny target PASS parsera z1bfd260 wycofany: cc65 V2.18 -O źle obniżał zagnieżdżony ternary, odtwarzał c z niewłaściwego offsetu stosu C i zamieniał ściany w floor. Host C był poprawny; target ring porównywał stan parsera z nim samym i nie wykrywał złych kafli. Jawne if/else naprawia przyczynę. Wszystkie targety używają obecnie tych samych -Oirs -Cl co Atari. Niezależny reviewer przygotował pełny793-B oracle20 plansz i482 kroków z osobną symulacją w Python, negative/fullsize parser test, flow/input,263 wartości uint32 ASM,296 kafli i576 ticków POKEY. Te testy włączone do make target-test za zgodą autora. Nie modyfikowano historii poprzedniego checkpointu. -Cl dopuszczone: main-thread C bez rekursji/reentrancy; ISR wyłącznie ASM, prywatna ZP. Nie wolno wywołać tych funkcji C z przerwań.

M1: MAIN22284/24576 B (2292 B zapasu), ZP38 B, BSS4282 B, code14052 B, rodata3756 B; screen1024 B i font1024 B w odrębnych regionach. XEX18270 B; raw charset1024/robot1280/music288, ich próbne count/value RLE848/1798/378 B, więc runtime używa raw. Dane są zawarte w XEX, nie dodawać kosztów assetów ponownie do kosztu XEX. Budżet dyskowy102400 B pozostaje ceiling przyszłej kampanii, nie rozmiarem M1.

M1 input ISR:256 próbek trzech urządzeń (768 B), usable255, head/tail byte. Każda klatka PAL próbkowana raz, zachowana kolejność także podczas parsera i zmiany widoku. Overflow jest licznikiem dowodowym; zero we wszystkich bramkach. Historyczny16-sample queue nie wystarczał na ładowanie. Opróżnianie backlogu może ruszyć wiele skrzyń — dirty renderer sprawdza wszystkie10 zamiast zakładać pojedynczy krok. Restart i zmiany widoków mogą wykonywać full render; idle i zwykłe ruchy tego nie robią.

DMA dla pełnego nowego widoku wyłączone w main, włączane wyłącznie przez deferred VBI po zakończeniu obrazu. Powtórna edycja menu tytułu zmienia tylko opcje. Robot32 B do charsetu kopiuje ISR w VBI ze wskaźnika wyliczonego ze40 walidowanych klatek; C publikuje jedynie atomic frame byte. Chroni to glyph przed częściową podmianą w widocznej klatce. Renderer ASM ma jawny ABI GameState (size793/width760/player762/boxes764/count784); build odczytuje tablicę rzeczywistych offsetof z XEX i odrzuca drift. Paleta pochodzi z tego samego JSON co preview:0/$EE/$9C/$84/$0E, emulatorowa paleta RGB zmierzona z PNG.

Timing w checkpoint report: ANTIC CPU_CLOCK, zawiera DMA i przerwania, nie samo CPU. Zwykły krok ciężkiej sceny około25k cykli; największy solve/update około53k, może przekroczyć jedną klatkę PAL35568. Full scene transition około1.42m cykli (~40 klatek), loader dysku nie jest jeszcze zaimplementowany. Nie obiecujemy50 pełnych renderów/s; input sampled w VBI i repeat14/5 klatek, animacja nie blokuje ruchu. Obserwowane stosy to peak w konkretnych runach, nie globalny worst-case. M2 zasoby doładowywane odzyskają obecne const data i mogą współdzielić parser scratch z decode wyłącznie po nowym kontrakcie faz.

Utwory oryginalnie stworzone w tej sesji dla projektu, bez muzyki shootera. Kanały1..3 music,4SFX, priorytet4>3>2>1 i niezależne mute. Naprawiony hat envelope: CMP#0 po CPY przed BEQ, aby Z odpowiadało envelope, nie typowi perkusji. Native POKEY register oracle i PCM PASS; odsłuch oraz fizyczny POKEY NOT_RUN. Na SIO cały player będzie suspend/mute w M2; obecnie transmisja NOT_RUN.

## D08 — rewizja grafiki M1 przed korektą kolorów

Baza D05/D07 i starszy checkpoint opisują stan do0e04b7e. Aktualny renderer pozostaje ANTIC4 we wszystkich24 wierszach:160×192 pikseli koloru, kafel8×16. Dwa DLI: po pierwszym wierszu przełączają COLPF3 z żółci nazwy na jasną stal, po drugim CHBASE z banku HUD$90 na bank planszy$8C. VBI ustawia bank/kolor dla początku kolejnego rastra. ANTIC2/bitmapowy ANTIC E/F oraz DMA PMG nie są używane.

| Region | Właściciel i czas życia |
|---|---|
| $8800–$8BFF | SCREEN1024 B: obraz960, dlist32, spare32; menu/play/load |
| $8C00–$8FFF | bieżący charset1024 B: gra albo tytuł; jawna wymiana przy wyłączonym DMA |
| $9000–$93FF | bitmapowy HUD1024 B,80 użytych glyphów; dawny reserve PMG |
| $9400–$953F | pending row320 B HUD; main pisze, VBI kopiuje po publikacji flagi |
| $9540–$97FF | pozostała część regionu PMG, bez użytkownika M1 |
| $9800–$9FFF | staging przyszłego loadera, M1 niewykorzystany |
| $A000–$B413 | ART5140 B: dwa charsety,40 klatek robota,2 mapy880 B, logo52 B |
| $B414–$B7FF | wolna część ASSETS,1004 B; nie jest dodatkowym limitem MAIN |

MAIN/ZP/stosy/stan/undo/parser/audio z rzeczywistej mapy: [raport rewizji](checkpoints/m1-graphics/README.md) i [budget.json](checkpoints/m1-graphics/budget.json). Wszystkie te obszary są statyczne; przygotowanie/przejście ekranów kopiuje zasób do istniejącego banku, nie alokuje dodatkowego ekranu. Zasób ART jest osobnym chunkem XEX z headerem linkowanym z __ART_LOAD__/SIZE. RAM pod BASIC dostępny przy BASIC off; RAM pod OS ROM nadal nieużywany. Loader M2 musi wyłączyć DMA/DLI/animację/audio i przestrzegać peak packed+decoded; jego38912-B ceiling nie jest runtime PASS.

Plansza wycentrowana w40×22 znakach pod HUD-em (160×176 pikseli koloru). FIRST DOCK6×3 pola →48×48, REACTOR13×6 →104×96, FOUNDRY20×10 →160×160. Żadnego scrolla ani trwałej stopki; wygrana pokazuje komunikat w ostatnim wierszu do świeżego FIRE/undo. Opaque ground kafli przesłania ilustrację. Biblioteka36 fragmentów obejmuje sylwetkę robota/ramię/kable/kabinety oraz2 lampki/4 gotowe fragmenty sinusoidy. Mapy scene0/1 i przypisanie poziom→scene są zasobami, możliwymi do zastąpienia w M2. To przykłady wspólnej palety, nie pełne zestawy kampanii.

VBI aktualizuje maksymalnie7 kodów co8 klatek. Maska wyklucza cały prostokąt planszy i HUD, w menu efekty są zatrzymane. Nie zmienia charsetu planszy. Robot ma odrębny32-B patch w VBI i jawne dirty po wymianie charsetu. Tytuł używa frame255 (brak patcha) i własnych glyphów, także w zakresie88..91. HUD publikuje320-B row dopiero po ukończeniu; nazwa jest zbudowana podczas wyłączonego DMA. Poziom/etykiety/ratio mają stałe pozycje, dwie wartości uint32 są pełne, maksymalnie10 cyfr. Zajęte doki liczy tani ASM dla max10 modułów, także gdy batch undo+inny push zachowuje wartość PUSHES.

Menu tytułu ma zaakceptowane cztery pozycje, CONFIG działa. BEGIN SHIFT uruchamia scenę; wybór testowych scen pozostaje w pauzie. CONTINUE jawnie niedostępne: M3 wymaga katalogu kampanii, odblokowania i walidacji continuation code. TOP SCORES jawnie niedostępne: brak fikcyjnej tablicy i zapisu. Zapis dyskowy/FujiNet są późniejsze. Muzyka i SFX oraz undo pozostają produkcyjnymi ścieżkami; bez rozbudowy kampanii/loadera.

Dowód pikselowy odczytuje dodatkowo RAM przed ANTIC_Frame. Końcowe VBI zapisuje już lampki/HUD kolejnej klatki, więc end-frame RAM nie zawsze jest źródłem właśnie zrobionego PNG. Zrzuty pozostają prawdziwymi Screen_SaveScreenshot, bez retuszu. Niewidoczne SDL dummy, osobna kopia emulatora, żadne widoczne okno/owner smoke nie były uruchamiane.

## D09 — korekta właściciela: kolorowa plansza, szara ilustracja, WINDOWED

Aktualna decyzja nadpisuje szarą planszę/podłogę i fullscreen w poprzednich opisach. Wcześniejsze ściany, robot, moduły, doki i pasy ostrzegawcze przywrócono ze sprawdzonego 0e04b7e. Nie przywracamy starej faktury podłogi. ANTIC4 pozostaje160×192; czarna powierzchnia ma delikatne niebieskie linie dużych płyt co4×2 pola oraz dwupikselowe ukośne nacięcia, bez szarego wypełnienia. Cztery fragmenty podłogi mają2/10/18/25 niezerowych pikseli na128. Plansza jest nieprzezroczysta i zachowuje pełną widoczność w dotychczasowych wymiarach.

Paleta $00/$EE/$9C/$84/$0A. Kody planszy bez bitu7 wybierają niebieski COLPF2 dla piksela3. Ilustracja robota, ramienia, przewodów i urządzeń ma wyłącznie piksele0/3, kody220..255 wybierają szary COLPF3, dithering przygasza szerokie sylwetki. Lampki i oscyloskop używają tego samego selektora; maska7 pozycji pozostaje. HUD, zwykłe teksty i logo zachowują kolory poprzedniego checkpointu. Bit7 map jest maskowany przy ustalaniu wolnych tytułowych glyphów, aby logo nie nadpisało ilustracji.

Mapa D08 bez zmiany regionów/życia zasobów: MAIN22474/24576 B (2102 B wolne), statyczne regiony aplikacji31044 B, ART5140/6144 B, ZP38, SCREEN1024, CHARSET1024, HUD1344. Przygotowanie nowej grafiki nie alokuje nowych buforów; statyczny szczyt obejmuje jednocześnie źródła ART i bieżące banki. Zachowane naprawy cache robota, tytułowego frame255, wszystkich dirty boxes oraz aktualizacji DOCKS przy batch undo+push z tym samym PUSHES. Stosy i koszt klatek: [aktualny checkpoint](checkpoints/m1-color-correction/README.md); przyszłe loader ceilings z D08 nie są runtime PASS.

Owner launcher kopiuje profil skalowania, wymusza VIDEOMODE_WINDOWED=1 oraz argument -windowed nawet dla globalnego fullscreen. INTEGRAL i SQUARE-PIXELS, brak filtrów pozostają. Nie zmienia ~/.atari800.cfg ani Void Strike. Test regresji prepare_launch sprawdza fullscreen na wejściu, zachowanie profilu i niezmienność źródła bez uruchamiania emulatora. Natywna weryfikacja tylko SDL dummy; okno interaktywne uruchamia właściciel. Bez merge/push przed owner PASS.

## D10 — osobny ANTIC2 HUD i czytelne menu

D10 nadpisuje opis HUD-u i menu w D08/D09. Rozgrywka: dwa wiersze ANTIC2
320×16, potem 22 wiersze ANTIC4 160×176 pikseli koloru. Każdy wiersz w obu
trybach zużywa40 B; dotychczasowe adresowanie kafli, centrowanie, maska tła,
paleta i animacje planszy pozostają. Display list $8BC0: $70,$70,$70,
$C2,$00,$88,$82,22×$04,$41,$C0,$8B. Jej32 B i screen960 B mieszczą się
w VIDEO1024 B. Dwa DLI są po wierszach0 i1.

ANTIC2 interpretuje bajt glifu jako8 bitów, bit7 kodu znaku oznacza inwersję.
HUD screen codes0..79 nie mają bitu7. Bitmapowe paski są składane z autorskich
6×7 glifów przy skoku7 (nazwy8), bez usuwania kolumn. Źródło352 B jest
niemodyfikowalne w ART. Nazwa ma COLPF1=$0E i COLPF2=$E0: kolor foreground
$EE, tło o luminancji0 w tej samej żółtej tonacji. Pierwszy DLI zmienia PF2
na$00 dla jasnych liczników; drugi ustawia CHBASE=$8C, PF1=$9C i PF2=$84,
zanim rozpocznie się pierwszy wiersz planszy. PF0=$EE, PF3=$0A i COLBK=$00
pozostają. OS shadows przechowują paletę planszy; deferred VBI ustawia jawny
stan początku rastra i zeruje fazę DLI. ISR zachowuje A/X, nie zmienia Y i nie
używa scratch cc65 ani rendererowych wskaźników.

| Zakres | Właściciel |
|---|---|
| $8800–$8BBF | 24×40 B screen; HUD pierwsze80 B, plansza pozostałe880 B |
| $8BC0–$8BDF | display list32 B; $8BE0–$8BFF zapas |
| $8C00–$8FFF | ANTIC4 planszy/title, robot patch tylko$8EC0–$8EDF |
| $9000–$913F | nazwa HUD320 B; main pisze tylko z DMA off |
| $9140–$927F | opublikowany wiersz liczników320 B; zapisuje VBI |
| $9280–$93FF | nieużywane, wyzerowane wnętrze banku HUD |
| $9400–$953F | pending strip320 B; main pisze, publikuje flagę na końcu |
| $9540–$97FF | wolne w PMG region; PMG DMA off |
| $9800–$9BFF | immutable menu charset1024 B, właściciel M1 frontend |
| $9C00–$9FFF | obecnie wolne; przyszły loader wymaga kontraktu odtworzenia menu |
| $A000–$B6D3 | immutable ART5844 B, w tym dwa źródła fontów po352 B |
| $B6D4–$B7FF | wolne300 B w ASSETS |

PMGDATA pozostaje1344 B, IO_BUFFER zajmuje1024 B. Staging nie jest już całym
wolnym buforem loadera. M2 musi wstrzymać DMA i odtworzyć charset menu przed
powrotem, jeśli przejmie$9800–$9FFF. Budget sprawdza stałe adresy, wyrównania,
segmenty, kolizje i ceilings. MAIN23120 B, zapas1456 B; statyczne regiony
aplikacji33418 B, +2374 B względem D09 (MAIN+646 B, ART+704 B,
menu bank+1024 B, ZP bez zmiany).
Autorytatywna suma segmentów jest w aktualnym raporcie checkpointu; stosy C2048
oraz CPU256 B raportowane osobno. Nie utożsamiamy zapasu MAIN z całym RAM.

Menu: ANTIC4 logo/hero/ilustracji u góry, osobny ANTIC2 credit w wierszu5;
monochromatyczny panel w13–23, pozycje14/16/18/20. Pełne glify referencyjne,
jasne litery i żółty wiersz wyboru z `>`; brak dolnej instrukcji. Panel usuwa
ilustrację tylko z obszaru tekstu, górna ilustracja i hero pozostają. Sześć
DLI przełącza credit→hero→menu oraz trzy następne wiersze wyboru. CONFIG,
CONTINUE i TOP SCORES używają pełnego ANTIC2. Menu pauzy pozostaje overlay
ANTIC4 na planszy. Powrót do gry zawsze odtwarza display list, charset i
paletę; publikacja następuje po ukończeniu scene/HUD. Powrót do title zatrzymuje
animacje i czeka na pending HUD przed zmianą grafiki.

Pomiary CPU obejmują DMA, WSYNC i przerwania; nie stanowią gwarancji50FPS ani
pomiaru globalnego worst case. Szczegóły referencji, szerokości, natywne obrazy,
czasy przed/po i niezależny review: [checkpoint czytelności](checkpoints/m1-hud-menu-readability/README.md).


## D11 — UI i audyt budżetu; OWNER PASS PENDING

D11 nadpisuje bieżący opis HUD-u/frontend i wstępne budżety D02/D10.
Źródło bieżących pomiarów, pełnej mapy/faz, inventory glifów, CPU i sektorów:
[raport](checkpoints/m1-ui-budget-warehouse/report.md).

CONFIG miał wiersze ANTIC4 przy banku monochromatycznym$98 wskutek błędnego
wygenerowanego odczytu `(sp),Y` w zagnieżdżonym operatorze warunkowym cc65.
Tryb wybieramy przed prostą pętlą. Wszystkie pełne ekrany tekstowe, w tym
pauza/restart/finał, mają ANTIC2, bit7 bez inwersji. Resume odtwarza planszę.
Logo używa pełnych glifów Void menu. Dwa istniejące wiersze HUD pozostają:
nazwa+DOCKS:00/00 u góry, STEPS:00 i PUSHES:00 poniżej, liczby wyrównane do lewej,
minimum2 cyfry, pełne uint32. Maksymalne szerokości315/261 px. Nazwy autorowane
≤28 znaków; generator pilnuje granicy pola doków. SHIFT CLEAR bez instrukcji
zostaje w wierszu23 poza planszą; FIRE/SELECT bez zmian. Tło zaakceptowane.

MAIN23085 B, reserve1491 B; statyczne regiony33383 B bez stosów, ART5844 B.
Istniejące fizyczne regiony/fazy w cfg/memory.json bez zmiany. Audit load peak
odróżnia ceiling38912 B od przyszłego low-loader6656 B i rezerwacji OS.
Jedna nowa logiczna płytka mieści się w wolnych44–47; oddzielne natywne
studium FOUNDRY nie zmienia produkcyjnych assetów ani loadera. Propozycja
14 ścian/urządzeń wymaga odzyskania fontu ANTIC4 dopiero po przeniesieniu
krótkiego statusu do hi-res; bank1024 B i tło92–127 pozostają.

ATR nie istnieje. Proponowany raw-sector model ED1040×128 dla4 pełnych banków
ma12800 B zapasu po boot/katalogu/nagłówkach/padding i rezerwach. Dla12:3456 B,
dla60:-52608 B. To nie zmiana geometrii dystrybucji, a decyzja do właściciela.
Compression raw/RLE/zlib pomierzono na istniejących zasobach; przyszłe brakujące
zasoby są oznaczone NOT_AVAILABLE, żadnego stałego współczynnika. SIO, sprzęt,
nowy preloader i kodek pozostają M2 po owner PASS. Pełny RAM/CPU/glyph/disk
review w checkpoint; automatyczne PASS nie są owner PASS.
