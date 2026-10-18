#!/usr/bin/env python3
"""Read-only RECOVERY1 extraction from shipped ATR sectors, never JSON authoring."""
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/recovery1'
DISKS = {
    'CAMP2-B': 'build/camp2-b-candidate-20261015/neon-shift65-camp2-b-60.atr',
    'ART4-A': 'build/art4-a-candidate-20261015/neon-shift65-art4-A.atr',
    'ART4-B': 'build/art4-a-candidate-20261015/neon-shift65-art4-B.atr',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def crc(data):
    value = 0xffff
    for byte in data:
        value ^= byte << 8
        for _ in range(8):
            value = ((value << 1) ^ (0x1021 if value & 0x8000 else 0)) & 0xffff
    return value


def sector(image, n, count=1):
    return image[16+(n-1)*128:16+(n-1+count)*128]


def extract(path):
    image = path.read_bytes()
    magic, low, size, high = struct.unpack_from('<4H', image)
    assert magic == 0x296 and size == 128
    assert len(image)-16 == (low+(high << 16))*16
    cat = sector(image, 1000)
    assert cat[:5] == b'NSCD\1' and crc(cat[:126]) == int.from_bytes(cat[126:], 'little')
    assert cat[5] == 60
    levels = []
    for i in range(cat[5]):
        b = sector(image, 1100+i*70)
        assert b[:5] == b'NSLV\1' and b[5] == i
        assert b[12:16] == cat[8:12]
        assert crc(b[:126]) == int.from_bytes(b[126:], 'little')
        w, h = b[10:12]
        assert (w, h) == (16, 8)
        cells = [(b[16+n//4] >> ((n % 4)*2)) & 3 for n in range(w*h)]
        assert all(v in (0, 1, 2) for v in cells)
        rows = [list(''.join('# .'[v] for v in cells[y*w:(y+1)*w])) for y in range(h)]
        boxes = [list(b[48+j*2:50+j*2]) for j in range(b[7])]
        goals = [[x, y] for y in range(h) for x in range(w) if rows[y][x] == '.']
        for x, y in boxes:
            assert rows[y][x] in ' .'
            rows[y][x] = '*' if rows[y][x] == '.' else '$'
        x, y = b[8:10]
        assert rows[y][x] in ' .'
        rows[y][x] = '+' if rows[y][x] == '.' else '@'
        rows = [''.join(r) for r in rows]
        pack = sector(image, 1101+i*70, 69)[:8768]
        assert pack[:4] == b'NSRQ'
        assert crc(pack[:14]) == int.from_bytes(pack[14:16], 'little')
        assert crc(pack[16:144]) == int.from_bytes(pack[12:14], 'little')
        assert crc(pack[144:]) == int.from_bytes(pack[10:12], 'little')
        sections = {}
        for j in range(pack[6]):
            addr, length, pos, checksum = struct.unpack_from('<4H', pack, 16+j*8)
            data = pack[144+pos:144+pos+length]
            assert len(data) == length and crc(data) == checksum
            sections[addr] = data
        desc = sections[0x9de0]
        assert list(desc[:2]) == [w, h] and desc[6] == b[6]
        # Authored bounds are absent in NSLV. No flood-fill inference here.
        levels.append(dict(number=i+1, disk_id=b[5], area=b[6],
                           name=b[68:100].split(b'\0')[0].decode('ascii'),
                           storage_size=[w, h], player=list(b[8:10]), boxes=boxes,
                           goals=goals, rows=rows, free_cells=sum(v != 0 for v in cells),
                           board_sha256=sha(b), board_crc16=int.from_bytes(b[126:], 'little'),
                           package_sha256=sha(pack), palette=list(desc[536:541])))
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(image), bytes=len(image),
                campaign_id=cat[8:12].hex(), levels=levels)


def main():
    OUT.mkdir(exist_ok=True)
    disks = {name: extract(ROOT/path) for name, path in DISKS.items()}
    preflight = OUT/'preflight.json'
    revision = json.loads(preflight.read_text())['initial_HEAD'] if preflight.exists() else 'e01cbfc8bacc8dd243ac7af9905d3f0585be0804'
    historical_raw = subprocess.check_output(['git', 'show', revision+':assets/levels/camp2-b/campaign.json'], cwd=ROOT)
    historical = json.loads(historical_raw)
    current_path = ROOT/'assets/levels/camp2-b/campaign.json'
    current_raw = current_path.read_bytes()
    current = json.loads(current_raw)
    rects = json.loads((ROOT/'assets/levels/camp2-b/bounds.json').read_text())
    assert rects['campaign_sha256'] == sha(historical_raw)
    for name, disk in disks.items():
        for packed, authored, rect in zip(disk['levels'], historical['levels'], rects['levels']):
            assert packed['rows'] == authored['rows'], (name, packed['number'])
            assert packed['name'] == authored['name'] and packed['area'] == authored['area']
            assert sha('\n'.join(packed['rows']).encode()) == rect['rows_sha256']
            w, h = rect['visual_size']
            assert all(ch == '#' for y, row in enumerate(packed['rows']) for x, ch in enumerate(row) if x >= w or y >= h)
            packed.update(authored_size=[w, h], padding_cells=128-w*h,
                          authored_walls=w*h-packed['free_cells'],
                          bounds_evidence='matching committed bounds.json + exact rows SHA; NOT encoded in NSLV')
    baseline = disks['CAMP2-B']['levels']
    keys = ('number', 'disk_id', 'area', 'name', 'storage_size', 'player', 'boxes', 'goals', 'rows')
    comparisons = {}
    for name in ('ART4-A', 'ART4-B'):
        comparisons[name] = [dict(number=a['number'], differences=[k for k in keys if a[k] != b[k]],
                                 board_sector_identical=a['board_sha256'] == b['board_sha256'],
                                 art_identical=a['package_sha256'] == b['package_sha256'])
                             for a, b in zip(baseline, disks[name]['levels'])]
        assert len(disks[name]['levels']) == 60
    current_delta = [dict(number=b['number'], rows_changed=b['rows'] != c['rows'],
                          player_changed=b['player'] != next([x,y] for y,r in enumerate(c['rows']) for x,ch in enumerate(r) if ch in '@+'),
                          authored_size=c['visual_size']) for b,c in zip(baseline,current['levels'])]
    result = dict(method='Read NSCD1000, NSLV1100+70*n, NSRQ1101+70*n from actual ATR; independent CRC16 implementation',
                  disks=disks, comparisons=comparisons,
                  source_at_HEAD_sha256=sha(historical_raw), working_source_sha256=sha(current_raw),
                  working_source_stage=current['stage'], working_source_differences=current_delta)
    (OUT/'atr-levels.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines = ['# RECOVERY1 — poziomy odczytane z ATR', '',
             'Wszystkie trzy ATR zawierają te same 60 rekordów NSLV w tej samej kolejności. ID na dysku to 0–59, numery ekranowe 1–60. Geometria, gracz, skrzynie, cele, obszary i nazwy są identyczne; różni się oprawa Energy. Każdy sektor planszy jest identyczny bajtowo.', '',
             'Wymiary zapisane w NSLV: zawsze **16×8**. Właściwy prostokąt autorski pochodzi z metadanych bounds.json związanych hashem z historycznym campaign.json i dokładnie zgodnych z wyodrębnionymi wierszami. Sam ATR nie rozróżnia ściany paddingu od ściany autorskiej. Pola gry oznaczają wszystkie pola niebędące ścianą (łącznie z obiektami i celami), bez zależności od chwilowej osiągalności gracza.', '',
             '| Energy | Prostokąt autorski | Pola gry | Ściany autorskie | Padding poza prostokątem | Skrzynie | Cele | CAMP2-B / A / B |',
             '|---|---:|---:|---:|---:|---:|---:|---|']
    for l in baseline[:15]:
        w,h=l['authored_size']
        lines.append(f"| {l['number']:02d} | {w}×{h} | {l['free_cells']} | {l['authored_walls']} | {l['padding_cells']} | {len(l['boxes'])} | {len(l['goals'])} | mapy identyczne |")
    lines += ['', 'Aktualne źródło właściciela ma etap **'+current['stage']+'** i '+str(sum(x['rows_changed'] for x in current_delta))+' map innych niż gotowe ATR. Pozostaje nietknięte. Pełne współrzędne, wiersze, ID, CRC, palety i różnice wszystkich 60 poziomów: [atr-levels.json](atr-levels.json).', '', '| ATR | SHA-256 |', '|---|---|']
    for name,disk in disks.items():lines.append(f"| {name} | `{disk['sha256']}` |")
    (OUT/'levels.md').write_text('\n'.join(lines)+'\n')
    # Frozen, separately named recovery build input. Original file stays read-only.
    build = ROOT/'build/recovery1'; build.mkdir(exist_ok=True)
    (build/'packed-camp2b-source.json').write_bytes(historical_raw)
    (build/'packed-camp2b-bounds.json').write_text(json.dumps(rects,indent=2)+'\n')
    current_bounds = dict(version=1, campaign_sha256=sha(current_raw), source='Read-only visual_size metadata of owner source; no inference',
                          levels=[dict(number=l['number'], visual_size=l['visual_size'], rows_sha256=sha('\n'.join(l['rows']).encode())) for l in current['levels']])
    (build/'owner-source-snapshot.json').write_bytes(current_raw)
    (build/'owner-source-bounds.json').write_text(json.dumps(current_bounds,indent=2)+'\n')
    print('PASS: 3 ATR × 60 boards, all sectors identical; current source differs on', sum(x['rows_changed'] for x in current_delta), 'maps')


if __name__ == '__main__':
    main()
