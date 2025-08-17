
/*
 * firmware_timer_isr.ino
 * Timer/ISR-driven APPI generator (Poisson ISI + Uniform PW)
 * Uses hardware timer for improved timing determinism.
 */
#include <Arduino.h>

const uint8_t PIN_OUT = 8;
volatile float lambda_hz = 2.0;
volatile uint16_t pw_min_us = 50, pw_max_us = 1000;

volatile bool due_to_fire = false;
volatile unsigned long next_fire_us = 0;
volatile uint16_t current_pw_us = 200;
volatile unsigned long last_sched_us = 0;

static inline float urand() {
  return (random(1, 10001)) / 10001.0f;
}

static inline float next_exponential_interval(float lambda_hz) {
  float u = urand();
  return -log(u) / lambda_hz; // seconds
}

ISR(TIMER1_COMPA_vect) {
  // Compare match ISR: check if it's time to fire
  unsigned long now = micros();
  if ((long)(now - next_fire_us) >= 0) {
    // Emit pulse
    digitalWrite(PIN_OUT, HIGH);
    delayMicroseconds(current_pw_us);
    digitalWrite(PIN_OUT, LOW);
    due_to_fire = false;
    // Schedule the next event in the main loop (to keep ISR short)
  }
}

void setupTimer1() {
  noInterrupts();
  TCCR1A = 0; TCCR1B = 0;
  // Prescaler 8 -> 0.5 us per tick on 16 MHz
  TCCR1B |= (1 << WGM12); // CTC mode
  TCCR1B |= (1 << CS11);  // prescaler 8
  OCR1A = 2000;           // 1 ms tick (approx): 2000 * 0.5us = 1ms
  TIMSK1 |= (1 << OCIE1A);
  interrupts();
}

void setup() {
  pinMode(PIN_OUT, OUTPUT);
  digitalWrite(PIN_OUT, LOW);
  Serial.begin(115200);
  randomSeed(analogRead(A0));
  setupTimer1();
  Serial.println(F("APPI ISR ready"));
  last_sched_us = micros();
  // schedule first
  float dt_s = next_exponential_interval(lambda_hz);
  current_pw_us = pw_min_us + (random(0, (long)(pw_max_us - pw_min_us + 1)));
  next_fire_us = last_sched_us + (unsigned long)(dt_s * 1e6);
  due_to_fire = true;
}

void loop() {
  // If not scheduled, schedule next
  if (!due_to_fire) {
    last_sched_us = micros();
    float dt_s = next_exponential_interval(lambda_hz);
    current_pw_us = pw_min_us + (random(0, (long)(pw_max_us - pw_min_us + 1)));
    next_fire_us = last_sched_us + (unsigned long)(dt_s * 1e6);
    due_to_fire = true;

    // Log schedule
    Serial.print(F("SCH,"));
    Serial.print(micros());
    Serial.print(F(","));
    Serial.print(current_pw_us);
    Serial.print(F(","));
    Serial.println((unsigned long)(dt_s * 1000000.0f));
  }

  // Handle simple serial updates (very minimal protocol)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // e.g., "SET,lambda,3.0"
    if (cmd.startsWith("SET,lambda,")) {
      lambda_hz = cmd.substring(11).toFloat();
      Serial.print(F("ACK,lambda,")); Serial.println(lambda_hz, 3);
    } else if (cmd.startsWith("SET,pwmin,")) {
      pw_min_us = (uint16_t)cmd.substring(10).toInt();
      Serial.print(F("ACK,pwmin,")); Serial.println(pw_min_us);
    } else if (cmd.startsWith("SET,pwmax,")) {
      pw_max_us = (uint16_t)cmd.substring(10).toInt();
      Serial.print(F("ACK,pwmax,")); Serial.println(pw_max_us);
    }
  }
}
