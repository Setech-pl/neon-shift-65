#!/usr/bin/env python3
"""Independent padding/layer ownership review of packed ATR and live frames."""
import argparse
import hashlib
import gzip
import importlib.util
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'experiments/renderer-a5c'), str(ROOT/'tools')]
import verify
import pixel_fast
from atr import offset

BANKS = (0x8c00, 0xa000, 0xa400, 0xa800, 0xac00)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sections(image, n):
    at = offset(1101 + n*70, 128)
    pack = image[at:at+8768]
    return {addr: pack[144+pos:144+pos+size] for addr, size, pos, crc in
            (struct.unpack_from('<4H', pack, 16+i*8) for i in range(pack[6]))}


def glyph(s, pos, code):
    bank = BANKS[min((pos//40-2)//4, 4)]
    return bytes([code & 128]) + s[bank][(code & 127)*8:(code & 127)*8+8]


def animations(s):
    d = s[0x9de0]
    return [struct.unpack_from('<HBB4B', d, 128+i*8) for i in range(d[4])]


def live(out, frame, labs, s):
    r = (out/f'frame-{frame:04}.ram').read_bytes()
    state = verify.state(out/f'frame-{frame:04}.ram', labs)
    assert state['phase'] in (1, 2) and state['error'] == 0
    occupied = set()
    for x, y in [state['player']] + state['boxes']:
        assert 0 <= x < 16 and 0 <= y < 8
        occupied.update((5+y*2+q//2)*40+4+x*2+q%2 for q in range(4))
    g = labs['_gs']
    for y in range(8):
        for x in range(16):
            if r[g+y*38+x] == ord('.'):
                occupied.update((5+y*2+q//2)*40+4+x*2+q%2 for q in range(4))
    anim = {a-0x8800: codes for a, period, phase, *codes in animations(s)}
    for pos in range(80, 960):
        if pos in occupied:
            continue
        code = r[0x8800+pos]
        if pos in anim:
            assert code in anim[pos], (frame, pos, 'invalid animation phase')
        else:
            assert code == s[0x9800][pos-80], (frame, pos, 'stale or out-of-map screen write')
    # Bank contents must also be current, except four reserved robot glyphs.
    for address in BANKS:
        assert r[address:address+124*8] == s[address][:124*8], (frame, 'stale font bank')
    return pixel_fast.pixel(out, frame, labs)


def enlarge(src, dest):
    im, pal = verify.png(src)
    # Integer replication only; retain every native palette RGB value.
    pixels = [[v for v in row for _ in range(3)] for row in im for _ in range(3)]
    def chunk(tag, data):
        return struct.pack('>I', len(data))+tag+data+struct.pack('>I', zlib.crc32(tag+data))
    ihdr = struct.pack('>IIBBBBB', len(pixels[0]), len(pixels), 8, 3, 0, 0, 0)
    raw = b''.join(b'\0'+bytes(row) for row in pixels)
    dest.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', ihdr)+
                     chunk(b'PLTE', b''.join(bytes(rgb) for rgb in pal))+
                     chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b''))
    got, palette = verify.png(dest)
    assert all(palette[got[3*y][3*x]] == pal[v] for y, row in enumerate(im) for x, v in enumerate(row))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build', required=True)
    p.add_argument('--before', default='build/product1-eng4-20261015/product-r12')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    B, old, out = Path(a.build), Path(a.before), Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    levels = json.loads((ROOT/'assets/levels/product1-campaign.json').read_text())['levels']
    bounds = json.loads((ROOT/'assets/levels/product1-bounds.json').read_text())['levels']
    original, fixed = (old/'candidate.atr').read_bytes(), (B/'candidate.atr').read_bytes()
    assert sha(old/'candidate.atr') == '251bed99b3567eb3fac8b1d0c243392ef5163405f98b88e9ccad54d81f742695'
    assert (old/'candidate.xex').read_bytes() == (B/'candidate.xex').read_bytes()
    assert (old/'campaign-run-r2/emulator.cfg').read_bytes() == (B/'campaign-run-r2/emulator.cfg').read_bytes()
    assert gzip.decompress((old/'campaign-run-r2/input.gz').read_bytes()) == gzip.decompress((B/'campaign-run-r2/input.gz').read_bytes())
    # Only the 60 precompiled art payloads may differ. Board sectors, loaders,
    # catalog, save slots, menu, splash and music remain byte identical.
    allowed = bytearray(len(fixed))
    for n in range(60):
        at = offset(1101+n*70, 128)
        allowed[at:at+8768] = bytes([1])*8768
    assert all(x == y or allowed[i] for i, (x, y) in enumerate(zip(original, fixed)))
    assert len(original) == len(fixed)
    spec = importlib.util.spec_from_file_location('backdrop', ROOT/'experiments/art3-contextual-decoration/decoration.py')
    backdrop = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backdrop)
    text = (B/'reference/prototype_assets.c').read_text()
    arrays = {name: bytes(map(int, re.findall(r'\d+', data))) for name, data in
              re.findall(r'const unsigned char (\w+)\[\] = \{(.*?)\};', text, re.S)}
    campaign = json.loads((B/'campaign-run-r2/campaign-result.json').read_text())
    labs = verify.labels(B/'candidate.lbl')
    records, pixels, observed = [], [], {area: 0 for area in range(1, 5)}
    for n, (level, rect, replay) in enumerate(zip(levels, bounds, campaign['levels'])):
        before, after = sections(original, n), sections(fixed, n)
        w, h = rect['visual_size']
        backdrop.AREA = level['area']
        d = after[0x9de0]
        assert d[:8] == before[0x9de0][:8] and d[536:] == before[0x9de0][536:]
        for strip, address in enumerate(BANKS):
            for index in range(24):
                aa, bb = before[0x9de0][8+strip*24+index], d[8+strip*24+index]
                assert (aa&128) == (bb&128)
                assert before[address][(aa&127)*8:(aa&127)*8+8] == after[address][(bb&127)*8:(bb&127)*8+8]
        oldanim, newanim = animations(before), animations(after)
        assert len(oldanim) == len(newanim)
        for aa, bb in zip(oldanim, newanim):
            assert aa[:3] == bb[:3], (n+1, 'device position/period/phase changed')
            pos = aa[0]-0x8800
            assert [glyph(before, pos, c) for c in aa[3:]] == [glyph(after, pos, c) for c in bb[3:]]
        deco = json.loads((B/f"art-area-{level['area']}/level-{n+1:02d}/scene-0-banks.json").read_text())['devices']
        previous = json.loads((old/f"art-area-{level['area']}/level-{n+1:02d}/scene-0-banks.json").read_text())['devices']
        assert deco == previous
        device_cells = {(x, y) for dev in deco for y in range(dev['y'], dev['y']+dev['height'])
                        for x in range(dev['x'], dev['x']+dev['width'])}
        pad = active = 0
        for y in range(8):
            for x in range(16):
                for q in range(4):
                    pos = (5+y*2+q//2)*40+4+x*2+q%2
                    c = after[0x1400][(y*20+x)*4+q]
                    assert c == after[0x9800][pos-80]
                    if x < w and y < h or (x, y) in device_cells:
                        assert glyph(before, pos, before[0x9800][pos-80]) == glyph(after, pos, c), (n+1, x, y, 'real wall/floor/device drift')
                        active += 1
                    else:
                        assert level['rows'][y][x] == '#'
                        if level['area'] == 1:
                            # VIS1 restores the original scene-map ink and
                            # selects dim brass PF3 for ambient fragments.
                            code = arrays['scene_maps'][pos-80]
                            data = arrays['gameplay_common'][32:]
                            data = bytes(8) if not code else data[((code&127)-92)*8:((code&127)-91)*8]
                            expected = bytes(sum((3 if (v>>k)&3 else 0)<<k for k in (0,2,4,6)) for v in data)
                            selector = 128
                        else:
                            expected = backdrop.background(pos, bytes(8), [])
                            selector = 0
                        assert glyph(after, pos, c) == bytes([selector])+expected, (n+1, x, y, 'padding covers backdrop')
                        pad += 1
        initial = replay['frame']-replay['moves']*8-15
        for frame in (initial, replay['frame']):
            pixels.append(live(B/'campaign-run-r2', frame, labs, after))
        r1 = (B/f'campaign-run-r2/frame-{initial:04}.ram').read_bytes()
        r2 = (B/f"campaign-run-r2/frame-{replay['frame']:04}.ram").read_bytes()
        observed[level['area']] += sum(r1[pos] != r2[pos] for pos, *_ in newanim)
        records.append(dict(level=n+1, visual_size=[w, h], active_quarters=active,
                            exposed_background_quarters=pad, initial_frame=initial, status='PASS'))
    assert all(observed.values()), observed
    # Verify redraw after restart and cold save resume, including real OS SIO.
    for name, frames in (('restart-after-resume', [1500]), ('cold-resume', [1200, 1300]), ('stock-os-sio-save', [4500, 4650])):
        for frame in frames:
            pixels.append(live(B/name, frame, labs, sections(fixed, 0)))
    selected = (1, 2, 3, 12, 13, 14, 18, 36, 40, 41, 48)
    comparisons = []
    for n in selected:
        frame = records[n-1]['initial_frame']
        for label, source in (('before', old), ('after', B)):
            src = source/f'campaign-run-r2/native-{frame:04}.png'
            dest = out/f'level-{n:02d}-{label}-native.png'
            shutil.copyfile(src, dest)
            enlarge(src, out/f'level-{n:02d}-{label}-3x.png')
        comparisons.append(dict(level=n, frame=frame, visual_size=bounds[n-1]['visual_size'],
                                source='unmodified candidate ATR, cold boot and full campaign replay, same inputs/frame/config'))
    for name, frame in (('restart-after-resume', 1500), ('cold-resume', 1200)):
        for label, source in (('before', old), ('after', B)):
            src = source/name/f'native-{frame:04}.png'
            dest = out/f'{name}-{label}-native.png'
            shutil.copyfile(src, dest)
            enlarge(src, out/f'{name}-{label}-3x.png')
    for name in ('campaign-run-r2', 'restart-after-resume', 'cold-resume', 'stock-os-sio-save'):
        target = out/'emulator'/name
        target.mkdir(parents=True)
        for f in ('command.json', 'emulator.cfg', 'artifact.json', 'host-pacing.json'):
            if (B/name/f).exists():
                shutil.copyfile(B/name/f, target/f)
    target = out/'emulator/before-campaign'
    target.mkdir()
    for f in ('command.json', 'emulator.cfg', 'artifact.json', 'host-pacing.json'):
        shutil.copyfile(old/'campaign-run-r2'/f, target/f)
    transitions = [dict(before=i, after=i+1, from_size=bounds[i-1]['visual_size'], to_size=bounds[i]['visual_size']) for i in range(1,60)]
    result = dict(status='PASS', ATR_sha256=sha(B/'candidate.atr'), before_sha256=sha(old/'candidate.atr'),
                  runtime_XEX_identical=True, only_disk_art_changed=True, levels=records,
                  comparison_config_and_input_identical=True,
                  comparisons=comparisons, transitions=transitions, animated_fragments_changed=observed,
                  pixels=pixels, pixel_comparisons=sum(p['pixels'] for p in pixels),
                  outline_scope='All authored outer rectangles are rectangular. Level 36 covers an irregular interior with 7 real wall obstacles; no exterior irregular shape was invented.',
                  visual_owner='OWNER_PENDING', r4_visual_owner='FAIL', hardware_owner='NOT_RUN')
    (out/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS 60 layer/geometry/backdrop/device audits, 120 campaign rasters + restart/resume, comparisons', flush=True)


if __name__ == '__main__':
    main()
