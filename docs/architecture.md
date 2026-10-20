# Runtime and disk layout

Target: Atari XL/XE PAL, 64 KB, cc65 C and ca65 assembly. The normal bootable
ATR has 8192 × 128-byte sectors plus a 16-byte ATR header. No BASIC is used.

C owns the campaign, puzzle state, undo and high-level flow. Assembly owns
hardware display timing, PMG, input acquisition and SIO veneers. Offline
Python/JavaScript generators turn authored pixel data and maps into compact
Atari resources. The builder applies the current composition layers to the
base C/ASM sources in a new output directory, then compiles and links them.

The 60 disk maps use NSLV records at sectors `1100 + 70*n`, n=0..59.
The NSCD campaign directory is at sector 1000. Records contain their own CRC.
Each logical map is 16×8; `visual_size` describes the visible rectangle and
padding outside it is wall. The campaign ID is `131c57e2` in byte order.

Save records use sectors 8100/8101. They store player/crate positions and
counters, with a campaign identity and CRC. Continue does not restore the
undo history. Always test with a writable copy; never modify a release master.

The renderer uses ANTIC character graphics and PMG overlays. Area artwork is
generated before runtime; resource transitions keep the display hidden while
loading and reveal a prepared screen at VBI. Loader and runtime use OS SIO.

[Build](building.md) · [Controls and saves](how-to-play.md)
