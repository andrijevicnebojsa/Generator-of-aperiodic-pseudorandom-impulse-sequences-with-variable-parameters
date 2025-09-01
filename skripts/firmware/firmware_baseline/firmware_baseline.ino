/* ---------------------------------------------------------------------------
 * APPI Generator – Baseline loop (blocking delays)
 * Platforma: Arduino Mega 2560 (16 MHz)
 * Pinovi: PULSE_OUT = D8, AnalogSeed = A0
 * Protokol (115200 8N1): SET,lambda,<float>; SET,pwmin,<int>; SET,pwmax,<int>
 *                        SEED,fixed,<uint32>; SEED,analog; START; STOP
 * Log linija: EV,t_ms=<uint32>,w_us=<uint32>,next_dt_ms=<uint32>
 * ------------------------------------------------------------------------- */
#include <Arduino.h>
#include <stdlib.h>
#include <math.h>

static const uint8_t PULSE_OUT = 8;
static const uint8_t ANALOG_SEED_PIN = A0;

volatile bool running = false;
float lambda_hz = 2.0f;     // default λ
uint32_t pw_min_us = 50;    // default PW min
uint32_t pw_max_us = 1000;  // default PW max

// uniform u ∈ (0,1]
static inline float uniform01(void) {
  // random() vraća [0, 2^31-1]; izbegni 0; dodaj 1 i podeli sa 2^31
  const float denom = 2147483648.0f; // 2^31
  long rv = random(0, 0x7FFFFFFF);   // [0, 2^31-2]
  return ( (rv + 1) / denom );       // (0,1]
}

static inline uint32_t now_ms() { return millis(); }

static uint32_t sample_dt_us(float lambda_hz_) {
  if (lambda_hz_ <= 0.0f) lambda_hz_ = 0.001f;
  float u = uniform01();
  // Δt [s] = -ln(u)/λ; konvertuj u µs
  double dt_s = -log((double)u) / (double)lambda_hz_;
  uint32_t dt_us = (uint32_t) (dt_s * 1e6);
  if (dt_us < 1) dt_us = 1;
  return dt_us;
}

static uint32_t sample_pw_us(uint32_t a_us, uint32_t b_us) {
  if (b_us < a_us) { uint32_t t = a_us; a_us = b_us; b_us = t; }
  uint32_t span = (b_us - a_us + 1);
  uint32_t r = (uint32_t) random(0, span);
  return a_us + r;
}

void apply_command(char *line) {
  // trim newline
  size_t n = strlen(line);
  while (n && (line[n-1]=='\n' || line[n-1]=='\r')) { line[--n] = 0; }

  if (strncmp(line, "SET,lambda,", 11) == 0) {
    float v = atof(line + 11);
    if (v > 0.0f && v < 1000.0f) { lambda_hz = v; }
    Serial.print(F("OK,lambda,")); Serial.println(lambda_hz, 6);
  } else if (strncmp(line, "SET,pwmin,", 10) == 0) {
    long v = atol(line + 10);
    if (v > 0) pw_min_us = (uint32_t)v;
    Serial.print(F("OK,pwmin,")); Serial.println(pw_min_us);
  } else if (strncmp(line, "SET,pwmax,", 10) == 0) {
    long v = atol(line + 10);
    if (v > 0) pw_max_us = (uint32_t)v;
    Serial.print(F("OK,pwmax,")); Serial.println(pw_max_us);
  } else if (strncmp(line, "SEED,fixed,", 11) == 0) {
    unsigned long s = strtoul(line + 11, NULL, 10);
    randomSeed(s);
    Serial.print(F("OK,seed,fixed,")); Serial.println(s);
  } else if (strcmp(line, "SEED,analog") == 0) {
    randomSeed(analogRead(ANALOG_SEED_PIN));
    Serial.println(F("OK,seed,analog"));
  } else if (strcmp(line, "START") == 0) {
    running = true;
    Serial.println(F("OK,START"));
  } else if (strcmp(line, "STOP") == 0) {
    running = false;
    Serial.println(F("OK,STOP"));
  } else {
    Serial.println(F("ERR,UnknownCommand"));
  }
}

void setup() {
  pinMode(PULSE_OUT, OUTPUT);
  digitalWrite(PULSE_OUT, LOW);
  pinMode(ANALOG_SEED_PIN, INPUT);
  Serial.begin(115200);
  while (!Serial) {}
  Serial.println(F("APPI Baseline Ready"));
  randomSeed(analogRead(ANALOG_SEED_PIN));
}

static char linebuf[96];
static uint8_t linelen = 0;

void loop() {
  // serial rx
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      linebuf[linelen] = 0;
      apply_command(linebuf);
      linelen = 0;
    } else if (linelen < sizeof(linebuf)-1) {
      linebuf[linelen++] = c;
    }
  }

  if (!running) return;

  uint32_t dt_us = sample_dt_us(lambda_hz);
  delayMicroseconds(dt_us);

  uint32_t w_us = sample_pw_us(pw_min_us, pw_max_us);

  // emit pulse
  digitalWrite(PULSE_OUT, HIGH);
  delayMicroseconds(w_us);
  digitalWrite(PULSE_OUT, LOW);

  // log: t_ms, w_us, next_dt_ms (planirani)
  uint32_t tms = now_ms();
  uint32_t next_dt_ms = sample_dt_us(lambda_hz) / 1000U; // samo planirani prikaz
  Serial.print(F("EV,t_ms=")); Serial.print(tms);
  Serial.print(F(",w_us=")); Serial.print(w_us);
  Serial.print(F(",next_dt_ms=")); Serial.println(next_dt_ms);
}
