**English** · [Polski](README.pl.md)

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** hold **OPTION** at power-on to disable BASIC. The new image awaits actual Atari visual, transition, save and sound acceptance; rights remain open. Report: [HWVIS1](docs/hwvis1/REPORT.md).

# NEON SHIFT 65

**A Sokoban puzzle game for the Atari 65XE PAL: 60 levels across four industrial areas.**

Drive the service robot, push cargo onto the docks and restore the station, one room at a time. Energy, Hydroponic, Data Hub and Reactor each contain 15 levels. The whole room stays visible; planning and recovering from mistakes are part of the shift.

**[Download the normal ATR](dist/neon-shift65-v1.0.0.atr)** · [Player ZIP](dist/neon-shift65-v1.0.0.zip) · [GitHub releases](https://github.com/Setech-pl/neon-shift-65/releases)

**1.0.0 preparation: DRAFT.** No stable release is published yet. Hardware/appearance acceptance and specific rights decisions remain pending.

![Sixteen-second montage of actual gameplay: crate docking and undo in Energy, then excerpts from Hydroponic, Data Hub and Reactor](docs/media/neon-shift65.gif)

*Four gameplay excerpts, edited together; recorded from the frozen ATRs in Atari800, PAL time, integer 2× nearest-neighbour. Area test starts were used for Hydro/Data/Reactor. They are test media, not an area-selection feature in the normal game. [Capture provenance and area GIFs](docs/media/README.md).*

## Four areas

| Energy · levels 01–15 | Hydroponic · levels 16–30 |
| --- | --- |
| ![Yellow Energy machinery around the robot, crates and docks](docs/media/energy.png) | ![Green Hydroponic room with four crates and docking positions](docs/media/hydro.png) |
| **Data Hub · levels 31–45** | **Reactor · levels 46–60** |
| ![Magenta Data Hub machinery and a crate puzzle](docs/media/data.png) | ![Red Reactor room, robot and cargo](docs/media/reactor.png) |

| Menu | Loader |
| --- | --- |
| ![Main menu with BEGIN SHIFT and CONTINUE](docs/media/menu.png) | ![Actual loading screen before gameplay](docs/media/loader.png) |
## Start a shift

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

## Requirements and current limits

Target: stock Atari 65XE PAL, 64 KB, joystick port 1, writable SIO2SD D1: supporting an **8192 × 128-byte** image (1,048,592 bytes including header). BASIC must be disabled; the game uses RAM under BASIC. The ATR is not a 720 × 256 physical floppy image. NTSC, CA-2001, other machines and firmware are unqualified.

RELEASE1 emulator evidence covers 60/60 levels, transitions and finale, undo256, saves, cold Continue and standard OS SIO. Independent re-review closes A-01–A-03 for the exact distributed bytes. **Physical hardware and final appearance: OWNER_PENDING.** These are separate from emulator results. No player study or proven linear difficulty curve is claimed.

## Guides and development

[How to play](docs/how-to-play.md) · [Quick start](docs/quick-start.md) · [Documentation](docs/README.md) · [Current build](docs/building.md) · [Release notes](docs/release-notes.md) · [Owner smoke](docs/owner-smoke.md)

The production builder is `python3 tools/v1_build.py --out build/my-release` (new output directory). The root Makefile belongs to the archived prototype. Packaging does not rebuild or modify the accepted ATR. Functional development is frozen; maintenance is limited to confirmed defects.

## Credits and licences

Marcin Krzetowski / **Setech Game Studio**, with documented Codex implementation and tooling assistance and a Claude independent audit. [Credits and provenance](docs/credits.md).

Own code, tools and technical documentation: [MIT](LICENSE). Own graphics, fonts, maps, creative text and visual materials: [CC BY-NC-SA 4.0](LICENSE-ASSETS), subject to explicit exceptions. Linked cc65 runtime and adapted Void Strike components retain their notices. **Music rights and historical First Dock provenance remain open**; see [third-party notices](THIRD_PARTY_NOTICES.md). Names and studio logo are reserved marks; neither licence grants branding rights.
