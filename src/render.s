; Main-thread native text and decimal helpers. Never called from interrupts.
.export _render_cell
.import _scene_cells
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
    lda #88
    jmp @chosen
@boxes:
    ldy #24
    lda (info_ptr),y
    sta box_left
    ldy #4
@box:
    lda (info_ptr),y
    iny
    cmp cx
    bne @skip
    lda (info_ptr),y
    cmp cy
    beq @module
@skip:
    iny
    dec box_left
    bne @box
    lda ground
    cmp #'.'
    beq @dock
    cmp #'#'
    beq @wall
    jmp @composition
@module:
    lda ground
    cmp #'.'
    beq @docked
    lda #84
    jmp @chosen
@docked:
    lda #60
    jmp @chosen
@dock:
    lda #80
    jmp @chosen
@wall:
@composition:
    ldy cy
    lda composition_offsets,y
    clc
    adc cx
    tax
    lda _scene_cells,x
@chosen:
    sta cell_base
    lda cy
    asl a
    clc
    adc _render_board_y
    asl a
    tax
    lda cx
    asl a
    clc
    adc _render_board_x
    adc screen_offsets,x
    sta _render_target
    lda #$88
    adc screen_offsets+1,x
    sta _render_target+1
    lda cell_base
    jsr _render_tile
    inc _render_tile_writes
    bne @done
    inc _render_tile_writes+1
@done: rts
_render_tile:
    pha
    lda _render_target
    sta render_dst
    lda _render_target+1
    sta render_dst+1
    pla
    ldy #0
    sta (render_dst),y
    clc
    adc #1
    iny
    sta (render_dst),y
    adc #1
    ldy #40
    sta (render_dst),y
    adc #1
    iny
    sta (render_dst),y
    rts
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
composition_offsets: .byte 0,20,40,60,80,100,120,140,160,180
