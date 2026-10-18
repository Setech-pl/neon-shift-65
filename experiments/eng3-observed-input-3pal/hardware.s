.import _loading_vbi
; Native PAL VBI audio + early gameplay DLI input. No C/cc65 calls in ISR.
.export _native_vbi,_vbi_end,_background_update,_background_end,_native_dli,_dli_end
.export _display_font,_display_pf1,_display_pf2
.export _hud_pending,_dli_font,_dli_pf1,_dli_pf2
.export _background_enabled,_background_mask,_hud_enabled
.export _display_active
.export _robot_dirty
.export _robot_frame,_robot_update
.import _phase_tick,_phase_commit
.export _asset_loading
.import _robot_frames

.export _infra_enabled,_infra_frame,_infra_dirty
.export _audio_resume
.export _frame_logic,_frame_audio,_frame_render
.export _hardware_init,_frame_begin,_frame_end,_video_clock
.export _music_enabled,_sfx_enabled,_sound_track,_sound_request
.export _input_head,_input_tail,_input_overflows,_input_clock
.export _queued_stick,_queued_trigger,_queued_console
.macpack longbranch
.segment "ZEROPAGE"
_input_head: .res 1
_input_tail: .res 1
_input_clock: .res 1
_poll_stick: .res 1
_poll_trigger: .res 1
_poll_console: .res 1
_poll_ready: .res 1
_poll_fence: .res 1
_capture_active: .res 1
_deferred_epoch: .res 1
_deferred_seen: .res 1
_poll_last_stick: .res 1
_poll_last_trigger: .res 1
_poll_last_console: .res 1
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
_dli_font: .res 8
_dli_pf1: .res 8
_dli_pf2: .res 8
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
input_sampled: .res 1
_music_enabled: .res 1
_sfx_enabled: .res 1
_sound_track: .res 1
_sound_request: .res 1
_input_overflows: .res 1
_queued_stick: .res 128
_queued_trigger: .res 128
_queued_console: .res 128
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
    sta _input_clock
    sta input_sampled
    sta _input_head
    sta _input_tail
    sta _input_overflows
    sta _poll_ready
    sta _capture_active
    sta _deferred_epoch
    sta _deferred_seen
    sta _sound_request
    sta _publish_pending
    sta _publish_count
    sta _robot_copy
    sta _ambient_active
    sta _menu_active
    sta _publish_late
    sta _publication_overflow
    sta _audio_calls
    sta order_index
    sta fx_type
    sta fx_time
    sta music_row
    sta music_tick
    lda #15
    sta _poll_last_stick
    lda #1
    sta _poll_last_trigger
    lda #7
    sta _poll_last_console
    lda #2
    sta _sound_track
    lda #$ff
    sta last_robot
    sta last_track
    lda #5
    sta _robot_frame
    lda #0
    sta _music_enabled
    sta _ratio_pending
    lda #1
    sta _sfx_enabled
    lda #0
    sta $D208                 ; AUDCTL: four independent 64-kHz channels
    sta $D201
    sta $D203
    sta $D205
    sta $D207
    lda #3
    sta $D20F                 ; keyboard scan remains active
    lda #1
    sta _asset_loading           ; inherit the already-visible bootstrap loader
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
palette_restore:
    lda #0
    sta $004d                 ; ATRACT: keep joystick/idle game palette
    sta $004f                 ; COLRSH: recover an already active attract
    lda #$fe
    sta $004e                 ; DRKMSK: natural OS luminance mask
    ldx #4
@palette:
    lda $02c4,x
    sta $d016,x
    dex
    bpl @palette
    rts
_native_vbi = native_vbi
native_vbi:
    pha
    txa
    pha
    tya
    pha
    jsr palette_restore
    inc _video_clock
    lda _asset_loading
    beq @normal
    lda #0
    sta input_sampled
    jsr _loading_vbi
    jmp _vbi_end
@normal:
    ; Gameplay samples immediately after the first HUD DLI. Resident UI,
    ; menu, blank transitions and absent DLI use this one-per-PAL fallback.
    lda input_sampled
    bne @sample_done
    jsr input_sample
@sample_done:
    lda #0
    sta input_sampled
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
    jsr _phase_tick              ; tick the PREVIOUS visible action once
    jsr publish_vbi              ; critical board/robot before cosmetic HUD
    jsr hud_commit
    jsr background_update
    jsr music_update
    jsr effects_update
    lda $D40B
    sta _publication_vcount
    cmp #12
    bcc :+
    cmp #124
    bcs :+
    inc _publish_late
:
_publication_end:
_vbi_end:
    lda $14
    sta vbi_rtc
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
    ; Colors/font are installed before input work; preserve Y for foreground.
    cpx #0
    bne _dli_end
    lda _hud_enabled
    beq _dli_end
    lda _display_active
    beq _dli_end
    lda _asset_loading
    bne _dli_end
    lda input_sampled
    bne _dli_end
    tya
    pha
    jsr input_sample
    lda #1
    sta input_sampled
    pla
    tay
_dli_end:
    pla
    tax
    pla
    rti
; Only ISR owns queue producer and wake clock. Direct device registers avoid
; stale OS shadows when the gameplay sample precedes OS VBI. Head is last,
; wake clock follows it; no cc65 scratch, no C call, Y saved by DLI caller.
input_sample:
    lda _capture_active
    beq :+
    cmp #2
    bne @defer
    ; A complete unchanged tuple exists logically in the last-value registers.
    ; Publish it at the foreground fence if NMI follows its epoch check.
    lda _poll_last_stick
    sta _poll_stick
    lda _poll_last_trigger
    sta _poll_trigger
    lda _poll_last_console
    sta _poll_console
    lda #1
    sta _poll_ready
@defer:
    inc _deferred_epoch
    inc _input_clock
    rts
:
    lda _input_head
    clc
    adc #1
    and #127
    cmp _input_tail
    beq @full
    tax
    ldy _input_head
    lda $D300
    and #15
    sta _queued_stick,y
    lda $D010
    and #1
    sta _queued_trigger,y
    lda $D01F
    and #7
    sta _queued_console,y
    stx _input_head
    inc _input_clock
    rts
@full:
    inc _input_overflows
    inc _input_clock
    rts
; Main publishes the mask before enabling. Seven writes
; at most, every eight PAL ticks; no board/charset indices are modified.
.export _publish_pending,_publish_count,_publish_addr_lo,_publish_addr_hi,_publish_code
.export _robot_bank_a,_robot_bank_b,_robot_copy,_ambient_active,_menu_active
.export _palette_dim,_publish_late,_publication_overflow,_audio_calls,_publication_vcount
.export _ratio_pending
.export _dock_timer,_music_update,_music_end,_publication_end
.segment "ZEROPAGE"
publish_ptr:.res 2
anim_ptr:.res 2
.segment "BSS"
_publish_pending:.res 1
_publish_count:.res 1
_publish_addr_lo:.res 32
_publish_addr_hi:.res 32
_publish_code:.res 32
_robot_bank_a:.res 1
_robot_bank_b:.res 1
_robot_copy:.res 1
_ambient_active:.res 1
_menu_active:.res 1
_palette_dim:.res 1
_publish_late:.res 1
_publication_overflow:.res 1
_publication_vcount:.res 1
_ratio_pending:.res 1
_audio_calls:.res 1
_dock_timer:.res 10
anim_ticks:.res 32
anim_phases:.res 32
anim_slot:.res 1
anim_count:.res 1
anim_cursor:.res 1
order_index:.res 1
pattern_hi:.res 1
.segment "CODE"
.import _hud_epoch,_hud_ready_epoch,_hud_committed_epoch
.import _hud_state_moves,_hud_state_pushes,_hud_state_docks
.segment "BSS"
hud_live_moves:.res 4
hud_live_pushes:.res 4
hud_live_docks:.res 1
_hud_live_valid:.res 1
hud_copy_mask:.res 1
.export _hud_live_valid,hud_live_moves,hud_live_pushes,hud_live_docks
.segment "CODE"
 .export _hud_commit,_hud_seed_live
; Stopped-DMA initialization only: caller cleared pending before constructing
; and copying the complete initial HUD, so ISR cannot write this cache here.
_hud_seed_live:
.repeat 4,I
    lda _hud_state_moves+I
    sta hud_live_moves+I
    lda _hud_state_pushes+I
    sta hud_live_pushes+I
.endrepeat
    lda _hud_state_docks
    sta hud_live_docks
    lda #1
    sta _hud_live_valid
    rts
hud_commit:
_hud_commit = hud_commit
    lda _hud_pending
    jeq @done
    lda _hud_ready_epoch
    cmp _hud_epoch
    jne @cancel
    lda _hud_ready_epoch+1
    cmp _hud_epoch+1
    jne @cancel
    ; Determine complete changed fields against the last committed snapshot.
    ; Unchanged fields retain their already-correct bytes. Every changed field
    ; is copied in this same blank before committing the common token.
    lda #0
    sta hud_copy_mask
    lda _hud_live_valid
    bne @moves
    lda #7
    sta hud_copy_mask
    jmp @copy
@moves:
    .repeat 4,I
        lda _hud_state_moves+I
        cmp hud_live_moves+I
        bne @moves_changed
    .endrepeat
    jmp @pushes
@moves_changed:
    inc hud_copy_mask
@pushes:
    .repeat 4,I
        lda _hud_state_pushes+I
        cmp hud_live_pushes+I
        bne @pushes_changed
    .endrepeat
    jmp @docks
@pushes_changed:
    lda hud_copy_mask
    ora #2
    sta hud_copy_mask
@docks:
    lda _hud_state_docks
    cmp hud_live_docks
    beq @copy
    lda hud_copy_mask
    ora #4
    sta hud_copy_mask
@copy:
    ; Absolute copies use eight CPU cycles per byte, without page/branch costs.
    lda hud_copy_mask
    and #1
    jeq @copy_pushes
    .repeat 72,I
        lda $9430+I
        sta $9170+I
    .endrepeat
@copy_pushes:
    lda hud_copy_mask
    and #2
    jeq @copy_ratio
    .repeat 72,I
        lda $94c0+I
        sta $9200+I
    .endrepeat
@copy_ratio:
    lda hud_copy_mask
    and #4
    jeq @cache
    .repeat 88,I
        lda $9540+I
        sta $90e8+I
    .endrepeat
@cache:
    .repeat 4,I
        lda _hud_state_moves+I
        sta hud_live_moves+I
        lda _hud_state_pushes+I
        sta hud_live_pushes+I
    .endrepeat
    lda _hud_state_docks
    sta hud_live_docks
    lda #1
    sta _hud_live_valid
@token:
    lda _hud_ready_epoch
    sta _hud_committed_epoch
    lda _hud_ready_epoch+1
    sta _hud_committed_epoch+1
@cancel:
    lda #0
    sta _hud_pending
@done:rts
publish_vbi:
    lda publication_owner
    bne @done
    lda #0
    sta _critical_guard
    jsr publish_update
@done:rts
publish_update:
    lda _critical_guard
    bne @done
    lda _publish_pending
    beq @done
    ldx #0
@write:
    cpx _publish_count
    beq @finish
    lda _publish_addr_lo,x
    sta publish_ptr
    lda _publish_addr_hi,x
    sta publish_ptr+1
    lda _publish_code,x
    ldy #0
    sta (publish_ptr),y
    inx
    bne @write
@finish:
    lda _publish_count
    beq :+
    lda #1
    sta _critical_guard
:
    jsr _phase_commit
    lda #0
    sta _publish_pending
    sta _publish_count
@done:rts
_robot_update = robot_update
robot_update:
    lda _robot_copy
    beq @done
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
    lda #$e0
    sta publish_ptr
    lda _robot_bank_a
    clc
    adc #3
    sta publish_ptr+1
    lda _robot_bank_b
    cmp #$ff
    beq @whole
    ldy #15
    ldx #16
    jsr @copy
    lda _robot_bank_b
    cmp #$ff
    beq @finish
    clc
    adc #3
    sta publish_ptr+1
    ldy #31
    ldx #16
    jsr @copy
    jmp @finish
@whole:
    ldy #31
    ldx #32
    jsr @copy
@finish:
    lda #0
    sta _robot_copy
@done:rts
@copy:
@loop:
    lda (robot_ptr),y
    sta (publish_ptr),y
    dey
    dex
    bne @loop
    rts
_background_update = background_update
background_update:
    lda _ambient_active
    beq @menu
    ; Transposed descriptors are prepared with DMA/ambient stopped. This
    ; keeps every original tick/phase and full device update, while removing
    ; descriptor-pointer setup/advance from the per-frame critical path.
    ldx #0
    stx anim_count
@one:
    cpx $9de4
    jcs @done
    inc anim_ticks,x
    lda anim_ticks,x
    cmp anim_period,x
    bcc @next
    inc anim_count
    lda #0
    sta anim_ticks,x
    clc
    lda anim_phases,x
    adc #32
    and #96
    sta anim_phases,x
    txa
    ora anim_phases,x
    tay
    lda anim_frames,y
    pha
    lda anim_addr_lo,x
    sta publish_ptr
    lda anim_addr_hi,x
    sta publish_ptr+1
    pla
    ldy #0
    sta (publish_ptr),y
@next:
    inx
    bne @one
@menu:
    lda _menu_active
    jeq @done
    inc background_tick
    lda background_tick
    and #7
    jne @done
    inc background_phase
    lda background_phase
    and #3
    tax
    ; Phase-shifted service lamps at authored terminal bulbs (x55/239,y52).
    txa
    and #1
    ora #$80
    sta $A000+52*40+6
    txa
    clc
    adc #1
    and #3
    tax
    txa
    and #1
    ora #$80
    sta $A000+52*40+29
    lda background_phase
    and #3
    tax
    lda menu_lamps,x
    sta $A000+33*40+30
    txa
    .repeat 4
        asl a
    .endrepeat
    tax
    ; One complete16x8 oscilloscope trace in the left monitor, inside its
    ; x54..73/y29..38 screen. Published entirely during blank, never piecemeal.
    .repeat 8,I
        lda menu_wave+I*2,x
        sta $A000+(30+I)*40+7
        lda menu_wave+I*2+1,x
        sta $A000+(30+I)*40+8
    .endrepeat
@done:
_background_end:
    rts
.export _animation_reset
_animation_reset:
    lda #0
    ldx #31
@clear:
    sta anim_ticks,x
    sta anim_phases,x
    dex
    bpl @clear
    ; Transpose validated packets into a resident224B descriptor cache.
    ; Every consumer is stopped by show_play/video_off at this point.
    lda #<$9e60
    sta anim_ptr
    lda #>$9e60
    sta anim_ptr+1
    ldx #0
@phase:
    cpx $9de4
    bcs @done
    ldy #0
    lda (anim_ptr),y
    sta anim_addr_lo,x
    iny
    lda (anim_ptr),y
    sta anim_addr_hi,x
    iny
    lda (anim_ptr),y
    sta anim_period,x
    iny
    lda (anim_ptr),y
    and #3
    .repeat 5
        asl a
    .endrepeat
    sta anim_phases,x
    iny
    lda (anim_ptr),y
    sta anim_frames,x
    iny
    lda (anim_ptr),y
    sta anim_frames+32,x
    iny
    lda (anim_ptr),y
    sta anim_frames+64,x
    iny
    lda (anim_ptr),y
    sta anim_frames+96,x
    clc
    lda anim_ptr
    adc #8
    sta anim_ptr
    bcc :+
    inc anim_ptr+1
:
    inx
    bne @phase
@done:rts
.segment "LOADBSS"
anim_period:.res 32
anim_addr_lo:.res 32
anim_addr_hi:.res 32
anim_frames:.res 128
.segment "CODE"
_music_update = music_update
music_update:
    inc _audio_calls
    lda _music_enabled
    bne @enabled
    lda #0
    sta $D201
    sta $D203
    sta $D205
    jmp _music_end
@enabled:
    lda music_tick
    bne @envelopes
    lda order_index
    tay
    lda $1e00,y
    ; Eight patterns, each192 bytes. Full16-bit pattern*3*64.
    sta pattern_hi
    asl a
    clc
    adc pattern_hi
    sta pattern_hi
    and #3
    .repeat 6
        asl a
    .endrepeat
    sta music_ptr
    lda pattern_hi
    lsr a
    lsr a
    clc
    adc #$18
    sta music_ptr+1
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
    clc
    adc vibrato,x
    sta $D202
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
    cmp #0
    beq @drum_off
    ora #$80
@drum_off:
    sta $D205
    inc music_tick
    lda music_tick
    cmp #6
    bcc _music_end
    lda #0
    sta music_tick
    inc music_row
    lda music_row
    cmp #64
    bcc _music_end
    lda #0
    sta music_row
    inc order_index
    lda order_index
    and #15
    sta order_index
_music_end:rts

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
vibrato: .byte 0,0,1,1,0,$ff
menu_lamps:.byte $80,$40,$20,$10

; Critical descriptors prepare independently of the previous visible action.
; Foreground commits before all affected ANTIC reads or in whole-board blank.
; critical_guard preserves one complete raster of the previous core action.
.export _publish_now,_foreground_publication_end,publish_update,_publish_first_row
.segment "BSS"
vbi_rtc:.res 1
_publish_first_row:.res 1
.segment "CODE"
.export _critical_guard
.segment "BSS"
publication_owner:.res 1
front_deadline:.res 1
_critical_guard:.res 1
.segment "CODE"
_publish_now:
    ; Whole-board blank interval; no screen/glyph writes during active DMA.
    ; At >=260 the physical248 NMI has already begun/completed. The >=48
    ; first gameplay fetch leaves >=24 lines in the early window.
    lda $d40b
    cmp #130
    bcs @safe
    cmp #12
    bcc @safe
    ; Earliest changed screen row includes every old/new robot/crate quarter.
    ; Dynamic slots124..127 only occur at those robot positions. Reserve32
    ; physical lines for the bounded commit incl. a possible DLI.
    ldx _publish_first_row
    cpx #24
    bcs _foreground_publication_end
    lda row_vcount,x
    sec
    sbc #16
    sta front_deadline
    lda $d40b
    cmp front_deadline
    bcs _foreground_publication_end
@safe:
    lda #1
    sta publication_owner
    ; NMI can occur before lock: recheck pending/guard in publish_update.
    jsr publish_update
    lda #0
    sta publication_owner
_foreground_publication_end:
    rts
.import _gs,_render_board_y
.segment "RODATA"
row_address_lo:
.repeat 24,I
 .byte <($8800+I*40)
.endrepeat
row_address_hi:
.repeat 24,I
 .byte >($8800+I*40)
.endrepeat
row_vcount:
.repeat 24,I
 ; Native PNG y=24+8*row; physical scanline adds8. Keep the
 ;24/34-scanline publication reserve relative to this actual boundary.
 .byte 16+I*4
.endrepeat

.segment "RODATA"
menu_wave:
 .byte 12,0,30,0,18,12,243,63,1,32,1,224,0,192,0,192
 .byte 192,0,224,1,32,193,51,255,18,0,30,0,12,0,12,0
 .byte 0,12,0,30,12,18,63,243,32,1,224,1,192,0,192,0
 .byte 0,192,1,224,193,32,255,51,0,18,0,30,0,12,0,12

; Foreground-only raw probe. ISR remains the sole raw queue producer.
; capture_active serializes reads; the fence orders older and later ISR tuples.
.export _poll_capture,input_sample
.export _input_probe,_poll_stick,_poll_trigger,_poll_console
.export _poll_ready,_poll_fence,_deferred_epoch,_deferred_seen
.export _poll_last_stick,_poll_last_trigger,_poll_last_console
.segment "BSS"
.segment "DATA"
.segment "CODE"
_input_probe:
    lda _poll_ready
    bne poll_ready
    ldx _input_head
    cpx _input_tail
    bne poll_ready
_poll_capture:
    ; Serialize full device transactions against the ISR producer. The ISR
    ; still ticks once/PAL but defers its heartbeat while these reads run.
    lda #1
    sta _capture_active
    ldx _input_head
    stx _poll_fence
    ; No-change polling compares at acquisition and avoids three stores.
    ; If changed, reconstruct exactly the acquired tuple: an earlier equal
    ; component is copied from the consumed last value, never re-read later.
    lda $D300
    and #15
    cmp _poll_last_stick
    jne poll_stick_changed
    lda $D010
    and #1
    cmp _poll_last_trigger
    jne poll_trigger_changed
    lda $D01F
    and #7
    cmp _poll_last_console
    jne poll_console_changed
    ; The ISR may have produced an older changed tuple before the lock.
    ; Preserve this completed tuple even if it equals the stale consumedlast.
    ldx _poll_fence
    cpx _input_tail
    jne poll_same_ready
    lda #2
    sta _capture_active
    lda _deferred_epoch
    cmp _deferred_seen
    jne poll_same_ready
    lda #0
    sta _capture_active
    lda _poll_ready
    ldx #0
    rts
poll_same_ready:
    ; No-change acquisition is nevertheless the deferred PAL repeat sample.
    lda _poll_last_stick
    sta _poll_stick
    lda _poll_last_trigger
    sta _poll_trigger
    lda _poll_last_console
    sta _poll_console
poll_commit:
    lda #1
    sta _poll_ready            ; fully initialized tuple before unlock
    lda #0
    sta _capture_active
poll_ready:
    lda #1
    ldx #0
    rts
.segment "LOADER"
poll_stick_changed:
    sta _poll_stick
    lda $D010
    and #1
    sta _poll_trigger
    lda $D01F
    and #7
    sta _poll_console
    jmp poll_commit
poll_trigger_changed:
    sta _poll_trigger
    lda _poll_last_stick
    sta _poll_stick
    lda $D01F
    and #7
    sta _poll_console
    jmp poll_commit
 .segment "CODE"
poll_console_changed:
    sta _poll_console
    lda _poll_last_stick
    sta _poll_stick
    lda _poll_last_trigger
    sta _poll_trigger
    jmp poll_commit
.segment "CODE"

.export _splash_clock_sync
.segment "CODE"
_splash_clock_sync:
    lda $14
    sta vbi_rtc
    lda #0
    sta input_sampled
    rts

; ENG1: native idle wait removes repeated cc65 call/boolean marshalling.
; ISR retains sole raw-ring ownership and the full probe remains unchanged.
.export _input_wait
.segment "LOADBSS"
wait_clock:.res 1
.segment "CODE"
_input_wait:
    sta wait_clock
wait_again:
    lda _input_clock
    cmp wait_clock
    bne wait_done
    lda _poll_ready
    bne wait_done
    ldx _input_head
    cpx _input_tail
    bne wait_done
_wait_capture:
    ; Serialize full device transactions against the ISR producer. The ISR
    ; still ticks once/PAL but defers its heartbeat while these reads run.
    lda #1
    sta _capture_active
    ldx _input_head
    stx _poll_fence
    ; No-change polling compares at acquisition and avoids three stores.
    ; If changed, reconstruct exactly the acquired tuple: an earlier equal
    ; component is copied from the consumed last value, never re-read later.
    lda $D300
    and #15
    cmp _poll_last_stick
    jne poll_stick_changed
    lda $D010
    and #1
    cmp _poll_last_trigger
    jne poll_trigger_changed
    lda $D01F
    and #7
    cmp _poll_last_console
    jne poll_console_changed
    ; The ISR may have produced an older changed tuple before the lock.
    ; Preserve this completed tuple even if it equals the stale consumedlast.
    ldx _poll_fence
    cpx _input_tail
    jne poll_same_ready
    lda #2
    sta _capture_active
    lda _deferred_epoch
    cmp _deferred_seen
    jne poll_same_ready
    lda #0
    sta _capture_active
    lda _poll_ready
    bne wait_done
    jmp wait_again
wait_done:
    rts
