# Third-party notices

Project code is MIT (LICENSE); own creative content is CC BY-NC-SA 4.0 with
explicit exceptions (LICENSE-ASSETS). This file does not claim the absence
of external code. Detailed evidence and open decisions: docs/publish1/RIGHTS.md; follow-up docs/hwvis1/RIGHTS.md (PUBLISH2, still OPEN).

## Contained in the ATR or repository

| Component | Actual input / use | Terms and attribution |
| --- | --- | --- |
| cc65 runtime | candidate.map links atari.lib startup, memcpy, arithmetic and stack helpers into the normal ATR | Original cc65 licence in docs/licenses/cc65.txt, copied verbatim from used cc65 2.19 distribution; runtime headers retain their authors. Original authors include Ullrich von Bassewitz and contributors; this project does not claim authorship. |
| Void Strike menu font/title | assets/graphics/mono-font.json adapted from frontend-h31.json at d67d560e8367da0347ce03de910f475952de44b8 | © 2026 Marcin Krzetowski (Setech Game Studio), CC BY-NC-SA 4.0. Complete adaptation notice: assets/graphics/mono-font-NOTICE.md. |
| Void Strike splash/loader definitions and tools | experiments/eng3-observed-input-3pal/reference/{void-loader.json,boot-splash-assets.mjs,broadside-lzss.mjs,void-generator.mjs}, frozen-inputs.json | MIT for code, original asset conditions for pixels/font/audio definitions. Original notices retained in that reference directory, assets/licenses/ and docs/licenses/. Adapted for NEON SHIFT loader/title/footer; no claim that Void Strike gameplay or hardware results apply. |
| Service Current music / player | compile.py music composition, hardware.s tracker and instruments, generated music.nrq | Historical LICENSE-music.md in experiments/renderer-a3, renderer-a4, renderer-a5, and matching later trees declares CC0 for composition/instruments and MIT for the new player (© 2026 Setech Game Studio). Authority for CC0 remains OPEN; preserve the historical grant rather than silently overwrite it. |
| Earlier map data | src/levels_data.c (20 inherited layouts), assets/levels/prototypes.json and generated prototype_assets.c copies | First Dock/REACTOR STORE lineage is stated but the original author/permission is not established. No blanket relicensing. These are repository/build fixtures, separate from final 60-map NSLV campaign. |
| Final campaign | assets/levels/camp2-b/campaign.json, plus earlier campaign/samples under assets/levels/ | Final metadata declare 46 new project layouts, 14 retained project layouts, no external level collection. The owner's selected content licence applies to project-owned maps; it is not proof of authorship of every historical map. |
| Reference image | reference/vis1-owner/energy-owner-reference.png | Owner-supplied visual reference, not a bitmap input to the ATR; origin/permission to redistribute the image is not recorded. Excluded from blanket licensing. |

Original Void Strike code notice: docs/licenses/void-strike-MIT.txt.
Original asset notice: docs/licenses/void-strike-LICENSE-ASSETS.md (applies to
upstream content, not a blanket licence for this game). Notices are included
in the player ZIP. Embedded source comments and older notices are preserved.

## Build and test tools, not included in the player package

cc65/cl65/ca65/ld65/sim65 (local distribution 2.19, binaries report V2.18),
Python 3, Node.js and clang are used by the production builder. Atari800 7.1.2
with a local read-only observer is GPL-2.0-or-later testing infrastructure.
ffmpeg is used only to encode promotional captures; no ffmpeg code is linked.
No emulator binary or ROM is included in dist or the player ZIP. The NS65
observer headers are project tools; distribution of a combined emulator would
have the emulator's GPL obligations. Python standard-library tools need no
vendored Python runtime. No Pillow dependency is required by the media script.

## Fonts, ROM data and promotional captures

Production fonts come from the explicit mono-font JSON and project procedural
pixel sources; the observed build has no input ROM file. The Atari OS used
by the emulator is privately supplied for testing and is not part of the ATR
or player ZIP. Existing historical evidence archives may contain private config
paths and RAM captures: they are retained locally as evidence, not copied into
new publication payloads. No claim about licensing unidentified historical
archive contents is made.

New docs/media GIFs and PNGs are actual captures of the product, not generated
illustrations. Code/tool assistance was provided by Codex; the independent
source audit is labelled Claude. Attribution does not invent human authorship
for individual generated assets. Names and marks are reserved (LICENSE-ASSETS).
