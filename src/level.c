#include <string.h>
#include "level.h"

/* Parser-owned bounded BFS scratch; no C-stack allocation and no ISR access.
 * Ignore crates for topology validation. Each floor cell is enqueued once. */
static unsigned char connected[MAX_LEVEL_HEIGHT][MAX_LEVEL_WIDTH];
static Point frontier[MAX_LEVEL_WIDTH * MAX_LEVEL_HEIGHT];

unsigned char level_load(GameState *gs, const Level *lvl)
{
    unsigned char x, y, width, len, players, boxes, targets, px, py, nx, ny, direction;
    unsigned int head, tail;
    static const signed char dx[4] = {-1,1,0,0};
    static const signed char dy[4] = {0,0,-1,1};
    char c;
    if (!gs || !lvl || !lvl->rows || lvl->height < 3 ||
        lvl->height > MAX_LEVEL_HEIGHT) return 0;
    width = players = boxes = targets = px = py = 0;
    /* First pass is bounded even for a row longer than 255 characters. */
    for (y = 0; y < lvl->height; ++y) {
        if (!lvl->rows[y]) return 0;
        for (len = 0; len <= MAX_LEVEL_WIDTH; ++len) {
            if (!lvl->rows[y][len]) break;
        }
        if (len < 3 || len > MAX_LEVEL_WIDTH) return 0;
        if (!y) width = len;
        if (len != width) return 0;
        for (x = 0; x < width; ++x) {
            c = lvl->rows[y][x];
            if (c != '#' && c != ' ' && c != '.' && c != '$' &&
                c != '*' && c != '@' && c != '+') return 0;
            if ((!x || !y || x == width-1 || y == lvl->height-1) && c != '#')
                return 0;
            if (c == '@' || c == '+') { if (++players > 1) return 0; px = x; py = y; }
            if (c == '$' || c == '*') { if (++boxes > MAX_BOXES) return 0; }
            if (c == '.' || c == '*' || c == '+') {
                if (++targets > MAX_BOXES) return 0;
            }
        }
    }
    if (players != 1 || !boxes || boxes != targets) return 0;
    memset(connected, 0, sizeof(connected));
    frontier[0].x=px; frontier[0].y=py; connected[py][px]=1;
    head=0; tail=1;
    while(head<tail) {
        px=frontier[head].x; py=frontier[head++].y;
        for(direction=0;direction<4;++direction) {
            nx=px+dx[direction]; ny=py+dy[direction];
            /* The validated wall perimeter bounds every queued neighbour. */
            if(!connected[ny][nx] && lvl->rows[ny][nx]!='#') {
                connected[ny][nx]=1;
                frontier[tail].x=nx; frontier[tail++].y=ny;
            }
        }
    }
    for (y = 1; y < lvl->height-1; ++y)
        for (x = 1; x < width-1; ++x)
            if (lvl->rows[y][x] != '#' && !connected[y][x]) return 0;
    /* Commit only after the complete level has passed validation. */
    memset(gs, 0, sizeof(*gs));
    memset(gs->map, '#', sizeof(gs->map));
    gs->width = width;
    gs->height = lvl->height;
    for (y = 0; y < gs->height; ++y) {
        for (x = 0; x < width; ++x) {
            c = lvl->rows[y][x];
            /* Explicit branches: cc65 V2.18 -O miscompiled a nested ternary
             * here by reloading c from the wrong software-stack offset. */
            if (c == '#') gs->map[y][x] = '#';
            else if (c == '.' || c == '*' || c == '+') gs->map[y][x] = '.';
            else gs->map[y][x] = ' ';
            if (c == '$' || c == '*') {
                gs->boxes[gs->box_count].x = x;
                gs->boxes[gs->box_count++].y = y;
            }
            if (c == '@' || c == '+') {
                gs->player.x = x; gs->player.y = y;
            }
        }
    }
    return 1;
}

signed char level_box_at(const GameState *gs, unsigned char x, unsigned char y)
{
    unsigned char i;
    const Point *box=gs->boxes;
    for (i = 0; i < gs->box_count; ++i,++box) {
        if (box->x == x && box->y == y) return (signed char)i;
    }
    return -1;
}

unsigned char level_try_move(GameState *gs, signed char dx, signed char dy, unsigned char *pushed)
{
    unsigned char nx, ny, bx, by;
    signed char bi, bi2;

    if (!gs || !pushed) return 0;
    *pushed = 0;
    if (!((dx == 0 && (dy == -1 || dy == 1)) ||
          (dy == 0 && (dx == -1 || dx == 1)))) return 0;
    if (!gs->width || gs->width > MAX_LEVEL_WIDTH ||
        !gs->height || gs->height > MAX_LEVEL_HEIGHT ||
        !gs->box_count || gs->box_count > MAX_BOXES) return 0;

    /* Unsigned wraparound is intentional here: if the player is at x=0 and
     * dx=-1, nx wraps to 255, which is always >= width and therefore
     * correctly rejected as out-of-bounds below. */
    nx = (unsigned char)(gs->player.x + dx);
    ny = (unsigned char)(gs->player.y + dy);

    if (nx >= gs->width || ny >= gs->height) {
        return 0;
    }
    if (gs->map[ny][nx] == '#') {
        return 0;
    }

    bi = level_box_at(gs, nx, ny);
    if (bi >= 0) {
        bx = (unsigned char)(nx + dx);
        by = (unsigned char)(ny + dy);
        if (bx >= gs->width || by >= gs->height) {
            return 0;
        }
        if (gs->map[by][bx] == '#') {
            return 0;
        }
        bi2 = level_box_at(gs, bx, by);
        if (bi2 >= 0) {
            return 0; /* another box blocks the push */
        }
        gs->boxes[bi].x = bx;
        gs->boxes[bi].y = by;
        gs->pushes++;
        *pushed = 1;
    }

    gs->player.x = nx;
    gs->player.y = ny;
    gs->moves++;
    return 1;
}

unsigned char level_is_solved(const GameState *gs)
{
    unsigned char i;
    const Point *box;
    static const unsigned int offsets[MAX_LEVEL_HEIGHT]={0,38,76,114,152,190,228,266,304,342,380,418,456,494,532,570,608,646,684,722};
    const char *map;
    if (!gs || !gs->width || gs->width > MAX_LEVEL_WIDTH ||
        !gs->height || gs->height > MAX_LEVEL_HEIGHT ||
        !gs->box_count || gs->box_count > MAX_BOXES) return 0;
    box=gs->boxes;map=&gs->map[0][0];
    for (i = 0; i < gs->box_count; ++i,++box) {
        if (box->x >= gs->width || box->y >= gs->height) return 0;
        if (map[offsets[box->y]+box->x] != '.') return 0;
    }
    return 1;
}
