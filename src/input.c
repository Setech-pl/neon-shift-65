#include "input.h"
static unsigned char previous_buttons;
static InputAction previous_direction;
static unsigned char repeat_frames;
void input_init(void) { previous_buttons=15; previous_direction=INPUT_NONE; repeat_frames=0; }
InputAction input_tick(unsigned char stick,unsigned char trigger,unsigned char console)
{
    unsigned char buttons,edges;
    InputAction dir=INPUT_NONE;
    buttons=(!trigger ? 1 : 0) | (!(console&2) ? 2 : 0) |
            (!(console&4) ? 4 : 0) | (!(console&1) ? 8 : 0);
    edges=buttons & (unsigned char)~previous_buttons;
    previous_buttons=buttons;
    if(edges&4) return INPUT_OPTION;
    if(edges&8) return INPUT_START;
    if(edges&2) return INPUT_SELECT;
    if(edges&1) return INPUT_FIRE;
    if(!(stick&1))dir=INPUT_UP;
    else if(!(stick&2))dir=INPUT_DOWN;
    else if(!(stick&4))dir=INPUT_LEFT;
    else if(!(stick&8))dir=INPUT_RIGHT;
    if(dir!=previous_direction) {
        previous_direction=dir;repeat_frames=14;return dir;
    }
    if(dir==INPUT_NONE)return INPUT_NONE;
    if(repeat_frames && --repeat_frames)return INPUT_NONE;
    repeat_frames=5;return dir;
}
