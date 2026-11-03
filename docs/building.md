# Reproduce the archival R6 ATR

From the repository or unpacked source ZIP:

```sh
make OUT=build/release
python3 tests/source_base1_check.py build/release
```

Use a new output directory. Requirements on PATH: Python 3, Node.js, cc65 (cl65, ca65, ld65, sim65), clang, make. Known toolchain: Python 3.15.2, Node 26.12.1, cc65 package 2.19 (binaries V2.18), Apple clang 21.0.0, GNU Make 3.81. No ROM or emulator is required to build.

Expected `build/release/candidate.atr`: 1,048,592 bytes, SHA-256 `72f1d0643c562937312d71beeaa7965cda5fd5213b9e3891f292bf55f12dc477`.

The builder runs host sanitizer and actual 6502 replays plus asset/package/budget checks. It composes the historical generator stages from the public src/assets/cfg/tools tree; it needs no old experiments, local artifacts or private files. `assets/build-inputs.json` records the preserved inputs. Historical branches/options inside generators are retained to preserve output; only `make` is the supported current product entry point.

Optional bounded smoke needs Python with Pillow/numpy, a separately prepared Atari800 7.1.2 NS65 observer and your legally supplied OS ROM configuration:

```sh
python3 tests/source_base1_smoke.py --build build/release --out .cache/smoke \
  --observer /path/to/observer/src/atari800 --config /path/to/legal.cfg
```

This tests private copies: menu, selector, four areas, move/push/undo, options/resume, save and cold Continue. Fixture save records choose area starts; game state is not injected into RAM. No physical hardware claim follows. Optional observer preparation: supply `NEON_ATARI_SOURCE` pointing at an already configured Atari800 source tree and optionally `NEON_OBSERVER_OUT` (default `.cache/observer`), then run `python3 tools/prepare_emulator.py`. Emulator and ROM are not distributed.

To export the committed public tree from a Git checkout: `python3 tools/export_source.py --out /path/to/source.zip`. The release source ZIP already contains the complete build tree and requires no Git checkout.

[README](../README.md)
