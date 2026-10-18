#ifndef LEVEL_H
#define LEVEL_H

#include <stdint.h>

/* Generous upper bounds; real levels are well within these. */
#define MAX_LEVEL_WIDTH   38
#define MAX_LEVEL_HEIGHT  20
#define MAX_BOXES         10

typedef struct {
    unsigned char x, y;
} Point;

/* A level as authored: plain XSB-style text rows.
 *   #  wall
 *   (space) floor
 *   .  target
 *   $  box
 *   @  player
 * level_load() parses this into a GameState.
 */
typedef struct {
    const char **rows;
    unsigned char height;
    const char *name;
} Level;

/* Live, mutable game state for the level currently being played. */
typedef struct {
    char map[MAX_LEVEL_HEIGHT][MAX_LEVEL_WIDTH]; /* static tiles only: '#', '.', ' ' */
    unsigned char width;
    unsigned char height;
    Point player;
    Point boxes[MAX_BOXES];
    unsigned char box_count;
    uint32_t moves;
    uint32_t pushes;
} GameState;

/* Validate before writing; failure leaves gs byte-for-byte unchanged.
 * Rows must be readable NUL-terminated strings, width <= MAX_LEVEL_WIDTH. */
unsigned char level_load(GameState *gs, const Level *lvl);

/* Attempts to move the player by (dx, dy), pushing a box if one is in the
 * way and the cell behind it is free. Returns 1 if the move happened, 0 if
 * it was blocked. When it returns 1, *pushed is set to 1 if a box moved as
 * part of this step (0 otherwise) - callers use this to record undo history
 * and trigger the push sound. */
unsigned char level_try_move(GameState *gs, signed char dx, signed char dy, unsigned char *pushed);

unsigned char level_is_solved(const GameState *gs);
signed char level_box_at(const GameState *gs, unsigned char x, unsigned char y);

#endif
