# ATMOSPHERE1 scores

Original project compositions, 2026-10-21; CC BY-NC-SA 4.0 under LICENSE-ASSETS.
The three JSON files are the editable scores, with all playable rows explicit.

- Hydroponic — **Glass Canopy**: sparse bass anchors, longer separated melodic
  phrases, light off-beat percussion.
- Data Hub — **Packet Switch**: syncopated bass, short alternating phrases,
  kick/snare/hat grid.
- Reactor — **Containment Drive**: low repeated anchors, semitone tension,
  interrupted phrases and heavier kick groups.

Each pattern has 64 rows `[bass AUDF, lead AUDF, drum]`. Zero means rest;
drum 1/2/3 means kick/hat/snare. Eight patterns, sixteen order entries,
six PAL frames per row; complete loop 122.88 s. The existing envelopes and
three music channels are retained. POKEY channel four remains exclusively SFX.
`tools/atmosphere1_music.py` validates and packs these rows into NSRQ v2.

Energy retains the byte-identical **Service Current** source in
`experiments/eng3-observed-input-3pal/compile.py:music`, including its CC0 grant.
The menu keeps this same original score; the splash is unchanged.

Build: `python3 tools/v1_build.py --atmosphere1 --out build/my-atmosphere1`.
The normal release builder remains pinned to the accepted v1.0.1 behavior.
Actual emulator PCM and owner-listening status are linked from
`docs/atmosphere1/REPORT.md`.
