; Three standard 128B boot sectors. Private raw stream starts at sector5.
; High spare is disjoint from all XEX chunks and runtime C/CPU stacks.
.segment "CODE"
    .byte 0,3
    .word $B800,init
boot:
    lda #5
    sta sector
    lda #0
    sta sector+1
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
:
    lda remaining
    bne :+
    dec remaining+1
:
    dec remaining
    lda remaining
    ora remaining+1
    bne copy
    jmp record
complete:
    lda destination
    sta $0A                ; DOSVEC called by OS after successful bootstrap
    lda destination+1
    sta $0B
init:
    clc
    rts
byte:
    ldx position
    cpx #128
    bne ready
    lda #$31
    sta $0300
    lda #1
    sta $0301
    lda #$52
    sta $0302
    lda #$40
    sta $0303
    lda #0
    sta $0304
    lda #$BA
    sta $0305
    lda #7
    sta $0306
    lda #128
    sta $0308
    lda #0
    sta $0309
    lda sector
    sta $030A
    lda sector+1
    sta $030B
    jsr $E459
    lda $0303
    cmp #1
    bne failed
    inc sector
    bne :+
    inc sector+1
:
    ldx #0
ready:
    lda $BA00,x
    inx
    stx position
    rts
failed:
    ; OS boot error/retry path; no jump to an incomplete application.
    pla
    pla
    sec
    rts
position: .byte 0
sector: .word 5
destination=$80
remaining=$7E
