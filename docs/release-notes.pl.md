[English](release-notes.md) · **Polski**

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** przy włączaniu trzymaj **OPTION**, aby wyłączyć BASIC. Nowy obraz czeka na odbiór wyglądu, przejść, zapisów i dźwięku na Atari; prawa pozostają otwarte. Raport: [HWVIS1](hwvis1/REPORT.md).

# NEON SHIFT 65 v1.0.0

**DRAFT — stabilne wydanie nie jest opublikowane.**

Sokoban na Atari 65XE PAL: prowadź robota serwisowego i przepychaj ładunki na doki w 60 poziomach Energy, Hydroponic, Data Hub i Reactor (po 15). Dostępne są: widok całej planszy, liczniki kroków/pchnięć, undo 256 kroków, restart, pauza, konfiguracja muzyki/efektów, trwały zapis, Continue i finał kampanii.

Pobierz `neon-shift65-v1.0.0.zip` (ATR, instrukcje EN/PL i licencje) albo sam `neon-shift65-v1.0.0.atr`; sprawdź `SHA256SUMS`. Bez ATR-ów testowych, ROM-u i emulatora. Skopiuj ATR przed grą, zamontuj zapisywalny jako D1:, PAL, XL/XE 64 KB, **BASIC wyłączony** (OPTION przy włączaniu 65XE), joystick w porcie 1.

Kierunki poruszają/pchają. FIRE lub SELECT cofa podczas gry; OPTION restartuje; START pauzuje. SELECT w pauzie zapisuje i wychodzi, FIRE otwiera konfigurację. Po rozwiązaniu zwolnij sterowanie i użyj świeżego FIRE, aby przejść dalej; SELECT cofa ostatnie pchnięcie. Zapis w pauzie i przejście poziomu zapisują postęp; zimne Continue przywraca planszę i liczniki bez historii undo. Zachowaj czysty oryginał; błędy zapisu pozwalają ponowić próbę.

Potwierdzone dowody dla produktu `600d934310b5ffb8e3fbf73a205f15a589a4efa6`: RELEASE1 60/60 poziomów, granice obszarów/finał, undo256, zapisy, zimne Continue i standardowe OS SIO. Niezależny re-review zamyka A-01–A-03. Commity dokumentacji i pakowania są późniejsze; bajty ATR pozostają identyczne. N-01 poprawia wyłącznie opis deskryptora/display listy.

Ograniczenia: sprzęt, wygląd i odsłuch nadal **OWNER_PENDING**; PASS emulatora nie jest odbiorem sprzętu. ATR 8192×128 wymaga obsługującego zapis nośnika; CA-2001/fizyczna dyskietka, NTSC i inne konfiguracje nie są zakwalifikowane. Uprawnienie do licencjonowania muzyki i pochodzenie historycznego First Dock wymagają decyzji przed publikacją stabilną. Repo pozostaje prywatne zgodnie z poleceniem; pobieranie wymaga dostępu do repo.

SHA-256 normalnego ATR: `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82`.

Marcin Krzetowski / Setech Game Studio; pomoc Codex w implementacji/narzędziach, niezależny audyt Claude. Własny kod/narzędzia/dokumentacja techniczna: MIT; własna twórczość: CC BY-NC-SA 4.0 z jawnymi wyjątkami; zachowane notices cc65 i Void Strike. Nazwy i logo zastrzeżone. Zobacz LICENSE, LICENSE-ASSETS i THIRD_PARTY_NOTICES.md w paczce. Utrzymanie obejmuje teraz tylko potwierdzone błędy.
