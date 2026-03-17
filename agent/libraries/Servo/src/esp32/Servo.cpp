#if defined(ARDUINO_ARCH_ESP32)

#include <Servo.h>
#include <Arduino.h>

class ServoImpl {
  uint8_t pin;
public:
  ServoImpl(const uint8_t _pin, const uint8_t _channel) : pin(_pin) {
    ledcSetup(_channel, (1000000 / REFRESH_INTERVAL), LEDC_MAX_BIT_WIDTH);
    ledcAttachPin(pin, _channel);
  }
  ~ServoImpl() {
    ledcDetachPin(pin);
  }
  void set(const uint8_t _channel, const uint32_t duration_us) {
    ledcWrite(_channel, LEDC_US_TO_TICKS(duration_us));
  }
  uint32_t get(const uint8_t _channel) const {
    return LEDC_TICKS_TO_US(ledcRead(_channel));
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
  servos[this->servoIndex] = new ServoImpl(pin, this->servoIndex);
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
  byte channel = this->servoIndex;
  if (channel < MAX_PWM_SERVOS) {
    if (value < SERVO_MIN()) value = SERVO_MIN();
    else if (value > SERVO_MAX()) value = SERVO_MAX();
    servos[this->servoIndex]->set(this->servoIndex, value);
  }
}

int Servo::read() {
  return map(readMicroseconds(), SERVO_MIN(), SERVO_MAX(), 0, 180);
}

int Servo::readMicroseconds() {
  if (!servos[this->servoIndex]) return 0;
  return servos[this->servoIndex]->get(this->servoIndex);
}

bool Servo::attached() {
  return servos[this->servoIndex] != NULL;
}

#endif
