/**
 * Calvin Hardware - Capa de abstracción centralizada
 * Proximidad, Buzzer, RGB, Motores. NO mezcla con max_*
 */
(function() {
    'use strict';

    // Pines por defecto (configurables si el bloque los especifica)
    // RGB en 5,6,11 para no chocar con motores 9,10
    const CALVIN_PINS = {
        PROX_TRIG: 6,
        PROX_ECHO: 7,
        BUZZER: 3,
        RGB_R: 5,
        RGB_G: 6,
        RGB_B: 11,
        MOTOR_IZQ: 9,
        MOTOR_DER: 10,
        LINEA_IZQ: 0,
        LINEA_CENT: 1,
        LINEA_DER: 2
    };

    // Notas musicales: [octava][nota] -> frecuencia Hz
    const NOTAS = {
        DO: [131, 262, 523],
        RE: [147, 294, 587],
        MI: [165, 330, 659],
        FA: [175, 349, 698],
        SOL: [196, 392, 784],
        LA: [220, 440, 880],
        SI: [247, 494, 988]
    };

    function getNoteFreq(nota, octava) {
        const arr = NOTAS[nota] || NOTAS.DO;
        const oct = Math.max(0, Math.min(2, (octava | 0) - 3));
        return arr[oct] || 262;
    }

    window.CalvinHardware = {
        PINS: CALVIN_PINS,
        getNoteFreq: getNoteFreq,

        getProximityCode: function(pinTrig, pinEcho) {
            const t = pinTrig || CALVIN_PINS.PROX_TRIG;
            const e = pinEcho || CALVIN_PINS.PROX_ECHO;
            return {
                defines: `#define CALVIN_PROX_TRIG ${t}\n#define CALVIN_PROX_ECHO ${e}`,
                vars: 'long _calvin_prox_us;\nfloat _calvin_prox_cm;',
                func: `float calvin_distancia_cm(void) {
  digitalWrite(CALVIN_PROX_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(CALVIN_PROX_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(CALVIN_PROX_TRIG, LOW);
  _calvin_prox_us = pulseIn(CALVIN_PROX_ECHO, HIGH, 30000);
  _calvin_prox_cm = _calvin_prox_us * 0.034f / 2.0f;
  return _calvin_prox_cm;
}`,
                setup: '  pinMode(CALVIN_PROX_TRIG, OUTPUT);\n  pinMode(CALVIN_PROX_ECHO, INPUT);'
            };
        },

        getBuzzerCode: function(pin) {
            const p = pin || CALVIN_PINS.BUZZER;
            return {
                defines: `#define CALVIN_BUZZER ${p}`,
                func: `void calvin_tocar_nota(int freq, int duracion_ms) {
  tone(CALVIN_BUZZER, freq, duracion_ms);
  delay(duracion_ms);
  noTone(CALVIN_BUZZER);
  delay(50);
}`,
                setup: '  pinMode(CALVIN_BUZZER, OUTPUT);'
            };
        },

        getRgbCode: function(pinR, pinG, pinB, tipo) {
            const r = pinR || CALVIN_PINS.RGB_R;
            const g = pinG || CALVIN_PINS.RGB_G;
            const b = pinB || CALVIN_PINS.RGB_B;
            const invert = (tipo === 'A'); // Common Anode = invertir
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

        getMotorsCode: function(pinIzq, pinDer, pwmDefault) {
            const izq = pinIzq || CALVIN_PINS.MOTOR_IZQ;
            const der = pinDer || CALVIN_PINS.MOTOR_DER;
            const pwm = pwmDefault || 30;
            return {
                includes: '#include <Servo.h>',
                defines: `#define CALVIN_MOTOR_IZQ ${izq}\n#define CALVIN_MOTOR_DER ${der}\n#define CALVIN_PWM_DEFAULT ${pwm}`,
                vars: 'Servo calvin_servoIzq;\nServo calvin_servoDer;',
                func: `void calvin_motor_adelante(int seg) {
  calvin_servoIzq.write(90 - CALVIN_PWM_DEFAULT);
  calvin_servoDer.write(90 + CALVIN_PWM_DEFAULT);
  delay(seg * 1000);
  calvin_servoIzq.write(90);
  calvin_servoDer.write(90);
}
void calvin_motor_girar(int lado, int sentido, int seg) {
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

        getLineSensorsCode: function(pinIzq, pinCent, pinDer) {
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
})();
