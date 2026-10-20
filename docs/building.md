# Build from source

Install Python 3, Node.js, cc65 (`cl65`, `ca65`, `ld65`, `sim65`) and clang with sanitizer support. On macOS use `brew install cc65`; on Linux install the cc65 and Clang packages. The tools must be on PATH. No ROM or emulator is required.

```sh
git clone https://github.com/Setech-pl/neon-shift-65.git
cd neon-shift-65
python3 tools/build.py --out build/release
# alternatively: make
```

Use a new output directory. The normal disk is `build/release/candidate.atr`.
SHA-256: `a22992f1c4350d0e5c72150c6902aefdd2f485c3be5979f9da2a7bc2d32f3407`.

Verified toolchain: Python 3.15.0, Node.js v26.12.0,
cc65 2.19 (binaries V2.18), Apple clang 21.0.1.
Other tool versions are not guaranteed to produce identical bytes. On Windows use WSL with these tools; Windows has not been separately verified.

## Source layout

- `src/`: C/ASM engine and robot sources.
- `assets/`: fonts, palette and the 60 campaign maps.
- `tools/`: generators and current build composition layers.
- `experiments/`: required production builder inputs retaining their directory identifiers; no reports or alternate packages.
- `build/`: locally generated outputs, excluded from release sources.

The builder composes the current C/ASM and artwork, links cc65 and runs sanitizer and sim65 checks for logic/undo fixtures. Extra diagnostic images under build/ are not the game distribution. Public campaign data contain no solutions; the explicit `id` preserves the campaign identity stored in the released ATR and save compatibility. It is not a checksum of edited maps; assign a new identity when making a custom campaign.

[Architecture](architecture.md) · [How to play](how-to-play.md)
