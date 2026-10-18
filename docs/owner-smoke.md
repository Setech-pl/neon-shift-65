**English** · [Polski](owner-smoke.pl.md)

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** hold **OPTION** at power-on to disable BASIC. The new image awaits actual Atari visual, transition, save and sound acceptance; rights remain open. Report: [HWVIS1](hwvis1/REPORT.md).

# Owner smoke — hardware and appearance

**Hardware: OWNER_PENDING. Appearance/listening: OWNER_PENDING.** No later
acceptance of product 600d934 has been found in local reports or the empty
GitHub repository. Emulator results do not constitute physical acceptance.

Prepare the complete identified set (no compiler or previous build needed):

```sh
python3 tools/hwvis1_prepare.py --routes
```

| Clean source | Purpose |
| --- | --- |
| dist/neon-shift65-v1.0.0.atr | Normal product, boot to menu |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-01.atr | Energy, level 1 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-16.atr | Hydroponic, level 16 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-31.atr | Data Hub, level 31 |
| build/owner-smoke/hwvis1/neon-shift65-hwvis1-test-46.atr | Reactor, level 46 |

The helper ZIP and manifest are in build/owner-smoke/hwvis1/. SHA-256 of the normal
source: fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82.
All five hashes: build/owner-smoke/hwvis1/manifest.json. These are clean images;
make working copies for hardware, keep originals unchanged.

1. Atari 65XE PAL, 64 KB, joystick port 1; writable copy mounted as D1: on
   SIO2SD supporting 8192×128 sectors. Disable BASIC (hold OPTION at power-on).
   Observe splash/loader/menu, full board, HUD, robot/crate/dock distinction.
2. Move, push, release, FIRE undo; repeat with SELECT. OPTION restarts and
   clears counters/undo. START pause → FIRE config, left/right music and FIRE
   SFX → START → START resume. Listen before/after I/O.
3. On normal level 1: R, START, SELECT save; CONTINUE, R, START, SELECT save
   again. Cold boot → CONTINUE should recover STEPS=02, PUSHES=02 and empty
   undo. In this pattern both R moves push. Use SELECT on the solved board
   to test undo before a fresh FIRE advances. Do not confuse in-RAM Continue
   with a cold read from disk.
4. On a disposable copy, write-protect after a move: pause → SELECT should
   show SAVE FAILED and stay paused. Enable writes and SELECT retries; cold
   Continue should recover the new state. No power-cut test is required.
5. Cold-boot the four area copies. Move, undo, restart and inspect the
   yellow/green/magenta/red rooms, walls, panels, robot, containers and docks.
   A used test image automatically resumes its own saved progress on cold
   boot. OPTION restarts that saved level; for a clean original area start,
   replace the working copy with the clean test source while powered off.
6. Short boundary/finale paths are in build/owner-smoke/hwvis1/routes/:
   smoke-level-15/30/45/60.atr plus routes.json. These are normal-product
   copies with valid disk saves one move before completion, not RAM patches.
   Cold boot → CONTINUE → last direction from routes.json → release → fresh
   FIRE. Expect 15→16, 30→31, 45→46 and finale 60/60. SELECT before FIRE
   undoes the winning push. Cold Continue after completion returns to finale.

Never change D1: during a running game or I/O. Power off, choose the next
working image, then cold boot. There is no obligation to manually solve 60
levels: the above focused smoke is enough for owner acceptance.

## WINDOWED emulator launcher

Set NEON_ATARI800 (or install atari800 on PATH) and NEON_ATARI_CONFIG to your
private config containing legally supplied OS ROM paths. No ROM is supplied.

```sh
python3 tools/release1_owner_smoke.py
python3 tools/release1_owner_smoke.py --area 31
python3 tools/release1_owner_smoke.py --route 60
```

PLAY-WINDOWED.command calls the same launcher. --check prepares a command
without opening a window; agents use only --check/headless. WASD/M, F2 OPTION,
F3 SELECT, F4 START; --physical-joystick enables your physical emulator pad.
Private play disks persist under build/owner-smoke/hwvis1/play/{normal,area-N,route-N}.
To reset, rename your private play disk as a backup, then relaunch; the clean
source is copied again. Source images are hash-checked and never mounted for
play. Routes are separate disposable saved states. Emulator success is not
physical acceptance.

## Result to supply

Record model, PAL/64 KB, OS, SIO2SD model/firmware, card, joystick, display,
clean source filename and SHA-256, working copy used, steps 1–6 with actual
outcomes and separate hardware/appearance/listening verdicts. Record defects
without changing the source ATR. No PASS will be entered without this result.
