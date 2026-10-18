/* Auto-generated from tools/levels_final.py (solver-verified, 20 levels). */
/* Do not hand-edit rows - regenerate from the Python source instead. */
#include "levels_data.h"

/* Level 1: Pierwszy krok (min. 1 ruchow) */
static const char *l1[] = {
    "######",
    "#.$@ #",
    "######",
};

/* Level 2: Za rog (min. 6 ruchow) */
static const char *l2[] = {
    "#######",
    "#.    #",
    "#     #",
    "#  $@ #",
    "#     #",
    "#######",
};

/* Level 3: Dwa pudelka (min. 12 ruchow) */
static const char *l3[] = {
    "########",
    "#.  .  #",
    "#  $ $ #",
    "#   @  #",
    "########",
};

/* Level 4: Wybor drogi (min. 26 ruchow) */
static const char *l4[] = {
    "########",
    "#. #   #",
    "#  #   #",
    "#  $ $ #",
    "#  #   #",
    "#. #  @#",
    "########",
};

/* Level 5: Kolejnosc ma znaczenie (min. 6 ruchow) */
static const char *l5[] = {
    "#########",
    "#  #    #",
    "#. $  . #",
    "#  #  $ #",
    "#  #  @ #",
    "#########",
};

/* Level 6: Ciasny magazyn (min. 28 ruchow) */
static const char *l6[] = {
    "########",
    "#.  .  #",
    "# $##$ #",
    "#  ##  #",
    "#   @  #",
    "########",
};

/* Level 7: Trzy skrzynie (min. 20 ruchow) */
static const char *l7[] = {
    "##########",
    "#.       #",
    "#  $     #",
    "#    $   #",
    "#      $ #",
    "#  .   . #",
    "#    @   #",
    "##########",
};

/* Level 8: Rozstaw (min. 17 ruchow) */
static const char *l8[] = {
    "##########",
    "#.   .   #",
    "#  $   $ #",
    "#    #   #",
    "#   @    #",
    "##########",
};

/* Level 9: Slepy zaulek (min. 33 ruchow) */
static const char *l9[] = {
    "##########",
    "#  #  .  #",
    "#  #$    #",
    "#. #  ####",
    "#  $  $. #",
    "#   @    #",
    "##########",
};

/* Level 10: Filar (min. 20 ruchow) */
static const char *l10[] = {
    "###########",
    "#.        #",
    "#  $   $  #",
    "#    #    #",
    "#    $    #",
    "#  .   .@ #",
    "###########",
};

/* Level 11: Cztery katy (min. 56 ruchow) */
static const char *l11[] = {
    "###########",
    "#.  #  .  #",
    "#  $#$    #",
    "#         #",
    "#  $#$    #",
    "#.  #  .@ #",
    "###########",
};

/* Level 12: Wnetrze (min. 25 ruchow) */
static const char *l12[] = {
    "############",
    "#.   .     #",
    "#  $   $   #",
    "#     #    #",
    "#    $     #",
    "#.   @     #",
    "############",
};

/* Level 13: Podwojny zamek (min. 28 ruchow) */
static const char *l13[] = {
    "############",
    "#          #",
    "#  ###  #  #",
    "#. $  $ .  #",
    "#  ###  #  #",
    "#     $  . #",
    "#    @     #",
    "############",
};

/* Level 14: Piatka (min. 24 ruchow) */
static const char *l14[] = {
    "#############",
    "#.   .      #",
    "#  $   $    #",
    "#     $     #",
    "#.   @      #",
    "#############",
};

/* Level 15: Waskie mosty (min. 19 ruchow) */
static const char *l15[] = {
    "#############",
    "#.  .   .   #",
    "#  $   $    #",
    "#     #     #",
    "#      $    #",
    "#      @    #",
    "#############",
};

/* Level 16: Kwadrat (min. 21 ruchow) */
static const char *l16[] = {
    "########",
    "#. .   #",
    "# $ $  #",
    "#  @   #",
    "# $ $  #",
    "#. .   #",
    "########",
};

/* Level 17: Rozgalezienie (min. 24 ruchow) */
static const char *l17[] = {
    "#########",
    "#.  .   #",
    "# $  $  #",
    "#   @   #",
    "# $  $  #",
    "#.  .   #",
    "#########",
};

/* Level 18: Sciezka wojownika (min. 26 ruchow) */
static const char *l18[] = {
    "##########",
    "#.  .    #",
    "# $  $   #",
    "#  #     #",
    "# $  $   #",
    "#.  @   .#",
    "##########",
};

/* Level 19: Ostatnia komnata (min. 30 ruchow) */
static const char *l19[] = {
    "##########",
    "#.  #   .#",
    "# $ # $  #",
    "#   #    #",
    "# $ # $  #",
    "#.  @   .#",
    "##########",
};

/* Level 20: Mistrz Sokoban (min. 60 ruchow) */
static const char *l20[] = {
    "#########",
    "#.     .#",
    "# $# #$ #",
    "#  # #  #",
    "# $# #$ #",
    "#.  @  .#",
    "#########",
};

const Level levels[LEVEL_COUNT] = {
    { l1, 3, "Pierwszy krok" },
    { l2, 6, "Za rog" },
    { l3, 5, "Dwa pudelka" },
    { l4, 7, "Wybor drogi" },
    { l5, 6, "Kolejnosc ma znaczenie" },
    { l6, 6, "Ciasny magazyn" },
    { l7, 8, "Trzy skrzynie" },
    { l8, 6, "Rozstaw" },
    { l9, 7, "Slepy zaulek" },
    { l10, 7, "Filar" },
    { l11, 7, "Cztery katy" },
    { l12, 7, "Wnetrze" },
    { l13, 8, "Podwojny zamek" },
    { l14, 6, "Piatka" },
    { l15, 7, "Waskie mosty" },
    { l16, 7, "Kwadrat" },
    { l17, 7, "Rozgalezienie" },
    { l18, 7, "Sciezka wojownika" },
    { l19, 7, "Ostatnia komnata" },
    { l20, 7, "Mistrz Sokoban" },
};

