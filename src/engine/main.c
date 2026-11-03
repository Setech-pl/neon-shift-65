#include <string.h>
#include "candidate.h"
#include "undo.h"
void menu_select(void);
unsigned char splash_run(void);
static void startup(void);
extern volatile unsigned char poll_ready;
extern unsigned char input_pending;
void __fastcall__ input_wait(unsigned char clock);
GameState gs;
unsigned char phase,scene,facing=2,selected,previous_phase;
static unsigned char startup_pending=1;
static unsigned char failed_kind,music_ready,pending_scene,game_valid,failed_resume;
static unsigned char prepare(unsigned char n)
{
    GameState *candidate=(GameState *)0xb680;
    /* BFS is$A000-$A8E7; candidate$B680-$B998. ISR consumers and DMA stop
       before parser, also on restart. No graphics cache survives overlay. */
    asset_load_begin();loaded=0;
    if(!level_load(candidate,&prototype_levels[n])){error=7;asset_load_end();return 0;}
    failed_kind=n+1;failed_resume=0;
    if(!load_package(failed_kind))return 0;
    memcpy(&gs,candidate,sizeof(gs));undo_reset();scene=n;facing=2;
#ifdef STRESS
    if(scene==1){gs.moves=4294967200UL;gs.pushes=4294967200UL;}
#endif
#ifdef CARRY
    if(scene==1){gs.moves=3999999999UL;gs.pushes=3999999999UL;}
#endif
#ifdef COUNTER_START
    if(scene==1){gs.moves=COUNTER_START;gs.pushes=COUNTER_START;}
#endif
#ifdef WRAP
    if(scene==1){gs.moves=4294967295UL;gs.pushes=4294967295UL;}
#endif
    game_valid=1;phase=1;show_play();return 1;
}
static unsigned char resume(void)
{failed_kind=scene+1;failed_resume=1;if(!load_package(failed_kind))return 0;phase=1;show_play();return 1;}
static void title(void)
{
    if(!music_ready){
        failed_kind=5;
        if(!load_package(5)){phase=6;show_ui();return;}
        music_ready=1;
    }
    failed_kind=4;
    if(!load_package(4)){phase=6;show_ui();return;}
    if(startup_pending){music_enabled=music_ready;startup_pending=0;}
    phase=0;show_menu();
}
static void startup(void)
{
    music_enabled=0;
    if(!music_ready){failed_kind=5;if(!load_package(5))goto fail;music_ready=1;}
    failed_kind=4;if(!load_package(4))goto fail;
    music_enabled=1;startup_pending=0;phase=0;show_menu();input_rearm();return;
fail:
    phase=6;show_ui();
}
int main(void)
{
    unsigned char clock,moved,pushed,was;
    signed char dx,dy;
    InputAction action;
    hardware_init();input_init();undo_configure(256);
    music_enabled=0;phase=0;scene=0;selected=0;
#if defined(STRESS) || defined(CARRY) || defined(WRAP) || defined(COUNTER_START)
    scene=1;
#endif
#ifdef DIM
    palette_dim=1;
#endif
    failed_kind=5;
    startup();
    clock=input_clock;
    for(;;){
        if(!input_pending)input_wait(clock);
        clock=input_clock;frame_begin();moved=pushed=0;
        action=INPUT_NONE;
        do{action=input_read();if(action!=INPUT_NONE)break;}while(poll_ready || input_tail!=input_head);
        was=phase;
        if((phase==1 || phase==2) && action!=INPUT_NONE)hud_invalidate();
        if(phase==0){
            if(action==INPUT_UP)selected=(selected+3)%4;
            if(action==INPUT_DOWN)selected=(selected+1)%4;
            if(action==INPUT_UP || action==INPUT_DOWN)menu_select();
            if(action==INPUT_FIRE){
                if(selected==0){if(!prepare(scene)){phase=6;show_ui();}}
                else if(selected==1){if(!(game_valid?resume():prepare(scene))){phase=6;show_ui();}}
                else if(selected==2){phase=9;show_ui();}
                else{previous_phase=0;phase=7;show_ui();}
            }
        }else if(phase==1 || phase==2){
            if(action==INPUT_START){pending_scene=scene;phase=3;show_ui();}
            else if(action==INPUT_OPTION){if(!prepare(scene)){phase=6;show_ui();}}
            else if(action==INPUT_FIRE || action==INPUT_SELECT){moved=undo_pop(&gs);if(moved){phase=1;sound_request=2;}}
            else{
                dx=dy=0;
                if(action==INPUT_UP){dy=-1;facing=0;}if(action==INPUT_DOWN){dy=1;facing=1;}
                if(action==INPUT_RIGHT){dx=1;facing=2;}if(action==INPUT_LEFT){dx=-1;facing=3;}
                if(dx || dy){moved=game_step(&gs,dx,dy,&pushed);sound_request=moved?(pushed?3:0):1;}
            }
        }else if(phase==3){
            if(action==INPUT_START){phase=1;show_play();}
            else if(action==INPUT_FIRE){previous_phase=3;phase=7;show_ui();}
            else if(action==INPUT_LEFT || action==INPUT_RIGHT){pending_scene=(pending_scene+(action==INPUT_LEFT?2:1))%3;show_ui();}
            else if(action==INPUT_OPTION){if(!prepare(pending_scene)){phase=6;show_ui();}}
            else if(action==INPUT_SELECT)title();
        }else if(phase==7){
            if(action==INPUT_LEFT || action==INPUT_RIGHT)music_enabled=music_ready && !music_enabled;
            else if(action==INPUT_FIRE)sfx_enabled^=1;
            else if(action==INPUT_START){phase=previous_phase;if(phase==0)show_menu();else show_ui();}
        }else if(phase==9){if(action==INPUT_START || action==INPUT_FIRE)title();}
        else if(phase==6){
            if(action==INPUT_FIRE){
                if(startup_pending || failed_kind==6 || failed_kind==5)startup();
                else if(failed_kind==4)title();
                else if(!(failed_resume?resume():prepare(failed_kind-1))){phase=6;show_ui();}
            }else if(action==INPUT_START)title();
        }
        frame_logic();frame_audio();
        if(phase==1 || phase==2){
            if(moved)display_changed(pushed);
            if(moved)display_animate(moved|(pushed<<1)); /* Robot publication precedes HUD composition. */
            if(moved){hud_undo=(action==INPUT_FIRE || action==INPUT_SELECT);display_counters();}
            /* Victory scan can be expensive on ten boxes. Publish the robot
               first; only a push changes dock occupancy. */
            if(moved && pushed && hud_state_docks==gs.box_count){phase=2;sound_request=4;}
            hud_budget_clock=clock;hud_work();
        }
        if(phase!=was && !((phase==1 || phase==2) && (was==1 || was==2))){input_tail=input_head;input_rearm();clock=input_clock;}
        frame_render();frame_end();
    }
    return 0;
}
