#include <string.h>
#include "candidate.h"
extern unsigned int loading_done;
extern unsigned char loading_progress;
void __fastcall__ loading_label(unsigned char kind);
#define progress_total (*(unsigned int *)0x17d2)
#define stage_mode (*(unsigned char *)0x17df)
static unsigned int package_done, high_water[7];
static unsigned char catalog[128],catalog_ready,reading_catalog;
static unsigned char progress_kind,progress_epoch;
void loading_update(void);
static void progress_step(void){
    unsigned int v;
    if(package_done<=high_water[progress_kind])return;
    ++loading_done;
    v=loading_done*31/progress_total;
    if(v>31)v=31;
    if(v>loading_progress)loading_progress=(unsigned char)v;
    loading_update();
}
#pragma code-name(push,"LOADER")
#pragma rodata-name(push,"LOADCONST")
#pragma bss-name(push,"LOADBSS")
unsigned char loaded,error;
unsigned int load_reads;
unsigned int crc;
static unsigned int sector;
static unsigned char cursor;
/* Sector/header and destinations have explicit ownership, not linker BSS. */
unsigned char *sector_buffer_pointer=(unsigned char *)0x9c00;
#pragma bss-name(pop)
static unsigned int word(const volatile unsigned char *p){return p[0]|((unsigned int)p[1]<<8);}
void __fastcall__ crc_byte(unsigned char b);
static unsigned char check(const unsigned char *p,unsigned int n,unsigned int expected){crc=0xffff;while(n--)crc_byte(*p++);return crc==expected;}
static unsigned char read(void){unsigned char n;for(n=0;n<2;n++){++load_reads;if(sio_read(sector)==1){if(progress_total && !reading_catalog){++package_done;progress_step();if(package_done>high_water[progress_kind])high_water[progress_kind]=package_done;}return 1;}}error=1;return 0;}
static unsigned char byte(unsigned char *p){if(cursor==128){++sector;if(!read())return 0;cursor=0;}*p=sector_buffer[cursor++];return 1;}
/* Exact address/length allowlists prevent forged sections touching error UI,
 * stacks, resident state or header. No arbitrary writes from package metadata. */
static const unsigned int addresses[9]={0x8c00,0xa000,0xa400,0xa800,0xac00,0x9800,0x1400,0xb160,0x9de0};
static const unsigned int lengths[9]={1024,1024,1024,1024,1024,880,800,1280,544};
static const unsigned int menu_addr[4]={0xa000,0xb000,0x8c00,0xb400};
static const unsigned int menu_size[4]={3200,800,1024,1200};
unsigned char __fastcall__ load_package(unsigned char kind)
{
    unsigned int start,count,total,at,n,size,expected,sum,whole;
    unsigned char i,k,b,ok=0,sections;
    unsigned char *dest;
    asset_load_begin();loading_label(kind);loaded=0;error=0;load_reads=0;
    if(progress_epoch!=REG(0x17dc)){memset(high_water,0,sizeof(high_water));progress_epoch=REG(0x17dc);}
    progress_kind=kind;package_done=0;
    /* Catalog is fixed6 records: header + entries protected by CRC. */
    if(!catalog_ready){
        reading_catalog=1;sector=4;if(!read()){reading_catalog=0;goto end;}reading_catalog=0;
        if(memcmp(sector_buffer,"NSRD",4) || sector_buffer[4]!=2 || sector_buffer[5]!=5 ||
           !check(sector_buffer,126,word(sector_buffer+126))){error=2;goto end;}
        memcpy(catalog,sector_buffer,128);catalog_ready=1;
        if(stage_mode==0x65)++loading_done;
    }
    memcpy(sector_buffer,catalog,128);
    if(kind<1 || kind>5){error=2;goto end;}
    at=16+(unsigned int)(kind-1)*16;
    if(sector_buffer[at]!=kind){error=2;goto end;}
    start=word(sector_buffer+at+2);count=word(sector_buffer+at+4);total=word(sector_buffer+at+6);
    if(start<5 || total<144 || count!=(total+127)/128 || start>65535U-count){error=2;goto end;}
    if(stage_mode!=0x65){progress_total=count+2;}
    /* Directory success above is counted once through the same high water. */
    sector=start;if(!read())goto end;cursor=0;
    for(n=0;n<144;n++)if(!byte(HEADER+n))goto end;
    if(memcmp(HEADER,"NSRQ",4) || HEADER[4]!=2 || HEADER[5]!=kind || HEADER[7] ||
       word(HEADER+8)!=total-144 || !check(HEADER,14,word(HEADER+14)) ||
       !check(HEADER+16,128,word(HEADER+12))){error=3;goto end;}
    sections=kind<4?9:kind==4?4:1;
    if(HEADER[6]!=sections){error=3;goto end;}
    sum=0;
    for(i=0;i<sections;i++){
        at=16+(unsigned int)i*8;
        if(kind<4){expected=addresses[i];size=lengths[i];}
        else if(kind==4){expected=menu_addr[i];size=menu_size[i];}
        else{expected=0x1800;size=1552;}
        if(word(HEADER+at)!=expected || word(HEADER+at+2)!=size || word(HEADER+at+4)!=sum){error=5;goto end;}
        sum+=size;
    }
    if(sum!=word(HEADER+8)){error=5;goto end;}
    for(k=16+sections*8;k<144;k++)if(HEADER[k]){error=5;goto end;}
    whole=0xffff;
    for(i=0;i<sections;i++){
        at=16+(unsigned int)i*8;dest=(unsigned char *)word(HEADER+at);size=word(HEADER+at+2);crc=0xffff;
        for(n=0;n<size;n++){
            if(!byte(&b))goto end;
            dest[n]=b;
            /* Section and complete-body CRC checked before activation. */
            crc_byte(b);expected=crc;crc=whole;crc_byte(b);whole=crc;crc=expected;
        }
        if(crc!=word(HEADER+at+6)){error=4;goto end;}

    }
    if(whole!=word(HEADER+10)){error=4;goto end;}
    if(kind<4 && !validate_descriptor(kind)){error=5;goto end;}
    ++package_done;progress_step();if(package_done>high_water[progress_kind])high_water[progress_kind]=package_done;loaded=kind;ok=1;
end:
    asset_load_end();input_rearm();return ok;
}
#pragma code-name(pop)
#pragma rodata-name(pop)
