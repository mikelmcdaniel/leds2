#include "arduino_lib.h"
#include <string.h>


// #define NUM_LEDS 144L
const int OUT_BYTES[] = {1, 2, 4, 8};
const int OUT_BYTES_OR = 1 | 2 | 4 | 8;

// global pixels array
uint8_t buffer[NUM_LEDS * 3 + 3 + 2]; // 'NC' + check_sum + 'S'
uint8_t * pixels = &buffer[2];
const uint16_t CHECK_SUM_BYTES[8] = {2, 3, 5, 7, 11, 13, 17, 19};

void ws2811_send_pixels(const uint8_t* pixels24,
    const uint8_t pixels24_size, const uint8_t out_byte) {
  uint8_t mask;
  // Add an extra byte to the end because the assembly code breaks a byte early.
  const uint8_t *pixels24_end = &pixels24[pixels24_size * 3 + 1];

  asm volatile(
"  wsc_outer_for:\n"
"    # start with 1 for the bitmask\n"
"    ldi %[mask],lo8(128)\n"
"    # r24=*pixels24, pixels24++   (note: Y is pixels24)\n"
"    ld r24,Y+\n"
"    wsc_inner_for:\n"
"      mov r25,r24\n"
"      # output high signal to pins\n"
"      out 0x5,%[out_byte]\n"
"      # *pixels24 & mask\n"
"      and r24,%[mask]\n"
"      # if(*pixels24 & mask) PC = wsc_one_case\n"
"      mov r24,r25\n"
"      brne wsc_one_case\n"
"      # 0 case\n"
"      wsc_zero_case:\n"
"        out 0x5,__zero_reg__\n"
"   nop\n"
"   nop\n"
"   nop\n"
"   nop\n"
"   nop\n"
"   cp %A[pixels24],%A[pixels24_end]\n"
"   cpc %B[pixels24],%B[pixels24_end]\n"
"   # branch if pixels24 != pixels24+pixels24_size\n"
"   breq wsc_end_zero\n"
"   # make branch be 2 clocks\n"
"   nop\n"
"   # shift mask\n"
"   lsr %[mask]\n"
"   # branch to out loop if we're done w/ this byte\n"
"   brcs wsc_outer_for\n"
"   # make branch be 2 clocks\n"
"   jmp wsc_inner_for\n"
"      # 1 case\n"
"      wsc_one_case:\n"
"   nop\n"
"   cp %A[pixels24],%A[pixels24_end]\n"
"   cpc %B[pixels24],%B[pixels24_end]\n"
"   # branch if pixels24 != pixels24+pixels24_size\n"
"   breq wsc_end_one\n"
"   # make branch take 2 clock ticks\n"
"   nop\n"
"   out 0x5,__zero_reg__\n"
"   # shift mask\n"
"   lsr %[mask]\n"
"   # branch to out loop if we're done w/ this byte\n"
"   brcs wsc_one_lsr\n"
"   nop\n"
"   nop\n"
"   nop\n"
"   jmp wsc_inner_for\n"
"      wsc_one_lsr:\n"
"        jmp wsc_outer_for\n"
"  wsc_end_one:\n"
"    out 0x5,__zero_reg__\n"
"  wsc_end_zero:\n"
: // output operands
: [pixels24] "y" (pixels24),
  [pixels24_end] "e" (pixels24_end),
  [out_byte] "a" (out_byte),
  [mask] "a" (mask)// input operands
: "r24","r25" // optional clobber list
);
}


inline void send_pixels(uint8_t * pixels) {
  uint8_t old_SREG;

  old_SREG = SREG;
  cli();

#if HALF_REVERSED == 0
  ws2811_send_pixels(pixels, NUM_LEDS, OUT_BYTES_OR);
#elif HALF_REVERSED == 1
  ws2811_send_pixels(pixels,                    NUM_LEDS / 2, OUT_BYTES[1]);
  ws2811_send_pixels(pixels + 3 * NUM_LEDS / 2, NUM_LEDS / 2, OUT_BYTES[3]);
#elif HALF_REVERSED == 2
  ws2811_send_pixels(pixels,                    NUM_LEDS / 4, OUT_BYTES[0]);
  ws2811_send_pixels(pixels + 3 * NUM_LEDS / 4, NUM_LEDS / 4, OUT_BYTES[1]);
  ws2811_send_pixels(pixels + 6 * NUM_LEDS / 4, NUM_LEDS / 4, OUT_BYTES[2]);
  ws2811_send_pixels(pixels + 9 * NUM_LEDS / 4, NUM_LEDS / 4, OUT_BYTES[3]);
#else
#error "HALF_REVERSED not 0, 1, or 2"
#endif
  SREG = old_SREG;
}

void setup() {
	int j;
  Serial.begin(115200);

  // LEDs
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);

  // LED Power
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  digitalWrite(2, LOW);
  digitalWrite(3, LOW);


  // initialize pixels to random, dim color
	for (j = 3 * NUM_LEDS - 1; j >= 0 ; j--) {
    pixels[j] = random(100);
	}
  send_pixels(&pixels[0]);
}

void loop() {
  static uint16_t count = 0;
  int16_t want, have, pos;
  uint16_t check_sum, j;

  want = Serial.read();
  if (want != -1) {
    count = 0;
    if (want == 'Y') {
      want = sizeof(buffer);
      have = 0;
      while (have < want) {
        have += Serial.readBytes((char *)&buffer[have], want - have);
      }
      if (buffer[0] == 'N' && buffer[1] == 'C') {
        check_sum = 0;
        for (j = 0; j < NUM_LEDS * 3; j++) {
          check_sum += (j + 1) * *(uint8_t *)&buffer[j + 2] * CHECK_SUM_BYTES[j % 8];
        }
        // If the calculated check_sum doesn't match, return.
        if (check_sum != 256 * (uint16_t)*(uint8_t *)&buffer[2 + NUM_LEDS * 3 + 1] + *(uint8_t *)&buffer[2 + NUM_LEDS * 3]) return;
        if (buffer[2] == 'Y' && buffer[3] == 'N' && buffer[4] == 'C' && buffer[5] == 'P') {
          if (buffer[6] == '0') {
            digitalWrite(2, LOW);
            digitalWrite(3, LOW);
          } else if (buffer[6] == '1') {
            digitalWrite(2, HIGH);
            digitalWrite(3, HIGH);
          } else {
            digitalWrite(2, LOW);
            digitalWrite(3, HIGH);
          }
        } else {
          send_pixels(&pixels[0]);
        }
      } else {
        while (Serial.read() != 'S');
      }
    }
  } else {
    count++;
    if (!count) {
      send_pixels(&pixels[0]);
    }
  }
}
