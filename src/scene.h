#ifndef SCENE_H
#define SCENE_H
#include "game.h"
extern unsigned char warehouse_choice,scene_loaded,scene_error;
extern unsigned char scene_cells[200],scene_data[784],scene_header[32];
extern unsigned int scene_reads,scene_first_sector,scene_last_sector;
void scene_init(void);
unsigned char scene_ensure(void);
void scene_build(const GameState *g,unsigned char level);
void scene_apply(unsigned char *bank);
void scene_animate(unsigned char *bank,unsigned char ticks);
unsigned char __fastcall__ sio_read(unsigned int sector);
void asset_load_begin(void);
void asset_load_end(void);
void input_rearm(void);
#endif
