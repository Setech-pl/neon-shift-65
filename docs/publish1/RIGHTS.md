# PUBLISH1 — provenance and remaining decisions

This is a focused input/licence inventory, not another engine audit. Owner's
PUBLISH1 instruction authorizes MIT for own code/tools/engineering docs and
CC BY-NC-SA 4.0 for own content. Earlier absence of an overall licence is
resolved by that instruction; it does not establish rights in unidentified works.

## Product and build inputs

The immutable source list is in source-inputs.json, derived from the RELEASE1
build-inputs inventory and checked against product commit 600d934. The normal
ATR has the accepted SHA-256; campaign/graphics sectors are equal across five
images. product-equivalence.json records generated-source comparisons: startup
and save namespace differences are distinguished from engine identity.
The linker at build/release1/final/candidate.map explicitly lists atari.lib
crt0.o, memcpy.o and compiler helpers; runtime code is really linked. A portable
list of library modules is preserved in cc65-linked-modules.txt. Original cc65
licence, upstream Void Strike MIT and asset notices are retained in docs/licenses/.

Fonts come from mono-font.json plus project procedural sources, not a host
system font or extracted Atari ROM. Pinned Void Strike JSON/generator sources
are in experiments/eng3-observed-input-3pal/reference/, with frozen-inputs.json.
No ROM path is an input to the production compiler. SFX use existing project
POKEY tables; splash audio is a pinned Void Strike definition/adaptation.
Service Current has editable procedural composition data in compile.py; no
external sample or RMT binary is imported. That observation does not resolve
who authorized its historical CC0 dedication.

## Open decisions — stable publication blocked

1. **Service Current:** experiments/eng3-observed-input-3pal/compile.py writes
   CC0 metadata and composes music.nrq; hardware.s plays it. Historical notices
   in experiments/renderer-a{3,4,5}/LICENSE-music.md declare composition and new
   instruments CC0-1.0, player MIT. Need the rights holder/authorized provenance
   and a decision preserving any valid CC0 grant as an explicit exception.
   The broad new NC-SA selection cannot silently revoke a valid CC0 dedication.
2. **Inherited maps in repository/build fixtures:** assets/levels/prototypes.json
   FIRST DOCK records inherited level1 from 8056a70; REACTOR STORE records
   inherited level14/Piatka. src/levels_data.c holds the earlier 20 layouts;
   experiments/eng3-observed-input-3pal/reference/prototype_assets.c contains
   their generated fixture lineage. Need original author/source and permission
   for redistribution of these specific historical maps. They are not the
   final 60 NSLV maps, but source publication includes build fixtures. No removal
   or replacement was authorized. The earlier question mentioning level01.xsb
   was provisional: the actual files are those listed here.
3. **Reference bitmap:** reference/vis1-owner/energy-owner-reference.png was
   supplied for visual direction; origin and redistribution permission remain
   undocumented. It is not compiled into the ATR. Exclude it from a safe export
   until the owner supplies permission; retain it locally unchanged.

Final CAMP2-B campaign metadata explicitly state 46 original new layouts and
14 retained CAMP2-B project layouts, with source/change fields per map and no
external collection. Earlier assets/levels/{product1-campaign.json,camp2-a/,
camp2-b/samples.json} remain historical; their presence is not a general rights
waiver. Map fixture exceptions above are kept explicit rather than attributed
by inference. Existing owner untracked references are never swept into a push.

## Release scope

New promotional captures are project screenshot/GIF content; they do not add
third-party imagery to the game. The player ZIP includes only the normal ATR,
EN/PL player guides/release summary, licences and notices. No emulator, ROM,
raw RAM, local config or player save. Technical permission to prepare/push a
private draft is not a claim that open rights are resolved for stable distribution.

## Primary licence references checked

CC legal code: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en
cc65 V2.19 licence: https://github.com/cc65/cc65/blob/V2.19/LICENSE
The preserved cc65 licence matches the used local distribution. Upstream notice
requirements remain distinct from this project's MIT/content declarations.
