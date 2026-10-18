/* Additional read-only observer, compiled only into the private emulator. */
#include "pia.h"
#include "pokey.h"
static FILE *nsq_cpu,*nsq_input,*nsq_pub;
static unsigned nsq_end_pc,nsq_pub_pc,nsq_pending,nsq_count,nsq_lo,nsq_hi,nsq_gs,nsq_phase;
static unsigned nsq_return[8],nsq_depth[8],nsq_active_pub;
static long long nsq_start_cpu[8];
static unsigned long long nsq_start_clock[8];
static const char *nsq_repair_marker,*nsq_truncate_marker;
static unsigned nsq_loaded;
static FILE *nsq_state;
static FILE *nsq_trace;
static unsigned nsq_trace_pc[20],nsq_trace_ret[20],nsq_trace_epoch,nsq_trace_ready;
static unsigned nsq_last_hud=999,nsq_last_ready=999;
static unsigned nsq_meta[6];
static void NSQ_TraceRow(unsigned event,unsigned edge)
{
    unsigned long moves=0,pushes=0,sm=0,sp=0;unsigned i,re=0,ce=0;
    if(!nsq_trace)return;
    for(i=0;i<4;i++){moves|=(unsigned long)MEMORY_mem[nsq_gs+785+i]<<(8*i);pushes|=(unsigned long)MEMORY_mem[nsq_gs+789+i]<<(8*i);}
    if(nsq_meta[0]){
        re=MEMORY_mem[nsq_meta[0]]+256u*MEMORY_mem[nsq_meta[0]+1];ce=MEMORY_mem[nsq_meta[1]]+256u*MEMORY_mem[nsq_meta[1]+1];
        for(i=0;i<4;i++){sm|=(unsigned long)MEMORY_mem[nsq_meta[2]+i]<<(8*i);sp|=(unsigned long)MEMORY_mem[nsq_meta[3]+i]<<(8*i);}
    }
    fprintf(nsq_trace,"%llu,%lld,%lld,%u,%u,%u,%u,%u,%u,%u,%lu,%lu,%u,%u,%u,%u,%u,%lu,%lu,%u,%u,%u\n",(unsigned long long)ANTIC_CPU_CLOCK,nsq_all,nsq_foreground,(unsigned)Atari800_nframes+1,event,edge,nsq_irq_depth,MEMORY_mem[nsq_phase],MEMORY_mem[nsq_gs+762],MEMORY_mem[nsq_gs+763],moves,pushes,MEMORY_mem[nsq_trace_epoch]+256u*MEMORY_mem[nsq_trace_epoch+1],MEMORY_mem[nsq_trace_ready],CPU_regA,re,ce,sm,sp,nsq_meta[4]?MEMORY_mem[nsq_meta[4]]:0,nsq_meta[5]?MEMORY_mem[nsq_meta[5]]:0,(unsigned)ANTIC_ypos);
}
static unsigned nsq_loading,nsq_calls,nsq_head,nsq_tail,nsq_music_order,nsq_music_row,nsq_music_tick;
static unsigned long long nsq_isr_clock[3];
static long long nsq_isr_cpu[3];
static void NSQ_StateFrame(void)
{
    char path[1024];
    if(!nsq_state){snprintf(path,sizeof(path),"%s/frame-schedule.csv",ns65_dir);nsq_state=fopen(path,"w");if(nsq_state)fprintf(nsq_state,"frame,clock,cpu_all,cpu_foreground,loading,phase,audio_calls,queue,skctl,audctl,order,row,tick,audc1,audc2,audc3,audc4\n");}
    if(nsq_state)fprintf(nsq_state,"%u,%llu,%lld,%lld,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",(unsigned)Atari800_nframes,(unsigned long long)ANTIC_CPU_CLOCK,nsq_all,nsq_foreground,MEMORY_mem[nsq_loading],MEMORY_mem[nsq_phase],MEMORY_mem[nsq_calls],(unsigned char)(MEMORY_mem[nsq_head]-MEMORY_mem[nsq_tail]),POKEY_SKCTL,POKEY_AUDCTL[0],MEMORY_mem[nsq_music_order],MEMORY_mem[nsq_music_row],MEMORY_mem[nsq_music_tick],POKEY_AUDC[0],POKEY_AUDC[1],POKEY_AUDC[2],POKEY_AUDC[3]);
}
void NSQ_InputFrame(void);
void NSQ_InputFrame(void)
{
    char path[1024];
    if(!ns65_dir)return;
    if(!nsq_input){snprintf(path,sizeof(path),"%s/input-clock.csv",ns65_dir);nsq_input=fopen(path,"w");if(nsq_input)fprintf(nsq_input,"frame,clock,stick,fire,consol\n");}
    if(nsq_input)fprintf(nsq_input,"%u,%llu,%u,%u,%u\n",(unsigned)Atari800_nframes+1,(unsigned long long)ANTIC_CPU_CLOCK,PIA_GetByte(0xD300,TRUE)&15,GTIA_TRIG[0],GTIA_GetByte(0xD01F,TRUE)&7);
}
static void NSQ_Observe(unsigned pc,unsigned hw_s)
{
    static int init;unsigned i;
    if(!init){const char *v;char path[1024];init=1;
        nsq_repair_marker=getenv("NSQ_REPAIR_MARKER");nsq_truncate_marker=getenv("NSQ_TRUNCATE_MARKER");
        v=getenv("NSQ_LOADED");if(v)nsq_loaded=(unsigned)strtoul(v,NULL,16);
        v=getenv("NSQ_STATE");if(v)sscanf(v,"%x,%x,%x,%x,%x,%x,%x",&nsq_loading,&nsq_calls,&nsq_head,&nsq_tail,&nsq_music_order,&nsq_music_row,&nsq_music_tick);
        v=getenv("NSQ_ADDRS");if(v)sscanf(v,"%x,%x,%x,%x,%x,%x,%x,%x",&nsq_end_pc,&nsq_pub_pc,&nsq_pending,&nsq_count,&nsq_lo,&nsq_hi,&nsq_gs,&nsq_phase);
        v=getenv("NSQ_TRACE");if(v){const char *q=v;for(i=0;i<20 && *q;i++){nsq_trace_pc[i]=(unsigned)strtoul(q,(char **)&q,16);if(*q==',')++q;}
            snprintf(path,sizeof(path),"%s/timeline.csv",ns65_dir);nsq_trace=fopen(path,"w");if(nsq_trace)fprintf(nsq_trace,"clock,cpu_all,cpu_foreground,frame,event,edge,depth,phase,player_x,player_y,moves,pushes,epoch,ready,a,ready_epoch,committed_epoch,state_moves,state_pushes,state_docks,dirty,ypos\n");}
        v=getenv("NSQ_EPOCH");if(v)sscanf(v,"%x,%x",&nsq_trace_epoch,&nsq_trace_ready);
        v=getenv("NSQ_META");if(v)sscanf(v,"%x,%x,%x,%x,%x,%x",&nsq_meta[0],&nsq_meta[1],&nsq_meta[2],&nsq_meta[3],&nsq_meta[4],&nsq_meta[5]);
        snprintf(path,sizeof(path),"%s/cpu-exclusive.csv",ns65_dir);nsq_cpu=fopen(path,"w");if(nsq_cpu)fprintf(nsq_cpu,"index,begin,end,elapsed,cpu,irq_depth,frame\n");
        snprintf(path,sizeof(path),"%s/publication.csv",ns65_dir);nsq_pub=fopen(path,"w");if(nsq_pub)fprintf(nsq_pub,"clock,frame,ypos,depth,count,row,player_x,player_y,moves\n");
    }
    /* Optional genuine sub-frame device fixture. No Atari RAM writes or
       CPU/raster delays: change the external joystick pins once, log the
       actual instruction-boundary injection clock as the response origin. */
    {static unsigned late_frame,late_y,late_stick=15,late_fire=1;static int late_init,late_done;
     if(!late_init){const char *v=getenv("NSQ_LATE_INPUT");late_init=1;if(v)sscanf(v,"%u,%u,%u,%u",&late_frame,&late_y,&late_stick,&late_fire);}
     if(late_frame && !late_done && (unsigned)Atari800_nframes+1==late_frame && (unsigned)ANTIC_ypos>=late_y){
       char path[1024];FILE *f;late_done=1;PIA_PORT_input[0]=(PIA_PORT_input[0]&240)|(late_stick&15);GTIA_TRIG[0]=late_fire&1;
       snprintf(path,sizeof(path),"%s/subframe-input.csv",ns65_dir);f=fopen(path,"w");if(f){fprintf(f,"frame,clock,ypos,stick,fire\n%u,%llu,%u,%u,%u\n",late_frame,(unsigned long long)ANTIC_CPU_CLOCK,(unsigned)ANTIC_ypos,late_stick,late_fire);fclose(f);}
     }}
    {static unsigned poll_pc,sample_pc;static int configured;static FILE *f;
     unsigned frame=(unsigned)Atari800_nframes+1;
     if(!configured){const char *v=getenv("NSQ_INPUT_CAPTURE");configured=1;
       if(v)sscanf(v,"%x,%x",&poll_pc,&sample_pc);}
     if(frame>=635 && frame<=647 && ((poll_pc && pc==poll_pc) || (sample_pc && pc==sample_pc))){
       if(!f){char path[1024];snprintf(path,sizeof(path),"%s/input-capture.csv",ns65_dir);f=fopen(path,"w");
         if(f)fprintf(f,"frame,clock,ypos,kind,stick,fire,consol\n");}
       if(f)fprintf(f,"%u,%llu,%u,%u,%u,%u,%u\n",frame,(unsigned long long)ANTIC_CPU_CLOCK,
         (unsigned)ANTIC_ypos,pc==poll_pc?0:1,PIA_GetByte(0xD300,TRUE)&15,
         GTIA_TRIG[0],GTIA_GetByte(0xD01F,TRUE)&7);
     }}
    for(i=0;i<20;i++){
        if(nsq_trace_ret[i] && pc==nsq_trace_ret[i]){NSQ_TraceRow(i,1);nsq_trace_ret[i]=0;}
        if(nsq_trace_pc[i] && pc==nsq_trace_pc[i]){NSQ_TraceRow(i,0);nsq_trace_ret[i]=1+MEMORY_mem[0x100+((hw_s+1)&255)]+256u*MEMORY_mem[0x100+((hw_s+2)&255)];}
    }
    if(nsq_trace && nsq_trace_ready && MEMORY_mem[nsq_trace_ready]!=nsq_last_ready){nsq_last_ready=MEMORY_mem[nsq_trace_ready];NSQ_TraceRow(24,nsq_last_ready);}
    for(i=0;i<8;i++){
        if(nsq_return[i] && pc==nsq_return[i]){
            long long exclusive=(nsq_depth[i]?nsq_all:nsq_foreground)-nsq_start_cpu[i];
            if(nsq_cpu)fprintf(nsq_cpu,"%u,%llu,%llu,%llu,%lld,%u,%u\n",i,nsq_start_clock[i],(unsigned long long)ANTIC_CPU_CLOCK,(unsigned long long)ANTIC_CPU_CLOCK-nsq_start_clock[i],exclusive,nsq_depth[i],(unsigned)Atari800_nframes);
            nsq_return[i]=0;
        }
        if(ns65_routine_pc[i] && pc==ns65_routine_pc[i]){
            nsq_return[i]=1+MEMORY_mem[0x100+((hw_s+1)&255)]+256u*MEMORY_mem[0x100+((hw_s+2)&255)];
            nsq_depth[i]=nsq_irq_depth;nsq_start_cpu[i]=nsq_irq_depth?nsq_all:nsq_foreground;nsq_start_clock[i]=ANTIC_CPU_CLOCK;
        }
    }
    for(i=0;i<3;i++){
        if(pc==ns65_isr_pc[i*2]){nsq_isr_clock[i]=ANTIC_CPU_CLOCK;nsq_isr_cpu[i]=nsq_all;}
        if(pc==ns65_isr_pc[i*2+1] && nsq_isr_clock[i]){
            if(nsq_cpu)fprintf(nsq_cpu,"%u,%llu,%llu,%llu,%lld,%u,%u\n",8+i,nsq_isr_clock[i],(unsigned long long)ANTIC_CPU_CLOCK,(unsigned long long)ANTIC_CPU_CLOCK-nsq_isr_clock[i],nsq_all-nsq_isr_cpu[i],nsq_irq_depth,(unsigned)Atari800_nframes);
            nsq_isr_clock[i]=0;
            /* A heavy deferred VBI can finish after PAL frame wrap, while
               still before the first physical content line32. The frame-start
               snapshot then predates a safe complete ambient/HUD commit. */
            if(i==0 && ANTIC_ypos<32)NS65_BeforeRaster();
        }
    }
    if(pc==nsq_pub_pc && MEMORY_mem[nsq_pending]){
        unsigned count=MEMORY_mem[nsq_count],row=23;unsigned long moves=0;
        for(i=0;i<count && i<32;i++){unsigned address=MEMORY_mem[nsq_lo+i]+256u*MEMORY_mem[nsq_hi+i];if(address>=0x8800 && address<0x8BC0 && (address-0x8800)/40<row)row=(address-0x8800)/40;}
        for(i=0;i<4;i++)moves|=(unsigned long)MEMORY_mem[nsq_gs+785+i]<<(i*8);
        if(nsq_pub)fprintf(nsq_pub,"%llu,%u,%u,%u,%u,%u,%u,%u,%lu\n",(unsigned long long)ANTIC_CPU_CLOCK,(unsigned)Atari800_nframes+1,(unsigned)ANTIC_ypos,nsq_irq_depth,count,row,MEMORY_mem[nsq_gs+762],MEMORY_mem[nsq_gs+763],moves);
        if(!nsq_irq_depth)nsq_active_pub=1;
    }
    /* The foreground publisher only commits before its affected rows. Refresh
     * the oracle's RAM for this raster after it has completed. Pixel comparison
     * still detects any prematurely drawn old row / partially copied glyph. */
    if(pc==nsq_end_pc && nsq_active_pub){nsq_active_pub=0;if(ANTIC_ypos<216)NS65_BeforeRaster();}
    /* External disk-repair fixture watches this flushed marker; no writes to
       emulated RAM and no artificial CPU delay. */
    if(nsq_repair_marker && MEMORY_mem[nsq_phase]==6){
        static int marked;if(!marked){FILE *f=fopen(nsq_repair_marker,"w");if(f){fprintf(f,"%u\n",(unsigned)Atari800_nframes+1);fclose(f);}marked=1;}
    }
    if(nsq_truncate_marker && MEMORY_mem[nsq_loaded]==4){
        static int marked;if(!marked){FILE *f=fopen(nsq_truncate_marker,"w");if(f){fprintf(f,"%u\n",(unsigned)Atari800_nframes+1);fclose(f);}marked=1;}
    }
}
