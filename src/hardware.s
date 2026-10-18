; Native PAL deferred-VBI audio + device sample queue. No C/cc65 calls in ISR.
.export _native_vbi,_vbi_end,_background_update,_background_end,_native_dli,_dli_end
.export _display_font,_display_pf1,_display_pf2
.export _hud_pending,_dli_font,_dli_pf1,_dli_pf2
.export _background_enabled,_background_mask,_hud_enabled
.export _display_active
.export _robot_dirty
.export _robot_frame
.export _asset_loading
.import _robot_frames
.import _scene_data
.export _infra_enabled,_infra_frame,_infra_dirty
.export _audio_resume
.export _frame_logic,_frame_audio,_frame_render
.export _hardware_init,_frame_begin,_frame_end,_video_clock
.export _music_enabled,_sfx_enabled,_sound_track,_sound_request
.export _input_head,_input_tail,_input_overflows
.export _queued_stick,_queued_trigger,_queued_console
.segment "ZEROPAGE"
music_ptr: .res 2
robot_ptr: .res 2
.segment "BSS"
_asset_loading: .res 1
_infra_enabled: .res 1
_infra_frame: .res 1
_infra_dirty: .res 1
last_infra: .res 1
_background_enabled: .res 1
_background_mask: .res 1
_hud_enabled: .res 1
_hud_pending: .res 1
_display_font: .res 1
_display_pf1: .res 1
_display_pf2: .res 1
dli_row: .res 1
_dli_font: .res 6
_dli_pf1: .res 6
_dli_pf2: .res 6
background_tick: .res 1
background_phase: .res 1
_display_active: .res 1
_robot_frame: .res 1
_robot_dirty: .res 1
last_robot: .res 1
; NMOS6502 JMP(indirect) wraps at xxFF; enforce a safe resident vector.
.align 2
old_vbi: .res 2
.assert <old_vbi <> $FF, lderror, "VBI vector crosses NMOS6502 page boundary"
_video_clock: .res 1
_music_enabled: .res 1
_sfx_enabled: .res 1
_sound_track: .res 1
_sound_request: .res 1
_input_head: .res 1
_input_tail: .res 1
_input_overflows: .res 1
_queued_stick: .res 256
_queued_trigger: .res 256
_queued_console: .res 256
last_track: .res 1
music_row: .res 1
music_tick: .res 1
bass_note: .res 1
lead_note: .res 1
drum_type: .res 1
fx_type: .res 1
fx_time: .res 1
.segment "CODE"
_frame_logic: rts
_frame_audio: rts
_frame_render: rts
_frame_begin: rts
_frame_end: rts
_audio_resume:
    ; Clear serial-channel/SFX residue and explicitly restore the paused
    ; notes before unmuting; percussion renews its divider each VBI.
    lda #0
    sta $D201
    sta $D203
    sta $D205
    sta $D207
    sta fx_type
    sta fx_time
    lda bass_note
    sta $D200
    lda lead_note
    sta $D202
    rts
_hardware_init:
    lda $0224
    sta old_vbi
    lda $0225
    sta old_vbi+1
    lda #0
    sta _asset_loading
    sta _infra_enabled
    sta _infra_frame
    sta _infra_dirty
    sta _background_enabled
    sta _hud_enabled
    sta _hud_pending
    sta _robot_dirty
    sta background_tick
    sta background_phase
    sta _video_clock
    sta _input_head
    sta _input_tail
    sta _input_overflows
    sta _sound_request
    sta fx_type
    sta fx_time
    sta music_row
    sta music_tick
    lda #2
    sta _sound_track
    lda #$ff
    sta last_robot
    sta last_track
    lda #5
    sta _robot_frame
    lda #1
    sta _music_enabled
    sta _sfx_enabled
    lda #0
    sta $D208                 ; AUDCTL: four independent 64-kHz channels
    sta $D201
    sta $D203
    sta $D205
    sta $D207
    lda #3
    sta $D20F                 ; keyboard scan remains active
    lda #<native_dli
    sta $0200
    lda #>native_dli
    sta $0201
    lda #$C0
    sta $D40E
    ldy #<native_vbi
    ldx #>native_vbi
    lda #7
    jsr $E45C                 ; SETVBV deferred OS vector, atomic OS routine
    rts
_native_vbi = native_vbi
native_vbi:
    pha
    txa
    pha
    tya
    pha
    inc _video_clock
    lda _asset_loading
    beq @normal
    lda #0
    sta $022F
    sta $D400
    jmp _vbi_end
@normal:
    ; Queue every PAL sample, producer publishes head last. Full is measured.
    lda _input_head
    clc
    adc #1
    cmp _input_tail
    beq @full
    tax
    ldy _input_head
    lda $0278
    sta _queued_stick,y
    lda $0284
    sta _queued_trigger,y
    lda $D01F
    and #7
    sta _queued_console,y
    stx _input_head
    jmp @audio
@full:
    inc _input_overflows
@audio:
    lda _display_active
    beq @display_off
    lda #$22
    bne @display_set
@display_off:
    lda #0
@display_set:
    sta $022F
    sta $D400
    lda #0
    sta dli_row
    lda _display_font
    sta $D409
    lda _display_pf1
    sta $D017
    lda _display_pf2
    sta $D018
    lda _hud_pending
    beq @no_hud
    ldx #0
@hud_copy:
    lda $9400,x
    sta $9140,x
    lda $9480,x
    sta $91C0,x
    inx
    bpl @hud_copy
    ldx #63
@hud_tail:
    lda $9500,x
    sta $9240,x
    dex
    bpl @hud_tail
    lda #0
    sta _hud_pending
@no_hud:
    jsr background_update
    jsr robot_update
    jsr infrastructure_update
    jsr music_update
    jsr effects_update
_vbi_end:
    pla
    tay
    pla
    tax
    pla
    jmp (old_vbi)              ; continue OS deferred chain/XITVBV
_native_dli = native_dli
native_dli:
    pha
    txa
    pha
    ldx dli_row
    ; Last scanline of each marked text/graphics band. Complete all three
    ; changes before the next line's character DMA and playfield rendering.
    sta $D40A
    lda _dli_font,x
    sta $D409
    lda _dli_pf1,x
    sta $D017
    lda _dli_pf2,x
    sta $D018
    inc dli_row
_dli_end:
    pla
    tax
    pla
    rti
; Main publishes the mask before enabling. Seven writes
; at most, every eight PAL ticks; no board/charset indices are modified.
_background_update = background_update
background_update:
    lda _background_enabled
    beq @done
    inc background_tick
    lda background_tick
    and #7
    bne @done
    inc background_phase
    lda background_phase
    and #3
    sta background_phase
    ldx #6
@patch:
    lda _background_mask
    and background_bits,x
    beq @next
    lda background_addresses_lo,x
    sta robot_ptr
    lda background_addresses_hi,x
    sta robot_ptr+1
    cpx #3
    bcs @scope
    txa
    clc
    adc background_phase
    and #3
    beq @lit
    lda #220                 ; scene glyph 92 + gray PF3 selector
    bne @write
@lit:
    lda #222
    bne @write
@scope:
    txa
    sec
    sbc #3
    asl a
    clc
    adc background_phase
    and #3
    clc
    adc #252
@write:
    ldy #0
    sta (robot_ptr),y
@next:
    dex
    bpl @patch
@done:
_background_end:
    rts
robot_update:
    lda _robot_frame
    cmp #40
    bcs @done
    ldx _robot_dirty
    bne @copy_frame
    cmp last_robot
    beq @done
@copy_frame:
    sta last_robot
    ldx #0
    stx _robot_dirty
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
    ldy #31
@copy:
    lda (robot_ptr),y
    sta $8EC0,y
    dey
    bpl @copy
@done: rts
infrastructure_update:
    lda _infra_enabled
    beq @done
    lda _infra_frame
    ldx _infra_dirty
    bne @copy_frame
    cmp last_infra
    beq @done
@copy_frame:
    sta last_infra
    asl a
    asl a
    asl a
    asl a
    asl a
    clc
    adc #<(_scene_data+720)
    sta robot_ptr
    lda #>(_scene_data+720)
    adc #0
    sta robot_ptr+1
    ldy #31
@copy:
    lda (robot_ptr),y
    sta $8DC0,y
    dey
    bpl @copy
    lda #0
    sta _infra_dirty
@done: rts
music_update:
    ldx _sound_track
    cpx #MUSIC_TRACKS
    bcc @valid
    ldx #0
@valid:
    cpx last_track
    beq @same
    stx last_track
    lda music_track_lo,x
    sta music_ptr
    lda music_track_hi,x
    sta music_ptr+1
    lda #0
    sta music_tick
    sta music_row
@same:
    lda _music_enabled
    bne @enabled
    lda #0
    sta $D201
    sta $D203
    sta $D205
    rts
@enabled:
    lda music_tick
    bne @envelopes
    lda music_row
    asl a
    clc
    adc music_row
    tay
    lda (music_ptr),y
    sta bass_note
    sta $D200
    iny
    lda (music_ptr),y
    sta lead_note
    sta $D202
    iny
    lda (music_ptr),y
    sta drum_type
@envelopes:
    ldx music_tick
    lda bass_note
    beq @bass_off
    lda bass_envelope,x
    ora #$A0
@bass_off:
    sta $D201
    lda lead_note
    beq @lead_off
    lda lead_envelope,x
    beq @lead_off
    ora #$A0
@lead_off:
    sta $D203
    lda drum_type
    beq @drum_off
    cmp #1
    bne @noise
    lda kick_freq,x
    sta $D204
    lda kick_envelope,x
    beq @drum_off
    ora #$A0
    jmp @drum_off
@noise:
    lda #12
    sta $D204
    lda hat_envelope,x
    ldy drum_type
    cpy #3
    bne @hat
    lda snare_envelope,x
@hat:
    cmp #0                    ; CPY above changes Z; test envelope A itself
    beq @drum_off
    ora #$80
@drum_off:
    sta $D205
    inc music_tick
    lda music_tick
    cmp #MUSIC_ROW_FRAMES
    bcc @done
    lda #0
    sta music_tick
    inc music_row
    lda music_row
    and #31
    sta music_row
@done: rts

effects_update:
    lda _sfx_enabled
    bne @enabled
    lda #0
    sta _sound_request
    sta fx_type
    sta fx_time
    sta $D207
    rts
@enabled:
    lda _sound_request
    beq @continue
    cmp #5
    bcs @consume             ; bounded request protocol 1..4
    cmp fx_type
    bcc @consume             ; win > push > undo > blocked
    sta fx_type
    tax
    lda effect_lengths-1,x
    sta fx_time
@consume:
    lda #0
    sta _sound_request
@continue:
    lda fx_time
    beq @off
    ldx fx_type
    cpx #4
    beq @win
    cpx #3
    beq @push
    cpx #2
    beq @undo
    lda #210
    ldy #$84
    bne @write
@push:
    lda fx_time
    asl a
    clc
    adc #44
    ldy #$A9
    bne @write
@undo:
    lda fx_time
    asl a
    clc
    adc #100
    ldy #$A6
    bne @write
@win:
    lda fx_time
    lsr a
    lsr a
    tax
    lda win_notes,x
    ldy #$A9
@write:
    sta $D206
    sty $D207
    dec fx_time
    rts
@off:
    lda #0
    sta fx_type
    sta $D207
    rts
.segment "RODATA"
background_bits: .byte 1,2,4,8,16,32,64
background_addresses_lo: .byte <$8852,<$8855,<$8AD3,<$8BBA,<$8BBB,<$8BBC,<$8BBD
background_addresses_hi: .byte >$8852,>$8855,>$8AD3,>$8BBA,>$8BBB,>$8BBC,>$8BBD
bass_envelope: .byte 6,6,5,4,3,2
lead_envelope: .byte 5,5,4,3,2,0
kick_freq: .byte 110,180,220,240,250,250
kick_envelope: .byte 7,5,3,1,0,0
hat_envelope: .byte 3,1,0,0,0,0
snare_envelope: .byte 5,4,2,1,0,0
effect_lengths: .byte 2,5,6,20
win_notes: .byte 53,60,71,80,90,107
.include "audio.inc"
.assert MUSIC_ROW_FRAMES=6,error,"envelopes are six PAL ticks"
.assert MUSIC_TRACKS=3,error,"M1 track table expected three motifs"
