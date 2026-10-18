[English](#english) · [Polski](#polski)

## English

# NEON SHIFT 65 v1.0.0

**DRAFT — not a published stable release.**

A Sokoban game for the Atari 65XE PAL: move the service robot and push cargo onto the docks in 60 levels across Energy, Hydroponic, Data Hub and Reactor (15 per area). Full-board view, step/push counters, 256-step undo, restart, pause, music/SFX configuration, persistent saves, Continue and a campaign finale are present.

Download `neon-shift65-v1.0.0.zip` (ATR, EN/PL guides and licences) or the standalone `neon-shift65-v1.0.0.atr`; verify `SHA256SUMS`. No test-start ATRs, ROM or emulator are included. Copy the ATR before play, mount it writable as D1:, PAL, XL/XE 64 KB, **BASIC disabled** (OPTION at power-on on 65XE), joystick port 1.

Directions move/push. FIRE or SELECT undo during play; OPTION restarts; START pauses. Paused SELECT saves and exits, FIRE opens configuration. Once solved, release controls and press a fresh FIRE for next level; SELECT undoes the last push. Pause-save and level advancement write progress; cold Continue restores board and counters but not undo history. Keep the clean original; save errors allow retry.

Confirmed evidence for product commit `600d934310b5ffb8e3fbf73a205f15a589a4efa6`: RELEASE1 60/60 levels, area boundaries/finale, undo256, saves, cold Continue and standard OS SIO. Independent re-review closes A-01–A-03. Packaging and media commits are later; the ATR bytes are unchanged. N-01 corrects only the descriptor/display-list documentation.

Limits: physical hardware, appearance and listening acceptance remain **OWNER_PENDING**; emulator PASS is not hardware acceptance. The 8192×128 ATR requires supporting writable media; CA-2001/physical floppy, NTSC and other configurations are unqualified. Music licence authority and historical First Dock provenance require decisions before stable publication. The repository remains private as requested; download access follows repository access.

Normal ATR SHA-256: `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82`.

Marcin Krzetowski / Setech Game Studio; Codex development/tooling assistance, Claude independent audit. Own code/tools/technical docs: MIT; own creative content: CC BY-NC-SA 4.0 with explicit exceptions; cc65 and Void Strike notices retained. Names and logo reserved. See LICENSE, LICENSE-ASSETS and THIRD_PARTY_NOTICES.md in the package. Maintenance now covers confirmed bugs only.

---

## Polski

# NEON SHIFT 65 v1.0.0

**DRAFT — stabilne wydanie nie jest opublikowane.**

Sokoban na Atari 65XE PAL: prowadź robota serwisowego i przepychaj ładunki na doki w 60 poziomach Energy, Hydroponic, Data Hub i Reactor (po 15). Dostępne są: widok całej planszy, liczniki kroków/pchnięć, undo 256 kroków, restart, pauza, konfiguracja muzyki/efektów, trwały zapis, Continue i finał kampanii.

Pobierz `neon-shift65-v1.0.0.zip` (ATR, instrukcje EN/PL i licencje) albo sam `neon-shift65-v1.0.0.atr`; sprawdź `SHA256SUMS`. Bez ATR-ów testowych, ROM-u i emulatora. Skopiuj ATR przed grą, zamontuj zapisywalny jako D1:, PAL, XL/XE 64 KB, **BASIC wyłączony** (OPTION przy włączaniu 65XE), joystick w porcie 1.

Kierunki poruszają/pchają. FIRE lub SELECT cofa podczas gry; OPTION restartuje; START pauzuje. SELECT w pauzie zapisuje i wychodzi, FIRE otwiera konfigurację. Po rozwiązaniu zwolnij sterowanie i użyj świeżego FIRE, aby przejść dalej; SELECT cofa ostatnie pchnięcie. Zapis w pauzie i przejście poziomu zapisują postęp; zimne Continue przywraca planszę i liczniki bez historii undo. Zachowaj czysty oryginał; błędy zapisu pozwalają ponowić próbę.

Potwierdzone dowody dla produktu `600d934310b5ffb8e3fbf73a205f15a589a4efa6`: RELEASE1 60/60 poziomów, granice obszarów/finał, undo256, zapisy, zimne Continue i standardowe OS SIO. Niezależny re-review zamyka A-01–A-03. Commity dokumentacji i pakowania są późniejsze; bajty ATR pozostają identyczne. N-01 poprawia wyłącznie opis deskryptora/display listy.

Ograniczenia: sprzęt, wygląd i odsłuch nadal **OWNER_PENDING**; PASS emulatora nie jest odbiorem sprzętu. ATR 8192×128 wymaga obsługującego zapis nośnika; CA-2001/fizyczna dyskietka, NTSC i inne konfiguracje nie są zakwalifikowane. Uprawnienie do licencjonowania muzyki i pochodzenie historycznego First Dock wymagają decyzji przed publikacją stabilną. Repo pozostaje prywatne zgodnie z poleceniem; pobieranie wymaga dostępu do repo.

SHA-256 normalnego ATR: `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82`.

Marcin Krzetowski / Setech Game Studio; pomoc Codex w implementacji/narzędziach, niezależny audyt Claude. Własny kod/narzędzia/dokumentacja techniczna: MIT; własna twórczość: CC BY-NC-SA 4.0 z jawnymi wyjątkami; zachowane notices cc65 i Void Strike. Nazwy i logo zastrzeżone. Zobacz LICENSE, LICENSE-ASSETS i THIRD_PARTY_NOTICES.md w paczce. Utrzymanie obejmuje teraz tylko potwierdzone błędy.
