#include <string.h>
#include "flow.h"
#include "undo.h"
#include "prototype_assets.h"
static unsigned char start(Flow *f,GameState *g,unsigned char scene)
{
    if(scene>=PROTOTYPE_LEVEL_COUNT || prototype_levels[scene].height>10 || strlen(prototype_levels[scene].rows[0])>20) return 0;
    if(!game_start(g,&prototype_levels[scene])) return 0;
    f->scene=scene;f->pending_scene=scene;f->phase=PHASE_PLAY;f->facing=2;f->pushed=0;f->last_push=0;return 1;
}
static unsigned char adjacent(unsigned char n,signed char d,unsigned char max)
{ if(d<0)return n ? n-1 : max-1; return n+1==max ? 0 : n+1; }
void flow_init(Flow *f)
{
    f->phase=PHASE_TITLE;f->previous_phase=PHASE_PLAY;f->scene=0;f->pending_scene=0;
    f->difficulty=0;f->menu=0;f->choice=0;f->music=f->sfx=1;f->facing=2;
    f->pushed=f->event=f->last_push=0;undo_configure(256);
}
unsigned char flow_handle(Flow *f,GameState *g,InputAction act)
{
    signed char dx=0,dy=0,d;
    f->event=0;f->pushed=0;
    if(act==INPUT_NONE)return 0;
    d=act==INPUT_LEFT ? -1 : 1;
    if(f->phase==PHASE_TITLE) {
        if(act==INPUT_UP || act==INPUT_DOWN)f->menu=adjacent(f->menu,act==INPUT_UP?-1:1,4);
        else if(act==INPUT_FIRE) {
            switch(f->menu) {
                case 0:
                    undo_configure(f->difficulty==0?256:f->difficulty==1?128:64);
                    if(!start(f,g,f->scene))f->phase=PHASE_ERROR;
                    return FLOW_VIEW|FLOW_BOARD;
                case 1:f->phase=PHASE_CONTINUE;break;
                case 2:f->phase=PHASE_SCORES;break;
                case 3:f->phase=PHASE_CONFIG;f->menu=0;break;
            }
        }
        return FLOW_VIEW;
    }
    if(f->phase==PHASE_CONTINUE || f->phase==PHASE_SCORES) {
        if(act==INPUT_FIRE || act==INPUT_START){f->phase=PHASE_TITLE;f->menu=0;}
        return FLOW_VIEW;
    }
    if(f->phase==PHASE_CONFIG) {
        if(act==INPUT_START){f->phase=PHASE_TITLE;f->menu=3;}
        else if(act==INPUT_UP || act==INPUT_DOWN)f->menu=adjacent(f->menu,act==INPUT_UP?-1:1,4);
        else if(act==INPUT_LEFT || act==INPUT_RIGHT || act==INPUT_FIRE) {
            if(f->menu==0)f->difficulty=adjacent(f->difficulty,d,3);
            else if(f->menu==1)f->music^=1;
            else if(f->menu==2)f->sfx^=1;
            else if(act==INPUT_FIRE){f->phase=PHASE_TITLE;f->menu=3;}
        }
        return FLOW_VIEW;
    }
    if(f->phase==PHASE_RESTART) {
        if(act==INPUT_START || act==INPUT_OPTION)f->phase=f->previous_phase;
        else if(act==INPUT_LEFT)f->choice=0;
        else if(act==INPUT_RIGHT)f->choice=1;
        else if(act==INPUT_UP || act==INPUT_DOWN)f->choice^=1;
        else if(act==INPUT_FIRE) {
            if(f->choice) { if(!start(f,g,f->pending_scene))f->phase=PHASE_ERROR;return FLOW_VIEW|FLOW_BOARD; }
            f->pending_scene=f->scene;f->phase=f->previous_phase;
        }
        return FLOW_VIEW;
    }
    if(f->phase==PHASE_MENU) {
        if(act==INPUT_START) { f->phase=f->previous_phase;return FLOW_VIEW; }
        if(act==INPUT_UP || act==INPUT_DOWN)f->menu=adjacent(f->menu,act==INPUT_UP?-1:1,7);
        else if(act==INPUT_LEFT || act==INPUT_RIGHT || act==INPUT_FIRE) {
            switch(f->menu) {
                case 0: if(act==INPUT_FIRE)f->phase=f->previous_phase;break;
                case 1: if(act==INPUT_FIRE){f->phase=PHASE_RESTART;f->pending_scene=f->scene;f->choice=0;}break;
                case 2: if(act==INPUT_FIRE){f->phase=PHASE_RESTART;f->choice=0;}else f->pending_scene=adjacent(f->pending_scene,d,PROTOTYPE_LEVEL_COUNT);break;
                case 3: f->music^=1;break;
                case 4: f->sfx^=1;break;
                case 5: if(act==INPUT_FIRE){f->phase=PHASE_TITLE;f->menu=0;}break;
            }
        }
        return FLOW_VIEW;
    }
    if(f->phase==PHASE_FINALE || f->phase==PHASE_ERROR) {
        if(act==INPUT_FIRE){f->phase=PHASE_TITLE;f->menu=0;return FLOW_VIEW;}
        return 0;
    }
    if(act==INPUT_OPTION) {
        f->previous_phase=f->phase;f->pending_scene=f->scene;f->phase=PHASE_RESTART;f->choice=0;return FLOW_VIEW;
    }
    if(act==INPUT_START) {
        f->previous_phase=f->phase;f->pending_scene=f->scene;f->phase=PHASE_MENU;f->menu=0;return FLOW_VIEW;
    }
    if(f->phase==PHASE_WIN) {
        if(act==INPUT_SELECT && undo_pop(g)){f->phase=PHASE_PLAY;f->event=FX_UNDO;return FLOW_VIEW|FLOW_COUNTERS;}
        if(act==INPUT_FIRE) {
            if(f->scene+1>=PROTOTYPE_LEVEL_COUNT)f->phase=PHASE_FINALE;
            else if(!start(f,g,f->scene+1))f->phase=PHASE_ERROR;
            return FLOW_VIEW|FLOW_BOARD;
        }
        return 0;
    }
    if(act==INPUT_FIRE || act==INPUT_SELECT) {
        if(undo_pop(g)){f->event=FX_UNDO;return FLOW_COUNTERS;}
        return 0;
    }
    switch(act) {
        case INPUT_UP:dy=-1;f->facing=0;break;
        case INPUT_DOWN:dy=1;f->facing=1;break;
        case INPUT_RIGHT:dx=1;f->facing=2;break;
        case INPUT_LEFT:dx=-1;f->facing=3;break;
        default:return 0;
    }
    if(game_step(g,dx,dy,&f->pushed)) {
        f->last_push=f->pushed;
        if(f->pushed && level_is_solved(g)){f->phase=PHASE_WIN;f->event=FX_WIN;return FLOW_VIEW|FLOW_COUNTERS|FLOW_MOTION;}
        if(f->pushed)f->event=FX_PUSH;
        return FLOW_COUNTERS|FLOW_MOTION;
    }
    f->event=FX_BLOCKED;return FLOW_MOTION;
}
