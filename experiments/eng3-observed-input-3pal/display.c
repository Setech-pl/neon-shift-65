#include <string.h>
#include "candidate.h"
#include "neon-palette.h"
extern volatile unsigned char asset_loading;
void loading_finish(void);
unsigned char render_board_x,render_board_y;
const GameState *render_game;
volatile unsigned int render_tile_writes,render_full_boards;
Point old_player,old_boxes[10];
volatile unsigned int hud_epoch,hud_ready_epoch,hud_committed_epoch;
volatile unsigned char hud_dirty,hud_undo;
uint32_t hud_state_moves,hud_state_pushes;
unsigned char hud_state_docks;
char hud_move_digits[11],hud_push_digits[11];
volatile unsigned char hud_budget_clock;
extern unsigned char hud_stage_chars[25],hud_cursor;
extern volatile unsigned char hud_live_valid;
void hud_seed_live(void);
void __fastcall__ hud_adjust(char *digits);
extern unsigned char robot_animation;
void __fastcall__ render_ratio(unsigned char docks);
unsigned char validate_area(void){
    static const unsigned char pf1[4]={156,188,76,56},pf2[4]={34,178,66,50};
    unsigned char area=DESC[6];
    if(area<1 || area>4)return 0;
    return DESC[7]==1 && DESC[536]==AREA_PF0 && DESC[537]==pf1[area-1] && DESC[538]==pf2[area-1] && DESC[539]==AREA_PF3 && !DESC[540] && !DESC[541] && !DESC[542] && !DESC[543];
}
static const unsigned char banks[5]={0x8c,0xa0,0xa4,0xa8,0xac};
void animation_reset(void);
void phase_reset(void);
extern volatile unsigned char critical_guard;
void video_off(void){hud_cancel();while(publish_pending || critical_guard){}publish_count=robot_copy=0;if(display_active || asset_loading)while(REG(0xd40b)<124){}asset_loading=0;display_active=ambient_active=menu_active=0;REG(0x022f)=0;REG(0xd400)=0;}
static void activate(void){if(phase!=6)loading_finish();asset_loading=0;REG(0x230)=0x60;REG(0x231)=0x9f;REG(0x2f3)=2;REG(0xd401)=2;REG(0x26f)=0;display_active=1;}
static void colors(unsigned char font,unsigned char pf1,unsigned char pf2)
{
    display_font=font;display_pf1=pf1;display_pf2=pf2;
    REG(0x2c4)=0xee;REG(0x2c5)=0x9c;REG(0x2c6)=0x22;REG(0x2c7)=0x2a;REG(0x2c8)=0;
}
static unsigned char glyph(unsigned char c)
{
    if(c>='A' && c<='Z')return c-'A'+1;
    if(c>='0' && c<='9')return c-'0'+27;
    if(c==':')return 37;if(c=='/')return 38;if(c=='-')return 39;if(c=='>')return 42;
    return 0;
}
static void text(unsigned char row,unsigned char col,const char *s)
{unsigned char *p=SCREEN+(unsigned int)row*40+col;while(*s && col++<40)*p++=glyph(*s++);}
static void hud_text(unsigned int x,unsigned char row,const char *s,unsigned char pitch)
{hud_x=x;hud_pitch=pitch;render_target=row?HUDSTAGE:HUD;render_hud_text(s);}
static void number(unsigned int x,unsigned char row,uint32_t n)
{render_number(n);if(n<10){hud_text(x,row,"0",7);x+=7;}hud_text(x,row,render_digits,7);}
/* Only foreground owns the caches/staging. Clear the one-byte ready flag
   BEFORE changing the 16-bit epoch; NMI observes the token only when ready=1.
   Invalidating a ready request never discards a core action or its undo. */
void hud_invalidate(void)
{
    if(hud_pending)hud_dirty=1;
    hud_pending=ratio_pending=0;
    ++hud_epoch;
}
void hud_cancel(void)
{
    hud_invalidate();hud_dirty=0;hud_live_valid=0;
}
static void seed(char *digits,uint32_t n)
{
    unsigned char len=0;
    render_number(n);while(render_digits[len])++len;
    memset(digits,'0',10);memcpy(digits+10-len,render_digits,len);digits[10]=0;
}
static void advance(char *digits,uint32_t n)
{
    if(!n)memset(digits,'0',10);
    else if(n==4294967295UL)memcpy(digits,"4294967295",10);
    else hud_adjust(digits);
}
void hud_request(void)
{
    advance(hud_move_digits,gs.moves);
    if(gs.pushes!=hud_state_pushes)advance(hud_push_digits,gs.pushes);
    hud_state_moves=gs.moves;hud_state_pushes=gs.pushes;
    hud_state_docks=render_docks(&gs);hud_dirty=1;
}
/* Retain the checkpoint label for apples-to-apples request cost tracing. */
void display_counters(void){hud_request();}
static void cell(unsigned char x,unsigned char y){render_cell(((unsigned int)y<<8)|x);}
void show_play(void)
{
    unsigned char i,x,y,j=0;
    video_off();hud_enabled=1;
    memcpy(SCREEN+80,BASE,880);
    for(i=0;i<3;i++)DLIST[j++]=0x70;
    DLIST[j++]=0xc2;DLIST[j++]=0;DLIST[j++]=0x88;DLIST[j++]=0x82;
    for(i=2;i<24;i++)DLIST[j++]=4|((i==5 || i==9 || i==13 || i==17)?128:0);
    DLIST[j++]=0x41;DLIST[j++]=0x60;DLIST[j++]=0x9f;
    colors(0x90,14,AREA_HUD);
    dli_font[0]=0x90;dli_pf1[0]=14;dli_pf2[0]=0;
    for(i=1;i<6;i++){dli_font[i]=banks[i-1];dli_pf1[i]=DESC[537];dli_pf2[i]=DESC[538];}
    for(i=0;i<5;i++)REG(0x2c4+i)=DESC[536+i];
    render_board_x=DESC[2];render_board_y=DESC[3];render_game=&gs;
    old_player=gs.player;memcpy(old_boxes,gs.boxes,sizeof(old_boxes));
    memset((void *)dock_timer,0,10);
    for(y=0;y<gs.height;y++)for(x=0;x<gs.width;x++){
        publish_count=0;cell(x,y);
        for(i=0;i<publish_count;i++)REG(((unsigned int)publish_addr_hi[i]<<8)|publish_addr_lo[i])=publish_code[i];
    }
    publish_count=0;memset(HUD,0,1024);memset(HUDSTAGE,0,320);
    for(i=0;i<80;i++)SCREEN[i]=i;
    hud_text(0,0,prototype_levels[scene].name,8);hud_text(232,0,"DOCKS:",7);
    number(281,0,render_docks(&gs));hud_text(295,0,"/",7);number(302,0,gs.box_count);
    memcpy((unsigned char *)0x9540,HUD+232,88);
    hud_text(0,1,"STEPS:",7);hud_text(136,1,"PUSHES:",7);
    seed(hud_move_digits,gs.moves);seed(hud_push_digits,gs.pushes);
    hud_state_moves=gs.moves;hud_state_pushes=gs.pushes;hud_state_docks=render_docks(&gs);
    memset(hud_stage_chars,255,25);hud_cursor=0;hud_dirty=1;
    do{hud_budget_clock=input_clock;hud_work();}while(hud_dirty);
    hud_pending=0;hud_committed_epoch=hud_ready_epoch;
    memcpy(HUD+320,HUDSTAGE,320);hud_seed_live();
    phase_reset();animation_reset();ambient_active=1;display_animate(0);++render_full_boards;activate();
}
/* Arrow-only selection publication in vertical blank; no DMA or DL changes. */
void menu_select(void)
{
    unsigned char i;
    while(REG(0xd40b)<124 || REG(0xd40b)>145){}
    for(i=0;i<4;i++)SCREEN[(unsigned int)i*40+11]=i==selected?42:0;
}
void show_menu(void)
{
    unsigned char i,j=0;
    video_off();hud_enabled=0;memset(SCREEN,0,960);
    for(i=0;i<3;i++)DLIST[j++]=0x70;
    DLIST[j++]=0x4f;DLIST[j++]=0;DLIST[j++]=0xa0;
    for(i=1;i<80;i++)DLIST[j++]=15;
    DLIST[j++]=0x4f;DLIST[j++]=0;DLIST[j++]=0xb0;
    for(i=1;i<20;i++)DLIST[j++]=15;
    DLIST[j++]=0x30;
    DLIST[j++]=0x42;DLIST[j++]=0;DLIST[j++]=0x88;
    for(i=0;i<3;i++){DLIST[j++]=0x30;DLIST[j++]=2|(i==2?128:0);}
    DLIST[j++]=0x50;
    DLIST[j++]=0x4e;DLIST[j++]=0;DLIST[j++]=0xb4;
    for(i=1;i<30;i++)DLIST[j++]=14;
    DLIST[j++]=0x70;
    DLIST[j++]=0x41;DLIST[j++]=0x60;DLIST[j++]=0x9f;
    text(0,13,"BEGIN SHIFT");text(1,13,"CONTINUE");text(2,13,"TOP SCORES");text(3,13,"CONFIG");text(selected,11,">");
    colors(0x8c,14,0);
    dli_font[0]=0x8c;dli_pf1[0]=0xd8;dli_pf2[0]=0;
    menu_active=1;activate();
}
void show_ui(void)
{
    unsigned char i,j=0;
    video_off();hud_enabled=0;memset(HUD,0,1024);memcpy(HUD,menu_font,352);memset(SCREEN,0,960);
    for(i=0;i<3;i++)DLIST[j++]=0x70;
    DLIST[j++]=0x42;DLIST[j++]=0;DLIST[j++]=0x88;
    for(i=1;i<24;i++)DLIST[j++]=2;
    DLIST[j++]=0x41;DLIST[j++]=0x60;DLIST[j++]=0x9f;colors(0x90,14,0);
    if(phase==6){text(7,7,"ASSET READ / VALIDATION ERROR");text(11,7,"FIRE RETRY COMPLETE PACKAGE");text(14,7,"START RETURN TO TITLE");}
    else if(phase==7){text(6,16,"CONFIG");text(10,9,"LEFT / RIGHT MUSIC");text(12,9,"FIRE SOUND EFFECTS");text(16,9,"START RETURN");}
    else if(phase==9){text(8,14,"TOP SCORES");text(12,9,"QUALIFICATION ONLY");text(16,9,"START RETURN TO TITLE");}
    else{ text(5,14,"SHIFT PAUSED");text(8,8,"START RESUME / FIRE CONFIG");text(10,8,"LEFT / RIGHT SCENE");text(12,8,"OPTION RESTART");text(14,8,"SELECT RETURN TO TITLE");text(17,8,prototype_levels[scene].name);}
    activate();
}
