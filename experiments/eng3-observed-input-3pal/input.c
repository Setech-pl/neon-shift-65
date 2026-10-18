#include "input.h"
unsigned char input_heartbeat=1;
/* Foreground owns the remaining requests of ONE immutable observation.
   Drain before acquiring another tuple; ISR never reads this mask. */
unsigned char input_pending;
extern unsigned char phase;
InputAction input_next(void)
{
    if(input_pending&3){input_pending&=8;return INPUT_FIRE;}
    input_pending=0;return INPUT_START;
}
static unsigned char previous_buttons;
static InputAction previous_direction;
static unsigned char repeat_frames,repeat_armed;
void input_init(void) { input_pending=0;previous_buttons=15; previous_direction=INPUT_NONE; repeat_frames=repeat_armed=0; }
InputAction input_tick(unsigned char stick,unsigned char trigger,unsigned char console)
{
    unsigned char buttons,edges;
    InputAction dir=INPUT_NONE;
    buttons=(!trigger ? 1 : 0) | (!(console&2) ? 2 : 0) |
            (!(console&4) ? 4 : 0) | (!(console&1) ? 8 : 0);
    edges=buttons & (unsigned char)~previous_buttons;
    previous_buttons=buttons;
    if(edges&4) return INPUT_OPTION;
    if(phase==1 || phase==2)input_pending=edges&11;
    else {
        if(edges&8) return INPUT_START;
        if(edges&2) return INPUT_SELECT;
        if(edges&1) return INPUT_FIRE;
    }
    if(!(stick&1))dir=INPUT_UP;
    else if(!(stick&2))dir=INPUT_DOWN;
    else if(!(stick&4))dir=INPUT_LEFT;
    else if(!(stick&8))dir=INPUT_RIGHT;
    if(dir!=previous_direction) {
        previous_direction=dir;repeat_frames=14;repeat_armed=input_heartbeat;goto result;
    }
    if(dir!=INPUT_NONE && input_heartbeat){
        if(!repeat_armed)repeat_armed=1;
        else if(!repeat_frames || !--repeat_frames){repeat_frames=5;goto result;}
    }
    dir=INPUT_NONE;
result:
    if(dir!=INPUT_NONE)return dir;
    return input_pending?input_next():INPUT_NONE;
}
