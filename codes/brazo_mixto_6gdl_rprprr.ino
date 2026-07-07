#include <Servo.h>

Servo base;       // J1 - R - pin 11
Servo elevador;   // J2 - P - pin 10
Servo hombro;     // J3 - R - pin 9
Servo extension;  // J4 - P - pin 6
Servo muneca;     // J5 - R - pin 5
Servo pinza;      // J6 - R gripper - pin 3

const int STOP_PRISMATICA = 90;
const int AVANZA_PRISMATICA = 0;
const int RETROCEDE_PRISMATICA = 180;

const int PINZA_ABIERTA = 10;
const int PINZA_MEDIA = 40;
const int PINZA_CERRADA = 73;

void pararPrismaticas() {
  elevador.write(STOP_PRISMATICA);
  extension.write(STOP_PRISMATICA);
}

void poseCentro() {
  base.write(90);
  pararPrismaticas();
  hombro.write(115);
  muneca.write(90);
  pinza.write(PINZA_MEDIA);
}

void setup() {
  base.attach(11);
  elevador.attach(10);
  hombro.attach(9);
  extension.attach(6);
  muneca.attach(5);
  pinza.attach(3);

  poseCentro();
  delay(1200);
}

void loop() {
  // Abrir pinza y orientar el brazo.
  pinza.write(PINZA_ABIERTA);
  base.write(55);
  hombro.write(125);
  muneca.write(70);
  delay(1200);

  // Subir el eje prismático vertical J2.
  elevador.write(AVANZA_PRISMATICA);
  delay(1800);
  elevador.write(STOP_PRISMATICA);
  delay(600);

  // Extender la prismática telescópica J4.
  extension.write(AVANZA_PRISMATICA);
  delay(1500);
  extension.write(STOP_PRISMATICA);
  delay(600);

  // Cerrar pinza y girar a otra pose.
  pinza.write(PINZA_CERRADA);
  base.write(130);
  hombro.write(65);
  muneca.write(125);
  delay(1300);

  // Retraer la telescópica J4.
  extension.write(RETROCEDE_PRISMATICA);
  delay(1500);
  extension.write(STOP_PRISMATICA);
  delay(600);

  // Bajar el elevador J2.
  elevador.write(RETROCEDE_PRISMATICA);
  delay(1800);
  elevador.write(STOP_PRISMATICA);
  delay(600);

  // Volver al centro con pinza semiabierta.
  poseCentro();
  delay(1400);
}
