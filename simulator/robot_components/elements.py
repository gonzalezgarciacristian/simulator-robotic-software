class Element:

    def __init__(self):
        """
        Constructor for Element
        """
        self.value = 0

    def get_value(self, pin=-1):
        """
        Gets the value (digital or analog) of the element
        Arguments:
            pin: the pin to read (only needed in case the
            element uses 2 or more pins)
        Returns:
            The value of the element
        """
        return self.value

    def set_value(self, pin, value):
        """
        Writes a value into an element
        Arguments:
            pin: the pin to write (only needed in case the
            element uses 2 or more pins)
            value: the value to write
        """
        self.value = value

    def get_pulse(self, pin, value):
        """
        Reads a pulse value from a pin
        Arguments:
            pin: the pin to read from
            value: the value to read
        Returns:
            The read value or None if none read
        """
        return None


class Servo(Element):

    def __init__(self):
        """
        Constructor for servo class.
        The servo will be rotational.
        """
        self.pin = -1
        self.min = 544  # default arduino value
        self.max = 2400  # default arduino value
        self.value = 90  # stopped (180 and 0 full speed)

    def set_value(self, pin, value):
        """
        Writes speed to servo.
        Arguments:
            angle: the value to write [0-180]
        Returns:
            True if updated, False if else
        """
        if 0 <= value <= 180:
            super().set_value(pin, value)
            return True
        return False

    def get_pin_type(self):
        """
        Returns connection type needed for the pin
        """
        return "digital"


class ArmJointServo(Servo):

    def __init__(self):
        super().__init__()
        self.value = 0.0
        self.command_mode = "position"
        self.pulse_value = None
        self.pulse_min = self.min
        self.pulse_max = self.max

    def set_value(self, pin, value):
        """
        Guarda directamente el valor articular del brazo en grados DH/mm.
        El clamping real se aplica después en el modelo cinemático.
        """
        try:
            Element.set_value(self, pin, float(value))
            self.command_mode = "velocity"
            self.pulse_value = None
            return True
        except (TypeError, ValueError):
            return False

    def set_position_value(self, value):
        """Sincroniza una posicion del modelo sin marcarla como sketch."""
        try:
            Element.set_value(self, self.pin, float(value))
            self.command_mode = "position"
            self.pulse_value = None
            return True
        except (TypeError, ValueError):
            return False

    def set_pulse_value(self, pin, pulse, pulse_min=None, pulse_max=None, angle=None):
        """Guarda un pulso PWM real y conserva el angulo equivalente para read()."""
        try:
            pulse = float(pulse)
            pulse_min = float(self.min if pulse_min is None else pulse_min)
            pulse_max = float(self.max if pulse_max is None else pulse_max)
            if pulse_max <= pulse_min:
                return False
            if angle is None:
                angle = (pulse - pulse_min) * 180.0 / (pulse_max - pulse_min)
            Element.set_value(self, pin, float(angle))
            self.command_mode = "pulse"
            self.pulse_value = pulse
            self.pulse_min = pulse_min
            self.pulse_max = pulse_max
            return True
        except (TypeError, ValueError):
            return False


class Button(Element):

    def __init__(self):
        """
        Constructor for button
        """
        self.pin = -1
        self.value = 1

    def set_value(self, pin, value):
        if value == 1 or value == 0:
            super().set_value(pin, value)
            return True
        return False

    def get_pin_type(self):
        """
        Returns connection type needed for the pin
        """
        return "digital"


class Joystick(Element):

    def __init__(self):
        """
        Constructor for joystick
        """
        self.pinx = -1
        self.piny = -1
        self.pinb = -1
        self.dx = 500
        self.dy = 500
        self.value = 1

    def get_value(self, pin):
        """
        Gets the analog value of the selected pin
        Arguments:
            pin: the pin to read
        Returns:
            The value of the pin
        """
        if pin == self.pinx:
            return self.dx
        elif pin == self.piny:
            return self.dy
        elif pin == self.pinb:
            return self.value
        else:
            return None

    def set_value(self, pin, value):
        if 0 <= value <= 1023:
            if pin == self.pinx:
                self.dx = value
            elif pin == self.piny:
                self.dy = value
            elif pin == self.pinb:
                self.value = value
            else:
                return False
            return True
        return False

    def get_button_pin_type(self):
        """
        Returns connection type needed for the button pin
        """
        return "digital"

    def get_x_pin_type(self):
        """
        Returns connection type needed for the x pin
        """
        return "analog"

    def get_y_pin_type(self):
        """
        Returns connection type needed for the y pin
        """
        return "analog"


class LightSensor(Element):

    def __init__(self):
        """
        Constructor for Light sensor
        """
        self.pin = -1
        self.value = 0

    def set_value(self, pin, value):
        if value == 1 or value == 0:
            super().set_value(pin, value)
            return True
        return False

    def get_pin_type(self):
        """
        Returns connection type needed for the pin
        """
        return "digital"


class UltrasoundSensor(Element):

    def __init__(self):
        """
        Constructor for Ultrasound sensor
        """
        self.pin_trig = -1
        self.pin_echo = -1
        self.value = 0
        self.dist = -1

    def set_value(self, pin, value):
        if pin == self.pin_trig:
            if value == 1 or value == 0:
                super().set_value(pin, value)
                return True
        return False

    def get_pulse(self, pin, value):
        if pin == self.pin_echo:
            return self.dist
        return None

    def get_echo_pin_type(self):
        """
        Returns the type of the connection needed for the echo
        pin
        """
        return "digital"

    def get_trig_pin_type(self):
        """
        Returns the type of the connection needed for the trig
        pin
        """
        return "digital"


class ResistanceArduino(Element):
    def __init__(self):
        """
        Constructor for resistance
        A resistance has two pins and a value
        """
        self.name = "Resistencia"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.value = 10

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "both"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "both"

    def set_value(self, value):
        self.value = value

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component

    def draw_self(self, x, y, number):
        if self.value == 56000:
            value = ""
        elif self.value == 220:
            value = "220"
        elif self.value == 10000:
            value = "10k"
        image = {
            "x": x,
            "y": y,
            "image": "assets/resistance" + value + ".png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x,
            "y": y - 55
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 55
        }
        return [button1, button2]


class ButtonArduino(Element):
    def __init__(self):
        """
        Constructor for button
        A button has four pins and a state
        """
        self.name = "Botón"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.pin4 = {
            "element": None,
            "pin": -1
        }
        self.state = True

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "both"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "both"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "both"

    def get_pin4_type(self):
        """
        Returns connection type needed for the pin4
        """
        return "both"

    def open(self):
        """Open the button"""
        self.state = False

    def close(self):
        """Close the button"""
        self.state = True

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3", "pin4"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component
        if pin == 4:
            self.pin4['element'] = component_to_attach
            self.pin4['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/button.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 25,
            "y": y - 60
        }
        button2 = {
            "n_pin": 2,
            "x": x + 25,
            "y": y - 60
        }
        button3 = {
            "n_pin": 3,
            "x": x - 25,
            "y": y + 60
        }
        button4 = {
            "n_pin": 4,
            "x": x + 25,
            "y": y + 60
        }
        return [button1, button2, button3, button4]


class PotentiometerArduino(Element):
    def __init__(self):
        """
        Constructor for potentiometer
        A potentiometer has three pins and a value
        """
        self.name = "Potenciómetro"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.value = 100

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "both"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "both"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "both"

    def set_value(self, value):
        """The value must be between 0 and 100"""
        if 0 <= value <= 100:
            self.value = value

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/potentiometer.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 31,
            "y": y + 56
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 64
        }
        button3 = {
            "n_pin": 3,
            "x": x + 30,
            "y": y + 56
        }
        return [button1, button2, button3]


class LedArduino(Element):
    def __init__(self):
        """
        Constructor for LED
        A LED has two pins, a state and a color
        - Color: 1 for red, 2 for yellow and 3 for green
            In future expansions, more colors could be added
        """
        self.name = "Led rojo"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.state = False
        self.color = 1

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "both"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "both"

    def set_on(self):
        """Turns on the LED"""
        self.state = True

    def set_off(self):
        """Turns off the LED"""
        self.state = False

    def set_color(self, color):
        """For now there are only three colors"""
        if color == 1:
            self.color = color
            self.name = "Led rojo"
        elif color == 2:
            self.color = color
            self.name = "Led Ámbar"
        elif color == 3:
            self.color = color
            self.name = "Led Verde"

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component

    def draw_self(self, x, y, number):
        if self.color == 1:
            color = ""
        elif self.color == 2:
            color = "Yellow"
        elif self.color == 3:
            color = "Green"
        image = {
            "x": x,
            "y": y,
            "image": "assets/led" + color + ".png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 15,
            "y": y + 60
        }
        button2 = {
            "n_pin": 2,
            "x": x + 5,
            "y": y + 50
        }
        return [button1, button2]


class BuzzerArduino(Element):
    def __init__(self):
        """
        Constructor for buzzer
        A buzzer has three pins and a state
        """
        self.name = "Buzzer"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.state = False

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "both"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "both"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "both"

    def set_on(self):
        """Turns on the buzzer"""
        self.state = True

    def set_off(self):
        """Turns off the buzzer"""
        self.state = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/buzzer.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 20,
            "y": y + 90
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 90
        }
        button3 = {
            "n_pin": 3,
            "x": x + 20,
            "y": y + 90
        }
        return [button1, button2, button3]


class RGBArduino(Element):
    def __init__(self):
        """
        Constructor for LED RGB
        A LED RGB has four pins and a value
        """
        self.name = "Led RGB"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.pin4 = {
            "element": None,
            "pin": -1
        }
        self.value = 1

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def get_pin4_type(self):
        """
        Returns connection type needed for the pin4
        """
        return "both"

    def set_value(self, value):
        """Sets the value of the LED to a certain value"""
        self.value = value

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3", "pin4"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component
        if pin == 4:
            self.pin4['element'] = component_to_attach
            self.pin4['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/ledRGB.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 20,
            "y": y + 50
        }
        button2 = {
            "n_pin": 2,
            "x": x - 8,
            "y": y + 70
        }
        button3 = {
            "n_pin": 3,
            "x": x + 5,
            "y": y + 60
        }
        button4 = {
            "n_pin": 4,
            "x": x + 17,
            "y": y + 48
        }
        return [button1, button2, button3, button4]


class LightSensorArduino(Element):
    def __init__(self):
        """
        Constructor for Light Sensor
        A Light sensor has three pins and a sensor
        """
        self.name = "Sensor de luz"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.sensor = False

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "analog"

    def set_sensor_on(self):
        """Turns the sensor on"""
        self.sensor = True

    def set_sensor_off(self):
        """Turns the sensor off"""
        self.sensor = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/lightSensor.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 22,
            "y": y + 60
        }
        button2 = {
            "n_pin": 2,
            "x": x - 2,
            "y": y + 60
        }
        button3 = {
            "n_pin": 3,
            "x": x + 17,
            "y": y + 60
        }
        return [button1, button2, button3]


class PIRSensorArduino(Element):
    def __init__(self):
        """
        Constructor for PIR Sensor
        A PIR sensor has three pins and a sensor
        """
        self.name = "Sensor PIR"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.sensor = False

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def set_sensor_on(self):
        """Turns the sensor on"""
        self.sensor = True

    def set_sensor_off(self):
        """Turns the sensor off"""
        self.sensor = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/PIRSensor.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x-25,
            "y": y + 60
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 60
        }
        button3 = {
            "n_pin": 3,
            "x": x + 25,
            "y": y + 60
        }
        return [button1, button2, button3]


class VibrationSensorArduino(Element):
    def __init__(self):
        """
        Constructor for Vibration Sensor
        A Vibration sensor has three pins and a sensor
        """
        self.name = "Sensor de vibración"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.sensor = True

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def set_sensor_on(self):
        """Turns the sensor on"""
        self.sensor = True

    def set_sensor_off(self):
        """Turns the sensor off"""
        self.sensor = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/VibrationSensor.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 17,
            "y": y + 110
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 110
        }
        button3 = {
            "n_pin": 3,
            "x": x + 17,
            "y": y + 110
        }
        return [button1, button2, button3]


class InfraredSensorArduino(Element):
    def __init__(self):
        """
        Constructor for Infrared Sensor
        An Infrared sensor has three pins and a sensor
        """
        self.name = "Sensor de infrarrojos"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.sensor = True

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def set_sensor_on(self):
        """Turns the sensor on"""
        self.sensor = True

    def set_sensor_off(self):
        """Turns the sensor off"""
        self.sensor = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/infraredSensor.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 20,
            "y": y + 110
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 110
        }
        button3 = {
            "n_pin": 3,
            "x": x + 20,
            "y": y + 110
        }
        return [button1, button2, button3]


class UltrasoundSensorArduino(Element):
    def __init__(self):
        """
        Constructor for Ultrasound Sensor
        An Ultrasound sensor has four pins and a sensor
        """
        self.name = "Sensor de ultrasonidos"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.pin4 = {
            "element": None,
            "pin": -1
        }
        self.sensor = True

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def get_pin4_type(self):
        """
        Returns connection type needed for the pin4
        """
        return "digital"

    def set_sensor_on(self):
        """Turns the sensor on"""
        self.sensor = True

    def set_sensor_off(self):
        """Turns the sensor off"""
        self.sensor = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3", "pin4"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component
        if pin == 4:
            self.pin4['element'] = component_to_attach
            self.pin4['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/ultrasonicSensor.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 22,
            "y": y + 50
        }
        button2 = {
            "n_pin": 2,
            "x": x - 8,
            "y": y + 50
        }
        button3 = {
            "n_pin": 3,
            "x": x + 6,
            "y": y + 50
        }
        button4 = {
            "n_pin": 4,
            "x": x + 20,
            "y": y + 50
        }
        return [button1, button2, button3, button4]


class KeyBoardArduino(Element):
    def __init__(self):
        """
        Constructor for keyboard
        A keyboard has eight pins
        """
        self.name = "Teclado"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.pin4 = {
            "element": None,
            "pin": -1
        }
        self.pin5 = {
            "element": None,
            "pin": -1
        }
        self.pin6 = {
            "element": None,
            "pin": -1
        }
        self.pin7 = {
            "element": None,
            "pin": -1
        }
        self.pin8 = {
            "element": None,
            "pin": -1
        }

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def get_pin4_type(self):
        """
        Returns connection type needed for the pin4
        """
        return "digital"

    def get_pin5_type(self):
        """
        Returns connection type needed for the pin5
        """
        return "digital"

    def get_pin6_type(self):
        """
        Returns connection type needed for the pin6
        """
        return "digital"

    def get_pin7_type(self):
        """
        Returns connection type needed for the pin7
        """
        return "digital"

    def get_pin8_type(self):
        """
        Returns connection type needed for the pin8
        """
        return "digital"

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3", "pin4", "pin5", "pin6", "pin7", "pin8"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component
        if pin == 4:
            self.pin4['element'] = component_to_attach
            self.pin4['pin'] = pin_component
        if pin == 5:
            self.pin5['element'] = component_to_attach
            self.pin5['pin'] = pin_component
        if pin == 6:
            self.pin6['element'] = component_to_attach
            self.pin6['pin'] = pin_component
        if pin == 7:
            self.pin7['element'] = component_to_attach
            self.pin7['pin'] = pin_component
        if pin == 8:
            self.pin8['element'] = component_to_attach
            self.pin8['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/keyBoard.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 130,
            "y": y + 185
        }
        button2 = {
            "n_pin": 2,
            "x": x - 90,
            "y": y + 185
        }
        button3 = {
            "n_pin": 3,
            "x": x - 60,
            "y": y + 185
        }
        button4 = {
            "n_pin": 4,
            "x": x - 20,
            "y": y + 185
        }
        button5 = {
            "n_pin": 5,
            "x": x + 20,
            "y": y + 185
        }
        button6 = {
            "n_pin": 6,
            "x": x + 60,
            "y": y + 185
        }
        button7 = {
            "n_pin": 7,
            "x": x + 95,
            "y": y + 185
        }
        button8 = {
            "n_pin": 8,
            "x": x + 130,
            "y": y + 185
        }
        return [button1, button2, button3, button4, button5, button6, button7, button8]


class ScreenArduino(Element):
    def __init__(self):
        """
        Constructor for Screen
        A screen has four pins
        """
        self.name = "Pantalla"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.pin4 = {
            "element": None,
            "pin": -1
        }

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def get_pin4_type(self):
        """
        Returns connection type needed for the pin4
        """
        return "digital"

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3", "pin4"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component
        if pin == 4:
            self.pin4['element'] = component_to_attach
            self.pin4['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/screen.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 170,
            "y": y - 27
        }
        button2 = {
            "n_pin": 2,
            "x": x - 170,
            "y": y - 10
        }
        button3 = {
            "n_pin": 3,
            "x": x - 170,
            "y": y + 8
        }
        button4 = {
            "n_pin": 4,
            "x": x - 170,
            "y": y + 25
        }
        return [button1, button2, button3, button4]


class ServomotorArduino(Element):
    def __init__(self):
        """
        Constructor for servomotor
        A servomotor has three pins and a state
        """
        self.name = "Servomotor"
        self.pin1 = {
            "element": None,
            "pin": -1
        }
        self.pin2 = {
            "element": None,
            "pin": -1
        }
        self.pin3 = {
            "element": None,
            "pin": -1
        }
        self.state = False

    def get_pin1_type(self):
        """
        Returns connection type needed for the pin1
        """
        return "digital"

    def get_pin2_type(self):
        """
        Returns connection type needed for the pin2
        """
        return "digital"

    def get_pin3_type(self):
        """
        Returns connection type needed for the pin3
        """
        return "digital"

    def set_on(self):
        """Turns on the servomotor"""
        self.state = True

    def set_off(self):
        """Turns off the servomotor"""
        self.state = False

    def get_pines(self):
        """Returns the pins of the element"""
        return ["pin1", "pin2", "pin3"]

    def attach_element(self, pin, component_to_attach, pin_component):
        if pin == 1:
            self.pin1['element'] = component_to_attach
            self.pin1['pin'] = pin_component
        if pin == 2:
            self.pin2['element'] = component_to_attach
            self.pin2['pin'] = pin_component
        if pin == 3:
            self.pin3['element'] = component_to_attach
            self.pin3['pin'] = pin_component

    def draw_self(self, x, y, number):
        image = {
            "x": x,
            "y": y,
            "image": "assets/servomotor180.png",
            "group": "component" + str(number),
            "element": self
        }
        return image

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": 1,
            "x": x - 20,
            "y": y + 91
        }
        button2 = {
            "n_pin": 2,
            "x": x,
            "y": y + 91
        }
        button3 = {
            "n_pin": 3,
            "x": x + 20,
            "y": y + 91
        }
        return [button1, button2, button3]
