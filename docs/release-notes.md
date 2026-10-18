**English** · [Polski](release-notes.pl.md)

**HWVIS1 — OWNER_PENDING. Atari XL/XE PAL 64 KB + SIO2SD:** hold **OPTION** at power-on to disable BASIC. The new image awaits actual Atari visual, transition, save and sound acceptance; rights remain open. Report: [HWVIS1](hwvis1/REPORT.md).

# NEON SHIFT 65 v1.0.0

**DRAFT — not a published stable release.**

A Sokoban game for the Atari 65XE PAL: move the service robot and push cargo onto the docks in 60 levels across Energy, Hydroponic, Data Hub and Reactor (15 per area). Full-board view, step/push counters, 256-step undo, restart, pause, music/SFX configuration, persistent saves, Continue and a campaign finale are present.

Download `neon-shift65-v1.0.0.zip` (ATR, EN/PL guides and licences) or the standalone `neon-shift65-v1.0.0.atr`; verify `SHA256SUMS`. No test-start ATRs, ROM or emulator are included. Copy the ATR before play, mount it writable as D1:, PAL, XL/XE 64 KB, **BASIC disabled** (OPTION at power-on on 65XE), joystick port 1.

Directions move/push. FIRE or SELECT undo during play; OPTION restarts; START pauses. Paused SELECT saves and exits, FIRE opens configuration. Once solved, release controls and press a fresh FIRE for next level; SELECT undoes the last push. Pause-save and level advancement write progress; cold Continue restores board and counters but not undo history. Keep the clean original; save errors allow retry.

Confirmed evidence for product commit `600d934310b5ffb8e3fbf73a205f15a589a4efa6`: RELEASE1 60/60 levels, area boundaries/finale, undo256, saves, cold Continue and standard OS SIO. Independent re-review closes A-01–A-03. Packaging and media commits are later; the ATR bytes are unchanged. N-01 corrects only the descriptor/display-list documentation.

Limits: physical hardware, appearance and listening acceptance remain **OWNER_PENDING**; emulator PASS is not hardware acceptance. The 8192×128 ATR requires supporting writable media; CA-2001/physical floppy, NTSC and other configurations are unqualified. Music licence authority and historical First Dock provenance require decisions before stable publication. The repository remains private as requested; download access follows repository access.

Normal ATR SHA-256: `fba5fae678c719f1afd022ac5e4a746882557fdacfa91fcefb5e0bb73cd76c82`.

Marcin Krzetowski / Setech Game Studio; Codex development/tooling assistance, Claude independent audit. Own code/tools/technical docs: MIT; own creative content: CC BY-NC-SA 4.0 with explicit exceptions; cc65 and Void Strike notices retained. Names and logo reserved. See LICENSE, LICENSE-ASSETS and THIRD_PARTY_NOTICES.md in the package. Maintenance now covers confirmed bugs only.
