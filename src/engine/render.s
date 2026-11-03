; Main-thread native text and decimal helpers. Never called from interrupts.
.export _render_cell
.import _publish_count,_publish_addr_lo,_publish_addr_hi,_publish_code,_publish_first_row
.import _render_game,_render_board_x,_render_board_y,_render_tile_writes
.export _render_tile
.export _render_mono_text,_render_text,_render_target,_render_limit,_render_number,_render_digits
.importzp sreg
.macpack longbranch
.segment "ZEROPAGE"
render_src: .res 2
render_dst: .res 2
map_ptr: .res 2
info_ptr: .res 2
.segment "BSS"
_render_target: .res 2
_render_limit: .res 1
_render_digits: .res 11
value: .res 4
digit: .res 1
started: .res 1
length: .res 1
cx: .res 1
cy: .res 1
ground: .res 1
cell_base: .res 1
box_left: .res 1
.segment "CODE"
_render_cell:
    sta cx
    stx cy
    txa
    asl a
    tax
    clc
    lda _render_game
    adc map_offsets,x
    sta map_ptr
    lda _render_game+1
    adc map_offsets+1,x
    sta map_ptr+1
    ldy cx
    lda (map_ptr),y
    sta ground
    clc
    lda _render_game
    adc #<760
    sta info_ptr
    lda _render_game+1
    adc #>760
    sta info_ptr+1
    ldy #2
    lda (info_ptr),y
    cmp cx
    bne @boxes
    iny
    lda (info_ptr),y
    cmp cy
    bne @boxes
    lda #$fe
    jmp @chosen
@boxes:
    ldy #24
    lda (info_ptr),y
    sta box_left
    ldy #4
    ldx #0
@box:
    lda (info_ptr),y
    iny
    cmp cx
    bne @skip
    lda (info_ptr),y
    cmp cy
    beq @module
@skip:
    inx
    iny
    dec box_left
    bne @box
    lda ground
    cmp #'.'
    beq @dock
    lda #$ff
    jmp @chosen
@module:
    lda #0
    ldy ground
    cpy #'.'
    bne @chosen
    lda _dock_timer,x
    beq @docked
    cmp #2
    bcc @docked
    cmp #5
    bcc @reaction2
    cmp #9
    bcc @reaction1
    lda #12
    jmp @chosen
@reaction1:lda #16
    jmp @chosen
@reaction2:lda #20
    jmp @chosen
@docked:lda #4
    jmp @chosen
@dock:
    lda #8
@chosen:
    sta cell_base
    lda cy
    asl a
    clc
    adc _render_board_y
    sta char_row
    ldx _publish_count
    beq :+
    cmp _publish_first_row
    bcs :++
:
    sta _publish_first_row
:
    asl a
    tax
    lda cx
    asl a
    clc
    adc _render_board_x
    adc screen_offsets,x
    sta render_dst
    lda #$88
    adc screen_offsets+1,x
    sta render_dst+1
    ; Composition pointer is y*80+x*4; each quarter is independent.
    ldy cy
    lda composition_offsets_lo,y
    clc
    adc cx
    sta render_src
    lda composition_offsets_hi,y
    adc #0
    sta render_src+1
    .repeat 2
        asl render_src
        rol render_src+1
    .endrepeat
    clc
    lda render_src+1
    adc #$14
    sta render_src+1
    ; A cell always has four quarters. Prepare the four pending entries
    ; without repeatedly publishing/counting the private write cursor.
    ldx _publish_count
    cpx #29
    jcs render_cell_overflow
    .repeat 4,Q
        .scope
        ldy char_row
        .if Q>=2
            iny
        .endif
        lda strip_offsets,y
        sta strip_offset
        lda cell_base
        cmp #$ff
        bne object
        ldy #Q
        lda (render_src),y
        jmp code
object:
        cmp #$fe
        bne static
        lda #124+Q
        jmp code
static:
        clc
        adc strip_offset
        adc #Q
        tay
        lda $9de8,y
code:
        sta _publish_code,x
        lda render_dst
        clc
        adc #((Q/2)*40+Q .mod 2)
        sta _publish_addr_lo,x
        lda render_dst+1
        adc #0
        sta _publish_addr_hi,x
        inx
        .endscope
    .endrepeat
    stx _publish_count
    inc _render_tile_writes
    bne @done
    inc _render_tile_writes+1
@done:rts
render_cell_overflow:
    ; Fail closed: main checks a nonzero publication error at next loop.
    inc _publication_overflow
    rts
_render_tile: rts
.import _publication_overflow,_dock_timer
.segment "BSS"
char_row:.res 1
quarter:.res 1
strip_offset:.res 1
.segment "RODATA"
quarter_offsets:.byte 0,1,40,41
strip_offsets:
.repeat 24,I
 .if I<2
  .byte 0
 .elseif I>=18
  .byte 96
 .else
  .byte ((I-2)/4)*24
 .endif
.endrepeat
.segment "CODE"
; fastcall const char* A/X; bounded destination supplied by C.
_render_text:
    sta render_src
    stx render_src+1
    lda _render_target
    sta render_dst
    lda _render_target+1
    sta render_dst+1
    ldy #0
@char:
    cpy _render_limit
    beq @done
    lda (render_src),y
    beq @done
    and #$7f
    tax
    lda glyphs,x
    ora #$80
    sta (render_dst),y
    iny
    bne @char
@done: rts
_render_mono_text:
    sta render_src
    stx render_src+1
    lda _render_target
    sta render_dst
    lda _render_target+1
    sta render_dst+1
    ldy #0
@char:
    cpy _render_limit
    beq @done
    lda (render_src),y
    beq @done
    and #127
    tax
    lda glyphs,x
    sta (render_dst),y         ; ANTIC 2: bit 7 is inverse, never a color bit
    iny
    bne @char
@done: rts
; fastcall uint32: A/X low word, sreg high word. Fully bounded uint32 conversion.
_render_number:
    sta value
    stx value+1
    lda sreg
    sta value+2
    lda sreg+1
    sta value+3
    lda #0
    sta started
    sta length
    ldx #0
@power:
    lda #0
    sta digit
@compare:
    lda value+3
    cmp powers+3,x
    bcc @emit
    bne @subtract
    lda value+2
    cmp powers+2,x
    bcc @emit
    bne @subtract
    lda value+1
    cmp powers+1,x
    bcc @emit
    bne @subtract
    lda value
    cmp powers,x
    bcc @emit
@subtract:
    sec
    lda value
    sbc powers,x
    sta value
    lda value+1
    sbc powers+1,x
    sta value+1
    lda value+2
    sbc powers+2,x
    sta value+2
    lda value+3
    sbc powers+3,x
    sta value+3
    inc digit
    jmp @compare
@emit:
    lda digit
    bne @write
    lda started
    bne @write
    cpx #36
    bne @next
@write:
    lda #1
    sta started
    lda digit
    clc
    adc #'0'
    ldy length
    sta _render_digits,y
    inc length
@next:
    inx
    inx
    inx
    inx
    cpx #40
    bne @power
    ldy length
    lda #0
    sta _render_digits,y
    rts
.segment "RODATA"
powers: .dword 1000000000,100000000,10000000,1000000,100000,10000,1000,100,10,1
glyphs:
.repeat 128,I
 .if I >= 'A' .and I <= 'Z'
  .byte I-'A'+1
 .elseif I >= '0' .and I <= '9'
  .byte I-'0'+27
 .elseif I = ':'
  .byte 37
 .elseif I = '/'
  .byte 38
 .elseif I = '-'
  .byte 39
 .elseif I = '+'
  .byte 40
 .elseif I = '.'
  .byte 41
 .elseif I = '>'
  .byte 42
 .elseif I = '='
  .byte 43
 .else
  .byte 0
 .endif
.endrepeat

map_offsets:
.repeat 20,I
 .word I*38
.endrepeat
screen_offsets:
.repeat 24,I
 .word I*40
.endrepeat
hazards:
.repeat 40,I
 .if (I .mod 5) = 0
  .byte 12
 .else
  .byte 0
 .endif
.endrepeat
 ; Monochrome ANTIC 2 strip: 320x8, forty glyph-addressed bytes per scanline.
; Immutable 6x7 font, pitch >=7; no column deletion or two-bit color data.
; hud_x is 16-bit because a complete counter layout reaches pixel 314.
.import _mono_font
.export _render_hud_text,_hud_x,_hud_pitch
.segment "BSS"
_hud_x: .res 2
_hud_pitch: .res 1
hud_index: .res 1
hud_shift: .res 1
hud_row: .res 1
hud_low: .res 1
hud_high: .res 1
.segment "CODE"
_render_hud_text:
    sta render_src
    stx render_src+1
    lda #0
    sta hud_index
@next_char:
    ldy hud_index
    lda (render_src),y
    jeq @done
    ; A complete six-column glyph must fit; unsupported positions never wrap.
    lda _hud_x+1
    cmp #1
    jcc @fits
    jne @done
    lda _hud_x
    cmp #59                  ; last accepted origin =314
    jcs @done
@fits:
    lda _hud_x
    and #7
    sta hud_shift
    lda _hud_x
    sta render_dst
    lda _hud_x+1
    sta render_dst+1
    .repeat 3
        lsr render_dst+1
        ror render_dst
    .endrepeat
    .repeat 3
        asl render_dst
        rol render_dst+1
    .endrepeat
    clc
    lda render_dst
    adc _render_target
    sta render_dst
    lda render_dst+1
    adc _render_target+1
    sta render_dst+1
    lda (render_src),y
    sec
    sbc #'0'
    cmp #10
    jcs @normal_font
    pha
    lsr a
    sta info_ptr+1
    pla
    and #1
    .repeat 7
        asl a
    .endrepeat
    sta info_ptr
    lda hud_shift
    .repeat 4
        asl a
    .endrepeat
    clc
    adc info_ptr
    adc #<hud_digits
    sta info_ptr
    lda info_ptr+1
    adc #>hud_digits
    sta info_ptr+1
    .repeat 8,I
    ldy #I
    lda (info_ptr),y
    ora (render_dst),y
    sta (render_dst),y
    ldy #I+8
    lda (info_ptr),y
    ora (render_dst),y
    sta (render_dst),y
    .endrepeat
    jmp @advance
@normal_font:
    lda (render_src),y
    and #127
    tax
    lda glyphs,x
    sta info_ptr
    lda #0
    sta info_ptr+1
    .repeat 3
        asl info_ptr
        rol info_ptr+1
    .endrepeat
    clc
    lda info_ptr
    adc #<_mono_font
    sta info_ptr
    lda info_ptr+1
    adc #>_mono_font
    sta info_ptr+1
    lda #7
    sta hud_row
@row:
    ldy hud_row
    lda (info_ptr),y
    sta hud_low
    lda #0
    sta hud_high
    ldx hud_shift
    beq @store
@shift:
    lsr hud_low
    ror hud_high
    dex
    bne @shift
@store:
    lda hud_low
    ora (render_dst),y
    sta (render_dst),y
    lda _hud_x+1
    beq @tail
    lda _hud_x
    cmp #56                  ; no forty-first cell at origin >=312
    bcs @no_tail
@tail:
    tya
    clc
    adc #8
    tay
    lda hud_high
    ora (render_dst),y
    sta (render_dst),y
@no_tail:
    dec hud_row
    bpl @row
@advance:
    clc
    lda _hud_x
    adc _hud_pitch
    sta _hud_x
    bcc :+
    inc _hud_x+1
:
    inc hud_index
    jmp @next_char
@done:rts
; Occupied docks, shared validated GameState ABI. At most ten boxes.
; Avoid scanning the map or expensive C indexing on every walking step.
.export _render_docks
.segment "CODE"
_render_docks:
    sta render_src
    stx render_src+1
    clc
    adc #<760
    sta info_ptr
    txa
    adc #>760
    sta info_ptr+1
    ldy #24
    lda (info_ptr),y
    sta box_left
    lda #0
    sta digit
    lda #4
    sta length
    lda box_left
    beq @done
@box:
    ldy length
    lda (info_ptr),y
    sta cx
    iny
    lda (info_ptr),y
    asl a
    tax
    clc
    lda render_src
    adc map_offsets,x
    sta map_ptr
    lda render_src+1
    adc map_offsets+1,x
    sta map_ptr+1
    ldy cx
    lda (map_ptr),y
    cmp #'.'
    bne @next
    inc digit
@next:
    inc length
    inc length
    dec box_left
    bne @box
@done:
    lda digit
    ldx #0
    rts

.segment "RODATA"
composition_offsets_lo: .byte 0,20,40,60,80,100,120,140,160,180
composition_offsets_hi: .res 10,0

.import hud_digits

; Only occupied/total changes. This fixed five-character native preparation
; replaces repeated C conversions/setups; stage is published as one VBI unit.
.export _render_ratio
.segment "BSS"
ratio_text:.res 6
.segment "CODE"
_render_ratio:
    pha
    lda #0
    ldy #39
@clear:sta $9570,y
    dey
    bpl @clear
    pla
    ldx #0
    jsr @pair
    lda #'/'
    sta ratio_text+2
    lda #0
    sta ratio_text+5
    lda _gs+784
    ldx #3
    jsr @pair
    lda #<$9458
    sta _render_target
    lda #>$9458
    sta _render_target+1
    lda #<281
    sta _hud_x
    lda #>281
    sta _hud_x+1
    lda #7
    sta _hud_pitch
    lda #<ratio_text
    ldx #>ratio_text
    jmp _render_hud_text
@pair:
    ldy #'0'
    cmp #10
    bcc :+
    sec
    sbc #10
    iny
:
    pha
    tya
    sta ratio_text,x
    pla
    clc
    adc #'0'
    sta ratio_text+1,x
    rts

; Same GameState ABI and puzzle logic, native dirty publication only.
.import _gs,_old_player,_old_boxes,_publish_pending
.export _display_changed
.segment "BSS"
dirty_delivery:.res 1
.export _dirty_index
_dirty_index:
dirty_index:.res 1
.segment "CODE"
_display_changed:
    sta dirty_delivery
    ; No screen-code writes means this pending item is cosmetic glyph-only.
    ; A successful game action always changes old/new player codes (count>0).
    ; Give the core action priority without erasing an accepted prior move.
    lda _publish_count
    bne @wait
    lda #0
    sta _publish_pending
    sta _robot_copy
@wait:lda _publish_pending
    bne @wait
    ldx #9
@timers:lda _live_dock_timer,x
    sta _dock_timer,x
    dex
    bpl @timers
    lda #0
    sta dirty_index
; A core action changes at most one crate. Find it and set its timer BEFORE
; rendering player cells, so undo onto an adjacent dock cannot retain a phase.
@find:
    lda dirty_index
    asl a
    tax
    lda _gs+764,x
    cmp _old_boxes,x
    bne @timer
    lda _gs+765,x
    cmp _old_boxes+1,x
    bne @timer
    inc dirty_index
    lda dirty_index
    cmp _gs+784
    bcc @find
    lda #$ff
    sta dirty_index
    jmp @player
@timer:
    ldy dirty_index
    lda #0
    sta _dock_timer,y
    lda dirty_delivery
    beq @player
    lda _gs+765,x
    asl a
    tay
    clc
    lda #<_gs
    adc map_offsets,y
    sta map_ptr
    lda #>_gs
    adc map_offsets+1,y
    sta map_ptr+1
    lda _gs+764,x
    tay
    lda (map_ptr),y
    cmp #'.'
    bne @player
    ldy dirty_index
    lda #12
    sta _dock_timer,y
@player:
    lda _gs+762
    cmp _old_player
    bne @draw_player
    lda _gs+763
    cmp _old_player+1
    beq @boxes
@draw_player:
    lda _old_player
    ldx _old_player+1
    jsr _render_cell
    lda _gs+762
    ldx _gs+763
    jsr _render_cell
@boxes:
    lda dirty_index
    cmp #$ff
    beq @done
    asl a
    tay
    lda _old_boxes,y
    cmp _gs+762
    bne @old
    lda _old_boxes+1,y
    cmp _gs+763
    beq @new
@old:
    lda _old_boxes+1,y
    tax
    lda _old_boxes,y
    jsr _render_cell
@new:
    lda dirty_index
    asl a
    tay
    lda _gs+764,y
    cmp _old_player
    bne @draw_new
    lda _gs+765,y
    cmp _old_player+1
    beq @snapshot
@draw_new:
    lda _gs+765,y
    tax
    lda _gs+764,y
    jsr _render_cell
@snapshot:
    lda dirty_index
    asl a
    tax
    lda _gs+764,x
    sta _old_boxes,x
    lda _gs+765,x
    sta _old_boxes+1,x
@done:
    lda _gs+762
    sta _old_player
    lda _gs+763
    sta _old_player+1
    rts

.importzp _input_clock
.export _display_animate
.import _facing,_video_clock,_robot_frame,_robot_bank_a,_robot_bank_b,_robot_copy,_publish_now
.import _live_dock_timer,_next_robot_base,_next_robot_push,_next_robot_ticks,_next_robot_bank_a,_next_robot_bank_b
.segment "BSS"
animate_flags:.res 1
animate_mode:.res 1
.segment "CODE"
_display_animate:
    sta animate_flags
    and #1
    beq @still
    lda #7
    bne @ticks
@still:lda #0
@ticks:sta _next_robot_ticks
    lda animate_flags
    and #2
    sta _next_robot_push
    lda #0
    sta animate_mode
    lda _gs+763
    asl a
    tay
    clc
    lda #<_gs
    adc map_offsets,y
    sta map_ptr
    lda #>_gs
    adc map_offsets+1,y
    sta map_ptr+1
    ldy _gs+762
    lda (map_ptr),y
    cmp #'.'
    bne @frame
    lda #20
    sta animate_mode
@frame:
    ldy _facing
    lda facing_frames,y
    clc
    adc animate_mode
    sta _next_robot_base
    lda _gs+763
    asl a
    clc
    adc _render_board_y
    tax
    lda robot_bank_rows,x
    sta _next_robot_bank_a
    inx
    lda robot_bank_rows,x
    cmp _next_robot_bank_a
    bne :+
    lda #$ff
:
    sta _next_robot_bank_b
    lda #1
    sta _robot_copy
    sta _publish_pending
    jmp _publish_now
.segment "RODATA"
facing_frames:.byte 0,5,10,15
robot_bank_rows:
.repeat 24,I
 .if I<6
  .byte $8c
 .elseif I<10
  .byte $a0
 .elseif I<14
  .byte $a4
 .elseif I<18
  .byte $a8
 .else
  .byte $ac
 .endif
.endrepeat

; Bounded decimal cache update: each accepted core move changes counters by
; +/-1. Foreground caches are ten padded ASCII digits; zero/max wrap is
; handled by the request layer. No cache or scratch is shared with NMI.
.export _hud_adjust
.import _hud_move_digits,_hud_push_digits,_hud_undo
.segment "CODE"
_hud_adjust:
    sta render_src
    stx render_src+1
    ldy #9
    lda _hud_undo
    bne @down
@up:
    lda (render_src),y
    cmp #'9'
    bne @up_digit
    lda #'0'
    sta (render_src),y
    dey
    bpl @up
    rts
@up_digit:
    clc
    adc #1
    sta (render_src),y
    rts
@down:
    lda (render_src),y
    cmp #'0'
    bne @down_digit
    lda #'9'
    sta (render_src),y
    dey
    bpl @down
    rts
@down_digit:
    sec
    sbc #1
    sta (render_src),y
    rts


; Cooperative native worker. Durable progress is a 25-byte description of
; the actual private staging image, independent of the latest digit caches.
; New requests repair only changed glyphs; completed unchanged work survives.
; Yield between glyphs when the next input sample wakes MAIN. Scratch
; pointers are reconstructed for every glyph and never retained across calls.
.export _hud_work,_hud_stage_chars,_hud_cursor
.import _hud_dirty,_hud_pending,_hud_epoch,_hud_ready_epoch,_hud_budget_clock
.import _hud_state_moves,_hud_state_pushes,_hud_state_docks,_hud_live_valid,hud_live_moves,hud_live_pushes,hud_live_docks
.segment "BSS"
_hud_stage_chars:.res 25
_hud_cursor:.res 1
hud_visits:.res 1
hud_wanted:.res 1
hud_first_move:.res 1
hud_first_push:.res 1
hud_mask_low:.res 1
hud_mask_high:.res 1
.segment "CODE"
_hud_work:
    lda _hud_dirty
    jeq @done
    lda _hud_pending
    jne @done
    ; A return (undo) to the complete currently visible payload needs no
    ; bitmap copy. Private partial staging and its true glyph description
    ; remain intact for the next changed state. ISR will select mask=0.
    lda _hud_live_valid
    beq @prepare
.repeat 4,I
    lda _hud_state_moves+I
    cmp hud_live_moves+I
    bne @prepare
    lda _hud_state_pushes+I
    cmp hud_live_pushes+I
    bne @prepare
.endrepeat
    lda _hud_state_docks
    cmp hud_live_docks
    jne @prepare
    jmp @publish_ready
@prepare:
    lda #0
    sta hud_visits
    ldy #0
@leading_move:
    lda _hud_move_digits,y
    cmp #'0'
    bne @move_ready
    cpy #8
    beq @move_ready
    iny
    bne @leading_move
@move_ready:
    sty hud_first_move
    ldy #0
@leading_push:
    lda _hud_push_digits,y
    cmp #'0'
    bne @push_ready
    cpy #8
    beq @push_ready
    iny
    bne @leading_push
@push_ready:
    sty hud_first_push
@next:
    lda _input_clock
    cmp _hud_budget_clock
    jne @done
    ldx _hud_cursor
    cpx #10
    bcs @push
    txa
    clc
    adc hud_first_move
    tay
    cpy #10
    bcs @blank
    lda _hud_move_digits,y
    jmp @wanted
@push:
    cpx #20
    bcs @ratio
    txa
    sec
    sbc #10
    clc
    adc hud_first_push
    tay
    cpy #10
    bcs @blank
    lda _hud_push_digits,y
    jmp @wanted
@ratio:
    cpx #22
    beq @slash
    cpx #23
    bcs @total
    lda _hud_state_docks
    jmp @pair
@total:
    lda _gs+784
@pair:
    cpx #20
    beq @tens
    cpx #23
    beq @tens
    cmp #10
    bcc @units
    sec
    sbc #10
@units:
    clc
    adc #'0'
    jmp @wanted
@tens:
    cmp #10
    lda #'0'
    adc #0
    jmp @wanted
@slash:
    lda #'/'
    jmp @wanted
@blank:
    lda #0
@wanted:
    sta hud_wanted
    cmp _hud_stage_chars,x
    beq @advance
    jsr hud_paint
    ldx _hud_cursor
    lda hud_wanted
    sta _hud_stage_chars,x
@advance:
    inc _hud_cursor
    lda _hud_cursor
    cmp #25
    bcc :+
    lda #0
    sta _hud_cursor
:
    inc hud_visits
    lda hud_visits
    cmp #25
    jne @next
    ; One complete scan with stable foreground caches proves all fields match
    ; the same current epoch. Publish token first, ready byte last for NMI.
@publish_ready:
    lda _hud_epoch
    sta _hud_ready_epoch
    lda _hud_epoch+1
    sta _hud_ready_epoch+1
    lda #0
    sta _hud_dirty
    lda #1
    sta _hud_pending
@done:rts
hud_paint:
    ldx _hud_cursor
    lda hud_positions_lo,x
    sta render_dst
    lda hud_positions_hi,x
    sta render_dst+1
    lda hud_masks_low,x
    sta hud_mask_low
    lda hud_masks_high,x
    sta hud_mask_high
    lda hud_wanted
    beq @zero
    cmp #'/'
    beq @slash
    sec
    sbc #'0'
    clc
    adc hud_shifts,x
    tax
    lda hud_lookup_lo,x
    sta info_ptr
    lda hud_lookup_hi,x
    sta info_ptr+1
    jmp @draw
@slash:
    lda hud_slash_lo,x
    sta info_ptr
    lda hud_slash_hi,x
    sta info_ptr+1
    jmp @draw
@zero:
    lda #<hud_zero
    sta info_ptr
    lda #>hud_zero
    sta info_ptr+1
@draw:
    .repeat 8,R
        ldy #R
        lda (render_dst),y
        and hud_mask_low
        ora (info_ptr),y
        sta (render_dst),y
    .endrepeat
    clc
    lda render_dst
    adc #8
    sta render_dst
    bcc :+
    inc render_dst+1
:
    .repeat 8,R
        ldy #R
        lda (render_dst),y
        and hud_mask_high
        ldy #R+8
        ora (info_ptr),y
        ldy #R
        sta (render_dst),y
    .endrepeat
    rts
.segment "RODATA"
hud_zero:.res 16,0
; Slash has the same six-column footprint as the number glyphs.
hud_slash:
 .byte 4,12,24,48,96,192,128,0,0,0,0,0,0,0,0,0
 .byte 2,6,12,24,48,96,64,0,0,0,0,0,0,0,0,0
 .byte 1,3,6,12,24,48,32,0,0,0,0,0,0,0,0,0
 .byte 0,1,3,6,12,24,16,0,128,128,0,0,0,0,0,0
 .byte 0,0,1,3,6,12,8,0,64,192,128,0,0,0,0,0
 .byte 0,0,0,1,3,6,4,0,32,96,192,128,0,0,0,0
 .byte 0,0,0,0,1,3,2,0,16,48,96,192,128,0,0,0
 .byte 0,0,0,0,0,1,1,0,8,24,48,96,192,128,0,0
hud_lookup_lo:
.repeat 8,S
 .repeat 10,D
  .byte <(hud_digits+D*128+S*16)
 .endrepeat
.endrepeat
hud_lookup_hi:
.repeat 8,S
 .repeat 10,D
  .byte >(hud_digits+D*128+S*16)
 .endrepeat
.endrepeat
hud_positions_lo:.byte 48,56,56,64,72,80,88,96,104,112,192,192,200,208,216,224,232,240,248,248,112,120,120,128,136
hud_positions_hi:.byte 148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,149,149,149,149,149
hud_masks_low:.byte 129,3,254,252,248,240,224,192,129,3,3,254,252,248,240,224,192,129,3,254,129,3,254,252,248
hud_masks_high:.byte 255,255,7,15,31,63,127,255,255,255,255,7,15,31,63,127,255,255,255,7,255,255,7,15,31
hud_shifts:.byte 10,0,70,60,50,40,30,20,10,0,0,70,60,50,40,30,20,10,0,70,10,0,70,60,50
hud_slash_lo:
 .byte <(hud_slash+1*16)
 .byte <(hud_slash+0*16)
 .byte <(hud_slash+7*16)
 .byte <(hud_slash+6*16)
 .byte <(hud_slash+5*16)
 .byte <(hud_slash+4*16)
 .byte <(hud_slash+3*16)
 .byte <(hud_slash+2*16)
 .byte <(hud_slash+1*16)
 .byte <(hud_slash+0*16)
 .byte <(hud_slash+0*16)
 .byte <(hud_slash+7*16)
 .byte <(hud_slash+6*16)
 .byte <(hud_slash+5*16)
 .byte <(hud_slash+4*16)
 .byte <(hud_slash+3*16)
 .byte <(hud_slash+2*16)
 .byte <(hud_slash+1*16)
 .byte <(hud_slash+0*16)
 .byte <(hud_slash+7*16)
 .byte <(hud_slash+1*16)
 .byte <(hud_slash+0*16)
 .byte <(hud_slash+7*16)
 .byte <(hud_slash+6*16)
 .byte <(hud_slash+5*16)
hud_slash_hi:
 .byte >(hud_slash+1*16)
 .byte >(hud_slash+0*16)
 .byte >(hud_slash+7*16)
 .byte >(hud_slash+6*16)
 .byte >(hud_slash+5*16)
 .byte >(hud_slash+4*16)
 .byte >(hud_slash+3*16)
 .byte >(hud_slash+2*16)
 .byte >(hud_slash+1*16)
 .byte >(hud_slash+0*16)
 .byte >(hud_slash+0*16)
 .byte >(hud_slash+7*16)
 .byte >(hud_slash+6*16)
 .byte >(hud_slash+5*16)
 .byte >(hud_slash+4*16)
 .byte >(hud_slash+3*16)
 .byte >(hud_slash+2*16)
 .byte >(hud_slash+1*16)
 .byte >(hud_slash+0*16)
 .byte >(hud_slash+7*16)
 .byte >(hud_slash+1*16)
 .byte >(hud_slash+0*16)
 .byte >(hud_slash+7*16)
 .byte >(hud_slash+6*16)
 .byte >(hud_slash+5*16)
