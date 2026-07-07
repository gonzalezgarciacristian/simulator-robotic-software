#include <Braccio.h>
#include <Servo.h>

// Estas 6 lineas son obligatorias para la libreria Braccio.
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;

const int STEP_DELAY_MS = 20;

// Pose de seguridad oficial usada por Braccio.begin().
const int SAFE_BASE = 90;
const int SAFE_SHOULDER = 45;
const int SAFE_ELBOW = 180;
const int SAFE_WRIST_VER = 180;
const int SAFE_WRIST_ROT = 90;
const int SAFE_GRIPPER = 10;

void moveToSafePose() {
  Braccio.ServoMovement(
    STEP_DELAY_MS,
    SAFE_BASE,
    SAFE_SHOULDER,
    SAFE_ELBOW,
    SAFE_WRIST_VER,
    SAFE_WRIST_ROT,
    SAFE_GRIPPER
  );
}

void setup() {
  Braccio.begin();
}

void loop() {
  // Pose de seguridad antes de empezar cada barrido.
  moveToSafePose();
  delay(500);

  // BASE: giro completo izquierda -> derecha
  Braccio.ServoMovement(STEP_DELAY_MS, 0, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, 180, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  moveToSafePose();
  delay(300);

  // SHOULDER: subir -> bajar
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, 15, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, 165, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  moveToSafePose();
  delay(300);

  // ELBOW: extendido -> plegado
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, 0, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, 180, SAFE_WRIST_VER, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  moveToSafePose();
  delay(300);

  // WRIST VERTICAL: arriba -> abajo
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, 0, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, 180, SAFE_WRIST_ROT, SAFE_GRIPPER);
  delay(500);
  moveToSafePose();
  delay(300);

  // WRIST ROTATION: giro completo
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, 0, SAFE_GRIPPER);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, 180, SAFE_GRIPPER);
  delay(500);
  moveToSafePose();
  delay(300);

  // GRIPPER: abrir -> cerrar
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, 10);
  delay(500);
  Braccio.ServoMovement(STEP_DELAY_MS, SAFE_BASE, SAFE_SHOULDER, SAFE_ELBOW, SAFE_WRIST_VER, SAFE_WRIST_ROT, 73);
  delay(500);
  moveToSafePose();
  delay(300);

  // COMBINADA: extremos minimos -> extremos maximos.
  Braccio.ServoMovement(STEP_DELAY_MS, 0, 15, 0, 0, 0, 10);
  delay(800);
  Braccio.ServoMovement(STEP_DELAY_MS, 180, 165, 180, 180, 180, 73);
  delay(800);
  moveToSafePose();
  delay(1000);
}
