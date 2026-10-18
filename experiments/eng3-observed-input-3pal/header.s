.export __EXEHDR__=1
.import __MAIN_START__,__DATA_LOAD__,__DATA_SIZE__
.import __LOADER_LOAD__,__LOADER_SIZE__,__LOADCONST_SIZE__
.import __COMMON_LOAD__,__COMMON_SIZE__
.segment "EXEHDR"
.word $FFFF
.segment "MAINHDR"
.word __MAIN_START__,__DATA_LOAD__+__DATA_SIZE__-1
.segment "LOADHDR"
.word __LOADER_LOAD__,__LOADER_LOAD__+__LOADER_SIZE__+__LOADCONST_SIZE__-1
.segment "COMHDR"
.word __COMMON_LOAD__,__COMMON_LOAD__+__COMMON_SIZE__-1

