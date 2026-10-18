#include "sound.h"
#include "hardware.h"
void sound_effect(unsigned char effect) { if(effect && effect>=sound_request) sound_request=effect; }
