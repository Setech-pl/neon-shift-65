/* Mutually exclusive with selector/game code in the existing $A000-$A7FF.
 * No game state or durable save is changed by this UI. */
#include "campaign.h"
#include <string.h>
extern unsigned char previous_phase;
void text(unsigned char row,unsigned char col,const char *s);
void activate(void);
void __fastcall__ input_wait(unsigned char clock);
static unsigned char clock,action,item,confirm,accept,i,last_row,layout,last_music,last_sfx;
static void draw(void)
{
    unsigned char *p;
    /* Build each layout once. Selection movement never stops/restarts DMA,
     * rebuilds the font, clears the screen or enters a loader. */
    if(layout!=confirm){
        phase=12;show_ui();
        text(3,15,"OPTIONS");
        if(confirm){
            text(7,7,"EXIT TO MAIN MENU?");
            text(9,7,"UNSAVED PROGRESS WILL BE LOST");
            text(12,7,"CANCEL");text(14,7,"EXIT TO MAIN MENU");
        }else{
            text(7,7,music_enabled?"MUSIC ON":"MUSIC OFF");
            text(9,7,sfx_enabled?"SFX ON":"SFX OFF");
            text(11,7,previous_phase?"RESUME GAME":"BACK");
            if(previous_phase)text(13,7,"EXIT TO MAIN MENU");
        }
        text(18,4,"UP/DOWN SELECT  FIRE CONFIRM");
        text(20,4,previous_phase?"OPTION RESUME GAME":"OPTION BACK");
        last_row=255;layout=confirm;
        last_music=music_enabled;last_sfx=sfx_enabled;
    }
    while(REG(0xd40b)<124 || REG(0xd40b)>130){}
    if(last_row!=255){
        p=SCREEN+(unsigned int)last_row*40+5;*p=0;p+=2;
        for(i=0;i<29;i++)p[i]&=127;
    }
    if(!confirm){
        if(last_music!=music_enabled){text(7,7,music_enabled?"MUSIC ON ":"MUSIC OFF");last_music=music_enabled;}
        if(last_sfx!=sfx_enabled){text(9,7,sfx_enabled?"SFX ON ":"SFX OFF");last_sfx=sfx_enabled;}
    }
    i=confirm?(accept?14:12):7+item*2;
    text(i,5,">");
    p=SCREEN+(unsigned int)i*40+7;last_row=i;
    for(i=0;i<29;i++)p[i]|=128;
    if(!display_active)activate();
}
unsigned char options_run(void)
{
    item=confirm=accept=0;layout=255;draw();input_rearm();clock=input_clock;
    for(;;){
        input_wait(clock);clock=input_clock;action=input_read();
        if(action==INPUT_OPTION || action==INPUT_START)return previous_phase?254:255;
        if(confirm){
            if(action==INPUT_UP || action==INPUT_DOWN || action==INPUT_LEFT || action==INPUT_RIGHT){accept^=1;draw();}
            else if(action==INPUT_FIRE){
                if(accept)return 253;
                confirm=0;draw();input_rearm();
            }
        }else if(action==INPUT_UP || action==INPUT_DOWN){
            if(action==INPUT_UP)item=item?item-1:(previous_phase?3:2);
            else if(++item>(previous_phase?3:2))item=0;
            draw();
        }else if(action==INPUT_LEFT || action==INPUT_RIGHT || action==INPUT_FIRE){
            if(item==0)music_enabled^=1;
            else if(item==1)sfx_enabled^=1;
            else if(action!=INPUT_FIRE)continue;
            else if(item==2)return previous_phase?254:255;
            else{confirm=1;accept=0;input_rearm();}
            draw();
        }
    }
}
