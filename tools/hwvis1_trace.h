/* Read-only Atari800 observation, private copy only. No device/RAM writes. */
#include "esc.h"
static FILE *hv_frames,*hv_dli;
static unsigned hv_dli_pc,hv_row,hv_load,hv_phase,hv_vbi_pc,hv_dlis,hv_vbis;
static void HWVIS_Observe(unsigned pc) {
    static int init;
    if(!init){const char *v=getenv("HWVIS_ADDRS"),*dir=getenv("NS65_OUTPUT");char path[1024];init=1;
        if(!v || !dir)return;
        sscanf(v,"%x,%x,%x,%x,%x,%x",&hv_dli_pc,&hv_row,&hv_load,&hv_phase,&hv_vbi_pc,&hv_dlis);
        hv_dlis=0;
        snprintf(path,sizeof(path),"%s/hwvis-frames.csv",dir);hv_frames=fopen(path,"w");
        fprintf(hv_frames,"frame,dli,vbi,row,loading,phase,critic,dma,dl,shadow_dl,font,pf0,pf1,pf2,pf3,bk,s0,s1,s2,s3,sbk\n");
        snprintf(path,sizeof(path),"%s/hwvis-dli.csv",dir);hv_dli=fopen(path,"w");
        fprintf(hv_dli,"frame,clock,vcount,row,loading,critic,pf1,pf2,shadow_pf1,shadow_pf2\n");
        snprintf(path,sizeof(path),"%s/hwvis-effective.json",dir);{FILE *f=fopen(path,"w");
        fprintf(f,"{\"machine_type\":%d,\"XLXE_enum\":%d,\"ram_kb\":%d,\"tv_lines\":%d,\"basic_disabled\":%d,\"sio_patch\":%d}\n",Atari800_machine_type,Atari800_MACHINE_XLXE,MEMORY_ram_size,Atari800_tv_mode,Atari800_disable_basic,ESC_enable_sio_patch);fclose(f);}
    }
    if(!hv_frames)return;
    if(pc==hv_vbi_pc)++hv_vbis;
    if(pc==hv_dli_pc){++hv_dlis;fprintf(hv_dli,"%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u\n",(unsigned)Atari800_nframes+1,(unsigned long long)ANTIC_CPU_CLOCK,(unsigned)ANTIC_ypos/2,MEMORY_mem[hv_row],MEMORY_mem[hv_load],MEMORY_mem[0x42],GTIA_COLPF1,GTIA_COLPF2,MEMORY_mem[0x2c5],MEMORY_mem[0x2c6]);}
}
void HWVIS_Frame(void){
    if(!hv_frames)return;
    fprintf(hv_frames,"%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",(unsigned)Atari800_nframes,hv_dlis,hv_vbis,MEMORY_mem[hv_row],MEMORY_mem[hv_load],MEMORY_mem[hv_phase],MEMORY_mem[0x42],ANTIC_DMACTL,ANTIC_dlist,MEMORY_mem[0x230]+256*MEMORY_mem[0x231],ANTIC_CHBASE,GTIA_COLPF0,GTIA_COLPF1,GTIA_COLPF2,GTIA_COLPF3,GTIA_COLBK,MEMORY_mem[0x2c4],MEMORY_mem[0x2c5],MEMORY_mem[0x2c6],MEMORY_mem[0x2c7],MEMORY_mem[0x2c8]);
    hv_dlis=hv_vbis=0;fflush(hv_frames);fflush(hv_dli);
}
