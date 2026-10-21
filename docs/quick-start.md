**English** · [Polski](quick-start.pl.md)

# Quick start

You need the game disk image and an Atari emulator. You do not need Git, Python, Node.js or a compiler to play.

[Play in a browser](https://setech-pl.github.io/setech-arcade/play/neon-shift-65/) · [Windows](#windows--altirra) · [macOS](#macos--atari800) · [Real Atari / SIO2SD](#real-atari--sio2sd)

## Download the game

1. Open the [Releases page](https://github.com/Setech-pl/neon-shift-65/releases) and download **neon-shift65.atr** from the release assets. Alternatively, download **neon-shift65-player.zip** and extract it first. The GitHub **Source code** archives are for building, not the quickest way to play.
2. Keep the downloaded ATR as your original. Make a second copy named **neon-shift65-play.atr** in a folder you can write to, such as Downloads.
3. Use that copy for play. The game writes progress **inside the ATR**. Do not play directly from a ZIP or mount the disk read-only.

The ATR is a bootable Atari disk image, not a Windows or macOS application. Mount it as **D1:**. Use **XL/XE with 64 KB**, **PAL**, **BASIC OFF**, and no cartridge.

## Windows — Altirra

1. Download a stable binary package from the [official Altirra page](https://www.virtualdub.org/altirra.html). Choose x86/x64 for a typical Intel/AMD PC, or ARM64 for Windows on ARM.
2. Extract the whole emulator ZIP. Run **Altirra64.exe** on 64-bit Intel/AMD Windows, or the executable supplied for your architecture.
3. In the first-run setup or **System → Configure System**, select **800XL / XL-XE**, **64 KB**, **PAL**, and **BASIC off**. You can start with the built-in **AltirraOS**; no separate Atari ROM is needed for that configuration.
4. Choose **File → Boot Image** and open **neon-shift65-play.atr**. In the disk-drive panel, check that D1: allows writes and that changes are saved back to this working copy, rather than discarded.
5. In **Input**, enable a keyboard joystick on **port 1**. The arrow-key joystick preset normally uses **arrow keys + left Ctrl for FIRE**. Names vary by version; check **Input Mappings** if necessary.
6. Click the emulator window. Wait for the loader and menu, choose **BEGIN SHIFT**, and press FIRE. Choose **CONTINUE** to restore a saved game.

| Action | Atari control | Altirra default console keys / keyboard joystick above |
| --- | --- | --- |
| Move and push; navigate menus | Joystick directions | Arrow keys |
| Confirm a menu choice; undo during play | FIRE | Left Ctrl |
| Undo | SELECT | F3 |
| Restart the level | OPTION | F4 |
| Pause / resume | START | F2 |
| Save and return to the menu | START, then SELECT | F2, then F3 |

**Altirra and Atari800 assign START and OPTION differently.** Use the table for your emulator. A custom mapping can override these defaults. Some keyboards require Fn with function keys.

## macOS — Atari800

The following route uses Terminal and [Homebrew](https://brew.sh/). If Homebrew is not installed, follow its official installation instructions first. To play without installing anything, use the browser link above.

1. Install [Atari800](https://formulae.brew.sh/formula/atari800):

   ```sh
   brew install atari800
   ```

2. Put the writable **neon-shift65-play.atr** copy in your Downloads folder.
3. Start the emulator in a window:

   ```sh
   atari800 -xl -pal -nobasic -xl-rev altirra -nopatch -windowed "$HOME/Downloads/neon-shift65-play.atr"
   ```

   This selects an XL with 64 KB, PAL, BASIC off, the built-in Altirra OS, and standard OS SIO. Change the quoted path if your copy is elsewhere. The ATR is the disk argument; do not pass it with an executable-loading option.
4. Press **F1** to open the emulator menu (use **Fn + F1** if macOS intercepts the key). In **Controller Configuration**, select a keyboard joystick for **port 1** (the first port, sometimes numbered 0 internally) and use **Define layout** to assign directions and FIRE. A convenient layout is **W/A/S/D + M for FIRE**.
5. In **Disk Management**, confirm that D1: contains your working copy in read/write mode. Return to the game with Esc.
6. Select **BEGIN SHIFT** with the configured joystick and FIRE; use **CONTINUE** for a saved game.

| Action | Atari control | Atari800 console keys / suggested keyboard layout |
| --- | --- | --- |
| Move and push; navigate menus | Joystick directions | W/A/S/D after assigning them |
| Confirm a menu choice; undo during play | FIRE | M after assigning it |
| Undo | SELECT | F3 |
| Restart the level | OPTION | F2 |
| Pause / resume | START | F4 |
| Save and return to the menu | START, then SELECT | F4, then F3 |
| Emulator settings | — | F1 |

On a MacBook, use Fn with F1–F4 if needed, or enable standard function keys in macOS keyboard settings. The game does not use the Mac's Option key as the Atari OPTION button.

The project has existing Atari800 emulation checks. These setup instructions follow the emulator documentation; they do not claim a new Altirra or Homebrew-package playtest.

## Saving and common problems

To save deliberately, press the Atari **START** control to pause, then **SELECT** to save and return to the menu. Wait until the menu appears before closing the emulator. If the emulator asks to commit disk changes, save them to your working ATR. Reopen **the same copy** and choose **CONTINUE**. Undo history is not restored after a cold start.

| Problem | What to check |
| --- | --- |
| BASIC or SELF TEST appears | Select XL/XE, 64 KB, PAL, BASIC off, remove any cartridge, and cold-boot the ATR as D1:. |
| The robot does not move | Focus the window and configure joystick port 1. Keyboard mapping is an emulator setting. |
| Restart happens when you wanted pause | START and OPTION have different PC keys in Altirra and Atari800; check the tables above. |
| Saving fails or CONTINUE loses progress | Use an extracted writable copy, disable write protection, and commit the emulator's disk writes. Reopen that same ATR. |
| Colors or speed look wrong | Check PAL and normal emulation speed; turn off turbo and optional display effects when comparing screenshots. |
| Loading seems slow | Standard OS SIO is intentionally used by the Atari800 command. Wait for the menu; loading is not instantaneous. |

## Real Atari / SIO2SD

1. Copy a writable working ATR onto the SIO2SD card and mount it as **D1:**.
2. Cold-start the Atari while holding **OPTION / BASIC OFF**.
3. Wait for the menu. Joystick port 1 and FIRE select **BEGIN SHIFT** or **CONTINUE**.

Hardware target: Atari 65XE PAL, 64 KB RAM; XL/XE PAL 64 KB has been tested in emulation. The image has 8192 sectors of 128 bytes (1,048,592 bytes including header). SIO2SD must support this format and writing. Physical Atari/SIO2SD acceptance remains unconfirmed in the published release; NTSC and physical disk drives are not qualified.

## Setech Arcade

[Open the game](https://setech-pl.github.io/setech-arcade/play/neon-shift-65/), focus the game area, and start playing. Arrows/WASD = movement, Z/X = FIRE, F2 = OPTION, F3 = SELECT, F4 = START.

Progress is stored in this browser's IndexedDB; clearing site data removes it. A downloaded ATR is a fresh disk, separate from browser progress. Full console-key controls require a keyboard; touch/gamepad expose movement and FIRE.

[How to play](how-to-play.md) · [README](../README.md) · [Atari800 controls and options](https://github.com/atari800/atari800/blob/master/DOC/USAGE)
