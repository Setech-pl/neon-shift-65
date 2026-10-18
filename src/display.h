#ifndef DISPLAY_H
#define DISPLAY_H
#include "flow.h"
void display_init(void);
void display_board(const GameState *gs);
void display_changed(const GameState *gs);
void display_hud(const GameState *gs,const Flow *flow);
void display_counters(const GameState *gs);
void display_view(const GameState *gs,const Flow *flow);
void display_animate(const GameState *gs,const Flow *flow,unsigned char ticks,unsigned char animate);
extern volatile unsigned int render_tile_writes;
extern volatile unsigned int render_full_boards;
#endif
