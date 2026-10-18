.export __EXEHDR__ = 1
.import __MAIN_START__, __DATA_LOAD__, __DATA_SIZE__
; cc65's default header ends at BSS_LOAD-1, including un-emitted BSS
; alignment padding. End at the last initialized DATA byte instead.
.segment "EXEHDR"
.word $FFFF
.segment "MAINHDR"
.word __MAIN_START__, __DATA_LOAD__ + __DATA_SIZE__ - 1

.import __ART_LOAD__, __ART_SIZE__
.segment "ARTHDR"
.word __ART_LOAD__, __ART_LOAD__ + __ART_SIZE__ - 1

.import __LOADER_LOAD__, __LOADER_SIZE__, __LOADCONST_SIZE__
.segment "LOADHDR"
.word __LOADER_LOAD__, __LOADER_LOAD__ + __LOADER_SIZE__ + __LOADCONST_SIZE__ - 1
