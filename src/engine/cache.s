; Three fixed outputs; CRC-verified source plus per-read and per-write bounds.
.segment "ZEROPAGE"
cache_src: .res 2
cache_dst: .res 2
cache_match: .res 2
.segment "SPLASH"
cache_index: .byte 0
cache_command: .byte 0
cache_low: .byte 0
cache_high: .byte 0
cache_starts_lo: .byte <$a000,<$b000,<$b400
cache_starts_hi: .byte >$a000,>$b000,>$b400
cache_ends_lo: .byte <$ac80,<$b320,<$b8b0
cache_ends_hi: .byte >$ac80,>$b320,>$b8b0
cache_restore:
    lda #0
    sta cache_index
    sta cache_src
    lda #$90
    sta cache_src+1
@stream:
    ldx cache_index
    lda cache_starts_lo,x
    sta cache_dst
    lda cache_starts_hi,x
    sta cache_dst+1
@command:
    jsr cache_get
    beq @end
    bmi @match
    tax
@literal:
    jsr cache_get
    jsr cache_put
    dex
    bne @literal
    jmp @command
@match:
    sta cache_command
    and #3
    sta cache_high
    jsr cache_get
    sta cache_low
    lda cache_dst
    clc
    sbc cache_low
    sta cache_match
    lda cache_dst+1
    sbc cache_high
    sta cache_match+1
    ; A back-reference must be inside the current fixed output.
    ldx cache_index
    lda cache_match
    cmp cache_starts_lo,x
    lda cache_match+1
    sbc cache_starts_hi,x
    bcc cache_fail
    lda cache_command
    and #$7c
    lsr a
    lsr a
    clc
    adc #3
    tax
@copy:
    ldy #0
    lda (cache_match),y
    jsr cache_put
    inc cache_match
    bne :+
    inc cache_match+1
:   dex
    bne @copy
    jmp @command
@end:
    ldx cache_index
    lda cache_dst
    cmp cache_ends_lo,x
    bne cache_fail
    lda cache_dst+1
    cmp cache_ends_hi,x
    bne cache_fail
    lda cache_progress,x
    sta _loading_progress
    inc cache_index
    lda cache_index
    cmp #3
    beq :+
    jmp @stream
:
    lda cache_src
    cmp #<($9000+CACHE_BYTES)
    bne cache_fail
    lda cache_src+1
    cmp #>($9000+CACHE_BYTES)
    bne cache_fail
    lda #1
    rts
cache_fail:
    lda #0
    rts
cache_get:
    lda cache_src
    cmp #<($9000+CACHE_BYTES)
    lda cache_src+1
    sbc #>($9000+CACHE_BYTES)
    bcs cache_abort
    ldy #0
    lda (cache_src),y
    inc cache_src
    bne :+
    inc cache_src+1
:   ora #0
    rts
cache_put:
    pha
    txa
    pha
    ldx cache_index
    lda cache_dst
    cmp cache_ends_lo,x
    lda cache_dst+1
    sbc cache_ends_hi,x
    bcs @bad
    pla
    tax
    pla
    ldy #0
    sta (cache_dst),y
    inc cache_dst
    bne :+
    inc cache_dst+1
:   rts
@bad:
    pla
    pla
cache_abort:
    pla
    pla
    jmp cache_fail

cache_progress: .byte 24,30,39
