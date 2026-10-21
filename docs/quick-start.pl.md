[English](quick-start.md) · **Polski**

# Szybki start

Do gry potrzebujesz obrazu dysku i emulatora Atari. Nie musisz instalować Git, Pythona, Node.js ani kompilatora.

[Zagraj w przeglądarce](https://setech-pl.github.io/setech-arcade/play/neon-shift-65/) · [Windows](#windows--altirra) · [macOS](#macos--atari800) · [Prawdziwe Atari / SIO2SD](#prawdziwe-atari--sio2sd)

## Pobierz grę

1. Otwórz [stronę wydań](https://github.com/Setech-pl/neon-shift-65/releases) i pobierz **neon-shift65.atr** z załączników wydania. Możesz też pobrać **neon-shift65-player.zip** i najpierw go rozpakować. Archiwa GitHub **Source code** służą do budowania gry, nie są najkrótszą drogą do uruchomienia.
2. Zachowaj pobrany ATR jako oryginał. Zrób drugą kopię o nazwie **neon-shift65-play.atr** w folderze z prawem zapisu, np. Pobrane.
3. Graj na tej kopii. Postęp jest zapisywany **wewnątrz ATR**. Nie uruchamiaj obrazu bezpośrednio z ZIP-a ani w trybie tylko do odczytu.

ATR to startowy obraz dysku Atari, a nie aplikacja Windows lub macOS. Zamontuj go jako **D1:**. Wybierz **XL/XE z 64 KB**, **PAL**, **BASIC OFF** i brak kartridża.

## Windows — Altirra

1. Pobierz stabilną wersję programu z [oficjalnej strony Altirra](https://www.virtualdub.org/altirra.html). Dla typowego PC z procesorem Intel/AMD wybierz x86/x64; dla Windows na ARM — ARM64.
2. Rozpakuj cały ZIP emulatora. Na 64-bitowym Windows Intel/AMD uruchom **Altirra64.exe**, a na innej architekturze odpowiedni program z paczki.
3. W konfiguracji pierwszego uruchomienia lub **System → Configure System** wybierz **800XL / XL-XE**, **64 KB**, **PAL** oraz **BASIC off**. Możesz zacząć od wbudowanego **AltirraOS** — ta konfiguracja nie wymaga osobnego ROM-u Atari.
4. Wybierz **File → Boot Image** i otwórz **neon-shift65-play.atr**. W panelu stacji sprawdź, czy D1: pozwala na zapis, a zmiany są zachowywane w tej kopii pliku zamiast odrzucane.
5. W menu **Input** włącz joystick klawiaturowy w **porcie 1**. Profil ze strzałkami zwykle używa **strzałek i lewego Ctrl jako FIRE**. Nazwy zależą od wersji; w razie potrzeby sprawdź **Input Mappings**.
6. Kliknij okno emulatora. Poczekaj na loader i menu, wybierz **BEGIN SHIFT** i naciśnij FIRE. **CONTINUE** odtwarza zapisaną grę.

| Działanie | Sterowanie Atari | Domyślne klawisze konsoli Altirra / opisany profil joysticka |
| --- | --- | --- |
| Ruch i pchanie; poruszanie po menu | Kierunki joysticka | Strzałki |
| Wybór w menu; undo podczas gry | FIRE | Lewy Ctrl |
| Undo | SELECT | F3 |
| Restart poziomu | OPTION | F4 |
| Pauza / wznowienie | START | F2 |
| Zapis i powrót do menu | START, następnie SELECT | F2, następnie F3 |

**Altirra i Atari800 inaczej przypisują START oraz OPTION.** Korzystaj z tabeli właściwego emulatora. Własne mapowanie może zmieniać te klawisze. Niektóre klawiatury wymagają użycia Fn z klawiszami funkcyjnymi.

## macOS — Atari800

Poniższy sposób korzysta z Terminala i [Homebrew](https://brew.sh/). Jeżeli nie masz Homebrew, zainstaluj je według oficjalnej instrukcji. Bez instalowania programów możesz zagrać przez link do przeglądarki powyżej.

1. Zainstaluj [Atari800](https://formulae.brew.sh/formula/atari800):

   ```sh
   brew install atari800
   ```

2. Umieść zapisywalną kopię **neon-shift65-play.atr** w folderze Pobrane.
3. Uruchom emulator w oknie:

   ```sh
   atari800 -xl -pal -nobasic -xl-rev altirra -nopatch -windowed "$HOME/Downloads/neon-shift65-play.atr"
   ```

   Polecenie wybiera XL z 64 KB, PAL, BASIC off, wbudowany Altirra OS oraz standardowe OS SIO. Jeżeli kopia jest w innym folderze, zmień ścieżkę w cudzysłowie. ATR jest argumentem dyskowym; nie używaj opcji ładowania plików wykonywalnych.
4. Naciśnij **F1**, aby otworzyć menu emulatora (lub **Fn + F1**, jeśli macOS przechwytuje klawisz). W **Controller Configuration** wybierz joystick klawiaturowy dla **portu 1** — pierwszego portu, czasem numerowanego wewnętrznie jako 0. W **Define layout** przypisz kierunki i FIRE. Wygodny układ to **W/A/S/D oraz M jako FIRE**.
5. W **Disk Management** sprawdź, czy D1: zawiera roboczą kopię w trybie odczytu i zapisu. Wróć do gry klawiszem Esc.
6. Wybierz **BEGIN SHIFT** skonfigurowanym joystickiem i FIRE. Do zapisanej gry wróć przez **CONTINUE**.

| Działanie | Sterowanie Atari | Klawisze konsoli Atari800 / proponowany układ |
| --- | --- | --- |
| Ruch i pchanie; poruszanie po menu | Kierunki joysticka | W/A/S/D po ich przypisaniu |
| Wybór w menu; undo podczas gry | FIRE | M po przypisaniu |
| Undo | SELECT | F3 |
| Restart poziomu | OPTION | F2 |
| Pauza / wznowienie | START | F4 |
| Zapis i powrót do menu | START, następnie SELECT | F4, następnie F3 |
| Ustawienia emulatora | — | F1 |

Na MacBooku w razie potrzeby używaj Fn z F1–F4 albo włącz standardowe klawisze funkcyjne w ustawieniach klawiatury macOS. Klawisz Option Maca nie jest w tej konfiguracji przyciskiem OPTION Atari.

Projekt ma istniejące kontrole w emulatorze Atari800. Powyższe kroki opierają się na dokumentacji emulatorów; nie stanowią deklaracji nowego testu gry w Altirra ani w paczce Homebrew.

## Zapis i typowe problemy

Aby zapisać grę, naciśnij Atari **START**, a w pauzie **SELECT**. Zaczekaj na menu przed zamknięciem emulatora. Jeśli emulator pyta o zapis zmian dysku, zachowaj je w roboczym ATR. Otwórz ponownie **tę samą kopię** i wybierz **CONTINUE**. Historia undo nie wraca po zimnym starcie.

| Problem | Co sprawdzić |
| --- | --- |
| Pojawia się BASIC albo SELF TEST | Wybierz XL/XE, 64 KB, PAL, BASIC off, usuń kartridż i uruchom ATR przez zimny start z D1:. |
| Robot nie reaguje | Uaktywnij okno i skonfiguruj joystick w porcie 1. Mapowanie klawiatury jest ustawieniem emulatora. |
| Zamiast pauzy następuje restart | START i OPTION mają inne klawisze w Altirra oraz Atari800; sprawdź odpowiednią tabelę. |
| Zapis nie działa albo CONTINUE nie pamięta postępu | Używaj rozpakowanej zapisywalnej kopii, wyłącz ochronę zapisu i zachowuj zmiany dysku emulatora. Otwieraj ten sam ATR. |
| Kolory lub tempo wyglądają inaczej | Sprawdź PAL i normalną prędkość; przy porównywaniu obrazów wyłącz turbo oraz dodatkowe efekty obrazu. |
| Ładowanie trwa długo | Polecenie Atari800 celowo używa standardowego OS SIO. Poczekaj na menu; ładowanie nie jest natychmiastowe. |

## Prawdziwe Atari / SIO2SD

1. Skopiuj roboczy ATR na zapisywalną kartę SIO2SD i zamontuj go jako **D1:**.
2. Przy zimnym starcie Atari trzymaj **OPTION / BASIC OFF**.
3. Poczekaj na menu. Joystick w porcie 1 i FIRE wybierają **BEGIN SHIFT** lub **CONTINUE**.

Cel sprzętowy: Atari 65XE PAL, 64 KB RAM; XL/XE PAL 64 KB sprawdzono w emulatorze. Obraz ma 8192 sektory po 128 B (1 048 592 B z nagłówkiem). SIO2SD musi obsługiwać ten format i zapis. Odbiór fizycznego Atari/SIO2SD pozostaje niepotwierdzony w opublikowanym wydaniu; NTSC i fizyczne stacje nie są zakwalifikowane.

## Setech Arcade

[Otwórz grę](https://setech-pl.github.io/setech-arcade/play/neon-shift-65/), uaktywnij pole gry i rozpocznij rozgrywkę. Strzałki/WASD = ruch, Z/X = FIRE, F2 = OPTION, F3 = SELECT, F4 = START.

Postęp jest zapisywany w IndexedDB tej przeglądarki; wyczyszczenie danych witryny usuwa zapis. Pobrany ATR jest świeżym dyskiem, osobnym od zapisu przeglądarki. Pełne sterowanie klawiszami konsoli wymaga klawiatury; dotyk i gamepad udostępniają ruch oraz FIRE.

[Instrukcja](how-to-play.pl.md) · [README](../README.pl.md) · [Sterowanie i opcje Atari800](https://github.com/atari800/atari800/blob/master/DOC/USAGE)
