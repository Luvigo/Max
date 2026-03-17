#if defined(ARDUINO_ARCH_ESP32)

#include <Servo.h>
#include <Arduino.h>

/* ESP32 Arduino 3.x: ledcSetup+ledcAttachPin -> ledcAttach; ledcDetachPin -> ledcDetach; ledcWrite/ledcRead usan pin */
class ServoImpl {
  uint8_t pin;
public:
  ServoImpl(const uint8_t _pin) : pin(_pin) {
    ledcAttach(pin, (1000000 / REFRESH_INTERVAL), LEDC_MAX_BIT_WIDTH);
  }
  ~ServoImpl() {
    ledcDetach(pin);
  }
  void set(const uint32_t duration_us) {
    ledcWrite(pin, LEDC_US_TO_TICKS(duration_us));
  }
  uint32_t get() const {
    return LEDC_TICKS_TO_US(ledcRead(pin));
  }
};

static ServoImpl* servos[MAX_PWM_SERVOS] = {nullptr};
uint8_t ServoCount = 0;

#define SERVO_MIN() (MIN_PULSE_WIDTH - this->min)
#define SERVO_MAX() (MAX_PULSE_WIDTH - this->max)

Servo::Servo() {
  if (ServoCount < MAX_PWM_SERVOS) {
    this->servoIndex = ServoCount++;
  } else {
    this->servoIndex = INVALID_SERVO;
  }
}

uint8_t Servo::attach(int pin) {
  return this->attach(pin, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH);
}

uint8_t Servo::attach(int pin, int min, int max) {
  servos[this->servoIndex] = new ServoImpl(pin);
  this->min = (MIN_PULSE_WIDTH - min);
  this->max = (MAX_PULSE_WIDTH - max);
  return this->servoIndex;
}

void Servo::detach() {
  delete servos[this->servoIndex];
  servos[this->servoIndex] = NULL;
}

void Servo::write(int value) {
  if (value < MIN_PULSE_WIDTH) {
    if (value < 0) value = 0;
    else if (value > 180) value = 180;
    value = map(value, 0, 180, SERVO_MIN(), SERVO_MAX());
  }
  writeMicroseconds(value);
}

void Servo::writeMicroseconds(int value) {
  if (!servos[this->servoIndex]) return;
  if (this->servoIndex < MAX_PWM_SERVOS) {
    if (value < SERVO_MIN()) value = SERVO_MIN();
    else if (value > SERVO_MAX()) value = SERVO_MAX();
    servos[this->servoIndex]->set(value);
  }
}

int Servo::read() {
  return map(readMicroseconds(), SERVO_MIN(), SERVO_MAX(), 0, 180);
}

int Servo::readMicroseconds() {
  if (!servos[this->servoIndex]) return 0;
  return servos[this->servoIndex]->get();
}

bool Servo::attached() {
  return servos[this->servoIndex] != NULL;
}

#endif
