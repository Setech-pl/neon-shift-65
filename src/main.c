#include "flow.h"
#include "display.h"
#include "input.h"
#include "sound.h"
#include "hardware.h"
#include "prototype_assets.h"
#include "scene.h"
static GameState gs;
static Flow flow;
int main(void)
{
    unsigned char clock,ticks,flags,next,old_phase,peak_fx,phase_before;
    InputAction action;
    scene_init();flow_init(&flow);input_init();hardware_init();display_init();display_view(&gs,&flow);
    clock=video_clock;
    for(;;) {
        while(clock==video_clock && input_tail==input_head) {}
        ticks=(unsigned char)(video_clock-clock);clock=video_clock;
        frame_begin();old_phase=flow.phase;flags=peak_fx=0;
        while(input_tail!=input_head) {
            phase_before=flow.phase;
            action=input_read();
            if(flow.phase==PHASE_MENU && flow.menu==6 &&
               (action==INPUT_LEFT || action==INPUT_RIGHT || action==INPUT_FIRE))
                warehouse_choice=warehouse_choice==1?2:1;
            next=flow_handle(&flow,&gs,action);flags|=next;
            if(flow.event>peak_fx)peak_fx=flow.event;
            /* Samples taken on the old screen must never become gameplay
               actions before the new board/assets are prepared. */
            if((next&FLOW_BOARD) || flow.phase!=phase_before)break;
        }
        frame_logic();
        music_enabled=flow.music;sfx_enabled=flow.sfx;
        sound_track=(flow.phase==PHASE_TITLE || flow.phase==PHASE_FINALE || flow.phase==PHASE_ERROR || flow.phase>=PHASE_CONFIG)?2:prototype_tracks[flow.scene];
        sound_effect(peak_fx);
        frame_audio();
        if((old_phase==PHASE_MENU || old_phase==PHASE_RESTART) &&
            (flow.phase==PHASE_PLAY || flow.phase==PHASE_WIN))flags|=FLOW_BOARD|FLOW_VIEW;
        if((flags&FLOW_BOARD) && (flow.phase==PHASE_PLAY || flow.phase==PHASE_WIN)) {
            if(scene_ensure()){display_board(&gs);display_hud(&gs,&flow);}
            else {flow.phase=PHASE_ERROR;flags|=FLOW_VIEW;}
            input_tail=input_head;input_rearm();
            clock=video_clock;
        }
        else if((flow.phase==PHASE_PLAY || flow.phase==PHASE_WIN) && (flags&FLOW_COUNTERS)) {
            display_changed(&gs);display_counters(&gs);
        }
        if(flags&FLOW_VIEW)display_view(&gs,&flow);
        frame_render();
        if(flow.phase==PHASE_PLAY || flow.phase==PHASE_WIN)
            display_animate(&gs,&flow,ticks,(flags&FLOW_MOTION) && peak_fx!=FX_BLOCKED);
        frame_end();
    }
    return 0;
}
