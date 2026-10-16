import unittest

from path_helper import codes_path

import robot_components.robots as r
import robot_components.elements as e
import robot_components.boards as b
import graphics.drawing as d


class TestsChallenges(unittest.TestCase):

    def get_correct_code(self):
        url = codes_path("challenge2")
        code_file = open(url, "r")
        code = code_file.read()
        code_file.close()
        return code

    def get_wrong_code(self):
        code = "// Este código no es correcto" \
               "#include <Keypad.h>\n\nint led_verde = 3;\nint led_rojo = 2;\n\n" \
               "char matriz[4][4] =\n{\n  {'1','2','3', 'A'},\n" \
               "  {'4','5','6', 'B'},\n  {'7','8','9', 'C'},\n  {'*','0','#', 'D'}\n};\n\n" \
               "byte pin_rows[4] = {4, 5, 6, 7};\n\nbyte pin_columns[4] = {A0, A1, A2, A3};\n\n" \
               "Keypad keyboard = Keypad( makeKeymap(matriz), pin_rows, pin_columns, 4, 4);" \
               "\n\nvoid setup(){\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"
        return code

    def test_correct(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 4)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
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
        # Circuito correcto
        self.assertEqual(circuit, True)

    def test_incorrect_code(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (CORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        led2.attach_element(1, robot.board, 4)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        led2.attach_element(2, resistance2, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, led2, 2)
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
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos menos componentes de los necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
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
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(keyboard)
        # Unimos algunos de los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        # Unimos algunos de los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
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


    def test_incorrect_circuit_wrong_elements(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios pero uno de tipo incorrecto
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        potentiometer = e.PotentiometerArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(potentiometer)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(4, potentiometer)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        potentiometer.attach_element(1, robot.board, 4)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
        # Unimos los componentes entre si
        led1.attach_element(2, resistance1, 1)
        potentiometer.attach_element(2, resistance2, 1)
        resistance1.attach_element(1, led1, 2)
        resistance2.attach_element(1, potentiometer, 2)
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
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos los componentes necesarios
        resistance1 = e.ResistanceArduino()
        resistance2 = e.ResistanceArduino()
        led1 = e.LedArduino()
        led2 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(led2)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(resistance2)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa con algunos errores de tipos de pines
        robot.board.attach_pin(22, led1)
        robot.board.attach_pin(4, led2)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(22, resistance2)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(22, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(1, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa con algunos errores de tipos de pines
        led1.attach_element(1, robot.board, 22)
        led2.attach_element(1, robot.board, 4)
        resistance1.attach_element(2, robot.board, 22)
        resistance2.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 22)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 1)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
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

    def test_incorrect_circuit_code(self):
        drawing = d.Drawing()
        # Obtenemos el robot correcto
        correct_robot = drawing.get_robot_challenge(2)
        # Obtenermos el código correcto
        correct_code = self.get_correct_code()
        # Configuramos el robot (INCORRECTO)
        robot = r.ArduinoBoard(self)
        # Creamos menos componentes de los necesarios
        resistance1 = e.ResistanceArduino()
        led1 = e.LedArduino()
        keyboard = e.KeyBoardArduino()
        # Añadimos los elementos
        robot.robot_elements.append(led1)
        robot.robot_elements.append(resistance1)
        robot.robot_elements.append(keyboard)
        # Unimos los componentes a la placa
        robot.board.attach_pin(3, led1)
        robot.board.attach_pin(22, resistance1)
        robot.board.attach_pin(5, keyboard)
        robot.board.attach_pin(6, keyboard)
        robot.board.attach_pin(7, keyboard)
        robot.board.attach_pin(8, keyboard)
        robot.board.attach_pin(15, keyboard)
        robot.board.attach_pin(16, keyboard)
        robot.board.attach_pin(17, keyboard)
        robot.board.attach_pin(18, keyboard)
        # Unimos los componentes a la placa
        led1.attach_element(1, robot.board, 3)
        resistance1.attach_element(2, robot.board, 22)
        keyboard.attach_element(1, robot.board, 5)
        keyboard.attach_element(2, robot.board, 6)
        keyboard.attach_element(3, robot.board, 7)
        keyboard.attach_element(4, robot.board, 8)
        keyboard.attach_element(5, robot.board, 15)
        keyboard.attach_element(6, robot.board, 16)
        keyboard.attach_element(7, robot.board, 17)
        keyboard.attach_element(8, robot.board, 18)
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
