; Code-native label raster,40 bytes ×8 native scanlines in dead HUD overlay.
; ROM uppercase glyphs have one blank leading bit. ASL removes that bearing.
; Self-modified operands avoid borrowing foreground/OS zero-page pointers.
.export loading_text
.segment "CODE"
loading_text:
    lda #0
    sta row
    sta output+1
    lda #$91
    sta output+2
text_row:
    ldx #39
text_char:
    lda $1740,x
    and #$1f
    asl a
    asl a
    asl a
    clc
    adc row
    sta glyph+1
    lda $1740,x
    lsr a
    lsr a
    lsr a
    lsr a
    lsr a
    ora #$e0
    sta glyph+2
glyph:
    lda $e000
    asl a
output:
    sta $9100,x
    dex
    bpl text_char
    lda output+1
    clc
    adc #40
    sta output+1
    bcc :+
    inc output+2
:   inc row
    lda row
    cmp #8
    bne text_row
    rts
row:.byte 0
