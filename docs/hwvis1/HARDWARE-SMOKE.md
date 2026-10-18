# HWVIS1 — OWNER_PENDING — Atari XL/XE PAL 64 KB + SIO2SD

PL: Graj na kopii ATR. Zachowaj dotychczasowe dyski z zapisami. Zamontuj
normalny kandydat jako D1: i uruchom Atari, trzymając **OPTION** (BASIC OFF).
Czarny ekran bez OPTION nie jest dowodem awarii SIO. BASIC musi być wyłączony.

Sprawdź: końcówkę początkowego ładowania, ciemne menu i strzałkę wyboru,
Begin Shift, napis/ilustrację/cienki pasek loadera, HUD, ruch, undo, następny
poziom, pauzę → config → powrót. Powtórz w czterech obszarach, używając
czterech ATR-ów testowych (01/16/31/46). Każdy uruchamia pełny boot i te same
zasoby, ma osobną tożsamość zapisów. Nie przenoś save pomiędzy wariantami.

W normalnym ATR: START, SELECT (zapis/wyjście), wyłącz komputer, zimny start
z OPTION, Continue. Sprawdź pozycję, liczniki, dźwięk/muzykę oraz brak
przedłużonych błysków szerokich kolorowych pól podczas I/O. Sygnał SIO może
być słyszalny. Oceń muzykę i SFX po powrocie do gry.

Zapisz wynik dla konkretnego SHA-256: model Atari, PAL/NTSC, SIO2SD/firmware,
obraz, ekran/poziom i moment problemu. Krótkie wideo lepiej dokumentuje
migotanie niż zdjęcie. Test emulatora nie stanowi odbioru sprzętowego.

EN: Use copies, preserve existing save disks. Mount normal candidate as D1:;
hold OPTION at power-on to disable BASIC. Test end of boot loading, dark
menu/selection, Begin Shift, loader illustration/text/thin progress bar, HUD,
next level, pause/config/resume, all four areas, save and cold Continue, music
and effects. Four full-boot test starts have isolated save identities. Record
ATR hash and actual Atari/SIO2SD/display details. Hardware acceptance is pending.

Launcher (emulator, WINDOWED, standard SIO):
`python3 tools/release1_owner_smoke.py` or `PLAY-WINDOWED.command`.
Use `--area 1`, `16`, `31`, `46` for helper disks; `--check` verifies without GUI.
Supply your own legal ROM config via NEON_ATARI_CONFIG and NEON_ATARI800.
