#include <Braccio.h>
#include <Servo.h>

// Objetos requeridos por la libreria Braccio.
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;

const int STEP_DELAY_MS = 20;

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

void testPose(
  const char* label,
  int m1,
  int m2,
  int m3,
  int m4,
  int m5,
  int m6
) {
  Serial.println();
  Serial.println(label);
  moveToSafePose();
  delay(1500);
  Braccio.ServoMovement(STEP_DELAY_MS, m1, m2, m3, m4, m5, m6);
  delay(2000);
  moveToSafePose();
  delay(1500);
}

void setup() {
  Serial.begin(9600);
  Braccio.begin();
  delay(2000);

  Serial.println("Identificacion de puertos M1..M6 del Braccio");
  Serial.println("Observa que articulacion se mueve en cada bloque.");
  Serial.println("Si el texto dice M1 y se mueve otra articulacion, hay cableado cruzado.");
}

void loop() {
  testPose(
    "Prueba M1 / base / pin D11",
    120,
    SAFE_SHOULDER,
    SAFE_ELBOW,
    SAFE_WRIST_VER,
    SAFE_WRIST_ROT,
    SAFE_GRIPPER
  );

  testPose(
    "Prueba M2 / shoulder / pin D10",
    SAFE_BASE,
    70,
    SAFE_ELBOW,
    SAFE_WRIST_VER,
    SAFE_WRIST_ROT,
    SAFE_GRIPPER
  );

  testPose(
    "Prueba M3 / elbow / pin D9",
    SAFE_BASE,
    SAFE_SHOULDER,
    140,
    SAFE_WRIST_VER,
    SAFE_WRIST_ROT,
    SAFE_GRIPPER
  );

  testPose(
    "Prueba M4 / wrist vertical / pin D6",
    SAFE_BASE,
    SAFE_SHOULDER,
    SAFE_ELBOW,
    140,
    SAFE_WRIST_ROT,
    SAFE_GRIPPER
  );

  testPose(
    "Prueba M5 / wrist rotation / pin D5",
    SAFE_BASE,
    SAFE_SHOULDER,
    SAFE_ELBOW,
    SAFE_WRIST_VER,
    130,
    SAFE_GRIPPER
  );

  testPose(
    "Prueba M6 / gripper / pin D3",
    SAFE_BASE,
    SAFE_SHOULDER,
    SAFE_ELBOW,
    SAFE_WRIST_VER,
    SAFE_WRIST_ROT,
    45
  );

  Serial.println();
  Serial.println("Fin del barrido. Reiniciando en 5 segundos.");
  delay(5000);
}
