/* NEON SHIFT 65 read-only observation patch for Atari800 7.1.2.
 * Used only in a separate local emulator copy; game bytes remain unchanged.
 * Atari800 is GPL-2.0-or-later; see its COPYING and DOC/CREDITS.
 */
#include "screen.h"
#include "gtia.h"
#include "file_export.h"
static unsigned ns65_isr_pc[6], ns65_isr_count[3], ns65_isr_max[3];
static unsigned long long ns65_isr_begin[3], ns65_isr_total[3];
static unsigned ns65_outside,ns65_outside_first,ns65_outside_pc,ns65_max_sp;
static unsigned ns65_sp_address=0x82;
static unsigned ns65_flow_address=65535,ns65_warehouse,ns65_work_active;
static unsigned long long ns65_work_last,ns65_work[4];
static FILE *ns65_work_csv;
static unsigned ns65_logic_pc,ns65_audio_pc,ns65_render_pc;
static unsigned ns65_main_pc, ns65_begin_pc, ns65_end_pc;
static unsigned ns65_min_sp=0x8800, ns65_min_s=255, ns65_started;
static const char *ns65_dir;
static FILE *ns65_sio;
static unsigned ns65_sio_return,ns65_sio_sector,ns65_sio_bytes,ns65_sio_buffer,ns65_sio_count;
static unsigned long long ns65_sio_begin;
static FILE *ns65_events,*ns65_routines;
static unsigned ns65_routine_pc[8], ns65_routine_return[8], ns65_routine_count[8], ns65_routine_max[8];
static unsigned long long ns65_routine_begin[8], ns65_routine_total[8];
static void NS65_Observe(unsigned pc, unsigned hw_s)
{
    static int init;
    unsigned csp;
    if (!init) {
        const char *v;char path[1024];init=1;ns65_dir=getenv("NS65_OUTPUT");
        if (!ns65_dir) return;
        v=getenv("NS65_ISRS");if(v)sscanf(v,"%x,%x,%x,%x,%x,%x",&ns65_isr_pc[0],&ns65_isr_pc[1],&ns65_isr_pc[2],&ns65_isr_pc[3],&ns65_isr_pc[4],&ns65_isr_pc[5]);
        v=getenv("NS65_SP");if(v)ns65_sp_address=(unsigned)strtoul(v,NULL,16);
        v=getenv("NS65_FLOW");if(v)ns65_flow_address=(unsigned)strtoul(v,NULL,16);
        ns65_warehouse=getenv("NS65_WAREHOUSE")!=NULL;
        v=getenv("NS65_MARKERS");if(v)sscanf(v,"%x,%x,%x",&ns65_main_pc,&ns65_begin_pc,&ns65_end_pc);
        v=getenv("NS65_PROFILE");if(v)sscanf(v,"%x,%x,%x",&ns65_logic_pc,&ns65_audio_pc,&ns65_render_pc);
        v=getenv("NS65_ROUTINES");if(v)sscanf(v,"%x,%x,%x,%x,%x,%x,%x,%x",&ns65_routine_pc[0],&ns65_routine_pc[1],&ns65_routine_pc[2],&ns65_routine_pc[3],&ns65_routine_pc[4],&ns65_routine_pc[5],&ns65_routine_pc[6],&ns65_routine_pc[7]);
        snprintf(path,sizeof(path),"%s/events.csv",ns65_dir);ns65_events=fopen(path,"w");
        if(ns65_events)fprintf(ns65_events,"frame,clock,pc,event,csp,hw_s,phase\n");
    }
    if (!ns65_dir) return;
    if(ns65_work_active){
        unsigned phase=MEMORY_mem[ns65_flow_address],category;
        category=(ns65_warehouse && ns65_routine_return[0])?2:
            (ns65_warehouse && (ns65_routine_return[1] || ns65_routine_return[2] || ns65_routine_return[7]))?1:
            (phase==1 || phase==2)?0:3;
        ns65_work[category]+=ANTIC_CPU_CLOCK-ns65_work_last;
    }
    ns65_work_last=ANTIC_CPU_CLOCK;
    if(pc==ns65_begin_pc)ns65_work_active=1;
    if(pc==ns65_end_pc)ns65_work_active=0;
    if(pc==0xE459 && MEMORY_mem[0x0302]==0x52 && MEMORY_mem[0x0300]==0x31){
        char path[1024];
        if(!ns65_sio){snprintf(path,sizeof(path),"%s/sio.csv",ns65_dir);ns65_sio=fopen(path,"w");if(ns65_sio)fprintf(ns65_sio,"read,sector,bytes,buffer,status,begin,end,clocks,frame\n");}
        ns65_sio_sector=MEMORY_mem[0x030A]+256u*MEMORY_mem[0x030B];
        ns65_sio_bytes=MEMORY_mem[0x0308]+256u*MEMORY_mem[0x0309];
        ns65_sio_buffer=MEMORY_mem[0x0304]+256u*MEMORY_mem[0x0305];
        ns65_sio_begin=ANTIC_CPU_CLOCK;
        ns65_sio_return=1+MEMORY_mem[0x100+((hw_s+1)&255)]+256u*MEMORY_mem[0x100+((hw_s+2)&255)];
    }else if(ns65_sio_return && pc==ns65_sio_return){
        char path[1024];FILE *f;
        if(ns65_sio)fprintf(ns65_sio,"%u,%u,%u,%u,%u,%llu,%llu,%llu,%u\n",ns65_sio_count,ns65_sio_sector,ns65_sio_bytes,ns65_sio_buffer,MEMORY_mem[0x0303],ns65_sio_begin,(unsigned long long)ANTIC_CPU_CLOCK,(unsigned long long)ANTIC_CPU_CLOCK-ns65_sio_begin,(unsigned)Atari800_nframes);
        snprintf(path,sizeof(path),"%s/read-%05u.bin",ns65_dir,ns65_sio_count);f=fopen(path,"wb");
        if(f){if(ns65_sio_bytes<=256 && ns65_sio_buffer+ns65_sio_bytes<=0xC000)fwrite(MEMORY_mem+ns65_sio_buffer,1,ns65_sio_bytes,f);fclose(f);}
        ++ns65_sio_count;ns65_sio_return=0;
    }
    if(!ns65_routines){char path[1024];snprintf(path,sizeof(path),"%s/routines.csv",ns65_dir);ns65_routines=fopen(path,"w");if(ns65_routines)fprintf(ns65_routines,"index,begin,end,clocks,frame\n");}
    {unsigned i;for(i=0;i<8;i++){
        if(ns65_routine_return[i] && pc==ns65_routine_return[i]) {
            unsigned elapsed=(unsigned)(ANTIC_CPU_CLOCK-ns65_routine_begin[i]);
            if(ns65_routines)fprintf(ns65_routines,"%u,%llu,%llu,%u,%u\n",i,ns65_routine_begin[i],(unsigned long long)ANTIC_CPU_CLOCK,elapsed,(unsigned)Atari800_nframes);
            ++ns65_routine_count[i];ns65_routine_total[i]+=elapsed;
            if(elapsed>ns65_routine_max[i])ns65_routine_max[i]=elapsed;
            ns65_routine_return[i]=0;
        }
        if(ns65_routine_pc[i] && pc==ns65_routine_pc[i]) {
            ns65_routine_begin[i]=ANTIC_CPU_CLOCK;
            ns65_routine_return[i]=1+MEMORY_mem[0x100+((hw_s+1)&255)]+256u*MEMORY_mem[0x100+((hw_s+2)&255)];
        }
    }}
    {unsigned i;for(i=0;i<3;i++){
        if(pc==ns65_isr_pc[i*2])ns65_isr_begin[i]=ANTIC_CPU_CLOCK;
        if(pc==ns65_isr_pc[i*2+1] && ns65_isr_begin[i]){unsigned elapsed=(unsigned)(ANTIC_CPU_CLOCK-ns65_isr_begin[i]);++ns65_isr_count[i];ns65_isr_total[i]+=elapsed;if(elapsed>ns65_isr_max[i])ns65_isr_max[i]=elapsed;ns65_isr_begin[i]=0;}
    }}
    if(pc==ns65_main_pc)ns65_started=1;
    csp=MEMORY_mem[ns65_sp_address]+256u*MEMORY_mem[ns65_sp_address+1];
    if(ns65_started && csp>=0x8000 && csp<=0x8800 && csp<ns65_min_sp)ns65_min_sp=csp;
    if(ns65_started) {
        if(csp>ns65_max_sp)ns65_max_sp=csp;
        if(csp<0x8000 || csp>0x8800){++ns65_outside;if(!ns65_outside_first){ns65_outside_first=csp;ns65_outside_pc=pc;}}
    }
    if(ns65_started && hw_s<ns65_min_s)ns65_min_s=hw_s;
    if(ns65_events && (pc==ns65_main_pc || pc==ns65_begin_pc || pc==ns65_end_pc || pc==ns65_logic_pc || pc==ns65_audio_pc || pc==ns65_render_pc))
        fprintf(ns65_events,"%u,%llu,%04x,%s,%u,%u,%u\n",(unsigned)Atari800_nframes,(unsigned long long)ANTIC_CPU_CLOCK,pc,pc==ns65_main_pc?"main":pc==ns65_begin_pc?"begin":pc==ns65_end_pc?"end":pc==ns65_logic_pc?"logic":pc==ns65_audio_pc?"audio":"render",csp,hw_s,(unsigned)MEMORY_mem[ns65_flow_address]);
}
/* Snapshot read-only rendering source BEFORE the visible raster. A VBI at
 * frame end may already publish next frame's animation/HUD into RAM. */
void NS65_BeforeRaster(void);
void NS65_BeforeRaster(void)
{
    const char *captures=getenv("NS65_CAPTURE");
    unsigned frame=(unsigned)Atari800_nframes+1;
    if(!ns65_dir)return;
    while(captures && *captures){char *next;unsigned n=(unsigned)strtoul(captures,&next,10);
        if(n==frame){char path[1024];FILE *f;
            snprintf(path,sizeof(path),"%s/raster-%04u.ram",ns65_dir,frame);
            f=fopen(path,"wb");if(f){fwrite(MEMORY_mem,1,0xC000,f);fclose(f);}
        }
        if(next==captures)break;captures=(*next==',')?next+1:next;
    }
}
void NS65_Frame(void);
void NS65_Frame(void)
{
    unsigned frame=(unsigned)Atari800_nframes;
    const char *captures,*limit;
    if(!ns65_dir)return;
    if(!ns65_work_csv){char path[1024];snprintf(path,sizeof(path),"%s/work.csv",ns65_dir);ns65_work_csv=fopen(path,"w");if(ns65_work_csv)fprintf(ns65_work_csv,"frame,game,build,load,ui\n");}
    if(ns65_work_csv)fprintf(ns65_work_csv,"%u,%llu,%llu,%llu,%llu\n",frame,ns65_work[0],ns65_work[1],ns65_work[2],ns65_work[3]);
    {unsigned i;for(i=0;i<4;i++)ns65_work[i]=0;}
    if(frame==80 && getenv("NS65_AUDIO"))File_Export_StartRecording(getenv("NS65_AUDIO"));
    captures=getenv("NS65_CAPTURE");limit=getenv("NS65_LIMIT");
    while(captures && *captures){char *next;unsigned n=(unsigned)strtoul(captures,&next,10);if(n==frame){char path[1024];FILE *f;
        snprintf(path,sizeof(path),"%s/video-%04u.json",ns65_dir,frame);f=fopen(path,"w");if(f){fprintf(f,"{\"chbase\":%u,\"dma\":%u,\"colpf\":[%u,%u,%u,%u],\"colbk\":%u}\n",ANTIC_CHBASE,ANTIC_DMACTL,GTIA_COLPF0,GTIA_COLPF1,GTIA_COLPF2,GTIA_COLPF3,GTIA_COLBK);fclose(f);}
        snprintf(path,sizeof(path),"%s/frame-%04u.ram",ns65_dir,frame);f=fopen(path,"wb");if(f){fwrite(MEMORY_mem,1,0xC000,f);fclose(f);}
        snprintf(path,sizeof(path),"%s/native-%04u.png",ns65_dir,frame);if(!Screen_SaveScreenshot(path,FALSE))fprintf(stderr,"NS65 screenshot failed\n");
    }if(next==captures)break;captures=(*next==',')?next+1:next;}
    if(limit && frame>=(unsigned)atoi(limit)){char path[1024];FILE *f;
        snprintf(path,sizeof(path),"%s/hud-timing.json",ns65_dir);f=fopen(path,"w");if(f){fprintf(f,"{\"routines\":[\"display_counters\",\"display_hud\"],\"samples\":[%u,%u],\"max_clocks\":[%u,%u],\"total_clocks\":[%llu,%llu]}\n",ns65_routine_count[0],ns65_routine_count[1],ns65_routine_max[0],ns65_routine_max[1],ns65_routine_total[0],ns65_routine_total[1]);fclose(f);}
        snprintf(path,sizeof(path),"%s/timing.json",ns65_dir);f=fopen(path,"w");if(f){fprintf(f,"{\"isr_max_clocks\":[%u,%u,%u],\"isr_samples\":[%u,%u,%u],\"isr_total_clocks\":[%llu,%llu,%llu],\"frames\":%u,\"min_csp\":%u,\"c_stack_sample_peak\":%u,\"min_hardware_s\":%u,\"hardware_stack_observed_peak\":%u,\"csp_outside_samples\":%u,\"csp_outside_first\":%u,\"csp_outside_pc\":%u,\"max_csp\":%u}\n",ns65_isr_max[0],ns65_isr_max[1],ns65_isr_max[2],ns65_isr_count[0],ns65_isr_count[1],ns65_isr_count[2],ns65_isr_total[0],ns65_isr_total[1],ns65_isr_total[2],frame,ns65_min_sp,0x8800-ns65_min_sp,ns65_min_s,255-ns65_min_s,ns65_outside,ns65_outside_first,ns65_outside_pc,ns65_max_sp);fclose(f);}
        snprintf(path,sizeof(path),"%s/routine-timing.json",ns65_dir);f=fopen(path,"w");
        if(f){unsigned i;fprintf(f,"{\"names\":[\"display_counters\",\"display_hud\",\"game_start\",\"game_step\",\"undo_pop\",\"display_changed\",\"display_animate\",\"display_board\"],\"samples\":[");for(i=0;i<8;i++)fprintf(f,"%s%u",i?",":"",ns65_routine_count[i]);fprintf(f,"],\"max_clocks\":[");for(i=0;i<8;i++)fprintf(f,"%s%u",i?",":"",ns65_routine_max[i]);fprintf(f,"]}\n");fclose(f);}
        if(ns65_sio)fclose(ns65_sio);
        if(ns65_work_csv)fclose(ns65_work_csv);
        if(ns65_routines)fclose(ns65_routines);
        if(ns65_events)fclose(ns65_events);Atari800_Exit(FALSE);exit(0);
    }
}
