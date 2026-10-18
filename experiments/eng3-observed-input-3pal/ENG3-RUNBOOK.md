# ENG3-B-v1 — reprodukcja

Canonical raport: docs/checkpoints/eng3-observed-input-3pal/report.md.
Odziedziczone README/ENG2 runbook i niewywołane legacy helpers nie są
instrukcjami ENG3. Nie nadpisuj istniejących raw/freeze.

```sh
python3 experiments/eng3-observed-input-3pal/observed_oracle.py
python3 experiments/eng3-observed-input-3pal/run_matrix.py build
python3 experiments/eng3-observed-input-3pal/qualify_B.py matrix
python3 experiments/eng3-observed-input-3pal/qualify_B.py new
python3 experiments/eng3-observed-input-3pal/qualify_B.py pairs
python3 experiments/eng3-observed-input-3pal/qualification.py phase
python3 experiments/eng3-observed-input-3pal/run_matrix.py game
python3 experiments/eng3-observed-input-3pal/qualification.py floor
python3 experiments/eng3-observed-input-3pal/qualification.py UX
python3 experiments/eng3-observed-input-3pal/qualification.py audio
python3 experiments/eng3-observed-input-3pal/pressure.py 1 5
python3 experiments/eng3-observed-input-3pal/pressure.py 1 450
python3 experiments/eng3-observed-input-3pal/owner_smoke.py --area 1 --check
```

Polecenia mają wymagać nowych odpowiednich katalogów; cached completed
runs oznaczają ponowne odczytanie dowodów, nie świeży run. pressure/fallback
--analyze-only służy reanalizie istniejącego pełnego raw, przed kompresją.
Canonical fresh source archive, binary/tool hashes i configs: manifest.json.
Host observer pochodzi z ENG2 latch-corrected-v4 plus PC device logger.
Osobny observer-missing-dli jest wyłącznie diagnostic fault tool, nie
narzędziem użytym w głównej matrycy. Żaden observer nie daje informacji
oracle targetowi. Wszystkie jego procesy mają SDL video/audio dummy.

Reviewer potrzebuje świeżego katalogu na własny rebuild/run. Główne
ATR muszą pozostać zgodne z freeze; frozen evidence nie jest outputem
następnej iteracji. Owner launcher jest jedyną ścieżką GUI i jest WINDOWED.
