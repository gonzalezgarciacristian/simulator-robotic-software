import unittest

from path_helper import codes_path

import robot_components.robots as r
import robot_components.elements as e
import robot_components.boards as b
import graphics.drawing as d


class TestsChallenges(unittest.TestCase):

    def get_correct_code(self):
        url = codes_path("challenge5")
        code_file = open(url, "r")
        code = code_file.read()
        code_file.close()
        return code

    def get_wrong_code(self):
        code = "// Este código no es correcto" \
               "int pinSensor = 2;\nint led = 4;\n\nvoid setup(){\n// Completar aquí\n}\n\n" \
               "void loop(){\n// Completar aquí\n}"
        return code

    def test_correct(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        pir = e.PIRSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(pir)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(23, pir)
        robot.board.attach_pin(6, pir)
        robot.board.attach_pin(20, pir)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        pir.attach_element(1, robot.board, 23)
        pir.attach_element(2, robot.board, 6)
        pir.attach_element(3, robot.board, 20)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (CORRECTO)
        code = self.get_correct_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código correcto
        self.assertEqual(code, True)
        # Circuito correcto
        self.assertEqual(circuit, True)

    def test_incorrect_code(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        pir = e.PIRSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(pir)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(23, pir)
        robot.board.attach_pin(6, pir)
        robot.board.attach_pin(20, pir)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        pir.attach_element(1, robot.board, 23)
        pir.attach_element(2, robot.board, 6)
        pir.attach_element(3, robot.board, 20)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (INCORRECTO)
        code = self.get_wrong_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código incorrecto
        self.assertEqual(code, False)
        # Circuito correcto
        self.assertEqual(circuit, True)

    def test_incorrect_circuit_less_elements(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos menos componentes de los necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (CORRECTO)
        code = self.get_correct_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código correcto
        self.assertEqual(code, True)
        # Circuito incorrecto
        self.assertEqual(circuit, False)

    def test_incorrect_circuit_less_connections(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        pir = e.PIRSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(pir)
        # Unimos solo algunos de los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(23, pir)
        robot.board.attach_pin(6, pir)
        # Unimos solo algunos de los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        pir.attach_element(1, robot.board, 23)
        pir.attach_element(2, robot.board, 6)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (CORRECTO)
        code = self.get_correct_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código correcto
        self.assertEqual(code, True)
        # Circuito incorrecto
        self.assertEqual(circuit, False)

    def test_incorrect_circuit_wrong_elements(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        light_sensor = e.LightSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(light_sensor)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(23, light_sensor)
        robot.board.attach_pin(6, light_sensor)
        robot.board.attach_pin(20, light_sensor)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        light_sensor.attach_element(1, robot.board, 23)
        light_sensor.attach_element(2, robot.board, 6)
        light_sensor.attach_element(3, robot.board, 20)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (CORRECTO)
        code = self.get_correct_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código correcto
        self.assertEqual(code, True)
        # Circuito incorrecto
        self.assertEqual(circuit, False)

    def test_incorrect_circuit_wrong_connections(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        pir = e.PIRSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(pir)
        # Unimos los componentes a la placa con errores en las conexiones
        robot.board.attach_pin(22, led1)
        robot.board.attach_pin(3, resistance1)
        robot.board.attach_pin(5, pir)
        robot.board.attach_pin(0, pir)
        robot.board.attach_pin(20, pir)
        # Unimos los componentes a la placa con errores en las conexiones
        led1.attach_element(1, robot.board, 22)
        resistance1.attach_element(2, robot.board, 3)
        pir.attach_element(1, robot.board, 5)
        pir.attach_element(2, robot.board, 0)
        pir.attach_element(3, robot.board, 20)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (CORRECTO)
        code = self.get_correct_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código correcto
        self.assertEqual(code, True)
        # Circuito incorrecto
        self.assertEqual(circuit, False)

    def test_incorrect_circuit_code(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(5)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        resistance1.attach_element(1, led1, 2)
        # Creamos el código a comprobar (INCORRECTO)
        code = self.get_wrong_code()
        # Comprobación
        code, circuit = drawing.probe(0, code, correct_code, robot, correct_robot)
        # Código incorrecto
        self.assertEqual(code, False)
        # Circuito incorrecto
        self.assertEqual(circuit, False)


if __name__ == '__main__':
    unittest.main()
