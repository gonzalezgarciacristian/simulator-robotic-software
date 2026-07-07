import os

import pytest

from compiler.transpiler import transpile
import libraries.standard as standard


def _generated_code(sketch):
    warns, errors, _ast = transpile(sketch)
    assert not errors, f"Errores inesperados al transpilar: {errors}"
    with open(os.path.join("temp", "script_arduino.py"), "r", encoding="utf-8") as fh:
        return fh.read()


def test_transpiler_injects_watchdog_checkpoint_in_empty_loop():
    code = _generated_code("void setup(){}\nvoid loop(){}")
    loop_body = code.split("def loop():", 1)[1]

    assert "standard.runtime_watchdog_checkpoint()" in loop_body
    assert "\tpass" not in loop_body


def test_transpiler_injects_watchdog_checkpoint_before_statements():
    code = _generated_code(
        """
void setup() {}
void loop() {
    int x = 0;
    x = x + 1;
}
"""
    )

    assert code.count("standard.runtime_watchdog_checkpoint()") >= 2


def test_runtime_watchdog_checkpoint_raises_on_stop_request():
    standard._stop_event.set()
    standard.reset_runtime_watchdog()

    try:
        with pytest.raises(standard.ExecutionInterrupted):
            standard.runtime_watchdog_checkpoint()
    finally:
        standard._stop_event.clear()
        standard.reset_runtime_watchdog()


def test_runtime_watchdog_defers_clock_checks_until_threshold(monkeypatch):
    perf_calls = 0

    standard.reset_runtime_watchdog()

    def fake_perf_counter_ns():
        nonlocal perf_calls
        perf_calls += 1
        return 0

    monkeypatch.setattr(standard.time, "perf_counter_ns", fake_perf_counter_ns)

    for _ in range(standard._WATCHDOG_CHECK_EVERY - 1):
        standard.runtime_watchdog_checkpoint()

    assert perf_calls == 0

    standard.runtime_watchdog_checkpoint()

    assert perf_calls == 1
