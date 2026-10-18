# NEON SHIFT 65 — kontrakt produktu

Aktualizacja 2026-10-15: decyzja właściciela PRODUCT1/ENG4 zastępuje dawne
wymaganie przyjęcia każdej obserwacji urządzenia. Bieżące sterowanie:
[ENG4](docs/product1/eng4/contract.md); zakres 60 poziomów i trwałego zapisu
ATR pozostaje. [Kompletny kandydat](docs/product1/candidate-report.md) wymaga
odbioru wizualnego, sterowania i hardware. Prawa OPEN, PUB1 osobno i bez zmian.
[Dawny bloker ENG3](docs/product1/blocker.md) oraz poprzedni kontrakt PRODUCT1
pozostają historią. Poniższe wcześniejsze ograniczenia etapów, continuation
code i brak obowiązkowego save zostały zastąpione decyzją PRODUCT1.

Studio: SETECH GAME STUDIO. Źródło decyzji: zlecenie właściciela z 2026-10-08; zastępuje dawny brief. Historyczna wersja i pochodzenie pozostają w baseline 8056a70.

## Platforma i dystrybucja
Atari65XE, standardowe64KB, PAL. Główny target: SIO2SD i emulatory.
Preferujemy jeden sprawdzony bootowalny ATR. Duży ATR i dystrybucja w wielu
plikach, także dwa ATR, są dozwolone, gdy potrzeba wynika z danych lub wygody.
Fizyczna dyskietka DD720×256 i CA-2001 nie wyznaczają pojemności głównego
wydania. Builder/procedury SIO mają jawne własne limity; weryfikacja sprzętu
SIO2SD należy do właściciela. Development może używać XEX z zamontowanym ATR.
Gra po angielsku, raporty i owner smoke po polsku. C/cc65 i ca65.
Decyzje właściciela z2026-10-09 zastępują wcześniejsze ograniczenia geometrii.


## Kampania i oprawa
60 poziomów, 4 rozdziały po 15. Plansza w całości na ekranie. Rozdziały mają własne zestawy graficzne; poziomy mogą doładowywać dekoracje, palety, animacje, utwory. Cyberpunkowy przemysłowy magazyn: ciemne tło, żółć i cyjan. Niski robot na gąsienicach, żółty korpus i cyjanowy wizjer; cztery orientacje, jazda i pchanie. Skrzynie: moduły energetyczne. Cele: świecące doki. Robot i moduł na doku rozróżnialne także kształtem. Cel jakości: pixel-perfect i poziom demosceny. Format obrazu zatwierdza właściciel po natywnym prototypie; screenshoty bez wygładzania pochodzą z emulatora.

## Sterowanie i zasady
Joystick 1: kierunek działa natychmiast, repeat po opóźnieniu. FIRE w grze i SELECT: undo; START: pauza/menu; OPTION: restart z potwierdzeniem; FIRE zatwierdza menu. Animacja nie blokuje wejścia. Undo obejmuje każdy udany krok (pchnięcie wraz ze skrzynią jest jednym krokiem), odrzucone próby nie są liczone. EASY 256 / MEDIUM 128 / HARD 64, ring usuwa najstarsze kroki, cofa planszę i liczniki; restart czyści historię. Zagadki identyczne w trybach, bez timera/kar/dodatkowych różnic. Po wygranej świeże FIRE przechodzi dalej; SELECT cofa ruch i przywraca grę. Przytrzymany przycisk nie przeskakuje ekranów.

Postęp odblokowuje następne poziomy i umożliwia powtórki. Krótki continuation code przywraca zakres odblokowania, nie planszę. Bez obowiązkowego zapisu na dysk.

## Audio i preloader
Oryginalna muzyka cyberpunk na POKEY: kilka utworów na rozdział, motyw tytułu i finału, dowolne przypisanie do poziomu. Wspólny odtwarzacz i doładowywane dane; muzyka i SFX wyłączane osobno, bez blokowania gry. Podział kanałów i priorytety w docs/architecture.md. SIO korzysta z POKEY: cisza albo krótki motyw, bez założenia swobody kanałów.

Baza preloadera/loadera: osobna kopia Setech-pl/void-strike-65 na SHA 85fccb76821dcc11aa4a8068cc8a64336af2ee1e. SETECH GAME STUDIO; inscenizacja standardowej kasety Atari 600 baud, 250 klatek PAL (5 s), fade obrazu i dźwięku, pomijanie świeżym SPACE/FIRE. Nowa natywna ilustracja robota/modułu/doku w magazynie; bez okrętu. Zachować charakter dźwięku i przebieg; właściwy odczyt dyskowy. Pamięć odzyskiwana po pokazie. Retry, timeout, walidacja/integralność; niepełny poziom nigdy nie jest aktywowany. Bez założonego turbo SIO.

## Walidacja
Każdy poziom: rozmiar, symbole, zamknięcie, jeden gracz, skrzynie=cele, solver, replay produkcyjnego C, duplikaty z odbiciami/obrotami, czytelność w rendererze. Kroki i pchnięcia osobno. Minimum tylko po wyczerpującej weryfikacji danej miary; długość rozwiązania nie oznacza trudności. Nie kopiować obcych poziomów bez praw/pochodzenia. Partie po rozdziale; nie produkować 60 poziomów ani finalnych assetów przed PASS formatu.

## Gauntlet i odbiór
Implementacja → build → testy → Atari800 → niezależny reviewer bez edycji → poprawki → ponowne bramki. Wyniki PASS/FAIL/BLOCKED/NOT_RUN z dowodami, bez zastępowania runtime wyszukiwaniem tekstu. Odsłuch i sprzęt wymagają osobnego wykonania.

M0: audyt/regresje/baseline/pamięć/budżet/reprodukowalny build, wewnętrzny checkpoint. M1: grywalny natywny PAL, plansza/robot/kafle/HUD/animacja/muzyka/SFX — READY FOR OWNER SMOKE, czeka na PASS właściciela. M2: bootowalny ATR/preloader/dwa poziomy o odmiennych zasobach i muzyce. M3: 15 poziomów rozdziału I/menu/wybór/continuation. M4: 60 poziomów/4 rozdziały/biblioteka muzyki/finał. M5: strojenie po graniu/regresja/finalny ATR/instrukcja/odbiór. M1 nadal bez OWNER PASS. Autoryzowany checkpoint zależny oprawy i doładowania może rozwijać technikę M2 na gałęzi; nie oznacza pełnego M2 PASS.

## Git
Lokalny katalog atari-sokoban. Prywatne Setech-pl/neon-shift-65. Main zachowuje historię; praca feature/* z checkpointami. Żadnego merge funkcjonalnego do main ani push checkpointu przed smoke i PASS właściciela. Bez automatycznego release/zmiany widoczności. Zachować zastane zmiany; bez hard reset/clean/force checkout/autostash. Publiczne repo dopiero po wydaniu w osobnym kroku.

## Źródła prawdy
Ten brief: wymagania i milestone’y. cfg/memory.json: zakresy, fazy i planowany budżet; cfg/neon.cfg: linker, kontrolowany przez build. docs/architecture.md: decyzje i pomiary. docs/checkpoints/: dowody/checkpoint/owner smoke. build/: regenerowane raporty i artefakty, bez ROM. docs/audit/: historyczny audyt, nie aktualny brief.
