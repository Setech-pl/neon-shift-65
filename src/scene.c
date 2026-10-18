#include <string.h>
#include "scene.h"
#include "hardware.h"
#include "prototype_assets.h"
#pragma code-name(push,"LOADER")
#pragma rodata-name(push,"LOADCONST")
#pragma bss-name(push,"LOADBSS")
unsigned char warehouse_choice=1;
unsigned char scene_loaded,scene_error;
unsigned char scene_cells[200],scene_data[784],scene_header[32];
unsigned int scene_reads,scene_first_sector,scene_last_sector;
static unsigned char animation_clock,animation_frame;
static unsigned int crc;
#pragma bss-name(pop)
#pragma bss-name(push,"SECTOR_BUFFER")
unsigned char sector_buffer[128];
#pragma bss-name(pop)
void scene_init(void) { scene_loaded=scene_error=0;scene_reads=0;warehouse_choice=1; }
static unsigned int word(const unsigned char *p) { return p[0]|((unsigned int)p[1]<<8); }
static void crc_byte(unsigned char b)
{
    unsigned char i;
    crc^=(unsigned int)b<<8;
    for(i=0;i<8;i++)crc=crc&0x8000?(crc<<1)^0x1021:crc<<1;
}
static unsigned char crc_check(const unsigned char *p,unsigned int n,unsigned int expected)
{
    crc=0xffff;while(n--)crc_byte(*p++);return crc==expected;
}
static unsigned char read_sector(unsigned int sector)
{
    unsigned char retry;
    for(retry=0;retry<2;retry++){
        ++scene_reads;scene_last_sector=sector;
        if(sio_read(sector)==1)return 1;
    }
    scene_error=1;return 0;
}
unsigned char scene_ensure(void)
{
    unsigned int start=0,count=0,offset=0,n,i,sector;
    unsigned char at,k,ok=0;
    if(scene_loaded==warehouse_choice)return 1;
    asset_load_begin();scene_loaded=0;scene_error=0;scene_reads=0;
    if(!read_sector(4))goto finish;
    if(memcmp(sector_buffer,"NSWD",4) || sector_buffer[4]!=1 || sector_buffer[5]!=2 ||
       word(sector_buffer+6)!=1 || !crc_check(sector_buffer,126,word(sector_buffer+126))){scene_error=2;goto finish;}
    for(k=0;k<2;k++){
        at=32+k*16;
        if(word(sector_buffer+at)==warehouse_choice && word(sector_buffer+at+2)==1){
            start=word(sector_buffer+at+4);count=word(sector_buffer+at+6);
            if(word(sector_buffer+at+8)!=816 || word(sector_buffer+at+10)!=784){scene_error=2;goto finish;}
        }
    }
    if(start<5 || count!=7 || start>65529U){scene_error=2;goto finish;}
    scene_first_sector=start;
    if(!read_sector(start))goto finish;
    memcpy(scene_header,sector_buffer,32);
    if(memcmp(scene_header,"NSWP",4) || scene_header[4]!=1 || scene_header[5]!=0 ||
       word(scene_header+6)!=warehouse_choice || word(scene_header+8)!=1 ||
       word(scene_header+10)!=784 || word(scene_header+12)!=784 ||
       scene_header[16]!=0 || scene_header[20]!=COLOR_COLPF3 ||
       scene_header[21]!=56 || scene_header[22]<16 || scene_header[23]!=2 ||
       word(scene_header+26)!=1 || word(scene_header+28)!=0 ||
       !crc_check(scene_header,30,word(scene_header+30))){scene_error=3;goto finish;}
    for(k=16;k<21;k++)if(scene_header[k]&1){scene_error=3;goto finish;}
    crc=0xffff;sector=start;at=32;
    while(offset<784){
        n=128-at;if(n>784-offset)n=784-offset;
        for(i=0;i<n;i++){scene_data[offset++]=sector_buffer[at+i];crc_byte(sector_buffer[at+i]);}
        if(offset<784){++sector;if(!read_sector(sector))goto finish;at=0;}
    }
    if(crc!=word(scene_header+14)){scene_error=4;goto finish;}
    for(i=640;i<656;i++)if(scene_data[i]<4 || scene_data[i]>56 || (scene_data[i]&3)){scene_error=5;goto finish;}
    for(i=656;i<720;i+=4){
        if(scene_data[i]==255)continue;
        if(scene_data[i]>=3 || scene_data[i+1]>=20 || scene_data[i+2]>=10 ||
           scene_data[i+3]<4 || scene_data[i+3]>56 || (scene_data[i+3]&3)){scene_error=5;goto finish;}
        /* Validate semantic wall ownership against immutable logical levels. */
        if(scene_data[i+2]>=prototype_levels[scene_data[i]].height ||
           scene_data[i+1]>=strlen(prototype_levels[scene_data[i]].rows[scene_data[i+2]]) ||
           prototype_levels[scene_data[i]].rows[scene_data[i+2]][scene_data[i+1]]!='#'){scene_error=5;goto finish;}
    }
    scene_loaded=warehouse_choice;ok=1;
finish:
    asset_load_end();input_rearm();return ok;
}
void scene_apply(unsigned char *bank)
{
    unsigned char i;
    memset(bank,0,32);
    memcpy(bank+32,scene_data,608); /* slots4..79 */
    memcpy(bank+80*8,gameplay_common,32);
    memcpy(bank+84*8,scene_data+608,32);
    memcpy(bank+88*8,robot_frames+160,32);
    memcpy(bank+92*8,gameplay_common+32,288);
    for(i=0;i<4;i++)((volatile unsigned char *)0x02c4)[i]=scene_header[17+i];
    /* Atari shadow order PF0,PF1,PF2,PF3,BK. */
    ((volatile unsigned char *)0x02c4)[4]=scene_header[16];
    dli_pf1[1]=scene_header[18];dli_pf2[1]=scene_header[19];
    animation_clock=animation_frame=infra_frame=0;infra_dirty=1;infra_enabled=1;robot_dirty=1;
}
void scene_build(const GameState *g,unsigned char level)
{
    unsigned char x,y,mask,base,k;
    unsigned int at;
    memset(scene_cells,0,200);
    for(y=0;y<g->height;y++)for(x=0;x<g->width;x++){
        if(g->map[y][x]=='#'){
            mask=0;
            if(y && g->map[y-1][x]=='#')mask|=1;
            if(x+1<g->width && g->map[y][x+1]=='#')mask|=2;
            if(y+1<g->height && g->map[y+1][x]=='#')mask|=4;
            if(x && g->map[y][x-1]=='#')mask|=8;
            base=scene_data[640+mask];
        }else base=64+(((x%4==0?1:0)+(y%2==0?2:0))*4);
        scene_cells[(unsigned int)y*20+x]=base;
    }
    for(k=0;k<16;k++){
        at=656+(unsigned int)k*4;
        if(scene_data[at]==level)
            scene_cells[(unsigned int)scene_data[at+2]*20+scene_data[at+1]]=scene_data[at+3];
    }
}
void scene_animate(unsigned char *bank,unsigned char ticks)
{
    /* Publish one byte; VBI copies the 32B patch before character DMA. */
    animation_clock+=ticks;
    if(animation_clock<scene_header[22])return;
    animation_clock=0;animation_frame^=1;infra_frame=animation_frame;
    (void)bank;
}
#pragma code-name(pop)
#pragma rodata-name(pop)
