.include "neon-palette.inc"
.export _loading_begin,_loading_progress,_loading_done,_loading_finish,_loading_label,_loading_vbi
_loading_progress=$17d4
_loading_done=$17d0

.segment "CODE"
_loading_begin:
    ; System screen remains one presentation through all internal packages.
    lda $17df
    cmp #$65
    beq @system
    cmp #$53
    beq @system
    cmp #$4d
    beq @system
    inc $17dc
    lda #0
    sta _loading_progress
    sta _loading_done
    sta _loading_done+1
    lda #$53
    sta $17df
@system:
    ldx #18
    lda $17df
    cmp #$53
    beq @shift_label
@system_label:
    lda system_message,x
    sta $1744,x
    dex
    bpl @system_label
    bmi @label_done
@shift_label:
    lda shift_message,x
    sta $1744,x
    dex
    bpl @shift_label
@label_done:
    lda #$00
    sta $230
    lda #$bf
    sta $231
    lda #$e0
    sta $2f4
    sta $d409
    lda #AREA_LOADER
    sta $2c4
    lda #14
    sta $2c5
    lda #0
    sta $2c6
    sta $2c8
    jmp loading_text
_loading_finish:
    lda $17df
    beq @done
    inc _loading_done
    bne :+
    inc _loading_done+1
:   lda #0
    sta $17df
    lda #32
    sta _loading_progress
    jmp _loading_update
@done:
    rts
_loading_label:
    cmp #4
    bcc @done
    lda $17df
    cmp #$65
    beq @done
    cmp #$4d
    beq @done
    lda #$4d
    sta $17df
    inc $17dc
    lda #0
    sta _loading_done
    sta _loading_done+1
    sta _loading_progress
    ldx #18
@menu_label:
    lda system_message,x
    sta $1744,x
    dex
    bpl @menu_label
@done:
    jmp loading_text
_loading_vbi:
    jsr _loading_update
    lda #$e0
    sta $d409
    lda #AREA_LOADER
    sta $d016
    lda #14
    sta $d017
    lda #0
    sta $d018
    lda #$22
    sta $22f
    sta $d400
    rts
.segment "RODATA"
system_message:
    .byte 41,46,41,52,41,33,44,41,58,41,46,39,0,51,57,51,52,37,45
shift_message:
    .byte 44,47,33,36,41,46,39,0,51,40,41,38,52,0,0,0,0,0,0

.export _loading_update
_loading_update:
    ldx #31
@cell:
    txa
    cmp $17d4
    lda #$55
    bcs :+
    lda #$ff
:   sta $176c,x
    sta $1794,x
    dex
    bpl @cell
    lda $176c
    ora #$80
    sta $176c
    sta $1794
    rts

.include "loading-text.s"
