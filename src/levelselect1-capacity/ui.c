/* Capacity probe only: no input, disk writes or game mutation.
 * Appended to display.c so it uses the existing text/font/display helpers.
 * Campaign labels are injected by the probe, never a second map table. */
static void selector_number(unsigned char row,unsigned char value)
{
    char digits[3];
    digits[0]='0'+value/10;digits[1]='0'+value%10;digits[2]=0;
    text(row,20,digits);
}
void selector_ui_capacity(unsigned char number)
{
    unsigned char area=number/15;
    text(3,13,"SELECT LEVEL");
    text(6,13,selector_areas[area]);
    text(9,10,"LOCAL");selector_number(9,number%15+1);text(9,22,"/15");
    text(11,10,"GLOBAL");selector_number(11,number+1);text(11,22,"/60");
    text(15,5,"UP/DOWN AREA / LEFT/RIGHT LEVEL");
    text(18,5,"FIRE START / OPTION MENU");
}
