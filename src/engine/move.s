; Experimental ABI-compatible level_try_move. No ISR calls this code.
; The parser and undo remain shared C; host C supplies an independent oracle.
.export _level_try_move
.import popa,popax
.macpack longbranch
.segment "ZEROPAGE"
move_g:.res 2
move_info:.res 2
move_map:.res 2
move_pushed:.res 2
.ifdef NATIVE_SIM65
.segment "BSS"
.else
.segment "LOADBSS"
.endif
move_dx:.res 1
move_dy:.res 1
move_nx:.res 1
move_ny:.res 1
move_bx:.res 1
move_by:.res 1
move_box:.res 1
.ifdef NATIVE_SIM65
.segment "CODE"
.else
.segment "LOADER"
.endif
_level_try_move:
    sta move_pushed
    stx move_pushed+1
    jsr popa
    sta move_dy
    jsr popa
    sta move_dx
    jsr popax
    sta move_g
    stx move_g+1
    ora move_g+1
    jeq move_fail
    lda move_pushed
    ora move_pushed+1
    jeq move_fail
    ldy #0
    lda #0
    sta (move_pushed),y
    lda move_dx
    beq @vertical
    cmp #1
    beq @horizontal
    cmp #$ff
    jne move_fail
@horizontal:
    lda move_dy
    jne move_fail
    beq @valid
@vertical:
    lda move_dy
    cmp #1
    beq @valid
    cmp #$ff
    jne move_fail
@valid:
    clc
    lda move_g
    adc #<760
    sta move_info
    lda move_g+1
    adc #>760
    sta move_info+1
    ldy #0
    lda (move_info),y
    jeq move_fail
    cmp #39
    jcs move_fail
    iny
    lda (move_info),y
    jeq move_fail
    cmp #21
    jcs move_fail
    ldy #24
    lda (move_info),y
    jeq move_fail
    cmp #11
    jcs move_fail
    ldy #2
    lda (move_info),y
    clc
    adc move_dx
    sta move_nx
    iny
    lda (move_info),y
    clc
    adc move_dy
    sta move_ny
    jsr move_floor
    jcc move_fail
    jsr move_find
    sty move_box
    cpy #$ff
    beq move_walk
    lda move_nx
    sta move_bx
    clc
    adc move_dx
    sta move_nx
    lda move_ny
    sta move_by
    clc
    adc move_dy
    sta move_ny
    jsr move_floor
    jcc move_fail
    jsr move_find
    cpy #$ff
    jne move_fail
    ldy move_box
    lda move_nx
    sta (move_info),y
    iny
    lda move_ny
    sta (move_info),y
    lda move_bx
    sta move_nx
    lda move_by
    sta move_ny
    ldy #0
    lda #1
    sta (move_pushed),y
    ldy #29
    jsr move_inc
move_walk:
    ldy #2
    lda move_nx
    sta (move_info),y
    iny
    lda move_ny
    sta (move_info),y
    ldy #25
    jsr move_inc
    lda #1
    ldx #0
    rts
move_fail:
    lda #0
    tax
    rts
move_floor:
    ldy #0
    lda move_nx
    cmp (move_info),y
    bcs @no
    iny
    lda move_ny
    cmp (move_info),y
    bcs @no
    asl a
    tax
    lda move_offsets,x
    clc
    adc move_g
    sta move_map
    lda move_offsets+1,x
    adc move_g+1
    sta move_map+1
    ldy move_nx
    lda (move_map),y
    cmp #'#'
    beq @no
    sec
    rts
@no:clc
    rts
move_find:
    ldy #24
    lda (move_info),y
    tax
    ldy #4
@loop:
    lda (move_info),y
    cmp move_nx
    bne @skip
    iny
    lda (move_info),y
    cmp move_ny
    beq @found
    dey
@skip:
    iny
    iny
    dex
    bne @loop
    ldy #$ff
    rts
@found:
    dey
    rts
move_inc:
    ldx #4
@loop:
    lda (move_info),y
    clc
    adc #1
    sta (move_info),y
    bne @done
    iny
    dex
    bne @loop
@done:rts
.ifdef NATIVE_SIM65
.segment "RODATA"
.else
.segment "LOADCONST"
.endif
move_offsets:
.repeat 20,I
 .word I*38
.endrepeat
