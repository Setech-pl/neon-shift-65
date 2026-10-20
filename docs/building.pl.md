# Budowanie ze źródeł

Zainstaluj Python 3, Node.js, cc65 (`cl65`, `ca65`, `ld65`, `sim65`) i clang z obsługą sanitizerów. Na macOS cc65 jest dostępne przez `brew install cc65`; na systemach Linux użyj pakietu cc65 i Clang. Wymagana jest powłoka i dostępne w PATH narzędzia. Nie potrzeba ROM-u ani emulatora.

```sh
git clone https://github.com/Setech-pl/neon-shift-65.git
cd neon-shift-65
python3 tools/build.py --out build/release
# alternatively: make
```

Użyj nowego katalogu wyjściowego. Normalny dysk to `build/release/candidate.atr`.
SHA-256: `a22992f1c4350d0e5c72150c6902aefdd2f485c3be5979f9da2a7bc2d32f3407`.

Sprawdzone narzędzia: Python 3.15.0, Node.js v26.12.0,
cc65 2.19 (binaries V2.18), Apple clang 21.0.1.
Inne wersje nie mają gwarancji identycznego wyniku. Windows: użyj środowiska WSL z tymi narzędziami; nie wykonano osobnej weryfikacji Windows.

## Układ źródeł

- `src/`: C/ASM silnika i robota.
- `assets/`: fonty, paleta i 60 map kampanii.
- `tools/`: generatory i warstwy kompozycji aktualnego builda.
- `experiments/`: wymagane wejścia produkcyjnego buildera o zachowanych identyfikatorach katalogów; bez raportów i alternatywnych paczek.
- `build/`: wyniki generowane lokalnie, nie są częścią źródeł wydania.

Builder składa aktualne C/ASM i grafikę, linkuje cc65 oraz wykonuje próby sanitizer i sim65 dla fixture’ów logiki/undo. Dodatkowe obrazy diagnostyczne w build/ nie są dystrybucją gry. Publiczne dane map nie zawierają rozwiązań; jawne pole `id` zachowuje identyfikator kampanii zapisany w wydanym ATR i kompatybilność zapisu. Nie jest to suma kontrolna zmienianych map — przy tworzeniu własnej kampanii nadaj nowy identyfikator.

[Architektura](architecture.md) · [Instrukcja](how-to-play.pl.md)
