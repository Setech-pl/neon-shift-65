destination=$80
remaining=$7e
; Three OS boot sectors. Splash-only records end in early entry sentinel.
.segment "CODE"
    .byte 0,3
    .word $9800,init
boot:
    lda #$31
    sta $0300
    lda #1
    sta $0301
    lda #$52
    sta $0302
    lda #$40
    sta $0303
    lda #$80
    sta $0304
    lda #$bf
    sta $0305
    lda #7
    sta $0306
    lda #128
    sta $0308
    lda #0
    sta $0309
    lda #0
    sta $22f
    sta $17de
    sta boot_phase
    sta sector+1
    lda #5
    sta sector
    lda #128
    sta position
record:
    jsr byte
    sta destination
    jsr byte
    sta destination+1
    jsr byte
    sta remaining
    jsr byte
    sta remaining+1
    ora remaining
    beq complete
copy:
    jsr byte
    ldy #0
    sta (destination),y
    inc destination
    bne :+
    inc destination+1
:   lda remaining
    bne :+
    dec remaining+1
:   dec remaining
    lda remaining
    ora remaining+1
    bne copy
    jmp record
complete:
    lda boot_phase
    cmp #2
    beq final
    inc boot_phase
    lda destination
    sta call+1
    lda destination+1
    sta call+2
call:
    jsr $0600
    jmp record
final:
    lda destination
    sta $0a
    lda destination+1
    sta $0b
init:
    clc
    rts
byte:
    ldx position
    cpx #128
    bne ready
read_sector:
    lda #$40
    sta $0303
    lda sector
    sta $030a
    lda sector+1
    sta $030b
    jsr $e459
    lda $0303
    cmp #1
    bne failed
    lda boot_phase
    beq advance
    inc $17d0
    bne :+
    inc $17d1
:   ; Progress computed by safe helper at $bf00 once its record is loaded.
    lda $17de
    beq advance
    jsr update
advance:
    inc sector
    bne :+
    inc sector+1
:   ldx #0
ready:
    lda $bf80,x
    inx
    stx position
    rts
failed:
    lda $17de
    beq read_sector
    ldx #18
@error:
    lda $1720,x
    sta $1744,x
    dex
    bpl @error
    jsr $9240
    jmp read_sector
position:.byte 0
sector:.word 5
boot_phase:.byte 0
.export progress_stride
progress_stride:.byte 1

render:
    ldx #31
@cell:
    txa
    cmp $17d4
    lda #$55
    bcs :+
    lda #$ff
:   sta $176c,x
    sta $1794,x
    dex
    bpl @cell
    rts
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
