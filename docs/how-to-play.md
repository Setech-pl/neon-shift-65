**English** · [Polski](how-to-play.pl.md)

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** hold **OPTION** at power-on to disable BASIC. The new image awaits actual Atari visual, transition, save and sound acceptance; rights remain open. Report: [HWVIS1](hwvis1/REPORT.md).

# How to play

Push every crate onto a dock. The robot walks in four directions and pushes one crate; it cannot pull or push two crates together. A crate against the wrong wall or in a corner can block a solution: use undo or restart. The HUD shows steps, pushes and docked crates.

The campaign contains 60 levels, 15 each in Energy, Hydroponic, Data Hub and Reactor. There is no normal area-select. BEGIN SHIFT starts level 1; CONTINUE restores the active in-memory game or, after cold boot, the disk save. BEGIN SHIFT does not erase an old disk save until a later successful save replaces it.

1. Copy `neon-shift65-v1.0.0.atr` before playing; saves modify the disk image.
2. Mount the writable copy as **D1:**. Select **PAL**, **64 KB XL/XE**, **BASIC off**. On a real 65XE, hold **OPTION** at power-on to disable BASIC.
3. Wait for the loader and menu; select **BEGIN SHIFT** with joystick port 1 and FIRE. **CONTINUE** restores saved progress.

| Input | During play |
| --- | --- |
| Joystick directions | Walk; push one crate at a time, never pull |
| FIRE or SELECT | Undo one successful step, up to 256 steps |
| OPTION | Restart this level; clear its counters and undo |
| START | Pause; START again resumes |
| SELECT while paused | Save and return to title |
| FIRE while paused | Configuration: left/right music, FIRE sound effects, START back |

After solving a level, release the controls and press a **fresh FIRE** to advance; **SELECT** still undoes the last push. FIRE captured during a move retains undo intent. Advancing saves the next level automatically; finishing saves completion. A cold CONTINUE restores the board and counters with **empty undo**. A failed save offers retry; do not remove the disk during I/O.

Undo is one action per press; release before the next press. Pause retains undo in the same session; new levels and restart clear it. A very short direction pulse during a finishing step can be missed; hold/release deliberately. Music/SFX settings persist with a successful game save.

The owner launcher maps WASD/M and F2/F3/F4 to joystick/FIRE and OPTION/SELECT/START. Other emulator mappings depend on your setup.


## Save behaviour

Pause → SELECT writes the current board and counters, then returns to title. Advancing with FIRE saves the next level automatically; the final FIRE saves campaign completion. Restart resets the current board, counters and undo in RAM; it does not itself erase a disk save. Undo holds the last 256 successful moves, including pushes; blocked moves do not consume it. Undo history is not stored on disk. Save failures remain visible and allow retry with SELECT. Keep a clean master ATR and play only on writable copies.

[Quick start](quick-start.md) · [Requirements and limitations](../README.md)
