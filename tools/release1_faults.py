#!/usr/bin/env python3
"""A-02 matrix against the generated campaign.c and real 6502 CRC in sim65.

Device harness derived from independent-audit-claude/repro/audit_fault.py.
The original reproducer and its real two-generation input remain untouched.
"""
import json
import subprocess
import sys
from pathlib import Path

B=Path(sys.argv[1]);O=B/'save-faults';O.mkdir(exist_ok=True)
initial=(Path('docs/independent-audit-claude/repro/save-slots.bin')).read_bytes()
c='''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "campaign.h"
GameState gs; unsigned char scene,error,sector_buffer[128];
volatile unsigned char music_enabled=1,sfx_enabled=1;
unsigned int crc;
void __fastcall__ crc_byte(unsigned char b);
static unsigned char disk[2][128],before[2][128],fail,protect,partial;
static unsigned int writes,target,reads,cases;
void undo_reset(void){}
unsigned char __fastcall__ sio_read(unsigned int sector){
    assert(sector==8100 || sector==8101);++reads;
    if(fail & (1<<(sector-8100)))return 138;
    memcpy(sector_buffer,disk[sector-8100],128);return 1;
}
unsigned char __fastcall__ sio_write(unsigned int sector){
    ++writes;target=sector;assert(sector==8100 || sector==8101);
    if(protect)return 144;
    memcpy(disk[sector-8100],sector_buffer,partial);
    return partial==128?1:138;
}
'''
c+='static const unsigned char initial[256]={'+','.join(map(str,initial))+'};\n'
c+='''
void fix(unsigned char *p){unsigned char i;crc=0xffff;for(i=0;i<126;i++)crc_byte(p[i]);p[126]=crc;p[127]=crc>>8;}
void setup(unsigned char latest,unsigned int gen){
    unsigned char i,j;
    memcpy(disk,initial,256);
    for(i=0;i<2;i++){
        j=i==latest?1:0;
        memcpy(disk[i],initial+j*128,128);
        disk[i][8]=i==latest?gen:gen-1;disk[i][9]=(i==latest?gen:gen-1)>>8;
        fix(disk[i]);
    }
    memcpy(before,disk,256);fail=protect=0;partial=128;writes=reads=target=0;
    memset(&gs,0,sizeof(gs));gs.width=16;gs.height=8;gs.box_count=1;
    memset(gs.map,' ',sizeof(gs.map));level_number=scene=0;
    level_crc=initial[14]|((unsigned int)initial[15]<<8);
    assert(save_scan());assert(save_apply());assert(gs.moves==2);gs.moves=3;
}
int main(void){
    unsigned char latest,f,p;unsigned int g,cut;
    const unsigned int gens[4]={2,0,65535U,1};
    for(latest=0;latest<2;latest++)for(g=0;g<4;g++){
        for(f=1;f<4;f++)for(p=0;p<2;p++){
            setup(latest,gens[g]);fail=f;partial=64;protect=p;
            /* Continue may recover a readable slot. Writes require both. */
            assert(save_scan()==(f!=3));
            assert(!save_write());assert(save_error==4);assert(writes==0);
            assert(reads<=8);assert(!memcmp(disk,before,256));
            fail=0;assert(save_scan());assert(save_apply());assert(gs.moves==2);++cases;
        }
        for(cut=0;cut<128;cut++){
            setup(latest,gens[g]);partial=cut;
            assert(!save_write());assert(save_error==4);assert(writes==1);
            assert(target==8100+(latest^1));assert(!memcmp(disk[latest],before[latest],128));
            assert(save_scan());assert(save_apply());assert(gs.moves==2);++cases;
        }
        setup(latest,gens[g]);protect=1;
        assert(!save_write());assert(save_error==4);assert(!memcmp(disk,before,256));++cases;
        setup(latest,gens[g]);assert(save_write());assert(target==8100+(latest^1));
        assert(!memcmp(disk[latest],before[latest],128));
        assert(save_scan());assert(save_apply());assert(gs.moves==3);++cases;
    }
    printf("PASS %u cases: unreadable slots, both orders, generation wrap, all 128 cuts, protect, success\\n",cases);
    return 0;
}
'''
(O/'fault.c').write_text(c)
cfg=Path('/opt/homebrew/share/cc65/cfg/sim6502.cfg').read_text()
cfg=cfg.replace('    CODE:', '    EXTRA: load = MAIN, type = ro;\n    LOADER: load = MAIN, type = ro;\n    LOADCONST: load = MAIN, type = ro;\n    CODE:')
cfg=cfg.replace('    BSS:', '    PERSIST: load = MAIN, type = bss;\n    BSS:')
(O/'sim.cfg').write_text(cfg)
args=['cl65','-t','sim6502','-Oirs','-Cl','-Isrc','-I'+str(B/'source'),'-I'+str(B)]
with (O/'result.log').open('w') as log:
    objects=[]
    for name,p in [('fault',O/'fault.c'),('campaign',B/'source/campaign.c')]:
        o=O/(name+'.o');subprocess.run([*args,'-c','-o',str(o),str(p)],check=True,stdout=log,stderr=log);objects.append(str(o))
    o=O/'crc.o';subprocess.run(['ca65','-t','sim6502','-o',str(o),str(B/'source/crc.s')],check=True,stdout=log,stderr=log);objects.append(str(o))
    subprocess.run(['cl65','-t','sim6502','-C',str(O/'sim.cfg'),'-o',str(O/'fault'),*objects],check=True,stdout=log,stderr=log)
    subprocess.run(['sim65',str(O/'fault')],check=True,stdout=log,stderr=log)
print((O/'result.log').read_text())
(O/'result.json').write_text(json.dumps(dict(status='PASS',cases=1088,device='sim65 device model, generated production campaign.c and CRC assembly',latest_generation_byte_preserved=True,ATR_physical_partial_write='OWNER_PENDING'),indent=2)+'\n')
