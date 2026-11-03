; Visible-frame animation state. No C call; private ISR scratch.
.macpack longbranch
.export _phase_tick,_phase_commit,_phase_reset
.export _live_dock_timer,_live_boxes,_robot_animation,_next_robot_base,_next_robot_push,_next_robot_ticks
.export _visible_robot_base,_visible_robot_push,_phase_generation
.export _next_robot_bank_a,_next_robot_bank_b
.import _robot_bank_a,_robot_bank_b
.import _ambient_active,_video_clock,_robot_frame,_robot_copy,_robot_update
.import _dock_timer,_old_boxes,_gs,_render_board_x,_render_board_y,_dirty_index
.segment "ZEROPAGE"
phase_map:.res 2
phase_dest:.res 2
.segment "BSS"
_live_dock_timer:.res 10
_live_boxes:.res 20
_robot_animation:.res 1
_next_robot_base:.res 1
_next_robot_push:.res 1
_next_robot_ticks:.res 1
_next_robot_bank_a:.res 1
_next_robot_bank_b:.res 1
_visible_robot_base:.res 1
_visible_robot_push:.res 1
_phase_generation:.res 1
phase_valid:.res 1
phase_index:.res 1
phase_row:.res 1
phase_col:.res 1
phase_object:.res 1
.segment "CODE"
_phase_reset:
    lda #0
    sta _robot_animation
    sta phase_valid
    ldx #9
@clear:sta _live_dock_timer,x
    dex
    bpl @clear
    ldx #19
@boxes:lda _old_boxes,x
    sta _live_boxes,x
    dex
    bpl @boxes
    rts
_phase_commit:
    lda #1
    sta phase_valid
    inc _phase_generation
    lda _next_robot_bank_a
    sta _robot_bank_a
    lda _next_robot_bank_b
    sta _robot_bank_b
    lda _next_robot_base
    sta _visible_robot_base
    lda _next_robot_push
    sta _visible_robot_push
    lda _next_robot_ticks      ; initial visible frame plus7 later frames
    sta _robot_animation
    ldx #19
@boxes:lda _old_boxes,x         ; immutable pending action, not mutable gs
    sta _live_boxes,x
    dex
    bpl @boxes
    ldx _dirty_index
    cpx #10
    bcs @robot
    lda _dock_timer,x          ; only the changed crate resets its timer
    sta _live_dock_timer,x
@robot:
    lda _next_robot_ticks
    bne robot_active
    lda _visible_robot_base
    sta _robot_frame
    jmp robot_copy
_phase_tick:
    lda phase_valid
    jeq @done
    lda _ambient_active
    jeq @done
    lda _robot_animation
    beq @idle
    dec _robot_animation
    jsr robot_active
    jmp @docks
@idle:
    lda _visible_robot_base
    cmp _robot_frame
    beq @docks
    sta _robot_frame
    jsr robot_copy
@docks:
    lda #0
    sta phase_index
@one:
    ldx phase_index
    cpx _gs+784
    bcs @done
    lda _live_dock_timer,x
    beq @next
    dec _live_dock_timer,x
    lda _live_dock_timer,x
    cmp #8
    beq @second
    cmp #4
    beq @third
    cmp #1
    bne @next
    lda #4
    bne @draw
@second:lda #16
    bne @draw
@third:lda #20
@draw:
    sta phase_object
    jsr dock_draw
@next:
    inc phase_index
    jmp @one
@done:rts
robot_active:
    lda _video_clock           ; phase evaluated at publication, not preparation
    lsr a
    and #1
    clc
    adc #1
    adc _visible_robot_push
    adc _visible_robot_base
    sta _robot_frame
robot_copy:
    lda #1
    sta _robot_copy
    jmp _robot_update
dock_draw:
    lda phase_index
    asl a
    tax
    lda _live_boxes,x
    asl a
    clc
    adc _render_board_x
    sta phase_col
    lda _live_boxes+1,x
    asl a
    clc
    adc _render_board_y
    sta phase_row
    ldx #0
@quarter:
    txa
    lsr a
    clc
    adc phase_row
    tay
    lda screen_lo,y
    clc
    adc phase_col
    sta phase_dest
    lda screen_hi,y
    adc #0
    sta phase_dest+1
    lda strip,y
    clc
    adc phase_object
    clc
    adc #$e8
    sta phase_map
    lda #$9d
    adc #0
    sta phase_map+1
    txa
    tay
    lda (phase_map),y
    pha
    txa
    and #1
    tay
    pla
    sta (phase_dest),y
    inx
    cpx #4
    bne @quarter
    rts
.segment "RODATA"
screen_lo:
.repeat 24,I
 .byte <($8800+I*40)
.endrepeat
screen_hi:
.repeat 24,I
 .byte >($8800+I*40)
.endrepeat
strip:
.repeat 24,I
 .if I<6
  .byte 0
 .elseif I<10
  .byte 24
 .elseif I<14
  .byte 48
 .elseif I<18
  .byte 72
 .else
  .byte 96
 .endif
.endrepeat
