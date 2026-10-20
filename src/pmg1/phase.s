; Game overlay. All calls gated by resident code or validated show_play.
.export _phase_reset,_phase_tick,_phase_commit,_robot_animation
.export _next_robot_base,_next_robot_push,_next_robot_ticks
.export _next_robot_bank_a,_next_robot_bank_b,_visible_robot_base,_visible_robot_push
.export _phase_generation,_live_dock_timer,_live_boxes,_robot_update
.export _pmg_next_x,_pmg_next_y,_pmg_visible_x,_pmg_visible_y
.export _pmg_update_end
.import _video_clock,_robot_frame,_robot_copy,_ambient_active
.import _old_boxes,_dock_timer,_dirty_index
.import _robot_frames
.importzp robot_ptr
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
_pmg_next_x:.res 1
_pmg_next_y:.res 1
_pmg_visible_x:.res 1
_pmg_visible_y:.res 1
pmg_old_y:.res 1
phase_valid:.res 1
.segment "GAMECODE"
_phase_reset:
    lda #0
    sta _robot_animation
    sta phase_valid
    sta pmg_old_y
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
    lda _pmg_next_x
    sta _pmg_visible_x
    lda _pmg_next_y
    sta _pmg_visible_y
    lda _next_robot_base
    sta _visible_robot_base
    lda _next_robot_push
    sta _visible_robot_push
    lda _next_robot_ticks
    sta _robot_animation
    jsr robot_frame
    inc _phase_generation       ; visible generation only after both layers
    rts
_phase_tick:
    lda phase_valid
    beq @done
    lda _ambient_active
    beq @done
    lda _robot_animation
    beq @done                  ; fixed recognizable idle, no pulse
    dec _robot_animation
    jsr robot_frame
@done:rts
robot_frame:
    lda _visible_robot_base
    ldx _robot_animation
    beq @chosen
    lda _video_clock
    lsr a
    and #1
    clc
    adc #1
    adc _visible_robot_push
    adc _visible_robot_base
@chosen:
    sta _robot_frame
    lda #1
    sta _robot_copy
_robot_update:
    lda _robot_copy
    bne :+
    rts
:
    lda _robot_frame
    ldx #0
    stx robot_ptr+1
    .repeat 5
        asl a
        rol robot_ptr+1
    .endrepeat
    clc
    adc #<_robot_frames
    sta robot_ptr
    lda robot_ptr+1
    adc #>_robot_frames
    sta robot_ptr+1
    ; Clear previous footprint first, copy both layers, publish HPOS last.
    ; Whole-board blank only, no ANTIC reads of either footprint in this unit.
    ldx pmg_old_y
    lda #0
    .repeat 16,I
        sta $ac00+I,x
        sta $ad00+I,x
    .endrepeat
    ldx _pmg_visible_y
    stx pmg_old_y
    .repeat 16,I
        ldy #I
        lda (robot_ptr),y
        sta $ac00+I,x
        ldy #I+16
        lda (robot_ptr),y
        sta $ad00+I,x
    .endrepeat
    lda _pmg_visible_x
    sta $d000
    sta $d001
    lda #0
    sta _robot_copy
_pmg_update_end:
    rts
