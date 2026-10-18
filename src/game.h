#ifndef GAME_H
#define GAME_H
#include "level.h"
/* Shared by Atari frontend and host replay. */
unsigned char game_start(GameState *gs, const Level *level);
unsigned char game_step(GameState *gs, signed char dx, signed char dy, unsigned char *pushed);
#endif
