"""
Librería Braccio para el simulador S4R.
Simula la librería Arduino TinkerKit Braccio.

Pines del Braccio:
    base         → pin 11
    shoulder     → pin 10
    elbow        → pin 9
    wrist_ver    → pin 6
    wrist_rot    → pin 5
    gripper      → pin 3

Uso en sketch Arduino (simulador):
    #include <Braccio.h>

    void setup(){
      Braccio.begin();
    }

    void loop(){
      Braccio.ServoMovement(20, 90, 45, 180, 180, 90, 10);
    }
"""

import time
import threading

# Pines estándar del Braccio
BRACCIO_PINS = {
    'base': 11,
    'shoulder': 10,
    'elbow': 9,
    'wrist_ver': 6,
    'wrist_rot': 5,
    'gripper': 3,
}

# Orden de los servos en servo_movement
_SERVO_ORDER = ['base', 'shoulder', 'elbow', 'wrist_ver', 'wrist_rot', 'gripper']

_DEFAULT_STEP_POSITIONS = {
    'base': 90,
    'shoulder': 45,
    'elbow': 180,
    'wrist_ver': 180,
    'wrist_rot': 90,
    'gripper': 10,
}

# Límites hardware oficiales en grados de servo.
_JOINT_LIMITS = {
    'base':      (0, 180),
    'shoulder':  (15, 165),
    'elbow':     (0, 180),
    'wrist_ver': (0, 180),
    'wrist_rot': (0, 180),
    'gripper':   (10, 73),
}


def _delay_ms(ms):
    """Aplica un retardo compatible con el runtime Arduino del simulador."""
    try:
        import libraries.standard as _standard
        if getattr(_standard, "state", None) is not None:
            try:
                if threading.current_thread() is threading.main_thread():
                    import graphics.screen_updater as _screen_updater
                    remaining = max(0, int(ms))
                    while remaining > 0:
                        _screen_updater.refresh()
                        chunk = min(remaining, 16)
                        _standard.delay(chunk)
                        remaining -= chunk
                    _screen_updater.refresh()
                else:
                    _standard.delay(ms)
            except _standard.ExecutionInterrupted:
                raise
            return
    except ImportError:
        pass
    time.sleep(ms / 1000.0)


def _get_board_braccio_pins(board):
    arm_robot = getattr(board, "arm_robot", None) if board is not None else None
    if arm_robot is not None and hasattr(arm_robot, "get_named_servo_pins"):
        return arm_robot.get_named_servo_pins(BRACCIO_PINS)
    return dict(BRACCIO_PINS)


def get_name():
    return "Braccio"


def get_methods():
    """
    Retorna los métodos de la librería Braccio como diccionario.
    Formato: ("tipo_retorno", "nombre_python", [tipos_args], -1)
    """
    methods = {}
    methods["begin"] = ("void", "begin", [], -1)
    methods["ServoMovement"] = (
        "int", "servo_movement",
        ['int', 'int', 'int', 'int', 'int', 'int', 'int'],
        -1
    )
    return methods


def get_not_implemented():
    return []


# ---------------------------------------------------------------------------
# Singleton de módulo (patrón idéntico al de serial.py / standard.py)
# El código generado por code_generator.py produce llamadas del tipo
#   import libraries.braccio as Braccio
#   Braccio.begin()
#   Braccio.servo_movement(...)
# Por eso se necesitan estas funciones a nivel de módulo.
# ---------------------------------------------------------------------------

_singleton = None


def _get_singleton():
    """Devuelve la instancia singleton de Braccio, sincronizándola con la placa activa."""
    global _singleton
    import libraries.standard as _std
    if _singleton is None or _singleton.board is not _std.board:
        _singleton = Braccio(_std.board)
    return _singleton


def begin():
    """Inicializa el Braccio y mueve al estado de reposo."""
    return _get_singleton().begin()


def servo_movement(step_delay, v_base, v_shoulder, v_elbow,
                   v_wrist_ver, v_wrist_rot, v_gripper):
    """Mueve los 6 servos del Braccio a las posiciones indicadas."""
    return _get_singleton().servo_movement(
        step_delay, v_base, v_shoulder, v_elbow,
        v_wrist_ver, v_wrist_rot, v_gripper
    )


class Braccio:
    """
    Clase que simula la librería Braccio de Arduino.
    Permite controlar los 6 servomotores del brazo TinkerKit Braccio.
    """

    OK = 1
    ERROR = 0

    def __init__(self, board=None):
        self.board = board
        self._step_positions = None
        self._servos = {}  # pin → elemento servo

    def set_board(self, board):
        """Establece la placa y resuelve los elementos servo por pin."""
        self.board = board
        self._step_positions = None
        self._resolve_servos()

    def _resolve_servos(self):
        """Busca los elementos servo en la placa por sus pines estándar."""
        self._servos = {}
        if self.board is None:
            return
        for name, pin in _get_board_braccio_pins(self.board).items():
            if pin is None:
                continue
            elem = self.board.get_pin_element(pin)
            if elem is None:
                arm_robot = getattr(self.board, "arm_robot", None)
                if arm_robot is not None:
                    elem = arm_robot.attach_servo_to_pin(pin, name)
            if elem is not None:
                self._servos[pin] = elem

    def begin(self):
        """
        Inicializa el Braccio.
        En el simulador, resuelve los servos y mueve al estado de reposo.
        """
        self._resolve_servos()
        # Posición de reposo estándar
        self._step_positions = dict(_DEFAULT_STEP_POSITIONS)
        for name, value in self._step_positions.items():
            self._write_servo(name, value)
        self._refresh_screen_if_main_thread()
        return self.OK

    def servo_movement(self, step_delay, v_base, v_shoulder, v_elbow,
                       v_wrist_ver, v_wrist_rot, v_gripper):
        """
        Mueve todos los servos del Braccio a las posiciones indicadas.

        Args:
            step_delay : retardo entre pasos en ms (10-30 ms en la libreria oficial)
            v_base     : ángulo servo base (0-180°)
            v_shoulder : ángulo servo hombro (15-165°)
            v_elbow    : ángulo servo codo (0-180°)
            v_wrist_ver: ángulo servo muñeca vertical (0-180°)
            v_wrist_rot: ángulo servo muñeca rotación (0-180°)
            v_gripper  : ángulo servo pinza (10-73°)

        Returns:
            OK (1) si la operación fue correcta, ERROR (0) si hubo fallo.
        """
        if not self._servos and self.board is not None:
            self._resolve_servos()

        values = [v_base, v_shoulder, v_elbow, v_wrist_ver, v_wrist_rot, v_gripper]

        # Validar rangos articulares y avisar en consola
        self._validate_values(values)
        step_delay = max(10, min(30, int(step_delay)))
        targets = self._clamp_values(values)
        step_positions = self._get_step_positions()

        while True:
            moved = False
            for name, target in zip(_SERVO_ORDER, targets):
                current = step_positions[name]
                if current == target:
                    continue
                moved = True
                current += 1 if target > current else -1
                step_positions[name] = current
                self._write_servo(name, current)

            if not moved:
                break

            _delay_ms(step_delay)

        self._step_positions = step_positions
        self._refresh_screen_if_main_thread()

        return self.OK

    def _get_step_positions(self):
        """Obtiene la posicion actual de trabajo usada por ServoMovement."""
        if self._step_positions is not None:
            return dict(self._step_positions)

        step_positions = {}
        for name in _SERVO_ORDER:
            pin = self._pin_for(name)
            elem = self._servos.get(pin)
            if elem is not None and hasattr(elem, "value"):
                step_positions[name] = int(elem.value)
            else:
                step_positions[name] = _DEFAULT_STEP_POSITIONS[name]
        return step_positions

    def _clamp_values(self, values):
        """Ajusta los objetivos a los rangos seguros de la libreria oficial."""
        clamped = []
        for name, value in zip(_SERVO_ORDER, values):
            lo, hi = _JOINT_LIMITS[name]
            clamped.append(max(lo, min(hi, int(value))))
        return clamped

    def _write_servo(self, name, value):
        """Escribe un paso de un grado sobre el servo indicado."""
        pin = self._pin_for(name)
        if pin is None:
            return
        elem = self._servos.get(pin)
        if elem is not None:
            elem.set_value(pin, int(value))
        elif self.board is not None:
            self.board.write_value(pin, int(value))

    def _pin_for(self, name):
        return _get_board_braccio_pins(self.board).get(name, BRACCIO_PINS[name])

    def _refresh_screen_if_main_thread(self):
        if threading.current_thread() is not threading.main_thread():
            return
        try:
            import graphics.screen_updater as _screen_updater
            layer = getattr(_screen_updater, "layer", None)
            if hasattr(layer, "snap_to_servo_targets"):
                layer.snap_to_servo_targets()
            _screen_updater.refresh(force=True)
        except Exception:
            pass

    def _validate_values(self, values):
        """Emite advertencias en consola si algún valor está fuera del rango hardware."""
        try:
            import libraries.serial as _serial
            import output.console as _console
            if _serial.cons is None:
                return
            for name, value in zip(_SERVO_ORDER, values):
                lo, hi = _JOINT_LIMITS[name]
                if not (lo <= value <= hi):
                    _serial.cons.write_warning(_console.Warning(
                        "Braccio", 0, 0,
                        f"ServoMovement: {name}={value}° fuera del rango permitido [{lo}°, {hi}°]"
                    ))
        except Exception:
            pass
