"""Tests del traductor del coche (digital_twin/translators.py): codificación de
instrucciones, constantes de calibración y rechazo de instrucciones inválidas.

Vocabulario del coche: A = avanzar, R = retroceder, I = girar a la izquierda,
D = girar a la derecha.

Ejecutar desde la raíz del repositorio:
    python -m unittest Simulador/simulator/digital_twin/tests/test_coche.py
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


class TestCocheInstruccionesValidas(unittest.TestCase):
    """Instrucciones legibles del coche -> trama compacta correcta."""

    def setUp(self):
        self.traductor = translators.CarTranslator()

    def test_control_take_and_release(self):
        self.assertEqual(self.traductor.encode("C O"), "0,1")
        self.assertEqual(self.traductor.encode("C F"), "0,0")

    def test_forward_in_changes_and_distance(self):
        # A <C|D> <valor> -> 1,0,<0=cambios|1=distancia>,<valor>
        self.assertEqual(self.traductor.encode("A C 50"), "1,0,0,50")
        self.assertEqual(self.traductor.encode("A D 190"), "1,0,1,190")

    def test_backward_in_changes_and_distance(self):
        # R <C|D> <valor> -> 1,1,<0=cambios|1=distancia>,<valor>
        self.assertEqual(self.traductor.encode("R C 50"), "1,1,0,50")
        self.assertEqual(self.traductor.encode("R D 190"), "1,1,1,190")

    def test_forward_with_decimal_distance(self):
        self.assertEqual(self.traductor.encode("A D 12.5"), "1,0,1,12.5")
        self.assertEqual(self.traductor.encode("A D 5.0"), "1,0,1,5")

    def test_turn_left_in_changes_and_degrees(self):
        # I <C|G> <valor> -> 2,0,<0=cambios|1=grados>,<valor>
        self.assertEqual(self.traductor.encode("I C 32"), "2,0,0,32")
        self.assertEqual(self.traductor.encode("I G 90"), "2,0,1,90")

    def test_turn_right_in_changes_and_degrees(self):
        # D <C|G> <valor> (3 tokens) -> 2,1,<0=cambios|1=grados>,<valor>
        self.assertEqual(self.traductor.encode("D C 32"), "2,1,0,32")
        self.assertEqual(self.traductor.encode("D G 90"), "2,1,1,90")

    def test_continuous_move_not_accepted_from_console(self):
        # El movimiento continuo y el STOP ya no son instrucciones de consola
        # (el control en vivo se hace con las teclas WASD).
        for texto in ("J A", "J R", "J I", "J D", "J P", "STOP", "stop"):
            with self.assertRaises(translators.TranslationError):
                self.traductor.encode(texto)

    def test_case_and_space_insensitive(self):
        self.assertEqual(self.traductor.encode("  a c 10 "), "1,0,0,10")
        self.assertEqual(self.traductor.encode("d g 45"), "2,1,1,45")


class TestCocheCalibracion(unittest.TestCase):
    """Constantes de calibración del coche."""

    def test_constants(self):
        self.assertAlmostEqual(
            translators.CarTranslator.MM_POR_CAMBIO_COCHE, 3.8, places=4)
        # Escala del circuito: 1 píxel = 0.38 mm reales.
        self.assertAlmostEqual(
            translators.CarTranslator.MM_POR_PX_COCHE, 0.38, places=4)
        # Píxeles por milímetro = inverso de la escala (1 / 0.38 ~ 2.63 px/mm).
        self.assertAlmostEqual(
            translators.CarTranslator.PX_POR_MM_COCHE,
            1.0 / translators.CarTranslator.MM_POR_PX_COCHE, places=6)
        # Píxeles por cambio es una constante derivada (milímetros/cambio * píxeles/milímetro).
        self.assertAlmostEqual(
            translators.CarTranslator.PX_POR_CAMBIO_COCHE,
            translators.CarTranslator.MM_POR_CAMBIO_COCHE
            * translators.CarTranslator.PX_POR_MM_COCHE, places=6)
        # Factor del giro = factor medido: 32 cambios = 90° (= 2.8125 grados/cambio).
        self.assertAlmostEqual(
            translators.CarTranslator.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE,
            90.0 / 32.0, places=6)
        self.assertAlmostEqual(
            translators.CarTranslator.FACTOR_CONVERSION_GRADOS_SIM_POR_CAMBIO_COCHE,
            2.8125, places=4)


class TestCocheInstruccionesInvalidas(unittest.TestCase):
    """Instrucciones del coche inválidas -> TranslationError."""

    def setUp(self):
        self.traductor = translators.CarTranslator()

    def _assert_error(self, texto):
        with self.assertRaises(translators.TranslationError):
            self.traductor.encode(texto)

    def test_empty_and_unknown(self):
        self._assert_error("")
        self._assert_error("   ")
        self._assert_error("Z 1 2 3")
        self._assert_error("L M")  # el límite es del actuador, no del coche
        self._assert_error("M A C 50")  # 'M'/'T' ya no son cabeceras (ahora A/R/I/D)
        self._assert_error("T I G 90")

    def test_forward_bad(self):
        self._assert_error("A X 3")    # modo inválido (no es C ni D)
        self._assert_error("A C")      # falta el valor
        self._assert_error("A C 0")    # valor no positivo
        self._assert_error("A C abc")  # valor no numérico
        self._assert_error("A C 1 2")  # sobran tokens

    def test_backward_bad(self):
        self._assert_error("R G 3")    # modo inválido (R usa C/D, no G)
        self._assert_error("R D")      # falta el valor

    def test_turn_left_bad(self):
        self._assert_error("I X 3")    # modo inválido (no es C ni G)
        self._assert_error("I G")      # falta el valor
        self._assert_error("I D 3")    # modo inválido (I usa C/G, no D)

    def test_turn_right_bad(self):
        self._assert_error("D X 3")        # modo inválido (no es C ni G)
        self._assert_error("D G")          # falta el valor
        self._assert_error("D C 0")        # valor no positivo
        self._assert_error("D M A S O 2")  # 'detectar' ya no existe: sobran tokens para el giro


if __name__ == "__main__":
    unittest.main(verbosity=2)
