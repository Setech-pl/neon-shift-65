#include "input.h"
#include "hardware.h"
extern unsigned char input_heartbeat,input_pending;
InputAction input_next(void);
extern unsigned char poll_stick,poll_trigger,poll_console;
extern volatile unsigned char poll_ready;
extern unsigned char poll_fence;
extern volatile unsigned char deferred_epoch;
extern unsigned char deferred_seen;
extern unsigned char poll_last_stick,poll_last_trigger,poll_last_console;
#pragma zpsym ("poll_stick")
#pragma zpsym ("poll_trigger")
#pragma zpsym ("poll_console")
#pragma zpsym ("poll_fence")
#pragma zpsym ("deferred_epoch")
#pragma zpsym ("deferred_seen")
#pragma zpsym ("poll_last_stick")
#pragma zpsym ("poll_last_trigger")
#pragma zpsym ("poll_last_console")
unsigned char input_probe(void);
static unsigned char await_release;
void input_rearm(void) { poll_ready=0;input_init();await_release=1; }
InputAction input_read(void)
{
    unsigned char t=input_tail,stick,trigger,console,e;
    InputAction action;
    if(input_pending)return input_next();
    input_heartbeat=1;
    /* The capture fence separates older ISR tuples from later ones.
       Consume the immutable foreground tuple exactly once at that fence. */
    if(poll_ready && t==poll_fence){
        e=deferred_epoch;
        input_heartbeat=(e!=deferred_seen);deferred_seen=e;
        stick=poll_stick;trigger=poll_trigger;console=poll_console;
        poll_ready=0;
    }else if(t!=input_head){
        stick=queued_stick[t];trigger=queued_trigger[t];console=queued_console[t];
        input_tail=(t+1)&127;
    }else{
        if(!input_probe())return INPUT_NONE;
        if(!poll_ready || input_tail!=poll_fence)return INPUT_NONE;
        e=deferred_epoch;
        input_heartbeat=(e!=deferred_seen);deferred_seen=e;
        stick=poll_stick;trigger=poll_trigger;console=poll_console;
        poll_ready=0;
    }
    poll_last_stick=stick;poll_last_trigger=trigger;poll_last_console=console;
    if(await_release){
        if(stick==15 && trigger==1 && console==7)await_release=0;
        return INPUT_NONE;
    }
    action=input_tick(stick,trigger,console);
    return action;
}
