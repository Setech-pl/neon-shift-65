#include "input.h"
#include "hardware.h"
static unsigned char await_release;
void input_rearm(void) { input_init();await_release=1; }
InputAction input_read(void)
{
    unsigned char t=input_tail;
    InputAction action;
    if(t==input_head)return INPUT_NONE;
    if(await_release){
        if(queued_stick[t]==15 && queued_trigger[t]==1 && queued_console[t]==7)await_release=0;
        input_tail=(t+1)&255;return INPUT_NONE;
    }
    action=input_tick(queued_stick[t],queued_trigger[t],queued_console[t]);
    input_tail=(t+1)&255;
    return action;
}
