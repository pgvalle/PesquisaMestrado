#include "Blink.h"

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif

void Input(int *tick) {
  delay(500);
  *tick = 1;
}

void Output(int *led) {
  digitalWrite(LED_BUILTIN, *led ? HIGH : LOW);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  ActivateBlink();
}

void loop() {
  // ActivateBlink() runs the generated eM-FRP reaction loop forever.
}
