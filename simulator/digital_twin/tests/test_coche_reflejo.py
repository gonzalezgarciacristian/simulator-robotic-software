"""Tests del lazo cerrado del coche (digital_twin/translators.py): apply_to_sim
refleja en el dibujo el feedback recibido del robot físico (movimiento y giro).

Ejecutar desde la raíz del repositorio:
    python -m unittest Simulador/simulator/digital_twin/tests/test_coche_reflejo.py
"""

import os
import sys
import unittest

# El módulo a probar vive en el simulador; lo hacemos importable subiendo tres
# niveles: tests -> digital_twin -> simulator.
_DIRECTORIO_SIMULADOR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _DIRECTORIO_SIMULADOR not in sys.path:
    sys.path.insert(0, _DIRECTORIO_SIMULADOR)

import digital_twin.translators as translators  # noqa: E402


class DibujoFalso:
    """Captura cuánto se ha movido/girado el dibujo (sin canvas real)."""

    def __init__(self):
        self.movido = 0.0
        self.girado = 0.0

    def move(self, velocidad):
        self.movido += velocidad

    def change_angle(self, delta_angulo):
        self.girado += delta_angulo


class CapaFalsa:
    """Capa de simulación falsa que imita a MobileRobotLayer sin canvas real."""

    def __init__(self):
        self.robot_drawing = DibujoFalso()
        self.twin_external = False

    def apply_twin_move(self, velocidad, delta_angulo):
        # Imita a MobileRobotLayer.apply_twin_move sin colisión (no hay mundo en el test).
        if velocidad != 0:
            self.robot_drawing.move(velocidad)
        if delta_angulo != 0:
            self.robot_drawing.change_angle(delta_angulo)


def create_continuous_move_layer(velocidad=0, delta_angulo=0):
    """Crea una capa falsa con la intención de movimiento en vivo ya fijada."""
    capa = CapaFalsa()
    capa.last_v = velocidad
    capa.last_da = delta_angulo
    return capa


class TestCocheReflejo(unittest.TestCase):
    """apply_to_sim refleja el feedback en el dibujo (lazo cerrado)."""

    def setUp(self):
        self.traductor = translators.CarTranslator()
        self.capa = CapaFalsa()

    def test_repeated_measured_orders_move_each_time(self):
        # Bug: dos 'I C 32' seguidas dan el mismo reporte (5,32,32); sin reiniciar la base
        # el segundo incremento sería 0 y el simulador no giraría. Cada orden debe reiniciar
        # la base.
        grados = (32
                  * translators.CarTranslator.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE)
        self.traductor.encode("I C 32")
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,32,32"))
        self.assertAlmostEqual(self.capa.robot_drawing.girado, grados)  # 1ª: +90°
        self.traductor.encode("I C 32")
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,32,32"))
        self.assertAlmostEqual(self.capa.robot_drawing.girado, 2 * grados)  # 2ª: +90° más

    def test_left_and_right_turn_opposite_signs(self):
        self.traductor.encode("I C 32")
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,32,32"))
        izquierda = self.capa.robot_drawing.girado
        self.traductor.encode("D C 32")
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,32,32"))
        # La derecha resta lo que la izquierda sumó (mismo módulo, signo opuesto).
        self.assertAlmostEqual(self.capa.robot_drawing.girado, 0.0)
        self.assertGreater(izquierda, 0.0)

    def test_autonomous_reflects_without_prior_order(self):
        # En autónomo el simulador NO ha emitido ninguna orden (_last_motion arranca en None):
        # el sentido lo trae cada trama en el 4º campo. Un lado (A) avanza; una esquina (D) gira.
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,50,50,0"))  # avanzar (A)
        pixeles = 50 * translators.CarTranslator.PX_POR_CAMBIO_COCHE
        self.assertAlmostEqual(self.capa.robot_drawing.movido, -pixeles)  # A -> píxeles negativos
        self.assertAlmostEqual(self.capa.robot_drawing.girado, 0.0)
        # Nuevo segmento: el microcontrolador reinicia contadores -> la trama baja a valores
        # pequeños.
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,32,32,3"))  # derecha (D)
        grados = (32
                  * translators.CarTranslator.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE)
        self.assertAlmostEqual(self.capa.robot_drawing.girado, -grados)  # D -> grados negativos

    def test_continuous_move_accumulates_growing(self):
        # En movimiento continuo el microcontrolador NO reinicia entre tramas (idempotente):
        # el reporte crece y el simulador aplica solo el incremento de cada trama.
        self.traductor.drive_from_sim(create_continuous_move_layer(delta_angulo=5))  # fija 'I'
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,10,10"))
        self.traductor.apply_to_sim(self.capa, self.traductor.decode("5,20,20"))
        grados = (20
                  * translators.CarTranslator.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE)
        self.assertAlmostEqual(self.capa.robot_drawing.girado, grados)


if __name__ == "__main__":
    unittest.main(verbosity=2)
