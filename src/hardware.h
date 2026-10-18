#ifndef HARDWARE_H
#define HARDWARE_H
void hardware_init(void);
void frame_begin(void);
void frame_end(void);
void frame_logic(void);
void frame_audio(void);
void frame_render(void);
extern volatile unsigned char background_enabled,hud_enabled;
extern volatile unsigned char background_mask;
extern volatile unsigned char hud_pending;
extern volatile unsigned char display_font,display_pf1,display_pf2;
extern volatile unsigned char dli_font[6],dli_pf1[6],dli_pf2[6];
extern volatile unsigned char video_clock,robot_frame,robot_dirty,display_active;
extern volatile unsigned char music_enabled,sfx_enabled,sound_track,sound_request;
extern volatile unsigned char input_head,input_tail,input_overflows;
extern volatile unsigned char infra_enabled,infra_frame,infra_dirty;
extern volatile unsigned char queued_stick[256],queued_trigger[256],queued_console[256];
#endif
