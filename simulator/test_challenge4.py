import unittest

from path_helper import codes_path

import robot_components.robots as r
import robot_components.elements as e
import robot_components.boards as b
import graphics.drawing as d


class TestsChallenges(unittest.TestCase):

    def get_correct_code(self):
        url = codes_path("challenge4")
        code_file = open(url, "r")
        code = code_file.read()
        code_file.close()
        return code

    def get_wrong_code(self):
        code = "// Este código no es correcto" \
               "int led1 = 2;\nint led2 = 3;\nint led3 = 4;\n\nvoid setup(){" \
               "\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"
        return code

    def test_correct(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(4)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        resistance3 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        led3 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(led3)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(resistance3)
        # Unimos los coponentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(5, led3)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(23, resistance3)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 4)
        led3.attach_element(1, robot.board, 5)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        resistance3.attach_element(2, robot.board, 23)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        led3.attach_element(2, resistance3, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
        resistance3.attach_element(1, led3, 2)
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
        correct_robot = drawing.get_robot_challenge(4)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        resistance3 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        led3 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(led3)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(resistance3)
        # Unimos los coponentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(5, led3)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(23, resistance3)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 4)
        led3.attach_element(1, robot.board, 5)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        resistance3.attach_element(2, robot.board, 23)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        led3.attach_element(2, resistance3, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
        resistance3.attach_element(1, led3, 2)
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
        correct_robot = drawing.get_robot_challenge(4)
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
        # Unimos los coponentes a la placa
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
        correct_robot = drawing.get_robot_challenge(4)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        resistance3 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        led3 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(led3)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(resistance3)
        # Unimos solo algunos coponentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        # Unimos solo algunos componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        led3.attach_element(2, resistance3, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
        resistance3.attach_element(1, led3, 2)
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
        correct_robot = drawing.get_robot_challenge(4)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios pero uno del tipo que no corresponde
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        led3 = e.LedArduino()
        light_sensor = e.LightSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(led3)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(light_sensor)
        # Unimos los coponentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(5, led3)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(23, light_sensor)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 4)
        led3.attach_element(1, robot.board, 5)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        light_sensor.attach_element(1, robot.board, 23)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
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
        correct_robot = drawing.get_robot_challenge(4)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        resistance3 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        led3 = e.LedArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(led3)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(resistance3)
        # Unimos los coponentes a la placa con errores en el tipo de pines
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, led2)
        robot.board.attach_pin(5, led3)
        robot.board.attach_pin(5, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(23, resistance3)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 22)
        led3.attach_element(1, robot.board, 5)
        resistance1.attach_element(2, robot.board, 5)
        resistance2.attach_element(2, robot.board, 22)
        resistance3.attach_element(2, robot.board, 23)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        led3.attach_element(2, resistance3, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
        resistance3.attach_element(1, led3, 2)
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
        correct_robot = drawing.get_robot_challenge(4)
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
        # Unimos los coponentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
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
