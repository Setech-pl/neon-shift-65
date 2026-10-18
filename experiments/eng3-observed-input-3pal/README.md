# ART3 — offline contextual decoration

Frozen base: ART2.1 `b1eb77f1c713f9a2fdbc67e084e40b9120a123b4`. Branch `feature/art3-contextual-decoration`. Existing sources, old checkpoints and untracked work are protected by the preflight manifest. No ENG1 worktree/branch was found.

`decoration.py` chooses small floor clusters outside narrow passages and dock neighbourhoods, sparse straight-wall details, quieter border patterns and separate device arrangements for each area. `compile.py` applies those choices to the existing five-bank scene ABI. Canonical animation record order is preserved when devices move. All64 final XEX binaries are identical to ART2.1; robot/containers/docks, palettes, schedule and geometry are immutable. Expected colors are from the frozen `palette-oracle.json`, not candidate images.

Two alternatives were measured before implementation: A uses existing wall variants; B adds rare interior notches. Final B has more useful composition at zero resident/RAM growth. Both area3 A and B reproduce a new external-input boundary regression versus ART2.1 (missing undo image and RZ→ZR). We retain B and report **ART scope PASS / overall qualification FAIL / ENGINE FAIL**, without altering the engine or tuning CRC/padding to a test phase. InitialB and trialA evidence are preserved. `candidate-binding.json` is the final runtime freeze; tests/report tooling are separately manifested.

```sh
python3 experiments/art3-contextual-decoration/budget_variants.py
python3 experiments/art3-contextual-decoration/run_matrix.py build
python3 experiments/art3-contextual-decoration/byte_audit.py
python3 experiments/art3-contextual-decoration/context_audit.py
python3 experiments/art3-contextual-decoration/verify_matrix.py oracle
python3 experiments/art3-contextual-decoration/verify_matrix.py game
python3 experiments/art3-contextual-decoration/verify_matrix.py export
python3 experiments/art3-contextual-decoration/verify_matrix.py media
python3 experiments/art3-contextual-decoration/verify_matrix.py dock
python3 experiments/art3-contextual-decoration/rebuild.py
# For each area1..4: qualify.py N obstacles measure; audio_video.py N
python3 experiments/art3-contextual-decoration/native_palette_audit.py
python3 experiments/art3-contextual-decoration/regression_summary.py
python3 experiments/art3-contextual-decoration/package_evidence.py
python3 experiments/art3-contextual-decoration/comparisons.py
python3 experiments/art3-contextual-decoration/resource_report.py
python3 experiments/art3-contextual-decoration/owner_smoke.py --area 1 --check
```

Build requires the unchanged cc65/clang/NumPy tools and preserved ART2.1/A5c/UX2 inputs. Native evidence requires the existing Atari800 observer, local OS ROM and private emulator configuration; no ROM is redistributed. Qualification uses original logic and fetch oracles. On ANTIC2 HUD the foreground is `HUD hue | $0E` (area4 `$3E`); this differs from gameplay PF0 `$3C`. This hardware-derived expectation is explicit in the measurement adapter.

`NEON_ART2_AREA=1..4` and `NEON_ART2_BUILD` remain the existing build-time controls. `ART3_VARIANT=A` is the documented comparison alternative; final default is B. Do not overwrite frozen evidence when experimenting: use a different output root. `freeze.py` is for a new candidate before review, not for silently rebinding a reviewed candidate.

The launcher is explicitly WINDOWED, uses a private config and disables config autosave. Agent runs are headless or `--check` only. Visible playback, listening, hardware/SIO2SD and M1 OWNER PASS remain unconfirmed. See `docs/checkpoints/art3-contextual-decoration/` for reports, native comparisons, diagnostic bank/actor atlases, portable traces and manifests.
