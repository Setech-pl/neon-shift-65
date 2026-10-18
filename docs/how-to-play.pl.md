[English](how-to-play.md) · **Polski**

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** przy włączaniu trzymaj **OPTION**, aby wyłączyć BASIC. Nowy obraz czeka na odbiór wyglądu, przejść, zapisów i dźwięku na Atari; prawa pozostają otwarte. Raport: [HWVIS1](hwvis1/REPORT.md).

# Jak grać

Przepchnij każdą skrzynię na dok. Robot chodzi w czterech kierunkach i pcha jedną skrzynię; nie ciągnie i nie przepycha dwóch naraz. Skrzynia pod złą ścianą albo w narożniku może zablokować rozwiązanie: użyj undo lub restartu. HUD pokazuje kroki, pchnięcia i zadokowane skrzynie.

Kampania ma 60 poziomów, po 15 w Energy, Hydroponic, Data Hub i Reactor. Normalna gra nie ma wyboru obszaru. BEGIN SHIFT zaczyna poziom 1; CONTINUE przywraca aktywną grę z RAM lub po zimnym starcie zapis z dysku. BEGIN SHIFT nie usuwa starego zapisu dyskowego, dopóki późniejszy udany zapis go nie zastąpi.

1. Przed grą skopiuj `neon-shift65-v1.0.0.atr`; zapis postępu modyfikuje obraz dysku.
2. Zamontuj zapisywalną kopię jako **D1:**. Ustaw **PAL**, **64 KB XL/XE**, **BASIC wyłączony**. Na prawdziwym 65XE trzymaj **OPTION** przy włączaniu, aby wyłączyć BASIC.
3. Poczekaj na loader i menu; wybierz **BEGIN SHIFT** joystickiem w porcie 1 i FIRE. **CONTINUE** odtwarza zapisany postęp.

| Wejście | Podczas gry |
| --- | --- |
| Kierunki joysticka | Chodzenie; pchanie jednej skrzyni, bez ciągnięcia |
| FIRE lub SELECT | Cofnięcie udanego kroku, do 256 kroków |
| OPTION | Restart bieżącego poziomu; zerowanie liczników i undo |
| START | Pauza; ponowny START wznawia |
| SELECT w pauzie | Zapis i powrót do menu tytułowego |
| FIRE w pauzie | Konfiguracja: lewo/prawo muzyka, FIRE efekty, START powrót |

Po rozwiązaniu poziomu zwolnij sterowanie i naciśnij **świeży FIRE**, aby przejść dalej; **SELECT** nadal cofa ostatnie pchnięcie. FIRE odebrany podczas ruchu zachowuje intencję undo. Przejście dalej automatycznie zapisuje następny poziom, a finał zapisuje ukończenie. Zimne CONTINUE odtwarza planszę i liczniki z **pustym undo**. Błąd zapisu pozwala ponowić próbę; nie wyjmuj dysku podczas I/O.

Undo wykonuje jedną akcję na naciśnięcie; przed następną zwolnij przycisk. Pauza zachowuje undo w tej samej sesji; nowy poziom i restart je zerują. Bardzo krótki impuls kierunku podczas kończenia kroku może zostać pominięty; używaj świadomego przytrzymania/zwolnienia. Ustawienia muzyki/efektów utrwalają się z udanym zapisem gry.

Launcher właściciela mapuje WASD/M i F2/F3/F4 na joystick/FIRE i OPTION/SELECT/START. Inne emulatory mają własne mapowanie.


## Zachowanie zapisu

Pauza → SELECT zapisuje bieżącą planszę i liczniki, następnie wraca do menu. FIRE przechodzący dalej automatycznie zapisuje następny poziom; końcowy FIRE zapisuje ukończenie kampanii. Restart zeruje planszę, liczniki i undo w RAM; sam nie usuwa zapisu dyskowego. Undo przechowuje ostatnie 256 udanych ruchów, także pchnięcia; ruchy zablokowane go nie zużywają. Historia undo nie trafia na dysk. Błędy zapisu są widoczne i pozwalają ponowić SELECT. Zachowaj czysty oryginał ATR i graj tylko na zapisywalnych kopiach.

[Szybki start](quick-start.pl.md) · [Wymagania i ograniczenia](../README.pl.md)
