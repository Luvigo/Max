/*
 Servo.h - Interrupt driven Servo library for Arduino using 16 bit timers - Version 2
 Copyright (c) 2009 Michael Margolis. All right reserved.
*/

#ifndef Servo_h
#define Servo_h

#include <Arduino.h>

#if defined(ARDUINO_ARCH_ESP32)
#include "esp32/ServoTimers.h"
#else
#error "Esta versión de Servo (MAX-IDE) solo soporta ESP32."
#endif

#define Servo_VERSION 2
#define MIN_PULSE_WIDTH 544
#define MAX_PULSE_WIDTH 2400
#define DEFAULT_PULSE_WIDTH 1500
#define REFRESH_INTERVAL 20000
#define SERVOS_PER_TIMER 12
#define MAX_SERVOS (_Nbr_16timers * SERVOS_PER_TIMER)
#define INVALID_SERVO 255

#if !defined(ARDUINO_ARCH_STM32F4) && !defined(ARDUINO_ARCH_XMC)
typedef struct {
  uint8_t nbr : 6;
  uint8_t isActive : 1;
} ServoPin_t;

typedef struct {
  ServoPin_t Pin;
  volatile unsigned int ticks;
} servo_t;

class Servo {
public:
  Servo();
  uint8_t attach(int pin);
  uint8_t attach(int pin, int min, int max);
  void detach();
  void write(int value);
  void writeMicroseconds(int value);
  int read();
  int readMicroseconds();
  bool attached();
private:
  uint8_t servoIndex;
  int8_t min;
  int8_t max;
};
#endif
#endif
