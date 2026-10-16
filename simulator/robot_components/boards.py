class Board:
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2

    def __init__(self):
        """
        Constructor for Arduino board
        """
        self.pins = {}
        self.used_pins = {}

    def get_pin_element(self, pin):
        """
        Gets the element attached to a pin
        Arguments:
            pin: the pin from which we want to get the element
        Returns:
            The element attached to the pin or None if there is none
            attached
        """
        if pin in self.used_pins:
            return self.used_pins[pin]["element"]
        return None

    def get_digital_pins(self):
        """
        Returns:
            The list of digital pins of the board
        """
        return self.pins["digital"]

    def get_analog_pins(self):
        """
        Returns:
            The list of analog pins of the board
        """
        return self.pins["analog"]

    def get_txrx_pins(self):
        """
        Returns:
            The list of txrx pins of the board
        """
        return self.pins["txrx"]

    def check_type(self, pin, type):
        """
        Checks if a pin is of the requested type
        Arguments:
            pin: the pin to check
            type: the requested type
        Returns:
            True if it is of the type, False if else
        """
        if type == "both":
            return True
        if type == "digital":
            return self.is_digital(pin)
        elif type == "analog":
            return self.is_analog(pin)
        elif type == "txrx":
            return self.is_txrx(pin)
        return False

    def is_digital(self, pin):
        """
        Checks if the pin is digital or not. The tx rx pins
        are considered as digital. However, the compiler
        must check if serial is being used, if not it would
        be executing wrong code.
        Arguments:
            pin: the pin to check if is digital
        Returns:
            True if is digital, False if else
        """
        return pin in self.pins["digital"] or pin in self.pins["txrx"]

    def is_analog(self, pin):
        """
        Checks if the pin is analog or not.
        Arguments:
            pin: the pin to check if is analog
        Returns:
            True if is analog, False if else
        """
        return pin in self.pins["analog"]

    def is_txrx(self, pin):
        """
        Checks if the pin is tx/rx or not.
        Arguments:
            pin: the pin to check if is tx/rx
        Returns:
            True if is tx/rx, False if else
        """
        return pin in self.pins["txrx"]

    def attach_pin(self, pin, elem):
        """
        Attaches a element to a pin
        Arguments:
            pin: the used pin
            elem: the elem to attach
        Returns:
            True if attached, False if else
        """
        if (
                pin in self.pins["analog"]
                or pin in self.pins["digital"]
                or pin in self.pins["txrx"]
        ) and pin not in self.used_pins:
            self.used_pins[pin] = {
                "element": elem,
                "mode": self.INPUT
            }
            return True
        return False

    def detach_pin(self, pin):
        """
        Detaches a element from a pin
        Arguments:
            pin: the pin to detach
        Returns:
            True if detached, False if else
        """
        if pin in self.used_pins:
            del self.used_pins[pin]
            return True
        return False

    def read(self, pin):
        """
        Reads the value of the elements
        Arguments:
            pin: the pin to read
        Returns:
            The value of the output or None if pin not input
        """
        if self.__is_used_pin(pin):
            if self.used_pins[pin]["mode"] == self.INPUT or self.used_pins[pin]["mode"] == self.INPUT_PULLUP:
                return self.used_pins[pin]["element"].get_value(pin)
        return None

    def read_pulse(self, pin, value):
        """
        Reads a pulse from a pin
        Arguments:
            pin: the pin to read the pulse from
            value: the value (0 or 1) to read
        Returns:
            The value or None if no value
        """
        if self.__is_used_pin(pin):
            if self.used_pins[pin]["mode"] == self.INPUT:
                return self.used_pins[pin]["element"].get_pulse(pin)
        return None

    def write_value(self, pin, value):
        """
        Writes value to element
        Arguments:
            pin: the pin of the element to write
            value: the value to write
        Returns:
            True if operation done, False if else
        """
        if self.__is_used_pin(pin):
            if self.used_pins[pin]["mode"] == self.OUTPUT:
                self.used_pins[pin]["element"].set_value(value)
                return True
        return False

    def set_pin_mode(self, pin, mode):
        """
        Changes pin's mode
        Arguments:
            pin: the pin whose mode will be changed
            mode: the mode to use
        Returns:
            True if operation done, False if else
        """
        if self.__is_used_pin(pin):
            self.used_pins[pin]["mode"] = mode
            return True
        return False

    def __is_used_pin(self, pin):
        """
        Checks if a pin is being used
        Arguments:
            pin: the pin to check
        Returns:
            True if used, False if else
        """
        return pin in self.used_pins


class ArduinoUno(Board):

    def __init__(self):
        """
        Constructor for Arduino Uno board.
        Includes the following pins as stated at:
        https://docs.arduino.cc/tutorials/uno-rev3/intro-to-board
        - Pins 2-13 are digital
        - Pins A0-A5 are analog
        - Pins 0 and 1 are tx/rx (no digital i/o if also using serial
        communication)
        """
        super().__init__()
        self.name = "Placa arduino"
        self.pins["digital"] = list(map(lambda x: x, range(2, 14)))
        self.pins["analog"] = list(map(lambda x: x, range(14, 20)))
        self.pins["txrx"] = [0, 1]
        self.pins["v"] = [20, 21]
        self.pins["gnd"] = [22, 23, 24]
        self.pines = []

    def is_txrx(self, pin):
        if pin == 0 or pin == 1:
            return True
        return False

    def is_analog(self, pin):
        if 14 <= pin < 20:
            return True
        return False

    def is_digital(self, pin):
        if 2 <= pin < 14:
            return True
        return False

    def is_v(self, pin):
        if pin == 20 or pin == 21:
            return True
        return False

    def is_gnd(self, pin):
        if 22 <= pin < 25:
            return True
        return False

    def attach_pin(self, pin, component):
        att_pin = {
            "element": component,
            "pin": pin
        }
        self.pines.append(att_pin)
        # Además de registrar el pin para el dibujo de la placa (self.pines), hay que
        # registrarlo en used_pins (como el resto de placas) para que la asignación de
        # pines del robot tenga efecto y digitalRead/analogRead (board.read) lo lea.
        return super().attach_pin(pin, component)

    def draw_buttons(self, x, y):
        button1 = {
            "n_pin": "pin0",
            "x": x + 197,
            "y": y - 150
        }
        button2 = {
            "n_pin": "pin1",
            "x": x + 181,
            "y": y - 150
        }
        button3 = {
            "n_pin": "pin2",
            "x": x + 165,
            "y": y - 150
        }
        button4 = {
            "n_pin": "pin3",
            "x": x + 149,
            "y": y - 150
        }
        button5 = {
            "n_pin": "pin4",
            "x": x + 133,
            "y": y - 150
        }
        button6 = {
            "n_pin": "pin5",
            "x": x + 117,
            "y": y - 150
        }
        button7 = {
            "n_pin": "pin6",
            "x": x + 101,
            "y": y - 150
        }
        button8 = {
            "n_pin": "pin7",
            "x": x + 85,
            "y": y - 150
        }
        button9 = {
            "n_pin": "pin8",
            "x": x + 62,
            "y": y - 150
        }
        button10 = {
            "n_pin": "pin9",
            "x": x + 46,
            "y": y - 150
        }
        button11 = {
            "n_pin": "pin10",
            "x": x + 30,
            "y": y - 150
        }
        button12 = {
            "n_pin": "pin11",
            "x": x + 14,
            "y": y - 150
        }
        button13 = {
            "n_pin": "pin12",
            "x": x - 2,
            "y": y - 150
        }
        button14 = {
            "n_pin": "pin13",
            "x": x - 18,
            "y": y - 150
        }
        button15 = {
            "n_pin": "pinA0",
            "x": x + 119,
            "y": y + 150
        }
        button16 = {
            "n_pin": "pinA1",
            "x": x + 135,
            "y": y + 150
        }
        button17 = {
            "n_pin": "pinA2",
            "x": x + 151,
            "y": y + 150
        }
        button18 = {
            "n_pin": "pinA3",
            "x": x + 167,
            "y": y + 150
        }
        button19 = {
            "n_pin": "pinA4",
            "x": x + 183,
            "y": y + 150
        }
        button20 = {
            "n_pin": "pinA5",
            "x": x + 199,
            "y": y + 150
        }
        button21 = {
            "n_pin": "pin3V",
            "x": x + 24,
            "y": y + 150
        }
        button22 = {
            "n_pin": "pin5V",
            "x": x + 40,
            "y": y + 150
        }
        button23 = {
            "n_pin": "pinGND1",
            "x": x + 56,
            "y": y + 150
        }
        button24 = {
            "n_pin": "pinGND2",
            "x": x + 72,
            "y": y + 150
        }
        button25 = {
            "n_pin": "pinGND3",
            "x": x - 34,
            "y": y - 150
        }
        return [button1, button2, button3, button4, button5, button6, button7, button8, button9,
                button10, button11, button12, button13, button14, button15, button16, button17,
                button18, button19, button20, button21, button22, button23, button24, button25]


class BQzumBT328(Board):

    def __init__(self):
        """
        Constructor for Arduino Uno board.
        Includes the following pins as stated at:
        https://aiglesias.com/?p=7314 (Spanish)
        - Pins 2-13 are digital
        - Pins A0-A5 are analog
        - Pins 0 and 1 are tx/rx (no digital i/o if also using serial
        communication)
        """
        super().__init__()
        self.pins["digital"] = list(map(lambda x: x, range(2, 14)))
        self.pins["analog"] = list(map(lambda x: x, range(14, 20)))
        self.pins["txrx"] = [0, 1]
