"""
Standard Arduino library. Includes the methods pressent
at: https://www.arduino.cc/reference/en/
"""

import builtins
import string
import time
import threading
import random as ran
from math import cos, sin, sqrt, tan
import robot_components.boards as boards
import robot_components.robot_state as robot_state
import graphics.screen_updater as screen_updater

# Evento global que interrumpe delay()/delayMicroseconds() cuando se detiene la ejecución.
# Loop.reboot() lo activa; Loop.execute() lo limpia antes de arrancar el hilo nuevo.
_stop_event = threading.Event()
_watchdog_local = threading.local()

# Limita la CPU consumida por sketches que giran sin delay() ni esperas cooperativas.
_WATCHDOG_TIME_SLICE_NS = 8_000_000
_WATCHDOG_IDLE_SLEEP_S = 0.001
_WATCHDOG_CHECK_EVERY = 128
_WATCHDOG_CHECK_MASK = _WATCHDOG_CHECK_EVERY - 1

HIGH = 1
LOW = 0

INPUT = "INPUT"
OUTPUT = "OUTPUT"
INPUT_PULLUP = "INPUT_PULLUP"

OK = 0
ERROR = -1
NOT_IMPL_WARNING = -2

board: boards.Board = None
state: robot_state.State = None
start = time.time()


class ExecutionInterrupted(Exception):
    """Parada cooperativa solicitada por stop/reset del simulador."""
    pass


class Ref:
    """Contenedor mutable para simular parametros C/C++ pasados por referencia."""

    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)


def reset_runtime_watchdog():
    """Reinicia el estado local del watchdog para el hilo actual."""
    _watchdog_local.spin_count = 0
    _watchdog_local.last_pause_ns = time.perf_counter_ns()


def note_runtime_blocking():
    """Marca que el sketch acaba de ceder CPU mediante una espera real."""
    reset_runtime_watchdog()


def runtime_watchdog_checkpoint():
    """Punto cooperativo de seguridad insertado en el código transpilado."""
    if _stop_event.is_set():
        raise ExecutionInterrupted()

    spin_count = getattr(_watchdog_local, "spin_count", 0) + 1
    _watchdog_local.spin_count = spin_count

    if spin_count & _WATCHDOG_CHECK_MASK:
        return

    now = time.perf_counter_ns()
    last_pause_ns = getattr(_watchdog_local, "last_pause_ns", now)
    if now - last_pause_ns < _WATCHDOG_TIME_SLICE_NS:
        return

    if threading.current_thread() is threading.main_thread():
        screen_updater.refresh()
        time.sleep(0)
    else:
        time.sleep(_WATCHDOG_IDLE_SLEEP_S)

    reset_runtime_watchdog()

    if _stop_event.is_set():
        raise ExecutionInterrupted()


def get_name():
    return "Standard"


def get_methods():
    """
    Returns the methods of the library as a dict, whose
    key is the naming in Arduino and whose value is the
    corresponding method.
    Returns:
        A dict with the methods
    """
    methods = {}
    # Digital I/O
    methods["digitalRead"] = ("int", "digital_read", ["int"], -1)
    methods["digitalWrite"] = ("void", "digital_write", ["int", "int"], -1)
    methods["pinMode"] = ("void", "pin_mode", ["int", "int"], -1)

    # Analog I/O
    methods["analogRead"] = ("int", "analog_read", ["int"], -1)
    methods["analogReference"] = (
        "void", "analog_reference", [], -1)  # Not implemented
    methods["analogWrite"] = ("void", "analog_write", ["int", "int"], -1)

    # Zero, Due & MKR Family
    methods["analogReadResolution"] = (
        "void", "analog_read_resolution", [], -1)  # Not implemented
    methods["analogWriteResolution"] = (
        "void", "analog_write_resolution", [], -1)  # Not implemented

    # Advanced I/O
    methods["noTone"] = ("void", "no_tone", [], -1)  # Not implemented
    methods["pulseIn"] = ("long", "pulse_in", ["int", "int"], -1)
    methods["pulseInLong"] = ("long", "pulse_in_long",
                              [], -1)  # Not implemented
    methods["shiftIn"] = ("byte", "shift_in", [], -1)  # Not implemented
    methods["shiftOut"] = ("void", "shift_out", [], -1)  # Not implemented
    methods["tone"] = ("void", "tone", [], -1)  # Not implemented

    # Time
    methods["delay"] = ("void", "delay", ["long"], -1)
    methods["delayMicroseconds"] = ("void", "delay_microseconds", ["uint"], -1)
    methods["micros"] = ("ulong", "micros", [], -1)
    methods["millis"] = ("ulong", "millis", [], -1)

    # Math
    methods["abs"] = ("double", "abs", ["int"], -1)
    methods["constrain"] = ("double", "constrain", [
                            "double", "double", "double"], -1)
    methods["F"] = ("string", "F", ["string"], -1)
    methods["map"] = ("int", "map", ["int", "int", "int", "int", "int"], -1)
    methods["max"] = ("double", "max", ["double", "double"], -1)
    methods["min"] = ("double", "min", ["double", "double"], -1)
    methods["pow"] = ("double", "pow", ["float", "float"], -1)
    methods["sizeof"] = ("int", "sizeof", ["any"], -1)
    methods["sq"] = ("double", "sq", ["double"], -1)
    methods["strtol"] = ("long", "strtol", ["any", "ref", "int"], -1)
    methods["sqrt"] = ("double", "sqrt", ["double"], -1)

    # Trigonometry
    methods["cos"] = ("double", "cos", ["float"], -1)
    methods["sin"] = ("double", "sin", ["float"], -1)
    methods["tan"] = ("double", "tan", ["float"], -1)

    # Characters
    methods["isAlpha"] = ("bool", "is_alpha", ["char"], -1)
    methods["isAlphaNumeric"] = ("bool", "is_alpha_numeric", ["char"], -1)
    methods["isAscii"] = ("bool", "is_ascii", ["char"], -1)
    methods["isControl"] = ("bool", "is_control", ["char"], -1)
    methods["isDigit"] = ("bool", "is_digit", ["char"], -1)
    methods["isGraph"] = ("bool", "is_graph", ["char"], -1)
    methods["isHexadecimalDigit"] = (
        "bool", "is_hexadecimal_digit", ["char"], -1)
    methods["isLowerCase"] = ("bool", "is_lower_case", ["char"], -1)
    methods["isPrintable"] = ("bool", "is_printable", ["char"], -1)
    methods["isPunct"] = ("bool", "is_punct", ["char"], -1)
    methods["isSpace"] = ("bool", "is_space", ["char"], -1)
    methods["isUpperCase"] = ("bool", "is_upper_case", ["char"], -1)
    methods["isWhiteSpace"] = ("bool", "is_whitespace", ["char"], -1)

    # Random Numbers
    # Caution, inverse order for two params
    methods["random"] = ("long", "random", ["int", "(int)"], -1)
    methods["randomSeed"] = ("void", "random_seed", [], -1)  # Not implemented

    # Bits and bytes
    methods["bit"] = ("int", "bit", ["int"], -1)
    methods["bitClear"] = ("int", "bit_clear", ["int", "int"], -1)
    methods["bitRead"] = ("int", "bit_read", ["int", "int"], -1)
    methods["bitSet"] = ("void", "bit_set", ["int", "int"], -1)
    methods["bitWrite"] = ("void", "bit_write", ["int", "int", "int"], -1)
    methods["highByte"] = ("byte", "high_byte", ["double"], -1)
    methods["lowByte"] = ("byte", "low_byte", ["double"], -1)

    # External Interrupts
    methods["attachInterrupt"] = (
        "void", "attach_interrupt", [], -1)  # Not implemented
    methods["detachInterrupt"] = (
        "void", "detach_interrupt", [], -1)  # Not implemented

    # Interrupts
    methods["interrupts"] = ("void", "interrupts", [], -1)  # Not implemented
    methods["noInterrupts"] = (
        "void", "no_interrupts", [], -1)  # Not implemented

    # Others
    methods["exit"] = ('void', "exit", ["int"], -1)

    # Los siguientes métodos deberían encontrarse en una clase externa, sin embargo se ha decidido mantenerlos aquí
    #       para simplificar el diseño del código.
    methods["makeKeymap"] = ("int", "make_keymap", ["char"], -1)
    methods["Keypad"] = ("Keypad", "keypad", ["int", "byte", "byte", "int", "int"], -1)
    return methods


def get_not_implemented():
    return [
        "analogReference",
        "analogReadResolution",
        "analogWriteResolution",
        "noTone",
        "pulseIn",
        "pulseInLong",
        "shiftIn",
        "shiftOut",
        "tone",
        "randomSeed",
        "attachInterrupt",
        "detachInterrupt",
        "interrupts",
        "noInterrupts"
    ]


# Digital I/O
def digital_read(pin):
    """
    Reads the value from a specified digital pin
    Arguments:
        pin: the pin to read
    Returns:
        HIGH if reads 1, LOW if reads 0, None if else
    """
    if board.is_digital(pin):
        return board.read(pin)
    return ran.randint(0, 1)


def digital_write(pin, value):
    """
    Writes a HIGH or a LOW value to a digital pin
    Arguments:
        pin: the pin which will be written
        value: the value to write (HIGH or LOW)
    Returns:
        -1 if error, 0 if else
    """
    if board.is_digital(pin):
        if board.write_value(pin, value):
            return OK
    return ERROR


def pin_mode(pin, mode):
    """
    Configures the pin to behave as INPUT, OUTPUT or INPUT_PULLUP
    Arguments:
        pin: the pin whose mode will be configured
        mode: the mode to use
    Returns:
        -1 if error, 0 if else
    """
    if board.is_digital(pin):
        board.set_pin_mode(pin, mode)
        return OK
    return ERROR


# Analog I/O
def analog_read(pin):
    """
    Reads the value from the specified analog pin.
    Its value can be in the range [0-1023]
    Arguments:
        pin: the pin to read
    Returns:
        the value that is read or None if error
    """
    if board.is_analog(pin):
        return board.read(pin)
    return ran.randint(0, 1023)


def analog_reference():
    """
    Should configure the reference voltage. As it is not
    necessary for the purpose of the simulator, it is not
    implemented
    Returns:
        -2, as a warning of not implemented
    """
    return NOT_IMPL_WARNING


def analog_write(pin, value):
    """
    Writes an analog value to a pin.
    Arguments:
        pin: the pin to write (int)
        value: the duty cycle [0-255] (int)
    Returns:
        0 if correct, -1 if error
    """
    if board.is_analog(pin):
        if board.write_value(pin, value * 4):
            return OK
    return ERROR


# Zero, Due & MKR Family
def analog_read_resolution():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def analog_write_resolution():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


# Advanced I/O
def no_tone():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def pulse_in(pin, value):
    """
    Reads a pulse (either HIGH or LOW) on a pin
    Arguments:
        pin: the pin to read
        value: the value (HIGH or LOW to read)
    Returns:
        The read value
    """
    return board.read_pulse(pin, value)


def pulse_in_long():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def shift_in():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def shift_out():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def tone():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


# Time
def delay(ms):
    """
    Pauses the program for the amount of time (in milliseconds) specified
    Arguments:
        ms: the number of milliseconds to pause
    """
    ms = max(0, int(ms))
    if state is not None:
        state.exec_time_ms = int(time.time_ns() / 1000000) + ms

    seconds = ms / 1000.0
    if threading.current_thread() is threading.main_thread():
        deadline = time.monotonic() + seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if _stop_event.wait(min(remaining, 0.016)):
                break
            screen_updater.refresh()
    else:
        # _stop_event.wait() duerme el tiempo pedido pero despierta inmediatamente
        # si se activa el evento (stop/reset), haciendo el delay() interrumpible.
        _stop_event.wait(seconds)
    note_runtime_blocking()


def delay_microseconds(us):
    """
    Pauses the program for the amount of time (in microseconds) specified
    Arguments:
        us: the number of microseconds to pause
    """
    state.exec_time_us = int(time.time_ns() / 1000) + us


def micros():
    """
    Returns the number of microseconds since the Arduino board
    began running the current program
    """
    now = time.time()
    diff = now - start
    return int(diff * 1000000)


def millis():
    """
    Returns the number of milliseconds since the Arduino board
    began running the current program
    """
    now = time.time()
    diff = now - start
    return int(diff * 1000)


# Math
def abs(x):
    """
    Calculates the absolute value of a number
    Arguments:
        x: the mentioned number
    Returns:
        the absolute value
    """
    return builtins.abs(x)


def constrain(x, a, b):
    """
    Constrains a number to be within a range
    Arguments:
        x: the number to constrain
        a: the lower end
        b: the upper end
    Returns:
        x if between a and b, a if x < a or b if x > b
    """
    if a < x < b:
        return x
    elif x < a:
        return a
    else:
        return b


def F(value):
    return value


def sizeof(value):
    try:
        return len(value)
    except TypeError:
        return 1


def strtol(value, end=None, base=10):
    try:
        if hasattr(value, "string"):
            value = value.string
        if isinstance(value, list):
            value = "".join(str(item) for item in value).split("\0", 1)[0]
        parsed = int(str(value).strip(), int(base))
        if isinstance(end, Ref):
            end.value = "\0"
        return parsed
    except (TypeError, ValueError):
        if isinstance(end, Ref):
            end.value = value
        return 0


def map(value, from_low, from_high, to_low, to_high):
    """
    Re-maps a number from one range to another.
    That is, the upper bound gets mapped to the new upper bound,
    the lower bound gets mappedt to the new lower bound and so on
    Arguments:
        value: the number to map
        from_low: the lower bound of the value’s current range
        from_high: the upper bound of the value’s current range
        to_low: the lower bound of the value’s target range
        to_high: the upper bound of the value’s target range
    Returns:
        The value re-mapped
    """
    from_range = from_high - from_low
    to_range = to_high - to_low
    if from_range == 0:
        return to_low
    else:
        return (((value - from_low) * to_range) / from_range) + to_low


def max(x, y):
    """
    Calculates the maximum between two numbers
    Arguments:
        x: the first number
        y: the second number
    Returns:
        The largest of the parameters
    """
    return x if x > y else y


def min(x, y):
    """
    Calculates the minimum between two numbers
    Arguments:
        x: the first number
        y: the second number
    Returns:
        The lowest of the parameters
    """
    return x if x < y else y


def pow(base, exponent):
    """
    Calculates the value of a number raised to a power. pow().
    Can be used to raise a number to a fractional power
    Arguments:
        base: the number
        exponent: the power to which the base is raised
    Returns:
        The result of the pow
    """
    return base ** exponent


def sq(x):
    """
    Calculates the square of a number: the number multiplied by itself
    Arguments:
        x: the number to be squared
    Returns:
        The square of the number
    """
    return x * x


def sqrt(x):
    """
    Calculates the square root of a number
    Arguments:
        x: the number
    Returns:
        The square root of the number
    """
    return sqrt(x)


# Trigonometry
def cos(rad):
    """
    Calculates the cosine of an angle (in radians)
    Arguments:
        rad: the angle in radians
    Returns:
        The cos of the angle [-1, 1]
    """
    return cos(rad)


def sin(rad):
    """
    Calculates the sine of an angle (in radians)
    Arguments:
        rad: the angle in radians
    Returns:
        The sin of the angle [-1, 1]
    """
    return sin(rad)


def tan(rad):
    """
    Calculates the tangent of an angle (in radians)
    Arguments:
        rad: the angle in radians
    Returns:
        The tan of the angle [-1, 1]
    """
    return tan(rad)


# Characters
def is_alpha(this_char: str):
    """
    Analyse if a char is alpha (that is a letter)
    Arguments:
        this_char: the char to analyse
    Returns:
        True if is a letter, False if else
    """
    return this_char.isalpha()


def is_alpha_numeric(this_char: str):
    """
    Analyse if a char is alphanumeric (that is a letter
    or a number)
    Arguments:
        this_char: the char to analyse
    Returns:
        True if alphanumeric, False if else
    """
    return this_char.isalnum()


def is_ascii(this_char: str):
    """
    Analyses if a char is Ascii
    Arguments:
        this_char: the char to analyse
    Returns:
        True if Ascii, False if else
    """
    return this_char.isascii()


def is_control(this_char: str):
    """
    Analyses if a char is a control character
    Arguments:
        this_char: the char to analyse
    Returns:
        True if control, False if else
    """
    return this_char.isprintable()


def is_digit(this_char: str):
    """
    Analyses if a char is a digit (number)
    Arguments:
        this_char: the char to analyse
    Returns:
        True if digit, False if else
    """
    return this_char.isdigit()


def is_graph(this_char: str):
    """
    Analyse if a char is printable with some content (space is
    printable but has no content)
    Arguments:
        this_char: the char to analyse
    Returns:
        True if printable with some content, False if else
    """
    if this_char == ' ' or this_char == '\t':
        return False
    return this_char.isprintable()


def is_hexadecimal_digit(this_char: str):
    """
    Analyse if a char is an hexadecimal digit (A-F, 0-9)
    Arguments:
        this_char: the char to analyse
    Returns:
        True if hexadecimal, False if else
    """
    return (
        '0' <= this_char <= '9'
        or 'a' <= this_char <= 'f'
        or 'A' <= this_char <= 'F'
    )


def is_lower_case(this_char: str):
    """
    Analyse if a char is in lower case
    Arguments
        this_char: the char to analyse
    Returns:
        True if lower case, False if else
    """
    return this_char.islower()


def is_printable(this_char: str):
    """
    Analyse if a char is printable
    Arguments:
        this_char: the char to analyse
    Returns:
        True if is printable, False if else
    """
    return this_char.isprintable()


def is_punct(this_char: str):
    """
    Analyse if a char is punctuation
    Arguments:
        this_char: the char to analyse
    Returns:
        True if is punctuation, False if else
    """
    return this_char in string.punctuation


def is_space(this_char: str):
    """
    Analyse if a char is a white space character, including
    form feed, newling, carriage return, horizontal tab or vertical
    tab
    Arguments:
        this_char: the char to analyse
    Returns:
        True if white space, False if else
    """
    return (
        this_char == '\f'
        or this_char == '\n'
        or this_char == '\r'
        or this_char == '\t'
        or this_char == '\v'
        or this_char == ' '
    )


def is_upper_case(this_char: str):
    """
    Analyse if a char is upper case
    Arguments:
        this_char: the char to analyse
    Returns:
        True if upper case, False if else
    """
    return this_char.isupper()


def is_whitespace(this_char: str):
    """
    Analyse if a char is a white space character
    Arguments:
        this_char: the char to analyse
    Returns:
        True if white space, False if else
    """
    return this_char.isspace()


# Random Numbers
def random(max, min=0):
    """
    Generates a random number
    Arguments:
        max: the max of the number (exclusive)
        min: the min of the number (inclusive, optional, default 0)
    Returns:
        The random number
    """
    return ran.randint(min, max - 1)


def random_seed():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


# Bits and Bytes
def bit(n):
    """
    Computes the value of the specified bit
    Arguments:
        n: the bit to compute
    Returns:
        The value of the bit
    """
    return 1 << n


def bit_clear(x, n):
    """
    Clears a bit of a numeric value
    Arguments:
        x: the numeric variable whose bit to clear
        n: which bit to clear (starting from right)
    Returns:
        The value after the position n is cleared
    """
    return x & ~(1 << n)


def bit_read(x, n):
    """
    Reads a bit of a number
    Arguments:
        x: the number
        n: the bit to read (starting from right)
    Returns:
        The value of the bit (1 or 0)
    """
    return x & (1 << n)


def bit_set(x, n):
    """
    Writes to 1 a bit of a number
    Arguments:
        x: the number
        n: the bit to set
    Returns:
        The number with the bit set
    """
    mask = 1 << n
    return (x & ~mask) | (1 << n)


def bit_write(x, n, b):
    """
    Writes a bit into the position specified
    Arguments:
        x: the number
        n: the bit position (starting right)
        b: the bit to write (0 or 1)
    Returns:
        The number with changed bit
    """
    mask = 1 << n
    return (x & ~mask) | ((b << n) & mask)


def high_byte(x):
    """
    Extracts the leftmost byte
    Arguments:
        x: the value
    Returns:
        The leftmost byte
    """
    return x & 0xff


def low_byte(x):
    """
    Extracts the rightmost byte
    Arguments:
        x: the value
    Returns:
        The rightmost byte
    """
    return (x & 0xff00) >> 8


# External Interrupts
def attach_interrupt():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def detach_interrupt():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


# Interrupts
def interrupts():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def no_interrupts():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


# Others
def exit(n):
    """
    Finishes the program
    Arguments:
        n: an option
    """
    state.exited = True
