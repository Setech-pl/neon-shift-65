# Components, credits and licences

© 2026 Marcin Krzetowski (Setech Game Studio). Project code and engineering
documentation: MIT. Creative content and complete ATR: CC BY-NC-SA 4.0, with
the exceptions below. See [LICENSE-ASSETS](LICENSE-ASSETS).

| Component | Use and attribution | Terms |
| --- | --- | --- |
| cc65 runtime | Linked startup, memory, arithmetic and stack helpers; Ullrich von Bassewitz and contributors | [Original cc65 licence](docs/licenses/cc65.txt) |
| Void Strike 65 menu font/title | Adapted `frontend-h31.json` at `d67d560e8367da0347ce03de910f475952de44b8`; © 2026 Marcin Krzetowski / Setech Game Studio | [Adaptation notice](assets/graphics/mono-font-NOTICE.md), [upstream asset terms](docs/licenses/void-strike-LICENSE-ASSETS.md) |
| Void Strike splash/loader definitions and conversion tools | Required inputs in `experiments/eng3-observed-input-3pal/reference/`; adapted for this game's loader/title/footer | Content CC BY-NC-SA 4.0; tools [MIT](docs/licenses/void-strike-MIT.txt); original notices retained beside inputs |
| Service Current | Composition and instruments in `compile.py`, tracker in `hardware.s`; developed for NEON SHIFT 65 | Existing [CC0-1.0 composition/instrument and MIT player notice](docs/licenses/service-current-LICENSE-music.md) retained |
| Campaign and earlier map fixtures | Project work begun by the owner with Claude Code and continued with Codex; owner confirmed this provenance | Project content licence; no third-party level collection is attributed |

External build tools: Python 3, Node.js, cc65 and clang. No tool executable,
emulator, ROM or private configuration is bundled. Atari800 is separate
GPL-2.0-or-later emulator software; no emulator code is linked into the game.
Actual gameplay captures are included under the content licence.
