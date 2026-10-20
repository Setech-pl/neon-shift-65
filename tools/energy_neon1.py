"""Energy-only PMG installation. P0/P1, DLI, palette and game overlay untouched."""
def artwork(background):
    previous = background.image
    def image(level):
        p = previous(level)
        # Recess the existing cabinet door behind the luminous tube.
        background.c.rect(p, 4, 70, 7, 40, 0)
        background.p = p
        return p
    background.image = image


def install(source):
    f = source/'validate.c'
    s = f.read_text().replace('DESC[6]==1?3:0', 'DESC[6]==1?4:0')
    s = s.replace('}else if(position!=0x8800+22*40+17 || DESC[at+2]!=50)return 0;',
                  '}else if(position!=(i==2?0x8800+22*40+17:0x8800+22*40+8) || DESC[at+2]!=(i==2?50:13))return 0;')
    f.write_text(s)
    f = source/'hardware.s'
    s = f.read_text()
    # Initialization runs with DMA and ambient stopped. No raster multiplexing.
    s = s.replace('_pmg_on:\n', '_pmg_on:\n    jsr neon_prepare\n')
    s = s.replace('lda #2                     ; players only, no missiles', 'lda #3                     ; players + M2; other missile masks zero')
    s = s.replace('lda #$3a', 'jsr neon_dma')
    s = s.replace('    ; Transposed descriptors', '    jsr neon_tick\n    ; Transposed descriptors')
    s += '''
.segment "BSS"
neon_clock:.res 1
neon_head:.res 1
cable_head:.res 1
.segment "CODE"
neon_dma:
    lda $9de6
    cmp #1
    bne @plain
    lda #$3e
    rts
@plain:
    lda #$3a
    rts
neon_prepare:
    lda #0
    sta neon_clock
    sta neon_head
    sta $d00c
    lda #64
    sta cable_head
    lda $9de6
    cmp #1
    bne @done
    lda #52
    sta $d002
    sta $d003
    lda #$9e
    sta $d014
    sta $02c2
    lda #$96
    sta $d015
    sta $02c3
    ldx #31
@tube:
    lda neon_core,x
    sta $ae00+104,x
    lda neon_shell,x
    sta $af00+104,x
    dex
    bpl @tube
    lda #$30
    sta $ab00+57
    sta $ab00+58
    lda #64
    sta $d006
@done:rts
neon_tick:
    lda $9de6
    cmp #1
    bne @done
    inc neon_clock
    lda neon_clock
    and #1
    bne @tube
    inc cable_head
    lda cable_head
    cmp #192
    bcc :+
    lda #64
    sta cable_head
:   sta $d006
@tube:
    lda neon_clock
    and #3
    bne @done
    ldx neon_head
    ldy #3
@restore:
    lda neon_core,x
    sta $ae00+104,x
    inx
    txa
    and #31
    tax
    dey
    bpl @restore
    inc neon_head
    lda neon_head
    and #31
    sta neon_head
    tax
    ldy #3
@highlight:
    lda neon_shell,x
    sta $ae00+104,x
    inx
    txa
    and #31
    tax
    dey
    bpl @highlight
@done:rts
.segment "RODATA"
; Normal player width: eight color clocks, no stretched block silhouette.
neon_core:
    .byte $06,$06,$0c,$0c,$0c,$18,$18,$18
    .byte $30,$30,$30,$60,$60,$7e,$7e,$06
    .byte $06,$0c,$0c,$0c,$18,$18,$18,$30
    .byte $30,$30,$60,$60,$40,$40,$00,$00
neon_shell:
    .byte $0f,$0f,$1e,$1e,$1e,$3c,$3c,$3c
    .byte $78,$78,$78,$f0,$f0,$ff,$ff,$0f
    .byte $0f,$1e,$1e,$1e,$3c,$3c,$3c,$78
    .byte $78,$78,$f0,$f0,$e0,$e0,$40,$00
'''
    f.write_text(s)
