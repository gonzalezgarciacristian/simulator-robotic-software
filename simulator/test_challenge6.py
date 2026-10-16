import unittest

from path_helper import codes_path

import robot_components.robots as r
import robot_components.elements as e
import robot_components.boards as b
import graphics.drawing as d


class TestsChallenges(unittest.TestCase):

    def get_correct_code(self):
        url = codes_path("challenge6")
        code_file = open(url, "r")
        code = code_file.read()
        code_file.close()
        return code

    def get_wrong_code(self):
        code = "// Este código no es correcto" \
               "long distance;\nlong responseTime;\nint pinTrig = 9;\nint pinEcho = 8;\nint led = 2;\n\n" \
               "void setup(){\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"
        return code

    def test_correct(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        ultrasound = e.UltrasoundSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(ultrasound)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(20, ultrasound)
        robot.board.attach_pin(23, ultrasound)
        robot.board.attach_pin(5, ultrasound)
        robot.board.attach_pin(6, ultrasound)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        ultrasound.attach_element(1, robot.board, 20)
        ultrasound.attach_element(2, robot.board, 23)
        ultrasound.attach_element(3, robot.board, 5)
        ultrasound.attach_element(4, robot.board, 6)
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        ultrasound = e.UltrasoundSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(ultrasound)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(20, ultrasound)
        robot.board.attach_pin(23, ultrasound)
        robot.board.attach_pin(5, ultrasound)
        robot.board.attach_pin(6, ultrasound)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        ultrasound.attach_element(1, robot.board, 20)
        ultrasound.attach_element(2, robot.board, 23)
        ultrasound.attach_element(3, robot.board, 5)
        ultrasound.attach_element(4, robot.board, 6)
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos menos componentesde los necesarios
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        ultrasound = e.UltrasoundSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(ultrasound)
        # Unimos solo algunos componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(20, ultrasound)
        robot.board.attach_pin(23, ultrasound)
        robot.board.attach_pin(5, ultrasound)
        # Unimos solo algunos componentes a la placa
        led1.attach_element(1, robot.board, 3)
        ultrasound.attach_element(1, robot.board, 20)
        ultrasound.attach_element(2, robot.board, 23)
        ultrasound.attach_element(3, robot.board, 5)
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios pero uno no es del tipo que debería
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        screen = e.ScreenArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(screen)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(20, screen)
        robot.board.attach_pin(23, screen)
        robot.board.attach_pin(5, screen)
        robot.board.attach_pin(6, screen)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        screen.attach_element(1, robot.board, 20)
        screen.attach_element(2, robot.board, 23)
        screen.attach_element(3, robot.board, 5)
        screen.attach_element(4, robot.board, 6)
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        ultrasound = e.UltrasoundSensorArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(ultrasound)
        # Unimos los componentes a la placa pero con errores en el tipo de conexiones
        robot.board.attach_pin(23, led1)
        robot.board.attach_pin(2, resistance1)
        robot.board.attach_pin(20, ultrasound)
        robot.board.attach_pin(0, ultrasound)
        robot.board.attach_pin(15, ultrasound)
        robot.board.attach_pin(6, ultrasound)
        # Unimos los componentes a la placa pero con errores en el tipo de conexiones
        led1.attach_element(1, robot.board, 23)
        resistance1.attach_element(2, robot.board, 2)
        ultrasound.attach_element(1, robot.board, 20)
        ultrasound.attach_element(2, robot.board, 0)
        ultrasound.attach_element(3, robot.board, 15)
        ultrasound.attach_element(4, robot.board, 6)
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
        correct_robot = drawing.get_robot_challenge(6)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos menos componentes de los necesarios
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
