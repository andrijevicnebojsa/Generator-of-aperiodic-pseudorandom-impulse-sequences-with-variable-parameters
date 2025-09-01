/* ---------------------------------------------------------------------------
 * APPI Generator – Timer/ISR (CTC) sa "tick" schedulerom
 * Timer1: CTC tick = 100 us (10 kHz), ISR je kratak; planiranje u loop()
 * Pinovi: PULSE_OUT = D8
 * Protokol: isti kao baseline (SET..., SEED..., START/STOP)
 * ------------------------------------------------------------------------- */
#include <Arduino.h>
#include <math.h>

static const uint8_t PULSE_OUT = 8;
static const uint16_t TICK_US = 100; // 100 µs tick

volatile uint32_t tick_us = 0;
volatile bool pulse_active = false;
volatile uint32_t pulse_end_us = 0;
volatile bool fired_flag = false;     // ISR signalizuje: upucan pulse start

// planiranje u "tick" vremenu
volatile uint32_t next_fire_us = 0;
volatile uint32_t armed_pw_us = 0;

float lambda_hz = 2.0f;
uint32_t pw_min_us = 50;
uint32_t pw_max_us = 1000;
volatile bool running = false;

static inline float uniform01(void) {
  const float denom = 2147483648.0f;
  long rv = random(0, 0x7FFFFFFF);
  return ( (rv + 1) / denom );
}

static uint32_t sample_dt_us(float lambda_hz_) {
  if (lambda_hz_ <= 0.0f) lambda_hz_ = 0.001f;
  double u = uniform01();
  double dt_s = -log(u) / lambda_hz_;
  uint32_t dt_us = (uint32_t)(dt_s * 1e6);
  if (dt_us < 1) dt_us = 1;
  return dt_us;
}

static uint32_t sample_pw_us(uint32_t a_us, uint32_t b_us) {
  if (b_us < a_us) { uint32_t t = a_us; a_us = b_us; b_us = t; }
  return a_us + (uint32_t)random(0, (long)(b_us - a_us + 1));
}

ISR(TIMER1_COMPA_vect) {
  tick_us += TICK_US;

  // kraj pulse-a?
  if (pulse_active && (tick_us >= pulse_end_us)) {
    digitalWrite(PULSE_OUT, LOW);
    pulse_active = false;
  }

  // vreme za start?
  if (running && !pulse_active && (tick_us >= next_fire_us)) {
    // start pulse
    digitalWrite(PULSE_OUT, HIGH);
    pulse_active = true;
    pulse_end_us = tick_us + armed_pw_us;
    fired_flag = true; // obavesti loop() da isplanira sledeci
  }
}

void timer1_setup_ctc() {
  // Timer1, 16 MHz / 8 = 2 MHz; želeli bismo tick = 100 µs -> OCR1A = 200
  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  OCR1A  = (uint16_t)( (F_CPU / 8UL) * TICK_US / 1000000UL ); // 200
  TCCR1B |= (1 << WGM12);   // CTC
  TCCR1B |= (1 << CS11);    // prescaler 8
  TIMSK1 |= (1 << OCIE1A);  // enable compare A
  interrupts();
}

void apply_command(char *line) {
  size_t n = strlen(line);
  while (n && (line[n-1]=='\n' || line[n-1]=='\r')) line[--n] = 0;

  if (strncmp(line, "SET,lambda,", 11) == 0) {
    float v = atof(line + 11);
    if (v > 0.0f && v < 1000.0f) lambda_hz = v;
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
    randomSeed(analogRead(A0));
    Serial.println(F("OK,seed,analog"));
  } else if (strcmp(line, "START") == 0) {
    noInterrupts();
    running = true;
    // inicijalizuj prvi dogadjaj
    armed_pw_us = sample_pw_us(pw_min_us, pw_max_us);
    next_fire_us = tick_us + sample_dt_us(lambda_hz);
    interrupts();
    Serial.println(F("OK,START"));
  } else if (strcmp(line, "STOP") == 0) {
    noInterrupts();
    running = false;
    interrupts();
    Serial.println(F("OK,STOP"));
  } else {
    Serial.println(F("ERR,UnknownCommand"));
  }
}

void setup() {
  pinMode(PULSE_OUT, OUTPUT);
  digitalWrite(PULSE_OUT, LOW);
  Serial.begin(115200);
  while(!Serial) {}
  Serial.println(F("APPI Timer/ISR Ready"));
  randomSeed(analogRead(A0));
  timer1_setup_ctc();
}

static char linebuf[96];
static uint8_t linelen = 0;

void loop() {
  // RX
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

  // ako je pulse upravo upucan, planiraj sledeci
  if (fired_flag) {
    noInterrupts();
    fired_flag = false;
    uint32_t plan_dt_us = sample_dt_us(lambda_hz);
    uint32_t plan_pw_us = sample_pw_us(pw_min_us, pw_max_us);
    next_fire_us = tick_us + plan_dt_us;
    armed_pw_us  = plan_pw_us;
    interrupts();

    // log (koristi millis() za timestamp)
    uint32_t tms = millis();
    Serial.print(F("EV,t_ms=")); Serial.print(tms);
    Serial.print(F(",w_us=")); Serial.print(plan_pw_us);
    Serial.print(F(",next_dt_ms=")); Serial.println(plan_dt_us/1000U);
  }
}
