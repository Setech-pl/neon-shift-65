#ifndef QUALIFICATION_H
#define QUALIFICATION_H
#include "game.h"
#include "input.h"
#include "hardware.h"
#include "prototype_assets.h"
#define REG(a) (*(volatile unsigned char *)(a))
#define SCREEN ((unsigned char *)0x8800)
#define BASE ((unsigned char *)0x9800)
#define COMPOSITION ((unsigned char *)0x1400)
#define DESC ((volatile unsigned char *)0x9de0)
#define HEADER ((unsigned char *)0x9b70)
#define HUD ((unsigned char *)0x9000)
#define HUDSTAGE ((unsigned char *)0x9400)
#define DLIST ((unsigned char *)0x9f60)
extern GameState gs;
extern unsigned char phase,scene,facing,loaded,error,selected,previous_phase;
extern unsigned int load_reads;
extern volatile unsigned char publish_pending,publish_count,publish_addr_lo[32],publish_addr_hi[32],publish_code[32];
extern volatile unsigned char robot_bank_a,robot_bank_b,robot_copy,ambient_active,menu_active;
extern volatile unsigned char palette_dim,publish_late,audio_calls,publication_vcount;
extern volatile unsigned char dock_timer[10];
extern volatile unsigned char ratio_pending;
extern unsigned char render_board_x,render_board_y;
extern const GameState *render_game;
extern volatile unsigned int render_tile_writes,render_full_boards;
extern unsigned char *render_target,render_limit;
extern unsigned int hud_x;
extern unsigned char hud_pitch;
extern char render_digits[11];
void __fastcall__ render_cell(unsigned int point);
unsigned char __fastcall__ render_docks(const GameState *g);
void __fastcall__ render_hud_text(const char *s);
void __fastcall__ render_number(uint32_t n);
void __fastcall__ render_mono_text(const char *s);
void video_off(void);
void show_menu(void);
void show_play(void);
void show_ui(void);
void display_counters(void);
void hud_request(void);
void hud_work(void);
void hud_invalidate(void);
void hud_cancel(void);
extern volatile unsigned int hud_epoch,hud_ready_epoch,hud_committed_epoch;
extern volatile unsigned char hud_dirty,hud_undo;
extern unsigned char hud_state_docks;
extern volatile unsigned char hud_budget_clock;
void __fastcall__ display_changed(unsigned char delivery);
void publish_now(void);
void __fastcall__ display_animate(unsigned char flags);
unsigned char __fastcall__ load_package(unsigned char kind);
unsigned char __fastcall__ validate_descriptor(unsigned char kind);
void asset_load_begin(void);
void asset_load_end(void);
unsigned char __fastcall__ sio_read(unsigned int sector);
void input_rearm(void);
extern unsigned char sector_buffer[128];
#endif

extern volatile unsigned char input_clock;

unsigned char input_probe(void);
