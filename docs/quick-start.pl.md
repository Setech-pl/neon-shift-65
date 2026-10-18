[English](quick-start.md) · **Polski**

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** przy włączaniu trzymaj **OPTION**, aby wyłączyć BASIC. Nowy obraz czeka na odbiór wyglądu, przejść, zapisów i dźwięku na Atari; prawa pozostają otwarte. Raport: [HWVIS1](hwvis1/REPORT.md).

# Szybki start

Pobierz `neon-shift65-v1.0.0.zip` albo sam ATR z [dist](../dist/). Publikacja stabilna oczekuje; są to niezmienione bajty kandydata 1.0.0. Rozpakuj ZIP i zachowaj oryginalny ATR bez zmian.

1. Zrób zapisywalną kopię do gry. Zamontuj ją jako **D1:**, nie jako program/XEX.
2. Atari800: `atari800 -xl -pal -nobasic -no-mapram -nopatch play.atr`. Ustaw 64 KB RAM i joystick w porcie 1. Emulator i legalny ROM dostarczasz osobno.
3. Prawdziwy 65XE: wybierz kopię na SIO2SD D1:, zezwól na zapis i trzymaj OPTION przy włączaniu, aby wyłączyć BASIC. Urządzenie musi obsługiwać 8192 sektory po 128 B. Odbiór fizyczny nadal OWNER_PENDING.
4. Wybierz BEGIN SHIFT i FIRE. Joystick porusza, FIRE/SELECT cofa, OPTION restartuje, START pauzuje. SELECT w pauzie zapisuje i wychodzi.
5. Na rozwiązanej planszy zwolnij FIRE i naciśnij ponownie, aby przejść dalej. SELECT cofa wygrywające pchnięcie. Po zimnym starcie wybierz CONTINUE; undo jest puste.

Launcher właściciela używa WASD/M, F2=OPTION, F3=SELECT, F4=START. Klawisze innych emulatorów zależą od mapowania. NTSC i CA-2001 nie są zakwalifikowane. Nie podmieniaj D1: podczas działania ani zapisu. [Pełne zasady](how-to-play.pl.md).
