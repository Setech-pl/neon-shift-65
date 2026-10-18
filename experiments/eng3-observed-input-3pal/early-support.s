.include "neon-palette.inc"
.export early_start,early_ui,early_unpack
.import _splash_run
src=$82
dst=$84
match=$86
.segment "CODE"
early_start:
    jsr early_unpack
    bcc @ok
@error:
    jmp @error
@ok:
    jsr _splash_run
    rts
early_ui:
    jsr $9240
    lda #$00
    sta $230
    lda #$bf
    sta $231
    lda #$e0
    sta $2f4
    lda #AREA_LOADER
    sta $2c4
    lda #14
    sta $2c5
    lda #0
    sta $2c6
    sta $2c8
    lda #$22
    sta $22f
    sta $d400
    lda #1
    sta $17de
    rts
early_unpack:
    lda #0
    sta src
    lda #$8c
    sta src+1
    lda #$10
    sta dst
    lda #$a0
    sta dst+1
@command:
    jsr get
    beq @end
    bmi @match
    tax
@literal:
    jsr get
    jsr put
    dex
    bne @literal
    jmp @command
@match:
    sta command
    and #3
    sta high
    jsr get
    sta low
    lda dst
    clc
    sbc low
    sta match
    lda dst+1
    sbc high
    sta match+1
    lda match
    cmp #$10
    lda match+1
    sbc #$a0
    bcc fail
    lda command
    and #$7c
    lsr a
    lsr a
    clc
    adc #3
    tax
@copy:
    ldy #0
    lda (match),y
    jsr put
    inc match
    bne :+
    inc match+1
:   dex
    bne @copy
    jmp @command
@end:
    lda dst
    cmp #$10
    bne fail
    lda dst+1
    cmp #$be
    bne fail
    lda src
    cmp #<($8c00+PACKED_BYTES)
    bne fail
    lda src+1
    cmp #>($8c00+PACKED_BYTES)
    bne fail
    clc
    rts
get:
    lda src
    cmp #<($8c00+PACKED_BYTES)
    lda src+1
    sbc #>($8c00+PACKED_BYTES)
    bcs abort
    ldy #0
    lda (src),y
    inc src
    bne :+
    inc src+1
:   ora #0
    rts
put:
    pha
    lda dst
    cmp #$10
    lda dst+1
    sbc #$be
    bcs bad_put
    pla
    ldy #0
    sta (dst),y
    inc dst
    bne :+
    inc dst+1
:   rts
bad_put:
    pla
abort:
    pla
    pla
fail:
    sec
    rts
command:.byte 0
high:.byte 0
low:.byte 0
