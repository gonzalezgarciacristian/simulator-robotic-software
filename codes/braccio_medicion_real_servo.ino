#include <Servo.h>
#include <stdlib.h>

// Medicion equivalente a braccio_medicion_real, pero sin usar Braccio.h.
// Esto evita los limites por articulacion que aplica Braccio.ServoMovement.
//
// Nota importante: Servo.write() no aplica los limites propios del Braccio,
// pero la libreria Servo de Arduino sigue interpretando angulos como 0..180.

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;

const int PIN_M1_BASE = 11;
const int PIN_M2_SHOULDER = 10;
const int PIN_M3_ELBOW = 9;
const int PIN_M4_WRIST_VER = 6;
const int PIN_M5_WRIST_ROT = 5;
const int PIN_M6_GRIPPER = 3;

const int STEP_DELAY_MS = 20;
const int SAFE_M2_ANGLE = 45;
const unsigned long SERIAL_BAUD_RATE = 9600;

int currentM1 = 90;
int currentM2 = SAFE_M2_ANGLE;
int currentM3 = 180;
int currentM4 = 180;
int currentM5 = 90;
int currentM6 = 10;

int selectedMotor = 1;
int angleStep = 1;
unsigned long movementCounter = 0;

int lastDirectionM1 = 0;
int lastDirectionM2 = 0;
int lastDirectionM3 = 0;
int lastDirectionM4 = 0;
int lastDirectionM5 = 0;
int lastDirectionM6 = 0;

void attachServos() {
  base.attach(PIN_M1_BASE);
  shoulder.attach(PIN_M2_SHOULDER);
  elbow.attach(PIN_M3_ELBOW);
  wrist_ver.attach(PIN_M4_WRIST_VER);
  wrist_rot.attach(PIN_M5_WRIST_ROT);
  gripper.attach(PIN_M6_GRIPPER);
}

void applyPose() {
  base.write(currentM1);
  shoulder.write(currentM2);
  elbow.write(currentM3);
  wrist_ver.write(currentM4);
  wrist_rot.write(currentM5);
  gripper.write(currentM6);
  delay(STEP_DELAY_MS);
}

const char* labelForMotor(int motor) {
  switch (motor) {
    case 1:
      return "base";
    case 2:
      return "shoulder";
    case 3:
      return "elbow";
    case 4:
      return "wrist_vertical";
    case 5:
      return "wrist_rotation";
    case 6:
      return "gripper";
    default:
      return "unknown";
  }
}

int angleForMotor(int motor) {
  switch (motor) {
    case 1:
      return currentM1;
    case 2:
      return currentM2;
    case 3:
      return currentM3;
    case 4:
      return currentM4;
    case 5:
      return currentM5;
    case 6:
      return currentM6;
    default:
      return 0;
  }
}

void setAngleForMotor(int motor, int value) {
  switch (motor) {
    case 1:
      currentM1 = value;
      break;
    case 2:
      currentM2 = value;
      break;
    case 3:
      currentM3 = value;
      break;
    case 4:
      currentM4 = value;
      break;
    case 5:
      currentM5 = value;
      break;
    case 6:
      currentM6 = value;
      break;
  }
}

int lastDirectionForMotor(int motor) {
  switch (motor) {
    case 1:
      return lastDirectionM1;
    case 2:
      return lastDirectionM2;
    case 3:
      return lastDirectionM3;
    case 4:
      return lastDirectionM4;
    case 5:
      return lastDirectionM5;
    case 6:
      return lastDirectionM6;
    default:
      return 0;
  }
}

void setLastDirectionForMotor(int motor, int value) {
  switch (motor) {
    case 1:
      lastDirectionM1 = value;
      break;
    case 2:
      lastDirectionM2 = value;
      break;
    case 3:
      lastDirectionM3 = value;
      break;
    case 4:
      lastDirectionM4 = value;
      break;
    case 5:
      lastDirectionM5 = value;
      break;
    case 6:
      lastDirectionM6 = value;
      break;
  }
}

int directionForDelta(int delta) {
  if (delta > 0) {
    return 1;
  }
  if (delta < 0) {
    return -1;
  }
  return 0;
}

bool tryParseLong(const String& text, long& value) {
  if (text.length() == 0) {
    return false;
  }

  char buffer[32];
  if (text.length() >= (int)sizeof(buffer)) {
    return false;
  }

  text.toCharArray(buffer, sizeof(buffer));

  char* end = nullptr;
  value = strtol(buffer, &end, 10);
  return end != buffer && *end == '\0';
}

void printPose() {
  Serial.println();
  Serial.println(F("POSE"));
  Serial.print(F("selected_motor=M"));
  Serial.print(selectedMotor);
  Serial.print(F(" label="));
  Serial.println(labelForMotor(selectedMotor));
  Serial.print(F("step="));
  Serial.println(angleStep);
  Serial.print(F("M1="));
  Serial.println(currentM1);
  Serial.print(F("M2="));
  Serial.println(currentM2);
  Serial.print(F("M3="));
  Serial.println(currentM3);
  Serial.print(F("M4="));
  Serial.println(currentM4);
  Serial.print(F("M5="));
  Serial.println(currentM5);
  Serial.print(F("M6="));
  Serial.println(currentM6);
  Serial.println(F("Los angulos mostrados son los mandados con Servo.write()."));
  Serial.println(F("No se usan los limites por articulacion de Braccio.h."));
}

void printProtocol() {
  Serial.println();
  Serial.println(F("PROTOCOLO_LIMITES"));
  Serial.println(F("1. Selecciona motor con m1/m2/m3/m4/m5/m6."));
  Serial.println(F("2. Usa step 5 o step 10 para acercarte al limite."));
  Serial.println(F("3. Cuando estes cerca, cambia a step 1."));
  Serial.println(F("4. Avanza hasta el ultimo comando seguro."));
  Serial.println(F("5. Anota el angulo visible como limite real de esa articulacion."));
  Serial.println();
  Serial.println(F("PROTOCOLO_HOLGURA"));
  Serial.println(F("1. Coloca una referencia visual en la articulacion."));
  Serial.println(F("2. Usa step 1."));
  Serial.println(F("3. Mueve en un sentido hasta estabilizar la referencia."));
  Serial.println(F("4. Invierte el sentido y cuenta ordenes hasta ver movimiento real."));
  Serial.println(F("5. Esa cuenta es la holgura aproximada en grados de comando."));
}

void printHelp() {
  Serial.println();
  Serial.println(F("COMANDOS"));
  Serial.println(F("help           -> mostrar ayuda"));
  Serial.println(F("protocol       -> mostrar protocolo de medicion"));
  Serial.println(F("pose           -> imprimir pose actual"));
  Serial.println(F("reset          -> volver a la pose base"));
  Serial.println(F("m1 m2 m3 m4 m5 m6 -> seleccionar motor"));
  Serial.println(F("step N         -> fijar paso incremental"));
  Serial.println(F("+              -> sumar el paso actual"));
  Serial.println(F("-              -> restar el paso actual"));
  Serial.println(F("+N             -> sumar N grados"));
  Serial.println(F("-N             -> restar N grados"));
  Serial.println(F("N              -> enviar ese angulo absoluto al motor seleccionado"));
  Serial.println(F("go N           -> enviar angulo absoluto al motor seleccionado"));
  Serial.println(F("note texto     -> dejar una nota en el log serie"));
}

void printMovementLog(const char* mode, int motor, int previousAngle, int targetAngle, int delta, bool reversed) {
  movementCounter++;
  Serial.println();
  Serial.print(F("LOG seq="));
  Serial.print(movementCounter);
  Serial.print(F(" mode="));
  Serial.print(mode);
  Serial.print(F(" motor=M"));
  Serial.print(motor);
  Serial.print(F(" label="));
  Serial.print(labelForMotor(motor));
  Serial.print(F(" previous="));
  Serial.print(previousAngle);
  Serial.print(F(" target="));
  Serial.print(targetAngle);
  Serial.print(F(" delta="));
  Serial.print(delta);
  Serial.print(F(" reversed="));
  Serial.println(reversed ? F("yes") : F("no"));
}

void selectMotor(int motor) {
  selectedMotor = motor;
  Serial.println();
  Serial.print(F("Motor seleccionado: M"));
  Serial.print(selectedMotor);
  Serial.print(F(" ("));
  Serial.print(labelForMotor(selectedMotor));
  Serial.println(F(")"));
  printPose();
}

void resetPose() {
  currentM1 = 90;
  currentM2 = SAFE_M2_ANGLE;
  currentM3 = 180;
  currentM4 = 180;
  currentM5 = 90;
  currentM6 = 10;

  lastDirectionM1 = 0;
  lastDirectionM2 = 0;
  lastDirectionM3 = 0;
  lastDirectionM4 = 0;
  lastDirectionM5 = 0;
  lastDirectionM6 = 0;

  applyPose();
  Serial.println();
  Serial.println(F("Pose base enviada con Servo.write()."));
  printPose();
}

void moveSelectedRelative(int delta) {
  int previousAngle = angleForMotor(selectedMotor);
  int targetAngle = previousAngle + delta;
  int direction = directionForDelta(delta);
  int previousDirection = lastDirectionForMotor(selectedMotor);
  bool reversed = direction != 0 && previousDirection != 0 && direction != previousDirection;

  setAngleForMotor(selectedMotor, targetAngle);
  applyPose();

  if (direction != 0) {
    setLastDirectionForMotor(selectedMotor, direction);
  }

  printMovementLog("relative", selectedMotor, previousAngle, targetAngle, delta, reversed);
  printPose();
}

void moveSelectedAbsolute(int targetAngle) {
  int previousAngle = angleForMotor(selectedMotor);
  int delta = targetAngle - previousAngle;
  int direction = directionForDelta(delta);
  int previousDirection = lastDirectionForMotor(selectedMotor);
  bool reversed = direction != 0 && previousDirection != 0 && direction != previousDirection;

  setAngleForMotor(selectedMotor, targetAngle);
  applyPose();

  if (direction != 0) {
    setLastDirectionForMotor(selectedMotor, direction);
  }

  printMovementLog("absolute", selectedMotor, previousAngle, targetAngle, delta, reversed);
  printPose();
}

void printNote(const String& text) {
  Serial.println();
  Serial.print(F("NOTE "));
  Serial.println(text);
}

void handleLine(String line) {
  line.trim();
  if (line.length() == 0) {
    return;
  }

  if (line.equalsIgnoreCase("help") || line == "?") {
    printHelp();
    return;
  }

  if (line.equalsIgnoreCase("protocol")) {
    printProtocol();
    return;
  }

  if (line.equalsIgnoreCase("pose")) {
    printPose();
    return;
  }

  if (line.equalsIgnoreCase("reset")) {
    resetPose();
    return;
  }

  if (line.equalsIgnoreCase("m1") || line == "1") {
    selectMotor(1);
    return;
  }

  if (line.equalsIgnoreCase("m2") || line == "2") {
    selectMotor(2);
    return;
  }

  if (line.equalsIgnoreCase("m3") || line == "3") {
    selectMotor(3);
    return;
  }

  if (line.equalsIgnoreCase("m4") || line == "4") {
    selectMotor(4);
    return;
  }

  if (line.equalsIgnoreCase("m5") || line == "5") {
    selectMotor(5);
    return;
  }

  if (line.equalsIgnoreCase("m6") || line == "6") {
    selectMotor(6);
    return;
  }

  if (line.startsWith("step ")) {
    long parsedValue = 0;
    String rawValue = line.substring(5);
    rawValue.trim();

    if (!tryParseLong(rawValue, parsedValue) || parsedValue <= 0) {
      Serial.println(F("Valor de step no valido."));
      return;
    }

    angleStep = (int)parsedValue;
    Serial.print(F("Nuevo step="));
    Serial.println(angleStep);
    return;
  }

  if (line.startsWith("go ")) {
    long parsedValue = 0;
    String rawValue = line.substring(3);
    rawValue.trim();

    if (!tryParseLong(rawValue, parsedValue)) {
      Serial.println(F("Angulo absoluto no valido."));
      return;
    }

    moveSelectedAbsolute((int)parsedValue);
    return;
  }

  if (line.startsWith("note ")) {
    String text = line.substring(5);
    text.trim();
    printNote(text);
    return;
  }

  if (line == "+") {
    moveSelectedRelative(angleStep);
    return;
  }

  if (line == "-") {
    moveSelectedRelative(-angleStep);
    return;
  }

  if (line[0] == '+' || line[0] == '-') {
    long parsedValue = 0;

    if (!tryParseLong(line, parsedValue) || parsedValue == 0) {
      Serial.println(F("Incremento relativo no valido."));
      return;
    }

    moveSelectedRelative((int)parsedValue);
    return;
  }

  {
    long parsedValue = 0;

    if (tryParseLong(line, parsedValue)) {
      moveSelectedAbsolute((int)parsedValue);
      return;
    }
  }

  Serial.print(F("Comando no reconocido: "));
  Serial.println(line);
  printHelp();
}

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  Serial.setTimeout(50);
  attachServos();
  delay(1000);

  Serial.println(F("Medicion real del Braccio con Servo.h directo."));
  Serial.println(F("Este sketch evita Braccio.ServoMovement y sus limites por articulacion."));
  Serial.println(F("Configura el monitor serie a 9600 baudios."));
  printHelp();
  printProtocol();
  resetPose();
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String line = Serial.readStringUntil('\n');
  handleLine(line);
}
