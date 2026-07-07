"""
Used for communication. Simulates the communication between
the board and the computer (with the possibility of expansion
into other devices not implemented)
"""

import output.console as console
import robot_components.boards as boards
import libraries.string as string_lib

OK = 0
ERROR = -1
NOT_IMPL_WARNING = -2

cons: console.Console = None


def get_name():
    return "Serial"


def get_methods():
    """
    Returns the methods of the library as a dict, whose
    key is the naming in Arduino and whose value is the
    corresponding method.
    Returns:
        A dict with the methods
    """
    methods = {}
    methods["if(Serial)"] = ("bool", "if_serial", [], -1)  # Not implemented
    methods["available"] = ("int", "available", [], -1)
    methods["availableForWrite"] = (
        "int", "available_for_write", [], -1)  # Not implemented
    methods["begin"] = ("void", "begin", ["long"], -1)
    methods["end"] = ("void", "end", [], -1)  # Not implemented
    methods["find"] = ("bool", "find", [], -1)  # Not implemented
    methods["findUntil"] = ("bool", "find_until", [], -1)  # Not implemented
    methods["flush"] = ("void", "flush", [], -1)  # Not implemented
    methods["parseFloat"] = ("float", "parse_float", [], -1)  # Not implemented
    methods["parseInt"] = ("long", "parse_int", [], -1)  # Not implemented
    methods["peek"] = ("int", "peek", [], -1)  # Not implemented
    methods["print"] = ("size_t", "print", ["any"], -1)
    methods["println"] = ("size_t", "println", ["(any)"], -1)
    methods["read"] = ("int", "read", [], -1)
    methods["readBytes"] = ("size_t", "read_bytes", [], -1)  # Not implemented
    methods["readBytesUntil"] = (
        "size_t", "read_bytes_until", [], -1)  # Not implemented
    methods["readString"] = ("string", "read_string",
                             [], -1)  # Not implemented
    methods["readStringUntil"] = (
        "string", "read_string_until", ["char"], -1)
    methods["setTimeout"] = ("void", "set_timeout", ["long"], -1)
    methods["write"] = ("size_t", "write", [], -1)  # Not implemented
    methods["serialEvent"] = ("void", "serial_event",
                              [], -1)  # Not implemented
    return methods


def get_not_implemented():
    return [
        "if(Serial)",
        "availableForWrite",
        "end",
        "find",
        "findUntil",
        "flush",
        "parseFloat",
        "parseInt",
        "peek",
        "readBytes",
        "readBytesUntil",
        "readString",
        "write",
        "serialEvent"
    ]


def if_serial():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def available():
    """
    Get the number of bytes (characters) available for reading from
    the serial port
    Returns:
        The number of bytes available to read
    """
    return cons.get_read_bytes()


def available_for_write():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def begin(speed):
    """
    Sets the data rate in bauds for serial data transmission.
    Config is not used because simulating its behaviour is very
    complex for our situation.
    Arguments:
        speed: the bauds (use: 50, 75, 110, 134, 150, 200, 300,
        600, 1200, 1800, 2400, 9600, 19200, 38400, 57600, 115200,
        230400, 460800, 500000, 576000, 921600, 1000000, 1152000,
        1500000, 2000000, 2500000, 3000000, 3500000, 4000000)
    """
    bauds = [50, 75, 110, 134, 150, 200, 300,
             600, 1200, 1800, 2400, 9600, 19200, 38400, 57600, 115200,
             230400, 460800, 500000, 576000, 921600, 1000000, 1152000,
             1500000, 2000000, 2500000, 3000000, 3500000, 4000000]
    if speed not in bauds:
        return ERROR
    else:
        cons.begin(speed)
    return OK


def end():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def find():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def find_until():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def flush():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def parse_float():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def parse_int():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def peek():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def print(val=""):
    """
    Prints a value to the console
    Arguments:
        val: the value
    """
    cons.write_output(val)


def println(val=""):
    """
    Prints a value to the console and finishes the line
    Arguments:
        val: the value
    """
    cons.write_output(str(val) + '\n')


def read():
    """
    Reads incoming serial data
    Returns:
        The first byte of incoming serial data or -1 if
        none available
    """
    return cons.read()


def read_bytes():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def read_bytes_until():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def read_string():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def read_string_until(terminator):
    value = []
    term = str(terminator)
    if len(term) > 0:
        term = term[0]
    while available() > 0:
        char = read()
        if char == term:
            break
        value.append(char)
    return string_lib.String("".join(value))


def set_timeout(_timeout):
    return OK


def write():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING


def serial_event():
    """
    Not needed (not implemented)
    """
    return NOT_IMPL_WARNING
