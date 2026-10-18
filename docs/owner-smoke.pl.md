[English](owner-smoke.md) · **Polski**

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** przy włączaniu trzymaj **OPTION**, aby wyłączyć BASIC. Nowy obraz czeka na odbiór wyglądu, przejść, zapisów i dźwięku na Atari; prawa pozostają otwarte. Raport: [HWVIS1](hwvis1/REPORT.md).

# Odbiór właściciela — sprzęt i wygląd

**Sprzęt: OWNER_PENDING. Wygląd/odsłuch: OWNER_PENDING.** Nie znaleziono późniejszego odbioru produktu 600d934 w lokalnych raportach ani pustym repo GitHub. Emulator nie zastępuje fizycznego Atari.

Przygotuj cały identyfikowany zestaw, bez kompilatora i wcześniejszych buildów:

```sh
python3 tools/hwvis1_prepare.py --routes
```

| Czysty obraz źródłowy | Przeznaczenie |
| --- | --- |
| dist/neon-shift65-v1.0.0.atr | Normalna gra, boot do menu |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-01.atr | Energy, poziom 1 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-16.atr | Hydroponic, poziom 16 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-31.atr | Data Hub, poziom 31 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-46.atr | Reactor, poziom 46 |

Pomocniczy ZIP i manifest są w build/owner-smoke/hwvis1/. SHA-256 normalnego źródła:
fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82.
Pięć hashów: build/owner-smoke/hwvis1/manifest.json. Na sprzęt skopiuj obrazy robocze; oryginały pozostaw czyste.

1. Atari 65XE PAL, 64 KB, joystick port 1; zapisywalna kopia na D1: SIO2SD obsługującym 8192×128 sektorów. Wyłącz BASIC (OPTION przy włączaniu). Sprawdź splash/loader/menu, całą planszę, HUD i rozróżnienie robota/skrzyni/doku.
2. Ruch, pchnięcie, zwolnienie, FIRE undo; powtórz SELECT. OPTION restartuje i zeruje liczniki/undo. START pauza → FIRE config, lewo/prawo muzyka i FIRE efekty → START → START gra. Posłuchaj przed i po I/O.
3. Na normalnym poziomie 1: R, START, SELECT zapis; CONTINUE, R, START, SELECT drugi zapis. Zimny boot → CONTINUE ma odzyskać STEPS=02, PUSHES=02 i puste undo. W tej ścieżce oba R pchają. SELECT na rozwiązanej planszy cofa przed świeżym FIRE przechodzącym dalej. Continue w RAM nie jest zimnym odczytem dysku.
4. Na roboczej kopii włącz ochronę zapisu po ruchu: pauza → SELECT ma pokazać SAVE FAILED i zostać w pauzie. Odblokuj zapis, ponów SELECT; zimne Continue ma odzyskać nowy stan. Test zaniku zasilania nie jest wymagany.
5. Uruchom zimno cztery kopie obszarów. Ruch, undo, restart i kontrola żółtego/zielonego/fuksjowego/czerwonego obszaru, ścian, paneli, robota, kontenerów i doków. Użyty testowy ATR automatycznie wznawia własny zapis po zimnym starcie. OPTION restartuje zapisany poziom; aby wrócić do czystego początku obszaru, przy wyłączonym zasilaniu zastąp kopię roboczą czystym źródłem testowym.
6. Krótkie ścieżki granic/finału są w build/owner-smoke/hwvis1/routes/: smoke-level-15/30/45/60.atr i routes.json. To kopie normalnego produktu z poprawnymi zapisami jeden ruch przed ukończeniem, bez patchy RAM. Zimny boot → CONTINUE → ostatni kierunek z routes.json → zwolnij → świeży FIRE. Wynik: 15→16, 30→31, 45→46, finał 60/60. SELECT przed FIRE cofa wygraną. Zimne Continue po ukończeniu wraca do finału.

Nie podmieniaj D1: podczas gry ani I/O. Wyłącz zasilanie, wybierz kolejną roboczą kopię i wykonaj zimny start. Odbiór nie wymaga ręcznego rozwiązania 60 poziomów: wystarczy ten krótki smoke.

## Launcher WINDOWED emulatora

Ustaw NEON_ATARI800 (lub atari800 w PATH) i NEON_ATARI_CONFIG na prywatną konfigurację z legalnym ROM-em OS. ROM nie jest dołączony.

```sh
python3 tools/release1_owner_smoke.py
python3 tools/release1_owner_smoke.py --area 31
python3 tools/release1_owner_smoke.py --route 60
```

PLAY-WINDOWED.command uruchamia to samo. --check przygotowuje komendę bez okna; agent używa wyłącznie --check/headless. WASD/M, F2 OPTION, F3 SELECT, F4 START; --physical-joystick pozwala użyć fizycznego kontrolera emulatora. Prywatne dyski zostają w build/owner-smoke/hwvis1/play/{normal,area-N,route-N}. Aby zacząć od czystego źródła, zmień nazwę prywatnego dysku jako backup i uruchom ponownie; launcher skopiuje czysty obraz. Źródła są sprawdzane hashem i nigdy nie są montowane do gry. Route to osobne robocze zapisy. Emulator nie jest odbiorem fizycznym.

## Wynik do przekazania

Zapisz model, PAL/64 KB, OS, model/firmware SIO2SD, kartę, joystick, monitor, nazwę i SHA-256 czystego obrazu, użytą kopię, rzeczywiste wyniki punktów 1–6 i osobne werdykty sprzętu/wyglądu/odsłuchu. Zgłoś konkretne błędy bez zmiany źródłowego ATR. Bez takiego wyniku nie wpisujemy PASS.
