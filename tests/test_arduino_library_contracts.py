"""Contract tests for the reusable Arduino-compatible libraries.

These tests intentionally exercise public behaviour shared by sketches instead
of details tied to a particular challenge or GUI layout.
"""

import threading
from types import SimpleNamespace

import pytest

from libraries import braccio, serial, servo, standard
from libraries.string import String
from output import console as console_module


class FakeConsole:
    def __init__(self, incoming=""):
        self.incoming = list(incoming)
        self.output = []
        self.speed = None

    def begin(self, speed):
        self.speed = speed

    def get_read_bytes(self):
        return len(self.incoming)

    def read(self):
        return self.incoming.pop(0) if self.incoming else -1

    def write_output(self, value):
        self.output.append(value)


class FakeTextWidget:
    def __init__(self):
        self.insertions = []
        self.pending_callbacks = []

    def tag_config(self, *_args, **_kwargs):
        pass

    def config(self, **_kwargs):
        pass

    def insert(self, _position, message, tag):
        self.insertions.append((message, tag))

    def see(self, _position):
        pass

    def delete(self, *_args):
        self.insertions.clear()

    def after(self, _delay, callback):
        self.pending_callbacks.append(callback)


class FakeLogger:
    def __init__(self):
        self.records = []

    def write_log(self, level, message):
        self.records.append((level, message))


class FakeServoElement:
    def __init__(self, pin, value=90):
        self.pin = pin
        self.value = value
        self.min = None
        self.max = None

    def set_value(self, pin, value):
        assert pin == self.pin
        self.value = value


class FakePulseServoElement(FakeServoElement):
    def __init__(self, pin, value=90):
        super().__init__(pin, value)
        self.pulses = []

    def set_pulse_value(self, pin, pulse, pulse_min, pulse_max, angle):
        assert pin == self.pin
        self.pulses.append((pulse, pulse_min, pulse_max, angle))
        self.value = angle
        return True


class FakeBoard:
    def __init__(self, elements=None):
        self.elements = dict(elements or {})
        self.detached = []
        self.writes = []

    def get_pin_element(self, pin):
        return self.elements.get(pin)

    def detach_pin(self, pin):
        self.detached.append(pin)

    def write_value(self, pin, value):
        self.writes.append((pin, value))
        return True


def test_string_supports_common_value_operations():
    value = String("  Robot")
    value.concat(" Arm  ")
    assert value.length() == 13
    assert value.starts_with(String("  Rob"))
    assert value.ends_with(String("  "))
    assert value.substring(2, 7) == "Robot"
    assert value.get_bytes() == b"  Robot Arm  "
    assert value.c_str().endswith("\0")

    value.trim()
    value.to_upper_case()
    assert value == "ROBOT ARM"
    value.to_lower_case()
    assert value.equals_ignore_case(String("robot arm"))
    assert value.to_char_array([], 20) == list("robot arm")


@pytest.mark.parametrize(
    ("raw", "as_int", "as_float"),
    [("42", 42, 42.0), ("-7", -7, -7.0), ("not-a-number", 0, 0.0)],
)
def test_string_numeric_conversions_use_arduino_fallbacks(raw, as_int, as_float):
    value = String(raw)
    assert value.to_int() == as_int
    assert value.to_float() == as_float
    assert value.to_double() == as_float


def test_string_in_place_concatenation_accepts_strings_and_values():
    value = String("arm")
    value += String("3d")
    value += 2
    assert value == "arm3d2"


def test_serial_validates_baud_rate_and_transfers_text(monkeypatch):
    console = FakeConsole("ready\nremaining")
    monkeypatch.setattr(serial, "cons", console)

    assert serial.begin(9600) == serial.OK
    assert console.speed == 9600
    assert serial.begin(12345) == serial.ERROR

    serial.print("status")
    serial.println(200)
    assert console.output == ["status", "200\n"]
    assert str(serial.read_string_until("\n")) == "ready"
    assert serial.available() == len("remaining")
    assert serial.read() == "r"
    assert serial.set_timeout(500) == serial.OK


@pytest.mark.parametrize(
    "operation",
    [
        serial.if_serial,
        serial.available_for_write,
        serial.end,
        serial.find,
        serial.find_until,
        serial.flush,
        serial.parse_float,
        serial.parse_int,
        serial.peek,
        serial.read_bytes,
        serial.read_bytes_until,
        serial.read_string,
        serial.write,
        serial.serial_event,
    ],
)
def test_unimplemented_serial_operations_report_a_warning(operation):
    assert operation() == serial.NOT_IMPL_WARNING


def test_console_round_trips_input_and_filters_report_types(monkeypatch):
    monkeypatch.setattr(console_module, "Logger", FakeLogger)
    widget = FakeTextWidget()
    console = console_module.Console(widget)

    console.input("go")
    assert console.get_read_bytes() == 3
    assert [console.read(), console.read(), console.read(), console.read()] == ["g", "o", "\n", -1]

    error = console_module.Error("runtime", 4, 2, "stopped")
    warning = console_module.Warning("range", 7, 1, "clamped")
    assert "runtime" in error.to_string()
    assert "range" in warning.to_string()
    console.write_error(error)
    console.write_warning(warning)
    console.filter_messages({"warning"})
    assert widget.insertions == [(warning.to_string() + "\n", "warning")]

    console.clear()
    assert console.messages == []
    assert console.input_msgs == []


def test_console_batches_background_output_on_widget_thread(monkeypatch):
    monkeypatch.setattr(console_module, "Logger", FakeLogger)
    widget = FakeTextWidget()
    console = console_module.Console(widget)

    worker = threading.Thread(target=lambda: (console.write_output("one"), console.write_output("two")))
    worker.start()
    worker.join()

    assert len(widget.pending_callbacks) == 1
    widget.pending_callbacks.pop()()
    assert widget.insertions == [("onetwo", "info")]

    error = console_module.Error("thread", 1, 1, "error")
    warning = console_module.Warning("thread", 1, 1, "warning")
    reporter = threading.Thread(target=lambda: (console.write_error(error), console.write_warning(warning)))
    reporter.start()
    reporter.join()
    assert len(widget.pending_callbacks) == 2
    for callback in list(widget.pending_callbacks):
        callback()
    assert (error.to_string() + "\n", "error") in widget.insertions
    assert (warning.to_string() + "\n", "warning") in widget.insertions


def test_servo_lifecycle_clamps_angles_and_releases_pin():
    element = FakeServoElement(pin=6)
    board = FakeBoard({6: element})
    motor = servo.Servo(board)

    assert motor.attach(6, 600, 2200) == motor.OK
    assert (element.min, element.max) == (600, 2200)
    assert motor.attached()

    motor.write(250)
    assert motor.read() == 180
    motor.write(-20)
    assert motor.read() == 0
    motor.write("invalid")
    assert motor.read() == 0
    assert motor.write_microseconds(1500) == motor.OK
    assert motor.read() == 101
    assert motor.write_microseconds(500) == motor.OK
    assert motor.read() == 0
    assert motor.write_microseconds(2500) == motor.OK
    assert motor.read() == 180
    assert motor.write_microseconds("invalid") == motor.ERROR
    assert motor.read() == 180

    assert motor.detach() == motor.OK
    assert board.detached == [6]
    assert not motor.attached()
    assert motor.detach() == motor.ERROR


def test_servo_write_microseconds_preserves_pulse_for_arm_elements():
    element = FakePulseServoElement(pin=6)
    board = FakeBoard({6: element})
    motor = servo.Servo(board)

    assert motor.attach(6, 500, 2500) == motor.OK
    assert motor.write_microseconds(2500) == motor.OK

    assert motor.read() == 180
    assert element.pulses == [(2500, 500, 2500, 180)]


def test_servo_reports_failure_when_no_compatible_pin_exists():
    motor = servo.Servo(FakeBoard())
    assert motor.attach(99) == motor.ERROR
    assert motor.read() is None
    assert motor.write_microseconds(1000) == motor.ERROR


class FakeIoBoard(FakeBoard):
    def __init__(self):
        super().__init__()
        self.modes = []

    @staticmethod
    def is_digital(pin):
        return pin in {2, 3}

    @staticmethod
    def is_analog(pin):
        return pin == 0

    @staticmethod
    def read(pin):
        return {0: 512, 2: standard.HIGH}[pin]

    def set_pin_mode(self, pin, mode):
        self.modes.append((pin, mode))

    @staticmethod
    def read_pulse(pin, value):
        return (pin, value)


def test_standard_io_delegates_valid_pins_and_rejects_invalid_writes(monkeypatch):
    board = FakeIoBoard()
    monkeypatch.setattr(standard, "board", board)
    monkeypatch.setattr(standard.ran, "randint", lambda low, high: high)

    assert standard.digital_read(2) == standard.HIGH
    assert standard.digital_read(99) == standard.HIGH
    assert standard.digital_write(3, standard.LOW) == standard.OK
    assert standard.digital_write(99, standard.HIGH) == standard.ERROR
    assert standard.pin_mode(2, standard.OUTPUT) == standard.OK
    assert standard.pin_mode(99, standard.OUTPUT) == standard.ERROR
    assert board.modes == [(2, standard.OUTPUT)]

    assert standard.analog_read(0) == 512
    assert standard.analog_read(99) == 1023
    assert standard.analog_write(0, 64) == standard.OK
    assert standard.analog_write(99, 64) == standard.ERROR
    assert board.writes == [(3, standard.LOW), (0, 256)]
    assert standard.pulse_in(2, standard.HIGH) == (2, standard.HIGH)


def test_standard_numeric_character_and_bit_helpers_obey_their_contracts():
    assert [standard.constrain(value, 0, 10) for value in (-1, 4, 11)] == [0, 4, 10]
    assert standard.map(5, 0, 10, 0, 100) == 50
    assert standard.map(5, 1, 1, 20, 30) == 20
    assert standard.sizeof([1, 2, 3]) == 3
    assert standard.sizeof(10) == 1
    assert standard.F("stored in flash") == "stored in flash"
    assert standard.pow(3, 2) == 9
    assert standard.sq(4) == 16

    assert standard.is_alpha("R")
    assert standard.is_alpha_numeric("7")
    assert standard.is_ascii("A")
    assert standard.is_digit("7")
    assert standard.is_graph("!") and not standard.is_graph(" ")
    assert standard.is_hexadecimal_digit("F")
    assert standard.is_lower_case("r")
    assert standard.is_printable(" ")
    assert standard.is_punct("?")
    assert standard.is_space("\n")
    assert standard.is_upper_case("R")
    assert standard.is_whitespace("\t")

    assert standard.bit(3) == 8
    assert standard.bit_clear(0b1111, 2) == 0b1011
    assert standard.bit_read(0b0100, 2) == 0b0100
    assert standard.bit_set(0, 2) == 0b0100
    assert standard.bit_write(0b1111, 1, 0) == 0b1101


def test_standard_reference_parsing_and_delays_preserve_runtime_contract(monkeypatch):
    end = standard.Ref()
    assert str(end) == "None"
    assert repr(end) == "None"
    assert standard.strtol(String("ff"), end, 16) == 255
    assert end.value == "\0"
    assert standard.strtol(["1", "2", "\0", "9"], end) == 12

    class FakeStopEvent:
        def __init__(self):
            self.waits = []

        def wait(self, seconds):
            self.waits.append(seconds)
            return False

        @staticmethod
        def is_set():
            return False

    stop_event = FakeStopEvent()
    state = SimpleNamespace(exec_time_ms=0)
    refreshes = []
    clock = iter((1.0, 1.0, 1.01))
    monkeypatch.setattr(standard, "_stop_event", stop_event)
    monkeypatch.setattr(standard, "state", state)
    monkeypatch.setattr(standard.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(standard.screen_updater, "refresh", lambda: refreshes.append(True))

    standard.delay(5)
    assert state.exec_time_ms > 0
    assert stop_event.waits == [pytest.approx(0.005)]
    assert refreshes == [True]

    worker = threading.Thread(target=lambda: standard.delay(2))
    worker.start()
    worker.join()
    assert stop_event.waits[-1] == pytest.approx(0.002)


def test_braccio_without_connected_servos_keeps_safe_default_pose():
    arm = braccio.Braccio()
    arm.set_board(None)

    assert arm.begin() == arm.OK
    assert arm._get_step_positions() == braccio._DEFAULT_STEP_POSITIONS
    values = [-20, 200, 90, 181, 40, 0]
    assert arm._clamp_values(values) == [0, 165, 90, 180, 40, 10]


def test_braccio_falls_back_to_board_writes_for_missing_servo_elements():
    board = FakeBoard()
    arm = braccio.Braccio(board)
    arm._write_servo("base", 45)
    assert board.writes == [(braccio.BRACCIO_PINS["base"], 45)]


def test_braccio_delay_cooperates_with_standard_runtime(monkeypatch):
    import graphics.screen_updater as screen_updater

    delays = []
    refreshes = []
    monkeypatch.setattr(standard, "state", SimpleNamespace())
    monkeypatch.setattr(standard, "delay", lambda milliseconds: delays.append(milliseconds))
    monkeypatch.setattr(screen_updater, "refresh", lambda *args, **kwargs: refreshes.append((args, kwargs)))

    braccio._delay_ms(20)
    assert delays == [16, 4]
    assert len(refreshes) == 3


def test_library_metadata_exposes_stable_names_and_callable_operations():
    assert standard.get_name() == "Standard"
    assert serial.get_name() == "Serial"
    assert servo.get_name() == "Servo"
    assert braccio.get_name() == "Braccio"

    # Standard also advertises the separately implemented Keypad helpers, so
    # only libraries whose metadata is entirely module-level are checked here.
    for module in (serial, braccio):
        for _, python_name, _, _ in module.get_methods().values():
            assert callable(getattr(module, python_name))

    assert standard.get_not_implemented()
    assert serial.get_not_implemented()
    assert servo.get_not_implemented() == []
    assert braccio.get_not_implemented() == []
