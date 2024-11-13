#include <Servo.h>

Servo servo;           // Objeto para controlar el servomotor
const int ledPin = 13; // Pin donde está conectado el LED
const int servoPin = 9; // Pin donde está conectado el servomotor

void setup() {
  Serial.begin(9600);     // Iniciar comunicación serial a 9600 bps
  pinMode(ledPin, OUTPUT); // Configurar el pin del LED como salida
  servo.attach(servoPin); // Asignar el pin del servomotor
  servo.write(0);          // Posición inicial del servomotor (reposo)
}

void loop() {
  if (Serial.available() > 0) { // Comprobar si hay datos en la serie
    char command = Serial.read(); // Leer el dato enviado desde el PC

    if (command == '1') {
      digitalWrite(ledPin, HIGH); // Encender el LED
      servo.write(90);            // Mover el servomotor a 90 grados
      Serial.println('ON');
  } 
    else if (command == '0') {
          digitalWrite(ledPin, LOW);  // Apagar el LED
          servo.write(0);             // Mover el servomotor a la posición de reposo (0 grados)
        Serial.println('OFF');
      }
  }
}
