#include "game.h"
#include "undo.h"
unsigned char game_start(GameState *gs, const Level *level)
{
    if (!level_load(gs, level)) return 0;
    undo_reset(); return 1;
}
unsigned char game_step(GameState *gs, signed char dx, signed char dy, unsigned char *pushed)
{
    if (!level_try_move(gs, dx, dy, pushed)) return 0;
    undo_push(dx, dy, *pushed); return 1;
}
