#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wristVer;
Servo wristRot;
Servo gripper;

const int SAFE_BASE = 90;
const int SAFE_SHOULDER = 45;
const int SAFE_ELBOW = 180;
const int SAFE_WRIST_VER = 180;
const int SAFE_WRIST_ROT = 90;
const int SAFE_GRIPPER = 10;

void writeSafePose() {
  base.write(SAFE_BASE);
  shoulder.write(SAFE_SHOULDER);
  elbow.write(SAFE_ELBOW);
  wristVer.write(SAFE_WRIST_VER);
  wristRot.write(SAFE_WRIST_ROT);
  gripper.write(SAFE_GRIPPER);
}

void setup() {
  base.attach(11);
  shoulder.attach(10);
  elbow.attach(9);
  wristVer.attach(6);
  wristRot.attach(5);
  gripper.attach(3);

  delay(3000);
  writeSafePose();
  delay(4000);
}

void loop() {
  // Pose de seguridad antes de empezar cada barrido.
  writeSafePose();
  delay(3000);

  // BASE: giro completo izquierda -> derecha
  base.write(0);
  delay(5000);
  base.write(180);
  delay(5000);
  writeSafePose();
  delay(3000);

  // SHOULDER: subir -> bajar
  shoulder.write(15);
  delay(5000);
  shoulder.write(165);
  delay(5000);
  writeSafePose();
  delay(3000);

  // ELBOW: extendido -> plegado
  elbow.write(0);
  delay(5000);
  elbow.write(180);
  delay(5000);
  writeSafePose();
  delay(3000);

  // WRIST VERTICAL: arriba -> abajo
  wristVer.write(0);
  delay(5000);
  wristVer.write(180);
  delay(5000);
  writeSafePose();
  delay(3000);

  // WRIST ROTATION: giro completo
  wristRot.write(0);
  delay(5000);
  wristRot.write(180);
  delay(5000);
  writeSafePose();
  delay(3000);

  // GRIPPER: abrir -> cerrar
  gripper.write(10);
  delay(5000);
  gripper.write(73);
  delay(5000);
  writeSafePose();
  delay(3000);

  // COMBINADA: extremos minimos -> extremos maximos
  base.write(0);
  shoulder.write(15);
  elbow.write(0);
  wristVer.write(0);
  wristRot.write(0);
  gripper.write(10);
  delay(6000);

  base.write(180);
  shoulder.write(165);
  elbow.write(180);
  wristVer.write(180);
  wristRot.write(180);
  gripper.write(73);
  delay(6000);

  writeSafePose();
  delay(4000);
}
