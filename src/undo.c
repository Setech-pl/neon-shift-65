#include "undo.h"

/* Ring holds the newest successful steps. 256 requires a 16-bit count. */
static unsigned char history[256];
static unsigned int count;
static unsigned int capacity = 256;
static unsigned char head;

void undo_reset(void) { count = 0; head = 0; }
unsigned int undo_count(void) { return count; }
unsigned char undo_configure(unsigned int n)
{
    if (n != 256 && n != 128 && n != 64) return 0;
    capacity = n; undo_reset(); return 1;
}
void undo_push(signed char dx, signed char dy, unsigned char pushed)
{
    unsigned char dir;
    if (dy == -1 && !dx) dir = 0;
    else if (dy == 1 && !dx) dir = 1;
    else if (dx == -1 && !dy) dir = 2;
    else if (dx == 1 && !dy) dir = 3;
    else return;
    history[head] = dir | (pushed ? 4 : 0);
    head = (unsigned char)((head + 1u) & (capacity - 1));
    if (count < capacity) ++count;
}
unsigned char undo_pop(GameState *gs)
{
    unsigned char pos, entry, px, py, nx, ny;
    signed char dx, dy, bi;
    if (!count || !gs) return 0;
    pos = (unsigned char)((head - 1u) & (capacity - 1));
    entry = history[pos];
    dx = dy = 0;
    switch (entry & 3) {
        case 0: dy = -1; break;
        case 1: dy = 1; break;
        case 2: dx = -1; break;
        default: dx = 1; break;
    }
    px = gs->player.x; py = gs->player.y;
    nx = (unsigned char)(px - dx); ny = (unsigned char)(py - dy);
    if (nx >= gs->width || ny >= gs->height || gs->map[ny][nx] == '#') return 0;
    if (entry & 4) {
        bi = level_box_at(gs, (unsigned char)(px + dx), (unsigned char)(py + dy));
        if (bi < 0) return 0;
        gs->boxes[bi].x = px; gs->boxes[bi].y = py;
        --gs->pushes;
    }
    gs->player.x = nx; gs->player.y = ny; --gs->moves;
    head = pos; --count; return 1;
}
