#!/usr/bin/env python3
"""WINDOWED ATMOSPHERE1: immutable master, versioned writable play disk.

NSCD v1 runtime (src/product1/campaign.c) reads/writes exactly the
two 128-byte records at sectors 8100 and 8101. No other bytes are exempt.
"""
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p / 'assets/levels/camp2-b/campaign.json').exists()), None)
OWNER = ROOT / 'build/owner-smoke/atmosphere1' if HERE.name == 'tools' else HERE
SAVE_SECTORS = (8100, 8101)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_span(data):
    if len(data) != 16 + 8192 * 128:
        raise ValueError('Unsupported ATR length: expected 8192 sectors of 128 bytes')
    magic, low, size, high = struct.unpack_from('<4H', data)
    if magic != 0x296 or size != 128 or (low | high << 16) * 16 != len(data) - 16:
        raise ValueError('Unsupported ATR header/geometry')
    catalog = data[16 + 999 * 128:16 + 1000 * 128]
    if catalog[:6] != b'NSCD\x01\x3c' or binascii.crc_hqx(catalog[:126], 65535) != int.from_bytes(catalog[126:], 'little'):
        raise ValueError('Not the supported NSCD v1 / 60-level campaign format')
    return slice(16 + (SAVE_SECTORS[0] - 1) * 128, 16 + SAVE_SECTORS[-1] * 128)


def immutable(data):
    span = save_span(data)
    return data[:span.start] + data[span.stop:]


def prepare(owner, mode, play_root=None):
    entry = json.loads((owner / 'candidate.json').read_text())['images'][mode]
    master = (owner / entry['file']).resolve()
    data = master.read_bytes()
    digest = sha(data)
    if digest != entry['sha256']:
        raise ValueError('Master ATR SHA-256 mismatch; master and saved progress preserved. Expected ' + entry['sha256'] + ', got ' + digest)
    game = immutable(data)
    output = (play_root or owner / 'play') / mode / digest
    output.mkdir(parents=True, exist_ok=True)
    play = output / master.name
    if play.is_symlink() or play.exists() and os.path.samefile(play, master):
        raise ValueError('Play ATR aliases the protected master; refusing to mount it')
    if not play.exists():
        try:
            with play.open('xb') as f:
                f.write(data)
        except FileExistsError:
            pass
    actual = play.read_bytes()
    if immutable(actual) != game:
        raise ValueError('Play ATR has changes outside save sectors 8100/8101; preserved without launching: ' + str(play))
    return dict(master=str(master), master_sha256=digest,
                opened_atr=str(play.resolve()), opened_sha256=sha(actual),
                immutable_sha256=sha(game), save_sectors=list(SAVE_SECTORS),
                version_id='ATMOSPHERE1:' + mode + ':' + digest,
                mode=mode, game_bytes_match=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('normal','01','16','31','46'),help='Normal game or isolated area start')
    p.add_argument('--check', action='store_true', help='Prepare/verify play copy and print exact command')
    p.add_argument('--emulator', default=os.environ.get('NEON_ATARI800') or shutil.which('atari800'))
    default = Path.home() / '.atari800.cfg'
    p.add_argument('--config', type=Path, default=os.environ.get('NEON_ATARI_CONFIG') or default)
    p.add_argument('--play-root', type=Path, help='Separate play directory; never imports another version’s saves')
    p.add_argument('--physical-joystick', action='store_true')
    a = p.parse_args()
    if not a.emulator or not a.config.expanduser().is_file():
        p.error('Supply Atari800 --emulator and a legal ROM --config')
    mode=a.mode
    if mode is None and not a.check and __import__('sys').stdin.isatty():
        print('WINDOWED: 0 normalna gra, 1 Energy, 2 Hydroponic, 3 Data, 4 Reactor')
        answer=input('Wybór [0]: ').strip() or '0'
        if answer not in ('0','1','2','3','4'):p.error('Wybierz 0–4')
        mode=('normal','01','16','31','46')[int(answer)]
    try:
        record = prepare(OWNER, mode or 'normal', a.play_root)
    except (OSError, ValueError, KeyError) as e:
        p.error(str(e))
    output = Path(record['opened_atr']).parent
    cfg = a.config.expanduser().resolve()
    text = cfg.read_text()
    def rom(m):
        k, v = m.groups()
        v = v.strip()
        if v and not v.startswith('UNSET'):
            q = Path(v).expanduser()
            v = str((q if q.is_absolute() else cfg.parent / q).resolve())
        return k + '=' + v
    text = re.sub(r'^(ROM_[A-Z0-9_/]+)=(.*)$', rom, text, flags=re.M)
    def put(k, v):
        nonlocal text
        text = re.sub(r'^' + re.escape(k) + r'=.*\n?', '', text, flags=re.M).rstrip('\n') + '\n' + k + '=' + str(v) + '\n'
    for k, v in dict(RAM_SIZE=64, TURBO_SPEED=0, SOUND_ENABLED=1, ENABLE_SIO_PATCH=0,
                     VIDEOMODE_WINDOWED=1, BILINEAR_FILTERING=0, ARTIFACT_PAL='NONE',
                     SCANLINES_PERCENTAGE=0, INTERPOLATE_SCANLINES=0).items():
        put(k, v)
    for prefix in ('SDL2_', 'SDL_'):
        for k, v in dict(JOY_0_UP=119, JOY_0_DOWN=115, JOY_0_LEFT=97, JOY_0_RIGHT=100, JOY_0_TRIGGER=109).items():
            put(prefix + k, v)
    config = output / 'emulator.cfg'
    config.write_text(text)
    command = [str(Path(a.emulator).expanduser().resolve()), '-config', str(config),
               '-no-autosave-config', '-xl', '-pal', '-nobasic', '-no-mapram', '-nostereo',
               '-sound', '-nopatch', '-windowed', '-win-width', '640', '-win-height', '480',
               '-no-bilinear-filter', '-pal-artif', 'none', '-scanlines', '0',
               '-no-scanlinesint', '-no-showstats']
    if not a.physical_joystick:
        command.append('-kbdjoy0')
    command.append(record['opened_atr'])
    record.update(command=command, display='WINDOWED', controls='WASD + M/FIRE; F2 restart, F3 undo, F4 pause')
    (output / 'launch.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2), flush=True)
    return 0 if a.check else subprocess.call(command)


if __name__ == '__main__':
    raise SystemExit(main())
