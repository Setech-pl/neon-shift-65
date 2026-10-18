#include <string.h>
#include "campaign.h"
#include "undo.h"
void menu_select(void);
void __fastcall__ input_wait(unsigned char clock);
extern unsigned char eng4_busy;
GameState gs;
unsigned char phase,scene,facing=2,selected,previous_phase;
static unsigned char music_ready,game_valid,failed_kind,startup_pending=1,failed_scene,failed_restore,failed_resume;
#define save_begin asset_load_begin
static void play(void)
{
    phase=level_is_solved(&gs)?2:1;show_play();
}
static unsigned char prepare(unsigned char n,unsigned char restore)
{
    asset_load_begin();loaded=0;failed_kind=1;failed_scene=n;failed_restore=restore;failed_resume=0;
    if(!board_load(n)){asset_load_end();return 0;}
    if(!load_package(1))return 0;
    memcpy(&gs,(void *)0xb680,sizeof(gs));undo_reset();scene=n;facing=2;save_complete=0;
    if(restore && !save_apply()){save_error=2;return 0;}
    game_valid=1;
    if(save_complete){phase=10;show_ui();}else play();
    return 1;
}
/* Menu and test-media cold starts share both semantic fallback attempts. */
static void continue_saved(unsigned char fresh)
{
    save_begin();
    if(!save_scan()){
        asset_load_end();
        if(save_error==1 && fresh<60){
            save_error=0;
            if(prepare(fresh,0))return;
        }else{phase=8;show_ui();return;}
    }else{
        if(prepare(save_level(),1))return;
        if(!error && save_previous() && prepare(save_level(),1))return;
    }
    phase=error?6:8;show_ui();
}
static unsigned char resume(void)
{
    if(save_complete){phase=10;show_ui();return 1;}
    failed_kind=1;failed_scene=scene;failed_resume=1;
    memcpy((void *)0xb680,&gs,sizeof(gs));level_number=scene;
    /* Only a completely validated game package sets loaded=1. Pause/config
     * overwrite HUD/screen, rebuilt by play(), but no game resource section.
     * Every package load clears loaded before its first read; menu uses 4. */
    if(loaded!=1 && !load_package(1))return 0;
    play();return 1;
}
static void title(void)
{
    if(!music_ready){failed_kind=5;if(!load_package(5)){phase=6;show_ui();return;}music_ready=1;}
    failed_kind=4;if(!load_package(4)){phase=6;show_ui();return;}
    phase=0;show_menu();
}
static void startup(void)
{
    music_enabled=0;title();
    if(phase!=6){music_enabled=sfx_enabled=1;startup_pending=0;input_rearm();}
}
int main(void)
{
    unsigned char clock,moved,pushed,was;
    signed char dx,dy;
    InputAction action;
    hardware_init();input_init();undo_configure(256);phase=scene=selected=0;save_error=save_valid=save_complete=0;startup();clock=input_clock;
    for(;;){
        input_wait(clock);clock=input_clock;frame_begin();moved=pushed=0;action=input_read();was=phase;
        if((phase==1 || phase==2) && action!=INPUT_NONE)hud_invalidate();
        if(phase==0){
            if(action==INPUT_UP)selected=(selected+3)%4;
            if(action==INPUT_DOWN)selected=(selected+1)%4;
            if(action==INPUT_UP || action==INPUT_DOWN)menu_select();
            if(action==INPUT_FIRE){
                if(selected==0){if(!prepare(0,0)){phase=6;show_ui();}}
                else if(selected==1){
                    if(game_valid){if(!resume()){phase=6;show_ui();}}
                    else continue_saved(60);
                }else if(selected==2){phase=9;show_ui();}
                else{previous_phase=0;phase=7;show_ui();}
            }
        }else if(phase==1 || phase==2){
            /* Establish FIRE intent before any state mutation, including the
             * first DLI inside game_step/undo_pop. Rejected attempts release
             * this guard below; accepted actions retain the raster barrier. */
            if(action==INPUT_START){phase=3;show_ui();}
            else if(action==INPUT_OPTION){if(!prepare(scene,0)){phase=6;show_ui();}}
            else if(phase==2 && action==INPUT_FIRE){
                if(scene==59){save_complete=1;save_begin();save_write();asset_load_end();phase=10;show_ui();}
                else if(!prepare(scene+1,0)){phase=6;show_ui();}
                else{save_begin();if(save_write()){asset_load_end();show_play();}else{asset_load_end();phase=11;show_ui();}}
            }else if(action==INPUT_SELECT || (phase==1 && action==INPUT_FIRE)){
                eng4_accepted();moved=undo_pop(&gs);if(moved){phase=1;sound_request=2;}
            }else if(phase==1){
                dx=dy=0;
                if(action==INPUT_UP){dy=-1;facing=0;}if(action==INPUT_DOWN){dy=1;facing=1;}
                if(action==INPUT_RIGHT){dx=1;facing=2;}if(action==INPUT_LEFT){dx=-1;facing=3;}
                if(dx || dy){eng4_accepted();moved=game_step(&gs,dx,dy,&pushed);sound_request=moved?(pushed?3:0):1;}
            }
            if(action!=INPUT_NONE)eng4_busy=moved;
        }else if(phase==3){
            if(action==INPUT_START){if(!resume()){phase=6;show_ui();}}
            else if(action==INPUT_FIRE){previous_phase=3;phase=7;show_ui();}
            else if(action==INPUT_OPTION){if(!prepare(scene,0)){phase=6;show_ui();}}
            else if(action==INPUT_SELECT){save_begin();if(save_write()){asset_load_end();title();}else{asset_load_end();show_ui();}}
        }else if(phase==7){
            if(action==INPUT_LEFT || action==INPUT_RIGHT){music_enabled=music_ready && !music_enabled;show_ui();}
            else if(action==INPUT_FIRE){sfx_enabled^=1;show_ui();}
            else if(action==INPUT_START){phase=previous_phase;if(phase==0)show_menu();else show_ui();}
        }else if(phase==11){
            if(action==INPUT_FIRE || action==INPUT_START){if(!resume()){phase=6;show_ui();}}
            else if(action==INPUT_SELECT){save_begin();if(save_write()){asset_load_end();if(!resume()){phase=6;show_ui();}}else{asset_load_end();show_ui();}}
        }else if(phase==8 || phase==9 || phase==10){
            if(phase==10 && action==INPUT_SELECT){save_begin();save_write();asset_load_end();show_ui();}
            else if(action==INPUT_START || action==INPUT_FIRE)title();
        }
        else if(phase==6){
            if(action==INPUT_FIRE){
                if(startup_pending || failed_kind==5)startup();
                else if(failed_kind==4)title();
                else if(!(failed_resume?resume():prepare(failed_scene,failed_restore))){phase=6;show_ui();}
            }else if(action==INPUT_START)title();
        }
        frame_logic();frame_audio();
        if(phase==1 || phase==2){
            if(moved){display_changed(pushed);display_animate(moved|(pushed<<1));hud_undo=(action==INPUT_FIRE || action==INPUT_SELECT);display_counters();}
            if(moved && pushed && hud_state_docks==gs.box_count){phase=2;sound_request=4;}
            hud_budget_clock=clock;hud_work();
        }
        if(phase!=was && !((phase==1 || phase==2) && (was==1 || was==2))){input_rearm();clock=input_clock;}
        frame_render();frame_end();
    }
    return 0;
}
