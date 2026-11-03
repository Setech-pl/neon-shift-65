# Controls and saving

Joystick directions move the robot and push one crate at a time; crates cannot be pulled. Dock every crate to finish a level.

| Input | Action |
| --- | --- |
| FIRE or SELECT during play | Undo; release before the next press, up to 256 successful steps |
| OPTION during play | Restart this level |
| START | Pause / resume |
| SELECT while paused | Save and return to menu |
| FIRE while paused | Options |
| Fresh FIRE on solved board | Next level and automatic save |

The title menu provides BEGIN SHIFT, CONTINUE, level selection and OPTIONS. In the level selector choose a level and confirm the selection. Options use up/down to select an item and FIRE to confirm; music and SFX toggle separately. RESUME GAME returns to the board. EXIT TO MAIN MENU requires confirmation and can discard unsaved progress; it is not a save command.

Continue restores saved board positions, counters and settings. A cold Continue starts with empty undo. Restart/new level clears undo. Use a writable copy of the matching ATR; do not power off or eject during I/O. Retry after a reported save failure. Saves are not automatically migrated between different versions. A short direction pulse during a finishing move can be missed; hold/release deliberately.

[README](../README.md)
