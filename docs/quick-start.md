**English** · [Polski](quick-start.pl.md)

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** hold **OPTION** at power-on to disable BASIC. The new image awaits actual Atari visual, transition, save and sound acceptance; rights remain open. Report: [HWVIS1](hwvis1/REPORT.md).

# Quick start

Download `neon-shift65-v1.0.0.zip` or the standalone ATR from [dist](../dist/). Stable publication is pending; these are the unchanged 1.0.0 candidate bytes. Extract the ZIP and keep its original ATR untouched.

1. Make a writable play copy. Mount it as **D1:**, not as an executable/XEX.
2. Atari800: `atari800 -xl -pal -nobasic -no-mapram -nopatch play.atr`. Configure RAM to 64 KB and joystick port 1. The ROM and emulator are supplied separately by you.
3. Real 65XE: select that copy on SIO2SD D1:, permit writes and hold OPTION at power-on to disable BASIC. The device must support 8192 sectors of 128 B. Physical acceptance remains OWNER_PENDING.
4. Select BEGIN SHIFT, press FIRE. Joystick moves, FIRE/SELECT undo, OPTION restarts, START pauses. In pause, SELECT saves and exits.
5. At a solved board release FIRE, then press it again to advance. SELECT undoes the winning push instead. After cold boot use CONTINUE; undo starts empty.

The supplied owner launcher uses WASD/M, F2=OPTION, F3=SELECT, F4=START. Generic emulator keys depend on your mapping. NTSC and CA-2001 are unqualified. Never swap D1: while running or during writes. [Full rules](how-to-play.md).
