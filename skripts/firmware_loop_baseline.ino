
/*
 * firmware_loop_baseline.ino
 * Baseline loop-timer APPI generator (Poisson ISI + Uniform PW)
 * NOTE: This skeleton prioritizes clarity over absolute timing precision.
 */
#include <Arduino.h>

// Parameters (can be updated via serial protocol)
volatile float lambda_hz = 2.0;        // average rate (events per second)
volatile uint16_t pw_min_us = 50;      // min pulse width (us)
volatile uint16_t pw_max_us = 1000;    // max pulse width (us)
const uint8_t PIN_OUT = 8;

static inline float urand() {
  return (random(1, 10001)) / 10001.0f;  // simple uniform(0,1]
}

static inline float next_exponential_interval(float lambda_hz) {
  float u = urand();
  return -log(u) / lambda_hz; // seconds
}

void setup() {
  pinMode(PIN_OUT, OUTPUT);
  digitalWrite(PIN_OUT, LOW);
  Serial.begin(115200);
  randomSeed(analogRead(A0)); // seed PRNG
  Serial.println(F("APPI baseline ready"));
}

void loop() {
  // Compute next interval and width
  float dt_s = next_exponential_interval(lambda_hz);
  uint16_t width = pw_min_us + (random(0, (long)(pw_max_us - pw_min_us + 1)));

  // Busy-wait style delay (rough, jitter-prone)
  unsigned long dt_ms = (unsigned long)(dt_s * 1000.0f);
  delay(dt_ms);

  // Emit impulse
  digitalWrite(PIN_OUT, HIGH);
  delayMicroseconds(width);
  digitalWrite(PIN_OUT, LOW);

  // Log (timestamp in ms since start)
  Serial.print(F("EV,"));
  Serial.print(millis());
  Serial.print(F(","));
  Serial.print(width);
  Serial.print(F(","));
  Serial.println(dt_ms);
}
