; ABI-compatible undo_pop. Foreground only, no shared ISR scratch.
.macpack longbranch
.export _undo_pop
.import _history,_head,_count,_capacity
.segment "ZEROPAGE"
u_g:.res 2
u_info:.res 2
u_map:.res 2
.segment "BSS"
u_pos:.res 1
u_entry:.res 1
u_dx:.res 1
u_dy:.res 1
u_px:.res 1
u_py:.res 1
u_nx:.res 1
u_ny:.res 1
u_bx:.res 1
u_by:.res 1
.segment "CODE"
_undo_pop:
    sta u_g
    stx u_g+1
    ora u_g+1
    jeq u_fail
    lda _count
    ora _count+1
    jeq u_fail
    lda _head
    sec
    sbc #1
    sta u_pos
    lda _capacity
    sec
    sbc #1
    and u_pos
    sta u_pos
    tax
    lda _history,x
    sta u_entry
    and #3
    tax
    lda dx,x
    sta u_dx
    lda dy,x
    sta u_dy
    lda u_g
    clc
    adc #<760
    sta u_info
    lda u_g+1
    adc #>760
    sta u_info+1
    ldy #2
    lda (u_info),y
    sta u_px
    sec
    sbc u_dx
    sta u_nx
    iny
    lda (u_info),y
    sta u_py
    sec
    sbc u_dy
    sta u_ny
    ldy #0
    lda u_nx
    cmp (u_info),y
    jcs u_fail
    iny
    lda u_ny
    cmp (u_info),y
    jcs u_fail
    ; Map address y*38, matching C's 20x38 layout.
    asl a
    tax
    lda offsets,x
    clc
    adc u_g
    sta u_map
    lda offsets+1,x
    adc u_g+1
    sta u_map+1
    ldy u_nx
    lda (u_map),y
    cmp #'#'
    jeq u_fail
    lda u_entry
    and #4
    beq @player
    lda u_px
    clc
    adc u_dx
    sta u_bx
    lda u_py
    clc
    adc u_dy
    sta u_by
    ldy #24
    lda (u_info),y
    tax
    beq u_fail
    ldy #4
@find:
    lda (u_info),y
    cmp u_bx
    bne @skip
    iny
    lda (u_info),y
    cmp u_by
    beq @box
    dey
@skip:
    iny
    iny
    dex
    bne @find
    beq u_fail
@box:
    lda u_py
    sta (u_info),y
    dey
    lda u_px
    sta (u_info),y
    ldy #29
    jsr decrement
@player:
    ldy #2
    lda u_nx
    sta (u_info),y
    iny
    lda u_ny
    sta (u_info),y
    ldy #25
    jsr decrement
    lda u_pos
    sta _head
    lda _count
    bne :+
    dec _count+1
:
    dec _count
    lda #1
    ldx #0
    rts
u_fail:
    lda #0
    tax
    rts
decrement:
    ldx #4
@byte:
    lda (u_info),y
    sec
    sbc #1
    sta (u_info),y
    cmp #$ff
    bne @done
    iny
    dex
    bne @byte
@done:rts
.segment "RODATA"
dx:.byte 0,0,$ff,1
dy:.byte $ff,1,0,0
offsets:
.repeat 20,I
 .word I*38
.endrepeat
