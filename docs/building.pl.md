# Odtworzenie ATR R6

W katalogu repozytorium lub rozpakowanych źródeł:

```sh
make OUT=build/release
python3 tests/source_base1_check.py build/release
```

Katalog wynikowy musi być nowy. W PATH: Python 3, Node.js, cc65 (cl65/ca65/ld65/sim65), clang i make. Build nie wymaga ROM-u, emulatora, Git ani dawnego projektu. Wynik: `build/release/candidate.atr`, 1 048 592 bajty.

SHA-256: `72f1d0643c562937312d71beeaa7965cda5fd5213b9e3891f292bf55f12dc477`.

Builder uruchamia replay z sanitizerami i replay rzeczywistego kodu 6502. Opcjonalny krótki smoke działa wyłącznie na kopiach ATR i wymaga osobnego obserwatora Atari800 oraz legalnej konfiguracji ROM. [Wersje narzędzi i polecenia smoke](building.md). LOAD-FIX1 i testy sprzętowe pozostają niewykonane.

[README](../README.pl.md)
