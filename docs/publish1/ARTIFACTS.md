# PUBLISH1 artifact relocation

Product checkpoint: `600d934310b5ffb8e3fbf73a205f15a589a4efa6`.
All five old docs/release1 images were hash-checked before any removal; all
matched the clean checkpoint and had empty player-save slots. No private
save was replaced and no ATR was rebuilt merely to rename or relocate it.

| Historical path under docs/release1/ | Current location |
| --- | --- |
| neon-shift65-v1.0-candidate.atr | dist/neon-shift65-v1.0.0.atr |
| neon-shift65-v1.0-test-01.atr | build/owner-smoke/neon-shift65-v1.0.0-test-01.atr |
| neon-shift65-v1.0-test-16.atr | build/owner-smoke/neon-shift65-v1.0.0-test-16.atr |
| neon-shift65-v1.0-test-31.atr | build/owner-smoke/neon-shift65-v1.0.0-test-31.atr |
| neon-shift65-v1.0-test-46.atr | build/owner-smoke/neon-shift65-v1.0.0-test-46.atr |
| neon-shift65-release1-owner.zip | build/owner-smoke/neon-shift65-v1.0.0-owner-smoke.zip (new helper bundle; original recoverable from Git) |

One command: `python3 tools/publish1_prepare.py --routes`. Generated test images,
helper ZIP, play copies and boundary saves are ignored. The normal ATR is
tracked only in dist/. A standalone ATR plus the same file inside the player
ZIP is intentional. No other checkpoint's ATR is represented as current product.

Historical reports, manifests, SHA256SUMS and evidence/source archives keep
their original paths/hashes as historical facts. Except for the explicitly
identified N-01 wording correction and a current-instructions pointer, their
results are unchanged. Removed delivery duplicates remain recoverable, e.g.:

```sh
git show 600d934310b5ffb8e3fbf73a205f15a589a4efa6:docs/release1/neon-shift65-v1.0-candidate.atr > build/owner-smoke/original-candidate.atr
git show 600d934310b5ffb8e3fbf73a205f15a589a4efa6:docs/release1/neon-shift65-release1-owner.zip > build/owner-smoke/original-owner.zip
```

First run the preparation command so the destination directory exists.
Historical qualification scripts with hard-coded docs/release1 image paths
should be reproduced from that checkpoint in an isolated tree; their old
commands are not the current release workflow. Only the active owner launcher
was redirected to the new paths. It never opens the clean source for gameplay.

Preserved locally: docs/release1/{capture-evidence.zip,capture-rc2-evidence.zip,
source-inputs.zip}, earlier historical archives/ATRs, and all previously
untracked owner files including the expanded old owner bundle. Evidence ZIPs
were not removed on account of their extension. Historical archives include
raw evidence/private config paths and are not part of a new safe GitHub export.
