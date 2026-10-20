; Foreground prepares the complete immutable PMG transaction, token last.
; Position uses the same character origin as the playfield renderer.
.segment "GAMECODE"
_display_animate:
    sta animate_flags
    and #1
    beq @ticks
    lda #7
@ticks:
    sta _next_robot_ticks
    lda animate_flags
    and #2
    sta _next_robot_push
    ldx _facing
    lda facing_frames,x
    sta _next_robot_base
    lda _render_board_x
    asl a
    asl a
    clc
    adc #48
    sta _pmg_next_x
    lda _gs+762
    asl a
    asl a
    asl a
    clc
    adc _pmg_next_x
    sta _pmg_next_x
    lda _render_board_y
    asl a
    asl a
    asl a
    clc
    adc #32
    sta _pmg_next_y
    lda _gs+763
    .repeat 4
    asl a
    .endrepeat
    clc
    adc _pmg_next_y
    sta _pmg_next_y
    lda #1
    sta _robot_copy
    sta _publish_pending
    jmp _publish_now
.segment "GAMERODATA"
facing_frames:.byte 0,5,10,15
.import _pmg_next_x,_pmg_next_y
