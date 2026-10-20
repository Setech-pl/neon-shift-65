; Resident lifecycle and IRQ gate. Never overwritten by menu or packages.
.export _pmg_off,_pmg_prepare,_pmg_on,_pmg_active
.exportzp robot_ptr
.segment "BSS"
_pmg_active:.res 1
.segment "CODE"
_pmg_off:
    lda #0
    sta _pmg_active             ; detach callback FIRST
    sta $d01d                  ; GRACTL
    sta $d000
    sta $d001
    sta $d002
    sta $d003
    sta $d004
    sta $d005
    sta $d006
    sta $d007
    sta $d00d
    sta $d00e
    sta $d00f
    sta $d010
    sta $d011
    sta $d01b
    sta $026f
    sta $d01c
    sta $d407
    ldx #3
@colors:
    sta $d012,x
    sta $02c0,x
    sta $d008,x
    dex
    bpl @colors
    lda #$22
    sta $022f
    sta $d400
    rts
_pmg_prepare:
    lda #0
    ldx #0
@clear:
    .repeat 8,I
        sta $a800+I*$100,x
    .endrepeat
    inx
    bne @clear
    lda #$a8
    sta $d407
    lda #$ee
    sta $d012
    sta $02c0
    lda #$9e
    sta $d013
    sta $02c1
    lda #1                     ; P0/P1 above playfield, disjoint color masks
    sta $d01b
    sta $026f
    rts
_pmg_on:
    lda #1
    sta _pmg_active
    lda #2                     ; players only, no missiles
    sta $d01d
    lda #$3a                   ; single-line player DMA + normal playfield
    sta $022f
    sta $d400
    rts
