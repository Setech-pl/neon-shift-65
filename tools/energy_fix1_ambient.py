"""Three screen-code ambient entries; original FINAL1 pixels/palette at phase 0.

Uses the existing validated descriptor/cache/VBI mechanism, bounded to four
entries instead of 32. Never mutates a shared glyph or a palette register.
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
CAPACITY = 4


def descriptors(background, level, fonts, screen):
    original = background.image(level)
    variants = [[row[:] for row in original] for _ in range(4)]
    c = background.c
    vw, vh = level['visual_size']
    if 16 + vw * 8 <= 120:
        x = 24 + vw * 8
        positions = [(7, (x + 4) // 4), (7, (x + 8) // 4)]
        for phase, peak in enumerate((58, 60, 62, 60)):
            if not phase:
                continue
            p = variants[phase]
            for yy in range(58, 64):
                for xx in range(x + 5, x + 12):
                    if p[yy][xx] == 1:
                        p[yy][xx] = 0
            c.line(p, x + 5, 63, x + 8, peak, 1)
            c.line(p, x + 8, peak, x + 11, 63, 1)
    else:
        positions = [(10, 37), (10, 38)]
        for phase, height in enumerate((4, 3, 2, 3)):
            p = variants[phase]
            for yy in range(80, 84):
                for xx in (151, 152):
                    p[yy][xx] = 1 if yy >= 84 - height else 0
    # Existing junction-box control; exactly its 3x2 pixels change ink.
    positions.append((22, 17))
    for phase in (2, 3):
        for yy in (182, 183):
            for xx in (69, 70, 71):
                variants[phase][yy][xx] = 3
    neon = os.environ.get('NEON_ENERGY_NEON1') == '1'
    if neon:
        positions.append((22, 8))
        for phase, image in enumerate(variants):
            if not phase: continue
            for xx in range(32,36):
                image[180][xx] = 1 if xx <= 32+phase else 3
    result = []
    metadata = []
    for slot, (row, col) in enumerate(positions):
        bank = 0 if row < 13 else 1
        codes = []
        selector = background.selector(level, row, col)
        for phase, image in enumerate(variants):
            glyph = background.glyph(image, row * 40 + col)
            if phase == 0:
                code = screen[(row - 2) * 40 + col]
                assert fonts[bank][code & 127] == glyph
                assert code & 128 == selector
            else:
                # A screen code is swapped, never font bytes: deduplication
                # cannot make another occurrence animate accidentally.
                try:
                    index = fonts[bank].index(glyph)
                except ValueError:
                    index = len(fonts[bank])
                    assert index < 124, 'Ambient font capacity exceeded'
                    fonts[bank].append(glyph)
                code = index | selector
            codes.append(code)
        assert len(set(codes)) > 1, (level['number'], slot)
        period = 36 if slot < 2 else 50 if slot == 2 else 13
        addr = 0x8800 + row * 40 + col
        result.append(bytes((addr & 255, addr >> 8, period, 0, *codes)))
        metadata.append(dict(role='meter' if slot < 2 else 'control' if slot == 2 else 'segments',
                             row=row, col=col, address=addr,
                             period=period, codes=codes,
                             native_box=[8 + col * 8, 24 + row * 8, 8, 8]))
    assert len(result) == (4 if neon else 3)
    return b''.join(result), metadata


def install(source):
    """Restore the existing ambient path after the industrial source transform."""
    original = (ROOT / 'experiments/eng3-observed-input-3pal/hardware.s').read_text()
    f = source / 'hardware.s'
    s = f.read_text()
    body = original[original.index('background_update:\n'):original.index('@menu:\n', original.index('background_update:\n'))]
    # The original routine transposes four phases at stride 32. Capacity 4
    # requires stride 4, phase mask 12 and two shifts in reset.
    body = body.replace('adc #32', 'adc #4').replace('and #96', 'and #12')
    a = s.index('background_update:\n')
    b = s.index('@menu:\n', a)
    s = s[:a] + body + s[b:]
    a = original.index('_animation_reset:\n')
    b = original.index('.segment "CODE"\n_music_update', a)
    reset = original[a:b].replace('ldx #31', 'ldx #3')
    reset = reset.replace('.repeat 5', '.repeat 2')
    reset = reset.replace('anim_frames+32', 'anim_frames+4')
    reset = reset.replace('anim_frames+64', 'anim_frames+8')
    reset = reset.replace('anim_frames+96', 'anim_frames+12')
    reset = reset.replace('.res 32', '.res 4').replace('.res 128', '.res 16')
    a = s.index('_animation_reset:\n')
    b = s.index('.segment "CODE"\n_music_update', a)
    s = s[:a] + reset + s[b:]
    s = s.replace('robot_ptr: .res 2\n', 'robot_ptr: .res 2\nanim_ptr:.res 2\n')
    s += '''\n.segment "BSS"
anim_ticks:.res 4
anim_phases:.res 4
anim_count:.res 1
'''
    f.write_text(s)
    # Existing validation remains in force: no more than three exact Energy
    # positions, unique addresses, nonzero periods, four legal screen codes.
    f = source / 'validate.c'
    s = f.read_text()
    assert s.count('count!=0') == 1
    s = s.replace('count!=0', 'count!=(DESC[6]==1?3:0)')
    marker = '        at=128+(unsigned int)i*8;position=word(DESC+at);'
    assert marker in s
    s = s.replace(marker, marker + '''
        /* Exact authored instrument cells. No target in puzzle/HUD/buffers. */
        if(i<2){
            if(DESC[541]<=13){
                if(position!=0x8800+7*40+7+2*DESC[541]+i || DESC[at+2]!=36)return 0;
            }else if(position!=0x8800+10*40+37+i || DESC[at+2]!=36)return 0;
        }else if(position!=0x8800+22*40+17 || DESC[at+2]!=50)return 0;
        if(DESC[at+3])return 0;''')
    f.write_text(s)
