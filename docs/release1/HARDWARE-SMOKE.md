> Historical RELEASE1 instructions and unchanged pending result. Current artifact paths and launcher: [EN](../owner-smoke.md) / [PL](../owner-smoke.pl.md). See [relocation](../publish1/ARTIFACTS.md).

# NEON SHIFT 65 — krótki odbiór sprzętowy

**Wynik: OWNER_PENDING.** Atari 65XE PAL, standardowe 64 KB, joystick 1,
SIO2SD. Wykonuj na kopiach ATR-ów. Zachowaj czyste oryginały i ich SHA-256.
Nie trzeba ręcznie rozwiązywać 60 poziomów. Około 15–20 minut, zależnie od SIO2SD.

1. Zamontuj normalny `neon-shift65-v1.0-candidate.atr` jako D1, odblokuj
   zapis, wyłącz BASIC (OPTION podczas włączania). Sprawdź splash, loader,
   menu, czytelny wybór i muzykę. BEGIN SHIFT: cała plansza i HUD mieszczą się
   na ekranie, robot/skrzynia/dok są rozróżnialne.
2. Joystick: prawo, zwolnienie, FIRE undo; powtórz z SELECT. Sprawdź
   przytrzymanie kierunku i pojedyncze undo po przytrzymanym FIRE. OPTION
   restartuje poziom i zeruje liczniki/historię. START pauza → FIRE konfiguracja
   → przełącz muzykę lewo/prawo → START → START gra. Muzyka wraca po wznowieniu.
3. Po restarcie wykonaj R, START, SELECT: zapis 1 i powrót do menu.
   CONTINUE, wykonaj L, START, SELECT: zapis 2. Wyłącz i ponownie włącz Atari;
   CONTINUE musi odtworzyć STEPS=02, PUSHES=01; undo jest puste.
4. Zabezpiecz roboczy ATR przed zapisem w SIO2SD. Wykonaj ruch, START,
   SELECT: czytelny SAVE FAILED, pozostaje pauza. Odblokuj zapis i naciśnij
   SELECT ponownie. Zimne CONTINUE odtwarza nowy stan. Muzyka po SIO wraca.
5. Uruchom kolejno czyste test-01 / test-16 / test-31 / test-46. Każdy
   przechodzi pełny boot i prawdziwy odczyt planszy. Sprawdź cztery dominanty:
   żółta Energy, zielona Hydro, fuksja Data, czerwona Reactor; ściany,
   podłogę, panele, wentylację, robota, dok i moduł. W każdym obszarze
   wykonaj kilka ruchów, undo i restart. Te obrazy mają osobne zapisy.
6. Przygotuj krótkie ścieżki przejść i finału na komputerze:

   ```sh
   python3 tools/release1_owner_smoke.py --prepare-routes
   ```

   Skopiuj cztery wygenerowane **robocze** obrazy z
   `build/release1/hardware-routes/` na SIO2SD. To kopie normalnego kandydata
   z poprawnym zapisem tuż przed ostatnim ruchem poziomów 15/30/45/60;
   kod, kampania i grafika są bez zmian. Kierunki podaje `routes.json`.
   Dla każdego: zimny boot → CONTINUE → ostatni kierunek → zwolnij → FIRE.
   Oczekiwane przejścia: 15→16, 30→31, 45→46 i finał 60/60. Przed FIRE
   sprawdź moduły na dokach; SELECT cofa ostatnie pchnięcie. Po finale
   zimne CONTINUE wraca do finału. Zanotuj muzykę przed i po odczytach.

Launcher emulatora dla właściciela otwiera okno:

```sh
python3 tools/release1_owner_smoke.py
python3 tools/release1_owner_smoke.py --area 31
python3 tools/release1_owner_smoke.py --route 60
```

WASD + M (FIRE), F2 OPTION, F3 SELECT, F4 START. Fizyczny joystick emulatora:
`--physical-joystick`. Launcher zachowuje prywatny dysk gry między startami.
`--check` tylko przygotowuje polecenie, bez okna. Można też uruchomić
`PLAY-WINDOWED.command` z tego katalogu. Globalny config Atari800 pozostaje
bez zmian. Test na emulatorze właściciela nie zastępuje fizycznego Atari.

Zapisz: model Atari, wersję SIO2SD/firmware, nośnik, joystick, monitor,
SHA normalnego ATR przed zapisem, wyniki punktów 1–6 i uwagi do wyglądu.
Odbiór sprzętu: **OWNER_PENDING**. Odbiór wyglądu: **OWNER_PENDING**.
Po dostarczeniu zmieniamy wyłącznie konkretne usterki zgłoszone w odbiorze.
