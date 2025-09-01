/* ---------------------------------------------------------------------------
 * APPI – Biphasic (charge-balanced) sekvenca preko dva pina:
 * Pins: EN_PIN (enable), PH_PIN (phase: HIGH=cathodic, LOW=anodic), oba TTL
 * Očekuje se eksterni CCS/H-bridge koji ove TTL upravljačke signale pretvara u
 * +I / -I i 0 (gap). State machine u ISR (Timer1 CTC, 100 us tick).
 * Komande: SET,lambda,<f>; SET,pw,<us>; SET,tgap,<us>; SET,iphase_mA,<f> (log samo)
 *          START; STOP; SEED,fixed,<u32>; SEED,analog
 * Log: BIP,t_ms=?,Iphase_mA=?,PW_us=?,tgap_us=?,next_dt_ms=?
 * ------------------------------------------------------------------------- */
#include <Arduino.h>
#include <math.h>

static const uint8_t EN_PIN = 6;   // enable
static const uint8_t PH_PIN = 7;   // phase (dir)
static const uint16_t TICK_US = 100;

enum PhaseState : uint8_t { IDLE=0, PH1, GAP, PH2 };

volatile uint32_t tick_us = 0;
volatile bool running = false;

volatile PhaseState st = IDLE;
volatile uint32_t st_end_us = 0;

float lambda_hz = 2.0f;
uint32_t PW_us = 200;
uint32_t TGAP_us = 50;
float Iphase_mA = 3.0f; // samo za log

volatile uint32_t next_fire_us = 0;
volatile bool fired_flag = false;

static inline float uniform01(void) {
  const float denom = 2147483648.0f;
  long rv = random(0, 0x7FFFFFFF);
  return ((rv + 1) / denom);
}
static uint32_t sample_dt_us(float lambda_hz_) {
  if (lambda_hz_ <= 0.0f) lambda_hz_ = 0.001f;
  double u = uniform01();
  double dt_s = -log(u) / lambda_hz_;
  uint32_t dt_us = (uint32_t)(dt_s * 1e6);
  if (dt_us < 1) dt_us = 1;
  return dt_us;
}

ISR(TIMER1_COMPA_vect) {
  tick_us += TICK_US;

  if (!running) return;

  switch (st) {
    case IDLE:
      if (tick_us >= next_fire_us) {
        // start PH1: cathodic
        digitalWrite(PH_PIN, HIGH);
        digitalWrite(EN_PIN, HIGH);
        st = PH1;
        st_end_us = tick_us + PW_us;
        fired_flag = true; // za log i planiranje sledećeg dt u loop()
      }
      break;
    case PH1:
      if (tick_us >= st_end_us) {
        // gap
        digitalWrite(EN_PIN, LOW);
        st = GAP;
        st_end_us = tick_us + TGAP_us;
      }
      break;
    case GAP:
      if (tick_us >= st_end_us) {
        // start PH2: anodic
        digitalWrite(PH_PIN, LOW);
        digitalWrite(EN_PIN, HIGH);
        st = PH2;
        st_end_us = tick_us + PW_us;
      }
      break;
    case PH2:
      if (tick_us >= st_end_us) {
        // done
        digitalWrite(EN_PIN, LOW);
        st = IDLE;
        // sledeci fire vreme postavlja loop()
      }
      break;
  }
}

void timer1_setup_ctc() {
  noInterrupts();
  TCCR1A=0; TCCR1B=0; TCNT1=0;
  OCR1A = (uint16_t)((F_CPU/8UL)*TICK_US/1000000UL);
  TCCR1B |= (1<<WGM12);
  TCCR1B |= (1<<CS11);
  TIMSK1 |= (1<<OCIE1A);
  interrupts();
}

void setup() {
  pinMode(EN_PIN, OUTPUT);
  pinMode(PH_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW);
  digitalWrite(PH_PIN, LOW);
  Serial.begin(115200);
  while(!Serial){}
  randomSeed(analogRead(A0));
  timer1_setup_ctc();
  Serial.println(F("APPI Biphasic ISR Ready"));
}

static char linebuf[96];
static uint8_t linelen=0;

void apply_command(char* line){
  size_t n=strlen(line);
  while(n && (line[n-1]=='\n'||line[n-1]=='\r')) line[--n]=0;

  if (strncmp(line,"SET,lambda,",11)==0){
    float v=atof(line+11); if (v>0 && v<1000) lambda_hz=v;
    Serial.print(F("OK,lambda,")); Serial.println(lambda_hz,6);
  } else if (strncmp(line,"SET,pw,",7)==0){
    long v=atol(line+7); if (v>0) PW_us=(uint32_t)v;
    Serial.print(F("OK,pw,")); Serial.println(PW_us);
  } else if (strncmp(line,"SET,tgap,",9)==0){
    long v=atol(line+9); if (v>=0) TGAP_us=(uint32_t)v;
    Serial.print(F("OK,tgap,")); Serial.println(TGAP_us);
  } else if (strncmp(line,"SET,iphase_mA,",14)==0){
    float v=atof(line+14); if (v>=0) Iphase_mA=v;
    Serial.print(F("OK,iphase_mA,")); Serial.println(Iphase_mA,3);
  } else if (strncmp(line,"SEED,fixed,",11)==0){
    unsigned long s=strtoul(line+11,nullptr,10); randomSeed(s);
    Serial.print(F("OK,seed,fixed,")); Serial.println(s);
  } else if (strcmp(line,"SEED,analog")==0){
    randomSeed(analogRead(A0)); Serial.println(F("OK,seed,analog"));
  } else if (strcmp(line,"START")==0){
    noInterrupts();
    running=true; st=IDLE;
    next_fire_us = tick_us + sample_dt_us(lambda_hz);
    interrupts();
    Serial.println(F("OK,START"));
  } else if (strcmp(line,"STOP")==0){
    noInterrupts(); running=false; interrupts();
    Serial.println(F("OK,STOP"));
  } else {
    Serial.println(F("ERR,UnknownCommand"));
  }
}

void loop(){
  // RX
  while(Serial.available()){
    char c=(char)Serial.read();
    if (c=='\n'){ linebuf[linelen]=0; apply_command(linebuf); linelen=0; }
    else if (linelen<sizeof(linebuf)-1){ linebuf[linelen++]=c; }
  }

  if (fired_flag){
    noInterrupts(); fired_flag=false; interrupts();
    uint32_t dt_us = sample_dt_us(lambda_hz);
    noInterrupts();
    next_fire_us = tick_us + dt_us;
    interrupts();

    uint32_t tms = millis();
    Serial.print(F("BIP,t_ms=")); Serial.print(tms);
    Serial.print(F(",Iphase_mA=")); Serial.print(Iphase_mA,3);
    Serial.print(F(",PW_us=")); Serial.print(PW_us);
    Serial.print(F(",tgap_us=")); Serial.print(TGAP_us);
    Serial.print(F(",next_dt_ms=")); Serial.println(dt_us/1000U);
  }
}
