**English** · [Polski](README.pl.md)

# NEON SHIFT 65

**Industrial Sokoban for Atari XL/XE PAL, 64 KB.** Guide a service robot through 60 levels. Push every crate onto a dock. You cannot pull crates or push two at once.

[Play in Setech Arcade](https://setech-pl.github.io/setech-arcade/play/neon-shift-65/) · [Download ATR](https://github.com/Setech-pl/neon-shift-65/releases/download/v1.0.0/neon-shift65.atr) · [How to play](docs/how-to-play.md) · [Build from source](docs/building.md)

![NEON SHIFT 65 gameplay](docs/media/neon-shift65.gif)

Four animated areas: Energy (01–15), Hydroponic H2 (16–30), Data Hub (31–45), and Reactor R1 (46–60). Up to 256 undo steps, level restart, progress saving and Continue. All 60 starting layouts have independently verified solutions. A wrong move can trap a crate; use undo or restart.

| Energy | Hydroponic H2 |
| --- | --- |
| ![Energy](docs/media/energy.png) | ![Hydroponic](docs/media/hydro.png) |
| Data Hub | Reactor R1 |
| ![Data Hub](docs/media/data.png) | ![Reactor](docs/media/reactor.png) |

Actual captures of the released ATR; 2× nearest-neighbour scaling. [Media](docs/media/README.md)

## Getting started

Mount a **writable copy** of the normal ATR as **D1:**. Select PAL, XL/XE 64 KB and **BASIC OFF** (hold OPTION during a cold Atari boot). At the menu choose BEGIN SHIFT or CONTINUE with the joystick and FIRE. The image has 8192 sectors of 128 bytes; SIO2SD must support this format and writing.

Controls: joystick moves/pushes; FIRE or SELECT undoes; OPTION restarts; START pauses. SELECT while paused saves and returns to the menu. See the manual for saving and configuration.

## Sources

```sh
python3 tools/build.py --out build/release
```

Python 3, Node.js, cc65 and clang. No ROM or emulator is needed to build. [Build](docs/building.md)

The normal ATR is reproducible from source and matches the version verified in emulation, including a 60/60 campaign replay. Physical Atari/SIO2SD testing and owner listening remain unconfirmed. NTSC support is not claimed.

## Credits and licences

© 2026 Marcin Krzetowski / **Setech Game Studio**. Developed with assistance from Claude Code and Codex. [Credits](docs/credits.md)

Code, tooling and engineering documentation: [MIT License](LICENSE). Graphics, fonts, maps, creative text and runtime images: [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE-ASSETS). The [full CC legal text](docs/licenses/CC-BY-NC-SA-4.0.txt) is included. The licence follows the content in mixed files. The complete ATR is distributed under CC BY-NC-SA 4.0 with MIT and cc65 notices retained. The earlier CC0 grant for “Service Current” remains effective; cc65 and adapted Void Strike components retain their own terms and attribution. Studio names and marks are reserved. [Components and exceptions](THIRD_PARTY_NOTICES.md).
