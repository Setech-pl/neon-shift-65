#ifndef CAMPAIGN_H
#define CAMPAIGN_H
#include "candidate.h"
extern unsigned char level_number,save_error,save_valid,save_complete;
/* Campaign boards are exactly16x8. Inactive rows18/19 travel with the
 * candidate GameState, so failed asset loads cannot commit its name/CRC. */
#define level_name (gs.map[18])
#define level_crc (*(unsigned int *)gs.map[19])
unsigned char board_load(unsigned char n);
unsigned char save_scan(void);
unsigned char save_apply(void);
unsigned char save_level(void);
unsigned char save_previous(void);
unsigned char save_write(void);
unsigned char __fastcall__ sio_write(unsigned int sector);
#endif
