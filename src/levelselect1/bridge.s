; Resident selector bridge. No overlay instruction runs during SIO/loading.
.export _selector_open,_selector_cursor,_selector_seen,_options_open,_menu_transition
.import _resume,_input_rearm,_game_valid
.import _asset_load_begin,_asset_load_end,_sio_read,_sector_buffer
.import _loaded,_error,_phase,_failed_kind,_prepare,_title,_show_ui
.import _crc,_crc_byte,pusha
.segment "ZEROPAGE"
selector_ptr: .res 2
.segment "PERSIST"
_selector_cursor: .res 1
_selector_seen: .res 1
selector_sector: .res 1
selector_crc: .res 2
_menu_transition: .res 1
.segment "CODE"
_selector_open:
    lda #0
    sta _menu_transition
    lda #6
    ldx #$80
    bne overlay_open
_options_open:
    lda #1
    sta _menu_transition
    lda #7
    ldx #$91
 overlay_open:
    stx selector_sector
    sta _failed_kind
    jsr selector_load
    beq selector_error
    jsr $a000
    pha
    jsr _input_rearm
    pla
    cmp #254
    beq options_resume
    cmp #253
    bne :+
    lda #0
    sta _game_valid
    jmp selector_cancel
:   cmp #60
    bcs selector_cancel
    ; Exact cc65 unsigned-char ABI for prepare(index,0,1).
    jsr pusha
    lda #0
    jsr pusha
    lda #1
    jsr _prepare
    tax                      ; C ABI returns A, not condition flags
    beq selector_error
    jmp overlay_done
options_resume:
    jsr _resume
    tax
    beq selector_error
    jmp overlay_done
selector_cancel:
    jsr _title
overlay_done:
    lda #0
    sta _menu_transition
    rts
selector_error:
    lda #0
    sta _menu_transition
    lda #6
    sta _phase
    jmp _show_ui
selector_load:
    jsr _asset_load_begin
    lda #0
    sta _loaded
    lda #1
    sta _error
    lda selector_sector      ; 640 selector / 657 options
    ldx #2
    jsr _sio_read
    cmp #1
    bne selector_failed
    ldx #7
@header:
    lda _sector_buffer,x
    cmp selector_header,x
    bne selector_bad_header
    dex
    bpl @header
    lda _sector_buffer+8
    sta selector_crc
    lda _sector_buffer+9
    sta selector_crc+1
    lda #0
    sta selector_ptr
    lda #$a0
    sta selector_ptr+1
    inc selector_sector
    lda #$ff
    sta _crc
    sta _crc+1
    jmp selector_read
selector_bad_header:
    lda #3
    bne selector_set_error
selector_bad_crc:
    lda #4
selector_set_error:
    sta _error
selector_failed:
    jsr _asset_load_end
    lda #0
    rts
.segment "EXTRA"
selector_header:
    .byte "NSLS",1,$a0,0,8
.segment "LOADER"
selector_read:
    lda selector_sector
    ldx #2
    jsr _sio_read
    cmp #1
    beq :+
    jmp selector_failed
:   ldy #0
@copy:
    lda _sector_buffer,y
    sta (selector_ptr),y
    jsr _crc_byte             ; preserves Y; no ISR owns the loader CRC
    iny
    bpl @copy
    lda selector_ptr
    eor #$80
    sta selector_ptr
    bne :+
    inc selector_ptr+1
:   inc selector_sector
    lda selector_ptr+1
    cmp #$a8
    bne selector_read
    jmp selector_checked

selector_checked:
    ldx #1
@check:
    lda _crc,x
    cmp selector_crc,x
    bne @bad
    dex
    bpl @check
    lda #6
    sta _loaded
    lda #0
    sta _error
    jsr _asset_load_end
    lda #1
    rts
@bad:
    jmp selector_bad_crc
