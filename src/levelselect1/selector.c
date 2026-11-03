/* Executed only at $A000..$A7FF. No package load or write is allowed here. */
void selector_art(void);
#include "campaign.h"
extern unsigned char game_valid,save_record[128],selector_cursor,selector_seen;
void text(unsigned char row,unsigned char col,const char *s);
void activate(void);
void __fastcall__ input_wait(unsigned char clock);
#define CAND ((GameState *)0xb680)
#include "selector-areas.h"
unsigned char selector_confirm,selector_accept,selector_replace;
static unsigned char clock,action,area,local,i,x,y,valid;
static char digits[6]="00/15";
static char global_digits[6]="00/60";

/* save_scan supplies bounded/unique record coordinates. Validate the same
 * map/CRC/complete constraints as save_apply, against the scratch candidate.
 * Unlike save_apply, this never touches gs, settings, undo or durable bytes. */
static unsigned char preview(void)
{
    if(!board_load(save_level()))return 0;
    if(save_record[14]!=(unsigned char)CAND->map[19][0] ||
       save_record[15]!=(unsigned char)CAND->map[19][1] || save_record[18]!=CAND->box_count)return 0;
    if(CAND->map[save_record[17]][save_record[16]]=='#')return 0;
    for(i=0;i<CAND->box_count;i++){
        x=save_record[19+i*2];y=save_record[20+i*2];
        if(CAND->map[y][x]=='#' || (save_record[7] && (save_level()!=59 || CAND->map[y][x]!='.')))return 0;
    }
    return 1;
}
static void draw(void)
{
    /* Only fields below row 3 change. Begin in the lower border, well before
     * ANTIC will next fetch them. No DMA/font rebuild or SIO while browsing. */
    while(REG(0xd40b)<124 || REG(0xd40b)>130){}
    area=selector_cursor/15;local=selector_cursor%15+1;
    digits[0]='0'+local/10;digits[1]='0'+local%10;
    global_digits[0]='0'+(selector_cursor+1)/10;global_digits[1]='0'+(selector_cursor+1)%10;
    text(6,2,"                    ");text(6,2,selector_areas[area]);
    text(9,10,digits);text(11,10,global_digits);
    text(19,2,selector_confirm?"REPLACE CURRENT / SAVED SHIFT?   ":"UP/DOWN AREA  LEFT/RIGHT LEVEL   ");
    text(21,2,selector_confirm?(selector_accept?" CANCEL    > START SELECTED      ":"> CANCEL     START SELECTED      "):"FIRE START SELECTED LEVEL        ");
}
unsigned char selector_run(void)
{
    valid=save_scan();selector_replace=game_valid || valid || save_error==3;
    if(valid && !preview()){valid=save_previous() && preview();}
    if(!selector_seen){selector_cursor=valid?save_level():0;selector_seen=1;}
    selector_confirm=selector_accept=0;
    phase=12;show_ui();selector_art();
    text(3,13,"SELECT LEVEL");text(9,2,"LOCAL");text(11,2,"GLOBAL");
    text(23,2,"OPTION RETURN TO MENU");
    draw();activate();input_rearm();clock=input_clock;
    for(;;){
        input_wait(clock);clock=input_clock;action=input_read();
        if(action==INPUT_OPTION)return 255;
        if(selector_confirm){
            if(action==INPUT_LEFT || action==INPUT_RIGHT){selector_accept^=1;draw();}
            else if(action==INPUT_FIRE){
                if(selector_accept)return selector_cursor;
                selector_confirm=0;input_rearm();draw();
            }
        }else if(action==INPUT_FIRE){
            if(!selector_replace)return selector_cursor;
            selector_confirm=1;selector_accept=0;input_rearm();draw();
        }else{
            local=selector_cursor%15;
            if(action==INPUT_UP)selector_cursor=selector_cursor<15?selector_cursor+45:selector_cursor-15;
            else if(action==INPUT_DOWN)selector_cursor=selector_cursor>=45?selector_cursor-45:selector_cursor+15;
            else if(action==INPUT_LEFT)selector_cursor=local?selector_cursor-1:selector_cursor+14;
            else if(action==INPUT_RIGHT)selector_cursor=local==14?selector_cursor-14:selector_cursor+1;
            else continue;
            draw();
        }
    }
}
