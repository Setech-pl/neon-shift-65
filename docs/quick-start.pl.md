[English](quick-start.md) · [Polski](quick-start.pl.md)

# Szybki start

1. Skopiuj normalny `neon-shift65.atr` na zapisywalny nośnik. Gra zapisuje postęp we własnym obrazie dysku.
2. Zamontuj kopię jako **D1:**. Przy zimnym starcie Atari trzymaj **OPTION / BASIC OFF**.
3. Poczekaj na menu. Joystick w porcie 1 i FIRE wybierają **BEGIN SHIFT** lub **CONTINUE**.

Cel sprzętowy: Atari 65XE PAL, 64 KB RAM; XL/XE PAL 64 KB sprawdzono w emulatorze. Obraz ma 8192 sektorów po 128 B (1 048 592 B z nagłówkiem). SIO2SD musi obsługiwać ten format i zapis. NTSC, fizyczne stacje i inne konfiguracje nie są zakwalifikowane.

## Emulator

Atari800: PAL, XL/XE 64 KB, BASIC OFF, normalne OS SIO (`-nopatch`). Zamontuj zapisywalną kopię jako D1: i wykonaj zimny start. Skonfiguruj joystick 1 w ustawieniach emulatora. W używanym profilu Atari800 WASD steruje ruchem, M = FIRE; F2 = OPTION, F3 = SELECT, F4 = START. Inne emulatory mają własne mapowanie. Użyj legalnej konfiguracji OS; ROM-u ani emulatora nie dołączono.

Setech Arcade: strzałki/WASD = ruch, Z/X = FIRE, F2 = OPTION, F3 = SELECT, F4 = START. Postęp jest zapisywany w IndexedDB tej przeglądarki; wyczyszczenie danych witryny usuwa zapis. Pobrany ATR jest świeżym dyskiem, osobnym od zapisu przeglądarki. Pełne sterowanie klawiszami konsoli wymaga klawiatury; dotyk i gamepad udostępniają ruch oraz FIRE.

[Instrukcja](how-to-play.pl.md) · [README](../README.pl.md)
