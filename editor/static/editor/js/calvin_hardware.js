/**
 * Calvin Hardware - Configuración centralizada de pines del carro Calvin.
 *
 * ÚNICA FUENTE DE VERDAD para pines Calvin. Los bloques y el generador deben
 * usar CalvinHardware.PINS (AVR) o CalvinHardware.PINS_ESP32 (ESP32).
 *
 * ESP32 (BotFlow real): L298N motores, sensor ultrasónico 18/36, buzzer 27,
 * RGB 23/21/22 (R/G/B), sensores línea 34/35/39. AVR: prox 6/7, etc.
 *
 * Conservado: Valores verificados con carro Calvin funcionando.
 * No cambiar pines sin confirmar hardware real.
 */
(function() {
    'use strict';

    // Pines Arduino (AVR) - Servo motores, tone, analogWrite, sensores
    const CALVIN_PINS_AVR = {
        PROX_TRIG: 6, PROX_ECHO: 7,      // Sensor ultrasónico HC-SR04
        BUZZER: 3,                        // Buzzer/tone
        RGB_R: 5, RGB_G: 6, RGB_B: 11,   // LED RGB
        MOTOR_IZQ: 9, MOTOR_DER: 10,     // Servos (adelante/girar)
        LINEA_IZQ: 0, LINEA_CENT: 1, LINEA_DER: 2  // A0, A1, A2 sensores de línea
    };

    // Pines ESP32 (BotFlow) - L298N IN1-4, ledc, ADC. PROX_ECHO usa 36; línea der usa 39 (evitar conflicto)
    const CALVIN_PINS_ESP32 = {
        IN_1: 32, IN_2: 33, IN_3: 25, IN_4: 26,   // L298N driver motores
        PROX_TRIG: 18, PROX_ECHO: 36,             // Sensor ultrasónico HC-SR04
        BUZZER: 27,                               // ledcWriteTone
        RGB_R: 23, RGB_G: 22, RGB_B: 21,          // LED RGB: original BotFlow (23=R, 22=G, 21=B)
        LINEA_IZQ: 34, LINEA_CENT: 35, LINEA_DER: 39  // ADC (36 reservado para PROX_ECHO)
    };

    const CALVIN_PINS = CALVIN_PINS_AVR;

    /**
     * Defaults de los bloques inout_* en el toolbox Calvin (ESP32: LED R=23, A0 ≈ GPIO36).
     * Mantener alineado con TOOLBOX_CALVIN "Calvin I/O" en toolbox_config.js.
     */
    const IO_TOOLBOX_DEFAULTS = {
        DIGITAL_WRITE_PIN: CALVIN_PINS_ESP32.RGB_R,
        DIGITAL_READ_PIN: CALVIN_PINS_ESP32.RGB_R,
        ANALOG_WRITE_PIN: CALVIN_PINS_ESP32.RGB_R,
        ANALOG_READ_PIN: 'A0'
    };

    // Notas musicales: [octava 0-5] -> frecuencia Hz
    const NOTAS = {
        DO: [33, 65, 131, 262, 523, 1047],
        RE: [37, 73, 147, 294, 587, 1175],
        MI: [41, 82, 165, 330, 659, 1319],
        FA: [44, 87, 175, 349, 698, 1397],
        SOL: [49, 98, 196, 392, 784, 1568],
        LA: [55, 110, 220, 440, 880, 1760],
        SI: [62, 123, 247, 494, 988, 1976]
    };

    function getNoteFreq(nota, octava) {
        const arr = NOTAS[nota] || NOTAS.DO;
        const oct = Math.max(0, Math.min(5, octava | 0));
        return arr[oct] || 262;
    }

    window.CalvinHardware = {
        PINS: CALVIN_PINS,
        PINS_ESP32: CALVIN_PINS_ESP32,
        IO_TOOLBOX_DEFAULTS: IO_TOOLBOX_DEFAULTS,
        getNoteFreq: getNoteFreq,

        getProximityCode: function(pinTrig, pinEcho, isEsp32) {
            const pins = isEsp32 ? CALVIN_PINS_ESP32 : CALVIN_PINS;
            const t = (pinTrig !== undefined && pinTrig !== null && pinTrig !== '') ? pinTrig : pins.PROX_TRIG;
            const e = (pinEcho !== undefined && pinEcho !== null && pinEcho !== '') ? pinEcho : pins.PROX_ECHO;
            // Misma plantilla AVR/ESP32: timeout pulseIn evita 0 espurio en ESP32; 999 = sin eco/timeout
            return {
                defines:
                    '#define CALVIN_PROX_TRIG ' + t + '\n' +
                    '#define CALVIN_PROX_ECHO ' + e + '\n' +
                    '#define CALVIN_DISTANCE_TRIG_PIN CALVIN_PROX_TRIG\n' +
                    '#define CALVIN_DISTANCE_ECHO_PIN CALVIN_PROX_ECHO\n' +
                    '#define SOUND_SPEED 0.034f',
                vars: 'long duration;\nfloat distanceCm;',
                func:
                    'float calvin_distancia_cm(void) {\n' +
                    '  digitalWrite(CALVIN_PROX_TRIG, LOW);\n' +
                    '  delayMicroseconds(5);\n' +
                    '  digitalWrite(CALVIN_PROX_TRIG, HIGH);\n' +
                    '  delayMicroseconds(10);\n' +
                    '  digitalWrite(CALVIN_PROX_TRIG, LOW);\n' +
                    '  duration = pulseIn(CALVIN_PROX_ECHO, HIGH, 30000);\n' +
                    '  if (duration == 0) {\n' +
                    '    // sin eco o timeout pulseIn (30 ms): revisar TRIG/ECHO, pinMode y cableado\n' +
                    '    return 999.0f;\n' +
                    '  }\n' +
                    '  distanceCm = (float)duration * SOUND_SPEED / 2.0f;\n' +
                    '  return distanceCm;\n' +
                    '}',
                setup: '  pinMode(CALVIN_PROX_TRIG, OUTPUT);\n  pinMode(CALVIN_PROX_ECHO, INPUT);'
            };
        },

        getBuzzerCode: function(pin, isEsp32) {
            if (isEsp32) {
                const p = pin || CALVIN_PINS_ESP32.BUZZER;
                return {
                    defines: `#define buzzerPin ${p}`,
                    vars: '',
                    func: `void calvin_tocar_nota(int freq, int duracion_ms) {
  ledcWriteTone(buzzerPin, freq);
  if (duracion_ms > 0) {
    delay(duracion_ms);
    ledcWriteTone(buzzerPin, 0);
  }
}`,
                    setup: '  ledcAttach(buzzerPin, 1000, 10);'
                };
            }
            const p = pin || CALVIN_PINS.BUZZER;
            return {
                defines: `#define CALVIN_BUZZER ${p}`,
                func: `void calvin_tocar_nota(int freq, int duracion_ms) {
  tone(CALVIN_BUZZER, freq, duracion_ms > 0 ? duracion_ms : 0);
  if (duracion_ms > 0) {
    delay(duracion_ms);
    noTone(CALVIN_BUZZER);
    delay(50);
  }
}`,
                setup: '  pinMode(CALVIN_BUZZER, OUTPUT);'
            };
        },

        getRgbCode: function(pinR, pinG, pinB, tipo, isEsp32) {
            const t = (tipo === undefined || tipo === null || tipo === '') ? 'A' : tipo;
            if (isEsp32) {
                const r = pinR || CALVIN_PINS_ESP32.RGB_R;
                const g = pinG || CALVIN_PINS_ESP32.RGB_G;
                const b = pinB || CALVIN_PINS_ESP32.RGB_B;
                // En Calvin tipo "A" = cátodo común (HIGH=ON), tipo "C" = ánodo común (LOW=ON)
                const useAnodo = (String(t).toUpperCase() === 'A') ? 0 : 1;
                return {
                    defines: `#define Rojo ${r}\n#define Verde ${g}\n#define Azul ${b}\n#define CALVIN_RGB_ANODO ${useAnodo}`,
                    func: `void calvin_rgb_encender(int r, int g, int b, int duracion_ms) {
  int vR = (r > 0) ? (CALVIN_RGB_ANODO ? 0 : 1) : (CALVIN_RGB_ANODO ? 1 : 0);
  int vG = (g > 0) ? (CALVIN_RGB_ANODO ? 0 : 1) : (CALVIN_RGB_ANODO ? 1 : 0);
  int vB = (b > 0) ? (CALVIN_RGB_ANODO ? 0 : 1) : (CALVIN_RGB_ANODO ? 1 : 0);
  digitalWrite(Rojo, vR);
  digitalWrite(Verde, vG);
  digitalWrite(Azul, vB);
  if (duracion_ms > 0) {
    delay(duracion_ms);
    digitalWrite(Rojo, CALVIN_RGB_ANODO ? 1 : 0);
    digitalWrite(Verde, CALVIN_RGB_ANODO ? 1 : 0);
    digitalWrite(Azul, CALVIN_RGB_ANODO ? 1 : 0);
  }
}`,
                    setup: '  pinMode(Rojo, OUTPUT);\n  pinMode(Verde, OUTPUT);\n  pinMode(Azul, OUTPUT);\n  digitalWrite(Rojo, CALVIN_RGB_ANODO);\n  digitalWrite(Verde, CALVIN_RGB_ANODO);\n  digitalWrite(Azul, CALVIN_RGB_ANODO);'
                };
            }
            const r = pinR || CALVIN_PINS.RGB_R;
            const g = pinG || CALVIN_PINS.RGB_G;
            const b = pinB || CALVIN_PINS.RGB_B;
            const invert = (String(t).toUpperCase() === 'A');
                return {
                defines: `#define CALVIN_RGB_R ${r}\n#define CALVIN_RGB_G ${g}\n#define CALVIN_RGB_B ${b}\n#define CALVIN_RGB_ANODO ${invert ? 1 : 0}`,
                func: `void calvin_rgb_encender(int r, int g, int b, int duracion_ms) {
  if (CALVIN_RGB_ANODO) { r=255-r; g=255-g; b=255-b; }
  analogWrite(CALVIN_RGB_R, r);
  analogWrite(CALVIN_RGB_G, g);
  analogWrite(CALVIN_RGB_B, b);
  delay(duracion_ms);
  analogWrite(CALVIN_RGB_R, CALVIN_RGB_ANODO?255:0);
  analogWrite(CALVIN_RGB_G, CALVIN_RGB_ANODO?255:0);
  analogWrite(CALVIN_RGB_B, CALVIN_RGB_ANODO?255:0);
}`,
                setup: '  pinMode(CALVIN_RGB_R, OUTPUT);\n  pinMode(CALVIN_RGB_G, OUTPUT);\n  pinMode(CALVIN_RGB_B, OUTPUT);'
            };
        },

        getMotorsCode: function(pinIzq, pinDer, pwmDefault, isEsp32) {
            if (isEsp32) {
                const in1 = CALVIN_PINS_ESP32.IN_1, in2 = CALVIN_PINS_ESP32.IN_2;
                const in3 = CALVIN_PINS_ESP32.IN_3, in4 = CALVIN_PINS_ESP32.IN_4;
                const speedCar = Math.min(255, Math.max(0, pwmDefault !== undefined && pwmDefault !== null ? pwmDefault : 220));
                return {
                    includes: '',
                    defines: `#define IN_1 ${in1}\n#define IN_2 ${in2}\n#define IN_3 ${in3}\n#define IN_4 ${in4}\n#define speedCar ${speedCar}`,
                    vars: `const int resolution = 8;
const int frequency = 8000;

void calvin_mover(int modo, float duracion) {
  if (modo == 0) {
    ledcWrite(IN_1, 0);
    ledcWrite(IN_2, 0);
    ledcWrite(IN_3, 0);
    ledcWrite(IN_4, 0);
  } else if (modo == 1) {
    ledcWrite(IN_1, 0);
    ledcWrite(IN_2, speedCar);
    ledcWrite(IN_3, speedCar);
    ledcWrite(IN_4, 0);
  } else if (modo == 2) {
    ledcWrite(IN_1, speedCar);
    ledcWrite(IN_2, 0);
    ledcWrite(IN_3, 0);
    ledcWrite(IN_4, speedCar);
  } else if (modo == 3) {
    ledcWrite(IN_1, speedCar);
    ledcWrite(IN_2, 0);
    ledcWrite(IN_3, speedCar);
    ledcWrite(IN_4, 0);
  } else if (modo == 4) {
    ledcWrite(IN_1, 0);
    ledcWrite(IN_2, speedCar);
    ledcWrite(IN_3, 0);
    ledcWrite(IN_4, speedCar);
  } else if (modo == 6) {
    ledcWrite(IN_3, speedCar);
    ledcWrite(IN_4, 0);
  } else if (modo == 7) {
    ledcWrite(IN_3, 0);
    ledcWrite(IN_4, speedCar);
  } else if (modo == 8) {
    ledcWrite(IN_1, speedCar);
    ledcWrite(IN_2, 0);
  } else if (modo == 9) {
    ledcWrite(IN_1, 0);
    ledcWrite(IN_2, speedCar);
  }
  if (duracion > 0.0f) {
    delay((int)(duracion * 1000));
    ledcWrite(IN_1, 0);
    ledcWrite(IN_2, 0);
    ledcWrite(IN_3, 0);
    ledcWrite(IN_4, 0);
  }
}

void calvin_motor_adelante(float seg) { calvin_mover(1, seg); }
void calvin_motor_girar(int lado, int sentido, float seg) {
  int modo = (lado == 0) ? (sentido == 0 ? 8 : 9) : (sentido == 0 ? 6 : 7);
  calvin_mover(modo, seg);
}`,
                    setup: `  ledcAttach(IN_1, frequency, resolution);
  ledcAttach(IN_2, frequency, resolution);
  ledcAttach(IN_3, frequency, resolution);
  ledcAttach(IN_4, frequency, resolution);`
                };
            }
            const izq = pinIzq || CALVIN_PINS.MOTOR_IZQ;
            const der = pinDer || CALVIN_PINS.MOTOR_DER;
            const pwm255 = pwmDefault !== undefined && pwmDefault !== null ? pwmDefault : 220;
            const pwm = Math.round(Math.min(255, Math.max(0, pwm255)) * 90 / 255);
            return {
                includes: '#include <Servo.h>',
                defines: `#define CALVIN_MOTOR_IZQ ${izq}\n#define CALVIN_MOTOR_DER ${der}\n#define CALVIN_PWM_DEFAULT ${pwm}`,
                vars: 'Servo calvin_servoIzq;\nServo calvin_servoDer;',
                func: `void calvin_mover(int modo, float seg) {
  int v = CALVIN_PWM_DEFAULT;
  if (modo == 1) {
    calvin_servoIzq.write(90 - v);
    calvin_servoDer.write(90 + v);
  } else if (modo == 2) {
    calvin_servoIzq.write(90 + v);
    calvin_servoDer.write(90 - v);
  } else if (modo == 3) {
    calvin_servoIzq.write(90 + v);
    calvin_servoDer.write(90 + v);
  } else if (modo == 4) {
    calvin_servoIzq.write(90 - v);
    calvin_servoDer.write(90 - v);
  } else {
    calvin_servoIzq.write(90);
    calvin_servoDer.write(90);
    return;
  }
  delay(seg * 1000);
  calvin_servoIzq.write(90);
  calvin_servoDer.write(90);
}
void calvin_motor_adelante(float seg) { calvin_mover(1, seg); }
void calvin_motor_girar(int lado, int sentido, float seg) {
  int v = CALVIN_PWM_DEFAULT;
  if (lado == 0) {
    calvin_servoIzq.write(sentido == 0 ? 90+v : 90-v);
    calvin_servoDer.write(90);
  } else {
    calvin_servoIzq.write(90);
    calvin_servoDer.write(sentido == 0 ? 90+v : 90-v);
  }
  delay(seg * 1000);
  calvin_servoIzq.write(90);
  calvin_servoDer.write(90);
}`,
                setup: '  calvin_servoIzq.attach(CALVIN_MOTOR_IZQ);\n  calvin_servoDer.attach(CALVIN_MOTOR_DER);\n  calvin_servoIzq.write(90);\n  calvin_servoDer.write(90);'
            };
        },

        getLineSensorsCode: function(pinIzq, pinCent, pinDer, isEsp32) {
            if (isEsp32) {
                const izq = pinIzq !== undefined && pinIzq !== null ? pinIzq : CALVIN_PINS_ESP32.LINEA_IZQ;
                const cent = pinCent !== undefined && pinCent !== null ? pinCent : CALVIN_PINS_ESP32.LINEA_CENT;
                const der = pinDer !== undefined && pinDer !== null ? pinDer : CALVIN_PINS_ESP32.LINEA_DER;
                return {
                    defines: `#define sensorIzq ${izq}\n#define sensorCen ${cent}\n#define sensorDer ${der}`,
                    vars: `int umbralIzq = 512, umbralCen = 512, umbralDer = 512;
int umbralIzqAnt = 1023, umbralCenAnt = 1023, umbralDerAnt = 1023;`,
                    func: `int calvin_linea_valor(int lado) {
  if (lado == 0) return analogRead(sensorIzq);
  if (lado == 1) return analogRead(sensorCen);
  return analogRead(sensorDer);
}
int calvin_linea_umbral(int lado) {
  if (lado == 0) return umbralIzq;
  if (lado == 1) return umbralCen;
  return umbralDer;
}
void calvin_linea_calibrar(int n) {
  for (int i = 0; i < n; i++) {
    int readIzq = analogRead(sensorIzq);
    int readCen = analogRead(sensorCen);
    int readDer = analogRead(sensorDer);
    if (readIzq < umbralIzqAnt) umbralIzq = readIzq + 15;
    if (readCen < umbralCenAnt) umbralCen = readCen + 15;
    if (readDer < umbralDerAnt) umbralDer = readDer + 15;
    umbralIzqAnt = readIzq;
    umbralCenAnt = readCen;
    umbralDerAnt = readDer;
    delay(200);
  }
}`,
                    setup: '  pinMode(sensorIzq, INPUT);\n  pinMode(sensorCen, INPUT);\n  pinMode(sensorDer, INPUT);'
                };
            }
            const izq = pinIzq !== undefined && pinIzq !== null ? pinIzq : CALVIN_PINS.LINEA_IZQ;
            const cent = pinCent !== undefined && pinCent !== null ? pinCent : CALVIN_PINS.LINEA_CENT;
            const der = pinDer !== undefined && pinDer !== null ? pinDer : CALVIN_PINS.LINEA_DER;
            return {
                defines: `#define CALVIN_LINEA_IZQ A${izq}\n#define CALVIN_LINEA_CENT A${cent}\n#define CALVIN_LINEA_DER A${der}`,
                vars: `int _calvin_linea_izq_min = 1023, _calvin_linea_izq_max = 0;
int _calvin_linea_cent_min = 1023, _calvin_linea_cent_max = 0;
int _calvin_linea_der_min = 1023, _calvin_linea_der_max = 0;`,
                func: `int calvin_linea_valor(int lado) {
  if (lado == 0) return analogRead(CALVIN_LINEA_IZQ);
  if (lado == 1) return analogRead(CALVIN_LINEA_CENT);
  return analogRead(CALVIN_LINEA_DER);
}
int calvin_linea_umbral(int lado) {
  int mn, mx;
  if (lado == 0) { mn = _calvin_linea_izq_min; mx = _calvin_linea_izq_max; }
  else if (lado == 1) { mn = _calvin_linea_cent_min; mx = _calvin_linea_cent_max; }
  else { mn = _calvin_linea_der_min; mx = _calvin_linea_der_max; }
  return (mn + mx) / 2;
}
void calvin_linea_calibrar(int n) {
  for (int i = 0; i < n; i++) {
    int v = analogRead(CALVIN_LINEA_IZQ);
    if (v < _calvin_linea_izq_min) _calvin_linea_izq_min = v;
    if (v > _calvin_linea_izq_max) _calvin_linea_izq_max = v;
    v = analogRead(CALVIN_LINEA_CENT);
    if (v < _calvin_linea_cent_min) _calvin_linea_cent_min = v;
    if (v > _calvin_linea_cent_max) _calvin_linea_cent_max = v;
    v = analogRead(CALVIN_LINEA_DER);
    if (v < _calvin_linea_der_min) _calvin_linea_der_min = v;
    if (v > _calvin_linea_der_max) _calvin_linea_der_max = v;
    delay(20);
  }
}`,
                setup: '  pinMode(CALVIN_LINEA_IZQ, INPUT);\n  pinMode(CALVIN_LINEA_CENT, INPUT);\n  pinMode(CALVIN_LINEA_DER, INPUT);'
            };
        }
    };

    // === Documentación de consolidación ===
    // CONSERVADO: Pines verificados con carro Calvin/BotFlow funcionando.
    // CORREGIDO: getMotorsCode ESP32 ahora usa CALVIN_PINS_ESP32.IN_1..4 en lugar de literales.
    // CORREGIDO: calvin_generator obtiene todos los pines desde CalvinHardware (antes hardcodeados).
})();
