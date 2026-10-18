Font provenance for NEON SHIFT 65

The full menu font in `mono-font.json` is adapted from `fontRowsHex` in
[Void Strike 65, assets/graphics/frontend-h31.json](https://github.com/Setech-pl/void-strike-65/blob/d67d560e8367da0347ce03de910f475952de44b8/assets/graphics/frontend-h31.json).
Reference SHA: `d67d560e8367da0347ce03de910f475952de44b8`.

Copyright (c) 2026 Marcin Krzetowski (Setech Game Studio).
The font data, including this adaptation, is licensed under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
[Full legal terms](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).
The reference asset notice is preserved in
[void-strike-LICENSE-ASSETS.md](void-strike-LICENSE-ASSETS.md).
The reference source-code MIT notice is preserved in
[void-strike-MIT.txt](void-strike-MIT.txt).

Changes: reordered glyph indices to the existing Neon ASCII map, added `+` and
`=`, cleared the eighth scanline. Menu glyph columns are copied in full.
The HUD glyphs are separately drawn at their final 6x7 width, inspired by the
reference's open forms; no glyph columns are removed, compressed or resampled.
These authored HUD glyphs are also supplied under CC BY-NC-SA 4.0.
The game name and studio branding are pre-existing owner material; no rights to
reference names or marks are inferred from the font licence.

`tools/assets.py` validates and builds both immutable 352-byte sources. The
runtime keeps the menu source in a 1024-byte ANTIC2 bank and composes the HUD
source into two 320-byte strips. Both keep one bit per pixel.

The NEON SHIFT 65 title logo also derives from the full reference menu glyphs.
It preserves all source columns and doubles their scanlines vertically in an
ANTIC4 title-only bitmap. The old three-column ANTIC4 alphabet is not enlarged.
The logo font adaptation remains under CC BY-NC-SA 4.0; owner branding is unchanged.
