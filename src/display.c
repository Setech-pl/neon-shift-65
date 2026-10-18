#include <string.h>
#include <stddef.h>
#include "display.h"
#include "prototype_assets.h"
#include "hardware.h"
#include "scene.h"
/* Native cell ASM uses this exact cc65 layout. Build fails on ABI drift. */
const unsigned int native_layout[]={sizeof(GameState),offsetof(GameState,width),offsetof(GameState,player),offsetof(GameState,boxes),offsetof(GameState,box_count)};
#define REG(a) (*(volatile unsigned char *)(a))
#pragma bss-name(push,"SCREEN")
static unsigned char screen[1024];
#pragma bss-name(pop)
#pragma bss-name(push,"PMGDATA")
static unsigned char hud_charset[1024];
static unsigned char hud_stage[320];
#pragma bss-name(pop)
#pragma bss-name(push,"IO_BUFFER")
static unsigned char menu_charset[1024];
#pragma bss-name(pop)
#pragma bss-name(push,"CHARSET")
static unsigned char charset[1024];
#pragma bss-name(pop)
unsigned char render_board_x,render_board_y;
const GameState *render_game;
#define board_x render_board_x
#define board_y render_board_y
void __fastcall__ render_cell(unsigned int point);
unsigned char __fastcall__ render_docks(const GameState *g);
static Point previous_player,previous_boxes[MAX_BOXES];
static unsigned char animation,animation_phase,last_robot_frame=255,shown_phase=255;
volatile unsigned int render_tile_writes,render_full_boards;

extern unsigned char *render_target;
extern unsigned char render_limit;
extern char render_digits[11];
void __fastcall__ render_tile(unsigned char base);
void __fastcall__ render_text(const char *s);
void __fastcall__ render_mono_text(const char *s);
void __fastcall__ render_number(uint32_t n);
static const unsigned int row_offset[24]={0,40,80,120,160,200,240,280,320,360,400,440,480,520,560,600,640,680,720,760,800,840,880,920};
static uint32_t shown_moves,shown_pushes;
static unsigned char shown_docks;
extern volatile unsigned char hud_pending;
extern unsigned int hud_x;
extern unsigned char hud_pitch;
void __fastcall__ render_hud_text(const char *s);
static void hud_text(unsigned int x,unsigned char row,const char *s,unsigned char pitch)
{
    hud_x=x;hud_pitch=pitch;render_target=row?hud_stage:hud_charset;render_hud_text(s);
}
static void scenery(unsigned char id) { memcpy(screen+80,scene_maps+(unsigned int)id*880,880); }
static void background(const GameState *g)
{
    static const unsigned int positions[7]={82,85,723,954,955,956,957};
    unsigned char i,x,y;
    background_mask=0;
    for(i=0;i<7;i++){
        x=positions[i]%40;y=positions[i]/40;
        if(x<board_x || x>=board_x+g->width*2 || y<board_y || y>=board_y+g->height*2)
            background_mask|=1<<i;
    }
    background_enabled=1;
}
static void text(unsigned char x,unsigned char y,const char *s)
{
    if(y>=24 || x>=40)return;
    render_target=screen+row_offset[y]+x;render_limit=40-x;
    if((screen[y?965+y:963]&15)==2)render_mono_text(s);else render_text(s);
}
static void clear_row(unsigned char y) { memset(screen+row_offset[y],0,40); }
static void tile(unsigned char col,unsigned char row,unsigned char base)
{
    if(col>38 || row>22)return;
    render_target=screen+row_offset[row]+col;
    render_tile(base);
    ++render_tile_writes;
}
static void cell(const GameState *g,unsigned char x,unsigned char y)
{
    render_game=g;
    render_cell(((unsigned int)y<<8)|x);
}
static void snapshot(const GameState *g)
{ previous_player=g->player;memcpy(previous_boxes,g->boxes,sizeof(previous_boxes)); }
/* ANTIC display list always consumes 24 x 40 screen bytes. DLI table is
   published with DMA disabled; menu selection changes only one-byte colors. */
static void raster(unsigned char layout)
{
    unsigned char i,mode=4;
    /* Avoid cc65's nested-conditional index-register miscompile. Choose the
       mode once, then write a simple loop. Every frontend line is ANTIC2. */
    if(layout==2)mode=2;
    screen[963]=mode|64;
    for(i=1;i<24;i++)screen[965+i]=mode;
    if(layout==1){screen[963]=0xC2;screen[966]=0x82;}
    display_font=layout==1?0x90:layout==2?0x98:0x8C;
    display_pf1=layout==0?COLOR_COLPF1:14;
    display_pf2=layout==0?COLOR_COLPF2:layout==1?0xE0:0;
    if(layout==1){
        dli_font[0]=0x90;dli_pf1[0]=14;dli_pf2[0]=0;
        dli_font[1]=0x8C;dli_pf1[1]=COLOR_COLPF1;dli_pf2[1]=COLOR_COLPF2;
    }
}
static void title_raster(void)
{
    unsigned char i;
    raster(0);
    screen[969]|=128;         /* row4 -> monochrome studio credit */
    screen[970]=0x82;         /* row5 -> colorful hero */
    screen[977]|=128;         /* row12 -> clean monochrome menu */
    for(i=13;i<24;i++)screen[965+i]=2;
    screen[980]|=128;screen[982]|=128;screen[984]|=128;
    for(i=0;i<6;i++){
        dli_font[i]=i==1?0x8C:0x98;
        dli_pf1[i]=i==1?COLOR_COLPF1:14;
        dli_pf2[i]=i==1?COLOR_COLPF2:0;
    }
}
void display_init(void)
{
    display_active=0;REG(0x022F)=0;REG(0xD400)=0;
    memset(screen,0,sizeof(screen));memcpy(charset,title_charset,1024);
    memset(menu_charset,0,sizeof(menu_charset));memcpy(menu_charset,menu_font,352);
    screen[960]=screen[961]=screen[962]=0x70;
    screen[964]=0;screen[965]=0x88;
    raster(0);
    screen[989]=0x41;screen[990]=0xC0;screen[991]=0x8B;
    REG(0x0230)=0xC0;REG(0x0231)=0x8B;
    REG(0x02F4)=0x8C;REG(0xD409)=0x8C;
    REG(0x02F3)=2;REG(0xD401)=2;
    REG(0x02C4)=COLOR_COLPF0;REG(0x02C5)=COLOR_COLPF1;REG(0x02C6)=COLOR_COLPF2;REG(0x02C7)=COLOR_COLPF3;REG(0x02C8)=COLOR_COLBK;
    REG(0x026F)=0;REG(0xD01B)=0;REG(0xD01D)=0;
    display_active=1;
    render_tile_writes=render_full_boards=0;
}
void display_board(const GameState *g)
{
    background_enabled=0;hud_enabled=1;
    display_active=0;REG(0x022F)=0;REG(0xD400)=0;
    memset(screen,0,960);raster(1);
    scene_apply(charset);robot_dirty=1;
    board_x=20-g->width;board_y=13-g->height;

    snapshot(g);last_robot_frame=255;animation=0;++render_full_boards;
    /* HUD/scenery publication completes before display_active in display_hud. */
}
void display_changed(const GameState *g)
{
    unsigned char i;
    const Point *box=g->boxes;
    Point *old_box=previous_boxes;
    if(previous_player.x!=g->player.x || previous_player.y!=g->player.y) {
        cell(g,previous_player.x,previous_player.y);cell(g,g->player.x,g->player.y);
    }
    for(i=0;i<g->box_count;i++,++box,++old_box)
        if(old_box->x!=box->x || old_box->y!=box->y) {
            cell(g,old_box->x,old_box->y);cell(g,box->x,box->y);
            /* A drained input backlog can move several distinct modules. */
        }
    snapshot(g);
}
static void hud_number(unsigned int x,unsigned char row,uint32_t n)
{
    render_number(n);
    if(n<10){hud_text(x,row,"0",7);x+=7;}
    hud_text(x,row,render_digits,7);
}
void display_counters(const GameState *g)
{
    unsigned char docks=render_docks(g);
    if(shown_moves==g->moves && shown_pushes==g->pushes && shown_docks==docks)return;
    while(hud_pending) {}
    /* Cell-aligned numeric ownership: x48..119 and x192..263. Clear
       entire fields after undo; labels end at40/183 and remain untouched. */
    if(shown_moves!=g->moves){memset(hud_stage+48,0,72);hud_number(49,1,g->moves);}
    if(shown_pushes!=g->pushes){memset(hud_stage+192,0,72);hud_number(192,1,g->pushes);}
    /* Dock value fits alongside the name. Main only writes this row with
       DMA off, and enables it again after the complete ratio is ready. */
    if(shown_docks!=docks){
        display_active=0;REG(0x022F)=0;REG(0xD400)=0;
        memset(hud_charset+232,0,88);
        hud_text(232,0,"DOCKS:",7);hud_number(281,0,docks);
        hud_text(295,0,"/",7);hud_number(302,0,g->box_count);
    }
    shown_moves=g->moves;shown_pushes=g->pushes;shown_docks=docks;hud_pending=1;
    display_active=1;
}
void display_hud(const GameState *g,const Flow *f)
{
    unsigned char i,x,y;
    scene_build(g,f->scene);scenery(prototype_scenes[f->scene]);
    for(y=0;y<g->height;y++)for(x=0;x<g->width;x++)cell(g,x,y);
    while(hud_pending) {}
    memset(hud_charset,0,1024);
    for(i=0;i<80;i++)screen[i]=i;
    hud_text(0,0,prototype_levels[f->scene].name,8);
    memset(hud_stage,0,320);hud_text(0,1,"STEPS:",7);hud_text(136,1,"PUSHES:",7);
    shown_moves=~g->moves;shown_pushes=~g->pushes;shown_docks=255;
    /* Publish substrate/direction before the first visible board VBI. */
    display_animate(g,f,0,0);
    display_counters(g);background(g);display_active=1;
}
static void option(unsigned char row,const char *name,unsigned char selected)
{ text(7,row,selected?">":" ");text(9,row,name); }
static void switches(unsigned char row,const Flow *f)
{ text(9,row,"MUSIC");text(29,row,f->music?"ON":"OFF");text(9,row+1,"SFX");text(29,row+1,f->sfx?"ON":"OFF"); }
static void window(void)
{
    unsigned char y;
    for(y=6;y<20;y++)memset(screen+row_offset[y]+6,0,28);
    text(6,6,"============================");text(6,19,"============================");
}
void display_view(const GameState *g,const Flow *f)
{
    unsigned char x,y,fresh=shown_phase!=f->phase;
    shown_phase=f->phase;
    if(f->phase!=PHASE_PLAY && f->phase!=PHASE_WIN)infra_enabled=0;
    if(f->phase!=PHASE_PLAY && f->phase!=PHASE_WIN)background_enabled=0;
    if(f->phase!=PHASE_PLAY && f->phase!=PHASE_WIN)hud_enabled=0;
    if(f->phase==PHASE_TITLE) {
        if(fresh) {
            display_active=0;REG(0x022F)=0;REG(0xD400)=0;
            robot_frame=255;while(hud_pending) {}
            memset(screen,0,960);memcpy(charset,title_charset,1024);scenery(0);title_raster();
            for(y=0;y<8;y++)clear_row(y);
            for(y=0;y<2;y++)for(x=0;x<TITLE_LOGO_WIDTH;x++)screen[row_offset[y+2]+7+x]=title_logo[y*TITLE_LOGO_WIDTH+x];
            text(10,5,"SETECH GAME STUDIO");
            for(y=7;y<11;y++)for(x=0;x<4;x++)screen[row_offset[y]+16+x]=TITLE_ROBOT+(y-7)*4+x;
            tile(21,9,TILE_MODULE);tile(24,9,TILE_DOCKED);
        }
        /* Full-width quiet area: no illustration or stale selection marker. */
        for(y=13;y<24;y++)clear_row(y);
        option(14,"BEGIN SHIFT",f->menu==0);option(16,"CONTINUE",f->menu==1);
        option(18,"TOP SCORES",f->menu==2);option(20,"CONFIG",f->menu==3);
        for(y=0;y<4;y++)dli_pf2[y+2]=f->menu==y?0xE0:0;
        display_active=1;return;
    }
    if(fresh && f->phase!=PHASE_PLAY && f->phase!=PHASE_WIN) {
        display_active=0;REG(0x022F)=0;REG(0xD400)=0;
        robot_frame=255;while(hud_pending) {}
        memset(screen,0,960);raster(2);
    }
    if(f->phase==PHASE_CONFIG) {
        window();text(17,8,"CONFIG");
        option(10,"DIFFICULTY:",f->menu==0);text(22,10,"      ");text(22,10,f->difficulty==0?"EASY":f->difficulty==1?"MEDIUM":"HARD");
        option(12,"MUSIC:",f->menu==1);text(22,12,f->music?"ON ":"OFF");
        option(14,"SFX:",f->menu==2);text(22,14,f->sfx?"ON ":"OFF");
        option(16,"BACK",f->menu==3);display_active=1;return;
    }
    if(f->phase==PHASE_CONTINUE || f->phase==PHASE_SCORES) {
        window();text(12,9,f->phase==PHASE_CONTINUE?"CONTINUE":"TOP SCORES");
        text(8,12,f->phase==PHASE_CONTINUE?"NO CONTINUATION CODE YET":"SCORES NOT AVAILABLE YET");
        text(10,16,"FIRE RETURN TO TITLE");display_active=1;return;
    }
    if(f->phase==PHASE_MENU) {
        window();text(16,8,"SHIFT PAUSED");
        option(10,"RESUME",f->menu==0);option(11,"RESTART",f->menu==1);
        option(12,"SCENE",f->menu==2);text(19,12,prototype_levels[f->pending_scene].name);
        option(13,"MUSIC",f->menu==3);option(14,"SFX",f->menu==4);switches(13,f);
        option(15,"TITLE SCREEN",f->menu==5);
        option(16,"WAREHOUSE:",f->menu==6);text(22,16,warehouse_choice==1?"ENERGY ":"REACTOR");text(9,17,"FIRE/SELECT UNDO");text(9,18,"OPTION RESTART / START RESUME");display_active=1;return;
    }
    if(f->phase==PHASE_RESTART) {
        window();text(12,9,"RESTART THIS SHIFT?");text(9,12,prototype_levels[f->pending_scene].name);
        option(15,"NO - KEEP PLAYING",!f->choice);option(16,"YES - RESTART",f->choice);display_active=1;return;
    }
    if(f->phase==PHASE_FINALE) {
        display_active=0;REG(0x022F)=0;REG(0xD400)=0;memset(screen,0,960);raster(2);
        text(9,8,"SHIFT SAMPLE COMPLETE");text(10,11,"SETECH GAME STUDIO");text(12,15,"FIRE RETURN TO TITLE");
        display_active=1;return;
    }
    if(f->phase==PHASE_ERROR){text(7,10,scene_error?"ASSET READ / VALIDATION ERROR":"INVALID SCENE");text(7,22,"FIRE RETURN TO TITLE");display_active=1;return;}
    if(f->phase==PHASE_WIN){
        background_enabled=0;display_active=0;REG(0x022F)=0;REG(0xD400)=0;
        screen[987]|=128;screen[988]=2;
        dli_font[2]=0x98;dli_pf1[2]=14;dli_pf2[2]=0;
        clear_row(23);text(2,23,"SHIFT CLEAR");display_active=1;
    }
    else if(f->phase==PHASE_PLAY){screen[987]&=127;screen[988]=4;memcpy(screen+920,scene_maps+(unsigned int)prototype_scenes[f->scene]*880+840,40);background(g);}
    (void)g;
}
void display_animate(const GameState *g,const Flow *f,unsigned char ticks,unsigned char animate)
{
    unsigned char index,mode=0;
    scene_animate(charset,ticks);
    if(animate){animation=8;animation_phase=0;}
    if(animation) {
        if(ticks>=animation)animation=0;else animation-=ticks;
        animation_phase+=ticks;
        mode=f->last_push?3:1;
        mode+=(animation_phase>>1)&1;
    }
    index=(g->map[g->player.y][g->player.x]=='.'?20:0)+f->facing*5+mode;
    if(index!=last_robot_frame) {
        robot_frame=index;last_robot_frame=index;
    }
}
