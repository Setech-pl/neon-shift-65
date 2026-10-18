"""Audit the final ATR: only wall pixels and their glyph remaps may differ."""
import json
from pathlib import Path
from verify import packages, sha, BUILD, ROOT

BANKS = (0x8c00, 0xa000, 0xa400, 0xa800, 0xac00)


def quarter(sections, code, row):
    bank = min((row-2)//4,4)
    raw = sections[BANKS[bank]][(code&127)*8:(code&127)*8+8]
    return tuple((4 if code&128 and (v>>k)&3 == 3 else (v>>k)&3)
                 for v in raw for k in (6,4,2,0))


def main():
    out = BUILD/'area-1'
    before = (BUILD/'baseline/area-1/candidate.atr').read_bytes()
    after = (out/'candidate.atr').read_bytes()
    old, new = packages(before), packages(after)
    levels = json.loads((out/'levels.json').read_text())['levels']
    result = []
    for scene,(a,b) in enumerate(zip(old[:3],new[:3])):
        ad,bd = a[0x9de0],b[0x9de0]
        assert ad[:8] == bd[:8] and ad[536:] == bd[536:]
        assert a[0xb160] == b[0xb160], 'Robot source frames'
        w,h,bx,by = bd[:4]
        plan = json.loads((out/f'scene-{scene}-wall-sections.json').read_text())
        allowed = {(c['x'],c['y']) for c in plan['cells'] if c['kind']}
        allowed_quarters = {(by+2*y+q//2)*40+bx+2*x+q%2
                            for x,y in allowed for q in range(4)}
        changed = []
        for pos,(ac,bc) in enumerate(zip(a[0x9800],b[0x9800]),80):
            row = pos//40
            if quarter(a,ac,row) != quarter(b,bc,row):
                assert pos in allowed_quarters, (scene,pos,'Changed non-wall art')
                changed.append(pos)
        floor_quarters = 0
        for y,row in enumerate(levels[scene]['rows']):
            for x,v in enumerate(row):
                if v == '#':
                    continue
                for q in range(4):
                    offset = (y*20+x)*4+q
                    rr = by+2*y+q//2
                    assert quarter(a,a[0x1400][offset],rr) == quarter(b,b[0x1400][offset],rr)
                    floor_quarters += 1
        # Resolve remapped object/animation codes through each actual font bank.
        for bank in range(5):
            for n in range(24):
                off = 8+bank*24+n
                assert quarter(a,ad[off],2+bank*4) == quarter(b,bd[off],2+bank*4)
        for i in range(ad[4]):
            off = 128+i*8
            assert ad[off:off+4] == bd[off:off+4], 'Animation position/period/phase'
            row = (int.from_bytes(ad[off:off+2],'little')-0x8800)//40
            for phase in range(4):
                assert quarter(a,ad[off+4+phase],row) == quarter(b,bd[off+4+phase],row)
        # Check solid connecting shoulders and centreline on both axes in ATR.
        def pixel(x,y,px,py):
            q = (py//8)*2+px//4
            rr = by+2*y+q//2
            code = b[0x1400][(y*20+x)*4+q]
            return quarter(b,code,rr)[(py%8)*4+px%4]
        for cell in plan['cells']:
            x,y,m = cell['x'],cell['y'],cell['mask']
            assert levels[scene]['rows'][y][x] == '#'
            if m&1: assert all(pixel(x,y,px,0) for px in (2,3,5))
            if m&4: assert all(pixel(x,y,px,15) for px in (2,3,5))
            if m&2: assert all(pixel(x,y,7,py) for py in (4,8,11))
            if m&8: assert all(pixel(x,y,0,py) for py in (4,8,11))
        bank_stats = []
        for i,addr in enumerate(BANKS):
            report = json.loads((out/f'scene-{scene}-banks.json').read_text())['banks'][i]
            baseline = json.loads((BUILD/f'baseline/area-1/scene-{scene}-banks.json').read_text())['banks'][i]
            def glyphs(data,n):return {data[j*8:j*8+8] for j in range(n)}
            aa = glyphs(a[addr],baseline['static_unique'])
            bb = glyphs(b[addr],report['static_unique'])
            assert report['dynamic_reserved'] == 4 and not report['conflicts']
            bank_stats.append(dict(bank=i,before_free=baseline['free'],after_free=report['free'],
                                   added_unique=len(bb-aa),removed_unique=len(aa-bb)))
        result.append(dict(scene=scene,changed_wall_quarters=changed,
            unchanged_floor_quarters=floor_quarters,unchanged_animations=ad[4],
            connected_shoulders='PASS',banks=bank_stats))
    allowed_bytes = set()
    for i,start in enumerate((512,640,768)):
        allowed_bytes.update(range(16+(start-1)*128,16+(start-1)*128+8768))
        allowed_bytes.update((400+16+i*16+8,400+16+i*16+9))
    allowed_bytes.update((526,527))
    changed_bytes = [i for i,(a,b) in enumerate(zip(before,after)) if a != b]
    assert len(before) == len(after) == 1048592
    assert all(i in allowed_bytes for i in changed_bytes), 'Unexpected ATR sector change'
    data = dict(status='PASS',scenes=result,ATR_bytes=len(after),
        changed_ATR_bytes=len(changed_bytes),ATR_diff_scope='Three scene packages and catalogue CRC only',
        scene_RAW_bytes=8624,scene_disk_bytes=8768,font_banks_bytes=5120,
        resource_RAM_growth_bytes=0,baseline_ATR_sha256=sha(BUILD/'baseline/area-1/candidate.atr'),
        candidate_ATR_sha256=sha(out/'candidate.atr'))
    (BUILD/'asset-audit.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))


if __name__ == '__main__':
    main()
