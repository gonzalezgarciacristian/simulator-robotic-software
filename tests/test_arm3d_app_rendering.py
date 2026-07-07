import threading
from types import SimpleNamespace

import numpy as np
import pytest


class _FakeWidget:
    def __init__(self, *args, **kwargs):
        self.parent = args[0] if args else None
        self.kwargs = kwargs
        self.pack_calls = []
        self.grid_calls = []
        self.added = []
        self.hidden = False

    def pack(self, *args, **kwargs):
        self.pack_calls.append((args, kwargs))

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))
        self.hidden = False

    def grid_remove(self):
        self.hidden = True

    def forget(self, *_args):
        self.hidden = True

    def panes(self):
        return [child for child, _ in self.added]

    def grid_columnconfigure(self, *_args, **_kwargs):
        return None

    def grid_rowconfigure(self, *_args, **_kwargs):
        return None

    def add(self, child, **kwargs):
        self.added.append((child, kwargs))

    def focus_force(self):
        return None

    def update_config_menu_label(self, *_args, **_kwargs):
        return None


class _FakeNotebook(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tabs = []
        self._selected = None

    def add(self, child, **kwargs):
        tab_id = str(child)
        if tab_id not in self._tabs:
            self._tabs.append(tab_id)
        self._selected = tab_id
        self.added.append((child, kwargs))

    def tabs(self):
        return list(self._tabs)

    def select(self, child=None):
        if child is None:
            return self._selected
        self._selected = str(child)
        if self._selected not in self._tabs:
            self._tabs.append(self._selected)
        return self._selected

    def forget(self, child):
        tab_id = str(child)
        if tab_id in self._tabs:
            self._tabs.remove(tab_id)


class _FakeSelector:
    def __init__(self, value=0):
        self.value = value

    def current(self):
        return self.value


class _FakeToggle:
    def __init__(self, value=1):
        self.value = value
        self.packed = False
        self.deselected = False

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def pack(self):
        self.packed = True

    def forget(self):
        self.packed = False

    def deselect(self):
        self.deselected = True


class _FakeText:
    def __init__(self):
        self.content = ""
        self.undo_calls = 0
        self.redo_calls = 0
        self.deleted = []

    def delete(self, *_args):
        self.deleted.append(True)
        self.content = ""

    def insert(self, _idx, text):
        self.content += text

    def get(self, *_args):
        return self.content

    def edit_undo(self):
        self.undo_calls += 1

    def edit_redo(self):
        self.redo_calls += 1


class _FakeConsole:
    def __init__(self):
        self.actions = []
        self.state = None

    def config(self, **kwargs):
        self.actions.append(("config", kwargs))
        if "state" in kwargs:
            self.state = kwargs["state"]

    def insert(self, _idx, text):
        self.actions.append(("insert", text))

    def delete(self, *_args):
        self.actions.append(("delete",))


class _FakeEditorFrame(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = _FakeText()
        self.last_controller = None
        self.changed_text = []

    def attach_controller(self, app):
        self.last_controller = app

    def change_text(self, text):
        self.changed_text.append(text)
        self.text.content = text


class _FakeDrawingChallenge:
    def __init__(self, idx):
        self.idx = idx

    def get_initial_code(self):
        return f"initial-{self.idx}"

    def get_challenge(self):
        return f"challenge-{self.idx}"


class _FakeDrawingModel:
    def __init__(self):
        self.scale = 100
        self.initialized = 0

    def zoom_percentage(self):
        return 133

    def get_robot_challenge(self, idx):
        return _FakeDrawingChallenge(idx)

    def initialize_points(self):
        self.initialized += 1


class _FakeLayer:
    def __init__(self):
        self.is_drawing = False
        self.drawing = _FakeDrawingModel()
        self.hud = SimpleNamespace(drawing=None, _info_panel=None)
        self.motor3d = SimpleNamespace()
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1


class _FakeArm3DLayer(_FakeLayer):
    pass


class _FakeDrawingFrame(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = SimpleNamespace(focus_force=lambda: None)
        self.hud_canvas = object()
        self.zoom_labels = []
        self.mouse_modes = []
        self.show_calls = []
        self.key_movement = _FakeToggle()
        self.key_drawing = _FakeToggle()

    def change_zoom_label(self, zoom_level):
        self.zoom_labels.append(zoom_level)

    def set_arm3d_mouse_mode(self, mode):
        self.mouse_modes.append(mode)

    def show_joystick(self):
        self.show_calls.append("show_joystick")

    def hide_joystick(self):
        self.show_calls.append("hide_joystick")

    def show_button_keys_movement(self):
        self.show_calls.append("show_button_keys_movement")

    def hide_button_keys_movement(self):
        self.show_calls.append("hide_button_keys_movement")

    def show_buttons_gamification(self):
        self.show_calls.append("show_buttons_gamification")

    def hide_buttons_gamification(self):
        self.show_calls.append("hide_buttons_gamification")

    def show_hud(self):
        self.show_calls.append("show_hud")

    def hide_hud(self):
        self.show_calls.append("hide_hud")

    def show_arm3d_camera_buttons(self):
        self.show_calls.append("show_arm3d_camera_buttons")

    def hide_arm3d_camera_buttons(self):
        self.show_calls.append("hide_arm3d_camera_buttons")

    def handle_global_key_press(self, event):
        self.show_calls.append(("key_press", event.char))


class _FakeSelectorBar(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.robot_selector = _FakeSelector(0)
        self.track_selector = _FakeSelector(1)
        self.gamification_option_selector = _FakeSelector(0)
        self.actions = []

    def hide_circuit_selector(self):
        self.actions.append("hide_circuit")

    def recover_circuit_selector(self):
        self.actions.append("recover_circuit")

    def hide_gamification_option_selector(self):
        self.actions.append("hide_gamification")

    def recover_gamification_option_selector(self):
        self.actions.append("recover_gamification")


class _FakeButtonBar(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = []

    def update_state(self, state):
        self.states.append(state)


class _FakeConsoleFrame(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = _FakeConsole()
        self.output = _FakeToggle(1)
        self.warning = _FakeToggle(0)
        self.error = _FakeToggle(1)


class _FakeInfoPanel(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_calls = []
        self.toggle_calls = 0

    def update(self, *args, **kwargs):
        self.update_calls.append((args, kwargs))

    def apply_visual_toggles(self):
        self.toggle_calls += 1


class _FakeControlPanel(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse_modes = []
        self.limit_updates = 0

    def set_mouse_drag_mode(self, mode):
        self.mouse_modes.append(mode)

    def update_joint_limits(self):
        self.limit_updates += 1


class _DummyController:
    def __init__(self, view):
        self.view = view
        self.calls = []
        self.board = False
        self.arm3d = False
        self.new = False
        self.console = None
        self.consoleGamification = SimpleNamespace(
            write_encrypted=lambda text, challenge: self.calls.append(
                ("write_encrypted", text, challenge)
            )
        )
        self.robot_layer = _FakeLayer()

    def configure_layer(self, drawing_canvas, hud_canvas):
        self.calls.append(("configure_layer", drawing_canvas, hud_canvas))

    def configure_console(self, text_component):
        self.console = text_component
        self.calls.append(("configure_console", text_component))

    def change_robot(self, option):
        self.calls.append(("change_robot", option))
        if option == 5:
            self.arm3d = True
            self.robot_layer = _FakeArm3DLayer()
        else:
            self.arm3d = False
            self.robot_layer = _FakeLayer()

    def change_circuit(self, option):
        self.calls.append(("change_circuit", option))

    def execute(self, option):
        self.calls.append(("execute", option))

    def stop(self):
        self.calls.append(("stop",))

    def toggle_pause(self):
        self.calls.append(("toggle_pause",))

    def step_once(self):
        self.calls.append(("step_once",))

    def zoom_in(self):
        self.calls.append(("zoom_in",))

    def zoom_out(self):
        self.calls.append(("zoom_out",))

    def filter_console(self, filters):
        self.calls.append(("filter_console", dict(filters)))

    def delete_elements(self):
        self.calls.append(("delete_elements",))

    def record_results(self, correct, challenge):
        self.calls.append(("record_results", correct, challenge))

    def exit(self):
        self.calls.append(("exit",))


class _FakeFileManager:
    def __init__(self):
        self.saved = []
        self.opened = []

    def open(self, path):
        self.opened.append(path)
        return ["line-1\n", "line-2\n"]

    def save(self, path, content):
        self.saved.append((path, content))


@pytest.fixture
def main_application_harness(monkeypatch):
    """Build MainApplication without a real Tk window and expose its spies."""
    import graphics.gui as gui_mod
    import graphics.layers as layers_mod

    file_managers = []
    opened_windows = []

    monkeypatch.setattr(gui_mod.tk.Tk, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(gui_mod.MainApplication, "title", lambda self, *_a, **_k: None)
    monkeypatch.setattr(gui_mod.MainApplication, "geometry", lambda self, *_a, **_k: None)
    monkeypatch.setattr(gui_mod.MainApplication, "config", lambda self, **_k: None)
    monkeypatch.setattr(gui_mod.MainApplication, "bind", lambda self, *_a, **_k: None)
    monkeypatch.setattr(gui_mod.MainApplication, "protocol", lambda self, *_a, **_k: None)
    monkeypatch.setattr(
        gui_mod.MainApplication,
        "after",
        lambda self, _delay, callback=None: callback() if callback is not None else "after-id",
    )
    monkeypatch.setattr(gui_mod.MainApplication, "after_cancel", lambda self, _ident: None)
    monkeypatch.setattr(gui_mod.MainApplication, "destroy", lambda self: setattr(self, "_destroyed", True))

    monkeypatch.setattr(gui_mod.tk, "Frame", _FakeWidget)
    monkeypatch.setattr(gui_mod.tk, "PanedWindow", _FakeWidget)
    monkeypatch.setattr(gui_mod.ttk, "Notebook", _FakeNotebook)
    monkeypatch.setattr(gui_mod, "MenuBar", _FakeWidget)
    monkeypatch.setattr(gui_mod, "ButtonBar", _FakeButtonBar)
    monkeypatch.setattr(gui_mod, "SelectorBar", _FakeSelectorBar)
    monkeypatch.setattr(gui_mod, "DrawingFrame", _FakeDrawingFrame)
    monkeypatch.setattr(gui_mod, "EditorFrame", _FakeEditorFrame)
    monkeypatch.setattr(gui_mod, "Arm3DControlPanel", _FakeControlPanel)
    monkeypatch.setattr(gui_mod, "ConsoleFrame", _FakeConsoleFrame)
    monkeypatch.setattr(gui_mod, "Arm3DInfoPanel", _FakeInfoPanel)
    monkeypatch.setattr(gui_mod.controller, "RobotsController", _DummyController)
    monkeypatch.setattr(
        gui_mod.files,
        "FileManager",
        lambda: file_managers.append(_FakeFileManager()) or file_managers[-1],
    )
    monkeypatch.setattr(gui_mod, "askopenfilename", lambda **_k: "opened.ino")
    monkeypatch.setattr(gui_mod, "asksaveasfilename", lambda **_k: "saved.ino")
    monkeypatch.setattr(
        gui_mod,
        "PinConfigurationWindow",
        lambda *args, **kwargs: opened_windows.append(("pin", args, kwargs)),
    )
    monkeypatch.setattr(
        gui_mod,
        "Arm3DConfigurationWindow",
        lambda *args, **kwargs: opened_windows.append(("arm3d", args, kwargs)),
    )
    monkeypatch.setattr(layers_mod, "Arm3DLayer", _FakeArm3DLayer)

    app = gui_mod.MainApplication()
    app.selector_bar.robot_selector.value = 0
    app.selector_bar.track_selector.value = 2
    app.selector_bar.gamification_option_selector.value = 0

    return SimpleNamespace(
        app=app,
        file_managers=file_managers,
        opened_windows=opened_windows,
    )


def test_main_application_delegates_execution_and_file_workflows(main_application_harness):
    harness = main_application_harness
    app = harness.app

    app.execute()
    app.stop()
    app.toggle_pause()
    app.step_once()
    app.editor_frame.text.content = "seed"
    app.editor_undo()
    app.editor_redo()
    app.open_file()
    app.save_file()

    assert app.get_code() == "line-1\nline-2\n"
    assert harness.file_managers[-1].opened == ["opened.ino"]
    assert harness.file_managers[-1].saved[-1] == ("saved.ino", "line-1\nline-2\n")
    assert app.editor_frame.text.undo_calls == 1
    assert app.editor_frame.text.redo_calls == 1
    assert ("execute", 0) in app.controller.calls
    assert ("stop",) in app.controller.calls
    assert ("toggle_pause",) in app.controller.calls
    assert ("step_once",) in app.controller.calls


def test_main_application_routes_robot_configuration_and_zoom(main_application_harness):
    harness = main_application_harness
    app = harness.app

    app.open_pin_configuration()
    app.selector_bar.robot_selector.value = 5
    app.controller.robot_layer = _FakeArm3DLayer()
    app.open_pin_configuration()
    app.open_arm3d_configuration()

    app.zoom_in()
    app.zoom_out()
    app.change_zoom_label("145%")
    app.set_arm3d_mouse_drag_mode("pan")

    app.change_robot(None)
    app.change_track(None)

    assert harness.opened_windows[0][0] == "pin"
    assert any(kind == "arm3d" for kind, _args, _kwargs in harness.opened_windows)
    assert ("zoom_in",) in app.controller.calls
    assert ("zoom_out",) in app.controller.calls
    assert app.drawing_frame.zoom_labels[-1] == "145%"
    assert app.drawing_frame.mouse_modes[-1] == "pan"


def test_main_application_updates_challenges_and_optional_controls(main_application_harness):
    app = main_application_harness.app

    app.controller.board = True
    for challenge in range(7):
        app.selector_bar.gamification_option_selector.value = challenge
        app._MainApplication__update_gamification_option()

    app.challenge = 0
    app.change_gamification_option(None)

    app.show_circuit_selector(True)
    app.show_circuit_selector(False)
    app.show_gamification_option_selector(True)
    app.show_gamification_option_selector(False)
    app.show_joystick(True)
    app.show_joystick(False)
    app.show_button_keys_movement(True)
    app.show_button_keys_movement(False)
    app.show_buttons_gamification(True)
    app.show_buttons_gamification(False)
    app.show_hud(True)
    app.show_hud(False)
    app.show_keys_movements(True)
    app.show_keys_movements(False)
    app.show_key_drawing(True)
    app.show_key_drawing(False)

    assert app.selector_bar.actions == [
        "recover_circuit",
        "hide_circuit",
        "recover_gamification",
        "hide_gamification",
    ]
    assert "show_joystick" in app.drawing_frame.show_calls
    assert "hide_joystick" in app.drawing_frame.show_calls
    assert app.drawing_frame.key_movement.packed is False
    assert app.drawing_frame.key_drawing.packed is False


def test_main_application_manages_arm_panel_input_console_and_shutdown(main_application_harness):
    app = main_application_harness.app

    app.selector_bar.robot_selector.value = 5
    app.controller.change_robot(5)
    app.show_arm3d_panel(True)
    app._connect_arm3d_info_panel()
    app.show_arm3d_panel(False)
    app._set_arm3d_control_tab_visible(True)
    app._set_arm3d_control_tab_visible(False)

    app.key_press(SimpleNamespace(char="w"))
    app.key_release(SimpleNamespace(char="w"))
    app.identifier = "after-id"
    app.abort_after()
    app.console_frame.output.set(1)
    app.console_frame.warning.set(0)
    app.console_frame.error.set(1)
    app.console_filter()
    app.toggle_keys()
    app.set_drawing()
    app.close()

    assert ("filter_console", {"info": True, "warning": False, "error": True}) in app.controller.calls
    assert app.move_WASD["w"] is False
    assert app._destroyed is True
    assert app.right_notebook.select() == str(app.editor_frame)


def test_arm3d_hud_reflects_joint_and_safety_state():
    import graphics.huds as huds_mod

    class DrawSpy:
        def __init__(self):
            self.calls = []

        def delete(self, *args):
            self.calls.append(("delete", args))

        def create_text(self, *args, **kwargs):
            self.calls.append(("text", args, kwargs))

    hud = huds_mod.Arm3DHUD()
    hud.set_text()
    canvas = DrawSpy()
    hud.set_canvas(canvas)
    info_panel_calls = []
    hud._info_panel = SimpleNamespace(update=lambda *a, **k: info_panel_calls.append((a, k)))
    hud.update(
        dof=3,
        joints=[45.0, 20.0, 15.0],
        end_effector=[100.0, 200.0, 300.0],
        in_workspace=False,
        singular=True,
        safety_blocked=False,
        warning_message="warning-text",
        joint_limits=[(-90.0, 90.0)] * 3,
        joint_types=["R", "P", "R"],
    )
    hud.update(
        dof=2,
        joints=[],
        end_effector=None,
        in_workspace=True,
        singular=False,
        safety_blocked=True,
        warning_message="",
        joint_limits=[(-90.0, 90.0)] * 2,
        joint_types=["R", "R"],
    )

    assert any(call[0] == "delete" for call in canvas.calls)
    assert any("BLOQUEADO" in str(call) for call in canvas.calls)
    assert info_panel_calls


def test_screen_updater_waits_for_resume_and_interrupts_stopped_execution(monkeypatch):
    import compiler.commands as commands_mod
    import graphics.screen_updater as screen_mod

    sleeping = []
    original_current_thread = screen_mod.threading.current_thread
    original_main_thread = screen_mod.threading.main_thread
    thread_obj = object()
    main_obj = object()
    monkeypatch.setattr(screen_mod.threading, "current_thread", lambda: thread_obj)
    monkeypatch.setattr(screen_mod.threading, "main_thread", lambda: main_obj)
    monkeypatch.setattr(screen_mod.time, "sleep", lambda delay: sleeping.append(delay))

    paused_state = {"paused": True}

    def should_pause(_line_no):
        return True

    screen_mod.controller = SimpleNamespace(
        paused=True,
        executing=True,
        debug_should_pause_at_line=should_pause,
    )
    screen_mod.view = SimpleNamespace(
        editor_frame=SimpleNamespace(
            set_current_exec_line=lambda line_no: paused_state.update(line=line_no)
        ),
        after=lambda _delay, callback=None: callback() if callback else None,
        update_idletasks=lambda: None,
        keys_used=False,
        move_WASD={},
    )

    def _sleep_and_resume(_delay):
        sleeping.append(_delay)
        screen_mod.controller.paused = False

    monkeypatch.setattr(screen_mod.time, "sleep", _sleep_and_resume)
    screen_mod._block_until_resumed()
    assert sleeping == [0.02]

    screen_mod.controller = SimpleNamespace(
        paused=True,
        executing=False,
        debug_should_pause_at_line=should_pause,
    )
    with pytest.raises(commands_mod.ExecutionPaused):
        screen_mod.debug_line(9)

    monkeypatch.setattr(screen_mod.threading, "current_thread", original_current_thread)
    monkeypatch.setattr(screen_mod.threading, "main_thread", original_main_thread)
    screen_mod.controller = None
    screen_mod.view = None


def test_arm_kinematic_state_normalizes_partial_configuration_and_limits():
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState

    state = ArmKinematicState()
    state.configure(
        dof=3,
        link_lengths=[120.0],
        joint_limits=[(-15.0, 15.0)],
        joint_types=["P", "X"],
        joints=[30.0],
        dh_rows=[{"theta": 0.0, "d": 5.0, "a": 10.0, "alpha": 0.0}],
        prismatic_pre_rotations=[("30", "45"), "bad"],
        base={"rpy": [10.0, 20.0, 30.0]},
    )

    state.set_dh([{"theta": 5.0, "d": 6.0, "a": 40.0, "alpha": 15.0}])
    state.set_limits([(-5.0, 5.0)])
    state.set_joint(0, 12.0)

    assert state.is_at_limit(0) is True
    assert state.is_at_limit(99) is False
    assert state.prismatic_pre_rotations[0] == {"yaw": 30.0, "pitch": 45.0}
    assert state.prismatic_pre_rotations[1] == {"yaw": 0.0, "pitch": 0.0}
    assert state.base_row["alpha"] > 0.0

    assert ArmKinematicState._normalize_prismatic_pre_rotation({"yaw": "bad", "pitch": 90}) == {
        "yaw": 0.0,
        "pitch": 90.0,
    }
    assert ArmKinematicState._normalize_base_row({"theta": "bad", "alpha": 12}) == {
        "theta": 0.0,
        "d": 0.0,
        "a": 0.0,
        "alpha": 12.0,
    }


def test_kinematics_fk_rejects_negative_prismatic_rotation_indexes():
    from motor3d.kinematics.kinematics_fk import get_prismatic_pre_rotation

    model = SimpleNamespace(
        prismatic_pre_rotations=[{"yaw": 45.0, "pitch": 15.0}],
    )

    assert get_prismatic_pre_rotation(model, -1) == {"yaw": 0.0, "pitch": 0.0}
    assert get_prismatic_pre_rotation(model, 0) == {"yaw": 45.0, "pitch": 15.0}


def test_generic_robot_renderer_builds_geometry_for_rotational_and_prismatic_models(monkeypatch):
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
    from motor3d.kinematics.kinematics_fk import forward_kinematics_chain
    from motor3d.rendering.robot3d_drawing import (
        GenericDhVisualModel,
        Robot3DDrawing,
        _axis_aligned_transform,
        _make_cylinder,
        _make_link_prism,
        _make_sphere_approx,
        _tint_color,
    )

    transform = _axis_aligned_transform([0.0, 0.0, 5.0])
    np.testing.assert_allclose(transform[:3, 2], [0.0, 0.0, 1.0], atol=1e-9)
    np.testing.assert_allclose(_axis_aligned_transform([0.0, 0.0, 0.0]), np.eye(4), atol=1e-9)

    cylinder = _make_cylinder([0.0, 0.0, 0.0], np.eye(4), 10.0, 20.0, 8)
    prism = _make_link_prism([0.0, 0.0, 0.0], [30.0, 0.0, 0.0], 8.0)
    sphere = _make_sphere_approx([0.0, 0.0, 0.0], 5.0, steps=4)
    assert cylinder.shape == (32, 3, 3)
    assert prism.shape == (12, 3, 3)
    assert sphere.shape == (64, 3, 3)
    assert _tint_color((200, 220, 240), 1.3) == (255, 255, 255)

    visual = GenericDhVisualModel()

    gripper_model = ArmKinematicState()
    gripper_model.configure(
        dof=3,
        link_lengths=[0.0, 160.0, 20.0],
        joint_limits=[(-90.0, 90.0), (-90.0, 90.0), (-80.0, -10.0)],
        joint_types=["R", "R", "R"],
        joints=[10.0, -15.0, -60.0],
        dh_rows=[
            {"theta": 0.0, "d": 120.0, "a": 0.0, "alpha": 90.0},
            {"theta": 0.0, "d": 0.0, "a": 160.0, "alpha": 0.0},
            {"theta": 0.0, "d": 0.0, "a": 20.0, "alpha": 0.0},
        ],
        visual={"mode": "auto_generic", "theme": "default", "sizes": {}},
    )
    gripper_chain = forward_kinematics_chain(gripper_model)
    gripper_tris = list(
        visual.iter_triangles(gripper_model, gripper_chain["positions"], gripper_chain)
    )
    assert gripper_tris
    assert visual.supports_model(gripper_model) is True
    assert visual.get_effective_end_effector(
        gripper_model, gripper_chain["positions"], gripper_chain
    )

    prismatic_model = ArmKinematicState()
    prismatic_model.configure(
        dof=1,
        link_lengths=[120.0],
        joint_limits=[(0.0, 120.0)],
        joint_types=["P"],
        joints=[60.0],
        dh_rows=[{"theta": 0.0, "d": 90.0, "a": 120.0, "alpha": 0.0}],
        visual={"mode": "auto_generic", "theme": "default", "sizes": {}},
    )
    prismatic_chain = forward_kinematics_chain(prismatic_model)
    prismatic_tris = list(
        visual.iter_triangles(prismatic_model, prismatic_chain["positions"], prismatic_chain)
    )
    assert prismatic_tris

    drawing = Robot3DDrawing()
    mesh_groups = []
    monkeypatch.setattr(
        drawing,
        "_render_mesh_vectorized",
        lambda draw_obj, projection, groups: mesh_groups.append((projection, groups)),
    )
    drawing._render_mesh(
        draw=SimpleNamespace(),
        camera=SimpleNamespace(
            get_view_matrix=lambda: (np.eye(3), np.zeros(3)),
            focal_length=800.0,
            get_focal=lambda h=None: 800.0,
            screen_offset_x=0.0,
            screen_offset_y=0.0,
            projection_mode="perspective",
            get_projection_scale=lambda h=None: 1.0,
            distance=500.0,
            PROJECTION_CABALLERA="caballera",
            CABALLERA_ANGLE_DEG=45.0,
            CABALLERA_DEPTH_SCALE=0.5,
        ),
        all_tris=[(cylinder[:1], (10, 20, 30)), (prism[:1], (40, 50, 60), False)],
        w=800,
        h=600,
    )
    assert len(mesh_groups[0][1]) == 2


def test_robot3d_drawing_projects_scene_and_parallelizes_meshes(monkeypatch):
    from motor3d.camera.camera import Camera
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
    from motor3d.kinematics.kinematics_fk import forward_kinematics_chain
    from motor3d.rendering import robot3d_drawing as drawing_mod

    class DrawSpy:
        def __init__(self):
            self.lines = []
            self.polygons = []
            self.ellipses = []
            self.texts = []

        def line(self, points, **kwargs):
            self.lines.append((points, kwargs))

        def ellipse(self, bounds, **kwargs):
            self.ellipses.append((bounds, kwargs))

        def polygon(self, points, **kwargs):
            self.polygons.append((points, kwargs))

        def text(self, pos, label, **kwargs):
            self.texts.append((pos, label, kwargs))

    drawing = drawing_mod.Robot3DDrawing()
    camera = Camera()
    projection = drawing._build_projection_context(camera, 800, 600)

    assert drawing._project_camera_space(np.array([10.0, 20.0, 100.0]), projection) is not None
    assert drawing._project_camera_space(
        np.array([10.0, 20.0, 100.0]),
        {
            **projection,
            "mode": "caballera",
            "ortho_scale": 1.0,
            "target_depth": camera.distance,
            "oblique_dx": 0.5,
            "oblique_dy": 0.5,
        },
    ) is not None
    assert drawing._project_camera_space(
        np.array([10.0, 20.0, 100.0]),
        {**projection, "mode": "isometrica", "ortho_scale": 1.0},
    ) is not None

    draw = DrawSpy()
    model = ArmKinematicState()
    model.configure(
        dof=2,
        link_lengths=[120.0, 120.0],
        joint_limits=[(-90.0, 90.0), (-80.0, 80.0)],
        joint_types=["R", "R"],
        joints=[15.0, -20.0],
        dh_rows=[
            {"theta": 0.0, "d": 90.0, "a": 0.0, "alpha": 90.0},
            {"theta": 0.0, "d": 0.0, "a": 120.0, "alpha": 0.0},
        ],
        visual={"mode": "skeleton", "theme": "default", "sizes": {}, "show_joint_ranges": True, "show_joint_axes": True},
    )
    chain = forward_kinematics_chain(model)
    points3d = chain["positions"]

    drawing._render_skeleton(draw, points3d, model, projection)
    drawing._draw_grid(draw, projection)
    drawing._draw_axes(draw, projection)
    drawing._draw_trail(draw, [[0.0, 0.0, 0.0], [10.0, 10.0, 0.0], [20.0, 10.0, 10.0]], projection)
    arcs = drawing._collect_joint_arcs(model, points3d, chain, projection)
    assert draw.lines
    assert draw.ellipses
    assert draw.texts
    assert arcs

    class CanvasSpy:
        def __init__(self):
            self.created = 0
            self.itemconfigs = 0

        def create_image(self, *_args, **_kwargs):
            self.created += 1
            return "img-id"

        def itemconfig(self, *_args, **_kwargs):
            self.itemconfigs += 1
            raise RuntimeError("missing item")

    monkeypatch.setattr(drawing_mod.ImageTk, "PhotoImage", lambda img: ("photo", img.size))
    canvas = CanvasSpy()
    image = drawing_mod.Image.new("RGB", (10, 10), (0, 0, 0))
    drawing._blit(canvas, image)
    drawing._blit(canvas, image)
    assert canvas.created == 2
    assert canvas.itemconfigs == 1

    worker_draw = DrawSpy()
    worker_drawing = drawing_mod.Robot3DDrawing()
    worker_drawing._mesh_worker_count = 2
    worker_drawing._mesh_worker_min_tris = 1
    tri = np.array([
        [[0.0, 0.0, 100.0], [0.0, 10.0, 100.0], [10.0, 0.0, 100.0]],
        [[0.0, 0.0, 120.0], [0.0, 10.0, 120.0], [10.0, 0.0, 120.0]],
        [[0.0, 0.0, 140.0], [0.0, 10.0, 140.0], [10.0, 0.0, 140.0]],
        [[0.0, 0.0, 160.0], [0.0, 10.0, 160.0], [10.0, 0.0, 160.0]],
    ])
    worker_drawing._render_mesh_vectorized(
        worker_draw,
        {
            "R_view": np.eye(3),
            "cam_pos": np.zeros(3),
            "f": 800.0,
            "cx": 400.0,
            "cy": 300.0,
            "mode": "perspective",
            "ortho_scale": 1.0,
            "target_depth": 500.0,
        },
        [(tri, (120, 160, 200), True)],
    )
    assert worker_draw.polygons
    assert worker_drawing._mesh_executor is not None


def test_arm3d_layer_delegates_camera_render_and_hud_operations(monkeypatch):
    import graphics.layers as layers_mod

    layer = layers_mod.Arm3DLayer()
    hud_calls = []
    layer.hud = SimpleNamespace(
        set_canvas=lambda canvas: hud_calls.append(("set_canvas", canvas)),
        reboot=lambda: hud_calls.append(("reboot",)),
        update=lambda **kwargs: hud_calls.append(("update", kwargs)),
        drawing=None,
    )
    layer.motor3d.renderer._canvas_image_id = "existing"
    layer.set_canvas(SimpleNamespace(delete=lambda *_a, **_k: None), object())
    layer.execute()
    layer.stop()
    layer.zoom_in()
    layer.zoom_out()
    layer.drag_camera(4, 5, pan=True)
    layer.dolly_camera(6)
    layer.set_camera_yaw(25.0)
    layer.set_camera_pitch(15.0)
    layer.reset_camera()
    layer.set_trail(True)
    layer.clear_trail()
    assert layer.get_model_config()["dof"] >= 1

    monkeypatch.setattr(layers_mod.time, "monotonic", lambda: layer._interactive_render_until + 1.0)
    layer._interactive_render_until = 0.0
    layer._sync_servos_from_model(reset_animation=True)
    assert layer.wants_fast_render() is False
    layer._request_fast_render(0.5)
    monkeypatch.setattr(layers_mod.time, "monotonic", lambda: layer._interactive_render_until - 0.1)
    assert layer.wants_fast_render() is True
    layer._update_hud(
        {
            "blocked": False,
            "message": "ok",
            "in_workspace": True,
            "singular": False,
        }
    )
    assert any(call[0] == "update" for call in hud_calls)


def test_stl_loader_handles_missing_truncated_and_ascii_files(tmp_path):
    from motor3d.rendering import robot3d_drawing as drawing_mod

    missing = drawing_mod._load_stl(tmp_path / "missing.stl")
    assert missing.shape == (0, 3, 3)

    short_binary = tmp_path / "short_binary.stl"
    short_binary.write_bytes(b"tiny")
    assert drawing_mod._load_stl(short_binary).shape == (0, 3, 3)

    ascii_stl = tmp_path / "triangle_ascii.stl"
    ascii_stl.write_text(
        "\n".join(
            [
                "solid triangle",
                "facet normal 0 0 1",
                "outer loop",
                "vertex 0 0 0",
                "vertex 1 0 0",
                "vertex 0 1 0",
                "endloop",
                "endfacet",
                "endsolid triangle",
            ]
        ),
        encoding="utf-8",
    )
    triangles = drawing_mod._load_stl(ascii_stl)
    assert triangles.shape == (1, 3, 3)


def test_robot3d_drawing_ignores_degenerate_geometry():
    from motor3d.rendering import robot3d_drawing as drawing_mod

    drawing = drawing_mod.Robot3DDrawing()
    camera = SimpleNamespace(
        get_view_matrix=lambda: (np.eye(3), np.zeros(3)),
        focal_length=1.0,
        get_focal=lambda h=None: 1.0,
        screen_offset_x=0.0,
        screen_offset_y=0.0,
        projection_mode="caballera",
        get_projection_scale=lambda h=None: 2.0,
        distance=100.0,
        PROJECTION_CABALLERA="caballera",
        CABALLERA_ANGLE_DEG=45.0,
        CABALLERA_DEPTH_SCALE=0.5,
    )
    projection = drawing._build_projection_context(camera, 400, 300)
    assert "oblique_dx" not in projection
    assert "oblique_dy" not in projection
    assert drawing._project_camera_space(np.array([0.0, 0.0, 0.01]), projection) is None

    class DrawSpy:
        def __init__(self):
            self.lines = []
            self.texts = []

        def line(self, points, **kwargs):
            self.lines.append((points, kwargs))

        def text(self, pos, label, **kwargs):
            self.texts.append((pos, label, kwargs))

    draw = DrawSpy()
    perspective = {
        **projection,
        "mode": "perspective",
        "R_view": np.eye(3),
        "cam_pos": np.zeros(3),
        "f": 1.0,
        "cx": 0.0,
        "cy": 0.0,
    }

    drawing._draw_axes(draw, perspective)
    drawing._draw_trail(draw, [[0.0, 0.0, 0.0]], perspective)

    assert draw.lines == []
    assert draw.texts == []
    assert drawing._resolve_joint_basis(
        {"pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 0.0], "xref": [1.0, 0.0, 0.0]}
    ) is None

    model = SimpleNamespace(dof=1, joint_types=["R"], joint_limits=[(-30.0, 30.0)])
    drawing.resolve_visual_model = lambda _model: SimpleNamespace(
        get_joint_frames=lambda *_args, **_kwargs: [
            {"pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 0.0], "xref": [1.0, 0.0, 0.0], "r_arc": 40.0}
        ]
    )
    arcs = drawing._collect_joint_arcs(model, [], {}, perspective)
    assert arcs == []


# ---------------------------------------------------------------------------
# Diseño responsive del módulo 3D (lógica pura, sin Tk real)
# ---------------------------------------------------------------------------


def test_arm3d_config_compute_ui_scale_fits_screen():
    """La escala adaptativa de la ventana de configuración se topea a 0.85 en
    pantallas grandes y encoge (sin bajar de 0.5) en pantallas pequeñas."""
    import graphics.gui as gui_mod

    Win = gui_mod.Arm3DConfigurationWindow
    big = SimpleNamespace(
        winfo_screenwidth=lambda: 3840, winfo_screenheight=lambda: 2160,
        _CONTENT_K_W=Win._CONTENT_K_W, _CONTENT_K_H=Win._CONTENT_K_H,
    )
    small = SimpleNamespace(
        winfo_screenwidth=lambda: 1024, winfo_screenheight=lambda: 600,
        _CONTENT_K_W=Win._CONTENT_K_W, _CONTENT_K_H=Win._CONTENT_K_H,
    )
    s_big = Win._compute_ui_scale(big)
    s_small = Win._compute_ui_scale(small)

    assert s_big == pytest.approx(0.85)
    assert 0.5 <= s_small < 0.85
    assert s_small <= s_big


def test_drawing_frame_camera_scale_tiers():
    """La barra de cámara elige el tamaño de icono por tramos de ancho del
    viewport (encoge de forma escalonada al estrecharse)."""
    import graphics.gui as gui_mod

    fake = SimpleNamespace(
        _cam_icon_size=None, _cam_buttons=[],
        _cam_font_scaler=gui_mod.FontScaler(),
    )
    expectations = [(700, 26), (500, 22), (400, 18), (300, 14)]
    for width, expected_icon in expectations:
        fake._cam_icon_size = None  # forzar recálculo en cada tramo
        gui_mod.DrawingFrame._apply_camera_scale(fake, width)
        assert fake._cam_icon_size == expected_icon


def test_arm3d_config_canvas_configure_fills_width():
    """Regresión: al ensanchar el canvas, el contenido se estira para llenar el
    hueco horizontal; al estrecharlo respeta su ancho natural (con scroll)."""
    import graphics.gui as gui_mod

    class FakeCanvas:
        def __init__(self):
            self.item_widths = []

        def itemconfigure(self, _id, width):
            self.item_widths.append(width)

        def configure(self, **_kwargs):
            return None

    canvas = FakeCanvas()
    inner = SimpleNamespace(winfo_reqwidth=lambda: 400, winfo_reqheight=lambda: 300)
    fake = SimpleNamespace(
        _scroll_canvas=canvas, _scroll_inner=inner, _scroll_inner_id="iid",
        _last_fill_w=None, _set_scrollbar_visibility=lambda *_a: None,
    )

    # Canvas más ancho que el contenido -> se estira hasta el ancho del canvas.
    gui_mod.Arm3DConfigurationWindow._on_scroll_canvas_configure(
        fake, SimpleNamespace(width=700, height=500))
    assert canvas.item_widths[-1] == 700

    # Canvas más estrecho -> mantiene el ancho natural (no aplasta el contenido).
    fake._last_fill_w = None
    gui_mod.Arm3DConfigurationWindow._on_scroll_canvas_configure(
        fake, SimpleNamespace(width=250, height=500))
    assert canvas.item_widths[-1] == 400


def test_arm3d_layer_fps_counter_scales_with_viewport():
    """El contador de FPS usa una fuente proporcional al viewport (mayor en
    ventanas grandes, menor en pequeñas), acotada al rango legible [8, 16]."""
    import graphics.layers as layers_mod

    class FakeCanvas:
        def __init__(self, w, h):
            self._w, self._h = w, h
            self.fonts = []

        def delete(self, *_a):
            return None

        def winfo_width(self):
            return self._w

        def winfo_height(self):
            return self._h

        def create_text(self, _x, _y, **kwargs):
            self.fonts.append(kwargs.get("font"))
            return 1

        def bbox(self, _id):
            return (0, 0, 10, 10)

        def create_rectangle(self, *_a, **_k):
            return 2

        def tag_lower(self, *_a):
            return None

    layer = layers_mod.Arm3DLayer()
    layer.motor3d.model.visual['show_fps_counter'] = True

    big = FakeCanvas(1600, 1000)
    layer._canvas = big
    layer._fps_last_frame_time = None
    layer._draw_fps_counter()

    small = FakeCanvas(320, 240)
    layer._canvas = small
    layer._fps_last_frame_time = None
    layer._draw_fps_counter()

    big_size = big.fonts[-1][1]
    small_size = small.fonts[-1][1]
    assert big_size > small_size
    assert 8 <= small_size <= 16
    assert 8 <= big_size <= 16
