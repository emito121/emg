#include <Servo.h>

Servo servo1; //Dedo 1
Servo servo2; //Dedo 2
Servo servo3; //Dedo 3
Servo servo4; //Dedo 4
Servo servo5; //Dedo 5

int servoPin1 = 6;
int servoPin2 = 5;
int servoPin3 = 3;
int servoPin4 = 9;
int servoPin5 = 10;

// Umbral para activar los servos
// int emgThreshold = 500;  // Cambia este valor según el umbral

// Variable para almacenar la señal EMG
// int emgSignal;

// Variable para almacenar el estado de los servos (activo o no)
bool servosActivos = false;

void setup() {
  // Adjuntar los servos a los pines
  servo1.attach(servoPin1);
  servo2.attach(servoPin2);
  servo3.attach(servoPin3);
  servo4.attach(servoPin4);
  servo5.attach(servoPin5);

  // Inicializar los servos en posición neutra
  servo1.write(0); 
  servo2.write(0);
  servo3.write(0);
  servo4.write(1);
  servo5.write(0);

  // Inicializar la comunicación serial 
  Serial.begin(9600);
  // Serial.print("Umbral configurado en: ");
  // Serial.println(emgThreshold);
}

void loop() {
  // Verificar si hay datos disponibles en el monitor serial para leer la señal EMG
  if (Serial.available() > 0) {
    // emgSignal = Serial.parseInt(); // Leer el valor de la señal EMG desde el monitor serial
    // Serial.print("EMG Signal: ");
    // Serial.println(emgSignal);
    char command = Serial.read(); // Leer el dato enviado desde el PC
    
    if (command == '1') {
      // Si la señal es mayor al umbral y los servos no están activos, activarlos a 100 grados
      if (!servosActivos) {
        moverServosA100Grados();
        servosActivos = true; // Cambiar el estado a activo
      }
    } else if (command == '0') {
      // Si la señal es menor al umbral y los servos están activos, desactivarlos
      if (servosActivos) {
        resetearServos();
        servosActivos = false; // Cambiar el estado a inactivo
      }
    }
  }
}

void moverServosA100Grados() {
  // Mover todos los servos a cierto grados
  servo1.write(88);
  servo2.write(70);
  servo3.write(88);
  servo4.write(88);
  servo5.write(88);
  // delay(200); //sacar en la prigramacion final
}

void resetearServos() {
  // Volver los servos a la posición neutra
  servo1.write(0); // Se puede cambiar a 0 si prefieres la posición totalmente neutra
  servo2.write(0);
  servo3.write(0);
  servo4.write(1);
  servo5.write(0);
}
//Diagrama de bloque hacer