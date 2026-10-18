#ifndef INPUT_H
#define INPUT_H

typedef enum { INPUT_NONE, INPUT_UP, INPUT_DOWN, INPUT_LEFT, INPUT_RIGHT,
    INPUT_FIRE, INPUT_START, INPUT_SELECT, INPUT_OPTION } InputAction;
void input_init(void);
/* One call each PAL frame. Independent button edges have priority over stick. */
InputAction input_tick(unsigned char stick, unsigned char trigger, unsigned char console);
InputAction input_read(void);
#endif
