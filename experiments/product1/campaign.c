#include <string.h>
#include "campaign.h"
#include "campaign-id.h"
#include "undo.h"
#define CAND ((GameState *)0xb680)
#pragma bss-name(push,"PERSIST")
unsigned char level_number,save_error,save_valid,save_complete;
static unsigned char save_record[128],save_slot,save_read_ok;
static unsigned int save_generation;
#pragma bss-name(pop)
extern unsigned int crc;
void __fastcall__ crc_byte(unsigned char b);
#pragma code-name(push,"EXTRA")
unsigned char save_level(void){return save_record[5];}
static unsigned int word(const unsigned char *p){return p[0]|((unsigned int)p[1]<<8);}
static unsigned int checksum(const unsigned char *p){unsigned char i;crc=0xffff;for(i=0;i<126;i++)crc_byte(p[i]);return crc;}
static unsigned char valid_record(void)
{
    unsigned char i,j,x,y;
    if(memcmp(sector_buffer,"NSAV",4) || sector_buffer[4]!=1 || sector_buffer[5]>=60 ||
        memcmp(sector_buffer+10,campaign_id,4) || checksum(sector_buffer)!=word(sector_buffer+126) ||
        sector_buffer[6]>3 || sector_buffer[7]>1 || sector_buffer[16]>=16 || sector_buffer[17]>=8 ||
        !sector_buffer[18] || sector_buffer[18]>10)return 0;
    for(i=0;i<sector_buffer[18];i++){
        x=sector_buffer[19+i*2];y=sector_buffer[20+i*2];
        if(x>=16 || y>=8 || (x==sector_buffer[16] && y==sector_buffer[17]))return 0;
        for(j=0;j<i;j++)if(x==sector_buffer[19+j*2] && y==sector_buffer[20+j*2])return 0;
    }
    return 1;
}
#pragma code-name(pop)
unsigned char board_load(unsigned char n)
{
    unsigned char x,y,t,i,j,goals=0;
    unsigned int pos=0;
    error=0;
    if(n>=60){error=7;return 0;}
    if(sio_read(1000)!=1){error=1;return 0;}
    if(memcmp(sector_buffer,"NSCD",4) || sector_buffer[4]!=1 || sector_buffer[5]!=60 ||
       memcmp(sector_buffer+8,campaign_id,4) || checksum(sector_buffer)!=word(sector_buffer+126)){error=7;return 0;}
    if(sio_read(1100+(unsigned int)n*70)!=1){error=1;return 0;}
    if(memcmp(sector_buffer,"NSLV",4) || sector_buffer[4]!=1 || sector_buffer[5]!=n || sector_buffer[6]!=n/15+1 ||
       sector_buffer[7]<1 || sector_buffer[7]>10 || sector_buffer[10]!=16 || sector_buffer[11]!=8 ||
       memcmp(sector_buffer+12,campaign_id,4) || checksum(sector_buffer)!=word(sector_buffer+126)){error=7;return 0;}
    memset(CAND,0,sizeof(GameState));memset(CAND->map,'#',760);
    CAND->width=16;CAND->height=8;CAND->box_count=sector_buffer[7];
    CAND->player.x=sector_buffer[8];CAND->player.y=sector_buffer[9];
    for(y=0;y<8;y++)for(x=0;x<16;x++,pos++){
        t=(sector_buffer[16+pos/4]>>((pos&3)*2))&3;
        if(t==3 || ((!x || !y || x==15 || y==7) && t)){error=7;return 0;}
        if(t==1)CAND->map[y][x]=' ';
        if(t==2){CAND->map[y][x]='.';++goals;}
    }
    if(goals!=CAND->box_count){error=7;return 0;}
    memcpy(CAND->boxes,sector_buffer+48,20);
    if(CAND->player.x>=16 || CAND->player.y>=8 || CAND->map[CAND->player.y][CAND->player.x]=='#'){error=7;return 0;}
    for(i=0;i<CAND->box_count;i++){
        x=CAND->boxes[i].x;y=CAND->boxes[i].y;
        if(x>=16 || y>=8 || CAND->map[y][x]=='#' || (x==CAND->player.x && y==CAND->player.y)){error=7;return 0;}
        for(j=0;j<i;j++)if(x==CAND->boxes[j].x && y==CAND->boxes[j].y){error=7;return 0;}
    }
    memcpy(CAND->map[18],sector_buffer+68,23);CAND->map[18][23]=0;
    CAND->map[19][0]=sector_buffer[126];CAND->map[19][1]=sector_buffer[127];
    level_number=n;return 1;
}
unsigned char save_scan(void)
{
    unsigned char i,nonempty=0;
    unsigned int gen;
    save_valid=0;save_error=0;save_read_ok=0;
    for(i=0;i<2;i++){
        if(sio_read(8100+i)!=1)continue;
        ++save_read_ok;if(sector_buffer[0])nonempty=1;
        if(!valid_record())continue;
        gen=word(sector_buffer+8);
        if(!save_valid || (signed int)(gen-save_generation)>0){
            memcpy(save_record,sector_buffer,128);save_slot=i;save_generation=gen;save_valid=1;
        }
    }
    if(!save_valid)save_error=save_read_ok<2?3:nonempty?2:1;
    return save_valid;
}
unsigned char save_apply(void)
{
    unsigned char i,j,x,y;
    if(!save_valid || save_record[5]!=level_number || word(save_record+14)!=level_crc || save_record[18]!=gs.box_count)return 0;
    x=save_record[16];y=save_record[17];
    if(x>=gs.width || y>=gs.height || gs.map[y][x]=='#')return 0;
    for(i=0;i<gs.box_count;i++){
        x=save_record[19+i*2];y=save_record[20+i*2];
        if(x>=gs.width || y>=gs.height || gs.map[y][x]=='#' || (x==save_record[16] && y==save_record[17]))return 0;
        if(save_record[7] && (level_number!=59 || gs.map[y][x]!='.'))return 0;
        for(j=0;j<i;j++)if(x==save_record[19+j*2] && y==save_record[20+j*2])return 0;
    }
    gs.player.x=save_record[16];gs.player.y=save_record[17];memcpy(gs.boxes,save_record+19,20);
    memcpy(&gs.moves,save_record+39,4);memcpy(&gs.pushes,save_record+43,4);
    music_enabled=save_record[6]&1;sfx_enabled=(save_record[6]>>1)&1;save_complete=save_record[7]&1;
    save_error=0;undo_reset();return 1;
}
unsigned char save_previous(void)
{
    save_slot^=1;
    if(sio_read(8100+save_slot)!=1 || !valid_record())return 0;
    memcpy(save_record,sector_buffer,128);save_generation=word(save_record+8);return 1;
}
unsigned char save_write(void)
{
    unsigned char target;
    unsigned int next;
    /* Discover the newest durable generation; failed writes never advance it. */
    save_scan();if(save_read_ok!=2){save_error=4;return 0;}
    target=save_valid?(save_slot^1):0;next=save_valid?save_generation+1:1;
    memset(save_record,0,128);memcpy(save_record,"NSAV",4);
    save_record[4]=1;save_record[5]=scene;save_record[6]=music_enabled|(sfx_enabled<<1);save_record[7]=save_complete;
    save_record[8]=next;save_record[9]=next>>8;memcpy(save_record+10,campaign_id,4);
    save_record[14]=level_crc;save_record[15]=level_crc>>8;save_record[16]=gs.player.x;save_record[17]=gs.player.y;
    save_record[18]=gs.box_count;memcpy(save_record+19,gs.boxes,20);memcpy(save_record+39,&gs.moves,4);memcpy(save_record+43,&gs.pushes,4);
    next=checksum(save_record);save_record[126]=next;save_record[127]=next>>8;
    memcpy(sector_buffer,save_record,128);
    if(sio_write(8100+target)!=1 || sio_read(8100+target)!=1 || memcmp(sector_buffer,save_record,128)){save_error=4;return 0;}
    save_error=0;save_valid=1;save_slot=target;save_generation=word(save_record+8);return 1;
}
