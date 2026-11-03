#include "candidate.h"
/* ENG4: observation is a snapshot, never a queue of gameplay actions. */
extern volatile unsigned char eng4_edges,eng4_buttons;
extern unsigned char poll_stick,poll_trigger,poll_console;
extern unsigned char poll_last_stick;
#pragma zpsym ("poll_stick")
#pragma zpsym ("poll_trigger")
#pragma zpsym ("poll_console")
#pragma zpsym ("poll_last_stick")
extern volatile unsigned char critical_guard;
unsigned char input_pending; /* compatibility symbol; no action FIFO */
unsigned char eng4_busy,eng4_settling,eng4_ready_clock;
unsigned char eng4_direction,eng4_repeat_clock,eng4_repeat_delay;
static unsigned char await_release;
void input_init(void)
{
    eng4_busy=eng4_settling=input_pending=0;
    eng4_direction=0;eng4_repeat_clock=input_clock;eng4_repeat_delay=0;
    eng4_edges=0;eng4_buttons=0;await_release=1;
}
void input_rearm(void) { input_init(); }
void eng4_accepted(void) { eng4_busy=1;eng4_settling=0; }
InputAction input_read(void)
{
    unsigned char dir=0,e;
    input_probe();
    poll_last_stick=poll_stick;
    if(await_release){
        eng4_edges=0;
        if(poll_stick==15 && poll_trigger==1 && poll_console==7)await_release=0;
        return INPUT_NONE;
    }
    if(!(poll_stick&1))dir=INPUT_UP;
    else if(!(poll_stick&2))dir=INPUT_DOWN;
    else if(!(poll_stick&4))dir=INPUT_LEFT;
    else if(!(poll_stick&8))dir=INPUT_RIGHT;
    if(dir!=eng4_direction){eng4_direction=dir;eng4_repeat_delay=0;}
    if(eng4_busy){
        if(publish_pending || critical_guard || hud_dirty || hud_pending){eng4_settling=0;return INPUT_NONE;}
        if(!eng4_settling){eng4_ready_clock=input_clock;eng4_settling=1;return INPUT_NONE;}
        /* HUD committed at VBI also gets a complete visible raster. */
        if(input_clock==eng4_ready_clock)return INPUT_NONE;
        eng4_busy=eng4_settling=0;
    }
    /* A native atomic exchange avoids losing an edge interrupted by NMI. */
    e=eng4_take_edges();
    if(e&4)return INPUT_OPTION;
    if(e&8)return INPUT_START;
    if(e&2)return INPUT_SELECT;
    if(e&1)return INPUT_FIRE;
    if(!dir)return INPUT_NONE;
    if(eng4_repeat_delay && (unsigned char)(input_clock-eng4_repeat_clock)<eng4_repeat_delay)return INPUT_NONE;
    eng4_repeat_clock=input_clock;
    eng4_repeat_delay=eng4_repeat_delay?5:14;
    return (InputAction)dir;
}
