import robot_components.boards as boards


def get_name():
    return "Servo"


def get_methods():
    """
    Returns the methods of the library as a dict, whose
    key is the naming in Arduino and whose value is the
    corresponding method.
    Returns:
        A dict with the methods
    """
    methods = {}
    methods["attach"] = ("void", "attach", ['int', '(int)', '(int)'], -1)
    methods["write"] = ("void", "write", ['int'], -1)
    methods["writeMicroseconds"] = ("void", "write_microseconds", ['int'], -1)
    methods["read"] = ("int", "read", [], -1)
    methods["attached"] = ("bool", "attached", [], -1)
    methods["detach"] = ("void", "detach", [], -1)
    return methods


def get_not_implemented():
    return []


class Servo:
    """
    Servo class, represents the movement of a real servo
    """

    OK = 0
    ERROR = -1
    NOT_IMPL_WARNING = -2

    def __init__(self, board=None, name=None):
        """
        Constructor for Servo class
        """
        self.board = board
        self.servo = None
        self.instance_name = name
        self.min = 544
        self.max = 2400
        self.speed = 90

    def set_board(self, board: boards.Board):
        """
        Sets the board that the robot is using
        """
        self.board = board

    def attach(self, pin, min=544, max=2400):
        """
        Attaches the servo to a pin
        Arguments:
            servo: the servo to attach
            pin: the number of the pin to be attached to
            min: pulse width corresponging with the minimun angle on
            the servo (default = 544)
            max: pulse width corresponging with the max angel on the
            the servo (default = 2400)
        Returns:
            OK if servo attached to pin correctly, ERROR if else
        """
        servo = None
        if self.board is not None:
            servo = self.board.get_pin_element(pin)
            if servo is None:
                arm_robot = getattr(self.board, "arm_robot", None)
                if arm_robot is not None:
                    servo = arm_robot.attach_servo_to_pin(pin, self.instance_name)
        if servo is not None:
            self.servo = servo
            self.min = min
            self.max = max
            servo.min = min
            servo.max = max
            return self.OK
        return self.ERROR

    def write(self, angle):
        """
        Writes speed/position to servo, replicando Servo::write() de Arduino.

        Arduino trata los valores por debajo de MIN_PULSE_WIDTH (544) como
        ángulos [0-180] y los mapea al rango de pulso configurado en attach()
        [min, max]; los valores >= 544 se interpretan directamente como
        microsegundos. En ambos casos delega en writeMicroseconds(), de modo
        que write() y writeMicroseconds() comparten el mismo camino (y así
        write(180) alcanza el extremo físico del servo, como en el hardware).
        Arguments:
            servo: the servo to write to
            angle: the value to write [0-180] (o microsegundos si es >= 544)
        """
        if self.servo is not None:
            try:
                value = int(float(angle))
            except (TypeError, ValueError):
                return
            if value < 544:
                value = max(0, min(180, value))
                value = self.min + value * (self.max - self.min) // 180
            self.write_microseconds(value)

    def write_microseconds(self, us):
        """
        Writes a pulse width to the servo.

        Arduino Servo clamps writeMicroseconds() to the attached pulse range.
        Arm joints keep the raw pulse so the 3D model can map it to the
        configured physical joint range; regular servo elements keep the
        equivalent 0..180 value used by Servo.read().
        Arguments:
            servo: the servo to write to
            us: the value of the parameter in microseconds (int)
        """
        if self.servo is not None:
            try:
                pulse = int(float(us))
            except (TypeError, ValueError):
                return self.ERROR

            pulse_min = int(getattr(self.servo, "min", self.min))
            pulse_max = int(getattr(self.servo, "max", self.max))
            if pulse_max <= pulse_min:
                return self.ERROR

            clamped = max(pulse_min, min(pulse_max, pulse))
            angle = (clamped + 1 - pulse_min) * 180 // (pulse_max - pulse_min)
            angle = max(0, min(180, angle))
            if hasattr(self.servo, "set_pulse_value"):
                if not self.servo.set_pulse_value(
                    self.servo.pin, clamped, pulse_min, pulse_max, angle
                ):
                    return self.ERROR
            elif hasattr(self.servo, "set_value"):
                self.servo.set_value(self.servo.pin, angle)
            else:
                self.servo.value = angle
            return self.OK
        return self.ERROR

    def read(self):
        """
        Reads the angle of the servo (being the last value passed to write)
        Arguments:
            The servo to read from
        Returns:
            The angle of the servo from 0 to 180 degrees
        """
        if self.servo is not None:
            return self.servo.value
        return None

    def attached(self):
        """
        Checks wether the Servo variable is attached or not
        Arguments:
            servo: the servo to check
        Returns:
            True if attached to pin, False if else
        """
        if self.servo is not None:
            return self.servo.pin != -1
        return False

    def detach(self):
        """
        Detach the Servo variable from its pin
        Arguments:
            servo: the servo to detach
        """
        if self.servo is not None:
            arm_robot = getattr(self.board, "arm_robot", None) if self.board is not None else None
            if arm_robot is not None:
                arm_robot.detach_servo(self.servo)
            elif self.board is not None and self.servo.pin != -1:
                self.board.detach_pin(self.servo.pin)
                self.servo.pin = -1
            self.servo = None
            return self.OK
        return self.ERROR
