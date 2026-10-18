#ifndef FLOW_H
#define FLOW_H
#include "game.h"
#include "input.h"
enum { PHASE_TITLE,PHASE_PLAY,PHASE_WIN,PHASE_MENU,PHASE_RESTART,PHASE_FINALE,PHASE_ERROR,PHASE_CONFIG,PHASE_CONTINUE,PHASE_SCORES };
enum { FX_NONE,FX_BLOCKED,FX_UNDO,FX_PUSH,FX_WIN };
#define FLOW_VIEW 1
#define FLOW_BOARD 2
#define FLOW_MOTION 4
#define FLOW_COUNTERS 8
/* Pure C product flow, used unchanged in the Atari main loop and host tests. */
typedef struct {
 unsigned char phase,previous_phase,scene,pending_scene,difficulty,menu,choice;
 unsigned char music,sfx,facing,pushed,event,last_push;
} Flow;
void flow_init(Flow *flow);
unsigned char flow_handle(Flow *flow,GameState *gs,InputAction action);
#endif
