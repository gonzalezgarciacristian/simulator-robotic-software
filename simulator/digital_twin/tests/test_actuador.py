"""Tests del traductor del actuador lineal (digital_twin/translators.py).

Comprueba que la forma LEGIBLE que el usuario escribe en la consola del
simulador se traduce a la forma COMPACTA numérica que se publica por MQTT al
Arduino, que el reporte de vuelta del robot se decodifica correctamente y que
las instrucciones inválidas se rechazan con TranslationError (mensaje apto para
mostrar en la consola).

Ejecutar desde la raíz del repositorio:
    python -m unittest Simulador/simulator/digital_twin/tests/test_actuador.py
El propio fichero añade Simulador/simulator al sys.path, así que no necesita el
entorno virtual activo más allá de tener instaladas las dependencias.
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


class TestActuadorInstruccionesValidas(unittest.TestCase):
    """Instrucciones legibles válidas -> trama compacta correcta."""

    def setUp(self):
        self.traductor = translators.ActuatorTranslator()

    def test_control_take_and_release(self):
        # 'C O' toma el control (1), 'C F' lo suelta (0).
        self.assertEqual(self.traductor.encode("C O"), "0,1")
        self.assertEqual(self.traductor.encode("C F"), "0,0")

    def test_case_and_space_insensitive(self):
        # El analizador es insensible a mayúsculas/minúsculas y a espacios sobrantes.
        self.assertEqual(self.traductor.encode("c o"), "0,1")
        self.assertEqual(self.traductor.encode("  l   s  "), "2,1")

    def test_limit_toward_motor_and_sensor(self):
        # Dirección: motor = 0, sensor = 1.
        self.assertEqual(self.traductor.encode("L M"), "2,0")
        self.assertEqual(self.traductor.encode("L S"), "2,1")

    def test_movement_in_changes_mode(self):
        # 'M M C 50' = mover hacia motor (dirección 0), modo cambios (0), valor 50.
        self.assertEqual(self.traductor.encode("M M C 50"), "1,0,0,50")

    def test_movement_in_distance_mode(self):
        # 'M S D 100' = mover hacia sensor (dirección 1), modo distancia (1), 100 milímetros.
        self.assertEqual(self.traductor.encode("M S D 100"), "1,1,1,100")

    def test_integer_distance_without_decimals(self):
        # Un valor flotante entero (5.0) se normaliza a "5" para no inflar la trama.
        self.assertEqual(self.traductor.encode("M S D 5.0"), "1,1,1,5")

    def test_decimal_distance_preserved(self):
        # Un decimal real sí se mantiene (el Arduino lo convierte a cambios).
        self.assertEqual(self.traductor.encode("M M D 12.5"), "1,0,1,12.5")

    def test_continuous_move_toward_motor_and_sensor(self):
        # Movimiento continuo en vivo: 'J M' hacia motor (3,0), 'J S' hacia sensor (3,1).
        self.assertEqual(self.traductor.encode("J M"), "3,0")
        self.assertEqual(self.traductor.encode("J S"), "3,1")

    def test_stop_continuous_move(self):
        # 'J P' y 'STOP' (insensible a mayúsculas) producen la parada (4).
        self.assertEqual(self.traductor.encode("J P"), "4")
        self.assertEqual(self.traductor.encode("STOP"), "4")
        self.assertEqual(self.traductor.encode("stop"), "4")


class TestActuadorCalibracion(unittest.TestCase):
    """Relación píxeles (simulador) <-> cambios (físico) usada para el control en vivo."""

    def test_travel_and_changes(self):
        # El bloque del simulador recorre de 508 a 1912 píxeles = una pasada = 140 cambios.
        self.assertEqual(translators.ActuatorTranslator.PIXELES_POR_PASADA, 1404)
        self.assertEqual(translators.ActuatorTranslator.CAMBIOS_POR_PASADA, 140)

    def test_pixels_per_change(self):
        # Aproximadamente 10.03 píxeles por cambio (1404 / 140).
        self.assertAlmostEqual(
            translators.ActuatorTranslator.PX_POR_CAMBIO, 1404 / 140, places=4)
        self.assertAlmostEqual(
            translators.ActuatorTranslator.PX_POR_CAMBIO, 10.03, places=2)

    def test_pixels_per_millimeter(self):
        # Aproximadamente 5.86 píxeles por milímetro (1404 píxeles / 239.4 milímetros).
        self.assertAlmostEqual(
            translators.ActuatorTranslator.PX_POR_MM, 5.864, places=2)


class TestActuadorDecodificacion(unittest.TestCase):
    """Decodificación del reporte del actuador físico -> simulador.

    Formato: '5,<posicion>[,<limiteMotor>,<limiteSensor>]'.
    """

    def setUp(self):
        self.traductor = translators.ActuatorTranslator()

    def test_position_only(self):
        # Forma corta '5,<posicion>': sin estado de los finales de carrera (limites = None).
        reporte = self.traductor.decode("5,0")
        self.assertEqual(reporte.pos, 0)
        self.assertIsNone(reporte.lim_motor)
        self.assertIsNone(reporte.lim_sensor)
        self.assertEqual(self.traductor.decode("  5 , 42 ").pos, 42)  # tolera espacios

    def test_position_with_limits(self):
        # Forma larga: posición + estado real de los dos finales de carrera (1 = pulsado).
        reporte = self.traductor.decode("5,0,1,0")  # en el tope del motor
        self.assertEqual(reporte.pos, 0)
        self.assertTrue(reporte.lim_motor)
        self.assertFalse(reporte.lim_sensor)

        reporte = self.traductor.decode("5,140,0,1")  # en el tope del sensor
        self.assertEqual(
            (reporte.pos, reporte.lim_motor, reporte.lim_sensor),
            (140, False, True))

        reporte = self.traductor.decode("5,73,0,0")  # a mitad, ninguno pulsado
        self.assertEqual((reporte.lim_motor, reporte.lim_sensor), (False, False))

    def test_not_a_report(self):
        # Comandos del simulador al robot u otros textos no son reportes válidos.
        for texto in ("3,0", "4", "hola", "5,abc", "5,1,2", "5,1,x,0", ""):
            self.assertIsNone(self.traductor.decode(texto), texto)


class TestActuadorInstruccionesInvalidas(unittest.TestCase):
    """Instrucciones inválidas -> TranslationError (no se publica nada)."""

    def setUp(self):
        self.traductor = translators.ActuatorTranslator()

    def _assert_error(self, texto):
        with self.assertRaises(translators.TranslationError):
            self.traductor.encode(texto)

    def test_empty(self):
        self._assert_error("")
        self._assert_error("   ")

    def test_unknown_command(self):
        self._assert_error("X")
        self._assert_error("Z 1 2 3")

    def test_control_bad_argument(self):
        self._assert_error("C Z")
        self._assert_error("C")

    def test_limit_bad_direction(self):
        self._assert_error("L X")
        self._assert_error("L")

    def test_movement_incomplete_fields(self):
        self._assert_error("M M C")        # falta el valor
        self._assert_error("M S")          # faltan el modo y el valor

    def test_movement_bad_direction_or_mode(self):
        self._assert_error("M X C 3")      # dirección inválida
        self._assert_error("M M X 3")      # modo inválido

    def test_movement_non_numeric_value(self):
        self._assert_error("M M C abc")

    def test_movement_non_positive_value(self):
        # El actuador no acepta objetivos menores o iguales que cero.
        self._assert_error("M M C 0")
        self._assert_error("M M C -5")

    def test_continuous_move_bad_argument(self):
        self._assert_error("J")        # falta la dirección
        self._assert_error("J X")      # dirección inválida
        self._assert_error("J M S")    # sobran tokens


if __name__ == "__main__":
    unittest.main(verbosity=2)
