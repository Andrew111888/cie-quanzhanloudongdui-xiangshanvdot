#ifndef VDOT_CONSOLE_H
#define VDOT_CONSOLE_H
#include <stdint.h>
static inline void putch(char c) {
  volatile uint32_t *uart = (volatile uint32_t *)(uintptr_t)0x40600000;
  while (uart[2] & 8u) {}
  uart[1] = (uint8_t)c;
}
static void puts_uart(const char *s) { while (*s) putch(*s++); }
static void print_uint(uint64_t x) {
  char text[24]; unsigned n = 0;
  do { text[n++] = '0' + x % 10; x /= 10; } while (x);
  while (n) putch(text[--n]);
}
#endif
