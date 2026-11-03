"""A code-native, two-colour ANTIC 2 scene; no bitmap/sprite RAM allocation."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def redraw(out):
    from PIL import Image,ImageDraw
    im=Image.new('1',(128,96));d=ImageDraw.Draw(im)
    # Quiet industrial frame and conduit, assembled on an eight-pixel grid.
    d.line((0,8,127,8),fill=1);d.line((0,12,127,12),fill=1)
    for x in (8,120):
        d.line((x,8,x,87),fill=1)
        for y in (16,80):d.rectangle((x-2,y,x+2,y+3),outline=1)
    for x in (32,80,112):d.line((x,8,x,12),fill=1)
    d.line((0,88,127,88),fill=1);d.line((0,92,127,92),fill=1)
    for x in range(0,128,16):d.line((x,93,x+4,93),fill=1)
    # Same broad domed body, right visor, forked feet and pushing hand as
    # pmg1_art.frames(), reinterpreted at native 1-bit character resolution.
    d.rectangle((30,32,53,37),fill=1)
    d.rectangle((24,38,59,61),fill=1)
    d.rectangle((30,62,53,67),fill=1)
    d.rectangle((42,41,59,49),fill=0)
    d.line((44,43,57,43),fill=1)
    d.rectangle((30,53,41,55),fill=0)
    d.rectangle((48,59,65,64),fill=1);d.rectangle((62,56,71,64),fill=1)
    # Rear leg trails left; front foot braces beneath the container edge.
    d.rectangle((23,65,34,73),fill=1);d.rectangle((17,74,28,79),fill=1)
    d.rectangle((11,80,28,83),fill=1)
    d.rectangle((48,66,59,78),fill=1);d.rectangle((48,79,65,83),fill=1)
    d.rectangle((50,71,53,74),fill=0)
    # Steel container, two runners and the game's lightning-shaped label.
    d.rectangle((72,48,111,83),outline=1)
    d.rectangle((75,51,108,79),outline=1)
    d.rectangle((78,84,85,87),fill=1);d.rectangle((100,84,107,87),fill=1)
    d.polygon([(94,56),(101,56),(94,63),(99,63),(86,74),(91,65),(86,65)],fill=1)
    for x in (78,104):d.point((x,54),fill=1);d.point((x,76),fill=1)
    # Short skid marks make the direction legible without animation.
    d.line((0,70,10,70),fill=1);d.line((4,74,13,74),fill=1)
    glyphs=[];codes=[];index={bytes(8):0}
    for y in range(0,96,8):
        for x in range(0,128,8):
            tile=bytes(sum(int(im.getpixel((x+xx,y+yy)))<<(7-xx) for xx in range(8)) for yy in range(8))
            if tile not in index:index[tile]=44+len(glyphs);glyphs.append(tile)
            codes.append(index[tile])
    assert len(glyphs)<=84,len(glyphs)
    font=b''.join(glyphs)
    (ROOT/'assets/graphics/selectart1.json').write_text(json.dumps(dict(width=128,height=96,glyph_start=44,glyphs_hex=font.hex(),map_hex=bytes(codes).hex(),status='OWNER_PENDING'),indent=2)+'\n')
    im.convert('RGB').save(out/'selectart1-scene-128x96.png')

def make(out):
    asset=json.loads((ROOT/'assets/graphics/selectart1.json').read_text())
    assert (asset['width'],asset['height'],asset['glyph_start'])==(128,96,44)
    font=bytes.fromhex(asset['glyphs_hex']);codes=bytes.fromhex(asset['map_hex'])
    assert len(font)%8==0 and len(font)<=672 and len(codes)==192
    assert all(c==0 or 44<=c<44+len(font)//8 for c in codes)
    def rle(raw):
        result=bytearray();i=0
        while i<len(raw):
            run=1
            while i+run<len(raw) and raw[i+run]==raw[i] and run<127:run+=1
            if run>=3:result.extend((128|run,raw[i]));i+=run
            else:
                start=i;i+=run
                while i<len(raw) and i-start<127:
                    n=1
                    while i+n<len(raw) and raw[i+n]==raw[i] and n<3:n+=1
                    if n>=3:break
                    if i-start+n>127:break
                    i+=n
                result.append(i-start);result.extend(raw[start:i])
        return bytes(result)
    # Linear decompression also clears the quiet left-hand part of each
    # following row; fields are drawn afterwards. No staging buffer needed.
    wide=b''.join(bytes(codes[i:i+16])+bytes(24) for i in range(0,176,16))+bytes(codes[176:])
    packed=rle(font)+bytes(1);maps=rle(wide)+bytes(1)
    (out/'selectart1-font.rle').write_bytes(packed)
    (out/'selectart1-map.rle').write_bytes(maps)
    h='static const unsigned char art_font[]={'+','.join(map(str,packed))+'};\n'
    h+='static const unsigned char art_map[]={'+','.join(map(str,maps))+'};\n'
    h+=f'#define ART_FONT_BYTES {len(font)}\n'
    (out/'selectart1-data.h').write_text(h)
    (out/'selectart1.s').write_text('''.export _selector_art
.importzp ptr1,ptr2,tmp1
.segment "CODE"
_selector_art:
    lda #<font
    sta ptr1
    lda #>font
    sta ptr1+1
    lda #$60
    sta ptr2
    lda #$91
    sta ptr2+1
    jsr unpack
    ; ptr1 already points to the map following the font terminator.
    lda #$07
    sta ptr2
    lda #$89
    sta ptr2+1
unpack:
    ldy #0
packet:
    jsr next
    tax
    beq done
    bmi run
literal:
    jsr next
    jsr put
    dex
    bne literal
    beq packet
run:
    and #127
    tax
    jsr next
    sta tmp1
repeat:
    lda tmp1
    jsr put
    dex
    bne repeat
    beq packet
next:
    lda (ptr1),y
    inc ptr1
    bne done
    inc ptr1+1
done:
    rts
put:
    sta (ptr2),y
    inc ptr2
    bne done
    inc ptr2+1
    rts
.segment "RODATA"
font:
    .incbin "selectart1-font.rle"
    .incbin "selectart1-map.rle"
''')
    report=dict(resolution=[320,192],scene=[128,96],glyphs=len(font)//8,font_bytes=len(font),font_range=[hex(0x9000+352),hex(0x9000+352+len(font)-1)],screen_map_bytes=192,packed_font=len(packed),packed_map=len(maps),packed_total=len(packed)+len(maps),palette='two colours, existing neutral UI',PMG_bytes_added=0,extended_RAM_bytes=0,acceptance='OWNER_PENDING')
    (out/'selectart1-resource.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':
    import sys
    make(Path(sys.argv[1]))
