/*
* firmware_timer_isr.ino
* Timer/ISR-driven APPI generator (Poisson ISI + Uniform PW)
* Uses hardware timer for improved timing determinism.
* Non-blocking ISR to avoid pulse overlap.
*/
#include &lt;Arduino.h&gt;
const uint8_t PIN_OUT = 8;
volatile float lambda_hz = 2.0;
volatile uint16_t pw_min_us = 50, pw_max_us = 1000;
volatile bool due_to_fire = false;
volatile unsigned long next_fire_us = 0;
volatile uint16_t current_pw_us = 200;
volatile unsigned long last_sched_us = 0;
volatile bool pulse_active = false;
volatile unsigned long pulse_start_us = 0;
static inline float urand() {
return (random(1, 10001)) / 10001.0f;
}
static inline float next_exponential_interval(float lambda_hz) {
float u = urand();
return -log(u) / lambda_hz; // seconds
}
ISR(TIMER1_COMPA_vect) {
unsigned long now = micros();

if (pulse_active) {
if ((long)(now - pulse_start_us) &gt;= current_pw_us) {
digitalWrite(PIN_OUT, LOW);
pulse_active = false;
}
} else if (due_to_fire &amp;&amp; (long)(now - next_fire_us) &gt;= 0) {
digitalWrite(PIN_OUT, HIGH);
pulse_start_us = now;
pulse_active = true;
due_to_fire = false;
}
}
void setupTimer1() {
noInterrupts();
TCCR1A = 0; TCCR1B = 0;
// Prescaler 8 -&gt; 0.5 us per tick on 16 MHz
TCCR1B |= (1 &lt;&lt; WGM12); // CTC mode
TCCR1B |= (1 &lt;&lt; CS11); // prescaler 8
OCR1A = 2000; // 1 ms tick (approx): 2000 * 0.5us = 1ms
TIMSK1 |= (1 &lt;&lt; OCIE1A);
interrupts();
}
void setup() {
pinMode(PIN_OUT, OUTPUT);
digitalWrite(PIN_OUT, LOW);
Serial.begin(115200);
randomSeed(analogRead(A0));
setupTimer1();
Serial.println(F(&quot;APPI ISR ready&quot;));
last_sched_us = micros();
// schedule first event ensuring no overlap
float dt_s = next_exponential_interval(lambda_hz);
while (dt_s * 1e6 &lt; pw_max_us) {
dt_s = next_exponential_interval(lambda_hz);
}
current_pw_us = pw_min_us + random(0, (long)(pw_max_us - pw_min_us + 1));
next_fire_us = last_sched_us + (unsigned long)(dt_s * 1e6);
due_to_fire = true;
}
void loop() {
if (!due_to_fire &amp;&amp; !pulse_active) {
last_sched_us = micros();
float dt_s = next_exponential_interval(lambda_hz);
while (dt_s * 1e6 &lt; pw_max_us) {
dt_s = next_exponential_interval(lambda_hz);
}
current_pw_us = pw_min_us + random(0, (long)(pw_max_us - pw_min_us + 1));
next_fire_us = last_sched_us + (unsigned long)(dt_s * 1e6);
due_to_fire = true;
Serial.print(F(&quot;SCH,&quot;));
Serial.print(micros());

Serial.print(F(&quot;,&quot;));
Serial.print(current_pw_us);
Serial.print(F(&quot;,&quot;));
Serial.println((unsigned long)(dt_s * 1000000.0f));
}
if (Serial.available()) {
String cmd = Serial.readStringUntil(&#39;\n&#39;);
if (cmd.startsWith(&quot;SET,lambda,&quot;)) {
lambda_hz = cmd.substring(11).toFloat();
Serial.print(F(&quot;ACK,lambda,&quot;)); Serial.println(lambda_hz, 3);
} else if (cmd.startsWith(&quot;SET,pwmin,&quot;)) {
pw_min_us = (uint16_t)cmd.substring(10).toInt();
Serial.print(F(&quot;ACK,pwmin,&quot;)); Serial.println(pw_min_us);
} else if (cmd.startsWith(&quot;SET,pwmax,&quot;)) {
pw_max_us = (uint16_t)cmd.substring(10).toInt();
Serial.print(F(&quot;ACK,pwmax,&quot;)); Serial.println(pw_max_us);
}
}
}