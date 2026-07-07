"""
This module defines the components used for both robots.
Those being: Servos, board, sensors and inputs (button and
joystick)
"""

import robot_components.boards as boards
import robot_components.elements as elements


class Robot:

    def __init__(self, board):
        self.board = board
        self.robot_elements = []

    def get_data(self):
        pass

    def assign_pins(self):
        pass

    def parse_pin(self, pin):
        if str(pin[0]).lower() == 'a':
            return int(pin[1]) + 14
        return int(pin)

    def add_component(self, component):
        pass

    def get_code(self):
        pass

    def reset(self):
        pass


class MobileRobot(Robot):

    def __init__(self, n_ligth_sens, pins):
        """
        Constructor for mobile robot
        Arguments:
            n_light_sens: the number of light sensors
            of the robot
            pins: the used pins of the board
        """
        super().__init__(boards.BQzumBT328())

        self.servo_left = elements.Servo()
        self.servo_right = elements.Servo()

        self.light_sensors = []
        i = 0
        while i < n_ligth_sens:
            self.light_sensors.append(elements.LightSensor())
            i += 1

        self.sound = elements.UltrasoundSensor()

        self.assign_pins(pins)

    def get_data(self):
        data = None
        if len(self.light_sensors) == 2:
            data = {
                "servo_left": self.servo_left.pin,
                "servo_right": self.servo_right.pin,
                "light_left": self.light_sensors[0].pin,
                "light_right": self.light_sensors[1].pin,
                "sound_trig": self.sound.pin_trig,
                "sound_echo": self.sound.pin_echo
            }
        elif len(self.light_sensors) == 3:
            data = {
                "servo_left": self.servo_left.pin,
                "servo_right": self.servo_right.pin,
                "light_mleft": self.light_sensors[0].pin,
                "light_left": self.light_sensors[1].pin,
                "light_right": self.light_sensors[2].pin,
                "sound_trig": self.sound.pin_trig,
                "sound_echo": self.sound.pin_echo
            }
        elif len(self.light_sensors) == 4:
            data = {
                "servo_left": self.servo_left.pin,
                "servo_right": self.servo_right.pin,
                "light_mleft": self.light_sensors[0].pin,
                "light_left": self.light_sensors[1].pin,
                "light_right": self.light_sensors[2].pin,
                "light_mright": self.light_sensors[3].pin,
                "sound_trig": self.sound.pin_trig,
                "sound_echo": self.sound.pin_echo
            }
        else:
            data = {
                "servo_left": self.servo_left.pin,
                "servo_right": self.servo_right.pin,
                "light_mleft": self.light_sensors[0].pin,
                "light_left": self.light_sensors[1].pin,
                "light_right": self.light_sensors[2].pin,
                "light_mright": self.light_sensors[3].pin,
                "sound_trig": self.sound.pin_trig,
                "sound_echo": self.sound.pin_echo
            }
        return data

    def assign_pins(self, pins):
        """
        Assigns the pins to the corresponding element
        Arguments:
            pins: a list of tuples with the name of the element
            and the corresponding pin
        """
        for pin in pins:
            name = pin[0]
            pin = self.parse_pin(pin[1])
            if name == "servo left":
                self.set_servo_left(pin)
            elif name == "servo right":
                self.set_servo_right(pin)
            elif name == "light 1":
                self.set_light_mleft(pin)
            elif name == "light 2":
                self.set_light_left(pin)
            elif name == "light 3":
                self.set_light_right(pin)
            elif name == "light 4":
                self.set_light_mright(pin)
            elif name == "trig":
                self.set_sound_trig(pin)
            elif name == "echo":
                self.set_sound_echo(pin)

    def set_light_sens_value(self, values):
        """
        Sets the light sensor values
        Arguments:
            values: the values to write into the sensors
        """
        for i in range(0, len(self.light_sensors)):
            self.light_sensors[i].value = values[i]

    def set_servo_left(self, pin):
        """
        Sets servo left attached to a pin and marks
        the pin as used at the board
        """
        if self.board.check_type(pin, self.servo_left.get_pin_type()):
            if self.board.attach_pin(pin, self.servo_left):
                self.servo_left.pin = pin

    def detach_servo_left(self):
        """
        Detaches left sensor from board
        """
        self.board.detach_pin(self.servo_left.pin)
        self.servo_left.pin = -1

    def set_servo_right(self, pin):
        """
        Sets servo right attached to a pin and marks
        the pin as used at the board
        """
        if self.board.check_type(pin, self.servo_right.get_pin_type()):
            if self.board.attach_pin(pin, self.servo_right):
                self.servo_right.pin = pin

    def detach_servo_right(self):
        """
        Detaches right sensor from board
        """
        self.board.detach_pin(self.servo_right.pin)
        self.servo_right.pin = -1

    def set_light_mleft(self, pin):
        """
        Sets the most left light sensor attached to a pin
        and marks the pin as used at the board
        """
        light = self.light_sensors[0]
        if self.board.check_type(pin, light.get_pin_type()):
            if self.board.attach_pin(pin, light):
                light.pin = pin

    def detach_light_mleft(self):
        """
        Detaches the most left light sensor from board
        """
        light = self.light_sensors[0]
        self.board.detach_pin(light.pin)
        light.pin = -1

    def set_light_left(self, pin):
        """
        Sets left light sensor attached to a pin
        and marks the pin as used at the board
        """
        light = self.light_sensors[0] if len(
            self.light_sensors) == 2 else self.light_sensors[1]
        if self.board.check_type(pin, light.get_pin_type()):
            if self.board.attach_pin(pin, light):
                light.pin = pin

    def detach_light_left(self):
        """
        Detaches left light sensor from board
        """
        light = self.light_sensors[0] if len(
            self.light_sensors) == 2 else self.light_sensors[1]
        self.board.detach_pin(light.pin)
        light.pin = -1

    def set_light_right(self, pin):
        """
        Sets right light sensor attached to a pin
        and marks the pin as used at the board
        """
        light = self.light_sensors[1] if len(
            self.light_sensors) == 2 else self.light_sensors[2]
        if self.board.check_type(pin, light.get_pin_type()):
            if self.board.attach_pin(pin, light):
                light.pin = pin

    def detach_light_right(self):
        """
        Detaches right light sensor from board
        """
        light = self.light_sensors[1] if len(
            self.light_sensors) == 2 else self.light_sensors[2]
        self.board.detach_pin(light.pin)
        light.pin = -1

    def set_light_mright(self, pin):
        """
        Sets the most right light sensor attached to a pin
        and marks the pin as used at the board
        """
        light = self.light_sensors[3]
        if self.board.check_type(pin, light.get_pin_type()):
            if self.board.attach_pin(pin, light):
                light.pin = pin

    def detach_light_mright(self):
        """
        Detaches the most right light sensor from board
        """
        light = self.light_sensors[3]
        self.board.detach_pin(light.pin)
        light.pin = -1

    def set_sound_trig(self, pin):
        """
        Sets sound sensor attached to a pin (trig) and marks it
        as used at the board
        """
        if self.board.check_type(pin, self.sound.get_trig_pin_type()):
            if self.board.attach_pin(pin, self.sound):
                self.sound.pin_trig = pin

    def detach_sound_trig(self):
        """
        Detaches ultrasound sensor (trig) from board
        """
        self.board.detach_pin(self.sound.pin_trig)
        self.sound.pin_trig = -1

    def set_sound_echo(self, pin):
        """
        Sets sound sensor attached to a pin (echo) and marks it
        as used at the board
        """
        if self.board.check_type(pin, self.sound.get_echo_pin_type()):
            if self.board.attach_pin(pin, self.sound):
                self.sound.pin_echo = pin

    def detach_sound_echo(self):
        """
        Detaches ultrasound sensor (echo) from board
        """
        self.board.detach_pin(self.sound.pin_echo)
        self.sound.pin_echo = -1


class LinearActuator(Robot):

    def __init__(self, pins):
        """
        Constructor for Linear Actuator
        Arguments:
            pins: the used pins of the board
        """
        super().__init__(boards.ArduinoUno())

        self.button_left = elements.Button()
        self.button_right = elements.Button()

        self.servo = elements.Servo()

        self.joystick = elements.Joystick()

        self.assign_pins(pins)

    def get_data(self):
        return {
            "button_left": self.button_left.pin,
            "button_right": self.button_right.pin,
            "servo": self.servo.pin,
            "button_joystick": self.joystick.pinb,
            "joystick_x": self.joystick.pinx,
            "joystick_y": self.joystick.piny
        }

    def assign_pins(self, pins):
        """
        Assigns the pins to the corresponding element
        Arguments:
            pins: a list of tuples with the name of the element
            and the corresponding pin
        """
        for pin in pins:
            name = pin[0]
            pin = self.parse_pin(pin[1])
            if name == "servo":
                self.set_servo(pin)
            elif name == "button joystick":
                self.set_joystick_button(pin)
            elif name == "x joystick":
                self.set_joystick_x(pin)
            elif name == "y joystick":
                self.set_joystick_y(pin)
            elif name == "button left":
                self.set_button_left(pin)
            elif name == "button right":
                self.set_button_right(pin)

    def set_button_left(self, pin):
        """
        Attaches left button to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.button_left.get_pin_type()):
            if self.board.attach_pin(pin, self.button_left):
                self.button_left.pin = pin

    def detach_button_left(self):
        """
        Detaches left button from board
        """
        self.board.detach_pin(self.button_left.pin)
        self.button_left.pin = -1

    def set_button_right(self, pin):
        """
        Attaches right button to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.button_right.get_pin_type()):
            if self.board.attach_pin(pin, self.button_right):
                self.button_right.pin = pin

    def detach_button_right(self):
        """
        Detaches right button from board
        """
        self.board.detach_pin(self.button_right.pin)
        self.button_right.pin = -1

    def set_servo(self, pin):
        """
        Attaches servo to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.servo.get_pin_type()):
            if self.board.attach_pin(pin, self.servo):
                self.servo.pin = pin

    def detach_servo(self):
        """
        Detaches servo from board
        """
        self.board.detach_pin(self.servo.pin)
        self.servo.pin = -1

    def set_joystick_x(self, pin):
        """
        Attaches joystick (x) to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.joystick.get_x_pin_type()):
            if self.board.attach_pin(pin, self.joystick):
                self.joystick.pinx = pin

    def detach_joystick_x(self):
        """
        Detaches joystick (x) from board
        """
        self.board.detach_pin(self.joystick.pinx)
        self.joystick.pinx = -1

    def set_joystick_y(self, pin):
        """
        Attaches joystick (y) to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.joystick.get_y_pin_type()):
            if self.board.attach_pin(pin, self.joystick):
                self.joystick.piny = pin

    def detach_joystick_y(self):
        """
        Detaches joystick (y) from board
        """
        self.board.detach_pin(self.joystick.piny)
        self.joystick.piny = -1

    def set_joystick_button(self, pin):
        """
        Attaches joystick (x) to board pin
        Arguments:
            pin: the pin of the board
        """
        if self.board.check_type(pin, self.joystick.get_button_pin_type()):
            if self.board.attach_pin(pin, self.joystick):
                self.joystick.pinb = pin

    def detach_joystick_button(self):
        """
        Detaches joystick (x) from board
        """
        self.board.detach_pin(self.joystick.pinb)
        self.joystick.pinb = -1


class ArmHardwareRobot(Robot):
    """
    Robot hardware simulado del sistema de brazo 3D.
    Contiene 6 servomotores pre-conectados a sus pines estándar.
    Los valores de los servos son leídos por Arm3DLayer en cada fotograma.
    """

    # Pines estándar del Braccio (coinciden con libraries/braccio.py)
    # Los joints se asignan secuencialmente segun el orden de attach().

    JOINT_NAMES = ['base', 'shoulder', 'elbow', 'wrist_ver', 'wrist_rot', 'gripper']

    def __init__(self):
        super().__init__(boards.BQzumBT328())
        self.board.arm_robot = self

        self._joint_servos = [elements.ArmJointServo() for _ in range(6)]
        self.servo_base = self._joint_servos[0]
        self.servo_shoulder = self._joint_servos[1]
        self.servo_elbow = self._joint_servos[2]
        self.servo_wrist_vertical = self._joint_servos[3]
        self.servo_wrist = self._joint_servos[4]
        self.servo_gripper = self._joint_servos[5]
        self.robot_elements = list(self._joint_servos)
        self._servo_pins = [None] * len(self._joint_servos)

    def attach_servo_to_pin(self, pin, joint_name=None):
        """Asocia un servo virtual solo si el pin coincide con la configuracion."""
        for servo in self._joint_servos:
            if servo.pin == pin and self.board.get_pin_element(pin) is servo:
                return servo

        mapped_idx = self._joint_index_for_pin(pin)
        if mapped_idx is None and joint_name:
            mapped_idx = self._joint_index_for_name(joint_name)
        if mapped_idx is not None:
            return self._attach_joint_servo(mapped_idx, pin)

        return None

    def set_servo_pin_mapping(self, pins):
        """Actualiza la tabla pin -> joint usada por Servo.attach y Braccio."""
        normalized = []
        for pin in list(pins or [])[:len(self._joint_servos)]:
            try:
                normalized.append(None if pin is None else int(pin))
            except (TypeError, ValueError):
                normalized.append(None)
        while len(normalized) < len(self._joint_servos):
            normalized.append(None)
        self._servo_pins = normalized

    def get_servo_pin_mapping(self):
        return list(self._servo_pins)

    def get_named_servo_pins(self, fallback=None):
        fallback = fallback or {}
        if not any(pin is not None for pin in self._servo_pins):
            return dict(fallback)
        result = {}
        for idx, name in enumerate(self.JOINT_NAMES):
            pin = self._servo_pins[idx] if idx < len(self._servo_pins) else None
            result[name] = pin
        return result

    def detach_servo(self, servo):
        """Libera el pin asociado a un servo virtual del brazo."""
        if servo is None or servo not in self._joint_servos:
            return False
        if servo.pin != -1:
            self.board.detach_pin(servo.pin)
            servo.pin = -1
        return True

    def _attach_joint_servo(self, joint_idx, pin):
        if not (0 <= joint_idx < len(self._joint_servos)):
            return None

        servo = self._joint_servos[joint_idx]
        if not self.board.check_type(pin, servo.get_pin_type()):
            return None

        existing = self.board.get_pin_element(pin)
        if existing is not None and existing is not servo:
            return None

        if servo.pin != -1 and servo.pin != pin:
            self.board.detach_pin(servo.pin)

        if existing is None and not self.board.attach_pin(pin, servo):
            return None

        servo.pin = pin
        self.board.set_pin_mode(pin, boards.Board.OUTPUT)
        return servo

    def _joint_index_for_pin(self, pin):
        try:
            pin = int(pin)
        except (TypeError, ValueError):
            return None
        for idx, mapped_pin in enumerate(self._servo_pins):
            if mapped_pin == pin:
                return idx
        return None

    def _joint_index_for_name(self, joint_name):
        if joint_name not in self.JOINT_NAMES:
            return None
        return self.JOINT_NAMES.index(joint_name)

    def get_servo_values(self):
        """
        Devuelve los valores actuales de los 6 servos en orden:
        [base, shoulder, elbow, wrist_vertical, wrist_rot, gripper]
        """
        return [servo.value for servo in self._joint_servos]


class ArduinoBoard(Robot):

    def __init__(self, pins):
        """
        Constructor for arduino board
        """
        super().__init__(boards.ArduinoUno())

    def reset(self):
        self.robot_elements.clear()

    def draw_buttons(self, x, y):
        return self.board.draw_buttons(x, y)

    def add_component(self, component):
        if component == "resistance":
            resistance = elements.ResistanceArduino()
            resistance.set_value(56000)
            self.robot_elements.append(resistance)
            return resistance
        if component == "resistance220":
            resistance = elements.ResistanceArduino()
            resistance.set_value(220)
            self.robot_elements.append(resistance)
            return resistance
        if component == "resistance10k":
            resistance = elements.ResistanceArduino()
            resistance.set_value(10000)
            self.robot_elements.append(resistance)
            return resistance
        elif component == "button":
            button = elements.ButtonArduino()
            self.robot_elements.append(button)
            return button
        elif component == "potentiometer":
            potentiometer = elements.PotentiometerArduino()
            self.robot_elements.append(potentiometer)
            return potentiometer
        elif component == "led":
            led = elements.LedArduino()
            led.set_color(1)
            self.robot_elements.append(led)
            return led
        elif component == "ledYellow":
            led = elements.LedArduino()
            led.set_color(2)
            self.robot_elements.append(led)
            return led
        elif component == "ledGreen":
            led = elements.LedArduino()
            led.set_color(3)
            self.robot_elements.append(led)
            return led
        elif component == "buzzer":
            buzzer = elements.BuzzerArduino()
            self.robot_elements.append(buzzer)
            return buzzer
        elif component == "ledRGB":
            led_rgb = elements.RGBArduino()
            self.robot_elements.append(led_rgb)
            return led_rgb
        elif component == "lightSensor":
            light_sensor = elements.LightSensorArduino()
            self.robot_elements.append(light_sensor)
            return light_sensor
        elif component == "PIRSensor":
            pir_sensor = elements.PIRSensorArduino()
            self.robot_elements.append(pir_sensor)
            return pir_sensor
        elif component == "vibrationSensor":
            vibration_sensor = elements.VibrationSensorArduino()
            self.robot_elements.append(vibration_sensor)
            return vibration_sensor
        elif component == "infraredSensor":
            infrared_sensor = elements.InfraredSensorArduino()
            self.robot_elements.append(infrared_sensor)
            return infrared_sensor
        elif component == "ultrasonicSensor":
            ultrasonic_sensor = elements.UltrasoundSensorArduino()
            self.robot_elements.append(ultrasonic_sensor)
            return ultrasonic_sensor
        elif component == "keyboard":
            keyboard = elements.KeyBoardArduino()
            self.robot_elements.append(keyboard)
            return keyboard
        elif component == "screen":
            screen = elements.ScreenArduino()
            self.robot_elements.append(screen)
            return screen
        elif component == "servomotor180":
            servomotor = elements.ServomotorArduino()
            self.robot_elements.append(servomotor)
            return servomotor

    def set_resistance1(self, pin, resistance):
        """
        Attaches the pin 1 of a resistance to board pin
        Arguments:
            pin: the pin of the board
            resistance: the resistance to attach
        """
        if self.board.check_type(pin, resistance.get_pin1_type()):
            if self.board.attach_pin(pin, resistance):
                resistance.pin1 = pin

    def set_resistance2(self, pin, resistance):
        """
        Attaches the pin 2 of a resistance to board pin
        Arguments:
            pin: the pin of the board
            resistance: the resistance to attach
        """
        if self.board.check_type(pin, resistance.get_pin2_type()):
            if self.board.attach_pin(pin, resistance):
                resistance.pin2 = pin

    def set_button1(self, pin, button):
        """
        Attaches the pin 1 of a button to board pin
        Arguments:
            pin: the pin of the board
            button: the button to attach
        """
        if self.board.check_type(pin, button.get_pin1_type()):
            if self.board.attach_pin(pin, button):
                button.pin1 = pin

    def set_button2(self, pin, button):
        """
        Attaches the pin 2 of a button to board pin
        Arguments:
            pin: the pin of the board
            button: the button to attach
        """
        if self.board.check_type(pin, button.get_pin2_type()):
            if self.board.attach_pin(pin, button):
                button.pin2 = pin

    def set_button3(self, pin, button):
        """
        Attaches the pin 3 of a button to board pin
        Arguments:
            pin: the pin of the board
            button: the button to attach
        """
        if self.board.check_type(pin, button.get_pin3_type()):
            if self.board.attach_pin(pin, button):
                button.pin3 = pin

    def set_button4(self, pin, button):
        """
        Attaches the pin 4 of a button to board pin
        Arguments:
            pin: the pin of the board
            button: the button to attach
        """
        if self.board.check_type(pin, button.get_pin4_type()):
            if self.board.attach_pin(pin, button):
                button.pin4 = pin

    def set_potentiometer1(self, pin, potentiometer):
        """
        Attaches the pin 1 of a potentiometer to board pin
        Arguments:
            pin: the pin of the board
            potentiometer: the potentiometer to attach
        """
        if self.board.check_type(pin, potentiometer.get_pin1_type()):
            if self.board.attach_pin(pin, potentiometer):
                potentiometer.pin1 = pin

    def set_potentiometer2(self, pin, potentiometer):
        """
        Attaches the pin 2 of a potentiometer to board pin
        Arguments:
            pin: the pin of the board
            potentiometer: the potentiometer to attach
        """
        if self.board.check_type(pin, potentiometer.get_pin2_type()):
            if self.board.attach_pin(pin, potentiometer):
                potentiometer.pin2 = pin

    def set_potentiometer3(self, pin, potentiometer):
        """
        Attaches the pin 3 of a potentiometer to board pin
        Arguments:
            pin: the pin of the board
            potentiometer: the potentiometer to attach
        """
        if self.board.check_type(pin, potentiometer.get_pin3_type()):
            if self.board.attach_pin(pin, potentiometer):
                potentiometer.pin3 = pin

    def set_led1(self, pin, led):
        """
        Attaches the pin 1 of a LED to board pin
        Arguments:
            pin: the pin of the board
            led: the LED to attach
        """
        if self.board.check_type(pin, led.get_pin1_type()):
            if self.board.attach_pin(pin, led):
                led.pin1 = pin

    def set_led2(self, pin, led):
        """
        Attaches the pin 2 of a LED to board pin
        Arguments:
            pin: the pin of the board
            led: the LED to attach
        """
        if self.board.check_type(pin, led.get_pin2_type()):
            if self.board.attach_pin(pin, led):
                led.pin2 = pin

    def set_buzzer1(self, pin, buzzer):
        """
        Attaches the pin 1 of a buzzer to board pin
        Arguments:
            pin: the pin of the board
            buzzer: the buzzer to attach
        """
        if self.board.check_type(pin, buzzer.get_pin1_type()):
            if self.board.attach_pin(pin, buzzer):
                buzzer.pin1 = pin

    def set_buzzer2(self, pin, buzzer):
        """
        Attaches the pin 2 of a buzzer to board pin
        Arguments:
            pin: the pin of the board
            buzzer: the buzzer to attach
        """
        if self.board.check_type(pin, buzzer.get_pin2_type()):
            if self.board.attach_pin(pin, buzzer):
                buzzer.pin2 = pin

    def set_buzzer3(self, pin, buzzer):
        """
        Attaches the pin 3 of a buzzer to board pin
        Arguments:
            pin: the pin of the board
            buzzer: the buzzer to attach
        """
        if self.board.check_type(pin, buzzer.get_pin3_type()):
            if self.board.attach_pin(pin, buzzer):
                buzzer.pin3 = pin

    def set_rgb1(self, pin, rgb):
        """
        Attaches the pin 1 of a LED rgb to board pin
        Arguments:
            pin: the pin of the board
            rgb: the LED rgb to attach
        """
        if self.board.check_type(pin, rgb.get_pin1_type()):
            if self.board.attach_pin(pin, rgb):
                rgb.pin1 = pin

    def set_rgb2(self, pin, rgb):
        """
        Attaches the pin 2 of a LED rgb to board pin
        Arguments:
            pin: the pin of the board
            rgb: the LED rgb to attach
        """
        if self.board.check_type(pin, rgb.get_pin2_type()):
            if self.board.attach_pin(pin, rgb):
                rgb.pin2 = pin

    def set_rgb3(self, pin, rgb):
        """
        Attaches the pin 3 of a LED rgb to board pin
        Arguments:
            pin: the pin of the board
            rgb: the LED rgb to attach
        """
        if self.board.check_type(pin, rgb.get_pin3_type()):
            if self.board.attach_pin(pin, rgb):
                rgb.pin3 = pin

    def set_rgb4(self, pin, rgb):
        """
        Attaches the pin 4 of a LED rgb to board pin
        Arguments:
            pin: the pin of the board
            rgb: the LED rgb to attach
        """
        if self.board.check_type(pin, rgb.get_pin4_type()):
            if self.board.attach_pin(pin, rgb):
                rgb.pin4 = pin

    def set_light_sensor1(self, pin, light_sensor):
        """
        Attaches the pin 1 of a light sensor to board pin
        Arguments:
            pin: the pin of the board
            light_sensor: the light_sensor to attach
        """
        if self.board.check_type(pin, light_sensor.get_pin1_type()):
            if self.board.attach_pin(pin, light_sensor):
                light_sensor.pin1 = pin

    def set_light_sensor2(self, pin, light_sensor):
        """
        Attaches the pin 2 of a light sensor to board pin
        Arguments:
            pin: the pin of the board
            light_sensor: the light_sensor to attach
        """
        if self.board.check_type(pin, light_sensor.get_pin2_type()):
            if self.board.attach_pin(pin, light_sensor):
                light_sensor.pin2 = pin

    def set_light_sensor3(self, pin, light_sensor):
        """
        Attaches the pin 3 of a light sensor to board pin
        Arguments:
            pin: the pin of the board
            light_sensor: the light sensor to attach
        """
        if self.board.check_type(pin, light_sensor.get_pin3_type()):
            if self.board.attach_pin(pin, light_sensor):
                light_sensor.pin3 = pin

    def set_pir_sensor1(self, pin, pir_sensor):
        """
        Attaches the pin 1 of a PIR sensor to board pin
        Arguments:
            pin: the pin of the board
            pir_sensor: the PIR sensor to attach
        """
        if self.board.check_type(pin, pir_sensor.get_pin1_type()):
            if self.board.attach_pin(pin, pir_sensor):
                pir_sensor.pin1 = pin

    def set_pir_sensor2(self, pin, pir_sensor):
        """
        Attaches the pin 2 of a PIR sensor to board pin
        Arguments:
            pin: the pin of the board
            pir_sensor: the PIR sensor to attach
        """
        if self.board.check_type(pin, pir_sensor.get_pin2_type()):
            if self.board.attach_pin(pin, pir_sensor):
                pir_sensor.pin2 = pin

    def set_pir_sensor3(self, pin, pir_sensor):
        """
        Attaches the pin 3 of a PIR sensor to board pin
        Arguments:
            pin: the pin of the board
            pir_sensor: the PIR sensor to attach
        """
        if self.board.check_type(pin, pir_sensor.get_pin3_type()):
            if self.board.attach_pin(pin, pir_sensor):
                pir_sensor.pin3 = pin

    def set_vibration_sensor1(self, pin, vibration_sensor):
        """
        Attaches the pin 1 of a vibration sensor to board pin
        Arguments:
            pin: the pin of the board
            vibration_sensor: the vibration sensor to attach
        """
        if self.board.check_type(pin, vibration_sensor.get_pin1_type()):
            if self.board.attach_pin(pin, vibration_sensor):
                vibration_sensor.pin1 = pin

    def set_vibration_sensor2(self, pin, vibration_sensor):
        """
        Attaches the pin 2 of a vibration sensor to board pin
        Arguments:
            pin: the pin of the board
            vibration_sensor: the vibration sensor to attach
        """
        if self.board.check_type(pin, vibration_sensor.get_pin2_type()):
            if self.board.attach_pin(pin, vibration_sensor):
                vibration_sensor.pin2 = pin

    def set_vibration_sensor3(self, pin, vibration_sensor):
        """
        Attaches the pin 3 of a vibration sensor to board pin
        Arguments:
            pin: the pin of the board
            vibration_sensor: the vibration sensor to attach
        """
        if self.board.check_type(pin, vibration_sensor.get_pin3_type()):
            if self.board.attach_pin(pin, vibration_sensor):
                vibration_sensor.pin3 = pin

    def set_infrared_sensor1(self, pin, infrared_sensor):
        """
        Attaches the pin 1 of an infrared sensor to board pin
        Arguments:
            pin: the pin of the board
            infrared_sensor: the infrared sensor to attach
        """
        if self.board.check_type(pin, infrared_sensor.get_pin1_type()):
            if self.board.attach_pin(pin, infrared_sensor):
                infrared_sensor.pin1 = pin

    def set_infrared_sensor2(self, pin, infrared_sensor):
        """
        Attaches the pin 2 of an infrared sensor to board pin
        Arguments:
            pin: the pin of the board
            infrared_sensor: the infrared sensor to attach
        """
        if self.board.check_type(pin, infrared_sensor.get_pin2_type()):
            if self.board.attach_pin(pin, infrared_sensor):
                infrared_sensor.pin2 = pin

    def set_infrared_sensor3(self, pin, infrared_sensor):
        """
        Attaches the pin 3 of an infrared sensor to board pin
        Arguments:
            pin: the pin of the board
            infrared_sensor: the infrared sensor to attach
        """
        if self.board.check_type(pin, infrared_sensor.get_pin3_type()):
            if self.board.attach_pin(pin, infrared_sensor):
                infrared_sensor.pin3 = pin

    def set_ultrasonic_sensor1(self, pin, ultrasonic_sensor):
        """
        Attaches the pin 1 of an ultrasonic sensor to board pin
        Arguments:
            pin: the pin of the board
            ultrasonic_sensor: the ultrasonic sensor to attach
        """
        if self.board.check_type(pin, ultrasonic_sensor.get_pin1_type()):
            if self.board.attach_pin(pin, ultrasonic_sensor):
                ultrasonic_sensor.pin1 = pin

    def set_ultrasonic_sensor2(self, pin, ultrasonic_sensor):
        """
        Attaches the pin 2 of an ultrasonic sensor to board pin
        Arguments:
            pin: the pin of the board
            ultrasonic_sensor: the ultrasonic sensor to attach
        """
        if self.board.check_type(pin, ultrasonic_sensor.get_pin2_type()):
            if self.board.attach_pin(pin, ultrasonic_sensor):
                ultrasonic_sensor.pin2 = pin

    def set_ultrasonic_sensor3(self, pin, ultrasonic_sensor):
        """
        Attaches the pin 3 of an ultrasonic sensor to board pin
        Arguments:
            pin: the pin of the board
            ultrasonic_sensor: the ultrasonic sensor to attach
        """
        if self.board.check_type(pin, ultrasonic_sensor.get_pin3_type()):
            if self.board.attach_pin(pin, ultrasonic_sensor):
                ultrasonic_sensor.pin3 = pin

    def set_ultrasonic_sensor4(self, pin, ultrasonic_sensor):
        """
        Attaches the pin 4 of an ultrasonic sensor to board pin
        Arguments:
            pin: the pin of the board
            ultrasonic_sensor: the ultrasonic sensor to attach
        """
        if self.board.check_type(pin, ultrasonic_sensor.get_pin4_type()):
            if self.board.attach_pin(pin, ultrasonic_sensor):
                ultrasonic_sensor.pin4 = pin

    def set_keyboard1(self, pin, keyboard):
        """
        Attaches the pin 1 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin1_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin1 = pin

    def set_keyboard2(self, pin, keyboard):
        """
        Attaches the pin 2 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin2_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin2 = pin

    def set_keyboard3(self, pin, keyboard):
        """
        Attaches the pin 3 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin3_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin3 = pin

    def set_keyboard4(self, pin, keyboard):
        """
        Attaches the pin 4 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin4_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin4 = pin

    def set_keyboard5(self, pin, keyboard):
        """
        Attaches the pin 5 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin5_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin5 = pin

    def set_keyboard6(self, pin, keyboard):
        """
        Attaches the pin 6 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin6_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin6 = pin

    def set_keyboard7(self, pin, keyboard):
        """
        Attaches the pin 7 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin7_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin7 = pin

    def set_keyboard8(self, pin, keyboard):
        """
        Attaches the pin 8 of a keyboard to board pin
        Arguments:
            pin: the pin of the board
            keyboard: the keyboard to attach
        """
        if self.board.check_type(pin, keyboard.get_pin8_type()):
            if self.board.attach_pin(pin, keyboard):
                keyboard.pin8 = pin

    def set_screen1(self, pin, screen):
        """
        Attaches the pin 1 of a screen to board pin
        Arguments:
            pin: the pin of the board
            screen: the screen to attach
        """
        if self.board.check_type(pin, screen.get_pin1_type()):
            if self.board.attach_pin(pin, screen):
                screen.pin1 = pin

    def set_screen2(self, pin, screen):
        """
        Attaches the pin 2 of a screen to board pin
        Arguments:
            pin: the pin of the board
            screen: the screen to attach
        """
        if self.board.check_type(pin, screen.get_pin2_type()):
            if self.board.attach_pin(pin, screen):
                screen.pin2 = pin

    def set_screen3(self, pin, screen):
        """
        Attaches the pin 3 of a screen to board pin
        Arguments:
            pin: the pin of the board
            screen: the screen to attach
        """
        if self.board.check_type(pin, screen.get_pin3_type()):
            if self.board.attach_pin(pin, screen):
                screen.pin3 = pin

    def set_screen4(self, pin, screen):
        """
        Attaches the pin 4 of a screen to board pin
        Arguments:
            pin: the pin of the board
            screen: the screen to attach
        """
        if self.board.check_type(pin, screen.get_pin4_type()):
            if self.board.attach_pin(pin, screen):
                screen.pin4 = pin

    def set_servomotor1(self, pin, servomotor):
        """
        Attaches the pin 1 of a servomotor to board pin
        Arguments:
            pin: the pin of the board
            servomotor: the servomotor to attach
        """
        if self.board.check_type(pin, servomotor.get_pin1_type()):
            if self.board.attach_pin(pin, servomotor):
                servomotor.pin1 = pin

    def set_servomotor2(self, pin, servomotor):
        """
        Attaches the pin 2 of a servomotor to board pin
        Arguments:
            pin: the pin of the board
            servomotor: the servomotor to attach
        """
        if self.board.check_type(pin, servomotor.get_pin2_type()):
            if self.board.attach_pin(pin, servomotor):
                servomotor.pin2 = pin

    def set_servomotor3(self, pin, servomotor):
        """
        Attaches the pin 3 of a servomotor to board pin
        Arguments:
            pin: the pin of the board
            servomotor: the servomotor to attach
        """
        if self.board.check_type(pin, servomotor.get_pin3_type()):
            if self.board.attach_pin(pin, servomotor):
                servomotor.pin3 = pin

class Challenge0Robot(Robot):
    """
    Class for the Arduino free use: no challenge
    """
    def __init__(self, robot):
        """
        Constructor for the robot of challenge1
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        """
        Charge the source code. This is the solution to compare with the student's code
        :return:
        """
        code_file = open("codes/challenge0", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        """
        It contains all the clues that you would like to show in the different clicks of help button
        :return:
        """
        if self.times_help == 0:
            self.help += "1. En este desafío no necesitas ayuda, \nes totalmente libre para que pruebes la interfaz.\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. Prueba los componentes, la conexión con el cable, el zoom, etc.\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. Trabaja y deja de jugar con la ayuda.\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        """
        Show the title and the description of the exercise
        :return: String: Text composed by title and description
        """
        return "Prueba libre\n\nEn este desafío no necesitas ayuda, es totalmente libre para que pruebes la interfaz.\n"

    def get_initial_code(self):
        """
        This is the initial code when the suer starts the callenge
        :return: String Initial code of the challenge
        """
        return "\n\nvoid setup(){\n\n}\n\nvoid loop(){\n\n}"

    def probe_robot(self, robot):
        """
        It checks the challenge: correct number of elements, code, etc.
        :param robot:
        :return:
        """
        return []

class Challenge1Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge1
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge1", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 2 LEDs rojos\n- 2 LEDs verdes\n- 2 LEDs " \
                         "amarillos\n- 6 resistencias\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. En el bucle es necesario llamar 4 veces al método delay(...)\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. Antes de cada llamada al método delay(...)\nse debe cambiar el valor " \
                         "de todos los componentes\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 1\n\nDeberá implementarse un cruce de semáforos.\nPara ello, cuando un semáforo esté en " \
               "verde, el otro estará en rojo.\nDespués de un tiempo, el semáforo que está en verde tendrá que " \
               "pasar a amarillo, y, tras unos segundos, a rojo.\nTras una breve pausa, el otro deberá de " \
               "ponerse en verde y repetir el mismo proceso.\n"

    def get_initial_code(self):
        return "int led_rojo1 = 12;\nint led_amarillo1 = 11;\nint led_verde1 = 10;\nint led_rojo2 = 9;\n" \
               "int led_amarillo2 = 8;\nint led_verde2 = 7;\nint tiempo1 = 8000;\nint tiempo2 = 3000;" \
               "\n\nvoid setup(){\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # Debe haber 12 elementos (6 leds y 6 resistencias)
        if len(robot.robot_elements) != 12:
            errors.append("El número de elementos añadidos no coincide con los correctos")
        # El número de conexiones a la placa deben ser 12
        if len(robot.board.pines) != 12:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    #no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
        # comprobamos que hay 6 resistencias y 6 leds
        if leds != 6 or resistances != 6:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors


class Challenge2Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge2
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge2", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 1 LED rojo\n- 1 LED verde\n- 2 resistencias\n- 1 " \
                         "teclado\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. En el bucle es necesario usar una operación condicional\n\n"

            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. El tiempo de espera para apagar el led será de 5000\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 2\n\nDeberá implementarse la apertura de una puerta.\nLa puerta se abre cuando " \
               "el usuario pulsa el botón A del teclado y permanece abierta durante 5 segundos,\nhaciendo " \
               "que un LED de color rojo esté encendido. Pasado ese tiempo se cierra.\nEn otros casos, " \
               "el LED verde estará iluminando para indicar que se puede pasar.\nSi el usuario vuelve a " \
               "pulsar el botón A mientras la puerta está abierta esa pulsación se ignora.\n" \
               "Si el usuario pulsa cualquier otra tecla, no debe realizar ninguna otra acción.\n"

    def get_initial_code(self):
        return "#include <Keypad.h>\n\nint led_verde = 3;\nint led_rojo = 2;\n\n" \
               "char matriz[4][4] =\n{\n  {'1','2','3', 'A'},\n" \
               "  {'4','5','6', 'B'},\n  {'7','8','9', 'C'},\n  {'*','0','#', 'D'}\n};\n\n" \
               "byte pin_rows[4] = {4, 5, 6, 7};\n\nbyte pin_columns[4] = {A0, A1, A2, A3};\n\n" \
               "Keypad keyboard = Keypad( makeKeymap(matriz), pin_rows, pin_columns, 4, 4);" \
               "\n\nvoid setup(){\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # debe haber 5 elementos (2 leds, 2 resistencias y 1 teclado)
        if len(robot.robot_elements) != 5:
            errors.append("El número de elementos añadidos no coincide con los correctos")
        # El número de conexiones a la placa deben ser 12
        if len(robot.board.pines) != 12:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        keyboards = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    # no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
            # calculamos el número de teclados añadidos
            if isinstance(component, elements.KeyBoardArduino):
                keyboards += 1
                # si es un teclado debe tener unidos los pines 1-4 a un pin digital y los pines 5-8 a un pin analógico
                if not (isinstance(component.pin1['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_digital(self, component.pin1['pin'])):
                    conex = False
                if not (isinstance(component.pin2['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_digital(self, component.pin2['pin'])):
                    conex = False
                if not (isinstance(component.pin3['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_digital(self, component.pin3['pin'])):
                    conex = False
                if not (isinstance(component.pin4['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_digital(self, component.pin4['pin'])):
                    conex = False
                if not (isinstance(component.pin5['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_analog(self, component.pin5['pin'])):
                    conex = False
                if not (isinstance(component.pin6['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_analog(self, component.pin6['pin'])):
                    conex = False
                if not (isinstance(component.pin7['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_analog(self, component.pin7['pin'])):
                    conex = False
                if not (isinstance(component.pin8['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_analog(self, component.pin8['pin'])):
                    conex = False
        # comprobamos que hay 2 leds, 2 resistencias y 1 teclado
        if leds != 2 or resistances != 2 or keyboards != 1:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors


class Challenge3Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge3
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge3", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 3 LEDs rojos" \
                         "\n- 3 resistencias\n- 1 potenciómetro\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. En el bucle es necesario tener una operación\ncondicional con 8 bloques\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. La intensidad del potenciómetro está entre 0 y 1023,\n" \
                         "por lo que las particiones serán:\n" \
                         "0-127\n128-255\n256-383\n384-511\n512-639\n640-767\n768-895\n896-1023\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 3\n\nControl y regulador de luz\nConectar 3 LEDs rojos y un potenciómetro. " \
               "En función del valor de entrada del potenciómetro Conectar 3 LEDs y un potenciómetro.\n" \
               "En función del valor de entrada del potenciómetro se tendrán que encender 0, 1, 2 o los 3 LEDs " \
               "de forma secuencial,\nempezando por el 0 y siguiendo el orden. En este caso, todos los LEDs " \
               "deben encenderse siempre con la misma intensidad,\nes decir, estarán apagados o encendidos.\n" \
               "La secuencia de encendido es: se encienda primero el A, después el B, después el C, " \
               "después A y B, después B y C,\ndespués A y C, y cuando esté en el máximo valor los 3.\n"

    def get_initial_code(self):
        return "int led1 = 4;\nint led2 = 5;\nint led3 = 6;\n\nint leds;\n\nvoid setup(){" \
               "\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # debe haber 7 elementos (3 leds, 3 resistencias y un potenciómettro)
        if len(robot.robot_elements) != 7:
            errors.append("El número de elementos añadidos no coincide con los correctos")
        # El número de conexiones a la placa deben ser 9
        if len(robot.board.pines) != 9:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        potentiometers = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    # no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
            # calculamos el número de potenciómetros añadidos
            if isinstance(component, elements.PotentiometerArduino):
                potentiometers += 1
                # si es un potenciómetro debe tener unido el pin 1 a un pin GND, el pin 2 a un pin analógico
                # y el 3 a un pin v de la placa
                if not (isinstance(component.pin1['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_gnd(self, component.pin1['pin'])):
                    conex = False
                if not (isinstance(component.pin2['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_analog(self, component.pin2['pin'])):
                    conex = False
                if not (isinstance(component.pin3['element'], boards.ArduinoUno)
                        and boards.ArduinoUno.is_v(self, component.pin3['pin'])):
                    conex = False
        # comprobamos que hay 3 resistencias, 3 leds y 1 potenciómetro
        if leds != 3 or resistances != 3 or potentiometers != 1:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors


class Challenge4Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge4
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge4", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 3 LEDs\n- 3 resistencias\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. En el bucle es necesario llamar 2 veces\nal método delay(...)\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. En el bucle será necesario llamar a la función\ndigitalWrite(...) 4 veces\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 4\n\nEn este desafío se pretende crear un sistema con 3LEDs que se enciendan y " \
               "apaguen de forma ordenada, primero el A, luego el B y finalmente el C. Una vez terminada la " \
               "secuencia, esta se repetirá de forma indefinida."

    def get_initial_code(self):
        return "int led1 = 2;\nint led2 = 3;\nint led3 = 4;\n\nvoid setup(){" \
               "\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # debe haber 6 elementos (3 leds y 3 resistencias)
        if len(robot.robot_elements) != 6:
            errors.append("El número de elementos añadidos no coincide con los correctos")
            # El número de conexiones a la placa deben ser 6
        if len(robot.board.pines) != 6:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    # no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
        # comprobamos que hay 3 resistencias y 3 leds
        if leds != 3 or resistances != 3:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors


class Challenge5Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge1
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge5", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 1 LED\n- 1 resistencia\n- 1 sensor PIR\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. Se deberá guardar el valor leído del sensor\nen una variable\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. Se pondrá un tiempo de espera\nde 50 para separar las mediciones\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 5\n\nSe debe crear un sistema que detecte movimientos.\nCuando sea así, se encenderá un " \
               "indicador LED, en caso contrario, este permanecerá apagado."

    def get_initial_code(self):
        return "int pinSensor = 2;\nint led = 4;\n\nvoid setup(){\n// Completar aquí\n}\n\n" \
               "void loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # debe haber 3 elementos (1 led, 1 sensor PIR y 1 resistencia)
        if len(robot.robot_elements) != 3:
            errors.append("El número de elementos añadidos no coincide con los correctos")
        # El número de conexiones a la placa deben ser 5
        if len(robot.board.pines) != 5:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        sensors = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    # no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
            # calculamos el número de sensores añadidos
            if isinstance(component, elements.PIRSensorArduino):
                sensors += 1
                # si es un sensor PIR debe tener el pin 1 unido a un pin GND de la placa, el pin 2 unido a un pin
                #   digital y el pin 3 a un pin v
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin2['pin']):
                        conex = False
                if isinstance(component.pin3['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_v(self, component.pin3['pin']):
                        conex = False
        # comprobamos que hay 1 resistencia, 1 led y un sensor PIR
        if leds != 1 or resistances != 1 or sensors != 1:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors


class Challenge6Robot(Robot):
    def __init__(self, robot):
        """
        Constructor for the robot of challenge1
        """
        super().__init__(boards.ArduinoUno())
        self.help = ""
        self.times_help = 0

    def get_code(self):
        code_file = open("codes/challenge6", "r")
        code = code_file.read()
        code_file.close()
        return code

    def increment_help(self):
        if self.times_help == 0:
            self.help += "1. Para este desafío necesitarás usar:\n- 1 LED\n- 1 resistencia\n" \
                         "- 1 sensor de ultrasonidos\n\n"
            self.times_help += 1
        elif self.times_help == 1:
            self.help += "2. Se deberá llamar al método\ndelayMicroseconds(...) 2 veces\n" \
                         "y al método delay(...) una\n\n"
            self.times_help += 1
        elif self.times_help == 2:
            self.help += "3. Para convertir el tiempo de espera a distancia\nse debe usar la " \
                         "siguiente conversión:\nint(0.01716*responseTime)\n\n"
            self.times_help += 1

    def get_help(self):
        self.increment_help()
        return self.help

    def get_challenge(self):
        return "Desafío 6\n\nSe debe crear un sistema que reconozca la distancia a la que se encuentra\n" \
               "un objeto. Si esta distancia es menor de 30, se encenderá un indicador LED.\nEn caso contrario, " \
               "este permanecerá apagado.\n"

    def get_initial_code(self):
        return "long distance;\nlong responseTime;\nint pinTrig = 9;\nint pinEcho = 8;\nint led = 2;\n\n" \
               "void setup(){\n// Completar aquí\n}\n\nvoid loop(){\n// Completar aquí\n}"

    def probe_robot(self, robot):
        errors = []
        # debe haber 3 elementos (1 led, 1 sensor de ultrasonidos y 1 resistencia)
        if len(robot.robot_elements) != 3:
            errors.append("El número de elementos añadidos no coincide con los correctos")
        # El número de conexiones a la placa deben ser 6
        if len(robot.board.pines) != 6:
            errors.append("El número de conexiones realizadas con la placa no es correcto")
        resistances = 0
        leds = 0
        sensors = 0
        conex = True
        for component in robot.robot_elements:
            # calculamos el número de leds añadidos
            if isinstance(component, elements.LedArduino):
                leds += 1
                # si es un led debe tener unido uno de sus pines a la resistencia. El pin 1 debe ir a un pin
                #   digital de la placa y el pin 2 a un pin gnd de esta
                if isinstance(component.pin1['element'], elements.ResistanceArduino):
                    # el pin 1 está unido a una resistencia, esta debe estar unida a un pin v de la placa
                    if not (boards.ArduinoUno.is_digital(self, component.pin1['element'].pin1['pin'])
                            or boards.ArduinoUno.is_digital(self, component.pin1['element'].pin2['pin'])):
                        conex = False
                elif isinstance(component.pin2['element'], elements.ResistanceArduino):
                    # el pin 2 está unido a una resistencia, esta debe estar unida a un pin gnd de la placa
                    if not (boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin1['pin'])
                            or boards.ArduinoUno.is_gnd(self, component.pin2['element'].pin2['pin'])):
                        conex = False
                else:
                    # no hay resistencia
                    conex = False
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
            # calculamos el número de resistencias añadidas
            if isinstance(component, elements.ResistanceArduino):
                resistances += 1
            # calculamos el número de sensores añadidos
            if isinstance(component, elements.UltrasoundSensorArduino):
                sensors += 1
                # si es un sensor de ultrasonidos, debe tener el pin 1 unido a un pin v de la placa,
                # el pin 2 unido a un pin GND y los pines 3 y 4 a pines digitales
                if isinstance(component.pin1['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_v(self, component.pin1['pin']):
                        conex = False
                if isinstance(component.pin2['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_gnd(self, component.pin2['pin']):
                        conex = False
                if isinstance(component.pin3['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin3['pin']):
                        conex = False
                if isinstance(component.pin4['element'], boards.ArduinoUno):
                    if not boards.ArduinoUno.is_digital(self, component.pin4['pin']):
                        conex = False
        # comprobamos que hay 1 resistencia, 1 led y un sensor de ultrasonidos
        if leds != 1 or resistances != 1 or sensors != 1:
            errors.append("El tipo de los elementos añadidos no coincide con los correctos")
        if not conex:
            errors.append("Las conexiones realizadas no son correctas")
        return errors

