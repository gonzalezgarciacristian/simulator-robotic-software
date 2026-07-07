from pathlib import Path
from types import ModuleType, SimpleNamespace
import runpy
import sys

import pytest


class RecordingConsole:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def write_error(self, error):
        self.errors.append(error)

    def write_warning(self, warning):
        self.warnings.append(warning)


def _make_controller():
    console = RecordingConsole()
    controller = SimpleNamespace(
        console=console,
        robot_layer=SimpleNamespace(robot=SimpleNamespace(board="demo-board")),
        executing=True,
        arm3d=False,
        notifications=[],
        get_code=lambda: "void setup() {}",
    )
    controller._notify_state = controller.notifications.append
    return controller


def test_import_module_loads_generated_sketch(monkeypatch):
    import compiler.commands as commands

    loaded = []

    class Loader:
        def exec_module(self, module):
            module.loaded = True
            loaded.append(module)

    fake_spec = SimpleNamespace(loader=Loader())

    monkeypatch.setattr(
        commands.importlib.util,
        "spec_from_file_location",
        lambda name, path: fake_spec,
    )
    monkeypatch.setattr(
        commands.importlib.util,
        "module_from_spec",
        lambda spec: SimpleNamespace(spec=spec),
    )

    commands._import_module()

    assert commands.module.loaded is True
    assert sys.modules["temp.script_arduino"] is commands.module
    assert loaded == [commands.module]


def test_command_prepare_exec_and_compile_execute_paths(monkeypatch):
    import compiler.commands as commands
    import libraries.serial as serial
    import libraries.standard as standard
    import output.console as console
    import robot_components.robot_state as state

    controller = _make_controller()
    base_command = commands.Command(controller)
    base_command.prepare_exec()

    assert standard.board == "demo-board"
    assert isinstance(standard.state, state.State)
    assert serial.cons is controller.console
    assert base_command.ready is True
    assert base_command.execute() is None

    compile_command = commands.Compile(controller)
    warning = console.Warning("Uso", 1, 1, "warning")
    error = console.Error("Error", 1, 1, "broken")

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([], [error], "ast-error"),
    )
    assert compile_command.execute() is False
    assert controller.console.errors[-1] is error

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([warning], [], "ast-warning"),
    )
    assert compile_command.execute() is True
    assert controller.console.warnings[-1] is warning
    assert compile_command.ast == "ast-warning"

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([], [], "ast-clean"),
    )
    assert compile_command.execute() is True
    assert compile_command.ast == "ast-clean"

    monkeypatch.setattr(commands.traceback, "print_exc", lambda: None)

    def _raise_compile(_code):
        raise RuntimeError("boom")

    monkeypatch.setattr(commands.transpiler, "transpile", _raise_compile)
    assert compile_command.execute() is None
    assert controller.console.errors[-1].r_type == "Error de compilación"


def test_compile_returns_ast_or_none(monkeypatch):
    import compiler.commands as commands
    import output.console as console

    controller = _make_controller()
    compile_command = commands.Compile(controller)
    warning = console.Warning("Uso", 1, 1, "warning")
    error = console.Error("Error", 1, 1, "broken")

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([], [error], "ast-error"),
    )
    assert compile_command.compile("code") is None

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([warning], [], "ast-warning"),
    )
    assert compile_command.compile("code") == "ast-warning"

    monkeypatch.setattr(
        commands.transpiler,
        "transpile",
        lambda _code: ([], [], "ast-clean"),
    )
    assert compile_command.compile("code") == "ast-clean"

    monkeypatch.setattr(commands.traceback, "print_exc", lambda: None)

    def _raise_compile(_code):
        raise RuntimeError("boom")

    monkeypatch.setattr(commands.transpiler, "transpile", _raise_compile)
    assert compile_command.compile("code") is None
    assert controller.console.errors[-1].r_type == "Error de compilación"


def test_setup_execute_prepares_and_handles_runtime_paths(monkeypatch):
    import compiler.commands as commands
    import libraries.standard as standard
    import robot_components.robot_state as state

    controller = _make_controller()
    monkeypatch.setattr(commands.traceback, "print_exc", lambda: None)

    setup_calls = []

    class ImportedModule:
        @staticmethod
        def setup():
            setup_calls.append("setup")

    imported = {"value": False}

    def _fake_import():
        imported["value"] = True
        commands.module = ImportedModule()

    monkeypatch.setattr(commands, "_import_module", _fake_import)

    command = commands.Setup(controller)
    assert command.execute() is True
    assert imported["value"] is True
    assert command.ready is True
    assert setup_calls == ["setup"]
    assert standard._stop_event.is_set() is False

    standard._stop_event.set()
    standard.state = state.State()
    stale_stop = commands.Setup(controller)
    stale_stop.ready = True
    monkeypatch.setattr(commands, "module", SimpleNamespace(setup=lambda: setup_calls.append("setup-after-stop")))
    assert stale_stop.execute() is True
    assert setup_calls[-1] == "setup-after-stop"
    assert standard._stop_event.is_set() is False

    standard.state = state.State()
    standard.state.exec_time_us = 10**18
    monkeypatch.setattr(
        commands,
        "module",
        SimpleNamespace(setup=lambda: pytest.fail("setup() should not run while timing gate is active")),
    )
    skipped = commands.Setup(controller)
    skipped.ready = True
    assert skipped.execute() is True

    standard.state = state.State()
    paused = commands.Setup(controller)
    paused.ready = True
    monkeypatch.setattr(
        commands,
        "module",
        SimpleNamespace(setup=lambda: (_ for _ in ()).throw(commands.ExecutionPaused())),
    )
    assert paused.execute() is True

    standard.state = state.State()
    interrupted = commands.Setup(controller)
    interrupted.ready = True
    monkeypatch.setattr(
        commands,
        "module",
        SimpleNamespace(setup=lambda: (_ for _ in ()).throw(standard.ExecutionInterrupted())),
    )
    assert interrupted.execute() is True

    standard.state = state.State()
    failed = commands.Setup(controller)
    failed.ready = True
    monkeypatch.setattr(
        commands,
        "module",
        SimpleNamespace(setup=lambda: (_ for _ in ()).throw(RuntimeError("boom"))),
    )
    assert failed.execute() is False
    assert controller.console.errors[-1].r_type == "Error de ejecución"


def test_loop_execute_and_reboot_manage_background_thread(monkeypatch):
    import compiler.commands as commands
    import libraries.standard as standard

    controller = _make_controller()
    standard._stop_event.set()
    created_threads = []

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon
            self.started = False
            self.alive = True
            self.join_calls = []
            created_threads.append(self)

        def start(self):
            self.started = True

        def is_alive(self):
            return self.alive

        def join(self, timeout=None):
            self.join_calls.append(timeout)

    monkeypatch.setattr(commands.threading, "Thread", FakeThread)

    loop_command = commands.Loop(controller)
    loop_command.execute()

    assert loop_command.ready is True
    assert len(created_threads) == 1
    assert created_threads[0].started is True
    assert standard._stop_event.is_set() is False

    existing_thread = FakeThread()
    controller.executing = False
    loop_command._thread = existing_thread
    loop_command.execute()
    assert len(created_threads) == 2
    controller.executing = True

    loop_command._thread = existing_thread
    loop_command.reboot()

    assert existing_thread.join_calls == [0.5]
    assert loop_command._old_thread is existing_thread
    assert loop_command._thread is None
    assert loop_command.ready is False
    assert standard._stop_event.is_set() is True
    standard._stop_event.clear()


def test_loop_run_continues_after_debug_pause_and_stops_on_interrupt(monkeypatch):
    import compiler.commands as commands
    import libraries.standard as standard
    import robot_components.robot_state as state

    controller = _make_controller()
    loop_command = commands.Loop(controller)
    standard.state = state.State()

    events = iter(["pause", "interrupt"])

    def _loop():
        event = next(events)
        if event == "pause":
            raise commands.ExecutionPaused()
        raise standard.ExecutionInterrupted()

    monkeypatch.setattr(commands, "module", SimpleNamespace(loop=_loop))
    loop_command._run()
    assert controller.executing is True
    assert controller.notifications == []


def test_loop_run_waits_while_arm_safety_is_blocked(monkeypatch):
    import compiler.commands as commands
    import graphics.layers as layers_mod
    import libraries.standard as standard
    import robot_components.robot_state as state

    controller = _make_controller()
    loop_command = commands.Loop(controller)
    standard.state = state.State()

    class FakeArm3DLayer:
        def __init__(self):
            self.safety_blocked = True

    monkeypatch.setattr(layers_mod, "Arm3DLayer", FakeArm3DLayer)
    controller.arm3d = True
    controller.robot_layer = FakeArm3DLayer()
    loop_command._stop_flag = False
    monkeypatch.setattr(commands.time, "sleep", lambda _secs: setattr(loop_command, "_stop_flag", True))
    monkeypatch.setattr(commands, "module", SimpleNamespace(loop=lambda: pytest.fail("loop() should be blocked")))
    loop_command._run()

    assert loop_command._stop_flag is True
    assert controller.executing is True


def test_loop_run_reports_unexpected_sketch_failure(monkeypatch):
    import compiler.commands as commands
    import libraries.standard as standard
    import robot_components.robot_state as state

    controller = _make_controller()
    loop_command = commands.Loop(controller)
    standard.state = state.State()

    controller.robot_layer = SimpleNamespace(robot=SimpleNamespace(board="demo-board"))
    controller.executing = True
    loop_command._stop_flag = False
    monkeypatch.setattr(commands.traceback, "print_exc", lambda: None)
    monkeypatch.setattr(commands, "module", SimpleNamespace(loop=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    loop_command._run()
    assert controller.executing is False
    assert controller.notifications[-1] == "idle"


def test_loop_run_handles_outer_runtime_failure(monkeypatch):
    import compiler.commands as commands
    import libraries.standard as standard
    import robot_components.robot_state as state

    controller = _make_controller()
    loop_command = commands.Loop(controller)
    standard.state = state.State()

    monkeypatch.setattr(commands.traceback, "print_exc", lambda: None)
    monkeypatch.setattr(standard, "reset_runtime_watchdog", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    loop_command._run()

    assert controller.executing is False
    assert loop_command._stop_flag is True
    assert controller.notifications[-1] == "idle"


def test_warning_analyzer_handles_member_access_and_missing_names():
    import compiler.ast as ast
    import compiler.warnings as warnings_mod

    analyzer = warnings_mod.WarningAnalyzer()

    library_expr = ast.IDNode("Braccio")
    library_expr.type = None
    member = ast.MemberAccessNode(library_expr, ast.IDNode("calibrate"))
    call = ast.FunctionCallNode(member, [])
    assert analyzer.visit_function_call(call, None) is None
    assert analyzer.warnings == []

    missing_name_call = ast.FunctionCallNode(None, [])
    assert analyzer.visit_function_call(missing_name_call, None) is None
    assert analyzer.warnings == []


def test_main_script_bootstraps_gui_and_runs_mainloop(monkeypatch, tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "simulator" / "main.py"
    calls = []

    fake_graphics = ModuleType("graphics")
    fake_gui = ModuleType("graphics.gui")
    fake_graphics.__path__ = []

    class FakeApplication:
        def __init__(self):
            calls.append("init")

        def mainloop(self):
            calls.append("mainloop")

    fake_gui.MainApplication = FakeApplication
    fake_graphics.gui = fake_gui

    monkeypatch.setitem(sys.modules, "graphics", fake_graphics)
    monkeypatch.setitem(sys.modules, "graphics.gui", fake_gui)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script_path), run_name="__main__")

    assert Path.cwd() == project_root
    assert calls == ["init", "mainloop"]
