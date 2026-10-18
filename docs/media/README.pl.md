[English](README.md) · **Polski**

# Galeria rozgrywki

[Główny montaż](neon-shift65.gif): cztery fragmenty po 200 ramek PAL, łącznie około 16 sekund, z jawnymi cięciami między obszarami. Energy pokazuje pchnięcie na dok, SELECT undo i ponowne dokowanie. Pozostałe fragmenty obejmują tylko krótkie początki, bez pełnych rozwiązań późnych map.

![Energy: dokowanie, undo i ponowne dokowanie](area-1.gif)
![Hydroponic: początkowe ruchy i undo](area-2.gif)
![Data Hub: początkowe ruchy i undo](area-3.gif)
![Reactor: początkowe ruchy i undo](area-4.gif)

Menu, loader i wszystkie obszary widać też w [głównym README](../../README.pl.md). Screenshot Energy to poziom 2, GIF Energy to poziom 1. Hydro/Data/Reactor to poziomy 16/31/46 z osobnych ATR-ów startowych. Sektory kampanii/grafiki są zgodne z normalnym wydaniem. Start i tożsamość zapisu są inne; normalna gra nie oferuje wyboru obszaru.

Rzeczywiste klatki zimnego bootu Atari800 7.1.2 z kopii wskazanych ATR-ów, bez generowanej gry, edycji obiektów, zmian palety lub wygładzania. Piksele 336×240 powiększono dokładnie 2× do 672×480. Pobierana jest co piąta ramka PAL; czas GIF zachowuje czas gry (zaokrąglenie do setnych sekundy). Turbo gospodarza tylko usuwa oczekiwanie na komputerze.

Odtworzenie: `python3 tools/hwvis1_prepare.py`, następnie NEON_ATARI800 wskazujący Atari800 7.1.2 z obserwatorem NS65 i NEON_ATARI_CONFIG wskazujący prywatny config legalnych ROM-ów; uruchom `python3 tools/hwvis1_media.py`. Wymagany ffmpeg. [Manifest](manifest.json) zawiera hashe, konfigurację, ramki, wejścia, tempo i montaż; [zgodność](product-equivalence.json) opisuje różnice źródeł i zgodność danych. Surowe klatki/RAM/configi zostają ignorowane w build/owner-smoke/hwvis1/media. Emulator i ROM nie są dystrybuowane.

HWVIS1: standard OS SIO (`-nopatch`), BASIC OFF, XL/XE 64 KB PAL. All current GIFs and screenshots were refreshed from the new ATRs. Hardware/appearance: OWNER_PENDING.
