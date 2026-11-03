; This 256-byte reservation is outside all package destinations and boot code.
; Shared renderer uses32 bytes at x32..287, two identical native scanlines.
.segment "CODE"
render:
    ldx #0
@cell:
    lda #0
    sta $1760,x
    sta $1788,x
    cpx #4
    bcc @next
    cpx #36
    bcs @next
    txa
    sec
    sbc #4
    cmp $17d4
    lda #$55
    bcs :+
    lda #$ff
:   sta $1760,x
    sta $1788,x
@next:
    inx
    cpx #40
    bne @cell
    rts
.res $80-(*-render),$ea
update:
    ; Multiplication done*31 with16-bit accumulator; denominator actual work.
    ; Preserve boot stream X/Y and ZP by using private scratch $17d5..17db.
    pha
    txa
    pha
    tya
    pha
    lda #0
    sta $17d5
    sta $17d6
    ldx #31
@mul:
    clc
    lda $17d5
    adc $17d0
    sta $17d5
    lda $17d6
    adc $17d1
    sta $17d6
    dex
    bne @mul
    ldx #0
@div:
    lda $17d5
    sec
    sbc $17d2
    tay
    lda $17d6
    sbc $17d3
    bcc @ready
    sta $17d6
    sty $17d5
    inx
    cpx #31
    bcc @div
@ready:
    cpx $17d4
    bcc :+
    stx $17d4
:   jsr render
    pla
    tay
    pla
    tax
    pla
    rts
