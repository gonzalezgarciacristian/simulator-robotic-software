"""Jerarquía de traductores del gemelo digital (Template Method + Strategy).

Cada robot enlazable al gemelo digital tiene su propio vocabulario LEGIBLE (lo que el
usuario escribe en la consola) y su forma COMPACTA numérica (lo que se publica por MQTT,
barata de parsear en el micro). Este módulo unifica esa traducción en una jerarquía:

    TwinTranslator (base, Template Method)
      ├── ActuatorTranslator   -> actuador lineal (servo + finales de carrera)
      └── CarTranslator        -> coche (2 servos + 2 opto-encoders)

El controlador selecciona la estrategia concreta en ``change_robot`` y delega en ella
(``encode`` / ``decode`` / ``drive_from_sim`` / ``apply_to_sim`` / anclaje), sin comprobar
el tipo del layer en cada método.

Convenio compacto compartido:
    Control:  0,<0|1>          0=off (C F)  ·  1=on (C O)
    Jog:      3,<dir>          mover continuo (control en vivo) hasta parar
    Parar:    4
    Feedback: 5,...            reporte físico -> simulador (lo decodifica ``decode``)
"""

import collections


class TranslationError(ValueError):
    """Instrucción legible inválida. El mensaje es apto para mostrar en consola."""
    pass


class TwinTranslator:
    """Base de la jerarquía (Template Method).

    ``encode`` es la plantilla: tokeniza el texto, valida la cabecera, despacha al hook
    del comando concreto y devuelve la trama compacta. El control ``C O``/``C F`` y el
    parseo de valores numéricos son comunes a todos los robots y viven aquí.

    Las subclases definen su vocabulario en ``_command_encoders`` (mapa cabecera -> método)
    y, si procede, sobreescriben ``decode``/``drive_from_sim``/``apply_to_sim`` y los
    enganches de anclaje (``attach``/``detach``/``on_control_activated``).
    """

    # ---- plantilla de codificación (legible -> compacto) ----
    def encode(self, text):
        tokens = (text or "").strip().split()
        if not tokens:
            raise TranslationError("instrucción vacía")
        head = tokens[0].upper()
        if head == "C":
            return self._encode_control(tokens)
        handler = self._command_encoders().get(head)
        if handler is None:
            raise TranslationError("comando desconocido: " + tokens[0])
        return handler(tokens)

    def _command_encoders(self):
        """Mapa cabecera (mayúsculas) -> método que recibe los tokens. Lo define cada
        subclase con su vocabulario propio."""
        raise NotImplementedError

    # ---- helpers compartidos ----
    def _encode_control(self, tokens):
        """``C O`` toma el control (0,1) · ``C F`` lo suelta (0,0)."""
        if len(tokens) != 2 or tokens[1].upper() not in ("O", "F"):
            raise TranslationError("uso: 'C O' o 'C F'")
        return "0,1" if tokens[1].upper() == "O" else "0,0"

    def control_on(self):
        """Trama compacta que toma el control en vivo del dispositivo físico
        (igual que la instrucción legible ``C O``). Común a todos los robots."""
        return "0,1"

    def control_off(self):
        """Trama compacta que suelta el control del dispositivo físico (igual que
        la instrucción legible ``C F``). Común a todos los robots: se envía al
        desconectar para que el dispositivo vuelva a su modo autónomo en vez de
        quedarse congelado esperando órdenes."""
        return "0,0"

    @staticmethod
    def _parse_value(raw, as_float):
        """Valida y normaliza un valor numérico positivo. ``as_float`` decide si se
        admite decimal (distancia/grados) o solo entero (cambios)."""
        try:
            valor = float(raw) if as_float else int(raw)
        except ValueError:
            raise TranslationError("valor numérico inválido: " + raw)
        if valor <= 0:
            raise TranslationError("el valor debe ser mayor que 0")
        # Evita decimales innecesarios en la trama compacta (5.0 -> "5").
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)

    # ---- lazo cerrado (robot -> simulador) ----
    def decode(self, text):
        """Decodifica un reporte físico a una namedtuple de feedback, o ``None`` si el
        texto no es un reporte válido para este robot."""
        return None

    def apply_to_sim(self, layer, feedback):
        """Refleja en el canvas el estado físico ya decodificado."""
        pass

    # ---- control en vivo (simulador -> robot) ----
    def drive_from_sim(self, layer):
        """Devuelve la trama de jog (``3,<dir>`` / ``4``) según la intención de
        movimiento del layer, o ``None`` si este robot no conduce en vivo."""
        return None

    # ---- enganches de anclaje (modo pasivo / control) ----
    def attach(self, layer):
        """Al conectar el gemelo: el layer empieza a reflejar la pose física (modo
        pasivo). Por defecto suprime el movimiento local."""
        if layer is not None and hasattr(layer, "twin_external"):
            layer.twin_external = True

    def detach(self, layer):
        """Al desconectar el gemelo: el layer recupera el control local."""
        if layer is not None and hasattr(layer, "twin_external"):
            layer.twin_external = False

    def on_control_activated(self, layer):
        """Al ceder el control con ``C O``: anclaje específico del robot (si lo hay)."""
        pass


# Reporte de vuelta del actuador físico al simulador.
#   pos        = posición absoluta en cambios desde el extremo motor (0..140).
#   lim_motor  = final de carrera del motor pulsado (True/False), o None si no se reporta.
#   lim_sensor = final de carrera del sensor pulsado (True/False), o None si no se reporta.
ActuatorFeedback = collections.namedtuple(
    "ActuatorFeedback", ["pos", "lim_motor", "lim_sensor"])


class ActuatorTranslator(TwinTranslator):
    """Traductor del actuador lineal (migrado de ``protocol.py``).

    Formato legible:
        C O | C F                 -> control on / off
        M <M|S> <C|D> <valor>     -> movimiento medido (Motor/Sensor, Cambios/Distancia mm)
        L <M|S>                   -> mover hasta el límite Motor / Sensor
        J <M|S>                   -> jog: mover continuo hacia Motor / Sensor (control vivo)
        J P  (o STOP)             -> parar el jog
    """

    # Calibración píxeles(simulador) <-> cambios(físico). El bloque del simulador recorre
    # de x=508 a x=1912 (una pasada completa) = 140 cambios = 240 mm a 1.71 mm/cambio.
    # Único punto de verdad para que el recorrido del simulador equivalga al del robot real.
    PIXELES_POR_PASADA = 1912 - 508   # recorrido del bloque del simulador (px)
    CAMBIOS_POR_PASADA = 140          # cambios del opto interruptor en una pasada física
    MM_POR_CAMBIO = 1.71              # calibración del actuador físico
    PX_POR_CAMBIO = PIXELES_POR_PASADA / CAMBIOS_POR_PASADA            # ~10.03 px/cambio
    PX_POR_MM = PIXELES_POR_PASADA / (CAMBIOS_POR_PASADA * MM_POR_CAMBIO)  # ~5.86 px/mm

    _DIR = {"M": 0, "S": 1}   # lado del actuador: Motor / Sensor
    _MODO = {"C": 0, "D": 1}  # interpretación del valor: Cambios / Distancia (mm)

    def _command_encoders(self):
        return {
            "L": self._encode_limit,
            "STOP": self._encode_stop,
            "J": self._encode_jog,
            "M": self._encode_movement,
        }

    def _encode_limit(self, tokens):
        if len(tokens) != 2 or tokens[1].upper() not in self._DIR:
            raise TranslationError("uso: 'L M' o 'L S'")
        return "2,{}".format(self._DIR[tokens[1].upper()])

    def _encode_stop(self, tokens):
        if len(tokens) != 1:
            raise TranslationError("uso: 'STOP'")
        return "4"

    def _encode_jog(self, tokens):
        if len(tokens) != 2:
            raise TranslationError("uso: 'J M' | 'J S' | 'J P'")
        arg = tokens[1].upper()
        if arg == "P":
            return "4"
        if arg not in self._DIR:
            raise TranslationError("uso: 'J M' | 'J S' | 'J P'")
        return "3,{}".format(self._DIR[arg])

    def _encode_movement(self, tokens):
        if len(tokens) != 4:
            raise TranslationError("uso: 'M <M|S> <C|D> <valor>'")
        direccion = tokens[1].upper()
        modo = tokens[2].upper()
        if direccion not in self._DIR:
            raise TranslationError("dirección debe ser M (motor) o S (sensor)")
        if modo not in self._MODO:
            raise TranslationError("modo debe ser C (cambios) o D (distancia)")
        valor = self._parse_value(tokens[3], as_float=(modo == "D"))
        return "1,{},{},{}".format(self._DIR[direccion], self._MODO[modo], valor)

    # ---- lazo cerrado ----
    def decode(self, text):
        """Decodifica un reporte del actuador físico (robot -> simulador).

        Formatos aceptados:
            ``5,<pos>``                        solo posición (lim_* = None)
            ``5,<pos>,<limMotor>,<limSensor>`` posición + estado de los finales (1=pulsado)
        """
        parts = [p.strip() for p in (text or "").strip().split(",")]
        if len(parts) not in (2, 4) or parts[0] != "5":
            return None
        try:
            pos = int(parts[1])
        except ValueError:
            return None
        lim_motor = lim_sensor = None
        if len(parts) == 4:
            try:
                lim_motor = int(parts[2]) != 0
                lim_sensor = int(parts[3]) != 0
            except ValueError:
                return None
        return ActuatorFeedback(pos, lim_motor, lim_sensor)

    def apply_to_sim(self, layer, feedback):
        """Refleja en AL1 la pose real reportada por ALF (lazo cerrado): posición del
        bloque y estado de los finales de carrera.

        pos = cambios desde el extremo motor (0 = motor/derecha, 140 = sensor/izquierda).
        x = 1912 - pos * PX_POR_CAMBIO, saturado al recorrido del bloque [508, 1912].
        Los finales SOLO salen del estado físico reportado; nunca se infieren de la posición.
        """
        x = int(round(1912 - feedback.pos * self.PX_POR_CAMBIO))
        x = max(508, min(1912, x))
        drawing = layer.robot_drawing
        drawing.block.x = x
        drawing.drawing.move_image("block", drawing.block.x, drawing.block.y)
        if feedback.lim_motor is not None:
            layer.set_physical_limits(feedback.lim_motor, feedback.lim_sensor)

    # ---- control en vivo ----
    def drive_from_sim(self, layer):
        """Traduce la velocidad del bloque del simulador a jog continuo:
        v>0 (derecha -> motor) -> 3,0 · v<0 (izquierda -> sensor) -> 3,1 · quieto -> 4."""
        v = getattr(layer, "last_v", 0)
        if v > 0:
            return "3,0"
        if v < 0:
            return "3,1"
        return "4"

    def on_control_activated(self, layer):
        """Bajo control, la posición del bloque la dicta ALF (mensajes ``5,<pos>``): se
        ancla el bloque al extremo motor (derecha) para compartir referencia con el homing."""
        layer.twin_external = True
        drawing = layer.robot_drawing
        drawing.block.x = 1912  # extremo motor en el simulador (der)
        drawing.drawing.move_image("block", drawing.block.x, drawing.block.y)


# Reporte de vuelta del coche físico al simulador: cambios acumulados de cada opto-encoder
# desde el inicio del comando en curso (se reinician en el micro al recibir uno nuevo).
#   motion = tipo de movimiento del reporte ('A'/'R'/'I'/'D'), o None si no viene en la trama.
#            Lo incluye el coche en MODO AUTÓNOMO (trama de 4 campos), donde el sim no ha dado
#            ninguna orden y por tanto no sabría si las cuentas son avance o giro. En modo
#            control la trama tiene 3 campos y el sim usa el sentido de su última orden.
CarFeedback = collections.namedtuple(
    "CarFeedback", ["cambios_der", "cambios_izq", "motion"])
CarFeedback.__new__.__defaults__ = (None,)

# Reporte de sensores del coche físico al simulador (lazo abierto, modo pasivo):
#   ir      = tupla de 0/1 de los IR de línea en orden físico izquierda->derecha
#             (1 = oscuro / sobre la línea, 0 = blanco).
#   dist_cm = distancia del ultrasonido en cm, o None si no hay eco (fuera de alcance).
CarSensorFeedback = collections.namedtuple("CarSensorFeedback", ["ir", "dist_cm"])


class CarTranslator(TwinTranslator):
    """Traductor del coche (mobile2/3/4): 2 servos de rueda + 2 opto-encoders.

    Formato legible (consola). Cada sentido es su propia instrucción:
        C O | C F                              -> control on / off
        A <C|D> <valor>                        -> Avanzar, Cambios o Distancia(mm)   -> 1,0,..
        R <C|D> <valor>                        -> Retroceder, Cambios o Distancia(mm)-> 1,1,..
        I <C|G> <valor>                        -> girar Izquierda, Cambios o Grados  -> 2,0,..
        D <C|G> <valor>                        -> girar Derecha, Cambios o Grados    -> 2,1,..

    El jog (control en vivo) NO se expone por consola: se conduce con WASD y sus tramas
    (3,<dir> / 4) las genera ``drive_from_sim``, no ``encode``.
    """

    # ---- calibración ----
    MM_POR_CAMBIO_COCHE = 3.8        # 190 mm / 50 cambios (calibración física)

    # Escala píxel <-> realidad: 1 px = 0.38 mm, la MISMA escala del circuito laberinto
    # (cinta 4 cm = 100 px y largo 119 cm ~ 3300 px -> ~0.38 mm/px). El coche se mueve
    # SOBRE el circuito, así que comparte su escala para que el avance del reflejo cuadre
    # con la pista.
    MM_POR_PX_COCHE = 0.38          # 1 píxel del circuito = 0.38 mm reales
    PX_POR_MM_COCHE = 1.0 / MM_POR_PX_COCHE                       # ~2.63 px/mm
    PX_POR_CAMBIO_COCHE = MM_POR_CAMBIO_COCHE * PX_POR_MM_COCHE   # derivada (px por cambio) = 10.0

    #El estudio realizado muestra que 32 cambios detectados son 90º de giro del coche
    FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE = 90.0/32

    _MOV_MODO = {"C": 0, "D": 1}           # cambios / distancia (mm)
    _TURN_MODO = {"C": 0, "G": 1}          # cambios / grados
    # Código de movimiento del feedback autónomo (4º campo de '5,...'): mismo orden que el jog.
    _MOTION_BY_CODE = {0: "A", 1: "R", 2: "I", 3: "D"}

    def __init__(self):
        # Estado para reflejar el lazo cerrado de forma incremental.
        self._last_motion = None   # 'A'/'R'/'I'/'D': sentido del último comando/jog emitido
        self._prev_der = 0         # último cambiosDer reportado (para calcular el delta)
        self._prev_izq = 0

    def _begin_command(self, sentido):
        """Una orden medida (A/R/I/D) reinicia los contadores del micro a 0, así que el sim
        alinea su base a 0. Si no, dos órdenes iguales seguidas (p. ej. 'I C 32' dos veces)
        darían el MISMO reporte final (5,32,32) y el delta saldría 0 -> el sim no se movería
        en la segunda. Reiniciar la base aquí hace que cada orden se mida desde 0."""
        self._last_motion = sentido
        self._prev_der = 0
        self._prev_izq = 0

    def _command_encoders(self):
        # Cada sentido es su propia cabecera. El jog/STOP no se exponen aquí (control en
        # vivo por WASD).
        return {
            "A": self._encode_forward,
            "R": self._encode_backward,
            "I": self._encode_left,
            "D": self._encode_right,
        }

    def _encode_linear_move(self, tokens, dir_code, sentido, cabecera):
        # A/R <C|D> <valor> -> 1,<0=A|1=R>,<0=C|1=D>,<valor>
        if len(tokens) != 3:
            raise TranslationError("uso: '" + cabecera + " <C|D> <valor>'")
        modo = tokens[1].upper()
        if modo not in self._MOV_MODO:
            raise TranslationError("modo debe ser C (cambios) o D (distancia)")
        valor = self._parse_value(tokens[2], as_float=(modo == "D"))
        self._begin_command(sentido)
        return "1,{},{},{}".format(dir_code, self._MOV_MODO[modo], valor)

    def _encode_forward(self, tokens):
        return self._encode_linear_move(tokens, 0, "A", "A")

    def _encode_backward(self, tokens):
        return self._encode_linear_move(tokens, 1, "R", "R")

    def _encode_turn(self, tokens, dir_code, sentido, cabecera):
        # I/D <C|G> <valor> -> 2,<0=I|1=D>,<0=C|1=G>,<valor>
        if len(tokens) != 3:
            raise TranslationError("uso: '" + cabecera + " <C|G> <valor>'")
        modo = tokens[1].upper()
        if modo not in self._TURN_MODO:
            raise TranslationError("modo debe ser C (cambios) o G (grados)")
        valor = self._parse_value(tokens[2], as_float=(modo == "G"))
        self._begin_command(sentido)
        return "2,{},{},{}".format(dir_code, self._TURN_MODO[modo], valor)

    def _encode_left(self, tokens):
        return self._encode_turn(tokens, 0, "I", "I")

    def _encode_right(self, tokens):
        return self._encode_turn(tokens, 1, "D", "D")

    # ---- lazo cerrado ----
    def decode(self, text):
        """Decodifica un reporte del coche físico. Tramas posibles:
            ``5,<cambiosDer>,<cambiosIzq>``          -> pose en control (CarFeedback)
            ``5,<cambiosDer>,<cambiosIzq>,<motion>`` -> pose autónoma (motion 0=A,1=R,2=I,3=D)
            ``7,<ir0>,<ir1>,...,<distCm>``           -> sensores (CarSensorFeedback)
        """
        parts = [p.strip() for p in (text or "").strip().split(",")]
        if not parts:
            return None
        if parts[0] == "5":
            # 3 campos: pose en modo control (el sim conoce el sentido por su orden).
            # 4 campos: pose en modo autónomo (el coche añade el tipo de movimiento).
            try:
                if len(parts) == 3:
                    return CarFeedback(int(parts[1]), int(parts[2]))
                if len(parts) == 4:
                    motion = self._MOTION_BY_CODE.get(int(parts[3]))
                    if motion is None:
                        return None
                    return CarFeedback(int(parts[1]), int(parts[2]), motion)
            except ValueError:
                return None
            return None
        if parts[0] == "7":
            # Cabecera + N bits IR + último campo distancia. Generaliza a cualquier nº de IR.
            if len(parts) < 3:
                return None
            try:
                ir = tuple(1 if int(b) != 0 else 0 for b in parts[1:-1])
                dist = float(parts[-1])
            except ValueError:
                return None
            if not ir:
                return None
            return CarSensorFeedback(ir, dist if dist >= 0 else None)
        return None

    def apply_to_sim(self, layer, feedback):
        """Despacha según el tipo de feedback: sensores -> reflejo directo; pose -> avance."""
        if isinstance(feedback, CarSensorFeedback):
            layer.apply_twin_sensors(feedback.ir, feedback.dist_cm)
            return
        self._apply_pose(layer, feedback)

    def _apply_pose(self, layer, feedback):
        """Refleja la pose del coche a partir de los cambios reportados por los encoders.

        El micro reinicia los contadores al empezar cada comando, así que se trabaja con el
        INCREMENTO desde el último reporte. El sentido del movimiento (``_last_motion``) decide
        si el incremento es avance (px) o giro (grados):
            A/R -> avance:  px = delta * PX_POR_CAMBIO_COCHE   (escala del circuito: 0.38 mm/px)
            I/D -> giro:    deg = delta * FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE
                            (32 cambios = 90°, medido)

        En modo control ese sentido viene del último comando/jog emitido por el sim. En modo
        autónomo el coche lo manda en el 4º campo (``feedback.motion``): el coche cambia de
        segmento (lado<->giro) sin que el sim ordene nada, así que cada trama trae su sentido.
        """
        if feedback.motion is not None:
            self._last_motion = feedback.motion
        der = feedback.cambios_der
        izq = feedback.cambios_izq
        # Reinicio del micro (nuevo comando): el contador baja -> se rebasa la base a 0.
        d_der = der - self._prev_der if der >= self._prev_der else der
        d_izq = izq - self._prev_izq if izq >= self._prev_izq else izq
        self._prev_der = der
        self._prev_izq = izq
        delta = (d_der + d_izq) / 2.0
        if delta <= 0 or self._last_motion is None:
            return
        # El reflejo pasa por el layer (no por el dibujo directo) para respetar bordes y
        # obstáculos: el coche del sim no los atraviesa aunque el coche real siga.
        if self._last_motion in ("A", "R"):
            px = delta * self.PX_POR_CAMBIO_COCHE
            # WASD: 'w' (adelante) da v negativo; 'A'vanzar -> px negativo.
            layer.apply_twin_move(-px if self._last_motion == "A" else px, 0)
        else:  # 'I' / 'D' -> giro
            deg = delta * self.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE
            # 'a' (izquierda) da da positivo; Izquierda -> grados positivos.
            layer.apply_twin_move(0, deg if self._last_motion == "I" else -deg)

    # ---- control en vivo ----
    def drive_from_sim(self, layer):
        """Mapea la intención de movimiento del layer (teclas/código) a jog continuo:
            v<0 (adelante) -> 3,0 · v>0 (atrás) -> 3,1
            da>0 (izq)     -> 3,2 · da<0 (der)  -> 3,3 · quieto -> 4
        El avance tiene prioridad sobre el giro (no se combinan en una sola trama)."""
        v = getattr(layer, "last_v", 0)
        da = getattr(layer, "last_da", 0)
        if v < 0:
            self._last_motion = "A"
            return "3,0"
        if v > 0:
            self._last_motion = "R"
            return "3,1"
        if da > 0:
            self._last_motion = "I"
            return "3,2"
        if da < 0:
            self._last_motion = "D"
            return "3,3"
        return "4"

    def attach(self, layer):
        super().attach(layer)
        self._reset_baseline()

    def on_control_activated(self, layer):
        layer.twin_external = True
        self._reset_baseline()

    def _reset_baseline(self):
        self._prev_der = 0
        self._prev_izq = 0
        self._last_motion = None
