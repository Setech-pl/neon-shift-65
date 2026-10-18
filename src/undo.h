#ifndef UNDO_H
#define UNDO_H

#include "level.h"

/* Clears the undo history. Call whenever a level is (re)loaded. */
void undo_reset(void);
/* EASY 256, MEDIUM 128, HARD 64. Changing capacity clears history. */
unsigned char undo_configure(unsigned int capacity);
unsigned int undo_count(void);

/* Records one completed move so it can later be reversed. dx/dy must match
 * what was just passed to level_try_move(), and pushed must match the value
 * level_try_move() wrote back through its output parameter. */
void undo_push(signed char dx, signed char dy, unsigned char pushed);

/* Reverses the most recently recorded move in gs (player position, and the
 * pushed box if any, plus the moves/pushes counters). Returns 1 if a move
 * was undone, 0 if the history is empty. */
unsigned char undo_pop(GameState *gs);

#endif
