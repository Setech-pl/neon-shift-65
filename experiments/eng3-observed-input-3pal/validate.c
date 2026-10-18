/* cc65 V2.18's optimizer incorrectly reuses ptr1 for fixed-address descriptor
 * reads after helper calls/dynamic indexing. Compile THIS validation without
 * -O; adversarial CRC-correct native ATR fixtures exercise every check. */
#include <string.h>
#include "candidate.h"
unsigned char validate_area(void);
static unsigned int word(const volatile unsigned char *p){return p[0]|((unsigned int)p[1]<<8);}
unsigned char __fastcall__ validate_descriptor(unsigned char kind)
{
    unsigned char i,j,k,w,h,bx,by,count;
    unsigned int at,position,n;
    w=DESC[0];h=DESC[1];bx=DESC[2];by=DESC[3];count=DESC[4];
    if(w!=strlen(prototype_levels[kind-1].rows[0]) || h!=prototype_levels[kind-1].height ||
       bx!=20-w || by!=13-h || count>32 || DESC[5]!=kind-1 || !validate_area())return 0;
    for(i=8;i<128;i++)if((DESC[i]&127)>=124)return 0;
    for(n=0;n<800;n++)if((COMPOSITION[n]&127)>=124)return 0;
    for(n=0;n<880;n++)if((BASE[n]&127)>=124)return 0;
    for(i=0;i<count;i++){
        at=128+(unsigned int)i*8;position=word(DESC+at);
        if(position<0x8850 || position>=0x8bc0 || !DESC[at+2] || DESC[at+3]>3)return 0;
        for(j=0;j<i;j++)if(position==word(DESC+128+(unsigned int)j*8))return 0;
        position-=0x8800;n=position/40;k=position%40;
        if(k>=bx && k<bx+w*2 && n>=by && n<by+h*2 &&
           prototype_levels[kind-1].rows[(n-by)/2][(k-bx)/2]!='#')return 0;
        for(k=4;k<8;k++)if((DESC[at+k]&127)>=124)return 0;
    }
    for(n=128+(unsigned int)count*8;n<536;n++)if(DESC[n])return 0;

    return 1;
}
