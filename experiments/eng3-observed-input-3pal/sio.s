.import _loading_begin
.import _hud_cancel
.export _sio_read,_asset_load_begin,_asset_load_end
.import _sector_buffer,_display_active,_background_enabled,_hud_enabled,_robot_frame,_hud_pending
.importzp _input_head,_input_tail
.import _sound_request
.import _infra_enabled
.import _audio_resume
.import _asset_loading
.import _ambient_active,_menu_active,_publish_pending,_publish_count,_robot_copy,_ratio_pending
.segment "LOADER"
_sio_read:
    sta $030A
    stx $030B                ; full unsigned 16-bit sector, no DOS chain
    lda #$31
    sta $0300
    lda #1
    sta $0301
    lda #$52
    sta $0302
    lda #$40
    sta $0303
    lda #<_sector_buffer
    sta $0304
    lda #>_sector_buffer
    sta $0305
    lda #7
    sta $0306
    lda #128
    sta $0308
    lda #0
    sta $0309
    jsr $E459
    lda $0303
    ldx #0
    rts
_asset_load_begin:
    lda _asset_loading
    beq :+
    jmp _loading_begin
:   jsr _hud_cancel
    ; Stop DMA only after the complete old raster, before overwriting overlays.
    lda _display_active
    beq @blank
@wait_blank:
    lda $D40B
    cmp #124
    bcc @wait_blank
@blank:
    lda #1
    sta _asset_loading
    lda #0
    sta _display_active
    sta _ambient_active
    sta _menu_active
    sta _publish_pending
    sta _publish_count
    sta _robot_copy
    sta _ratio_pending
    sta _background_enabled
    sta _infra_enabled
    sta _hud_enabled
    sta $022F
    sta $D400
    sta $D201
    sta $D203
    sta $D205
    sta $D207
    sta _sound_request
    lda #255
    sta _robot_frame
    jmp _loading_begin
_asset_load_end:
    lda #0
    sta $D208
    lda #3
    sta $D20F
    jsr _audio_resume
    lda _input_head
    sta _input_tail
    rts
