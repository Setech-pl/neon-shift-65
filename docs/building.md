# Production build and packaging

The current candidate is HWVIS1, **OWNER_PENDING**. Source checkpoint is in
[hwvis1/source-checkpoint.txt](hwvis1/source-checkpoint.txt); campaign unchanged.
Hardware boot requires OPTION held at power-on (BASIC OFF).

## Build the product

Install Python 3, Node.js, cc65/cl65/ca65/ld65/sim65 and clang. The qualified
local cc65 package is 2.19; its binaries identify as V2.18. Current exact tool
versions are recorded in dist/manifest.json. No emulator or ROM is needed to
build. From the repository root, choose an output directory that does not exist:

```sh
python3 tools/v1_build.py --out build/my-release
```

The normal product is `build/my-release/candidate.atr`. With the qualified
versions its SHA-256 must be
`48b6f81986d8ffb705830aa7f2dfffdb4419b3508a8409be006210441bac8c7d`.
For a test-start variant add `--test-start 1`, `16`, `31` or `46` and use a new
output directory each time. Do not use `--rc1` or the band-colour diagnostic for
this release. The root Makefile and its prototype tests are historical.

The builder copies ENG3 source and applies existing offline VIS1-r2,
PRODUCT1/FINISH1/FINISH2/RELEASE1 overlays. All required frozen reference files
are tracked. No dependency on an existing generated build or /tmp is allowed.
The 216 exact pinned inputs (including historical build helpers) are listed in
[hwvis1/source-inputs.json](hwvis1/source-inputs.json). Materialize a fresh
source-only tree and build with no inherited output:

```sh
python3 tools/hwvis1_sources.py --out build/fresh-sources
python3 build/fresh-sources/tools/v1_build.py --out build/normal
```

The second command resolves the output relative to that fresh tree. Missing
inputs or mismatched hashes are errors. In a reviewed snapshot export without
the original Git objects, the source materializer verifies available source
files against the same lock. It never silently accepts changed source bytes.
A fresh HWVIS1 pair of isolated source builds reproduced the candidate byte for byte; this
is an input-availability check, not a new full engine audit.

## Prepare immutable distribution and owner media

```sh
python3 tools/hwvis1_prepare.py
python3 tools/hwvis1_package.py
```

Preparation verifies five current hashes and empty save sectors, keeps all existing
owner play disks, and generates the internal kit under build/owner-smoke/hwvis1/.
Missing variants can be rebuilt from current locked compiler inputs. Packaging
reuses the deterministic PUBLISH1 ZIP layout and updates manifest/checksums;
only the normal ATR is included. PUBLISH1 report and scripts remain historical.
Use `--pre-hwvis1` solely to reproduce historical RELEASE1. Normal builds apply
HWVIS1 after the existing RELEASE1 overlay; compiler inputs are locked above.

For media use [the capture recipe](media/README.md). ffmpeg is optional for game
builds and required for GIF regeneration. Supply your own legal ROM config and
an Atari800 7.1.2 NS65 observer for capture. The observer's code/setup is retained
under tools/emulator_trace.h and tools/prepare_emulator.py. The latter requires a separately configured
Atari800 source tree (NEON_ATARI_SOURCE); it copies and builds locally rather
than shipping an emulator.
All agent emulator sessions are headless. Owner launcher is WINDOWED and takes
explicit emulator/config paths; see [owner smoke](owner-smoke.md).
