; Adapted cassette state machine from pinned Void Strike ef1924d (MIT).
; NEON owns its overlay, display, clock bridge and menu restoration.
.include "boot-splash.inc"
.include "splash-data.inc"
LOADER_TITLE_COLPF1=$0e
LOADER_TITLE_COLPF2=$00
LOADER_SHIP_COLPF1=$0e
LOADER_SHIP_COLPF2=$00
LOADER_STUDIO_COLPF1=$d8
LOADER_STUDIO_COLPF2=$00
SPLASH_SPACE_KEY=$21
AUDF1=$d200
AUDC1=$d201
AUDCTL=$d208
KBCODE=$d209
RANDOM=$d20a
SKSTAT=$d20f
TRIG0=$d010
COLPF1=$d017
COLPF2=$d018
COLBK=$d01a
VCOUNT=$d40b
WSYNC=$d40a
NMIEN=$d40e
DMACTL=$d400
.import _loading_begin,_loading_label,_loading_progress
.import _video_clock,_native_dli,_input_rearm,_splash_clock_sync
.export _splash_run,splash_hold,splash_exit,splash_colors,loader_frame_count
.segment "SPLASH"
loader_frame_count: .byte 250
loader_dli_phase: .byte 0
_splash_run:
    lda #250
    sta loader_frame_count
    lda #0
    sta loader_dli_phase
    ldx #splash_immutable-splash_segment_index-1
@reset:
    sta splash_segment_index,x
    dex
    bpl @reset
    lda #$ff
    sta splash_q16
    sta splash_q16+1
    lda #SPLASH_START_VOLUME
    sta splash_volume
    ldx #5
@colors:
    lda splash_colour_base,x
    sta splash_colors,x
    dex
    bpl @colors
@blank:
    lda VCOUNT
    cmp #132
    bcc @blank
    php
    sei
    lda #0
    sta NMIEN
    sta DMACTL
    sta $22f
    sta $d201
    sta $d203
    sta $d205
    sta $d207
    sta AUDCTL
    sta $2c8
    sta COLBK
    lda #3
    sta $d20f
    lda #<loader_dli
    sta $200
    lda #>loader_dli
    sta $201
    lda #0
    sta $d402
    lda #$88
    sta $d403
    lda #$80
    sta NMIEN
    jsr splash_hold
    jsr _loading_begin
    lda #7
    jsr _loading_label
    lda #0
    sta AUDCTL
    sta $2c8
    sta COLBK
    lda #3
    sta $d20f
    lda #<_native_dli
    sta $200
    lda #>_native_dli
    sta $201
    jsr _splash_clock_sync
    lda #$c0
    sta NMIEN
    plp
    jsr cache_restore
    ldx #0
    rts
wait_frame_start:
    lda VCOUNT
    beq wait_frame_start
@zero:
    lda VCOUNT
    bne @zero
count_frame:
    inc _video_clock
    inc $14
    bne :+
    inc $13
    bne :+
    inc $12
:   rts
wait_boundary:
    lda VCOUNT
    beq wait_boundary
@zero:
    lda VCOUNT
    bne @zero
    rts
.segment "SPLASH"

splash_blob_start:

; -----------------------------------------------------------------------------
; Variables (image-initialised; see above)

; Faded playfield colours for this frame: title, ship and studio COLPF1/COLPF2
; pairs in display order. The main loop writes the title pair at frame top and
; `loader_dli` loads the other two pairs from here.
splash_colors:
    .byte LOADER_TITLE_COLPF1, LOADER_TITLE_COLPF2
    .byte LOADER_SHIP_COLPF1, LOADER_SHIP_COLPF2
    .byte LOADER_STUDIO_COLPF1, LOADER_STUDIO_COLPF2

; q16 = $FFFF before the fade; one SPLASH_FADE_STEP is subtracted per fade
; frame, clamped at zero, so q = q16>>8 is 0 on the final hold frame.
splash_q16:
    .word $FFFF
splash_product:
    .word $0000
splash_volume:
    .byte SPLASH_START_VOLUME

splash_segment_index:
    .byte $00
splash_segment_frames:
    .byte $00
splash_segment_type:
    .byte $00
; The framed byte being clocked out, its cell index (0 = start bit, 1-8 = data
; bits LSB first, 9 = stop bit, >= 10 = load the next byte) and the sync bytes
; still owed by the current DATA segment.
splash_shift:
    .byte $00
splash_bit_index:
    .byte $0A
splash_sync_left:
    .byte $00
; VCOUNT at which the next bit cell is emitted.
splash_cell_target:
    .byte $00

; Skip: each input arms only on a frame where it is released, so a button or
; key held from frame 1 never skips (plan §4.2).
splash_armed_fire:
    .byte $00
splash_armed_space:
    .byte $00
splash_skipped:
    .byte $00

; -----------------------------------------------------------------------------
; Tables and code. Everything from here to the end of the window is immutable
; for the life of the blob, which is what the boot smoke checksums at the loader
; milestones: the variables above are mutated by the hold itself, so only this
; part can prove that nothing between `start` and the hold wrote into $0500-$06FF.

splash_immutable:
splash_colour_base:
    .byte LOADER_TITLE_COLPF1, LOADER_TITLE_COLPF2
    .byte LOADER_SHIP_COLPF1, LOADER_SHIP_COLPF2
    .byte LOADER_STUDIO_COLPF1, LOADER_STUDIO_COLPF2

splash_segment_types:
    EMIT_SPLASH_SEGMENT_TYPES
splash_segment_lengths:
    EMIT_SPLASH_SEGMENT_FRAMES

; -----------------------------------------------------------------------------
; The hold. `show_loader` keeps the display-list, PRIOR, palette and VDSLST
; setup and the NMIEN/DMACTL start, then jumps here; the exit path below returns
; to `start`'s `jsr show_loader`.

splash_hold:
    jsr splash_segment_load
@frame:
    jsr wait_frame_start
    lda #$22
    sta DMACTL
    ; Frame top: the title pair, COLBK and the first cell's VCOUNT target. This
    ; replaces the per-frame `set_loader_title_palette` call; the routine itself
    ; stays for `show_loader`'s initialisation.
    lda splash_colors
    sta COLPF1
    lda splash_colors+1
    sta COLPF2
    lda #$00
    sta COLBK
    sta splash_cell_target

    ; SPLASH_CELLS_PER_FRAME bit cells, each aligned to its own VCOUNT, so the
    ; tone switches per bit rather than per frame: 312 PAL scanlines over 12
    ; cells of 26 lines is exactly 600 baud.
    ldy #SPLASH_CELLS_PER_FRAME
@cell:
    lda VCOUNT
    cmp splash_cell_target
    bcc @cell
    jsr splash_emit_cell
    lda splash_cell_target
    clc
    adc #SPLASH_CELL_VCOUNT_STEP
    sta splash_cell_target
    dey
    bne @cell

    ; Frame tail, inside blanking: the segment step and the fade arithmetic run
    ; where no DMA contends for cycles and no bit cell is waiting, so the values
    ; are in place at the top of the next frame.
    jsr splash_poll_skip
    lda splash_skipped
    bne splash_natural_end
    dec loader_frame_count
    beq splash_natural_end
    jsr splash_frame_tail
    jmp @frame

; -----------------------------------------------------------------------------
; One exit path for the natural end of frame 250 and for the skip.

splash_natural_end:
    jsr wait_boundary
    ; Both exits hand off at a NEW PAL boundary not manually counted yet.
splash_exit:
    lda #$00
    sta AUDC1                   ; the deck stops before the display is blanked
    ldy #$05
@black:
    sta splash_colors,y
    dey
    bpl @black
    sta COLBK
    sta COLPF1
    sta COLPF2
    sta NMIEN
    sta DMACTL
    ; A skip leaves the input still pressed. Waiting for both to be released
    ; means the frontend cannot see this press at all; belt and braces over
    ; `frontend_input_armed`, which the menu clears on entry and sets only on a
    ; frame with the stick centred and FIRE up. The natural exit presses
    ; nothing, so this is a no-op there and in every automated boot trace.
@release:
    lda TRIG0
    and #$01
    beq @release_frame
    lda SKSTAT
    and #$04
    beq @release_frame
@done:
    rts
@release_frame:
    jsr count_frame
    jsr wait_boundary
    jmp @release

; -----------------------------------------------------------------------------
; Bit cells

; Emits one cell: AUDF1 takes the mark or space divisor and AUDC1 the pure tone
; with this frame's volume. SILENCE writes volume 0 and leaves AUDF1 alone.
splash_emit_cell:
    lda splash_segment_type
    beq @silence
    ldx #SPLASH_MARK_AUDF
    cmp #SPLASH_SEGMENT_LEADER
    beq @emit
    ; DATA: start bit 0, eight data bits LSB first, stop bit 1.
    lda splash_bit_index
    cmp #$0A
    bcc @framed
    jsr splash_next_byte        ; returns with A = 0, the new cell index
@framed:
    inc splash_bit_index
    cmp #$09
    beq @emit                   ; the stop bit is a mark
    cmp #$00
    beq @space                  ; the start bit is a space
    lsr splash_shift
    bcs @emit
@space:
    ldx #SPLASH_SPACE_AUDF
@emit:
    ; One octave down for a DATA_LOW block: the divider doubles, N -> 2N+1, so
    ; (N + 1) -> 2 * (N + 1) exactly. The same pure tone, so the three imitated
    ; records do not sound identical (owner, 2026-09-23). SILENCE never reaches
    ; here and LEADER is type 1, so only a DATA_LOW block takes the shift.
    txa
    ldx splash_segment_type
    cpx #SPLASH_SEGMENT_DATA_LOW
    bne @store
    asl a
    ora #$01
@store:
    sta AUDF1
    lda splash_volume
    ora #SPLASH_AUDC_BASE
    sta AUDC1
    rts
@silence:
    lda #SPLASH_AUDC_BASE
    sta AUDC1
    rts

; Two sync bytes head every imitated record; the payload is POKEY's own random
; register, which is exactly as informative as a real tape's data would be.
splash_next_byte:
    lda splash_sync_left
    beq @random
    dec splash_sync_left
    lda #SPLASH_SYNC_BYTE
    jmp @store
@random:
    lda RANDOM
@store:
    sta splash_shift
    lda #$00
    sta splash_bit_index
    rts

; -----------------------------------------------------------------------------
; Frame tail: segment step, then the fade

splash_frame_tail:
    dec splash_segment_frames
    bne @fade
    inc splash_segment_index
    jsr splash_segment_load
@fade:
    ; loader_frame_count has already been decremented, so this runs on the tails
    ; of frames SPLASH_FADE_START_FRAME-1 .. 249: SPLASH_FADE_FRAMES steps, the
    ; last of which lands q = 0 before the final hold frame is drawn.
    lda loader_frame_count
    cmp #SPLASH_FADE_FRAMES+1
    bcs @done
    lda splash_q16
    sec
    sbc #<SPLASH_FADE_STEP
    sta splash_q16
    lda splash_q16+1
    sbc #>SPLASH_FADE_STEP
    sta splash_q16+1
    bcs @scale
    lda #$00
    sta splash_q16
    sta splash_q16+1
@scale:
    ; volume = END + ceil(SPAN * q / 256): 10 while q is high, 2 on frame 250,
    ; never 0 - the deck is cut by the teardown, it does not fade to silence.
    ldx #SPLASH_VOLUME_SPAN
    jsr splash_scale
    lda splash_product
    clc
    adc #$FF
    lda splash_product+1
    adc #SPLASH_END_VOLUME
    sta splash_volume
    ; Every splash colour, the DLI zones included: hue kept, luminance scaled to
    ; 0 on frame 250. A 4-bit luminance times an 8-bit q cannot carry into the
    ; hue nibble, so the result is monotone non-increasing by construction.
    ldy #$05
@colour:
    lda splash_colour_base,y
    and #$0F
    tax
    jsr splash_scale
    lda splash_colour_base,y
    and #$F0
    ora splash_product+1
    sta splash_colors,y
    dey
    bpl @colour
@done:
    rts

; splash_product = (q16 >> 8) * X, for X = 0..15. Preserves Y.
splash_scale:
    lda #$00
    sta splash_product
    sta splash_product+1
    cpx #$00
    beq @done
@add:
    lda splash_product
    clc
    adc splash_q16+1
    sta splash_product
    bcc @next
    inc splash_product+1
@next:
    dex
    bne @add
@done:
    rts

splash_segment_load:
    ldy splash_segment_index
    cpy #SPLASH_SEGMENT_COUNT
    bcc @in_range
    ; The generator asserts that the frames sum to the 250-frame hold, so the
    ; index can only reach the count on the tail of the last frame, which the
    ; exit takes first. Holding the last segment keeps that structural.
    dey
    sty splash_segment_index
@in_range:
    lda splash_segment_lengths,y
    sta splash_segment_frames
    lda splash_segment_types,y
    sta splash_segment_type
    cmp #SPLASH_SEGMENT_DATA
    bcc @done                   ; DATA and DATA_LOW both frame bytes; SILENCE
                                ; and LEADER number below DATA and do not
    lda #SPLASH_SYNC_BYTES
    sta splash_sync_left
    lda #$0A                    ; force a byte load on this segment's first cell
    sta splash_bit_index
@done:
    rts

; -----------------------------------------------------------------------------
; Skip. Hardware registers only: the OS VBI is off (NMIEN = $80, DLI only) so
; STRIG0 is never refreshed, and the CPU I-flag has been set since `sei` at
; `start` with no `cli` anywhere, so the OS keyboard IRQ never runs and CH is
; never written. SKCTL keeps what the OS's last SIOV left ($13: keyboard scan
; and debounce on), so POKEY still updates SKSTAT and KBCODE without any
; handler. Its bit 4 stops channels 3 and 4; the splash uses channel 1 alone,
; and the frontend writes $03 before the menu (fix/hardware-audio).

splash_poll_skip:
    lda TRIG0
    lsr a                       ; carry = FIRE released
    bcs @arm_fire
    lda splash_armed_fire
    bne @skip
    beq @space
@arm_fire:
    lda #$01
    sta splash_armed_fire
@space:
    ldx #$01                    ; X = 1 unless SPACE is the key currently down
    lda SKSTAT
    and #$04                    ; bit 2 clear = some key is down
    bne @space_state
    lda KBCODE
    and #$3F
    cmp #SPLASH_SPACE_KEY
    bne @space_state
    ldx #$00
@space_state:
    txa
    bne @arm_space
    lda splash_armed_space
    bne @skip
    rts
@arm_space:
    stx splash_armed_space
    rts
@skip:
    lda #$01
    sta splash_skipped
    rts

; -----------------------------------------------------------------------------
; The loader DLI moves here with the colours it loads. WSYNC aligns each switch
; to the first colour clock of the following zone. Two `lda abs` replace two
; `lda #imm`, so the 160-cycle bound of the MAIN version becomes 164.
; Only A is used and preserved; X and Y are untouched.

loader_dli:
    pha
    lda #$00
    sta WSYNC
    lda loader_dli_phase
    bne @studio
    lda splash_colors+2
    sta COLPF1
    lda splash_colors+3
    sta COLPF2
    inc loader_dli_phase
    pla
    rti
@studio:
    lda splash_colors+4
    sta COLPF1
    lda splash_colors+5
    sta COLPF2
    lda #$00                    ; restore title phase for the next frame
    sta loader_dli_phase
    pla
    rti


.include "cache.s"
