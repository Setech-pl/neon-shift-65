#!/usr/bin/env python3
"""Deliver five isolated read-only masters; never mount them or update dist."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODES=('normal','01','16','31','46')
def deliver(builds,out):
    out.mkdir(parents=True,exist_ok=False);images={}
    for m in MODES:
        name='neon-shift65-atmosphere1'+('' if m=='normal' else '-test-'+m)+'.atr'
        raw=(builds[m]/'candidate.atr').read_bytes();(out/name).write_bytes(raw);(out/name).chmod(0o444)
        images[m]=dict(file=name,sha256=hashlib.sha256(raw).hexdigest(),build=str(builds[m]))
    (out/'candidate.json').write_text(json.dumps(dict(name='ATMOSPHERE1',images=images),indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+v['file']+'\n' for v in images.values()))
    shutil.copyfile(ROOT/'tools/atmosphere1_owner_smoke.py',out/'launch.py')
    (out/'PLAY-WINDOWED.command').write_text('#!/bin/zsh\nset -e\nHERE="$(cd -- "$(dirname -- "$0")" && pwd)"\nexec python3 "$HERE/launch.py" "$@"\n')
    (out/'PLAY-WINDOWED.command').chmod(0o755)
    (out/'START-HERE.txt').write_text('''ATMOSPHERE1 — lokalny kandydat, bez publikacji.

Normalny ATR: menu, BEGIN SHIFT, pełna kampania 60 poziomów, Continue.
-test-01/-16/-31/-46: zimny start wybranego obszaru, ta sama pełna kampania.
Każdy wariant ma oddzielny save-id. Nie przenoś zapisów ze starszej wersji.
Atari XL/XE PAL, 64 KB, BASIC OFF (OPTION podczas zimnego startu).
SIO2SD: skopiuj wybrany ATR, zdejmij ochronę zapisu kopii i zamontuj jako D1:.
Kopia ATR i karta muszą umożliwiać zapis. Wzorce pozostają read-only.
Joystick: ruch/push, FIRE lub SELECT undo, OPTION restart, START pauza.
Zapis i menu: START, następnie SELECT. CONFIG: MUSIC i SFX osobno.

WINDOWED: ./PLAY-WINDOWED.command --mode normal
Tryby: normal / 01 / 16 / 31 / 46. Bez --mode wybór w terminalu.
WASD + M/FIRE, F2 restart, F3 undo, F4 pauza.
Opcje: --emulator /ścieżka/atari800 --config /ścieżka/legalny.cfg
Domyślnie atari800 z PATH i ~/.atari800.cfg. Nie dostarczamy ROM-ów.
Launcher weryfikuje SHA wzorca i montuje zapisywalne play/<tryb>/<SHA>/.
Zachowuje postęp; akceptuje zmiany tylko w sektorach 8100/8101.

Raport i porównania: docs/atmosphere1/REPORT.md w worktree źródłowym.
Grafika, odsłuch właściciela i fizyczne Atari: OWNER_PENDING.
''')
    return images
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    deliver({m:a.build_root/('normal' if m=='normal' else 'test-'+m) for m in MODES},a.out)
